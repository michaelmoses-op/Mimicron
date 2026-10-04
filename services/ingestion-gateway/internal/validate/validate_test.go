package validate

import (
	"encoding/json"
	"testing"
	"time"

	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/model"
)

func TestEventTelemetryOK(t *testing.T) {
	ev := model.InboundEvent{
		DeviceID:  "dev-1",
		EventTime: time.Now().UTC().Format(time.RFC3339),
		Kind:      "telemetry",
		Data:      map[string]jsonNumber("temperature_c", "21.5"),
	}
	env, err := Event(ev, nil)
	if err != nil {
		t.Fatalf("unexpected error: %+v", err)
	}
	if env.DeviceID != "dev-1" {
		t.Fatalf("device mismatch")
	}
}

func jsonNumber(k, v string) map[string]json.Number {
	m := map[string]json.Number{}
	m[k] = json.Number(v)
	return m
}
