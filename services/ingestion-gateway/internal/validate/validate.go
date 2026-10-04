package validate

import (
	"fmt"
	"regexp"
	"time"

	"github.com/google/uuid"

	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/model"
)

var deviceIDPattern = regexp.MustCompile(`^[A-Za-z0-9._:-]+$`)

const maxMetrics = 64

func Event(ev model.InboundEvent, principalRunID *uuid.UUID) (model.Envelope, *model.IngestError) {
	if ev.DeviceID == "" || len(ev.DeviceID) > 128 || !deviceIDPattern.MatchString(ev.DeviceID) {
		return model.Envelope{}, &model.IngestError{Code: "invalid_device_id", Message: "invalid device_id"}
	}
	if ev.Kind == "" {
		ev.Kind = "telemetry"
	}
	if ev.Kind != "telemetry" && ev.Kind != "traffic" {
		return model.Envelope{}, &model.IngestError{Code: "invalid_schema", Message: "invalid kind"}
	}
	if ev.SchemaVersion == 0 {
		ev.SchemaVersion = 1
	}
	if ev.SchemaVersion != 1 {
		return model.Envelope{}, &model.IngestError{Code: "invalid_schema", Message: "unsupported schema_version"}
	}
	eventTime, err := time.Parse(time.RFC3339, ev.EventTime)
	if err != nil {
		return model.Envelope{}, &model.IngestError{Code: "invalid_time", Message: "event_time must be RFC3339"}
	}
	now := time.Now().UTC()
	if eventTime.Before(now.Add(-30*24*time.Hour)) || eventTime.After(now.Add(5*time.Minute)) {
		return model.Envelope{}, &model.IngestError{Code: "invalid_time", Message: "event_time out of allowed window"}
	}
	if ev.Data == nil || len(ev.Data) == 0 {
		return model.Envelope{}, &model.IngestError{Code: "invalid_schema", Message: "data required"}
	}
	if len(ev.Data) > maxMetrics {
		return model.Envelope{}, &model.IngestError{Code: "too_many_metrics", Message: "too many data fields"}
	}
	data := make(map[string]any, len(ev.Data))
	if ev.Kind == "telemetry" {
		for k, v := range ev.Data {
			f, err := v.Float64()
			if err != nil {
				return model.Envelope{}, &model.IngestError{Code: "non_numeric_metric", Message: fmt.Sprintf("metric %s must be numeric", k)}
			}
			data[k] = f
		}
	} else {
		for k, v := range ev.Data {
			f, err := v.Float64()
			if err != nil {
				data[k] = v.String()
			} else {
				data[k] = f
			}
		}
	}
	if ev.RunID != nil && *ev.RunID != "" {
		if principalRunID != nil {
			parsed, err := uuid.Parse(*ev.RunID)
			if err != nil || parsed != *principalRunID {
				return model.Envelope{}, &model.IngestError{Code: "unauthorized_run", Message: "run_id not authorized for this credential"}
			}
		}
	} else if principalRunID != nil {
		rid := principalRunID.String()
		ev.RunID = &rid
	}
	eventID := ev.EventID
	if eventID == "" {
		eventID = uuid.NewString()
	}
	if _, err := uuid.Parse(eventID); err != nil {
		return model.Envelope{}, &model.IngestError{Code: "invalid_schema", Message: "event_id must be a UUID"}
	}
	if len(ev.DeviceType) > 64 {
		return model.Envelope{}, &model.IngestError{Code: "invalid_schema", Message: "device_type too long"}
	}
	if len(ev.Tags) > 16 {
		return model.Envelope{}, &model.IngestError{Code: "invalid_schema", Message: "too many tags"}
	}
	for k, v := range ev.Tags {
		if len(k) == 0 || len(v) > 128 {
			return model.Envelope{}, &model.IngestError{Code: "invalid_schema", Message: "invalid tag"}
		}
	}
	return model.Envelope{
		SchemaVersion: ev.SchemaVersion,
		EventID:       eventID,
		Kind:          ev.Kind,
		RunID:         ev.RunID,
		DeviceID:      ev.DeviceID,
		DeviceType:    ev.DeviceType,
		EventTime:     ev.EventTime,
		Seq:           ev.Seq,
		Tags:          ev.Tags,
		Data:          data,
	}, nil
}
