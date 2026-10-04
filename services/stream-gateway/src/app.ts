import express from "express";

export function createApp(): express.Express {
  const app = express();
  app.use((_req, res, next) => {
    res.setHeader("Access-Control-Allow-Origin", "*");
    next();
  });

  app.get("/healthz", (_req, res) => {
    res.json({ status: "ok" });
  });

  app.get("/readyz", (_req, res) => {
    res.json({ status: "ready" });
  });

  app.get("/metrics", (_req, res) => {
    res.type("text/plain").send("# TYPE up gauge\nup 1\n");
  });

  return app;
}
