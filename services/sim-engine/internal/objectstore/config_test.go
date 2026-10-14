package objectstore

import "testing"

func TestFromEnvDefaults(t *testing.T) {
	t.Setenv("S3_ENDPOINT", "")
	t.Setenv("S3_BUCKET", "")
	t.Setenv("S3_ACCESS_KEY", "")
	t.Setenv("S3_SECRET_KEY", "")
	t.Setenv("S3_FORCE_PATH_STYLE", "")

	cfg := FromEnv()
	if cfg.Region != "us-east-1" {
		t.Fatalf("region: got %q", cfg.Region)
	}
	if !cfg.ForcePathStyle {
		t.Fatal("expected path-style default true")
	}
	if cfg.Configured() {
		t.Fatal("expected not configured")
	}
}

func TestFromEnvConfigured(t *testing.T) {
	t.Setenv("S3_ENDPOINT", "http://127.0.0.1:9000")
	t.Setenv("S3_REGION", "garage")
	t.Setenv("S3_BUCKET", "mimicron-archives")
	t.Setenv("S3_ACCESS_KEY", "key")
	t.Setenv("S3_SECRET_KEY", "secret")
	t.Setenv("S3_FORCE_PATH_STYLE", "false")

	cfg := FromEnv()
	if !cfg.Configured() {
		t.Fatal("expected configured")
	}
	if cfg.ForcePathStyle {
		t.Fatal("expected path-style false")
	}
}
