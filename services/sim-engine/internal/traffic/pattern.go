package traffic

import (
	"math"
	"time"
)

// rateMultiplier applies flat, diurnal, or spiky patterns to base ratePerSec.
func rateMultiplier(pattern map[string]any, virtualTime time.Time, seed int64) float64 {
	if pattern == nil {
		return 1
	}
	typ, _ := pattern["type"].(string)
	switch typ {
	case "diurnal":
		peak := toFloat(pattern["peakHour"])
		amp := toFloat(pattern["amplitude"])
		if amp <= 0 {
			amp = 0.5
		}
		hour := float64(virtualTime.UTC().Hour()) + float64(virtualTime.UTC().Minute())/60
		phase := 2 * math.Pi * (hour-peak) / 24
		return 1 + amp*math.Cos(phase)
	case "spiky":
		// Deterministic spikes every ~7 minutes with short burst.
		slot := virtualTime.Unix() / 420
		inBurst := (virtualTime.Unix()+seed)%420 < 30
		if inBurst {
			return 1 + 4*math.Sin(float64(slot))
		}
		return 0.6
	default:
		return 1
	}
}
