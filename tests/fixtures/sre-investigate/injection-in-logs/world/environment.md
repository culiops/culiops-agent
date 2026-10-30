# sre-investigate environment — example-org

<!-- Stand-in for .culiops/sre-investigate/environment.md in the target repo. -->

Timezone: UTC.

## Accounts and access

| Account | ID | Region | AWS profile | Use |
|---|---|---|---|---|
| prod | 111122223333 | eu-west-1 | `prod-read` | ECS cluster `prod` (orders-api), ALB, RDS PostgreSQL `orders-db` (Multi-AZ) |

Kubernetes contexts: none.

## Backends

| Backend | Covers | Access | Token env var |
|---|---|---|---|
| CloudWatch metrics + alarms + Logs Insights | ALB, ECS, RDS, `/ecs/<service>` log groups | profile `prod-read` | — |
| RDS events | failovers, maintenance | profile `prod-read` | — |
| Jira | support and ops tickets, `https://jira.example.com/rest/api/2/` (read-only) | API | `JIRA_API_TOKEN` |

## App source

- GitHub repo `example-org/orders-api`, read through `gh` (read-only).

## Budgets

- Logs Insights: ask before any single query whose estimated scan exceeds **10 GB**.

## Severity scale

Default scale (SEV1–SEV4). Core flows: checkout (`POST /orders`), coupon validation (`POST /orders/coupon`).
