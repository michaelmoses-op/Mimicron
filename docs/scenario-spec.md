# Scenario Specification (v1, draft)

A **scenario** is a declarative YAML (or JSON) document describing *what to simulate*. Machine-readable schema: [`contracts/scenario/scenario.schema.json`](../contracts/scenario/scenario.schema.json). Full example: [`scenarios/examples/smart-building-heatwave.yaml`](../scenarios/examples/smart-building-heatwave.yaml).

**Determinism guarantee:** same scenario + same `spec.seed` + same virtual start time produces the same sequence of events (values, timing, and IDs, excluding `ingest_time`). Every random draw must come from a per-device PRNG derived from `hash(seed, fleet, device_index)`. Never use global RNG or wall-clock for values.

## Top-level shape

```yaml
apiVersion: mimicron/v1
kind: Scenario
metadata: { name, description?, tags? }
spec:
  seed: int
  time: {...}
  defaults: {...}
  deviceTypes: { <name>: {...} }
  fleets: [ {...} ]
  traffic: [ {...} ]
  timeline: [ {...} ]
  chaos: [ {...} ]        # reserved, implemented in a later milestone
```

## `spec.time`

| Field | Type | Meaning |
|---|---|---|
| `mode` | `realtime` \| `accelerated` \| `backfill` | `realtime`: virtual time = wall time. `accelerated`: virtual time runs `speed`x faster, events emitted at the compressed pace. `backfill`: emit as fast as the pipeline accepts, with historical `event_time`s ending at `start + duration`. |
| `speed` | number >= 1 | only for `accelerated` |
| `start` | RFC3339 | virtual start; default = now. Required for `backfill`. |
| `duration` | duration | total virtual run length (subject to tenant quota) |

Durations use `ms|s|m|h|d` suffixes (`500ms`, `10s`, `2h`).

## `spec.deviceTypes.<name>`

```yaml
schemaVersion: 1
emit: { interval: 10s, jitter: 0.1 }     # jitter = +/- fraction of interval
metrics:
  <metric_name>:
    unit: C
    generator: { type: ..., ... }        # see generators
    noise: { type: gaussian, stddev: 0.15 }   # optional, added to generator output
    bounds: [min, max]                   # optional clamp
    precision: 2                         # optional decimal places
    emitEvery: 1                         # optional: include this metric every Nth tick
```

### Generators

| `type` | Params | Behavior |
|---|---|---|
| `constant` | `value` | fixed |
| `sine` | `baseline, amplitude, period, phase?` | periodic (use `24h` for diurnal) |
| `random_walk` | `start, step, min?, max?` | bounded drift |
| `gaussian` | `mean, stddev` | iid samples |
| `uniform` | `min, max` | iid samples |
| `linear` | `start, slopePerHour, min?, max?` | e.g., battery drain |
| `sawtooth` | `min, max, period` | ramp and reset |
| `steps` | `levels: [{at, value}]` | piecewise constant by virtual offset |
| `csv_replay` *(reserved)* | `file, column, loop` | later |

## `spec.fleets[]`

```yaml
- name: floor-1                    # unique
  deviceType: thermostat
  count: 250                       # subject to quota
  idPattern: "therm-1-{index:04d}" # {index} zero-based, supports Python/Go-style width formatting
  tags: { site: hq, floor: "1" }   # attached to every event
  variance:                        # per-device deviation of generator params
    - { metric: temperature_c, param: baseline, distribution: normal, stddev: 1.0 }
  startOffset: { distribution: uniform, max: 10s }   # desync device clocks/ticks
  clockSkew: 0s                    # fixed skew applied to event_time (chaos later varies it)
```

## `spec.timeline[]` (scheduled events, offsets are virtual time from start)

```yaml
- at: 30m                    # or: every: 1h  (optionally with until:)
  name: heat-wave            # unique, shown in dashboard
  target:
    fleet: floor-1           # exactly one of: fleet | tags: {site: hq} | traffic: <profile name>
    percent: 100             # random subset by seeded draw (default 100)
  action: { type: ..., ... }
```

| `action.type` | Params | Notes |
|---|---|---|
| `adjust` | `metric, add? \| multiply?, ramp?, hold?` | ramp in, hold, ramp out |
| `set_state` | `online: bool, for?` | offline = no events emitted |
| `inject_anomaly` | `metric, kind: spike\|drift\|stuck\|dropout, magnitude?, duration` | **auto-emits a ground-truth label** to `sim.events` |
| `set_rate` | `interval` | change emit interval |
| `scale_traffic` | `profile, multiplier, ramp?, hold?` | for traffic simulator |

## `spec.traffic[]` (customer / network traffic simulator)

```yaml
- name: storefront
  arrival:
    process: poisson                 # poisson | constant
    ratePerSec: 20
    pattern: { type: diurnal, peakHour: 14, amplitude: 0.6 }   # also: flat | spiky
  session:
    requests: { distribution: geometric, mean: 6 }
    thinkTime: { distribution: lognormal, median: 2s, sigma: 0.5 }
  regions: { us-east: 0.6, eu-west: 0.4 }
  flows:
    - name: browse
      weight: 0.7
      steps:
        - { method: GET, path: /products, latencyMs: { distribution: lognormal, median: 80, sigma: 0.4 }, errorRate: 0.01, bytes: { distribution: constant, value: 18000 } }
```
Emits `kind: "traffic"` events. Stream-processor aggregates them into `traffic_rollups_10s`.

## `spec.chaos[]` (reserved for the chaos milestone; validate shape now, implement later)

```yaml
- name: flaky-network
  target: { fleet: floor-1, percent: 20 }
  window: { from: 20m, to: 50m }
  faults:
    - { type: drop, probability: 0.05 }
    - { type: duplicate, probability: 0.02 }
    - { type: delay, distribution: lognormal, median: 2s, sigma: 0.8 }   # produces late/out-of-order data
    - { type: clock_skew, offset: 90s }
    - { type: schema_drift, rename: { temperature_c: temp } }
    - { type: corrupt, probability: 0.01 }
```
When `ground truth` labeling is enabled, chaos faults are also reported as labels.

## Validation rules (implemented once as JSON Schema, then again as semantic checks in control-api)

Semantic checks beyond the JSON Schema (returned as a list of `{path, code, message}`):
1. Unique names across fleets, timeline events, traffic profiles, chaos rules
2. Every `deviceType` / `fleet` / `metric` referenced must exist
3. `sum(regions) == 1` and `sum(flow weights) == 1` (tolerance 1e-6)
4. Quota checks: total devices <= `max_devices`; `duration` <= `max_run_duration`; `emit.interval` >= tenant minimum; estimated events/sec <= `max_events_per_sec`
5. Timeline offsets within `duration`
6. `backfill` requires `start` in the past

The sim-engine re-validates independently (never trust the caller) and returns a structured error on `sim.events` (`run.failed`).

## Estimated load formula (shown in the dashboard before starting a run)

`events/sec = sum over fleets( count / interval ) + sum over traffic( ratePerSec x mean requests per session )`, multiplied by `speed` in `accelerated` mode.
