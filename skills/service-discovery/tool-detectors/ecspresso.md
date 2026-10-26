---
name: ecspresso
url: https://github.com/kayac/ecspresso
deploys: AWS ECS services and task definitions
---

Syntax below follows the ecspresso v2 README (https://github.com/kayac/ecspresso, fetched 2026-10-26). Re-check the README if a repo uses features not listed here.

## File signatures
- Config file named `ecspresso.yml` / `ecspresso.yaml` / `ecspresso.json` / `ecspresso.jsonnet`, or any YAML/JSON/Jsonnet file passed via `--config` / `$ECSPRESSO_CONFIG`. The README documents only `ecspresso.yml` as the default; for other names detect by top-level keys: `region`, `cluster`, `service`, `service_definition`, `task_definition`, `plugins` (any two of these, including `service_definition` or `task_definition`)
- Files referenced by `service_definition:` (a file PATH, typically `ecs-service-def.json` or `*.jsonnet`)
- Files referenced by `task_definition:` (a file PATH, typically `ecs-task-def.json` or `*.jsonnet`)
- `express_definition:` replaces both of the above in Express mode (README, v2.7) — record the referenced file

## Stack boundary
One stack = one ecspresso config file. The service-def and task-def files it references belong to the same stack.

Multi-instance is expressed via:
- separate config files per environment passed with `--config`
- per-environment directories (`prod/ecspresso.yml`, `staging/ecspresso.yml`)
- environment variables read by `must_env` / `env` in the config and definition files

## Secret-bearing files
- NEVER resolve a `tfstate` plugin: reading Terraform state reads secrets. This holds even when the plugin points at an `s3://` URL or a local `*.tfstate`; NEVER open `*.tfstate*`. Record the reference (see Typical cross-stack dependencies).
- `--envfile` / `$ECSPRESSO_ENVFILE` targets are **not opened** (env files are secret-bearing — SKILL.md Constraint 5). Record the file path as a parameter source and ask the operator for any non-secret values needed.
- Container `environment` values in the task definition: record names; withhold a value (`<set in <file>:<line>>`) when the name contains (case-insensitive) any of: `password`, `passwd`, `secret`, `token`, `key`, `apikey`, `api_key`, `private`, `credential`, `dsn`, `conn`, `connection_string`, `auth`, `cert` — unless the value is itself a reference (an ARN or SSM parameter name), which is recorded as a reference.
- Container `secrets:` → record `name` and `valueFrom` reference; never resolve. `secretsmanager_arn` / `ssm` lookups are runtime references.
- `secrets*.yaml`, `*.sops.*`, `*.enc.*` are not opened at all.

## Parameter sources (highest to lowest priority)
- `--envfile <path>` (`$ECSPRESSO_ENVFILE`): env files exported before rendering
- Environment variables read by template functions in the config and definition files: `` {{ must_env `VAR` }} `` (aborts if unset) and `` {{ env `VAR` `default` }} ``; `json_escape` is also available. Record the variable NAME; the value is unresolved unless the operator supplies it
- Jsonnet: `--ext-str KEY=VALUE` / `--ext-code KEY=VALUE` external variables, and native functions `std.native('env')`, `std.native('must_env')` (v2.4+)
- Plugin functions (declared under `plugins:`), each a runtime or cross-stack reference — record, do NOT resolve:
  - `tfstate` plugin: `` {{ tfstate `resource.addr` }} `` / `` {{ tfstatef `aws_subnet.private['%s'].id` ... }} ``, state location in `plugins[].config.url` (`s3://`, `https://`, `remote://`, …) or `config.path`; `config.func_prefix` renames the functions (e.g. `first_tfstate`)
  - `cloudformation` plugin: `` {{ cfn_output `Stack` `Key` }} ``, `` {{ cfn_export `Name` }} ``
  - `` {{ ssm `/path` }} `` (SSM Parameter Store; Jsonnet `ssm` / `ssm_list`)
  - `` {{ secretsmanager_arn `name` }} `` (resolves a secret ARN by name; never read the secret)
- Constants embedded in the JSON / Jsonnet itself

## Resource extraction
- The config's `service:` key gives the ECS service name; `cluster:` the cluster; `region:` the region. `service_definition` is a file path, NOT a nested object, so there is no `service_definition.serviceName`. Use the `service:` value (and `serviceName` inside the referenced file if present; if they differ, record both)
- The file referenced by `service_definition:` → one inventory entry equivalent to `aws_ecs_service` / `AWS::ECS::Service`; raw type: `ecspresso/service`
- The file referenced by `task_definition:` → one inventory entry equivalent to `aws_ecs_task_definition`; raw type: `ecspresso/task`
- Container definitions inside the task definition → record image references, port mappings, log configuration; container `secrets:` entries → reference only
- `loadBalancers:` inside the service definition → ALB target group dependency
- `taskRoleArn` and `executionRoleArn` → IAM role dependencies
- `plugins:` → record each plugin as a configured behavior (`tfstate`, `cloudformation`, …)

## Naming pattern hints
ecspresso does not enforce a naming convention. Record `service:` and `task_definition.family` as-is. If a value uses `` {{ must_env ... }} ``, record the template and the variable name; resolve it only for a value the operator gives.

## Typical cross-stack dependencies
- Terraform state via the `tfstate` plugin (the most common pattern): record the plugin `config.url` / `config.path` and each `tfstate` address used as a CROSS-STACK dependency on the owning Terraform stack. Do not chase or read the state
- CloudFormation via the `cloudformation` plugin: `cfn_output` / `cfn_export` also signal that a CloudFormation stack OWNS the referenced resources (ownership signal; recognition only)
- Secrets Manager / SSM Parameter Store (container `secrets:`, `ssm`, `secretsmanager_arn`)
- ECR repositories (container `image:`)
- ALB target groups (service `loadBalancers:`)
- ECS cluster (`cluster:` in the config)
- CloudWatch Log Groups (container `logConfiguration:`)
