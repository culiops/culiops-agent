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
- **Secrets (references only):** the RDS-managed master secret (`DB_SECRET_ARN` in `values-prod.yaml`), the out-of-band Kubernetes Secret `widgetapi` (External Secrets Operator), and, when `secretsStore.enabled`, a Secrets Manager secret `widgetapi/<env>/db` mounted through the Secrets Store CSI Driver (AWS provider) via `templates/secretproviderclass.yaml`. The catalog records secret names, ARNs and key names (`DB_USERNAME`, `DB_PASSWORD`), never values.
- **Third-party (not in the repo's IaC):** Datadog (agent subchart + `docs/oncall.md`), PagerDuty (`pagerduty.enabled` in values + `docs/oncall.md`; routing key lives in the `widgetapi` Secret). Stripe, SendGrid and LaunchDarkly are mentioned **only** in `docs/oncall.md` (no Helm value or Terraform resource references them), so they are doc claims, not code facts.

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
│       └── templates/      # incl. secretproviderclass.yaml (CSI, gated by secretsStore.enabled)
└── docs/
    └── oncall.md       # third-party references (Datadog, PagerDuty, Stripe, SendGrid, LaunchDarkly) + a 99.9% / 30d SLO claim
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
- **Third-party signals:** Datadog and PagerDuty appear in Helm values and `docs/oncall.md`; Stripe, SendGrid and LaunchDarkly appear only in `docs/oncall.md`. The skill surfaces all five as "ask the team" entries and does not treat the doc-only three as code facts.
- **Registry modules:** `module.vpc`, `module.eks`, `module.widgetapi_irsa` are `terraform-aws-modules` registry modules — recorded by source + version, not fetched.
- **Secrets by projection:** secret references (Secrets Manager names/ARNs, the `widgetapi` Secret, the CSI-synced `<release>-db` Secret) are recorded by name and key names only.
- **Doc-declared SLO:** `docs/oncall.md:22` declares 99.9% over 30 days. It is a doc claim (`source=doc`, Medium at most) for the signal envelope, to be verified in Datadog, not "no SLO declared".
- **Step 2V live cross-check:** the verification batch (see DRY-RUN-NOTES) finds one cloud drift, one cluster drift and one resource not found live.
- **Naming patterns:** the `widgetapi-<env>-<component>` convention should be inferred from the TF resource names.
