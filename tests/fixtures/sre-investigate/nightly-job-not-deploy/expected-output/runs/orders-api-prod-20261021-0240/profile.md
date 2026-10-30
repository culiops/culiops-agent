# Profile: orders-api prod

Last verified: 2026-10-21 · Built by: helper (PROFILE task, cheapest tier), reviewed by main session · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | orders-api |
| Environment | prod (ECS Fargate) |
| Account or profile / Region | prod-read (account 111122223333) / us-east-1 |
| Cluster, context and namespace | ECS cluster `prod`, service `orders-api` (verified 2026-10-21, listed); no Kubernetes |
| IaC repo and paths | none named in environment.md (unverified) |
| Core flows served | checkout (`POST /orders`) and order status updates (`PATCH /orders/{id}`) are the core flows in environment.md; that orders-api serves them is (unverified) |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (a name prefix or suffix, a label value, a job name) |
|---|---|---|
| replicas | the 6 ECS tasks of service orders-api | task ID (last segment of the task ARN) |
| none (no regions, shards or tenants found) | | |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none known |
| Client-ID header name | none known |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | CloudWatch Logs group `/ecs/orders-api` (STANDARD, retention 30 d); JSON lines with fields level, status, route, error_code, msg, duration_ms, ecs_task_revision (revision 42 ties the lines to task definition orders-api:42). Insights scan was about 16x the storedBytes estimate | (verified 2026-10-21, returned log lines in W2-Q5) |
| Sidecar or proxy logs | none known | (unverified) |
| APM or trace service name | none (no tracing backend) | n/a |
| Prometheus job and labels | none (no Prometheus) | n/a |
| Business or flow counters | none named | n/a |
| Compute | ECS cluster `prod`; service `orders-api`; task definition families `orders-api`, `orders-migrate`, `orders-reconcile` | (verified 2026-10-21, listed) |
| Load balancing | LB `app/prod-public/50dc6c495c0c9188`; target group `targetgroup/orders-api/943f017f100becff`; metrics HTTPCode_Target_5XX_Count, HTTPCode_Target_4XX_Count, RequestCount, TargetResponseTime, HealthyHostCount, UnHealthyHostCount | (verified 2026-10-21, listed by list-metrics) |
| Data stores | Aurora `orders-db` (from environment.md) | (unverified; describe-db-clusters returned an empty reply) |
| Queues and streams | none known | (unverified) |
| Functions | none known | (unverified) |
| Log datasource | CloudWatch Logs via profile prod-read | (verified 2026-10-21) |
| Error tracker project | none connected | n/a |
| Code | example-org/orders-api via `gh`; default branch not read. Image tag to ref rule: the image tag is the GitHub release tag (for example 2026.10.21-1 on orders-api:42); commit SHA not resolved (gh compare returned `{}`) | (verified 2026-10-21 for the tag rule via gh release view; default branch unverified) |
| Tickets and wiki | none named | n/a |
| Alarm | `orders-api-5xx-high` (HTTPCode_Target_5XX_Count Sum, period 60, > 25, 2 of 3; SNS oncall-page) | (verified 2026-10-21, listed) |
| Other workload in same log prefix | `/ecs/orders-reconcile` (task family orders-reconcile, task definition orders-reconcile:7, started by EventBridge rule `orders-reconcile-nightly`); a separate workload, not orders-api's logs; its plain-text lines give the job's run window | (verified 2026-10-21, returned log lines in W3-Q1) |
| Schedule | EventBridge rule `orders-reconcile-nightly`, cron(0 2 * * ? *) (UTC), ENABLED; `catalog-sitemap-weekly` cron(30 3 ? * SUN *) | (verified 2026-10-21, W1-Q6, W2-Q2) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| upstream | Application Load Balancer prod-public | HTTP to target group | app/prod-public/50dc6c495c0c9188 | none (own) |
| downstream | Aurora cluster orders-db | database (assumed from environment.md Backends row) | orders-db | none (own) (unverified) |
| downstream | payments service | HTTP via env var PAYMENTS_URL (name only; value not read) | payments | internal-looking; owner and contact not known (unverified) |
| co-tenant on the data store | orders-reconcile nightly job | direct database access (env var names DB_HOST, RECON_LOCK_MODE, RECON_BATCH_SIZE); takes SELECT ... FOR UPDATE row locks on orders rows | task definition orders-reconcile:7 | none (own) |
| unknown | other callers or downstreams | not discovered; no service-discovery catalog and no traces | | |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none (no Grafana connected) | | |

## Baseline notes

- Normal load and latency: not known yet (RequestCount and TargetResponseTime not read yet).
- Known periodic jobs and their usual effect: orders-reconcile-nightly at 02:00 UTC daily runs about 17-20 minutes; orders-api returns a 5xx burst (52 to 455 per hour, above 25 per minute on about every second or third day) while it runs.
- Known benign noise: background of about 1 to 6 target 5xx per hour outside the 02:00 UTC hour (median 1, p95 6, W1-Q4).

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | | |
