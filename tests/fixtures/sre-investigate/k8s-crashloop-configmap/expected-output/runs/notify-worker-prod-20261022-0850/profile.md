# Profile: notify-worker prod

Last verified: 2026-10-22 · Built by: helper PROFILE (simulated inline, cheapest tier), updated by the main session after waves 2 and 3 · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | notify-worker |
| Environment | prod |
| Account or profile / Region | `prod-read` (account 111122223333) / us-east-1 |
| Cluster, context and namespace | cluster `prod`, context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `notify` |
| IaC repo and paths | example-org/notify-deploy, local clone `~/src/notify-deploy`, values file `charts/notify-worker/values-prod.yaml` (verified 2026-10-22: a git log and diff on the path returned it, W2-Q3, W3-Q1) |
| Core flows served | transactional email (order confirmations, password resets); critical |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart |
|---|---|---|
| replicas | pods `notify-worker-5c8d7b9f4c-8wq2d`, `-jt6kz`, `-x4p9n` (current ReplicaSet `notify-worker-5c8d7b9f4c`; previous `notify-worker-7f6b8c5d2e`, 0 replicas) | labels `app.kubernetes.io/name=notify-worker`, `app.kubernetes.io/instance=notify-worker`; no regions, shards or tenants |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none (queue consumer, no HTTP entry) |
| Client-ID header name | none |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | `kubectl logs <pod> -n notify`, pods of Deployment `notify-worker`; no log aggregator listed | (verified 2026-10-22) via W2-Q2: the three lines returned for pods whose names share the Deployment's ReplicaSet and name the service version `notify-worker 3.8.1` |
| Sidecar or proxy logs | none (single container `notify-worker` per pod) | (verified 2026-10-22) via W2-Q1 |
| APM or trace service name | none (no trace backend in environment.md) | n/a |
| Prometheus job and labels | none (no Prometheus in environment.md) | n/a |
| Business or flow counters | none configured for the email flow | n/a |
| Compute | namespace `notify`; Deployment `notify-worker` (strategy Recreate); Helm release `notify-worker`; ConfigMaps `notify-worker-config` (envFrom), `kube-root-ca.crt`; ServiceAccount `notify-worker` | (verified 2026-10-22) via W0-Q7, W0-Q8, W0-Q10, W2-Q1, W3-Q3 |
| Load balancing | none (queue consumer) | n/a |
| Data stores | none known | (unverified) |
| Queues and streams | SQS `notify-outbound`, `notify-outbound-dlq` (CloudWatch dimension QueueName, same names) | (verified 2026-10-22) via W0-Q9, W1-Q6 |
| Functions | none | n/a |
| Log datasource | none; kubectl only | n/a |
| Error tracker project | none | n/a |
| Code | example-org/notify-worker via `gh` (read-only), default branch unknown, not read this run. Image `111122223333.dkr.ecr.us-east-1.amazonaws.com/notify-worker`, tag `3.8.1` equals the Helm app version; tag to ref rule not resolved | repo (unverified); image tag (verified 2026-10-22) via W2-Q1 |
| Tickets and wiki | none | n/a |

## Dependencies

| Direction | Dependency | How | Identifier | Status page or contact |
|---|---|---|---|---|
| upstream (work source) | SQS queue | consumes | `notify-outbound` | n/a (AWS) |
| downstream | SQS dead-letter queue | redrive target | `notify-outbound-dlq` | n/a |
| downstream | SMTP relay | SMTP; the host is set through a ConfigMap key whose name changed in commit 3f9a1c2 (old key `NOTIFY_SMTP_RELAY_HOST`, new key `SMTP_RELAY_HOST`); host value not recorded | ConfigMap `notify-worker-config` | none recorded |
| downstream | SMTP credentials | env var `SMTP_PASSWORD` from Secret `notify-smtp` key `password` (names only; Secret not read) | Secret `notify-smtp` | n/a |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none known | | |

## Baseline notes

- Normal load and latency: queue `notify-outbound` visible depth 7-27 and dead-letter queue 0 between 07:50 and 08:10 UTC on 2026-10-22 (W1-Q6, a single 20-minute sample, not a 14-day baseline).
- Known periodic jobs and their usual effect: none known (no CronJobs in the cluster listing, no scheduled EventBridge rules; W2-Q4).
- Known benign noise: none known.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | | |
