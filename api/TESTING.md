# Testing strategy (Stage 5)

## Objectives

- **Unit**: deterministic logic (GPA, JWT crypto, Argon2, Redis sliding-window math, schema validation, RBAC permission maps, audit scrubbing) without external services.
- **Security** (focused): SSRF URL gate, SQL identifier ordering, sensitive-route classification, validator edge cases—aligned with OWASP abuse scenarios.
- **Integration** (gated): full FastAPI stack over ASGI with **real PostgreSQL + Redis**, Alembic migrations, and HTTP semantics (`httpx.AsyncClient`). Disabled locally unless `RUN_INTEGRATION=1` (see `docker-compose.test.yml`).
- **Performance**: k6 smoke (`tests/performance/k6/smoke.js`) and optional Locust (`tests/performance/locustfile.py`) for throughput/latency budgets—run against a dedicated environment.

## Running tests

```bash
# Default (unit + security; integration skipped)
pytest tests -q

# Integration — start DB/Redis (see docker-compose.test.yml), export env, then:
set RUN_INTEGRATION=1   # Windows PowerShell: $env:RUN_INTEGRATION=1
pytest tests/integration -m integration -v

# Coverage (matches CI gate)
pytest tests/unit tests/security --cov=app --cov-report=term-missing
```

## Environment variables (integration)

| Variable | Purpose |
|----------|---------|
| `RUN_INTEGRATION` | Must be `1` to run `@pytest.mark.integration` tests |
| `DATABASE_URL` | Async SQLAlchemy URL (`postgresql+asyncpg://…`) |
| `REDIS_URL` | Redis for auth rate limits + sessions |
| `APP_SECRET_KEY` | ≥32 chars |
| `API_ALLOWED_HOSTS` | Must include `test` (ASGI client uses host `test`) |

## Markers

- `integration` — requires migrated DB + Redis.
- `slow` — reserved for load scripts / long scenarios.

## Coverage policy

- Line + branch coverage measured on `app/` (see `[tool.coverage]` in `pyproject.toml`).
- **fail_under** is set to a baseline that passes today; **raise gradually** toward **≥85% on critical packages** (`app/services`, `app/auth`, `app/security`) as scenarios grow.

## Lint / types

- **Ruff**: enforced on the **test tree** in CI (application code left unchanged in Stage 5 to avoid churn).
- **mypy**: scoped to `app/academic/gpa.py`, `app/security/safe_query.py`, `app/security/validators.py` for stable typing evidence.

## Evidence for audits

- CI workflow `.github/workflows/ci.yml`: lint, mypy, unit+coverage, integration, bandit, pip-audit, Docker build, migration check.
- Security workflow `.github/workflows/security.yml`: supplemental dependency audit path.
