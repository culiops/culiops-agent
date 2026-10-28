# Profile: orders-api prod

Last verified: 2026-10-21 · Built by: helper (cheapest tier) + main session · Status: partly unverified
Working copy for this run. The stored profile (`profiles/orders-api-prod.md`) does not exist and is written only in the record phase after the operator replies.

## Identity

| Field | Value |
|---|---|
| Service | orders-api |
| Environment | prod |
| Account or profile / Region | `prod-read` (account 111122223333) / us-east-1 |
| Cluster, context and namespace | ECS cluster `prod` (verified 2026-10-21); no Kubernetes |
| IaC repo and paths | none named in environment.md (gap) |
| Core flows served | checkout (`POST /orders`) and order status updates (`PATCH /orders/{id}`) from environment.md; both appeared in error lines on 2026-10-21 (verified 2026-10-21, W2-Q5b) |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (alarm-name prefix, label value, load balancer suffix, job name) |
|---|---|---|
| none | one service, one region, one target group | n/a |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | unknown (not investigated; WAF not in the path of this report) |
| Client-ID header name | unknown |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | CloudWatch log group `/ecs/orders-api`; JSON lines with fields level, status, route, error_code, msg, duration_ms, ecs_task_revision | (verified 2026-10-21) |
| Sidecar or proxy logs | none known | (unverified) |
| APM or trace service name | none connected | n/a |
| Prometheus job and labels | none connected | n/a |
| Business or flow counters | none named | n/a |
| Compute | ECS cluster `prod`, service `orders-api` (FARGATE, desired 6); task definition family `orders-api` (live revision 42); other families `orders-migrate`, `orders-reconcile` (scheduled task `orders-reconcile:7` runs in cluster `prod`, rule `orders-reconcile-nightly`) | (verified 2026-10-21) |
| Load balancing | ALB `app/prod-public/50dc6c495c0c9188`, target group `targetgroup/orders-api/943f017f100becff` | (verified 2026-10-21) |
| Data stores | Aurora cluster `orders-db` (from environment.md only; AWS/RDS list-metrics and get-metric-data returned empty replies) | (unverified) |
| Queues and streams | none known | n/a |
| Functions | none known | n/a |
| Log datasource | CloudWatch Logs via profile `prod-read`; related group `/ecs/orders-reconcile` (listed, not read) | (verified 2026-10-21) for `/ecs/orders-api`; `/ecs/orders-reconcile` listed only |
| Error tracker project | none connected | n/a |
| Code | `example-org/orders-api`, default branch (unverified). Image tag to ref rule: the image tag equals the GitHub release tag name (orders-api:42 image `2026.10.21-1` = release `2026.10.21-1`). Local clone: none | (verified 2026-10-21) for the tag rule; branch (unverified) |
| Tickets and wiki | none | n/a |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| downstream | Aurora `orders-db` | SQL (lock wait errors in app logs show a MySQL-compatible engine) | `orders-db` (unverified) | n/a |
| downstream | payments service (internal by its name) | HTTP; env var `PAYMENTS_URL` (name only; `ECONNRESET` seen on 6 lines on 2026-10-21) | not otherwise identified | none known |
| related job | `orders-reconcile` (ECS scheduled task, rule `orders-reconcile-nightly`, 02:00 UTC daily) | shares the database (both task definitions carry a `DB_HOST` variable; values not compared) | `orders-reconcile:7`, log group `/ecs/orders-reconcile` | n/a |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | n/a | n/a |

## Baseline notes

- Normal load and latency: not readable in this run (request count and latency returned empty replies). Normal 5xx: median 1 per hour, p95 6 per hour (14 days to 2026-10-21 01:30 UTC, W1-Q3).
- Known periodic jobs and their usual effect: `orders-reconcile-nightly`, `cron(0 2 * * ? *)`, EventBridge so UTC, runs about 20 minutes; on 14 of 14 earlier nights the 02:00 UTC hour has 52 to 455 target 5xx; alarm `orders-api-5xx-high` fires on the larger nights (10-08, 10-11, 10-14, 10-16, 10-19, 10-21). `catalog-sitemap-weekly`, `cron(30 3 ? * SUN *)`, no effect seen.
- Known benign noise: none established (no baseline day was queried for ECONNRESET or UPSTREAM_TIMEOUT).

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | n/a | `orders-db` returned empty replies, but it is unverified and the empty reply is not specific to the name (other empty replies in the same run), so it is not moved here |
