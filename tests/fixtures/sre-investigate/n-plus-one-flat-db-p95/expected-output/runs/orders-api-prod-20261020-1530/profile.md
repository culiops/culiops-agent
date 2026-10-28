# Profile: orders-api prod

Last verified: 2026-10-20 · Built by: helper (cheapest tier) with main-session corrections · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | orders-api |
| Environment | prod |
| Account or profile / Region | prod-read (account 111122223333) / us-east-1 |
| Cluster, context and namespace | cluster `prod`, context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `orders`; Deployment `orders-api`, Helm release `orders-api` (chart orders-api-4.2.0) |
| IaC repo and paths | none configured in environment.md (chart values not visible; only the app repo is listed) |
| Core flows served | order history `GET /orders` (core), checkout `POST /orders` (core) |
| SLO or error-budget source | none named in environment.md |

## Sibling set

| Dimension | Member | How to tell it apart |
|---|---|---|
| replicas | orders-api-7c9b6d8f5d-4kq2m, orders-api-7c9b6d8f5d-9vx7t, orders-api-7c9b6d8f5d-tz5wp | pod name; single cluster, no regions, shards or tenants found (PB-Q9) |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known |
| Client-ID header name | none known |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | Loki datasource `loki-prod`: `app="orders"`, `namespace="orders"`, `container="api"`; returned `GET /orders` access lines (PB-Q15) but the stream has no pod label and its value (`orders`) differs from the service name, so no tie to the orders-api pods | (unverified) |
| Sidecar or proxy logs | none discovered | (unverified) |
| APM or trace service name | Tempo `tempo-prod`: `orders-api` (exact); resource tags `k8s.namespace.name`, `k8s.pod.name`, `service.name`, `service.version` exist, but the two fetched traces carry only `service.name` and `k8s.namespace.name` | (verified 2026-10-20) by W1-Q17 and W2-Q8 (a bare `{resource.service.name="orders-api"}` search returned no traces, PB-Q17; see lesson candidates) |
| Prometheus job and labels | datasource `prom-prod`: `service="orders-api"` on `http_server_request_duration_seconds_{bucket,count,sum}` (labels `method`, `route`; no status or code label) and `db_client_operation_duration_seconds_{bucket,count,sum}` (labels `service`, `db_system`); `db_client_connections_usage` and `db_client_connections_pending_requests` (labels `service`, `pool`, `state`); `container_cpu_usage_seconds_total` (labels `namespace`, `pod`). No `job` label seen. | (verified 2026-10-20) |
| Business or flow counters | none discovered | (unverified) |
| Compute | namespace `orders`, Deployment `orders-api`, ReplicaSets `orders-api-7c9b6d8f5d` (v2.15.0, 3 ready) and `orders-api-5f8d9c7b6a` (v2.14.0, 0 replicas); no HPA, Service or Ingress found (the listing printed nothing, PB-Q10: absence not proven) | (verified 2026-10-20) for the Deployment and ReplicaSets |
| Load balancing | not discovered | (unverified) |
| Data stores | RDS `orders-db` (PostgreSQL 16.6, db.r6g.2xlarge, Multi-AZ); pool name `orders-db` in the app's metrics | (verified 2026-10-20) |
| Queues and streams | none discovered | (unverified) |
| Functions | none | (unverified) |
| Log datasource | Grafana `https://grafana.example.com`, datasource UIDs `prom-prod`, `loki-prod`, `tempo-prod` | (verified 2026-10-20) |
| Error tracker project | none configured | (unverified) |
| Code | `example-org/orders-api`; default branch unknown (the `gh` repo lookup printed `{}`); image tag to ref rule: image tag `vX.Y.Z` = git tag `vX.Y.Z` (tags v2.14.0 and v2.15.0 exist locally, PB-Q12; the rollout history names image v2.14.0 then v2.15.0, W1-Q3). Local clone `~/src/orders-api` (environment.md). | (verified 2026-10-20) for the tag rule |
| Tickets and wiki | none configured | (unverified) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| downstream | orders-db | PostgreSQL over a psycopg connection pool | RDS `orders-db`; pool `orders-db` | not a third party |
| downstream | auth-api | HTTP `GET /verify` client span on every request | `auth-api.auth.svc.cluster.local` (seen in traces W2-Q10, W2-Q11); no latency series (W3-Q7 returned nothing) | internal team, owner unknown |

No third party found in the path. No service-discovery catalog exists (`.culiops/service-discovery` is absent, PB-Q14).

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none found (Grafana search for "orders" printed `{}`, PB-Q8) | | |

## Baseline notes

- Normal load and latency: `GET /orders` about 56 req/s; p50 about 0.09 s and p95 about 0.18 s (10:00 to 13:06 UTC on 2026-10-20 and the whole of 10:00 to 15:30 on 2026-10-13: W1-Q8..Q11). DB operations about 380/s service-wide (W1-Q15, W1-Q16). Pool `used` 14 to 19. RDS CPU about 24%.
- Known periodic jobs and their usual effect: none found (no CronJobs, EventBridge rules or Scheduler schedules returned: W2-Q3..Q5; the `{}` replies do not prove absence).
- Known benign noise: none known.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | | |
