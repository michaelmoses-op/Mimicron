package usage

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

func IncrementIngested(ctx context.Context, rdb *redis.Client, tenantID uuid.UUID, count int) error {
	if count <= 0 {
		return nil
	}
	day := time.Now().UTC().Format("2006-01-02")
	key := fmt.Sprintf("usage:%s:ingested:%s", tenantID.String(), day)
	return rdb.IncrBy(ctx, key, int64(count)).Err()
}

func IncrementRejected(ctx context.Context, rdb *redis.Client, tenantID uuid.UUID, count int) error {
	if count <= 0 {
		return nil
	}
	day := time.Now().UTC().Format("2006-01-02")
	key := fmt.Sprintf("usage:%s:rejected:%s", tenantID.String(), day)
	return rdb.IncrBy(ctx, key, int64(count)).Err()
}
