package traffic

import (
	"math"
	"math/rand"
	"time"
)

func sampleDistribution(rng *rand.Rand, spec map[string]any) float64 {
	if spec == nil {
		return 0
	}
	typ, _ := spec["type"].(string)
	switch typ {
	case "constant":
		return toFloat(spec["value"])
	case "geometric":
		mean := toFloat(spec["mean"])
		if mean <= 0 {
			mean = 1
		}
		p := 1.0 / mean
		return float64(sampleGeometric(rng, p))
	case "lognormal":
		median := parseDurationMs(spec["median"])
		sigma := toFloat(spec["sigma"])
		if sigma <= 0 {
			sigma = 0.5
		}
		return sampleLognormal(rng, median, sigma)
	case "normal":
		return rng.NormFloat64()*toFloat(spec["stddev"]) + toFloat(spec["mean"])
	case "uniform":
		lo := toFloat(spec["min"])
		hi := toFloat(spec["max"])
		return lo + rng.Float64()*(hi-lo)
	default:
		return toFloat(spec["value"])
	}
}

func sampleGeometric(rng *rand.Rand, p float64) int {
	if p <= 0 {
		p = 0.5
	}
	return int(math.Floor(math.Log(1-rng.Float64()) / math.Log(1-p))) + 1
}

func sampleLognormal(rng *rand.Rand, median, sigma float64) float64 {
	if median <= 0 {
		median = 1
	}
	mu := math.Log(median)
	z := rng.NormFloat64()*sigma + mu
	return math.Exp(z)
}

func parseDurationMs(v any) float64 {
	switch t := v.(type) {
	case string:
		d, err := time.ParseDuration(t)
		if err != nil {
			return 0
		}
		return float64(d) / float64(time.Millisecond)
	case float64:
		return t
	default:
		return 0
	}
}

func toFloat(v any) float64 {
	switch t := v.(type) {
	case float64:
		return t
	case int:
		return float64(t)
	case int64:
		return float64(t)
	default:
		return 0
	}
}
