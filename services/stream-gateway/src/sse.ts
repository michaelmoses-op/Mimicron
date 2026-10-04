import type { Request, Response } from "express";
import { subscribe, type StreamEvent } from "./consumer.js";

const MAX_CONNECTIONS = 20;
let connections = 0;

export function handleStream(req: Request, res: Response): void {
  if (connections >= MAX_CONNECTIONS) {
    res.status(429).json({ error: "too many connections" });
    return;
  }
  connections++;
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  const tenantFilter = (req as Request & { tenantId?: string }).tenantId;
  const runId = req.query.run_id as string | undefined;

  const unsubscribe = subscribe((ev: StreamEvent) => {
    if (tenantFilter && ev.tenantId && ev.tenantId !== tenantFilter) return;
    const body = ev.payload as { run_id?: string };
    if (runId && body.run_id !== runId) return;
    res.write(`id: ${ev.offset}\n`);
    res.write(`event: ${ev.kind}\n`);
    res.write(`data: ${JSON.stringify(ev.payload)}\n\n`);
  });

  const heartbeat = setInterval(() => {
    res.write(`event: heartbeat\ndata: {}\n\n`);
  }, 15000);

  req.on("close", () => {
    clearInterval(heartbeat);
    unsubscribe();
    connections--;
  });
}
