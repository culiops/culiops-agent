# Profile: payments-worker staging

Last verified: 2026-10-25 · Built by: helper (cheapest tier, TASK: PROFILE), merged by the main session · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | payments-worker |
| Environment | staging (shared account 444455556666; the cluster also runs orders-api) |
| Account or profile / Region | staging-read / eu-west-1 |
| Cluster, context and namespace | ECS Fargate cluster `staging` (no Kubernetes) |
| IaC repo and paths | not listed in environment.md; unknown |
| Core flows served | payment capture and refunds are the core flows in environment.md; which of them this worker serves is not confirmed by a query |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (a name prefix or suffix, a label value, a job name) |
|---|---|---|
| environment | staging | profile staging-read, account 444455556666, cluster `staging` |
| environment | prod | profile prod-read, account 111122223333, cluster `prod` (expired session; not readable this run) |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none (queue worker, not an HTTP service; not queried) |
| Client-ID header name | none |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | `/ecs/payments-worker` (CloudWatch Logs, STANDARD class, retention 14 d, eu-west-1, staging account). JSON lines with fields `level`, `task_def_revision`, `handler`, `error`, `message_id`, `file`, `line` | (verified 2026-10-25, W0-Q5, W1-Q6, W2-Q1) |
| Sidecar or proxy logs | none seen | (unverified) |
| APM or trace service name | none (no trace backend in environment.md) | (unverified) |
| Prometheus job and labels | none (not in environment.md) | (unverified) |
| Business or flow counters | none defined in environment.md | (unverified) |
| Compute | ECS cluster `staging`; service `payments-worker`; task definition family `payments-worker` (current `payments-worker:19`) | cluster (verified 2026-10-25, W0-Q6); service (verified 2026-10-25, W0-Q7); family and revision 19 (verified 2026-10-25, W1-Q1) |
| Load balancing | none known | (unverified) |
| Data stores | none discovered (none listed in environment.md) | (unverified) |
| Queues and streams | `payments-worker-jobs`, `payments-worker-dlq` (staging account, eu-west-1) | (verified 2026-10-25, W0-Q8; both return metric data in W1) |
| Functions | none | (unverified) |
| Log datasource | CloudWatch via profile staging-read | (verified 2026-10-25, W0-Q5) |
| Error tracker project | Sentry org `example-org`, project `payments-worker`, env var `SENTRY_AUTH_TOKEN` | (unverified: token unset) |
| Code | example-org/payments-worker; default branch not read. Newest release range seen: v4.11.0 -> v4.12.0. Image tag to ref rule: unknown (task definition image unreadable in this run, W2-Q3) | repo reachable through gh (verified 2026-10-25, W2-Q2); rule (unverified) |
| Tickets and wiki | none listed | (unverified) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| upstream | producer of `payments-worker-jobs` | SQS messages | unknown (not discoverable from read-only calls so far) | not applicable |
| downstream | dead-letter queue | SQS redrive (redrive policy not read) | `payments-worker-dlq` | not applicable |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | | |

## Baseline notes

- Normal load and latency: jobs queue visible messages 0-9 in 5-min maxima (05:30-07:10, W1-Q4); DLQ 0 before the incident (05:30-06:20). Throughput and age not measured.
- Known periodic jobs and their usual effect: none known.
- Known benign noise: candidate only, no lesson: `SQS ReceiveMessage throttled, retrying` ×2 on the old revision in 03:00-07:15, first at 03:12:07 (W2-Q1).

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
