# sre-investigate environment — example-org

<!-- Stand-in for .culiops/sre-investigate/environment.md in the target repo. -->

Timezone: America/Sao_Paulo (UTC-3, no daylight saving). Reports use UTC with this zone alongside.

## Accounts and access

| Account | ID | Region | AWS profile | Use |
|---|---|---|---|---|
| prod | 111122223333 | us-east-1 | `prod-read` | EKS cluster `prod`, CloudWatch Logs |

| Kubernetes context | Cluster | Namespaces in scope |
|---|---|---|
| `arn:aws:eks:us-east-1:111122223333:cluster/prod` | `prod` | `catalog` |

## Backends

| Backend | Covers | Access | Token env var |
|---|---|---|---|
| Prometheus | app RED metrics (`http_server_request_duration_seconds`, label `service`) | `$PROM_URL` (`https://prometheus.example.com`) | — (network-restricted, no token) |
| Tempo | traces, `resource.service.name` | `$TEMPO_URL` (`https://tempo.example.com`) | — |
| CloudWatch Logs Insights | container logs shipped by Fluent Bit, group `/eks/prod/<service>` | profile `prod-read` | — |
| kubectl / Helm | workload state, events, rollout and release history | context above | — |

## App source

- GitHub repo `example-org/catalog-api`, read through `gh` (read-only). Helm values in `example-org/catalog-deploy`.

## Budgets

- Logs Insights: ask before any single query whose estimated scan exceeds **1 GB** (container logs here are verbose).

## Severity scale

Default scale (SEV1–SEV4). Core flows: product page (`GET /products/{id}`), search (`GET /search`).
