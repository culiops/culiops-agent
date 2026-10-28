# sre-investigate environment — example-org

<!-- Stand-in for .culiops/sre-investigate/environment.md in the target repo. -->

Timezone: Europe/Paris (UTC+2 until 2026-10-25 01:00 UTC, then UTC+1). Reports use UTC with this zone alongside.

## Accounts and access

| Account | ID | Region | AWS profile | Use |
|---|---|---|---|---|
| prod | 111122223333 | us-east-1 | `prod-ops` | EKS cluster `prod`, SQS queues (the profile the platform team uses day to day) |

| Kubernetes context | Cluster | Namespaces in scope |
|---|---|---|
| `arn:aws:eks:us-east-1:111122223333:cluster/prod` | `prod` | `payments` |

## Backends

| Backend | Covers | Access | Token env var |
|---|---|---|---|
| kubectl / Helm | workload state, events, logs, release history | context above | — |
| CloudWatch metrics | SQS queue depth | profile `prod-ops` | — |

## App source

- Helm values: repo `example-org/payments-deploy`, local clone `~/src/payments-deploy`, path `charts/payments-worker/values-prod.yaml`. Read by ref only.

## Budgets

- Logs Insights: ask above 10 GB per query (not expected to be needed here).

## Severity scale

Default scale (SEV1–SEV4). Core flows: payment capture and refunds processed by `payments-worker`.
