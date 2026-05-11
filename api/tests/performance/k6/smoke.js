/**
 * k6 smoke / load script (Stage 5 performance validation).
 *
 * Install: https://k6.io/docs/getting-started/installation/
 * Run against running API:
 *   k6 run -e BASE_URL=http://localhost:8000 tests/performance/k6/smoke.js
 *
 * Thresholds assert latency and error budgets for demo / regression detection.
 */

import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "30s", target: 10 },
    { duration: "1m", target: 25 },
    { duration: "30s", target: 0 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<800"],
  },
};

const BASE = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  const res = http.get(`${BASE}/api/v1/health/live`);
  check(res, {
    "live 200": (r) => r.status === 200,
  });
  sleep(1);
}
