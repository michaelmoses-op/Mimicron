import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 2,
  duration: "10s",
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(99)<500"],
  },
};

const url = __ENV.INGEST_URL || "http://localhost:8081/v1/ingest";
const apiKey = __ENV.API_KEY;

export default function () {
  const now = new Date().toISOString();
  const payload = JSON.stringify({
    events: [
      {
        device_id: "k6-device-1",
        event_time: now,
        data: { temperature_c: 21.2 },
      },
    ],
  });
  const res = http.post(url, payload, {
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
    },
  });
  check(res, { "status is 202": (r) => r.status === 202 });
  sleep(0.2);
}
