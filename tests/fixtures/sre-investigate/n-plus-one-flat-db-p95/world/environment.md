# sre-investigate environment — example-org

<!-- Stand-in for .culiops/sre-investigate/environment.md in the target repo. -->

Timezone: Australia/Brisbane (UTC+10, no daylight saving). Reports use UTC with this zone alongside.

## Accounts and access

| Account | ID | Region | AWS profile | Use |
|---|---|---|---|---|
| prod | 111122223333 | us-east-1 | `prod-read` | EKS cluster `prod`, RDS PostgreSQL `orders-db` |

| Kubernetes context | Cluster | Namespaces in scope |
|---|---|---|
| `arn:aws:eks:us-east-1:111122223333:cluster/prod` | `prod` | `orders` |

## Backends

All three go through the Grafana datasource proxy at `https://grafana.example.com` (or a Grafana MCP server with the same token).

| Backend | Datasource UID | Token env var |
|---|---|---|
| Prometheus | `prom-prod` | `GRAFANA_SERVICE_ACCOUNT_TOKEN` |
| Loki | `loki-prod` | `GRAFANA_SERVICE_ACCOUNT_TOKEN` |
| Tempo | `tempo-prod` | `GRAFANA_SERVICE_ACCOUNT_TOKEN` |
| CloudWatch (RDS metrics) | — | profile `prod-read` |
| kubectl / Helm | — | context above |

## App source

- GitHub repo `example-org/orders-api`, read through `gh` (read-only).
- Local clone: `~/src/orders-api` (tags `v2.14.0`, `v2.15.0` fetched). Read by ref only.

## Budgets

- Logs Insights: not used here. Loki: ask before a query expected to process more than 20 GB.

## Severity scale

Default scale (SEV1–SEV4). Core flows: checkout (`POST /orders`), order history (`GET /orders`).
