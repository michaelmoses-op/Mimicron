package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/redis/go-redis/v9"

	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/config"
	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/auth"
	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/httpapi"
	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/kafka"
)

func main() {
	cfg := config.Load()
	logger := slog.New(slog.NewJSONHandler(os.Stdout, nil))

	opt, err := redis.ParseURL(cfg.RedisURL)
	if err != nil {
		logger.Error("redis url", "err", err)
		os.Exit(1)
	}
	rdb := redis.NewClient(opt)

	producer, err := kafka.NewProducer(cfg.KafkaBrokers, cfg.TelemetryTopic)
	if err != nil {
		logger.Error("kafka", "err", err)
		os.Exit(1)
	}
	defer producer.Close()

	verifier := auth.NewVerifier(
		rdb,
		cfg.ControlAPIURL,
		cfg.InternalSecret,
		cfg.JWTSecret,
		time.Duration(cfg.APIKeyCacheTTL)*time.Second,
	)
	handler := httpapi.NewHandler(verifier, producer, rdb, cfg.MaxBodyBytes, logger)

	mux := http.NewServeMux()
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	})
	mux.HandleFunc("/readyz", func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()
		checks := map[string]string{}
		if err := rdb.Ping(ctx).Err(); err != nil {
			checks["redis"] = "fail"
		} else {
			checks["redis"] = "ok"
		}
		checks["kafka"] = "ok"
		w.Header().Set("Content-Type", "application/json")
		_ = jsonReady(w, checks)
	})
	mux.HandleFunc("/metrics", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "text/plain; version=0.0.4")
		_, _ = w.Write([]byte("# TYPE up gauge\nup 1\n"))
	})
	mux.HandleFunc("/v1/ingest", handler.Ingest)

	srv := &http.Server{Addr: cfg.HTTPAddr, Handler: mux, ReadHeaderTimeout: 5 * time.Second}

	go func() {
		logger.Info("ingestion-gateway listening", "addr", cfg.HTTPAddr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Error("server failed", "err", err)
			os.Exit(1)
		}
	}()

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()
	<-ctx.Done()

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(shutdownCtx)
}

func jsonReady(w http.ResponseWriter, checks map[string]string) error {
	ready := true
	for _, v := range checks {
		if v == "fail" {
			ready = false
		}
	}
	status := "ready"
	code := http.StatusOK
	if !ready {
		status = "not_ready"
		code = http.StatusServiceUnavailable
	}
	w.WriteHeader(code)
	_, err := w.Write([]byte(`{"status":"` + status + `"}`))
	return err
}
