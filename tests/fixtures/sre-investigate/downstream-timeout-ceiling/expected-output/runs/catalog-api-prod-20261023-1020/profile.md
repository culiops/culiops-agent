# Profile: catalog-api prod

Last verified: 2026-10-23 · Built by: helper (cheapest tier) with the main session's wave 1 and 2 results · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | catalog-api |
| Environment | prod |
| Account or profile / Region | prod-read (account 111122223333) / us-east-1 |
| Cluster, context and namespace | cluster `prod`; context `arn:aws:eks:us-east-1:111122223333:cluster/prod`; namespace `catalog` (verified 2026-10-23) |
| IaC repo and paths | `example-org/catalog-deploy` holds the Helm values (from environment.md; unverified, `gh` read returned `{}`); Helm release `catalog-api` (verified 2026-10-23, chart catalog-api-2.6.1, app 1.31.2) |
| Core flows served | product page (`GET /products/{id}`) is served and was the affected route (verified 2026-10-23); search (`GET /search`) is served too |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (alarm-name prefix, label value, load balancer suffix, job name) |
|---|---|---|
| replicas | 6 pods `catalog-api-6b9d7c5f48-*` (4 older, 2 added by the HPA at about 09:32 UTC on 2026-10-23) | pod name; HPA `catalog-api` min 4, max 12 (verified 2026-10-23). No regions, shards or tenants found. |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | not discovered (WAF not in scope for this run) |
| Client-ID header name | not discovered (WAF not in scope for this run) |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | `/eks/prod/catalog-api` (STANDARD class, 14-day retention, 2.42 TB stored, about 172.8 GB per day, about 1.8 GB per 15 minutes). Message field: results came back as `msg` (the query named `message`). | (verified 2026-10-23) group; field `msg` (verified 2026-10-23); `message` (unverified) |
| Sidecar or proxy logs | none discovered | (unverified) |
| APM or trace service name | `catalog-api` as `resource.service.name`; outgoing-call peer attribute `span.server.address` | (verified 2026-10-23) |
| Prometheus job and labels | label `service="catalog-api"`, `route`, `status` on `http_server_request_duration_seconds_{bucket,count,sum}`; also `http_client_request_duration_seconds_*`, `http_server_requests_in_flight`, `kube_deployment_status_replicas`, `kube_pod_container_status_restarts_total`, `up`. Job label not discovered. Alert `CatalogApiLatencyHigh` (labels alertname, namespace, service, severity). | metric names, `service`, `route`, `status` (verified 2026-10-23); job (unverified); no `ALERTS` series listed |
| Business or flow counters | none listed in environment.md | (unverified) |
| Compute | Deployment `catalog-api`; ReplicaSets `catalog-api-6b9d7c5f48` (current) and `catalog-api-58f4d6b7c9` (old); HPA `catalog-api`; pod selector label not discovered; ConfigMap names not discovered | Deployment, ReplicaSets, HPA (verified 2026-10-23); selector, ConfigMaps (unverified) |
| Load balancing | none discovered (`kubectl get deployment,service,ingress` printed nothing) | (unverified) |
| Data stores | `catalog-db.internal.example.com` (database), `catalog-cache.internal.example.com` (cache), seen as client-span peers; engine and cluster names not discovered | peer addresses (verified 2026-10-23); engines (unverified) |
| Queues and streams | none discovered | (unverified) |
| Functions | none discovered | (unverified) |
| Log datasource | CloudWatch Logs Insights through profile `prod-read` | (verified 2026-10-23) |
| Error tracker project | none listed | (unverified) |
| Code | `example-org/catalog-api` (default branch not read). Image tag to ref rule: not resolved; image tag is `1.31.2` in registry 111122223333.dkr.ecr.us-east-1.amazonaws.com/catalog-api, matching Helm app version. Local clone: none listed in environment.md. | (unverified) |
| Tickets and wiki | none listed. The alert annotation names a runbook page for catalog-api latency (lead only, not opened) | (unverified) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| downstream | pricing API | outgoing HTTP GET from `GET /products/{id}`; client timeout observed at 5000 ms; on timeout the service logs "serving cached price" | `api.pricing.example.com` (verified 2026-10-23) | owner and status route not recorded; same domain as internal hosts suggests an internal team, unconfirmed |
| downstream | reviews API | outgoing HTTP, in-cluster; 9 lines "reviews-api returned 503; reviews block hidden" in the 15 minutes to 10:20 UTC | `reviews-api.catalog.svc.cluster.local` (verified 2026-10-23) | internal service, owner not recorded |
| downstream | catalog database | database client spans | `catalog-db.internal.example.com` (verified 2026-10-23) | not applicable |
| downstream | catalog cache | cache client spans | `catalog-cache.internal.example.com` (verified 2026-10-23) | not applicable |
| upstream | ingress or load balancer | not discovered | (unverified) | not applicable |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none | environment.md lists no Grafana | none |

## Baseline notes

- Normal load and latency (2026-10-23 04:20 to 09:30 UTC, and the same clock window 7 days back): about 410 req/s; p50 0.11 s; p95 0.42 s; p99 0.89 s; 5xx share about 0.2%. Per route p95 (7 days back): /products/{id} 0.441 s, /search 0.372, /products/{id}/reviews 0.207, /categories 0.079, /healthz 0.004. Per route rate at 10:20 UTC: /products/{id} 144 req/s, /search 122, /categories 84, /products/{id}/reviews 58, /healthz 2.
- Client-span p95 per peer at baseline: pricing 0.21 s, reviews-api 0.06 s, database 0.004 s, cache 0.001 s.
- Capacity: 4 replicas at baseline, 6 during the incident, about 0.2 CPU core and 350 to 390Mi memory per pod, HPA max 12.
- Known periodic jobs and their usual effect: none found (no CronJob, EventBridge rule or Scheduler schedule returned).
- Known benign noise: unknown. No baseline log scan was run; "reviews-api returned 503" (9 in 15 minutes during the incident) may or may not be background.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | not applicable | The p90 query and the 14-day pulls returned empty matrices, but the selector was verified by other queries in the same wave, so no identifier is marked stale. |
