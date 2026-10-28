# Profile: orders-api prod

Last verified: 2026-10-21 · Built by: helper (TASK: PROFILE, cheapest tier), tie rule re-applied by main session · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | orders-api |
| Environment | prod |
| Account or profile / Region | prod-read (account 111122223333) / us-east-1 |
| Cluster, context and namespace | ECS cluster `prod` (verified 2026-10-21, W0-Q5); service `orders-api` (verified 2026-10-21, W0-Q6). No Kubernetes. |
| IaC repo and paths | none configured in environment.md (gap) |
| Core flows served | checkout (`POST /orders`), order status updates (`PATCH /orders/{id}`), both from environment.md; no counter or datasource named for either |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (a name prefix or suffix, a label value, a job name) |
|---|---|---|
| none | single service in a single region | not applicable. `orders-reconcile` and `orders-migrate` are separate task families, not siblings (they are not behind this target group) |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known (not discovered; no WAF in scope) |
| Client-ID header name | none known |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | CloudWatch log group `/ecs/orders-api` (30-day retention, STANDARD, about 64.4 GB stored); JSON lines with `level`, `status`, `route`, `error_code`, `msg`, `duration_ms`, `ecs_task_revision`. Also `/ecs/orders-reconcile` for the nightly job (about 1.1 GB stored). | (verified 2026-10-21, W2-Q7 and W3-Q3 returned lines; tied to the service: awslogs group named in task definition `orders-api:41`/`:42` (W2-Q3) and `ecs_task_revision` 42 in the lines matches the running revision (W1-Q2)) |
| Sidecar or proxy logs | none discovered | (unverified) |
| APM or trace service name | none (no tracing backend) | not applicable |
| Prometheus job and labels | none (no Prometheus) | not applicable |
| Business or flow counters | none named for checkout or order updates | (unverified) |
| Compute | ECS cluster `prod`, service `orders-api` (6 Fargate tasks, circuit breaker on), task definition family `orders-api` (rev 41 `2026.10.14-2`, rev 42 `2026.10.21-1`); other families `orders-migrate`, `orders-reconcile` (rev 7 `2026.09.30-1`) | (verified 2026-10-21, W0-Q5, W0-Q6, W0-Q7, W1-Q1, W2-Q3, W3-Q5) |
| Load balancing | ALB `app/prod-public/50dc6c495c0c9188`, target group `targetgroup/orders-api/943f017f100becff` (metrics: RequestCount, HTTPCode_Target_5XX_Count, HTTPCode_Target_4XX_Count, TargetResponseTime, HealthyHostCount, UnHealthyHostCount; no HTTPCode_ELB_5XX_Count series in the last two weeks) | (verified 2026-10-21, list-metrics W0-Q8; also the dimensions of alarm W0-Q4) |
| Data stores | Aurora `orders-db` (named in environment.md; `rds describe-db-clusters` returned `{}`) | (unverified) |
| Queues and streams | none discovered | (unverified) |
| Functions | none discovered | (unverified) |
| Log datasource | CloudWatch Logs Insights through profile prod-read | (verified 2026-10-21, W0-Q3) |
| Error tracker project | none connected | not applicable |
| Code | example-org/orders-api via `gh`, no local clone. Image tag to ref rule: the image tag equals the GitHub release tag (`2026.10.21-1`, `2026.10.14-2`). Default branch not read. | (verified 2026-10-21 for the tag rule, W2-Q3 and W2-Q6; default branch unverified) |
| Tickets and wiki | none configured | not applicable |
| Alarm | `orders-api-5xx-high`: HTTPCode_Target_5XX_Count Sum, period 60, 2 of 3 datapoints above 25, actions to an SNS paging topic | (verified 2026-10-21, W0-Q4) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| upstream | ALB `prod-public` | HTTP | `app/prod-public/50dc6c495c0c9188` | none (AWS) |
| downstream | Aurora `orders-db` | database (from environment.md) | `orders-db` | none |
| neighbour (shares the database) | `orders-reconcile` | ECS Fargate task started by EventBridge rule `orders-reconcile-nightly` (`cron(0 2 * * ? *)`, UTC), task definition `orders-reconcile:7` | family `orders-reconcile`, log group `/ecs/orders-reconcile` (verified 2026-10-21, W2-Q1, W3-Q2, W3-Q3) | none |
| downstream | payments (named by env var `PAYMENTS_URL` and a log message "payments call reset by peer"; whether it is internal or a vendor is not known) | HTTP call from orders-api | `PAYMENTS_URL` (name only) | owner and status page unknown |

No third party known to be in the path. No service-discovery catalog exists under the output root.

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | | |

## Baseline notes

- Normal load and latency: request rate and latency not readable in this run (RequestCount and TargetResponseTime came back empty). Target 5xx background is about 1 per minute, in single minutes, with a 14-day hourly median of 1 and p95 of 6 (W1-Q8).
- Known periodic jobs and their usual effect: `orders-reconcile-nightly` starts at 02:00 UTC (11:00 JST) every day and runs about 19–20 minutes, holding row locks on the previous day's orders; orders-api target 5xx rise from 1–2 minutes after the start until the commit. The 02:00 UTC hour totals 52–133 on most mornings and 386–455 every 2–3 days (W1-Q8, W3-Q1, W3-Q3). `catalog-sitemap-weekly` runs Sundays 03:30 UTC (no effect seen). EventBridge Scheduler has no schedules.
- Known benign noise: the 02:00 UTC episode is the incident itself, not noise; a background of about 1 target 5xx in some minutes is normal.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | | |
