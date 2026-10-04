#!/usr/bin/env sh
set -eu

BROKER="${KAFKA_BROKERS:-redpanda:9092}"

create_topic() {
  name="$1"
  partitions="$2"
  rpk topic create "$name" -p "$partitions" -r 1 -c retention.ms="$3" \
    --brokers "$BROKER" 2>/dev/null || true
}

# retention.ms: 7d = 604800000, 24h = 86400000
create_topic sim.commands 3 604800000
create_topic sim.events 3 604800000
create_topic telemetry.raw 12 86400000
create_topic telemetry.processed 12 86400000
create_topic anomalies.detected 6 604800000
create_topic telemetry.dlq 3 604800000

echo "Redpanda topics ready."
