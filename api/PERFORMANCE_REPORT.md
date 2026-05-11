# Performance validation — Stage 5

## Tooling

| Tool | Path | Purpose |
|------|------|---------|
| k6 | `tests/performance/k6/smoke.js` | Ramp VUs, threshold on `/api/v1/health/live` |
| Locust | `tests/performance/locustfile.py` | Optional interactive load (`pip install locust`) |

## Default thresholds (k6)

- **http_req_failed** `rate < 0.05`
- **http_req_duration** `p(95) < 800ms`

Tune per environment; authenticate scenarios require scripting token acquisition.

## Baseline procedure

1. Deploy API + dependencies (Compose stack).
2. `k6 run -e BASE_URL=http://localhost:8000 tests/performance/k6/smoke.js`
3. Capture stdout + Prometheus scrape during run.

## Evidence expectations

- Grafana panels show latency & error rate during test window.
- Alert rules (`infra/prometheus/alerts/security.yml`) remain unrelated to pure throughput—add horizontal scaling alerts separately.

## Residual risks

- Smoke test hits **liveness only**; authenticated endpoints need dedicated scenarios.
- Load generation against shared dev clusters may violate fair-use—use isolated perf env.
