package engine

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"math"
	"math/rand"
	"net/http"
	"sync"
	"time"

	"sync/atomic"

	"github.com/google/uuid"
	"github.com/twmb/franz-go/pkg/kgo"

	"github.com/mimicron/mimicron/services/sim-engine/internal/traffic"
)

type Runtime struct {
	logger   *slog.Logger
	brokers  string
	consumer *kgo.Client
	producer *kgo.Client
	ingest   string
	mu       sync.Mutex
	runs     map[string]context.CancelFunc
}

func New(logger *slog.Logger, brokers, ingestURL string) (*Runtime, error) {
	consumer, err := kgo.NewClient(
		kgo.SeedBrokers(brokers),
		kgo.ConsumerGroup("sim-engine"),
		kgo.ConsumeTopics("sim.commands"),
	)
	if err != nil {
		return nil, err
	}
	producer, err := kgo.NewClient(kgo.SeedBrokers(brokers))
	if err != nil {
		consumer.Close()
		return nil, err
	}
	return &Runtime{
		logger: logger, brokers: brokers, consumer: consumer, producer: producer,
		ingest: ingestURL, runs: map[string]context.CancelFunc{},
	}, nil
}

func (r *Runtime) Close() {
	r.consumer.Close()
	r.producer.Close()
}

func (r *Runtime) Run(ctx context.Context) {
	for {
		fetches := r.consumer.PollFetches(ctx)
		if fetches.IsClientClosed() {
			return
		}
		fetches.EachRecord(func(rec *kgo.Record) {
			var cmd map[string]any
			if json.Unmarshal(rec.Value, &cmd) != nil {
				return
			}
			action, _ := cmd["action"].(string)
			runID, _ := cmd["run_id"].(string)
			switch action {
			case "start":
				r.startRun(cmd)
			case "stop", "pause", "resume":
				r.mu.Lock()
				cancel, ok := r.runs[runID]
				r.mu.Unlock()
				if ok && action == "stop" {
					cancel()
				}
			}
		})
	}
}

func (r *Runtime) startRun(cmd map[string]any) {
	runID, _ := cmd["run_id"].(string)
	runToken, _ := cmd["run_token"].(string)
	scenario, _ := cmd["scenario"].(map[string]any)
	seedF, _ := cmd["seed"].(float64)
	seed := int64(seedF)
	mode, _ := cmd["mode"].(string)
	speed, _ := cmd["speed"].(float64)
	if speed <= 0 {
		speed = 1
	}
	ingestURL, _ := cmd["ingestion_url"].(string)
	if ingestURL != "" {
		r.ingest = ingestURL
	}
	ctx, cancel := context.WithCancel(context.Background())
	r.mu.Lock()
	if old, ok := r.runs[runID]; ok {
		old()
	}
	r.runs[runID] = cancel
	r.mu.Unlock()
	go r.executeRun(ctx, runID, runToken, scenario, seed, mode, speed)
}

func (r *Runtime) executeRun(ctx context.Context, runID, runToken string, scenario map[string]any, seed int64, mode string, speed float64) {
	defer func() {
		r.mu.Lock()
		delete(r.runs, runID)
		r.mu.Unlock()
	}()
	r.publishEvent(map[string]any{"type": "run.started", "run_id": runID})
	spec, _ := scenario["spec"].(map[string]any)
	duration := time.Hour
	if timeSpec, ok := spec["time"].(map[string]any); ok {
		if raw, ok := timeSpec["duration"].(string); ok {
			duration = parseDuration(raw)
		}
	}
	if mode == "accelerated" {
		duration = time.Duration(float64(duration) / speed)
	}
	if duration > 30*time.Minute {
		duration = 5 * time.Minute
	}
	deadline := time.Now().Add(duration)
	runStart := time.Now()
	deviceTypes, _ := spec["deviceTypes"].(map[string]any)
	fleets, _ := spec["fleets"].([]any)
	trafficProfiles, _ := spec["traffic"].([]any)
	scales := map[string]*atomic.Uint64{}
	for _, tp := range trafficProfiles {
		raw, _ := tp.(map[string]any)
		name, _ := raw["name"].(string)
		if name != "" {
			scales[name] = traffic.ScaleMultiplier(1)
		}
	}
	watchScaleTraffic(ctx, spec, runStart, scales)
	var wg sync.WaitGroup
	events := int64(0)
	var eventsMu sync.Mutex
	for i, tp := range trafficProfiles {
		raw, _ := tp.(map[string]any)
		profile := traffic.ParseProfile(raw)
		scale := scales[profile.Name]
		profileSeed := seed + int64(i+1)*7919
		wg.Add(1)
		go func(p traffic.Profile, scale *atomic.Uint64, profileSeed int64) {
			defer wg.Done()
			emit := func(clientID string, seq int, data map[string]any) error {
				err := r.emitEvent(runToken, runID, clientID, "traffic", "", seq, data)
				if err == nil {
					eventsMu.Lock()
					events++
					eventsMu.Unlock()
				}
				return err
			}
			traffic.Run(ctx, p, profileSeed, runStart, deadline, scale, emit)
		}(profile, scale, profileSeed)
	}
	for _, f := range fleets {
		fleet, _ := f.(map[string]any)
		count := int(toFloat(fleet["count"]))
		dtName, _ := fleet["deviceType"].(string)
		dt, _ := deviceTypes[dtName].(map[string]any)
		interval := parseDuration(dt["emit"].(map[string]any)["interval"].(string))
		metrics, _ := dt["metrics"].(map[string]any)
		idPattern, _ := fleet["idPattern"].(string)
		for i := 0; i < count; i++ {
			i := i
			wg.Add(1)
			go func() {
				defer wg.Done()
				devID := formatDeviceID(idPattern, i)
				rng := rand.New(rand.NewSource(seed + int64(i)*9973))
				ticker := time.NewTicker(interval)
				defer ticker.Stop()
				seq := 0
				for {
					select {
					case <-ctx.Done():
					 return
					case t := <-ticker.C:
						if time.Now().After(deadline) {
							return
						}
						data := map[string]any{}
						for name, m := range metrics {
							metric, _ := m.(map[string]any)
							gen, _ := metric["generator"].(map[string]any)
							data[name] = evalGenerator(gen, rng, t)
						}
						if err := r.emitEvent(runToken, runID, devID, "telemetry", dtName, seq, data); err == nil {
							eventsMu.Lock()
							events++
							eventsMu.Unlock()
						}
						seq++
					}
				}
			}()
		}
	}
	wg.Wait()
	r.publishEvent(map[string]any{"type": "run.completed", "run_id": runID, "events_emitted": events})
}

func (r *Runtime) emitEvent(
	token, runID, deviceID, kind, deviceType string,
	seq int,
	data map[string]any,
) error {
	payload := map[string]any{
		"events": []map[string]any{{
			"event_id":    uuid.NewString(),
			"kind":        kind,
			"run_id":      runID,
			"device_id":   deviceID,
			"device_type": deviceType,
			"event_time":  time.Now().UTC().Format(time.RFC3339Nano),
			"seq":         seq,
			"data":        data,
		}},
	}
	body, _ := json.Marshal(payload)
	req, err := http.NewRequest(http.MethodPost, r.ingest+"/v1/ingest", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	_, _ = io.ReadAll(resp.Body)
	if resp.StatusCode >= 300 {
		return fmt.Errorf("ingest status %d", resp.StatusCode)
	}
	return nil
}

func (r *Runtime) publishEvent(ev map[string]any) {
	body, _ := json.Marshal(ev)
	r.producer.ProduceSync(context.Background(), &kgo.Record{Topic: "sim.events", Value: body, Key: []byte(ev["run_id"].(string))})
}

func formatDeviceID(_ string, index int) string {
	return fmt.Sprintf("dev-%04d", index)
}

func parseDuration(raw string) time.Duration {
	d, err := time.ParseDuration(raw)
	if err != nil {
		return time.Hour
	}
	return d
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

func evalGenerator(gen map[string]any, rng *rand.Rand, t time.Time) float64 {
	typ, _ := gen["type"].(string)
	switch typ {
	case "constant":
		return toFloat(gen["value"])
	case "sine":
		base := toFloat(gen["baseline"])
		amp := toFloat(gen["amplitude"])
		period := parseDuration(gen["period"].(string))
		phase := 0.0
		if p, ok := gen["phase"].(float64); ok {
			phase = p
		}
		x := 2 * math.Pi * (float64(t.UnixNano())/float64(period) + phase)
		return base + amp*math.Sin(x)
	case "random_walk":
		return toFloat(gen["start"]) + rng.NormFloat64()*toFloat(gen["step"])
	default:
		return rng.Float64() * 100
	}
}
