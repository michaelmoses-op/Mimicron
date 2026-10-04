package kafka

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/mimicron/mimicron/services/ingestion-gateway/internal/model"
)

type Producer struct {
	client *kgo.Client
	topic  string
}

func NewProducer(brokers, topic string) (*Producer, error) {
	cl, err := kgo.NewClient(
		kgo.SeedBrokers(brokers),
		kgo.AllowAutoTopicCreation(false),
	)
	if err != nil {
		return nil, err
	}
	return &Producer{client: cl, topic: topic}, nil
}

func (p *Producer) Close() {
	p.client.Close()
}

func (p *Producer) Publish(ctx context.Context, tenantID string, env model.Envelope) error {
	key := fmt.Sprintf("%s:%s", tenantID, env.DeviceID)
	body, err := json.Marshal(env)
	if err != nil {
		return err
	}
	record := &kgo.Record{
		Topic: p.topic,
		Key:   []byte(key),
		Value: body,
		Headers: []kgo.RecordHeader{
			{Key: "tenant_id", Value: []byte(tenantID)},
			{Key: "schema_version", Value: []byte("1")},
		},
	}
	return p.client.ProduceSync(ctx, record).FirstErr()
}
