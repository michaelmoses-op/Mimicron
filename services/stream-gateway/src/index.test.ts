import request from "supertest";
import { describe, expect, it } from "vitest";
import { createApp } from "./app.js";

describe("health", () => {
  it("healthz", async () => {
    const res = await request(createApp()).get("/healthz");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });
});
