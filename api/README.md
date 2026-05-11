# Student Platform API — Infrastructure Foundation

Production-oriented foundation for a secure academic enrollment and performance tracking system. This repository intentionally stops at infrastructure: database schema skeletons, observability plumbing, Docker topology, and operational endpoints—no authentication flows, grade workflows, or UI.

## Architecture Overview

- **Layered layout**: HTTP adapters (`app/api`) stay thin; configuration (`app/core`), persistence (`app/db`, `app/models`, `app/repositories`), cross-cutting middleware/logging/metrics, and future domain services (`app/services`) remain isolated for scaling teams and responsibilities.
- **Async-first I/O**: FastAPI runs with SQLAlchemy 2.0 async sessions (`asyncpg`) and Redis async clients to avoid blocking the event loop under concurrent academic workloads.
- **Explicit configuration**: `pydantic-settings` pulls strictly from environment variables (plus optional `.env` during development). Secrets never ship inside the image—Compose injects them at runtime.
- **Defense in depth**: Trusted hosts, optional CORS, request correlation IDs, structured JSON logs to stdout (Docker-friendly), payload size limits, and hardened defaults (`APP_DEBUG=false` enforcement when `APP_ENV=production`).
- **Observability**: Prometheus scrapes FastAPI metrics; Grafana provisions Prometheus automatically; Logstash accepts JSON logs over HTTP and forwards them into Elasticsearch for Kibana exploration.

## Prerequisites

- Docker Engine 24+ with Compose v2
- Python 3.12 (for local execution outside Docker)

## Quick Start (Docker Compose)

1. **Optional:** copy `.env.example` to `.env` and adjust secrets. If you skip this, Compose supplies **development defaults** for Postgres, Redis, API secrets, Grafana admin, and trusted hosts so `docker compose up --build` works immediately (override for production).
2. Build and start the stack:

```powershell
docker compose up --build
```

3. Verify the API:

- Swagger UI: `http://localhost:8000/api/v1/docs`
- Liveness: `GET http://localhost:8000/api/v1/health/live`
- Readiness (PostgreSQL + Redis): `GET http://localhost:8000/api/v1/health/ready`
- Prometheus metrics: `GET http://localhost:8000/metrics`

4. Observability UIs:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin credentials from `.env`)
- Kibana: `http://localhost:5601`

The API container runs `alembic upgrade head` before starting Uvicorn, ensuring migrations apply automatically.

### Optional Log Shipping

Set `LOG_SHIP_LOGSTASH=true` and ensure `LOGSTASH_HTTP_ENDPOINT` targets the Logstash HTTP input (defaults to `http://logstash:5044/` inside Compose). Logs remain on stdout regardless—shipping is additive.

### Reverse Proxy (Optional)

An example NGINX configuration lives in `infra/nginx/nginx.conf`. Wire it into Compose when you need TLS termination or edge rate limiting.

## Local Development (Without Docker)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
$env:APP_SECRET_KEY = "<32+ chars>"
$env:DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/db"
$env:REDIS_URL = "redis://localhost:6379/0"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run migrations manually when PostgreSQL is reachable:

```powershell
alembic upgrade head
```

## Quality Gates

```powershell
pip install -e ".[dev]"
pytest
```

## Elasticsearch Host Settings (Linux/macOS)

Elasticsearch containers require sufficient virtual memory maps on Linux hosts:

```bash
sudo sysctl -w vm.max_map_count=262144
```

Windows Docker Desktop typically abstracts this; apply when deploying to bare-metal Linux.

## Project Layout

```
app/
  api/              # Routers, dependencies, exception handlers
  core/             # Settings, lifespan, Redis helpers
  db/               # Async engine/session/base metadata
  logging/          # Structlog configuration and helpers
  metrics/          # Prometheus instrumentation
  middleware/       # Request ID, access logs, payload limits
  models/           # SQLAlchemy entities (schema-only)
  repositories/     # Shared repository primitives
  schemas/          # Pydantic DTO foundations
  services/         # Reserved for future orchestration logic
  utils/            # Shared helpers
  tests/            # Automated tests
infra/
  grafana/          # Datasource provisioning
  logstash/         # Pipeline + Logstash settings
  prometheus/       # Scrape configuration
  nginx/            # Sample reverse proxy configuration
alembic/            # Async Alembic migrations
scripts/            # Container entrypoints
```

## Security Notes

- Rotate secrets regularly and store production secrets in a vault/KMS—not in Git.
- Tune `REQUEST_MAX_BODY_BYTES`, `API_ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS` per environment.
- ELK components ship with security features disabled for local foundation work—**enable Elastic Stack security before any real deployment**.
