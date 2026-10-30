# Profile: payments-worker prod

Last verified: 2026-10-24 · Built by: helper (cheapest tier), tie rule re-applied by main session · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | payments-worker |
| Environment | prod |
| Account or profile / Region | prod-ops / us-east-1 |
| Cluster, context and namespace | cluster prod, context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace payments |
| IaC repo and paths | example-org/payments-deploy, local clone `~/src/payments-deploy`, Helm chart `charts/payments-worker`, values file `charts/payments-worker/values-prod.yaml` (default branch unknown, (unverified)) |
| Core flows served | payment capture and refunds (core, per environment.md) |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (a name prefix or suffix, a label value, a job name) |
|---|---|---|
| replicas | payments-worker-6d4f8a2b7c-3mfk8, -q7c2z, -vn5tr | pod name suffix; all carry pod-template-hash 6d4f8a2b7c (from pod names) |

No regions, shards or tenants are named in environment.md.

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none (worker, not a web service) |
| Client-ID header name | none |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | none: no log backend listed; container logs via kubectl logs on the pods above | (verified 2026-10-24) for the pod names |
| Sidecar or proxy logs | none found | (unverified) |
| APM or trace service name | none listed | (unverified) |
| Prometheus job and labels | none listed | (unverified) |
| Business or flow counters | none listed | (unverified) |
| Compute | namespace payments, Deployment `payments-worker` (3 desired, strategy Recreate), ReplicaSet hash 6d4f8a2b7c (pods carry label pod-template-hash=5c8d7b9f4c: map by owner), ConfigMap `payments-worker-config` (keys PAYMENTS_CURRENCY_DEFAULT, PAYMENTS_QUEUE_URL, PAYMENTS_WORKER_CONCURRENCY, LEDGER_BASE_URL), Helm release `payments-worker` chart payments-worker-2.3.1 | (verified 2026-10-24) |
| Load balancing | no Service, Ingress or HPA returned in payments | (verified 2026-10-24) empty |
| Data stores | none found | (unverified) |
| Queues and streams | `payments-jobs`, `payments-jobs-dlq` (SQS, us-east-1, listed by prefix `payments`); payments-worker is configured for `payments-jobs` (ConfigMap key PAYMENTS_QUEUE_URL names it); whether it is the only consumer is not established | listing (verified 2026-10-24); configured queue (verified 2026-10-24, W2-Q3); sole-consumer (unverified) |
| Functions | none found | (unverified) |
| Log datasource | none | n/a |
| Error tracker project | none | n/a |
| Code | example-org/payments-deploy (Helm values). Image tag to ref rule: unknown. Application source repo not listed in environment.md. | (unverified) |
| Tickets and wiki | none listed | n/a |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| upstream | payments-jobs queue | SQS, configured through ConfigMap key PAYMENTS_QUEUE_URL | payments-jobs, DLQ payments-jobs-dlq | none (AWS) |
| downstream | internal ledger service | HTTP, configured through ConfigMap key LEDGER_BASE_URL (was LEDGER_API_BASE_URL until Helm revision 31) and Secret-backed LEDGER_API_TOKEN; not queried | (unverified) | owning team unknown |

No service-discovery catalog exists (`.culiops/service-discovery` not found). Downstream dependencies not yet known.

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none | | |

## Baseline notes

- Normal load and latency: not known. payments-jobs visible messages 10-30 at 10:30-10:50 UTC on 2026-10-24 (20 minutes of data only); DLQ 0.
- Known periodic jobs and their usual effect: none found (no CronJob, no EventBridge rule or Scheduler schedule named payments*)
- Known benign noise: none known

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | | |
