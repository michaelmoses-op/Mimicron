import { Kafka } from "kafkajs";

const brokers = (process.env.KAFKA_BROKERS ?? "localhost:19092").split(",");

export type StreamEvent = {
  tenantId: string;
  kind: "telemetry" | "anomaly";
  payload: unknown;
  offset: string;
};

type Listener = (ev: StreamEvent) => void;

const listeners = new Set<Listener>();

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function fanOut(ev: StreamEvent) {
  for (const l of listeners) l(ev);
}

export async function startKafkaConsumer(): Promise<void> {
  const kafka = new Kafka({ brokers, clientId: "stream-gateway" });
  const consumer = kafka.consumer({ groupId: "stream-gateway-fanout" });
  await consumer.connect();
  await consumer.subscribe({ topic: "telemetry.processed", fromBeginning: false });
  await consumer.run({
    eachMessage: async ({ message, partition, topic }) => {
      if (!message.value) return;
      const payload = JSON.parse(message.value.toString()) as { tenant_id?: string };
      const headers = message.headers ?? {};
      const tenant = headers.tenant_id?.toString() ?? payload.tenant_id ?? "";
      fanOut({
        tenantId: tenant,
        kind: "telemetry",
        payload,
        offset: `${topic}:${partition}:${message.offset}`,
      });
    },
  });
}
