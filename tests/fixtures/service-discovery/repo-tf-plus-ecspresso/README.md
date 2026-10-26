# repo-tf-plus-ecspresso — Terraform + ecspresso fixture

Two stacks in one repo: a Terraform stack owns the ECS cluster + ALB + IAM roles; an ecspresso stack owns the service + task definition and consumes the TF stack's outputs through ecspresso's `tfstate` plugin (`` {{ tfstate `output.<name>` }} ``, state URL `s3://orderapi-tfstate/platform/terraform.tfstate`).

## What's modelled

`orderapi` — a fictional ECS Fargate service.

- `platform/` (Terraform, 8 resources): ECS cluster, ALB, ALB target group, ALB and task security groups, task and exec IAM roles, ECR repo. The VPC and subnets are **not** managed here: they come in as variables (`vpc_id`, `public_subnets`, `private_subnets`). Outputs: `cluster_name`, `target_group_arn`, `task_role_arn`, `exec_role_arn`, `ecr_repo_url`, `task_subnets`, `task_sg_id`.
- `platform/envs/prod.tfvars` also sets `db_password` (declared `sensitive = true`; the value is a deliberate `REDACTED-FIXTURE-VALUE` marker). It is a **names-only proof**: the catalog must record `db_password = <set in platform/envs/prod.tfvars:6>` and never the value.
- `service/` (ecspresso): one ECS service + task definition; consumes platform's outputs via `{{ tfstate ... }}` (7 references: 1 in `ecspresso.yml`, 3 in the service def, 3 in the task def).

## Stack layout

```
repo-tf-plus-ecspresso/
├── platform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── envs/
│       └── prod.tfvars
└── service/
    ├── ecspresso.yml
    ├── ecs-service-def.json
    ├── ecs-task-def.json
    └── envs/
        └── prod.env
```

## What this fixture exercises in the skill

- **Multi-tool detection:** Both `terraform.md` (matches `platform/*.tf`) and `ecspresso.md` (matches `service/ecspresso.yml`) are loaded.
- **Two stacks listed independently:** the catalog presents `platform` and `service` as separate stacks.
- **Iron Law preserved:** the ecspresso stack's `{{ tfstate }}` references point at the platform stack — they MUST be recorded as a cross-stack dependency, NOT chased into platform's resources.
- **Cross-stack-aware target instance prompt:** the skill prompts "catalog `platform`, `service`, or both?" — both are valid choices; cataloging both is the same as cataloging each separately and noting the dependency between them.
- **Names-only tfvars (secrets by projection):** reading `platform/envs/prod.tfvars` yields every variable name; `db_password` (sensitive variable, key matches `password`) is recorded as `<set in platform/envs/prod.tfvars:6>`. The literal `REDACTED-FIXTURE-VALUE` must appear nowhere in chat output, the catalog or the commit. Terraform state is never read.
