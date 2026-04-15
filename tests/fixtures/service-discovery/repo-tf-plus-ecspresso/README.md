# repo-tf-plus-ecspresso — Terraform + ecspresso fixture

Two stacks in one repo: a Terraform stack owns the ECS cluster + ALB + IAM roles; an ecspresso stack owns the service + task definition and consumes the TF stack's outputs via `tfstate://`.

## What's modelled

`orderapi` — a fictional ECS Fargate service.

- `platform/` (Terraform): VPC, ECS cluster, ALB + target group, IAM roles, ECR repo. Outputs: `cluster_name`, `target_group_arn`, `task_role_arn`, `exec_role_arn`, `ecr_repo_url`, `subnets`, `security_group`.
- `service/` (ecspresso): one ECS service + task definition; consumes platform's outputs via `tfstate://`.

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
- **Iron Law preserved:** the ecspresso stack's `tfstate://` references point at the platform stack — they MUST be recorded as a cross-stack dependency, NOT chased into platform's resources.
- **Cross-stack-aware target instance prompt:** the skill prompts "catalog `platform`, `service`, or both?" — both are valid choices; cataloging both is the same as cataloging each separately and noting the dependency between them.
