# Kibana / Elasticsearch query examples (structured logs)

Assuming JSON logs indexed with fields such as `logger`, `message`, `event.action`, `http.request.path`, `client.ip`.

## Denied-response bursts

```
logger:"security.observability" AND message:"security.denied_burst"
```

## Sensitive-route throttling

```
message:"sensitive_route.limited" OR message:"sensitive_route.token_limited"
```

## Validation failures (correlation)

```
logger:"api.validation" AND path:/api/v1/*
```

Add `request_id:"<uuid>"` when correlating with API client `X-Request-ID`.
