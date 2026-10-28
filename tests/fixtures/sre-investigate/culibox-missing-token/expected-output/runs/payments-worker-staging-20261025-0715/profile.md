# Profile: payments-worker staging

Last verified: 2026-10-25 · Built by: helper PROFILE (cheapest tier), merged by the main session · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | payments-worker |
| Environment | staging |
| Account or profile / Region | staging-read (account 444455556666) / eu-west-1 (verified 2026-10-25) |
| Cluster, context and namespace | ECS Fargate cluster `staging`, service `payments-worker`, task definition family `payments-worker` (verified 2026-10-25). No Kubernetes. |
| IaC repo and paths | none named in environment.md (unverified) |
| Core flows served | refunds (handler `refund` seen in logs); payment capture is a core flow in environment.md, handler not seen (unverified) |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (alarm-name prefix, label value, load balancer suffix, job name) |
|---|---|---|
| environment | staging payments-worker | account 444455556666, profile staging-read, cluster staging |
| environment | prod payments-worker | account 111122223333, profile prod-read, cluster prod (unverified; not readable this run) |
| replicas | 2 Fargate tasks in staging | ECS desiredCount 2 (verified 2026-10-25) |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none (queue worker) |
| Client-ID header name | none |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | CloudWatch log group `/ecs/payments-worker` (STANDARD, retention 14 d); JSON fields `task_def_revision`, `error`, `handler`, `file`, `line`, `message_id`, `level` | (verified 2026-10-25) |
| Sidecar or proxy logs | none found | (unverified) |
| APM or trace service name | none configured | (unverified) |
| Prometheus job and labels | none configured | (unverified) |
| Business or flow counters | none in environment.md | (unverified) |
| Compute | ECS cluster `staging`, service `payments-worker`, family `payments-worker` (revision 18 before, 19 since 06:24Z 2026-10-25) | (verified 2026-10-25) |
| Load balancing | none returned (empty reply) | (unverified) |
| Data stores | none returned (empty reply) | (unverified) |
| Queues and streams | SQS `payments-worker-jobs`, `payments-worker-dlq` (eu-west-1) | (verified 2026-10-25) |
| Functions | none | (unverified) |
| Log datasource | CloudWatch Logs through profile staging-read | (verified 2026-10-25) |
| Error tracker project | Sentry org example-org, project payments-worker, token variable SENTRY_AUTH_TOKEN (not set this run) | (unverified) |
| Code | example-org/payments-worker via `gh`; default branch not returned; image tag to ref rule unknown; tags v4.11.0 and v4.12.0 exist | (unverified) |
| Tickets and wiki | none | (unverified) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| upstream | producer of refund and capture jobs | SQS messages | payments-worker-jobs | unknown producer (unverified) |
| downstream | dead-letter queue | SQS redrive (policy not read) | payments-worker-dlq | internal |
| downstream | payment provider, if any | not known | not known | none known |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | — | — |

## Baseline notes

- Normal load: payments-worker-jobs visible depth 0 to 9 (05:30-06:00 and after onset, 5-minute Maximum); payments-worker-dlq 0 before 06:25 on 2026-10-25 (W1-Q7, W1-Q8). Only 1.7 h of metric history was returned.
- Known periodic jobs: none found (schedule listings returned empty replies).
- Known benign noise: 2 lines "SQS ReceiveMessage throttled, retrying" on revision 18 at 03:12 UTC 2026-10-25, a single observation, not enough to call it a rate (W1-Q12).

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | — | — |
