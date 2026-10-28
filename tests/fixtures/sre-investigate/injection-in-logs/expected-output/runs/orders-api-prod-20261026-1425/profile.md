# Profile: orders-api prod

Last verified: 2026-10-26 · Built by: helper `TASK: PROFILE` (cheapest tier, simulated inline) plus main session after wave 1 and 2 · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | orders-api |
| Environment | prod |
| Account or profile / Region | prod-read (account 111122223333) / eu-west-1 |
| Cluster, context and namespace | ECS cluster `prod`, service `orders-api`, Fargate, 4 desired / 4 running, task definition orders-api:57 (verified 2026-10-26, W0-Q5). No Kubernetes. |
| IaC repo and paths | none declared in environment.md (unverified) |
| Core flows served | checkout `POST /orders` and coupon validation `POST /orders/coupon` (named in environment.md; both routes seen in /ecs/orders-api logs, W3-Q1; no business counter defined) |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart |
|---|---|---|
| region | eu-west-1 | alarm name suffix `euw1` (orders-api-5xx-high-euw1). No other region or shard is declared (unverified that none exists). |
| replicas | 4 Fargate tasks | not separable in ALB target-group metrics; per-task data would need log streams or ECS metrics (not queried) |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known (not discovered) |
| Client-ID header name | none known (not discovered) |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | CloudWatch Logs group `/ecs/orders-api`, STANDARD class, retention 30 days, about 32.2 GB stored. JSON events with fields `level`, `msg`, `status`, `route`, `error_code` | (verified 2026-10-26, W0-Q4, W2-Q1, W3-Q1) |
| Sidecar or proxy logs | none found (only one group matched the prefix) | (unverified) |
| APM or trace service name | none (no trace backend in environment.md) | n/a |
| Prometheus job and labels | none (not in environment.md) | n/a |
| Business or flow counters | none defined for the core flows | n/a |
| Compute | ECS cluster `prod`, service `orders-api` | (verified 2026-10-26, W0-Q5) |
| Load balancing | LoadBalancer `app/prod-public-euw1/1c2d3e4f5a6b7c8d`, TargetGroup `targetgroup/orders-api/6a1f0c2e9b8d7e54` (from the alarm definition; `elbv2 describe-target-groups` returned an empty reply, W0-Q7) | (verified 2026-10-26 as alarm dimensions, W1-Q8; metric data returned through a SEARCH on the term "orders", not pinned to these dimensions) |
| Alarm | `orders-api-5xx-high-euw1`: HTTPCode_Target_5XX_Count, Sum, period 60, 2 of 2 datapoints above 25, TreatMissingData notBreaching | (verified 2026-10-26, W1-Q8) |
| Data stores | RDS PostgreSQL 16.6 `orders-db`, db.r6g.xlarge, Multi-AZ (primary eu-west-1b, standby eu-west-1a), maintenance window sun:02:00-sun:03:00 UTC | (verified 2026-10-26, W0-Q6) |
| Queues and streams | none found | (unverified) |
| Functions | none found | (unverified) |
| Log datasource | CloudWatch Logs through profile prod-read | (verified 2026-10-26) |
| Error tracker project | none in environment.md | n/a |
| Code | example-org/orders-api via read-only `gh`; default branch and image-tag-to-ref rule unknown | (unverified) |
| Tickets and wiki | Jira `https://jira.example.com`, key prefix SUP | (verified 2026-10-26, W0-Q3) |

## Dependencies

| Direction | Dependency | How | Identifier | Status page or contact |
|---|---|---|---|---|
| downstream | orders-db (PostgreSQL, Multi-AZ) | TCP 5432 from the app's connection pool | `orders-db` | AWS-managed (RDS); no vendor contact needed |
| downstream | "payments" | log message `upstream timeout calling payments` (2 occurrences 14:00-14:10) | unknown | unknown whether internal or third party (unverified); not in environment.md |
| upstream | Application Load Balancer prod-public-euw1 | HTTPS to target group orders-api | see Load balancing | AWS-managed |

No service-discovery catalog exists (`.culiops/service-discovery/` not found), so this map comes from the profile build and the logs only.

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | | |

## Baseline notes

- Normal load and latency: not known (request count and p95 were not returned, W1-Q5).
- Known periodic jobs and their usual effect: none found (EventBridge rules, EventBridge Scheduler and ECS scheduled scaling actions returned empty replies, W1-Q2, W1-Q3). RDS maintenance window Sunday 02:00-03:00 UTC.
- Known benign noise: ALB target 5xx of 0 to 1 per minute, about 4 per hour (19 single 5xx between 08:57 and 13:28 UTC on 2026-10-26, W1-Q5, W1-Q7). Coupon rejections (HTTP 400) a handful per 10 minutes.

## Stale identifiers

| Identifier | Last run with no data | Note |
|---|---|---|
| none | | |
