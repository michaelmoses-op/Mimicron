package config

import (
	"os"
	"strconv"
)

type Config struct {
	HTTPAddr         string
	RedisURL         string
	KafkaBrokers     string
	ControlAPIURL    string
	InternalSecret   string
	JWTSecret        string
	TelemetryTopic   string
	MaxBodyBytes     int64
	APIKeyCacheTTL   int // seconds
}

func Load() Config {
	return Config{
		HTTPAddr:       env("HTTP_ADDR", ":8081"),
		RedisURL:       env("REDIS_URL", "redis://localhost:6379/0"),
		KafkaBrokers:   env("KAFKA_BROKERS", "localhost:19092"),
		ControlAPIURL:  env("CONTROL_API_URL", "http://localhost:8000"),
		InternalSecret: env("INTERNAL_API_SECRET", "dev-internal-secret-change-me"),
		JWTSecret:      env("JWT_SECRET", "dev-jwt-secret-change-me"),
		TelemetryTopic: env("TELEMETRY_RAW_TOPIC", "telemetry.raw"),
		MaxBodyBytes:   envInt64("MAX_BODY_BYTES", 5*1024*1024),
		APIKeyCacheTTL: envInt("API_KEY_CACHE_TTL_SECONDS", 300),
	}
}

func env(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func envInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return fallback
}

func envInt64(key string, fallback int64) int64 {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.ParseInt(v, 10, 64); err == nil {
			return n
		}
	}
	return fallback
}
