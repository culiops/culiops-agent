# Profile: payments-worker prod

Last verified: 2026-10-24 · Built by: helper (cheapest tier, simulated inline) then updated by the main session after waves 1 and 2 · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | payments-worker |
| Environment | prod |
| Account or profile / Region | prod-ops / us-east-1 (account 111122223333) |
| Cluster, context and namespace | EKS cluster `prod` (verified 2026-10-24), context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `payments` |
| IaC repo and paths | example-org/payments-deploy, local clone `~/src/payments-deploy`; chart `charts/payments-worker/` (`templates/deployment.yaml`, `values-prod.yaml`); Helm release `payments-worker`, chart payments-worker-2.3.1, app 5.2.0, revision 31 (verified 2026-10-24) |
| Core flows served | payment capture and refunds processed by payments-worker (core, from environment.md) |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart |
|---|---|---|
| replicas (3) | payments-worker-6d4f8a2b7c-3mfk8, -q7c2z, -vn5tr (verified 2026-10-24) | pod name suffix; all carry app.kubernetes.io/name=payments-worker |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none (queue worker, no HTTP path) |
| Client-ID header name | none |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | none listed in environment.md; `kubectl logs` on the pods (returned lines with `--previous`) | (verified 2026-10-24) for kubectl logs; no aggregator |
| Sidecar or proxy logs | none | - |
| APM or trace service name | none listed | - |
| Prometheus job and labels | none listed | - |
| Business or flow counters | none listed | - |
| Compute | namespace `payments`; Deployment `payments-worker` (selector app.kubernetes.io/instance=payments-worker, app.kubernetes.io/name=payments-worker; strategy Recreate); ConfigMaps `payments-worker-config` (keys by name: LEDGER_BASE_URL, PAYMENTS_CURRENCY_DEFAULT, PAYMENTS_QUEUE_URL, PAYMENTS_WORKER_CONCURRENCY) and `kube-root-ca.crt`; Secret `payments-ledger-auth` (named by the pod spec, never read); no Service, Ingress or HPA | (verified 2026-10-24) except the Secret, named only |
| Load balancing | none (queue worker) | - |
| Data stores | none listed | - |
| Queues and streams | `payments-jobs`, `payments-jobs-dlq` (us-east-1, account 111122223333); the DLQ pairing of the two is not confirmed | queues (verified 2026-10-24); pairing (unverified) |
| Functions | none | - |
| Log datasource | none | - |
| Error tracker project | none | - |
| Code | example-org/payments-deploy, default branch (unverified); image `111122223333.dkr.ecr.us-east-1.amazonaws.com/payments-worker:5.2.0`; application source repo not listed. Image tag to ref rule: unknown | (unverified) |
| Tickets and wiki | none listed | - |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| upstream | SQS queue payments-jobs | consumes jobs | payments-jobs (verified 2026-10-24) | not a third party |
| downstream | Ledger API | HTTP; endpoint from a config key (LEDGER_BASE_URL since revision 31, LEDGER_API_BASE_URL before; app 5.2.0 requires the old name), credential from Secret `payments-ledger-auth` | config key names above (verified 2026-10-24); no call to the API seen | owner unknown; PR #377 mentions a "shared ledger client" |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none listed | - | - |

## Baseline notes

- Normal load and latency: payments-jobs depth 10 to 30 at 10:30-10:50 UTC on 2026-10-24 (one 20-minute sample, 5-minute maxima); no seven-day baseline.
- Known periodic jobs and their usual effect: none found (no CronJobs, no scheduled EventBridge rules or Scheduler schedules).
- Known benign noise: none.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | - | - |
