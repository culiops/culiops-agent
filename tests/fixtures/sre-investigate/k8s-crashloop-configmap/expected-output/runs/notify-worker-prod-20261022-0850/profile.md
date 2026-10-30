# Profile: notify-worker prod

Last verified: 2026-10-22 · Built by: helper (TASK: PROFILE, cheapest tier), merged by main session · Status: partly unverified

## Identity

| Field | Value |
|---|---|
| Service | notify-worker |
| Environment | prod |
| Account or profile / Region | prod-read / us-east-1 |
| Cluster, context and namespace | cluster `prod`, context arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace `notify` |
| IaC repo and paths | example-org/notify-deploy (clone ~/src/notify-deploy), chart path charts/notify-worker, prod values file charts/notify-worker/values-prod.yaml |
| Core flows served | transactional email (order confirmations, password resets): critical |
| SLO or error-budget source | none |

## Sibling set

| Dimension | Member | How to tell it apart (a name prefix or suffix, a label value, a job name) |
|---|---|---|
| replicas | Deployment notify-worker, desired 3 | pod name `notify-worker-<pod-template-hash>-<suffix>`; label pod-template-hash |

## Client identity (for WAF triangulation)

| Field | Value |
|---|---|
| Session cookie name | none (queue worker, no HTTP front) |
| Client-ID header name | none |

## Identifiers per source

| Source | Identifier | Verified |
|---|---|---|
| Application log label or log group | no log backend; `kubectl logs` of pods of Deployment notify-worker, namespace notify, container `notify-worker` (pod names `notify-worker-<hash>-<suffix>`, tied to the service by the Deployment's selector) | (verified 2026-10-22, W2-Q2) |
| Sidecar or proxy logs | none: one container per pod | (verified 2026-10-22, W2-Q1) |
| APM or trace service name | none listed in environment.md | (unverified) |
| Prometheus job and labels | none listed in environment.md | (unverified) |
| Business or flow counters | none listed in environment.md | (unverified) |
| Compute | namespace notify; Deployment notify-worker (selector app.kubernetes.io/name=notify-worker, app.kubernetes.io/instance=notify-worker; strategy Recreate); ReplicaSets by pod-template-hash; Helm release notify-worker; ConfigMaps notify-worker-config (4 keys), kube-root-ca.crt; Secret reference notify-smtp (key name `password`, object not read); ServiceAccount notify-worker | Deployment, ConfigMaps, Helm release (verified 2026-10-22, W0-Q5, W1-Q5, W1-Q6); Secret notify-smtp (unverified: referenced only, not read) |
| Load balancing | none found (svc, ingress, hpa listing returned no output) | (unverified) |
| Data stores | none seen | (unverified) |
| Queues and streams | SQS notify-outbound, notify-outbound-dlq (us-east-1) | (verified 2026-10-22, W1-Q8 returned datapoints for both) |
| Functions | none seen | (unverified) |
| Log datasource | none | (unverified) |
| Error tracker project | none | (unverified) |
| Code | example-org/notify-deploy, chart path charts/notify-worker (git log returned commits, W0-Q7), default branch unknown; example-org/notify-worker via gh, not queried. Image tag 3.8.1 equals the Helm APP VERSION; tag-to-ref rule not tested. Helm records no commit: tie a release to a commit through the live ConfigMap keys. | notify-deploy path (verified 2026-10-22, W0-Q7); rest (unverified) |
| Tickets and wiki | none listed | (unverified) |

## Dependencies

| Direction | Dependency | How (protocol, queue, shared store) | Identifier | Status page or contact (third parties) |
|---|---|---|---|---|
| downstream of the queue (consumer) | SQS notify-outbound and its DLQ | worker polls the queue | notify-outbound, notify-outbound-dlq | not a third party |
| downstream | SMTP relay (outbound mail) | SMTP; host set by a ConfigMap key | key name only recorded | unknown whether third party; contact not in environment.md |
| upstream | producers of notify-outbound | queue | unknown | unknown |

## Dashboards

| Name | UID or URL | Useful panels |
|---|---|---|
| none | | |

## Baseline notes

- Normal load and latency: not known. Queue notify-outbound held 7-27 visible messages and the DLQ 0 between 07:50 and 08:10 UTC on 2026-10-22 (W1-Q8, one window only).
- Known periodic jobs and their usual effect: none known.
- Known benign noise: none known.

## Stale identifiers

| Identifier | Last empty run | Note |
|---|---|---|
| none | | |
