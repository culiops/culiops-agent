# Profile: catalog-api prod

Last verified: 2026-10-23 · Built by: helper (cheapest tier) plus main session updates after wave 1 · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | catalog-api |
| Environment | prod |
| Account or profile / Region | prod-read / us-east-1 (account 111122223333) |
| Cluster, context and namespace | cluster `prod` · context `arn:aws:eks:us-east-1:111122223333:cluster/prod` · namespace `catalog` (verified 2026-10-23, W0-Q20) |
| IaC repo and paths | `example-org/catalog-deploy` holds the Helm values (from environment.md) (unverified: `gh api` returned `{}`, W0-Q25); no local clone listed |
| Core flows served | product page (`GET /products/{id}`) and search (`GET /search`), both from environment.md; route labels `/products/{id}` and `/search` (verified 2026-10-23, W1-Q5) |
| SLO or error-budget source | none named in environment.md |

## Sibling set

| Dimension | Member | How to tell it apart |
|---|---|---|
| replicas (single environment, no regions/shards/tenants listed) | pods `catalog-api-6b9d7c5f48-{2hxkq,4tq8w,7mzpl,c2r5d,kx9vn,p6wfj}` (verified 2026-10-23, W0-Q20) | pod name suffix; pod-template-hash `6b9d7c5f48` |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known |
| Client-ID header name | none known |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | `/eks/prod/catalog-api` (CloudWatch Logs, STANDARD class, 14-day retention, ~2.42 TB stored); message field is `msg` (the Insights result column in W2-Q1; the query had asked for `message`, an unverified guess) | group (verified 2026-10-23, W0-Q14, W2-Q1 returned data); field `msg` (verified 2026-10-23, W2-Q1); `message` (stale, see below) |
| Sidecar or proxy logs | none found: the prefix `/eks/prod/catalog` lists one group | (verified absent in this prefix, W0-Q14) |
| APM or trace service name | `catalog-api` as `resource.service.name` (peer attribute `server.address`); resource attributes `service.name`, `k8s.pod.name`, `k8s.namespace.name`; span attributes include `server.address`, `http.route`, `db.system` | name (verified 2026-10-23, W1-Q6: TraceQL metrics returned series; the earlier tag-values call and unfiltered search had returned nothing, W0-Q15, W0-Q17); attribute names (verified, W0-Q16) |
| Prometheus job and labels | metrics `http_server_request_duration_seconds_{bucket,count,sum}`, `http_server_requests_in_flight`, `kube_pod_container_status_restarts_total`, `kube_deployment_status_replicas`, `up`; label `service="catalog-api"` (the alert carries it). No `traces_spanmetrics_*`, cAdvisor or `kube_pod_owner` names in the list | metric names (verified, W0-Q19); label `service` and `route` on the histogram (verified 2026-10-23, W1-Q3, W1-Q5) |
| Business or flow counters | none named | (unverified) |
| Compute | namespace `catalog`; pods `catalog-api-6b9d7c5f48-*`; ReplicaSets `catalog-api-6b9d7c5f48` (current, rev 22) and `catalog-api-58f4d6b7c9` (0 replicas); HPA `catalog-api` (min 4, max 12, pods metric `http_requests_in_flight` target 40); Deployment `catalog-api` (rollout history read, W1-Q1); Helm release `catalog-api` (chart 2.6.1, image 1.31.2) | pods, HPA, ReplicaSets, Deployment rollout history and Helm release (verified, W0-Q20, W0-Q21, W1-Q1) |
| Load balancing | none found (`kubectl get ingresses,services` printed nothing, W0-Q22) | (unverified) |
| Data stores | `catalog-db.internal.example.com` (database; engine unknown), `catalog-cache.internal.example.com` (cache): seen only as span peer addresses | (verified as span peers 2026-10-23, W1-Q6; engine and AWS resource unverified) |
| Queues and streams | none known | (unverified) |
| Functions | none known | (unverified) |
| Log datasource | CloudWatch Logs, profile `prod-read`, us-east-1 | (verified, W0-Q12) |
| Error tracker project | none in environment.md | n/a |
| Code | `example-org/catalog-api`; default branch unknown; image tag to ref rule unknown | (unverified: `gh api` returned `{}`, W0-Q25) |
| Tickets and wiki | none configured; the firing alert carries a `runbook_url` annotation (not read) | n/a |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| downstream | api.pricing.example.com | outbound HTTP client spans from catalog-api; client timeout 5000 ms with a cached-price fallback (from the app's own log line, W2-Q1) | span peer `server.address` (verified, W1-Q6) | owner unknown (vendor or internal team); no status page or contact known |
| downstream | reviews-api.catalog.svc.cluster.local | in-cluster service call | span peer `server.address` (verified, W1-Q6) | internal |
| downstream | catalog-db.internal.example.com | database client spans | span peer `server.address` (verified, W1-Q6) | internal |
| downstream | catalog-cache.internal.example.com | cache client spans | span peer `server.address` (verified, W1-Q6) | internal |
| note | no service-discovery catalog exists (`.culiops/service-discovery/` missing, W0-Q24); dependencies come from Tempo client spans of 2026-10-23 | | | |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none: Grafana is not listed in environment.md | | |

## Baseline notes

- Normal load and latency: about 411 req/s; p50 0.11 s, p95 0.42 s, p99 0.89 s; 5xx share about 0.21% (2026-10-23 04:20-09:30 and the same hours a week earlier for latency; W1-Q3, W1-Q4). Route mix: /products/{id} 144, /search 122, /categories 84, /products/{id}/reviews 58, /healthz 2 req/s (W1-Q5).
- HPA: scales on pods metric http_requests_in_flight (target 40), min 4, max 12.
- Known periodic jobs and their usual effect: none known.
- Known benign noise: none known. Log messages seen 10:05-10:20 during the incident (no baseline window): pricing timeout 25,914, pricing cache miss 611, reviews-api 503 reviews hidden 9 (W2-Q1); none can be called normal.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| `message` as the Insights field name | run catalog-api-prod-20261023-1020 | the query used `by message`; the reply labelled the group column `msg`; use `msg` |
