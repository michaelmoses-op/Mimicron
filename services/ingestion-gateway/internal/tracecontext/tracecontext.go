package tracecontext

import (
	"context"
	"net/http"

	"github.com/twmb/franz-go/pkg/kgo"
)

const header = "traceparent"

// FromRequest returns W3C traceparent from the HTTP request, if present.
func FromRequest(r *http.Request) string {
	return r.Header.Get(header)
}

// KafkaHeaders appends traceparent to Kafka record headers when set in ctx.
func KafkaHeaders(ctx context.Context, base []kgo.RecordHeader) []kgo.RecordHeader {
	tp, _ := ctx.Value(traceKey{}).(string)
	if tp == "" {
		return base
	}
	out := make([]kgo.RecordHeader, 0, len(base)+1)
	out = append(out, base...)
	out = append(out, kgo.RecordHeader{Key: header, Value: []byte(tp)})
	return out
}

type traceKey struct{}

// WithTraceparent stores traceparent on context for downstream publish.
func WithTraceparent(ctx context.Context, tp string) context.Context {
	if tp == "" {
		return ctx
	}
	return context.WithValue(ctx, traceKey{}, tp)
}
