use anyhow::{Context, Result};
use rdkafka::config::ClientConfig;
use rdkafka::consumer::{Consumer, StreamConsumer};
use rdkafka::message::Message;
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::util::Timeout;
use std::time::Duration;
use tracing::{error, info, warn};

use crate::config::Config;
use crate::dedupe::Dedupe;
use crate::envelope::Envelope;
use crate::sink::Sink;

pub async fn run(cfg: Config, sink: Sink) -> Result<()> {
    let consumer: StreamConsumer = ClientConfig::new()
        .set("bootstrap.servers", &cfg.kafka_brokers)
        .set("group.id", &cfg.group_id)
        .set("enable.auto.commit", "false")
        .set("auto.offset.reset", "earliest")
        .create()
        .context("create consumer")?;

    consumer
        .subscribe(&[&cfg.raw_topic])
        .context("subscribe raw topic")?;

    let producer: FutureProducer = ClientConfig::new()
        .set("bootstrap.servers", &cfg.kafka_brokers)
        .set("message.timeout.ms", "5000")
        .create()
        .context("create producer")?;

    let mut dedupe = Dedupe::new(50_000);
    loop {
        let mut batch = Vec::new();
        let deadline = tokio::time::Instant::now() + Duration::from_millis(500);
        while batch.len() < cfg.batch_size && tokio::time::Instant::now() < deadline {
            match tokio::time::timeout(Duration::from_millis(100), consumer.recv()).await {
                Ok(Ok(msg)) => {
                    let payload = msg.payload().context("empty payload")?;
                    match serde_json::from_slice::<Envelope>(payload) {
                        Ok(env) => {
                            if dedupe.check(&env.event_id) {
                                batch.push((msg, env));
                            }
                        }
                        Err(err) => {
                            warn!(?err, "invalid envelope");
                            send_dlq(&producer, &cfg.dlq_topic, payload, "validation").await;
                        }
                    }
                }
                Ok(Err(err)) => error!(?err, "kafka recv"),
                Err(_) => break,
            }
        }
        if batch.is_empty() {
            continue;
        }
        let events: Vec<Envelope> = batch.iter().map(|(_, e)| e.clone()).collect();
        if let Err(err) = sink.write_batch(&events).await {
            error!(?err, "sink failed");
            for (msg, _) in &batch {
                if let Some(p) = msg.payload() {
                    send_dlq(&producer, &cfg.dlq_topic, p, "sink_error").await;
                }
            }
            continue;
        }
        for (_, env) in &batch {
            if let Ok(body) = serde_json::to_vec(env) {
                let key = format!("{}:{}", env.tenant_id, env.device_id);
                let _ = producer
                    .send(
                        FutureRecord::to(&cfg.processed_topic)
                            . key(&key)
                            .payload(&body),
                        Timeout::After(Duration::from_secs(3)),
                    )
                    .await;
            }
        }
        let mut tpl = rdkafka::TopicPartitionList::new();
        for (msg, _) in batch {
            tpl.add_partition_offset(
                msg.topic(),
                msg.partition(),
                rdkafka::Offset::Offset(msg.offset() + 1),
            )?;
        }
        if let Err(err) = consumer.commit(&tpl, rdkafka::consumer::CommitMode::Async) {
            error!(?err, "commit failed");
        } else {
            info!(count = tpl.count(), "batch committed");
        }
    }
}

async fn send_dlq(producer: &FutureProducer, topic: &str, payload: &[u8], _reason: &str) {
    let _ = producer
        .send(
            FutureRecord::to(topic).payload(payload),
            Timeout::After(Duration::from_secs(3)),
        )
        .await;
}
