# widgetapi — AWS / EKS / Helm fixture

A synthetic repo used to validate the `service-discovery` skill. Nothing here is runnable (the Terraform won't `init`, the Helm chart won't `install` against a real cluster); it is **plausible-looking input** for the skill to read.

## What's modelled

`widgetapi` is a fictional HTTP API for CRUD on "widgets" with image uploads.

- **Runtime:** a Go service in a container, running on Amazon EKS, fronted by an ALB, with CloudFront caching asset routes.
- **Data:**
  - PostgreSQL on RDS (primary + 1 read replica) for widget metadata.
  - ElastiCache Redis for session + rate-limit caches.
  - S3 bucket for user-uploaded widget images.
- **Async:** an SQS queue for image-resize and webhook-delivery work, processed by a second Deployment in the same Helm release.
- **Identity:** pods assume an IRSA role to read/write S3, consume SQS, and read the DB password from AWS Secrets Manager.
- **Observability (third-party):** Datadog agent injected as a sidecar via a Helm subchart; alerts route to PagerDuty via the `PAGERDUTY_ROUTING_KEY` env var resolved from a Kubernetes Secret.

## Environments

Two environments, both in `eu-west-1`:

- `prod` — higher replica counts, multi-AZ RDS, larger Redis node type.
- `staging` — single-AZ RDS, smaller Redis, single replica, same topology.

Environment selection flows through two axes:

- **Terraform**: each stack (`infra/`, `platform/`) is one root module; per-env overrides live in `envs/<env>.tfvars`. An operator runs `terraform -chdir=infra apply -var-file=envs/prod.tfvars` (or similar).
- **Helm**: one chart under `helm/widgetapi/`; per-env overrides live in `values-<env>.yaml`. An operator runs `helm upgrade --install widgetapi helm/widgetapi -f helm/widgetapi/values-<env>.yaml`.

## Stack layout

```
widgetapi-aws-eks/
├── infra/              # stack 1 (shared data plane per env)
│   ├── main.tf         # VPC + RDS + ElastiCache + S3 + SQS
│   ├── variables.tf
│   ├── outputs.tf
│   └── envs/
│       ├── prod.tfvars
│       └── staging.tfvars
├── platform/           # stack 2 (compute / network edge per env)
│   ├── main.tf         # EKS + node group + ALB + CloudFront + IRSA
│   ├── variables.tf
│   ├── outputs.tf
│   └── envs/
│       ├── prod.tfvars
│       └── staging.tfvars
├── helm/
│   └── widgetapi/      # stack 3 (workload, deployed into the EKS cluster)
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-prod.yaml
│       ├── values-staging.yaml
│       └── templates/
└── docs/
    └── oncall.md       # third-party references (Datadog / PagerDuty)
```

`platform` references `infra` outputs via `terraform_remote_state`. The Helm chart is parameterised by the platform stack's outputs (cluster name, ALB DNS, IRSA role ARN) + the infra stack's outputs (RDS host, Redis host, S3 bucket, SQS URL) — those values are written into `values-<env>.yaml` by the operator during deploy.

## Naming convention

All resources follow `widgetapi-<env>-<component>`:

- `widgetapi-prod-db` (RDS instance)
- `widgetapi-prod-cache` (ElastiCache replication group)
- `widgetapi-prod-uploads` (S3 bucket)
- `widgetapi-prod-async` (SQS queue)
- `widgetapi-prod` (EKS cluster)
- `widgetapi-prod-alb` (ALB)
- `widgetapi-prod-cdn` (CloudFront distribution)

## What this fixture exercises in the skill

- **IaC detection (multi-tool):** Terraform *and* Helm in one repo.
- **Stack boundaries:** three stacks — reading `platform` should NOT chase into `infra`'s resources; they are cross-stack *dependencies*.
- **Parameter resolution:** `envs/<env>.tfvars`, `values-<env>.yaml`, and the TF → Helm handoff.
- **Multi-instance:** two environments; skill must ask "which instance?" before cataloguing.
- **Cloud × Kubernetes orthogonality:** runbook needs both `examples/aws.md` (for EKS control plane, ALB, RDS, CloudFront, etc.) AND `examples/kubernetes.md` (for the in-cluster Deployment, HPA, logs, Helm release).
- **Third-party signals:** Datadog and PagerDuty are referenced only in Helm values + `docs/oncall.md`; the skill should surface them and ask the human where to look.
- **Naming patterns:** the `widgetapi-<env>-<component>` convention should be inferred from the TF resource names.
