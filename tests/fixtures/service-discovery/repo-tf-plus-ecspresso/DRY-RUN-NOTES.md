# Dry-run of `service-discovery` against `repo-tf-plus-ecspresso`

Simulated run of the IaC path against this fixture. First recorded 2026-04-15; re-run 2026-10-26 for secrets-by-projection.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Multi-tool detection | `tool-detectors/terraform.md` (matches `platform/*.tf`) and `tool-detectors/ecspresso.md` (matches `service/ecspresso.yml`) both loaded and matched |
| Two-stack repo | `platform/` is a Terraform root module (has `terraform { backend "s3" ... }` + `provider "aws"`); `service/` is an ecspresso unit (`ecspresso.yml` with `service_definition:` + `task_definition:`) |
| Iron Law: stop at stack boundary | `service/ecspresso.yml` declares the `tfstate` plugin with `url: s3://orderapi-tfstate/platform/terraform.tfstate`; all seven `` {{ tfstate `output.*` }} `` references (1 in `ecspresso.yml`, 3 in `ecs-service-def.json`, 3 in `ecs-task-def.json`) recorded as cross-stack dependencies, none chased, state never read |
| Stack-selection prompt | Skill asks "which to catalog: `platform`, `service`, or both?" at Step 1 Gate |
| `tfstate` plugin as cross-stack dep | The ecspresso `tfstate` plugin URL maps directly to the platform stack's backend key — recorded as the explicit dependency linkage |
| Names-only tfvars (secrets by projection) | `platform/envs/prod.tfvars:6` sets `db_password`; `platform/variables.tf:6` declares it `sensitive = true`. Catalog records `db_password = <set in platform/envs/prod.tfvars:6>`; see "Names-only tfvars proof" |

## Findings and fixes applied

No findings — the skill produced a complete catalog without surfacing gaps.

Both detectors loaded cleanly and identified non-overlapping stacks. The Terraform detector correctly identified `platform/` as a root module (has `required_providers` + `backend "s3"` at top level, no parent module calling it). The ecspresso detector correctly identified `service/ecspresso.yml` as the stack entry point and attributed `service/ecs-service-def.json` and `service/ecs-task-def.json` as part of the same stack.

The unclassified-deploy-artifacts scan produced no hits: all `*.tf` files attributed to Terraform, all JSON files in `service/` attributed to ecspresso, `envs/prod.env` is a plain env-var file (no deploy-shape keys), `platform/envs/prod.tfvars` is a Terraform vars file (attributed to the Terraform detector).

The `tfstate` plugin URL in `service/ecspresso.yml` (`s3://orderapi-tfstate/platform/terraform.tfstate`) matches the backend config in `platform/main.tf` (`bucket = "orderapi-tfstate"`, `key = "platform/terraform.tfstate"`). The skill correctly records this as a named cross-stack linkage rather than inferring it.

## What a produced doc would look like (for choice = `service`)

`.culiops/service-discovery/orderapi-svc-prod.md` would contain:

- Header: commit SHA, date=2026-04-15, instance=prod, tools=ecspresso.
- `## Resource Inventory` — 2 rows from the ecspresso stack only:

  | Category | Type | Resolved Name | Naming Fragment | Conditional? | Identifying Dimensions | Signal Envelope | Source |
  |----------|------|---------------|-----------------|--------------|------------------------|-----------------|--------|
  | compute | `ecspresso/service` / `aws_ecs_service` | `orderapi-svc-prod` | `orderapi-svc-{env}` | No | env, Fargate, desiredCount from env file | not declared | `service/ecs-service-def.json` |
  | compute | `ecspresso/task` / `aws_ecs_task_definition` | `orderapi-task-prod` | `orderapi-task-{env}` | No | env, CPU=1024, memory=2048, image tag from env | not declared | `service/ecs-task-def.json` |

- `## Dependency Graph` — upstream (critical-path): Terraform `platform` stack at `s3://orderapi-tfstate/platform/terraform.tfstate` — consumes: `output.cluster_name` (ECS cluster), `output.target_group_arn` (ALB target group), `output.task_role_arn` (task IAM role), `output.exec_role_arn` (exec IAM role), `output.ecr_repo_url` (ECR repository), `output.task_subnets` (private subnets), `output.task_sg_id` (task security group). All seven are `{{ tfstate }}` references — NOT resolved at catalog time.
- `## Assumptions and Caveats` — explicit note that `platform/` was NOT chased; the seven `{{ tfstate }}` values were not resolved (state is never read and `terraform output` is never run); live values can only come from Step 2V reads of the AWS resources, if the operator accepts it; platform resources (ECS cluster, ALB, IAM roles, ECR repo, VPC networking) are out of scope for this catalog.

## What a produced doc would look like (for choice = `both`)

Two catalog sections (or two separate files), one per stack:

- **`orderapi-platform-prod.md`** — Terraform stack inventory: 8 resources (ECS cluster, ALB, target group, ALB security group, task security group, task IAM role, exec IAM role, ECR repo). The VPC is not among them: `vpc_id` and the subnet lists are input variables. Naming pattern: `orderapi-{env}[-<component>]`. Dependency edge `service → platform` noted in the platform catalog.
- **`orderapi-svc-prod.md`** — ecspresso stack inventory as described above, with the `service → platform` dependency edge shown in both catalogs.

For the "both" choice, Step 1 would present two separate "which instance?" confirmation prompts — one per stack — since each stack has its own parameter sources (`platform/envs/prod.tfvars` for Terraform; `service/envs/prod.env` for ecspresso).

## Names-only tfvars proof (choice = `platform` or `both`)

`platform/envs/prod.tfvars` is read for variable **names** and non-secret values. At the Step 2 gate the skill shows:

| Parameter | Resolved value |
|-----------|----------------|
| `region` | `us-east-1` |
| `env` | `prod` |
| `vpc_id` | `vpc-redactedabcd1234` |
| `public_subnets` | `subnet-redacted-pub-a`, `subnet-redacted-pub-b` |
| `private_subnets` | `subnet-redacted-prv-a`, `subnet-redacted-prv-b` |
| `db_password` | `<set in platform/envs/prod.tfvars:6>` |

Why withheld: the variable is declared `sensitive = true` (`platform/variables.tf:6`) and the key matches the secret-key list (`password`). The catalog's parameter table and Assumptions record the same placeholder. `db_password` has no consumer in this stack (no resource references `var.db_password`): the skill lists it under Open Questions ("declared and set, not consumed here — who uses it?"), not as a resource.

Assertions (acceptance checks):

- The literal `REDACTED-FIXTURE-VALUE` appears nowhere in the chat presentations, the written catalog, or the commit: `grep -rn "REDACTED-FIXTURE-VALUE" .culiops/` returns nothing.
- `terraform.tfstate`, `terraform output` and `terraform state *` are never read or run.
- `db_password = <set in platform/envs/prod.tfvars:6>` is present.
