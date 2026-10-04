package ratelimit

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

// Token bucket per tenant (events/sec capacity = limit, burst = limit).
var tokenBucketScript = redis.NewScript(`
local key = KEYS[1]
local rate = tonumber(ARGV[1])
local now = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local burst = rate
local data = redis.call("HMGET", key, "tokens", "ts")
local tokens = tonumber(data[1])
local ts = tonumber(data[2])
if tokens == nil then
  tokens = burst
  ts = now
end
local delta = math.max(0, now - ts)
tokens = math.min(burst, tokens + delta * rate)
if tokens < requested then
  redis.call("HMSET", key, "tokens", tokens, "ts", now)
  redis.call("EXPIRE", key, 60)
  return {0, math.floor(tokens)}
end
tokens = tokens - requested
redis.call("HMSET", key, "tokens", tokens, "ts", now)
redis.call("EXPIRE", key, 60)
return {1, math.floor(tokens)}
`)

func AllowEvents(ctx context.Context, rdb *redis.Client, tenantID uuid.UUID, limit int, count int) (allowed bool, remaining int, err error) {
	if limit <= 0 {
		return true, limit, nil
	}
	key := fmt.Sprintf("rl:ingest:%s", tenantID.String())
	now := float64(time.Now().UnixNano()) / 1e9
	res, err := tokenBucketScript.Run(ctx, rdb, []string{key}, limit, now, count).Int64Slice()
	if err != nil {
		return false, 0, err
	}
	return res[0] == 1, int(res[1]), nil
}
