# sre-investigate environment — example-org

<!-- Stand-in for .culiops/sre-investigate/environment.md in the target repo. -->

Timezone: America/Bogota (UTC-5, no daylight saving). Reports use UTC with this zone alongside.

## Accounts and access

| Account | ID | Region | AWS profile | Use |
|---|---|---|---|---|
| prod | 111122223333 | eu-west-1 | `prod-read` (SSO) | ECS cluster `prod`: payments-worker, SQS, CloudWatch Logs |
| staging | 444455556666 | eu-west-1 | `staging-read` (SSO) | ECS cluster `staging`: same services |

Kubernetes contexts: none (ECS Fargate only).

## Backends

| Backend | Covers | Access | Token env var |
|---|---|---|---|
| CloudWatch metrics + Logs Insights | ECS, SQS, `/ecs/<service>` log groups | the profile of each account | — |
| Sentry | application errors, org `example-org`, project `payments-worker`, `https://sentry.io/api/0/` | API | `SENTRY_AUTH_TOKEN` |

## App source

- GitHub repo `example-org/payments-worker`, read through `gh` (read-only).

## Budgets

- Logs Insights: ask before any single query whose estimated scan exceeds **5 GB**.

## Severity scale

Default scale (SEV1–SEV4). Core flows: payment capture and refunds. Staging incidents are SEV4 unless they block a release.
