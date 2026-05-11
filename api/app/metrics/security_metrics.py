from __future__ import annotations

from prometheus_client import Counter

security_sensitive_route_limited_total = Counter(
    "security_sensitive_route_limited_total",
    "Sensitive route requests blocked by Redis sliding-window limits",
    ["bucket"],
)

security_http_denied_total = Counter(
    "security_http_denied_total",
    "HTTP responses indicating client authn/authz failure or forbidden access",
    ["status_code"],
)

security_denied_burst_alerts_total = Counter(
    "security_denied_burst_alerts_total",
    "Alerts emitted when an IP exceeds denied-response thresholds within a window",
)
