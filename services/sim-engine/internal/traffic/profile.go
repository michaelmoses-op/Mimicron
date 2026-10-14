package traffic

import "math/rand"

type Step struct {
	Method    string
	Path      string
	LatencyMs map[string]any
	ErrorRate float64
	Bytes     map[string]any
}

type Flow struct {
	Name   string
	Weight float64
	Steps  []Step
}

type Profile struct {
	Name       string
	Process    string
	RatePerSec float64
	Pattern    map[string]any
	SessionReq map[string]any
	ThinkTime  map[string]any
	Regions    map[string]float64
	Flows      []Flow
}

func ParseProfile(raw map[string]any) Profile {
	p := Profile{Name: str(raw["name"])}
	if arr, ok := raw["arrival"].(map[string]any); ok {
		p.Process = str(arr["process"])
		p.RatePerSec = toFloat(arr["ratePerSec"])
		if pat, ok := arr["pattern"].(map[string]any); ok {
			p.Pattern = pat
		}
	}
	if sess, ok := raw["session"].(map[string]any); ok {
		if r, ok := sess["requests"].(map[string]any); ok {
			p.SessionReq = r
		}
		if t, ok := sess["thinkTime"].(map[string]any); ok {
			p.ThinkTime = t
		}
	}
	if regs, ok := raw["regions"].(map[string]any); ok {
		p.Regions = map[string]float64{}
		for k, v := range regs {
			p.Regions[k] = toFloat(v)
		}
	}
	for _, f := range sliceMaps(raw["flows"]) {
		flow := Flow{Name: str(f["name"]), Weight: toFloat(f["weight"])}
		for _, s := range sliceMaps(f["steps"]) {
			step := Step{
				Method: str(s["method"]),
				Path:   str(s["path"]),
				ErrorRate: toFloat(s["errorRate"]),
			}
			if lat, ok := s["latencyMs"].(map[string]any); ok {
				step.LatencyMs = lat
			}
			if b, ok := s["bytes"].(map[string]any); ok {
				step.Bytes = b
			}
			flow.Steps = append(flow.Steps, step)
		}
		p.Flows = append(p.Flows, flow)
	}
	if p.Process == "" {
		p.Process = "poisson"
	}
	if len(p.Regions) == 0 {
		p.Regions = map[string]float64{"default": 1}
	}
	return p
}

func str(v any) string {
	s, _ := v.(string)
	return s
}

func sliceMaps(v any) []map[string]any {
	arr, ok := v.([]any)
	if !ok {
		return nil
	}
	out := make([]map[string]any, 0, len(arr))
	for _, item := range arr {
		if m, ok := item.(map[string]any); ok {
			out = append(out, m)
		}
	}
	return out
}

func (p Profile) pickRegion(rng *rand.Rand) string {
	r := rng.Float64()
	var acc float64
	for name, w := range p.Regions {
		acc += w
		if r <= acc {
			return name
		}
	}
	for name := range p.Regions {
		return name
	}
	return "default"
}

func (p Profile) pickFlow(rng *rand.Rand) Flow {
	r := rng.Float64()
	var acc float64
	for _, f := range p.Flows {
		acc += f.Weight
		if r <= acc {
			return f
		}
	}
	if len(p.Flows) > 0 {
		return p.Flows[0]
	}
	return Flow{Name: "default", Steps: []Step{{Method: "GET", Path: "/"}}}
}