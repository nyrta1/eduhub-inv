# Security architecture & OWASP hardening (Stage 4)

This document describes defensive controls added on top of Stages 1–3 (auth, RBAC, academic domain). It is intended for **secure SDLC review**, **OWASP alignment**, and **university security assessments**.

---

## 1. Security audit summary

The codebase previously relied on FastAPI defaults, JWT/RBAC, Redis-backed auth rate limiting, structured logging, and SQLAlchemy parameter binding. Stage 4 adds:

| Area | Enhancement |
|------|-------------|
| Transport / browser | Configurable **security headers** (CSP, HSTS, XFO, CORP/COOP, Referrer-Policy, Permissions-Policy), selective **Cache-Control** on auth/admin routes |
| Abuse resistance | **Sensitive-route rate limits** (applications, grade mutations, application review, admin role changes) — Redis sliding windows, IP + credential fingerprint for grades |
| Monitoring | **Prometheus metrics** for denied HTTP responses, sensitive-route throttling, burst alerts; **Grafana** dashboard + **Prometheus** alert rules |
| Telemetry | **Denied-response burst detector** (401/403 spikes per IP) with structured `security.denied_burst` logs |
| Disclosure | **Production-safe validation errors** (no field internals unless `APP_DEBUG=true`), standardized **`request_id`** on errors |
| SSRF | **`secure_http`** helper blocking RFC1918, loopback, IPv6 ULA, link-local, **optional hostname allow-list**, **no redirects by default**, **`trust_env=False`** |
| Query safety | **`safe_query`** utilities for identifier validation and allow-listed dynamic ordering |
| Audit | Domain audit metadata enriched with **`severity`**, **`event_category`**, **`request_id`** (stored in JSON `details`) |
| Supply chain | **`constraints.txt`** pins, **GitHub Actions** workflow (**pip-audit**, **bandit**), **pre-commit** hooks |
| Containers | **Non-root** API image (UID **10001**), **`no-new-privileges`**, selective **`cap_drop`** |

---

## 2. Threat model overview (STRIDE-style summary)

| Threat | Assets | Mitigations |
|--------|----------|-------------|
| Credential stuffing / brute force | Auth endpoints | Existing Redis limits + lockouts; extended sensitive-route limits |
| IDOR / privilege escalation | Academic records | Unchanged business-layer checks (Stage 3); defense-in-depth headers reduce XSS impact |
| Automated scraping / grading fraud | Grades, applications | Redis route-aware limits + monitoring |
| SSRF via outbound integrations | Internal networks | `secure_http.assert_url_allowed` + timeouts |
| Information disclosure | Stack traces, validation internals | Sanitized 422/500 responses in non-debug mode |
| Supply-chain compromise | Dependencies | pip-audit workflow, pinned constraints, bandit |
| Container breakout | Host kernel | Non-root user, dropped capabilities |

**Trust boundaries:** Internet → reverse proxy/WAF (recommended) → FastAPI API → PostgreSQL / Redis. ELK receives structured logs; Prometheus scrapes `/metrics` from API.

---

## 3. OWASP Top 10 mapping (2021)

| OWASP | Control highlights |
|-------|-------------------|
| A01 Broken Access Control | Stage 3 RBAC + service checks unchanged; rate limits reduce brute probing |
| A02 Cryptographic Failures | TLS terminates at proxy (recommended); HSTS header when HTTPS used; secrets remain env-only |
| A03 Injection | SQLAlchemy bound parameters; `safe_query` for future dynamic fragments |
| A04 Insecure Design | Threat model + documented residual risks; deny-by-default headers |
| A05 Security Misconfiguration | Headers configurable via env; OpenAPI **disabled in production** unless `SECURITY_EXPOSE_OPENAPI=true` |
| A06 Vulnerable Components | CI pip-audit + `constraints.txt` |
| A07 Identification & Auth Failures | Existing JWT/session controls + expanded limits |
| A08 Software/Data Integrity | SBOM workflow hook documented; pre-commit + CI |
| A09 Logging & Monitoring Failures | Security metrics, Grafana dashboard, burst anomaly logs |
| A10 SSRF | `secure_http` outbound guard |

---

## 4. Formal vulnerability table

| Vulnerability | OWASP | Location | Risk | Severity | Exploitation scenario | Mitigation | Status |
|---------------|-------|----------|------|----------|----------------------|------------|--------|
| OpenAPI/schema disclosure in prod | A05 | `/api/v1/docs`, `/openapi.json` | API surface enumeration | Medium | Attacker maps endpoints for targeted abuse | Docs disabled when `APP_ENV=production` unless `SECURITY_EXPOSE_OPENAPI=true` | **Mitigated** |
| Weak browser isolation | A05 | Global responses | Clickjacking / MIME sniffing | Medium | Embed admin UI in iframe; MIME confusion | CSP, XFO DENY, nosniff, CORP/COOP | **Mitigated** |
| Sensitive response caching | A02/A05 | Auth endpoints | Token/metadata cached by shared proxies | Low–Med | Shared browser caches API responses | `Cache-Control: no-store` on `/api/v1/auth`, `/api/v1/users/` | **Mitigated** |
| Validation field leakage | A04 | `422` responses | Schema inference | Low | Automated probing learns internal keys | Non-debug mode hides `exc.errors()` details | **Mitigated** |
| Internal SSRF | A10 | Future outbound HTTP | Lateral movement | High | Webhook URL hits metadata IP | `secure_http` URL gate | **Mitigated** (library API) |
| Grade/application automation | A07/A04 | Academic POST/PATCH | Fraud / DoS | Medium | Scripted submissions | Redis sensitive-route limits | **Mitigated** |
| Privilege probe floods | A07 | Any authenticated route | Account profiling | Low–Med | Rapid 403/401 probing | Burst detector + `security_http_denied_total` | **Detected** |
| Dependency CVEs | A06 | Third-party wheels | RCE / TLS bypass | Varies | Public CVE | CI pip-audit + pins | **Process control** |
| Immutable audit trail | A09 | `audit_logs` table | Repudiation | Low | DBA UPDATE rows | Document append-only policy + DB permissions (operational) | **Residual** |

---

## 5. Incident response (short)

1. **Identify**: Grafana alerts (`security_denied_burst_alerts_total`), Prometheus rules, Kibana `security.*` / `security.denied_burst` logs (filter `request_id`).
2. **Contain**: Block IP at WAF / reverse proxy; rotate JWT signing keys if compromise suspected (`JWT_*_SECRET`, `APP_SECRET_KEY`).
3. **Eradicate**: Patch dependency CVE (pip-audit), revoke Redis sessions (`auth:revoked_*` patterns already exist).
4. **Recover**: Replay audits from PostgreSQL `audit_logs` (immutable requirement is **operational** — revoke UPDATE on prod role).
5. **Post-incident**: Export Prometheus range + ELK timeline using correlation IDs.

---

## 6. Secure deployment checklist

- [ ] `APP_ENV=production`, `APP_DEBUG=false`, `DATABASE_ECHO=false`
- [ ] Strong random `APP_SECRET_KEY` (≥32 chars); distinct `JWT_ACCESS_SECRET` / `JWT_REFRESH_SECRET` in high-threat environments
- [ ] `SECURITY_EXPOSE_OPENAPI=false` (default) — enable only on bastion/staging
- [ ] `CORS_ALLOWED_ORIGINS` explicit list (**never** `*` with credentials)
- [ ] `API_ALLOWED_HOSTS` matches public hostname behind LB
- [ ] TLS termination + HSTS at proxy (application emits HSTS when HTTPS used end-to-end)
- [ ] PostgreSQL/Redis not exposed publicly; network segmentation (`backend` Docker network)
- [ ] Run `pip-audit` / `bandit` from CI before promote
- [ ] Grafana dashboards imported; Prometheus alerts routed to on-call
- [ ] Log retention & GDPR/FERPA alignment for student PII (operational policy)

---

## 7. Elasticsearch / Kibana query examples

Saved as plain-text references (`infra/kibana/security-queries.md`). Typical filters:

- `security.denied_burst` — `"security.denied_burst"` in message field (structured JSON logs).
- Rate-limit violations — `"sensitive_route.limited"` or `"sensitive_route.token_limited"`.
- Failed validation (without leaking fields in prod) — `api.validation` logger + `path`.

---

## 8. Residual limitations & accepted risks

| Topic | Limitation |
|-------|------------|
| JWT crypto | Still symmetric HS256 by default; asymmetric JWKS is an architectural upgrade path |
| Audit immutability | Enforced by DB privileges / triggers — **not** cryptographic chaining |
| Rate limits | IP-based buckets can affect NAT-heavy campuses — tune thresholds |
| `secure_http` | Does not replace SSRF-safe architecture for user-supplied URLs in business logic — callers must use the helper |
| Container hardening | Root filesystem not marked read-only (Python may need ephemeral caches) — optional future hardening |

---

## 9. References

- OWASP ASVS (Application Security Verification Standard)
- OWASP API Security Top 10
- NIST SP 800-53 moderate baseline mapping (operational)
