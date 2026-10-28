# Profile: orders-api prod

Last verified: 2026-10-20 · Built by: helper (cheapest tier, TASK: PROFILE), then marks updated by the main session after waves 1-4 · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | orders-api |
| Environment | prod |
| Account or profile / Region | `prod-read` (account 111122223333) / us-east-1 |
| Cluster, context and namespace | cluster `prod`, context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `orders`; Deployment `orders-api` (verified 2026-10-20), Helm release `orders-api` chart `orders-api-4.2.0` (verified 2026-10-20) |
| IaC repo and paths | not named in environment.md; the Helm chart's source repo and values files are unknown (unverified) |
| Core flows served | order history `GET /orders` (core flow, listed), checkout `POST /orders` (core flow, listed; served by this service, route present in metrics) |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (alarm-name prefix, label value, load balancer suffix, job name) |
|---|---|---|
| replicas | 3 pods of Deployment `orders-api` (ReplicaSet `orders-api-7c9b6d8f5d` at 2026-10-20) | `pod` label / `k8s.pod.name` resource attribute; no per-pod latency series pulled this run |

No regions, shards, tenants or availability-zone split was found.

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known (not investigated; no WAF symptom) |
| Client-ID header name | none known (not investigated; no WAF symptom) |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | Loki `{namespace="orders", app="orders", container="api"}` on datasource UID `loki-prod`; the `app` value is `orders`, not `orders-api` | (verified 2026-10-20) |
| Sidecar or proxy logs | none found | (unverified) |
| APM or trace service name | Tempo `resource.service.name = "orders-api"` (resource tags: service.name, service.version, k8s.namespace.name, k8s.pod.name); db spans `span.db.system = "postgresql"`; route `span.http.route`, method `span.http.request.method`; datasource UID `tempo-prod` | (verified 2026-10-20) |
| Prometheus job and labels | datasource UID `prom-prod`; `http_server_request_duration_seconds_{bucket,count,sum}{service="orders-api", route, method}`; `db_client_operation_duration_seconds_{bucket,count,sum}{service="orders-api", db_system="postgresql"}`; `db_client_connections_usage` and `db_client_connections_pending_requests{service="orders-api", pool="orders-db"}`; `container_cpu_usage_seconds_total{namespace="orders", pod}`; `kube_deployment_status_replicas`; `up`. Not exposed: ALERTS, traces_spanmetrics_*, CFS throttling | (verified 2026-10-20) |
| Business or flow counters | none found | (unverified) |
| Compute | namespace `orders`, Deployment `orders-api`, Helm release `orders-api`; sibling workload `orders-reconcile` (Loki app `orders-reconcile`, container `worker`); HPA and ConfigMaps not readable in this setup | Deployment/Helm (verified 2026-10-20); HPA (unverified) |
| Load balancing | none found (no ingress or load-balancer series; ingress listing returned nothing) | (unverified) |
| Data stores | RDS PostgreSQL instance `orders-db` (db.r6g.2xlarge, postgres 16.6, Multi-AZ, Performance Insights off); CloudWatch AWS/RDS dimension DBInstanceIdentifier=orders-db returns CPUUtilization, ReadLatency, DatabaseConnections (other RDS metrics returned nothing) | (verified 2026-10-20) |
| Queues and streams | none found | (unverified) |
| Functions | none found | (unverified) |
| Log datasource | Loki UID `loki-prod`; Prometheus `prom-prod`; Tempo `tempo-prod`; Grafana `https://grafana.example.com`; token variable `GRAFANA_SERVICE_ACCOUNT_TOKEN` | (verified 2026-10-20) |
| Error tracker project | none | (unverified) |
| Code | example-org/orders-api, default branch not read. Image tag to ref rule: Helm APP VERSION `v2.15.0` equals git tag `v2.15.0` (tags v2.12.0 ... v2.15.0 present locally). Local clone path lives in environment.md | tag rule (verified 2026-10-20); default branch (unverified) |
| Tickets and wiki | none configured | (unverified) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| downstream | PostgreSQL `orders-db` (in-house, RDS) | SQL through a connection pool | pool `orders-db`; RDS instance `orders-db` | none (not a third party) |
| downstream | `auth-api` | HTTP client call `GET auth-api /verify` per request, about 3.4 ms in the one trace read | `auth-api.auth.svc.cluster.local` (seen in trace e3ea7a39..., W4-Q3) | none (in-cluster, owning team unknown) |
| sibling | `orders-reconcile` worker | same namespace; "outbox drained" loop every 137 s; whether and how it uses orders-db is not visible | Loki app `orders-reconcile` | none |

No third party in the path found.

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none found (search for "orders-api" returned `{}`) | — | — |

## Baseline notes

- Normal load and latency (2026-10-20 10:00-13:06 UTC, v2.14.0): GET /orders about 56 req/s, p50 about 0.09 s, p95 0.16-0.20 s; other routes p95: GET /orders/{id} 0.061 s, POST /orders 0.139 s, PATCH /orders/{id} 0.091 s, GET /healthz 0.003 s; DB operations about 380/s; pool used 14-19 with 0 pending; RDS CPU about 24 %, ReadLatency 0.5-0.7 ms, DatabaseConnections 40-44; 3 db spans per GET /orders request (p50, max 4).
- Known periodic jobs and their usual effect: none found. `orders-reconcile` drains every 137 s (not a schedule listing; no effect seen on orders-api).
- Known benign noise: `orders-reconcile` "outbox drained batch=N pending=0" about every 137 s.

## Stale identifiers

| Identifier | Last run with no data | Note |
|---|---|---|
| (none this run) | — | no identifier returned empty on a later query; note that `app="orders-api"` is not a Loki label value (W0-Q13), the value is `orders` |
