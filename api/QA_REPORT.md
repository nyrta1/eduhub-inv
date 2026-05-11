# QA report — Stage 5

## Executive summary

The repository now includes a **layered test architecture** (unit / security / integration), **observability checks** (health, metrics, security headers), **CI/CD validation** (lint, typecheck, coverage gate, integration services, static analysis, Docker build, Alembic), and **performance tooling** (k6 + Locust stubs).

## Test inventory (automated)

| Suite | Location | Pass criteria |
|-------|----------|----------------|
| Unit | `tests/unit/` | Deterministic assertions; no network |
| Security-focused | `tests/security/` | Abuse-resistant helpers behave |
| Integration | `tests/integration/` | HTTP 2xx on health/auth flow when `RUN_INTEGRATION=1` |
| Performance | `tests/performance/` | k6 thresholds optional run |

## Pass/fail matrix (design intent)

| Scenario | Expected | Evidence |
|----------|----------|----------|
| Registration + login + `/auth/me` | 201 / 200 / 200 | `test_auth_flow.py` |
| Readiness (DB+Redis) | 200 `ready` | `test_health_observability.py` |
| Prometheus scrape path | 200 body non-empty | `test_health_observability.py` |
| Security headers | CSP, XFO, nosniff present | `test_security_headers.py` |
| JWT tamper / expiry | `TokenValidationError` | `test_jwt_tokens.py` |
| Password hash verify | verify fails on wrong password | `test_password_hashing.py` |
| Rate limit increment | raises after threshold | `test_rate_limit_engine.py` |
| GPA weighted math | Decimal quantization | `test_gpa.py` |
| RBAC permission maps | teacher ≠ dean privileges | `test_permissions_role_maps.py` |

## Residual gaps (honest)

- **Academic CRUD IDOR matrix**: covered at **permission-unit** level; full grade/enrollment IDOR requires seeded academic fixtures (future expansion).
- **Brute-force Redis replay**: auth rate limits exercised via **mock Redis** for sliding window math; full Redis integration is implicit via login path in integration tests.
- **Coverage %**: global line coverage ≈38% with current narrow tests; **critical-path ratchet** documented in `TESTING.md`.

## Known limitations

- Integration runs **skip by default** to keep developer laptops lightweight.
- Locust not pinned in `pyproject.toml` (optional `pip install locust`).
- ELK/Grafana live validation remains **operational** (curl dashboards); automated probes would need stack-specific tokens.

## Sign-off recommendation

**Acceptable for academic defense / SDLC demo** when CI green + integration job demonstrates migrated schema + auth smoke.
