package auth

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

type Verifier struct {
	redis          *redis.Client
	controlAPIURL  string
	internalSecret string
	jwtSecret      []byte
	cacheTTL       time.Duration
	httpClient     *http.Client
}

func NewVerifier(rdb *redis.Client, controlAPIURL, internalSecret, jwtSecret string, cacheTTL time.Duration) *Verifier {
	return &Verifier{
		redis:          rdb,
		controlAPIURL:  strings.TrimRight(controlAPIURL, "/"),
		internalSecret: internalSecret,
		jwtSecret:      []byte(jwtSecret),
		cacheTTL:       cacheTTL,
		httpClient:     &http.Client{Timeout: 3 * time.Second},
	}
}

func (v *Verifier) Verify(ctx context.Context, rawCredential string) (Principal, error) {
	rawCredential = strings.TrimSpace(rawCredential)
	if rawCredential == "" {
		return Principal{}, fmt.Errorf("missing credential")
	}
	if strings.HasPrefix(rawCredential, "mc_live_") {
		return v.verifyAPIKey(ctx, rawCredential)
	}
	return v.verifyRunToken(rawCredential)
}

func (v *Verifier) verifyAPIKey(ctx context.Context, fullKey string) (Principal, error) {
	hash := sha256.Sum256([]byte(fullKey))
	hashHex := hex.EncodeToString(hash[:])
	cacheKey := "apikey:" + hashHex

	cached, err := v.redis.Get(ctx, cacheKey).Result()
	if err == nil {
		var payload verifyResponse
		if json.Unmarshal([]byte(cached), &payload) == nil {
			return principalFromVerify(payload)
		}
	}
	if err != nil && err != redis.Nil {
		return Principal{}, err
	}

	payload, err := v.callControlVerify(ctx, hashHex)
	if err != nil {
		return Principal{}, err
	}
	b, _ := json.Marshal(payload)
	_ = v.redis.Set(ctx, cacheKey, string(b), v.cacheTTL).Err()
	return principalFromVerify(payload)
}

type verifyResponse struct {
	TenantID string `json:"tenant_id"`
	KeyID    string `json:"key_id"`
	Scopes   []string `json:"scopes"`
	Limits   struct {
		MaxEventsPerSec int `json:"max_events_per_sec"`
	} `json:"limits"`
}

func (v *Verifier) callControlVerify(ctx context.Context, keyHash string) (verifyResponse, error) {
	body, _ := json.Marshal(map[string]string{"key_hash": keyHash})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, v.controlAPIURL+"/internal/v1/keys/verify", bytes.NewReader(body))
	if err != nil {
		return verifyResponse{}, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-Internal-Secret", v.internalSecret)
	resp, err := v.httpClient.Do(req)
	if err != nil {
		return verifyResponse{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusNotFound {
		return verifyResponse{}, fmt.Errorf("invalid api key")
	}
	if resp.StatusCode != http.StatusOK {
		b, _ := io.ReadAll(resp.Body)
		return verifyResponse{}, fmt.Errorf("verify failed: %s", string(b))
	}
	var out verifyResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return verifyResponse{}, err
	}
	return out, nil
}

func principalFromVerify(v verifyResponse) (Principal, error) {
	tid, err := uuid.Parse(v.TenantID)
	if err != nil {
		return Principal{}, err
	}
	kid, err := uuid.Parse(v.KeyID)
	if err != nil {
		return Principal{}, err
	}
	return Principal{
		TenantID:        tid,
		KeyID:           &kid,
		Scopes:          v.Scopes,
		MaxEventsPerSec: v.Limits.MaxEventsPerSec,
	}, nil
}

type runClaims struct {
	TenantID string   `json:"tenant_id"`
	RunID    string   `json:"run_id"`
	Scopes   []string `json:"scopes"`
	Type     string   `json:"type"`
	jwt.RegisteredClaims
}

func (v *Verifier) verifyRunToken(token string) (Principal, error) {
	parsed, err := jwt.ParseWithClaims(token, &runClaims{}, func(t *jwt.Token) (any, error) {
		if t.Method != jwt.SigningMethodHS256 {
			return nil, fmt.Errorf("unexpected signing method")
		}
		return v.jwtSecret, nil
	})
	if err != nil || !parsed.Valid {
		return Principal{}, fmt.Errorf("invalid run token")
	}
	claims, ok := parsed.Claims.(*runClaims)
	if !ok {
		return Principal{}, fmt.Errorf("invalid claims")
	}
	if claims.Type != "run" {
		return Principal{}, fmt.Errorf("invalid token type")
	}
	tid, err := uuid.Parse(claims.TenantID)
	if err != nil {
		return Principal{}, err
	}
	rid, err := uuid.Parse(claims.RunID)
	if err != nil {
		return Principal{}, err
	}
	return Principal{
		TenantID: tid,
		RunID:    &rid,
		Scopes:   claims.Scopes,
		// Run tokens inherit tenant quota at mint time in control-api; use generous default until wired.
		MaxEventsPerSec: 500,
	}, nil
}
