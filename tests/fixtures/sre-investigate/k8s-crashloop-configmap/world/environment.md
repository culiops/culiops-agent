# sre-investigate environment — example-org

<!-- Stand-in for .culiops/sre-investigate/environment.md in the target repo. -->

Timezone: UTC (the on-call team works in UTC).

## Accounts and access

| Account | ID | Region | AWS profile | Use |
|---|---|---|---|---|
| prod | 111122223333 | us-east-1 | `prod-read` | EKS cluster `prod`, SQS queues |

| Kubernetes context | Cluster | Namespaces in scope |
|---|---|---|
| `arn:aws:eks:us-east-1:111122223333:cluster/prod` | `prod` | `notify` |

## Backends

| Backend | Covers | Access | Token env var |
|---|---|---|---|
| kubectl / Helm | workload state, events, logs, release history | context above | — |
| CloudWatch metrics | SQS queue depth | profile `prod-read` | — |

## App source

- Helm values: repo `example-org/notify-deploy`, local clone `~/src/notify-deploy`, path `charts/notify-worker/values-prod.yaml`. Read by ref only.
- App code: `example-org/notify-worker` through `gh` (read-only).

## Budgets

- Logs Insights: ask above 10 GB per query (not expected to be needed here).

## Severity scale

Default scale (SEV1–SEV4). Core flows: transactional email (order confirmations, password resets) sent by `notify-worker`.
