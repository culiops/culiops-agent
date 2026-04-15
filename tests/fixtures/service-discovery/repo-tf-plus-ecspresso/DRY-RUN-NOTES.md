# Dry-run of `service-discovery` against `repo-tf-plus-ecspresso`

Simulated run of the 5-step skill against this fixture. Recorded on 2026-04-15.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Multi-tool detection | `tool-detectors/terraform.md` (matches `platform/*.tf`) and `tool-detectors/ecspresso.md` (matches `service/ecspresso.yml`) both loaded and matched |
| Two-stack repo | `platform/` is a Terraform root module (has `terraform { backend "s3" ... }` + `provider "aws"`); `service/` is an ecspresso unit (`ecspresso.yml` with `service_definition:` + `task_definition:`) |
| Iron Law: stop at stack boundary | `service/ecspresso.yml` references `platform/`'s outputs via `tfstate://s3://orderapi-tfstate/platform/terraform.tfstate`; all seven `{{ tfstate `output.*` }}` references in service JSON files recorded as cross-stack dependencies, none chased |
| Stack-selection prompt | Skill asks "which to catalog: `platform`, `service`, or both?" at Step 1 Gate |
| `tfstate://` as cross-stack dep | The ecspresso `tfstate` plugin URL maps directly to the platform stack's backend key — recorded as the explicit dependency linkage |

## Findings and fixes applied

No findings — the skill produced a complete catalog without surfacing gaps.

Both detectors loaded cleanly and identified non-overlapping stacks. The Terraform detector correctly identified `platform/` as a root module (has `required_providers` + `backend "s3"` at top level, no parent module calling it). The ecspresso detector correctly identified `service/ecspresso.yml` as the stack entry point and attributed `service/ecs-service-def.json` and `service/ecs-task-def.json` as part of the same stack.

The unclassified-deploy-artifacts scan produced no hits: all `*.tf` files attributed to Terraform, all JSON files in `service/` attributed to ecspresso, `envs/prod.env` is a plain env-var file (no deploy-shape keys), `platform/envs/prod.tfvars` is a Terraform vars file (attributed to the Terraform detector).

The `tfstate://` URL in `service/ecspresso.yml` (`s3://orderapi-tfstate/platform/terraform.tfstate`) matches the backend config in `platform/main.tf` (`bucket = "orderapi-tfstate"`, `key = "platform/terraform.tfstate"`). The skill correctly records this as a named cross-stack linkage rather than inferring it.

## What a produced doc would look like (for choice = `service`)

`.culiops/service-discovery/orderapi-svc-prod.md` would contain:

- Header: commit SHA, date=2026-04-15, instance=prod, tools=ecspresso.
- `## Resource Inventory` — 2 rows from the ecspresso stack only:

  | Category | Type | Resolved Name | Naming Fragment | Conditional? | Identifying Dimensions | Signal Envelope | Source |
  |----------|------|---------------|-----------------|--------------|------------------------|-----------------|--------|
  | compute | `ecspresso/service` / `aws_ecs_service` | `orderapi-svc-prod` | `orderapi-svc-{env}` | No | env, Fargate, desiredCount from env file | not declared | `service/ecs-service-def.json` |
  | compute | `ecspresso/task` / `aws_ecs_task_definition` | `orderapi-task-prod` | `orderapi-task-{env}` | No | env, CPU=1024, memory=2048, image tag from env | not declared | `service/ecs-task-def.json` |

- `## Dependency Graph` — upstream (critical-path): Terraform `platform` stack at `s3://orderapi-tfstate/platform/terraform.tfstate` — consumes: `output.cluster_name` (ECS cluster), `output.target_group_arn` (ALB target group), `output.task_role_arn` (task IAM role), `output.exec_role_arn` (exec IAM role), `output.ecr_repo_url` (ECR repository), `output.task_subnets` (private subnets), `output.task_sg_id` (task security group). All seven output values are `tfstate://` references — NOT resolved at catalog time.
- `## Assumptions and Caveats` — explicit note that `platform/` was NOT chased; `tfstate://` values were not de-referenced at catalog time and would require `terraform output` against the live state; platform resources (ECS cluster, ALB, IAM roles, ECR repo, VPC networking) are out of scope for this catalog.

## What a produced doc would look like (for choice = `both`)

Two catalog sections (or two separate files), one per stack:

- **`orderapi-platform-prod.md`** — Terraform stack inventory: 7 resources (ECS cluster, ALB, target group, ALB security group, task security group, task IAM role, exec IAM role, ECR repo). Naming pattern: `orderapi-{env}[-<component>]`. Dependency edge `service → platform` noted in the platform catalog.
- **`orderapi-svc-prod.md`** — ecspresso stack inventory as described above, with the `service → platform` dependency edge shown in both catalogs.

For the "both" choice, Step 1 would present two separate "which instance?" confirmation prompts — one per stack — since each stack has its own parameter sources (`platform/envs/prod.tfvars` for Terraform; `service/envs/prod.env` for ecspresso).
