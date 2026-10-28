# Profile: notify-worker prod

Last verified: 2026-10-22 · Built by: helper (cheapest tier, simulated inline) and main session · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | notify-worker |
| Environment | prod |
| Account or profile / Region | `prod-read` (account 111122223333) / us-east-1 |
| Cluster, context and namespace | cluster `prod`, context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `notify` |
| IaC repo and paths | `example-org/notify-deploy`, local clone `~/src/notify-deploy`, Helm chart `charts/notify-worker`, values `charts/notify-worker/values-prod.yaml` (verified 2026-10-22: `git log` with the chart path returned commits) |
| Core flows served | transactional email (order confirmations, password resets): this service sends it; critical |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (alarm-name prefix, label value, load balancer suffix, job name) |
|---|---|---|
| replicas | notify-worker-5c8d7b9f4c-8wq2d, -jt6kz, -x4p9n (3 pods, one ReplicaSet) | label `pod-template-hash=5c8d7b9f4c`; no regions, shards or tenants |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none (queue worker, no HTTP clients) |
| Client-ID header name | none |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | none: no log backend; logs only via `kubectl logs` (container `notify-worker`) | (verified 2026-10-22) container name |
| Sidecar or proxy logs | none | - |
| APM or trace service name | none | - |
| Prometheus job and labels | none | - |
| Business or flow counters | none defined in environment.md | - |
| Compute | Deployment `notify-worker` (Helm release `notify-worker`, chart `notify-worker-1.8.0`, app version 3.8.1, strategy Recreate), selector `app.kubernetes.io/instance=notify-worker,app.kubernetes.io/name=notify-worker`; ConfigMap `notify-worker-config` (4 keys); Secret `notify-smtp` (key name `password`, referenced by env var `SMTP_PASSWORD`; by name only) | (verified 2026-10-22) |
| Load balancing | none found (no Service, Ingress or HPA in `notify`) | (verified 2026-10-22) |
| Data stores | none found | (unverified) |
| Queues and streams | SQS `notify-outbound` and `notify-outbound-dlq`, us-east-1, account 111122223333 | (verified 2026-10-22) |
| Functions | none | - |
| Log datasource | none | - |
| Error tracker project | none | - |
| Code | `example-org/notify-worker` (via `gh`), default branch unknown. Image tag to ref rule: image tag `3.8.1` equals Helm appVersion `3.8.1`; the mapping tag to git ref was not tested. | (unverified) |
| Tickets and wiki | none listed | - |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| upstream | SQS queue `notify-outbound` | consumes messages | queue URL in ConfigMap key `NOTIFY_QUEUE_URL` | AWS, internal |
| downstream | SMTP relay | SMTP; host from env var `NOTIFY_SMTP_RELAY_HOST` (app 3.8.1), credentials from Secret `notify-smtp` | host value not recorded | owner and contact route unknown |
| downstream | `notify-outbound-dlq` | dead-letter queue | - | internal |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | - | - |

## Baseline notes

- Normal load and latency: `notify-outbound` depth 7-27 messages at 07:50-08:10 UTC on 2026-10-22 (5-minute maxima), consumers keeping up. No latency data.
- Known periodic jobs and their usual effect: none seen (no CronJobs in the cluster listing).
- Known benign noise: none.

## Stale identifiers

| Identifier | Last run with no data | Note |
|---|---|---|
| none | - | - |
