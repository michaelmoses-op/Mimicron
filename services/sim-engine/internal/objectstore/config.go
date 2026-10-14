package objectstore

import (
	"os"
	"strings"
)

// Config holds S3-compatible object storage settings (replay archives — not wired yet).
type Config struct {
	Endpoint         string
	Region           string
	Bucket           string
	AccessKey        string
	SecretKey        string
	ForcePathStyle   bool
}

// FromEnv reads S3_* variables shared across services.
func FromEnv() Config {
	return Config{
		Endpoint:       env("S3_ENDPOINT", ""),
		Region:         env("S3_REGION", "us-east-1"),
		Bucket:         env("S3_BUCKET", ""),
		AccessKey:      env("S3_ACCESS_KEY", ""),
		SecretKey:      env("S3_SECRET_KEY", ""),
		ForcePathStyle: envBool("S3_FORCE_PATH_STYLE", true),
	}
}

// Configured reports whether a client could be constructed.
func (c Config) Configured() bool {
	return c.Endpoint != "" && c.Bucket != "" && c.AccessKey != "" && c.SecretKey != ""
}

func env(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func envBool(key string, def bool) bool {
	v := strings.ToLower(os.Getenv(key))
	if v == "" {
		return def
	}
	switch v {
	case "1", "true", "yes", "on":
		return true
	case "0", "false", "no", "off":
		return false
	default:
		return def
	}
}
