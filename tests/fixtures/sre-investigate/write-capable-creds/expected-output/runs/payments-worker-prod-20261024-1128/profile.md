# Profile: payments-worker prod

Last verified: 2026-10-24 · Built by: helper TASK: PROFILE (cheapest tier, simulated inline), extended by the main session in waves 1-2 · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | payments-worker |
| Environment | prod |
| Account or profile / Region | `prod-ops` (111122223333) / us-east-1 |
| Cluster, context and namespace | cluster `prod`, context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `payments` |
| IaC repo and paths | `example-org/payments-deploy`, local clone `~/src/payments-deploy`; Helm chart `charts/payments-worker/`, values `charts/payments-worker/values-prod.yaml`, template `charts/payments-worker/templates/deployment.yaml` |
| Core flows served | payment capture and refunds processed by payments-worker (critical) |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart |
|---|---|---|
| replicas (3) | pods `payments-worker-6d4f8a2b7c-3mfk8`, `-q7c2z`, `-vn5tr`, on three different nodes | pod name suffix; label `app.kubernetes.io/name=payments-worker` |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none |
| Client-ID header name | none |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | no log backend listed in `environment.md`; logs via `kubectl logs <pod> --previous` | (verified 2026-10-24, W2-Q2..Q4) |
| Sidecar or proxy logs | none | n/a |
| APM or trace service name | none | n/a |
| Prometheus job and labels | none | n/a |
| Business or flow counters | none | n/a |
| Compute | Deployment `payments-worker`; Helm release `payments-worker` (chart payments-worker-2.3.1, app 5.2.0); ConfigMap `payments-worker-config` (keys PAYMENTS_CURRENCY_DEFAULT, PAYMENTS_QUEUE_URL, PAYMENTS_WORKER_CONCURRENCY, LEDGER_BASE_URL); container `payments-worker`; Secret reference `payments-ledger-auth` (key name `password`, read as env LEDGER_API_TOKEN; Secret never read); no Service, Ingress or HPA returned | (verified 2026-10-24, PB-Q1, PB-Q3, PB-Q5, W2-Q1) |
| Load balancing | none returned | (verified 2026-10-24, PB-Q2: empty reply) |
| Data stores | none known | (unverified) |
| Queues and streams | SQS `payments-jobs` (consumed by this worker via env PAYMENTS_QUEUE_URL), `payments-jobs-dlq`; CloudWatch dimension `QueueName` = same names | (verified 2026-10-24, PB-Q4, W1-Q6, W1-Q10) |
| Functions | none | n/a |
| Log datasource | none | n/a |
| Error tracker project | none | n/a |
| Code | `example-org/payments-deploy` (deploy repo only); the worker's own application repo is not named in `environment.md`; default branch unknown. Image tag is the app version (`5.2.0`), not a commit SHA, so a tag cannot be tied to a ref. | (unverified) |
| Tickets and wiki | none | n/a |

## Dependencies

| Direction | Dependency | How | Identifier | Status page or contact |
|---|---|---|---|---|
| upstream (feeds) | SQS queue `payments-jobs` | worker consumes jobs | `payments-jobs` | n/a (AWS) |
| downstream | ledger API | HTTP; endpoint named by env LEDGER_API_BASE_URL (the worker requires it at startup), token via env LEDGER_API_TOKEN from a Secret | env var names only | internal service; owner not recorded |
| downstream | dead-letter queue | after failed receives | `payments-jobs-dlq` | n/a |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | | |

## Baseline notes

- Normal load: `payments-jobs` backlog 10-30 messages between 10:30 and 10:50 UTC on 2026-10-24 (W1-Q6). Longer baselines were not returned (W1-Q7..Q9).
- Known periodic jobs: none found (no CronJobs in namespace `payments`, W2-Q7).
- Known benign noise: none.
- Rollout history: Helm revision 30 on 2026-10-13 15:40 UTC ran 11 days; revision 31 on 2026-10-24 10:52 UTC.

## Stale identifiers

| Identifier | Last run with no data | Note |
|---|---|---|
| none | | |
