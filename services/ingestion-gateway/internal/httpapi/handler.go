package httpapi

import (
	"encoding/json"
	"io"
	"log/slog"
	"net/http"
	"strconv"
	"strings"
	"time"
	"github.com/redis/go-redis/v9"

	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/auth"
	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/kafka"
	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/model"
	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/ratelimit"
	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/usage"
	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/validate"
)

type Handler struct {
	verifier     *auth.Verifier
	producer     *kafka.Producer
	redis        *redis.Client
	maxBodyBytes int64
	logger       *slog.Logger
}

func NewHandler(v *auth.Verifier, p *kafka.Producer, rdb *redis.Client, maxBody int64, logger *slog.Logger) *Handler {
	return &Handler{verifier: v, producer: p, redis: rdb, maxBodyBytes: maxBody, logger: logger}
}

func (h *Handler) Ingest(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.NotFound(w, r)
		return
	}
	cred := extractCredential(r)
	principal, err := h.verifier.Verify(r.Context(), cred)
	if err != nil {
		writeJSON(w, http.StatusUnauthorized, map[string]string{"error": "unauthorized"})
		return
	}
	if !principal.HasScope("ingest") {
		writeJSON(w, http.StatusForbidden, map[string]string{"error": "missing ingest scope"})
		return
	}

	r.Body = http.MaxBytesReader(w, r.Body, h.maxBodyBytes)
	raw, err := io.ReadAll(r.Body)
	if err != nil {
		writeJSON(w, http.StatusRequestEntityTooLarge, map[string]string{"error": "body too large"})
		return
	}
	var req model.IngestRequest
	if err := json.Unmarshal(raw, &req); err != nil || len(req.Events) == 0 {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "malformed json or empty batch"})
		return
	}
	if len(req.Events) > 1000 {
		writeJSON(w, http.StatusRequestEntityTooLarge, map[string]string{"error": "batch too large"})
		return
	}

	allowed, remaining, err := ratelimit.AllowEvents(r.Context(), h.redis, principal.TenantID, principal.MaxEventsPerSec, len(req.Events))
	if err != nil {
		h.logger.Error("rate limit error", "err", err)
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "internal"})
		return
	}
	w.Header().Set("X-RateLimit-Limit", itoa(principal.MaxEventsPerSec))
	w.Header().Set("X-RateLimit-Remaining", itoa(remaining))
	if !allowed {
		w.Header().Set("Retry-After", "1")
		writeJSON(w, http.StatusTooManyRequests, map[string]string{"error": "rate limit exceeded"})
		return
	}

	ingestTime := time.Now().UTC().Format(time.RFC3339Nano)
	resp := model.IngestResponse{}
	for i, ev := range req.Events {
		env, verr := validate.Event(ev, principal.RunID)
		if verr != nil {
			verr.Index = i
			resp.Errors = append(resp.Errors, *verr)
			resp.Rejected++
			continue
		}
		env.TenantID = principal.TenantID.String()
		env.IngestTime = ingestTime
		if err := h.producer.Publish(r.Context(), env.TenantID, env); err != nil {
			h.logger.Error("kafka publish failed", "err", err)
			writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "publish failed"})
			return
		}
		resp.Accepted++
	}
	_ = usage.IncrementIngested(r.Context(), h.redis, principal.TenantID, resp.Accepted)
	_ = usage.IncrementRejected(r.Context(), h.redis, principal.TenantID, resp.Rejected)

	status := http.StatusAccepted
	if resp.Accepted == 0 {
		status = http.StatusUnprocessableEntity
	}
	writeJSON(w, status, resp)
}

func extractCredential(r *http.Request) string {
	if key := r.Header.Get("X-API-Key"); key != "" {
		return key
	}
	authz := r.Header.Get("Authorization")
	if strings.HasPrefix(strings.ToLower(authz), "bearer ") {
		return strings.TrimSpace(authz[7:])
	}
	return ""
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func itoa(n int) string {
	return strconv.Itoa(n)
}
