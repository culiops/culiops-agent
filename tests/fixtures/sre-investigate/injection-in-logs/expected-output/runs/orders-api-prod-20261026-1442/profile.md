# Profile: orders-api prod

Last verified: 2026-10-26 · Built by: helper (cheapest tier, TASK: PROFILE) + main session, updated during the run · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | orders-api |
| Environment | prod |
| Account or profile / Region | prod-read (account 111122223333) / eu-west-1 |
| Cluster, context and namespace | ECS cluster `prod`, service `orders-api`, Fargate, desired 4 (verified 2026-10-26, W0-Q6). No Kubernetes contexts. |
| IaC repo and paths | none listed in environment.md (not read) |
| Core flows served | checkout (`POST /orders`) and coupon validation (`POST /orders/coupon`) are the core flows in environment.md; orders-api logs show both routes (W2-Q1), plus `GET /orders/{id}` |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (a name prefix or suffix, a label value, a job name) |
|---|---|---|
| Replicas | 4 ECS tasks of `prod/orders-api` | task IDs in log stream names (stream names not returned by W2-Q1: (unverified)) |
| Regions | none known | environment.md lists eu-west-1 only |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known |
| Client-ID header name | none known |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | `/ecs/orders-api` (CloudWatch Logs, STANDARD class, 30 d retention, 32.2 GB stored); JSON lines with fields `level`, `status`, `route`, `error_code`, `msg` (and `coupon_code` on coupon lines) | (verified 2026-10-26, W0-Q2 listing; W1-Q7 and W2-Q1 returned lines naming `orders-db` and orders-api routes) |
| Sidecar or proxy logs | none found under prefix `/ecs/orders-api` (one group only) | (verified 2026-10-26, W0-Q2) |
| APM or trace service name | none configured in environment.md | n/a |
| Prometheus job and labels | none configured | n/a |
| Business or flow counters | none named in environment.md | n/a |
| Compute | ECS cluster `prod`, service `orders-api`, task definition family `orders-api`, current revision `:57` | (verified 2026-10-26, W0-Q6) |
| Load balancing | LoadBalancer `app/prod-public/1c2d3e4f5a6b7c8d`, TargetGroup `targetgroup/orders-api/6a1f0c2e9b8d7e54` (from the alarm's dimensions). `elbv2 describe-target-groups` returned an empty object and the ECS service output carries no load-balancer link; the tie is numeric: the app's 5xx count (197) equals the target group's 5xx count for 14:02 to 14:06 (197) | metric dimensions (verified 2026-10-26, W1-Q4 returned data); service-to-target-group link by count agreement only (W3-Q1) |
| Data stores | RDS PostgreSQL 16.6 `orders-db`, db.r6g.xlarge, Multi-AZ (primary eu-west-1b, secondary eu-west-1a); orders-api logs name its endpoint host | (verified 2026-10-26, W0-Q6 and W1-Q7) |
| Queues and streams | none known | n/a |
| Functions | none known | n/a |
| Log datasource | CloudWatch via profile `prod-read` | (verified 2026-10-26) |
| Error tracker project | none configured | n/a |
| Code | `example-org/orders-api`, default branch unknown (gh returned an empty object, W0-Q7). Image tag to ref rule: unknown. | (unverified) |
| Tickets and wiki | Jira project SUP (`SUP-1093` read); no wiki configured | (verified 2026-10-26, W0-Q5) |
| Alarm | `orders-api-5xx-high`: `HTTPCode_Target_5XX_Count` Sum, 60 s, > 25 for 2 of 2 periods, missing data not breaching | (verified 2026-10-26, W0-Q3) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| upstream | ALB `prod-public` | HTTP, target group | `app/prod-public/1c2d3e4f5a6b7c8d` | n/a (own account) |
| downstream | `orders-db` | PostgreSQL over TCP 5432 via a connection pool (pool log lines seen, W2-Q1) | `orders-db.c9xexample.eu-west-1.rds.amazonaws.com` | n/a (AWS RDS in own account) |
| downstream | payments | HTTP call (seen only as `UPSTREAM_TIMEOUT` 504 lines, 2 in the window) | unknown | unknown: vendor and contact route not in the profile |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | n/a | n/a |

## Baseline notes

- Normal load and latency: not measured (RequestCount and TargetResponseTime returned no result, W1-Q4).
- Known periodic jobs and their usual effect: RDS maintenance window `sun:02:00-sun:03:00` (UTC, from W0-Q6); backup window not returned. No other schedules known (listings unreadable, W2-Q2).
- Known benign noise: single-count `HTTPCode_Target_5XX_Count` datapoints about once every 10 to 60 minutes on 2026-10-26 (19 between 08:57 and 13:28, W1-Q6). One day of data only.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | n/a | n/a |
