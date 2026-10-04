package model

import "encoding/json"

type IngestRequest struct {
	Events []InboundEvent `json:"events"`
}

type IngestResponse struct {
	Accepted int           `json:"accepted"`
	Rejected int           `json:"rejected"`
	Errors   []IngestError `json:"errors,omitempty"`
}

type IngestError struct {
	Index   int    `json:"index"`
	Code    string `json:"code"`
	Message string `json:"message"`
}

type InboundEvent struct {
	SchemaVersion int                    `json:"schema_version"`
	EventID       string                 `json:"event_id"`
	Kind          string                 `json:"kind"`
	RunID         *string                `json:"run_id"`
	DeviceID      string                 `json:"device_id"`
	DeviceType    string                 `json:"device_type"`
	EventTime     string                 `json:"event_time"`
	Seq           *int                   `json:"seq"`
	Tags          map[string]string      `json:"tags"`
	Data          map[string]json.Number `json:"data"`
}

type Envelope struct {
	SchemaVersion int               `json:"schema_version"`
	EventID       string            `json:"event_id"`
	Kind          string            `json:"kind"`
	TenantID      string            `json:"tenant_id"`
	RunID         *string           `json:"run_id"`
	DeviceID      string            `json:"device_id"`
	DeviceType    string            `json:"device_type"`
	EventTime     string            `json:"event_time"`
	IngestTime    string            `json:"ingest_time"`
	Seq           *int              `json:"seq,omitempty"`
	Tags          map[string]string `json:"tags,omitempty"`
	Data          map[string]any    `json:"data"`
}
