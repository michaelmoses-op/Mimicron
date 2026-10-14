package engine

import (
	"context"
	"sync/atomic"
	"time"

	"github.com/mimicron/mimicron/services/sim-engine/internal/traffic"
)

// watchScaleTraffic applies timeline scale_traffic actions to profile multipliers.
func watchScaleTraffic(
	ctx context.Context,
	spec map[string]any,
	runStart time.Time,
	scales map[string]*atomic.Uint64,
) {
	events, _ := spec["timeline"].([]any)
	for _, raw := range events {
		ev, _ := raw.(map[string]any)
		target, _ := ev["target"].(map[string]any)
		profileName, _ := target["traffic"].(string)
		if profileName == "" {
			continue
		}
		action, _ := ev["action"].(map[string]any)
		if action["type"] != "scale_traffic" {
			continue
		}
		atRaw, _ := ev["at"].(string)
		at := parseDuration(atRaw)
		mult := toFloat(action["multiplier"])
		if mult <= 0 {
			mult = 1
		}
		ramp := parseDuration(strDuration(action["ramp"]))
		hold := parseDuration(strDuration(action["hold"]))
		scale, ok := scales[profileName]
		if !ok {
			continue
		}
		go func(fireAt, ramp, hold time.Duration, mult float64) {
			wait := runStart.Add(fireAt).Sub(time.Now())
			if wait > 0 {
				timer := time.NewTimer(wait)
				select {
				case <-ctx.Done():
					timer.Stop()
					return
				case <-timer.C:
				}
			}
			if ramp <= 0 {
				traffic.SetScale(scale, mult)
				return
			}
			steps := 20
			stepDur := ramp / time.Duration(steps)
			if stepDur <= 0 {
				stepDur = time.Millisecond
			}
			for i := 1; i <= steps; i++ {
				select {
				case <-ctx.Done():
					return
				default:
				}
				frac := float64(i) / float64(steps)
				traffic.SetScale(scale, 1+frac*(mult-1))
				time.Sleep(stepDur)
			}
			if hold > 0 {
				select {
				case <-ctx.Done():
					return
				case <-time.After(hold):
				}
			}
			for i := steps; i >= 0; i-- {
				select {
				case <-ctx.Done():
					return
				default:
				}
				frac := float64(i) / float64(steps)
				traffic.SetScale(scale, 1+frac*(mult-1))
				time.Sleep(stepDur)
			}
		}(at, ramp, hold, mult)
	}
}

func strDuration(v any) string {
	s, _ := v.(string)
	return s
}
