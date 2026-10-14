package traffic

import (
	"math/rand"
	"testing"
	"time"
)

func TestRateMultiplierDiurnalBounded(t *testing.T) {
	pattern := map[string]any{"type": "diurnal", "peakHour": 14.0, "amplitude": 0.6}
	for h := 0; h < 24; h++ {
		m := rateMultiplier(pattern, mustHour(h), 1)
		if m < 0.4 || m > 1.6 {
			t.Fatalf("hour %d multiplier %v out of range", h, m)
		}
	}
}

func TestSampleGeometricMean(t *testing.T) {
	rng := rand.New(rand.NewSource(42))
	var sum float64
	n := 5000
	for i := 0; i < n; i++ {
		sum += float64(sampleGeometric(rng, 1.0/6.0))
	}
	mean := sum / float64(n)
	if mean < 4 || mean > 8 {
		t.Fatalf("expected mean ~6, got %v", mean)
	}
}

func mustHour(h int) time.Time {
	return timeFromParts(2024, 1, 1, h, 0)
}

func timeFromParts(y, m, d, h, min int) time.Time {
	return time.Date(y, time.Month(m), d, h, min, 0, 0, time.UTC)
}
