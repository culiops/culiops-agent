# Dry-run of `service-discovery` against `repo-ecspresso-only`

Simulated run of the 5-step skill against this fixture. Recorded on 2026-04-15.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Detector loading | `tool-detectors/ecspresso.md` matched `ecspresso.yml` (keys `region:`, `cluster:`, `service_definition:`, `task_definition:` present) |
| Unclassified-deploy-artifacts escape hatch | Did NOT fire — every file accounted for: `ecspresso.yml`, `ecs-service-def.json`, `ecs-task-def.json` all attributed to the ecspresso detector; `envs/prod.env` and `envs/staging.env` are plain env-var files, not deploy-shaped |
| Stack boundary | One stack = `ecspresso.yml` + `ecs-service-def.json` + `ecs-task-def.json`; no other stacks in repo |
| Multi-instance | `envs/prod.env` and `envs/staging.env` trigger the "which env?" prompt; prod resolves `DESIRED_COUNT=4`, `TASK_CPU=1024`, `TASK_MEMORY=2048`, `IMAGE_TAG=2026.04.1` |
| Cross-stack dependency, not chased | `tfstate://s3://paymentapi-tfstate/platform/${ENV}/terraform.tfstate` referenced in `ecspresso.yml` `plugins.tfstate`; five `{{ tfstate ... }}` references in service/task defs (target group ARN, subnets, security group, task role ARN, exec role ARN, ECR URL) — all recorded as upstream Terraform dependency, none chased |
| Secret references, never resolved | `ecs-task-def.json` `secrets:` array lists two Secrets Manager ARNs (`paymentapi/${ENV}/db-password`, `paymentapi/${ENV}/stripe-api-key`) — recorded as references only |
| Detector-prefixed raw types | Inventory shows `ecspresso/service` (from `ecs-service-def.json`) and `ecspresso/task` (from `ecs-task-def.json`) |

## Findings and fixes applied

No findings — the skill produced a complete catalog without surfacing gaps.

The ecspresso detector's `## Resource extraction` section cleanly maps both referenced files (service-def → `ecspresso/service`, task-def → `ecspresso/task`), handles container `secrets:` entries as reference-only, and lists all expected cross-stack dependency types (ALB target group, IAM roles, VPC networking, ECR repo, CloudWatch Log Groups). The `## Parameter sources` section correctly identifies `--envfile` as the highest-priority source and `tfstate://` lookups as cross-stack (not chased). The `## Naming pattern hints` section is adequate: `serviceName` resolves to `paymentapi-svc-prod` and `family` resolves to `paymentapi-task-prod` via the env file.

One minor observation (no fix required): the fixture uses the `MUST_ENV:` interpolation prefix (`${MUST_ENV:ENV}`) rather than plain `${ENV}`. The ecspresso detector's `## Parameter sources` section names this pattern explicitly (`${MUST_ENV:VAR_NAME}` / `${env:VAR_NAME}`), so no gap exists.

## What a produced doc would look like

`.culiops/service-discovery/paymentapi-svc-prod.md` would contain:

- Header: commit SHA, date=2026-04-15, instance=prod, tools=ecspresso.
- `## Overview` — fictional payment ECS service in us-east-1, env=prod.
- `## Prerequisites` — `aws` CLI v2, `ecspresso` ≥ v2; AWS auth via SSO; least-privilege: ECS read + ECR read + CloudWatch Logs read; mutations listed (ecspresso deploy, ecspresso scale).
- `## Resource Inventory` — 2 rows:

  | Category | Type | Resolved Name | Naming Fragment | Conditional? | Identifying Dimensions | Signal Envelope | Source |
  |----------|------|---------------|-----------------|--------------|------------------------|-----------------|--------|
  | compute | `ecspresso/service` / `aws_ecs_service` | `paymentapi-svc-prod` | `paymentapi-svc-{env}` | No | env, ECS cluster, Fargate task revision | not declared | `ecs-service-def.json` |
  | compute | `ecspresso/task` / `aws_ecs_task_definition` | `paymentapi-task-prod` | `paymentapi-task-{env}` | No | env, CPU=1024, memory=2048, image tag=2026.04.1 | not declared | `ecs-task-def.json` |

- `## Naming Patterns` — `paymentapi-{component}-{env}` (service: `paymentapi-svc-{env}`; task family: `paymentapi-task-{env}`; log group: `/ecs/paymentapi-{env}`).
- `## Identifying Dimensions` — env, ECS cluster name, container name (`app`), task definition revision, log stream prefix (`ecs/app/`).
- `## Dependency Graph` — upstream (critical-path): Terraform `platform/prod` stack via `tfstate://s3://paymentapi-tfstate/platform/prod/terraform.tfstate` — consumes: ALB target group ARN, private subnets (×2), security group ID, task IAM role ARN, exec IAM role ARN, ECR repository URL; additional: Secrets Manager (db-password reference, stripe-api-key reference — read-only at runtime, not at catalog time); ECS cluster (`paymentapi-cluster-prod`); CloudWatch Log Group (`/ecs/paymentapi-prod`).
- `## Signal Envelopes` — none declared in code; runbook anchor falls back to "no declared SLI — establish baseline."
- `## Investigation Runbooks` — at least one for "user-facing payment requests slow / erroring", with first branch checking the upstream Terraform stack (ALB target group health, VPC connectivity) and second branch checking ECS task health, container logs in `/ecs/paymentapi-prod`.
- `## Stack-Specific Tooling` — `examples/aws.md` plus a 1-line note: "ecspresso CLI (`ecspresso verify`, `ecspresso status`) is the primary operator tool; see https://github.com/kayac/ecspresso."
- `## Assumptions and Caveats` — drift note; `tfstate://` values (target group ARN, subnet IDs, role ARNs, ECR URL) were NOT resolved at catalog time — a `terraform output` against the live state would be needed; Secrets Manager values were not read; desiredCount=4 reflects the `envs/prod.env` setting at the cataloged commit.
- `## Open Questions` — none raised during dry-run.
