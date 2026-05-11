# Security validation — Stage 5 evidence pack

This document ties **automated tests** and **CI checks** to OWASP-oriented outcomes. Detailed controls remain in `SECURITY.md`.

## OWASP alignment checklist

| Control | Automated evidence | Manual / ops evidence |
|---------|-------------------|------------------------|
| A01 Broken access control | RBAC unit tests; integration auth smoke | Admin review of service-layer checks |
| A02 Cryptographic failures | JWT + Argon2 unit tests | TLS at reverse proxy |
| A03 Injection | `safe_query` / validator tests; schema rejects injection-like strings | DB permission review |
| A05 Misconfiguration | Integration security-header test; CI Docker build | Prod env audit |
| A06 Vulnerable components | `pip-audit` in CI | Dependabot / renovate |
| A07 Identification failures | JWT tamper/expiry tests; login/register integration | Account lockout monitoring |
| A09 Logging failures | Structured log fields via middleware (see ops) | ELK retention policies |
| A10 SSRF | `secure_http` URL gate tests | Outbound allow-lists in prod |

## Penetration-style scenarios (test mapping)

| Attack idea | Test / check |
|-------------|--------------|
| Token forgery | `test_decode_rejects_tampered_signature` |
| Replay expired access | `test_decode_rejects_expired_token` |
| Horizontal privilege (grades) | Permission matrix (`test_permissions_role_maps`) + future IDOR integration |
| Automation on sensitive routes | Rate-limit unit test + Redis-backed limits in runtime |
| Metadata scrubbing in audits | `test_audit_scrub_metadata` |

## Secure SDLC gates

1. **PR**: CI must pass (`ci.yml`).
2. **Dependencies**: pip-audit job must pass (no critical unfixed CVE policy—resolve or waive with ticket).
3. **Static analysis**: Bandit medium+ threshold.
4. **Container**: Docker image builds in CI.
5. **Schema**: `alembic upgrade head` against ephemeral Postgres in CI.

## Deployment verification (quick)

- [ ] `curl -sI https://<api>/api/v1/health/live` shows security headers (CSP, HSTS when TLS terminated correctly).
- [ ] `/metrics` requires internal network only (network policy).
- [ ] No `APP_DEBUG=true` in production env.
