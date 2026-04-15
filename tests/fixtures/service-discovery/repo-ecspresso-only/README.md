# repo-ecspresso-only — ecspresso fixture

A synthetic ecspresso-managed ECS service. Nothing is runnable. Plausible-looking input for the skill to read.

## What's modelled

`paymentapi-svc` — a fictional ECS Fargate service in `us-east-1`, running on a cluster owned by a separate Terraform stack (referenced via `tfstate://`).

- One ECS service (`paymentapi-svc-${ENV}`) on cluster `paymentapi-cluster-${ENV}`.
- One task definition (`paymentapi-task-${ENV}`) with one container pulling from ECR.
- Container reads two secrets from Secrets Manager (DB password, Stripe API key) — referenced by ARN, never resolved.
- Container logs to CloudWatch Log Group `/ecs/paymentapi-${ENV}`.
- Service registers with an ALB target group whose ARN comes from `tfstate://`.

## Environments

Two environments, both in `us-east-1`:

- `prod` — 4 desired tasks, 1 vCPU / 2GB RAM per task.
- `staging` — 1 desired task, 0.5 vCPU / 1GB RAM per task.

Environment selection flows through `--envfile envs/<env>.env`.

## Stack layout

```
repo-ecspresso-only/
├── ecspresso.yml         # the deploy unit
├── ecs-service-def.json  # service definition (referenced by ecspresso.yml)
├── ecs-task-def.json     # task definition (referenced by ecspresso.yml)
└── envs/
    ├── prod.env
    └── staging.env
```

## What this fixture exercises in the skill

- **Detector loading:** `ecspresso.md` matches `ecspresso.yml`; nothing else does.
- **Cross-stack dependency, not chased:** `tfstate://` lookups in `ecspresso.yml` point at a Terraform stack the catalog must NOT chase — recorded as an upstream cross-stack dependency.
- **Secret references, never resolved:** container `secrets:` ARNs to Secrets Manager are recorded as references; values are never read.
- **Multi-instance via envfile:** the skill must ask "which env?" before producing the catalog.
- **Raw-type prefixing:** inventory rows use `ecspresso/service` and `ecspresso/task` raw types alongside their `aws_ecs_*` equivalents.
