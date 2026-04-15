---
name: ecspresso
url: https://github.com/kayac/ecspresso
deploys: AWS ECS services and task definitions
---

## File signatures
- `ecspresso.yml` / `ecspresso.yaml` / `ecspresso-*.yml` with top-level keys including any of: `region:`, `cluster:`, `service_definition:`, `task_definition:`
- Files referenced by `service_definition:` (typically `ecs-service-def.json` or `*.jsonnet`)
- Files referenced by `task_definition:` (typically `ecs-task-def.json` or `*.jsonnet`)

## Stack boundary
One stack = one `ecspresso.yml` config file. The service-def and task-def files it references belong to the same stack.

Multi-instance is expressed via:
- separate `ecspresso-<env>.yml` files passed to `ecspresso --config ecspresso-<env>.yml ...`
- per-environment directories (`prod/ecspresso.yml`, `staging/ecspresso.yml`)
- ecspresso plugins that select per-environment task definition variants

## Parameter sources (highest to lowest priority)
- `--envfile <path>` flag (file of `KEY=VALUE` pairs sourced into the environment)
- `ECSPRESSO_*` environment variables and any other env vars referenced via `${MUST_ENV:VAR_NAME}` / `${env:VAR_NAME}` interpolation in the config or referenced JSON/Jsonnet files
- `tfstate://` lookups (ecspresso reads outputs from a Terraform state file when configured with the `tfstate` plugin) — record the upstream Terraform stack as a CROSS-STACK dependency, do NOT chase it
- `ssm://` lookups (SSM Parameter Store) — record the parameter path as a runtime reference
- Jsonnet TLA / external variables when service-def or task-def is `.jsonnet`
- Constants embedded in the JSON / Jsonnet itself

## Resource extraction
- The file referenced by `service_definition:` → one inventory entry equivalent to `aws_ecs_service` / `AWS::ECS::Service`; raw type: `ecspresso/service`
- The file referenced by `task_definition:` → one inventory entry equivalent to `aws_ecs_task_definition` / `AWS::ECS::TaskDefinition`; raw type: `ecspresso/task`
- Container definitions inside the task definition → record image references, port mappings, log configuration; container `secrets:` entries → record reference, do NOT resolve secret values
- `loadBalancers:` inside the service definition → cross-resource reference to an ALB target group (record as dependency)
- `taskRoleArn` and `executionRoleArn` → IAM role dependencies
- ecspresso plugins declared under `plugins:` → record each plugin as a configured behavior (e.g., `tfstate`, `cloudwatch_logs`, `verify_platform_version`)

## Naming pattern hints
ecspresso does not enforce a naming convention. Record `service_definition.serviceName` and `task_definition.family` as-is. If those values use env-var interpolation (e.g., `"serviceName": "${MUST_ENV:SERVICE_NAME}"`), record the resolved value for the target instance.

## Typical cross-stack dependencies
- Terraform state via `tfstate://` (the most common pattern — service config consumes outputs of a TF stack that owns the cluster, ALB, IAM roles, etc.)
- Secrets Manager / SSM Parameter Store (referenced by container `secrets:`)
- ECR repositories (referenced by container `image:`)
- ALB target groups (referenced by service `loadBalancers:`)
- ECS cluster (referenced by `cluster:` in the ecspresso config)
- CloudWatch Log Groups (referenced by container `logConfiguration:`)
