# Performance validation

## k6 (`tests/performance/k6/smoke.js`)

Ramp-up scenario against `/api/v1/health/live` with **p95 latency < 800ms** and **error rate < 5%**.

```bash
k6 run -e BASE_URL=http://localhost:8000 tests/performance/k6/smoke.js
```

Authenticated endpoints require scripting JWT acquisition; extend this file for login/grade scenarios behind a dedicated perf environment.

## Locust (optional)

For interactive ramp testing with Python:

```bash
pip install locust
locust -f tests/performance/locustfile.py --host http://localhost:8000
```

See `locustfile.py` if present in repository.
