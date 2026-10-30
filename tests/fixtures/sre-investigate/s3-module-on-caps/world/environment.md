# sre-investigate environment — example-org

<!-- Stand-in for .culiops/sre-investigate/environment.md in the target repo. -->

## Accounts and access

| Account | ID | Region | AWS profile | Use |
|---|---|---|---|---|
| prod | 111122223333 | us-east-1 | `prod-read` | shop-web (ECS Fargate), ALB `shop-web-alb`, WAF web ACL `example-shop-acl` |

Kubernetes contexts: none (this estate runs on ECS Fargate).

## Backends

| Backend | Covers | Access | Token env var |
|---|---|---|---|
| CloudWatch metrics + alarms | ALB, ECS, WAFV2 | profile `prod-read` | — |
| CloudWatch Logs Insights | `/ecs/*` log groups | profile `prod-read` | — |
| CloudTrail | management events, 90 days | profile `prod-read` | — |

No tracing or error-tracking backend is connected.

## App source

- GitHub repo `example-org/shop-web`, read through `gh` (read-only). No local clone.

## Budgets

- Logs Insights: ask before any single query whose estimated scan exceeds **10 GB**.

## Severity scale

Default scale (SEV1–SEV4). Core flows: checkout (`POST /checkout`), cart (`/api/cart`).
