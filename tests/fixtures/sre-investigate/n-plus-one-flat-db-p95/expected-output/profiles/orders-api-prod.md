# Profile: orders-api prod

Last verified: 2026-10-20 · Built by: helper (cheapest tier) + main session; merged from run orders-api-prod-20261020-1530 · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | orders-api |
| Environment | prod |
| Account or profile / Region | prod-read / us-east-1 (account 111122223333) |
| Cluster, context and namespace | cluster `prod`, context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `orders` |
| IaC repo and paths | Helm release `orders-api`, chart `orders-api-4.2.0` (verified 2026-10-20, W1-Q4). IaC repo and values-file paths not found (unverified) |
| Core flows served | checkout `POST /orders`, order history `GET /orders` (both from environment.md) |
| SLO or error-budget source | none named in environment.md |

## Sibling set

| Dimension | Member | How to tell it apart (alarm-name prefix, label value, load balancer suffix, job name) |
|---|---|---|
| replicas | `orders-api-7c9b6d8f5d-4kq2m`, `orders-api-7c9b6d8f5d-9vx7t`, `orders-api-7c9b6d8f5d-tz5wp` | pod name (verified 2026-10-20, PB-Q10) |
| related workload (not a replica) | `orders-reconcile` (Loki `app`, container `worker`) | Loki label `app="orders-reconcile"` (unverified relation to the service) |

No regions, shards or tenants found.

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known (not applicable to this run) |
| Client-ID header name | none known (not applicable to this run) |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | Loki `namespace="orders"` | (verified 2026-10-20, PB-Q3; the namespace also holds the orders-api pods per PB-Q10) |
| Application log label or log group | Loki `app="orders"`, `container="api"` | (unverified) value differs from the service name `orders-api`; the stream carries no pod label, so the tie rule (shared pod name, or a trace or request ID in both) is not met. Lines that look like the service's traffic (`method=GET path=/orders`) are a lead only |
| Sidecar or proxy logs | none found | (unverified) |
| APM or trace service name | `orders-api` in resource attribute `service.name` (Tempo scope `resource`) | (verified 2026-10-20, W1-Q21: a TraceQL metrics query with `span.db.system` returned the series). The bare exact-name search returned 0 traces in the last hour (PB-Q7) and the tag-values call returned `{}`, so use a span filter |
| Prometheus job and labels | `service="orders-api"` on `http_server_request_duration_seconds_*`, `db_client_*`, `container_cpu_usage_seconds_total`{namespace="orders"} | (verified 2026-10-20, W1-Q5, W1-Q7: series returned with `service="orders-api"`, routes `/orders`, `/orders/{id}`, `/healthz`; `db_system="postgresql"` on `db_client_*`; pool label `pool="orders-db"`) |
| Business or flow counters | none named | (unverified) no counter in environment.md |
| Compute | Deployment `orders-api` (ns `orders`), ReplicaSets `orders-api-5f8d9c7b6a` (old, 0 pods) and `orders-api-7c9b6d8f5d` (3 pods) | (verified 2026-10-20, W1-Q1, W1-Q2). Services, ingresses, HPAs not found (combined listing returned nothing, PB-Q11) (unverified) |
| Load balancing | none found | (unverified) |
| Data stores | RDS PostgreSQL 16.6 `orders-db`, db.r6g.2xlarge, Multi-AZ, Performance Insights disabled | (verified 2026-10-20, PB-Q12) |
| Queues and streams | none found | (unverified) |
| Functions | none found | (unverified) |
| Log datasource | Grafana datasource `loki-prod` (labels returned) | (verified 2026-10-20, PB-Q1) |
| Error tracker project | none | (unverified) |
| Code | example-org/orders-api, default branch unknown (gh returned `{}`); app diffs read by tag from the local clone. Image tag to ref rule: image tag is `v<semver>` and equals a git tag (v2.14.0, v2.15.0 exist in the clone) | tag rule (verified 2026-10-20, PB-Q13 with W1-Q1 and W1-Q4: Helm APP VERSION v2.15.0 equals git tag v2.15.0); default branch (unverified) |
| Tickets and wiki | none | (unverified) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| downstream | orders-db (PostgreSQL) | SQL; `db_client_*` metrics exported by the service; pool label `pool="orders-db"` | RDS `orders-db` (verified 2026-10-20, PB-Q12, W4-Q5) | internal (AWS RDS); not a third party |
| downstream | auth-api | HTTP client span `GET auth-api /verify` on every GET /orders request, host `auth-api.auth.svc.cluster.local`; about 3.4-3.8 ms in the two fetched traces | span name and `server.address` (seen in W4-Q3, W4-Q4; latency series not available) | internal service (owner not recorded) |

Upstream callers and other downstreams unknown. No service-discovery catalog is present.

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none found (Grafana search for "orders" returned `{}`) | - | - |

## Baseline notes

- Normal load and latency (verified 2026-10-20, 2026-10-13 window, W1-Q5, W1-Q6, W1-Q14, W1-Q16, W2-Q10): GET /orders p95 about 0.18 s, p50 about 0.09 s, about 56 requests per second; database operations about 380 /s service-wide; pool used 14-19, pending 0; orders-db CPU about 25%, ReadLatency about 0.6 ms, connections 40-44 (W4-Q5). Other routes: GET /orders/{id} p95 0.06 s, POST /orders 0.14 s, PATCH /orders/{id} 0.09 s.
- Trace shape of GET /orders before v2.15.0: root plus one GET auth-api /verify plus one `SELECT orders JOIN order_items` (descendant spans p50 3, max 4, W4-Q2).
- Known periodic jobs and their usual effect: none known. `orders-reconcile` (Loki `app`, container `worker`) exists in the namespace; its schedule is not established.
- Known benign noise: none known.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| Tempo bare search `{ resource.service.name = "orders-api" }` limit 5, last hour | orders-api-prod-20261020-1530 | returned 0 traces, but the name is valid (W1-Q21); not a stale name, kept here as a query-form note |
