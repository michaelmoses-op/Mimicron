from __future__ import annotations

import json
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.core.config import settings

_producer: AIOKafkaProducer | None = None


async def start_kafka() -> None:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_brokers)
        await _producer.start()


async def stop_kafka() -> None:
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None


async def publish_sim_command(payload: dict[str, Any]) -> None:
    if _producer is None:
        await start_kafka()
    assert _producer is not None
    key = payload.get("run_id", "").encode()
    body = json.dumps(payload).encode()
    await _producer.send_and_wait("sim.commands", body, key=key)


def sim_events_consumer() -> AIOKafkaConsumer:
    return AIOKafkaConsumer(
        "sim.events",
        bootstrap_servers=settings.kafka_brokers,
        group_id="control-api-sim-events",
        enable_auto_commit=True,
        auto_offset_reset="earliest",
    )
