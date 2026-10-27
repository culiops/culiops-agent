# Dry-run of `service-discovery` against `repo-ecspresso-only`

Simulated run of the IaC path against this fixture. First recorded 2026-04-15; re-run 2026-10-26 for secrets-by-projection and the ecspresso v2 template syntax; re-run 2026-10-27 for the deployed-ref, membership, parameter-provenance and edge-basis rules.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Detector loading | `tool-detectors/ecspresso.md` matched `ecspresso.yml` (keys `region:`, `cluster:`, `service_definition:`, `task_definition:`, `plugins:` present) |
| Unclassified-deploy-artifacts escape hatch | Did NOT fire — every file accounted for: `ecspresso.yml`, `ecs-service-def.json`, `ecs-task-def.json` all attributed to the ecspresso detector; `envs/prod.env` and `envs/staging.env` are plain env-var files, not deploy-shaped |
| Stack boundary | One stack = `ecspresso.yml` + `ecs-service-def.json` + `ecs-task-def.json`; no other stacks in repo |
| Multi-instance | `envs/prod.env` and `envs/staging.env` trigger the "which env?" prompt. They are read as `--envfile` targets, names first: `ENV`, `DESIRED_COUNT`, `TASK_CPU`, `TASK_MEMORY`, `IMAGE_TAG` — none secret-shaped, so prod resolves `DESIRED_COUNT=4`, `TASK_CPU=1024`, `TASK_MEMORY=2048`, `IMAGE_TAG=2026.04.1` |
| Cross-stack dependency, not chased | `` plugins.tfstate.config.url: s3://paymentapi-tfstate/platform/{{ must_env `ENV` }}/terraform.tfstate `` in `ecspresso.yml`; **seven** `{{ tfstate ... }}` calls: `ecs-service-def.json` ×4 (target group ARN, `private_a` and `private_b` subnet IDs, security group ID) + `ecs-task-def.json` ×3 (task role ARN, exec role ARN, ECR repo URL). All recorded as the upstream Terraform dependency, none chased, state never opened |
| Secret references, never resolved | `ecs-task-def.json:16-17` `secrets:` lists two Secrets Manager ARNs (`` paymentapi/{{ must_env `ENV` }}/db-password ``, `.../stripe-api-key`) — recorded as `name` + `valueFrom` reference only; `secretsmanager get-secret-value` is never run |
| Detector-prefixed raw types | Inventory shows `ecspresso/service` (from `ecs-service-def.json`) and `ecspresso/task` (from `ecs-task-def.json`) |

## Findings and fixes applied

No findings — the skill produced a complete catalog without surfacing gaps.

The ecspresso detector's `## Resource extraction` section cleanly maps both referenced files (service-def → `ecspresso/service`, task-def → `ecspresso/task`) and handles container `secrets:` entries as reference-only. `## Parameter sources` identifies `--envfile` as the highest-priority source and the `tfstate` plugin lookups as cross-stack (recorded, never resolved). `## Naming pattern hints`: `serviceName` resolves to `paymentapi-svc-prod` and `family` to `paymentapi-task-prod` once the operator confirms `ENV=prod`.

The fixture uses ecspresso v2 template functions (`` {{ must_env `ENV` }} ``, `` {{ tfstate `addr` }} ``), the syntax the detector documents.

The cluster name is **not** a tfstate reference: `ecspresso.yml:2` builds it from `ENV` (`paymentapi-cluster-prod`). It is recorded as a dependency on the ECS cluster, whose owner is unknown (not in the Terraform references).

## Evidence rules (re-run 2026-10-27)

- **Deployed ref:** the repo shows no pipeline or other record of which ref `ecspresso deploy` runs from, so the ref is `UNVERIFIED`; the skill asks and records the answer as `operator-stated`. `git status --short` on the stack is shown at Gate 1.
- **Membership:** not asked. Every resolved name carries the `paymentapi` prefix (`ecs-service-def.json:2`, `ecs-task-def.json:2`) and the stack is two files for one service. Recorded `membership: single prefix paymentapi, code:ecs-service-def.json:2`; Unattributed: none.
- **Parameter provenance:** values are recorded `value <- file:line`: `ENV <- envs/prod.env:1`, `DESIRED_COUNT <- envs/prod.env:2`, `TASK_CPU <- envs/prod.env:3`, `TASK_MEMORY <- envs/prod.env:4`, `IMAGE_TAG <- envs/prod.env:5`. The `--envfile envs/<env>.env` choice comes from `README.md` and is confirmed by the operator at Gate 1.
- **Edges:** the Terraform `platform/prod` stack is linked by the `tfstate` plugin (`code: ecspresso.yml:7-9`). The code shows the references, not which of them sit on a synchronous request path, so the stack-level edge is `critical-path: unknown` until the operator confirms at the dependency gate.

## What a produced doc would look like

`.culiops/service-discovery/paymentapi-svc-prod.md` would contain:

- Header: commit SHA, date=2026-04-15, instance=prod, tools=ecspresso, `Working tree: clean`, `Deployed ref: <answer> — operator-stated`.
- `## Overview` — fictional payment ECS service in us-east-1, env=prod.
- `## Prerequisites` — `aws` CLI v2, `ecspresso` ≥ v2; AWS auth via SSO; least-privilege: ECS read + ECR read + CloudWatch Logs read; mutations listed (ecspresso deploy, ecspresso scale).
- `## Resource Inventory` — 2 rows:

  | Category | Type | Resolved Name | Naming Fragment | Conditional? | Identifying Dimensions | Signal Envelope | Source |
  |----------|------|---------------|-----------------|--------------|------------------------|-----------------|--------|
  | compute | `ecspresso/service` / `aws_ecs_service` | `paymentapi-svc-prod` | `paymentapi-svc-{env}` | No | env, ECS cluster, Fargate task revision | not declared | `ecs-service-def.json` |
  | compute | `ecspresso/task` / `aws_ecs_task_definition` | `paymentapi-task-prod` | `paymentapi-task-{env}` | No | env, CPU=1024, memory=2048, image tag=2026.04.1 | not declared | `ecs-task-def.json` |

- `## Naming Patterns` — `paymentapi-{component}-{env}` (service: `paymentapi-svc-{env}`; task family: `paymentapi-task-{env}`; log group: `/ecs/paymentapi-{env}`).
- `## Identifying Dimensions` — env, ECS cluster name, container name (`app`), task definition revision, log stream prefix (`ecs/app/`).
- `## Dependency Graph` — upstream (`critical-path: unknown`, basis `code: ecspresso.yml:7-9`; downstream: `none found in this repo — consumers in other repos / stacks are not visible`): Terraform `platform/prod` stack via the `tfstate` plugin (`s3://paymentapi-tfstate/platform/prod/terraform.tfstate`) — consumes (7 references): ALB target group ARN, private subnets (×2), security group ID, task IAM role ARN, exec IAM role ARN, ECR repository URL; additional: Secrets Manager (db-password reference, stripe-api-key reference — read-only at runtime, not at catalog time); ECS cluster (`paymentapi-cluster-prod`); CloudWatch Log Group (`/ecs/paymentapi-prod`).
- `## Signal Envelopes` — none declared in code; runbook anchor falls back to "no declared SLI — establish baseline."
- `## Investigation Runbooks` — at least one for "user-facing payment requests slow / erroring", with first branch checking the upstream Terraform stack (ALB target group health, VPC connectivity) and second branch checking ECS task health, container logs in `/ecs/paymentapi-prod`.
- `## Stack-Specific Tooling` — `examples/aws.md` plus a 1-line note: "ecspresso CLI (`ecspresso verify`, `ecspresso status`) is the primary operator tool; see https://github.com/kayac/ecspresso."
- `## Assumptions and Caveats` — drift note; the seven `{{ tfstate }}` values (target group ARN, subnet IDs, security group ID, role ARNs, ECR URL) were NOT resolved — state is never read and `terraform output` is never run; the live values are only obtainable through the optional Step 2V reads of the AWS resources; Secrets Manager values were not read; desiredCount=4 reflects the `envs/prod.env:2` setting at the cataloged commit; **Unattributed:** none (single prefix `paymentapi`); **Completeness:** the inventory lists what the code declares; resources created outside it (console, runtime, other stacks) are not listed.
- `## Open Questions` — none raised during dry-run.
