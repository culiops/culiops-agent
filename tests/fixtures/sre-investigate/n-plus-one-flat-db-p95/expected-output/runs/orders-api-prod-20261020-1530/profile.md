# Profile: orders-api prod

Last verified: 2026-10-20 · Built by: helper (cheapest tier) at the start of the run, marks updated by the main session after Phase 4 · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | orders-api |
| Environment | prod |
| Account or profile / Region | prod-read / us-east-1 (account 111122223333, matches environment.md) |
| Cluster, context and namespace | EKS cluster `prod`, context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `orders` |
| IaC repo and paths | none configured in environment.md; Helm chart `orders-api-4.2.0` (name from helm history, repo unknown) |
| Core flows served | order history (`GET /orders`), checkout (`POST /orders`), both listed in environment.md |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (alarm-name prefix, label value, load balancer suffix, job name) |
|---|---|---|
| replicas | orders-api-7c9b6d8f5d-4kq2m, -9vx7t, -tz5wp (verified 2026-10-20, W0-Q20) | pod name (CPU series carry `pod`); the HTTP latency histogram has NO `pod` label (W3-Q1) |

No region, shard or tenant siblings: one cluster, one namespace.

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known (not needed: no WAF symptom) |
| Client-ID header name | none known |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | Loki `{namespace="orders", container="api", app="orders"}`. The `app` value (`orders`) differs from the service name; the lines carry no pod name or trace ID, so no query ties the stream to orders-api (W3-Q9). Sibling stream `app="orders-reconcile"` (container `worker`) is a different workload. | (unverified) |
| Sidecar or proxy logs | none found | (unverified) |
| APM or trace service name | Tempo `resource.service.name = "orders-api"` (case-sensitive); DB spans carry `db.system=postgresql`; traces carry no `service.version` or pod attribute | (verified 2026-10-20) |
| Prometheus job and labels | `service="orders-api"`, `route`, `method` on `http_server_request_duration_seconds_{bucket,count,sum}`; `service`, `db_system` on `db_client_operation_duration_seconds_*`; `service`, `pool="orders-db"`, `state` on `db_client_connections_*`; `namespace`, `pod` on `container_cpu_usage_seconds_total` | (verified 2026-10-20) |
| Business or flow counters | none named in environment.md | (unverified) |
| Compute | namespace `orders`, Deployment `orders-api` (helm release `orders-api`), current ReplicaSet `orders-api-7c9b6d8f5d`; no HPA or ingress listing returned (empty output, not read as "none") | (verified 2026-10-20) for Deployment and ReplicaSet |
| Load balancing | not found | (unverified) |
| Data stores | RDS PostgreSQL 16.6 `orders-db`, db.r6g.2xlarge, Multi-AZ, Performance Insights off | (verified 2026-10-20) |
| Queues and streams | none found | (unverified) |
| Functions | none found | (unverified) |
| Log datasource | Grafana datasource UID `loki-prod` | (verified 2026-10-20) |
| Error tracker project | none in environment.md | (unverified) |
| Code | example-org/orders-api, default branch not read. Image tag to ref rule: image `v2.15.0` is git tag `v2.15.0` (tag list W2-Q7). Clone `~/src/orders-api` (path from environment.md). | (verified 2026-10-20) for the tag rule |
| Tickets and wiki | none named | (unverified) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| downstream | orders-db | PostgreSQL via pool `orders-db` | RDS `orders-db`; `db_system=postgresql` (verified 2026-10-20) | not third party |
| downstream | auth-api | HTTP client span `GET auth-api /verify` in every fetched GET /orders trace | `auth-api.auth.svc.cluster.local` (seen in W3-Q6 and W3-Q7) | not third party; owner unknown |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none found | Grafana dashboard search returned an empty object (W0-Q23) | n/a |

## Baseline notes

- Normal load and latency (2026-10-20 10:00-13:06 UTC and 10-13 same clock window): GET /orders about 56 req/s, p95 about 0.18 s, p50 about 0.09 s.
- Normal DB activity: about 380 statements/s service-wide (`db_system=postgresql`), pool `used` 14-19, `pending_requests` 0, RDS CPU about 25%, connections about 42.
- Known periodic jobs and their usual effect: `orders-reconcile` (Loki app, container `worker`) logs "outbox drained" about every 137 s (seen in the namespace stream); no CronJob, EventBridge rule or Scheduler schedule was returned (W2-Q1..Q3).
- Known benign noise: none recorded.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| Prometheus `ALERTS{alertstate="firing", namespace="orders"}` | orders-api-prod-20261020-1530 | returned an empty matrix; alert name unknown, selector unverified |
| histogram_quantile 0.90 and 0.99 on `http_server_request_duration_seconds_bucket{service="orders-api", route="/orders"}` | orders-api-prod-20261020-1530 | empty while 0.50 and 0.95 returned data (W1-Q9, W1-Q10) |
