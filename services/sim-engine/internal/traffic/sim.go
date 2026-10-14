package traffic

import (
	"context"
	"math"
	"math/rand"
	"sync/atomic"
	"time"

	"fmt"

	"github.com/google/uuid"
)

// Emitter sends one traffic event to ingestion.
type Emitter func(clientID string, seq int, data map[string]any) error

// Run simulates one traffic profile until ctx is done or deadline passes.
func Run(
	ctx context.Context,
	p Profile,
	seed int64,
	start time.Time,
	deadline time.Time,
	scaleMult *atomic.Uint64,
	emit Emitter,
) {
	rng := rand.New(rand.NewSource(seed))
	seq := 0
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}
		now := time.Now()
		if now.After(deadline) {
			return
		}
		virtual := start.Add(now.Sub(start))
		mult := rateMultiplier(p.Pattern, virtual, seed)
		scale := 1.0
		if scaleMult != nil {
			scale = math.Float64frombits(scaleMult.Load())
		}
		rate := p.RatePerSec * mult * scale
		if rate <= 0 {
			rate = 0.01
		}
		wait := poissonWait(rng, rate)
		timer := time.NewTimer(wait)
		select {
		case <-ctx.Done():
			timer.Stop()
			return
		case <-timer.C:
		}
		if time.Now().After(deadline) {
			return
		}
		clientID := fmt.Sprintf("client-%08x", rng.Uint32())
		reqCount := int(sampleDistribution(rng, p.SessionReq))
		if reqCount < 1 {
			reqCount = 1
		}
		for i := 0; i < reqCount; i++ {
			flow := p.pickFlow(rng)
			for _, step := range flow.Steps {
				latency := sampleDistribution(rng, step.LatencyMs)
				bytes := int64(sampleDistribution(rng, step.Bytes))
				status := 200
				if rng.Float64() < step.ErrorRate {
					status = 500
				}
				region := p.pickRegion(rng)
				data := map[string]any{
					"session_id":  uuid.NewString(),
					"client_id":   clientID,
					"flow":        flow.Name,
					"method":      step.Method,
					"path":        step.Path,
					"status":      status,
					"latency_ms":  latency,
					"bytes":       bytes,
					"region":      region,
				}
				if err := emit(clientID, seq, data); err != nil {
					return
				}
				seq++
			}
			if i+1 < reqCount {
				think := time.Duration(sampleDistribution(rng, p.ThinkTime)) * time.Millisecond
				if think > 0 {
					select {
					case <-ctx.Done():
						return
					case <-time.After(think):
					}
				}
			}
		}
	}
}

func poissonWait(rng *rand.Rand, rate float64) time.Duration {
	u := rng.Float64()
	if u <= 0 {
		u = 1e-9
	}
	sec := -math.Log(u) / rate
	return time.Duration(sec * float64(time.Second))
}

// ScaleMultiplier returns atomic storage for profile rate multiplier (float64 bits).
func ScaleMultiplier(initial float64) *atomic.Uint64 {
	var u atomic.Uint64
	u.Store(math.Float64bits(initial))
	return &u
}

func SetScale(u *atomic.Uint64, v float64) {
	if u != nil {
		u.Store(math.Float64bits(v))
	}
}

