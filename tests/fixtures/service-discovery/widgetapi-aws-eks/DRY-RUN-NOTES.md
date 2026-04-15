# Dry-run of `service-discovery` against `widgetapi-aws-eks`

Simulated run of the 5-step skill against this fixture. Recorded on 2026-04-15.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| IaC tool detection (multi-tool) | Terraform (`*.tf`) + Helm (`Chart.yaml`, `templates/*.yaml`, `values*.yaml`) in one repo |
| Stack boundaries | 3 stacks (`infra/`, `platform/`, `helm/widgetapi/`); platform references infra via `terraform_remote_state` — recorded as dependency, not chased |
| Parameter resolution | `envs/<env>.tfvars` for TF; `values-<env>.yaml` for Helm; prod vs staging |
| Multi-instance | Two envs — skill correctly prompted "which instance?" |
| Cloud × Kubernetes orthogonality | Runbook needs both `examples/aws.md` (EKS control plane, ALB, RDS, ElastiCache, S3, SQS, CloudFront, Secrets Manager) and `examples/kubernetes.md` (Deployment, Service, Ingress, HPA, PDB, Helm release) |
| Third-party SaaS | Datadog, PagerDuty, Stripe, SendGrid, LaunchDarkly referenced in Helm values + `docs/oncall.md`; skill correctly surfaces them as "ask the team" entries outside `examples/` |
| Naming patterns | `widgetapi-${env}-<component>` detected consistently across all TF resources |
| Conditional resources | RDS `deletion_protection` on env==prod; CloudFront `price_class` on env==prod; cache `automatic_failover_enabled` on num_nodes>1; Helm `web.autoscaling.enabled`, `ingress.enabled`, `podDisruptionBudget.enabled` |
| No declared SLO | Nothing in code declares an SLO — runbook anchor falls back to "no declared SLI — establish baseline" |

## Findings and fixes applied

### F1 — Helm stack rule was ambiguous about base `values.yaml` *(fixed)*

Old wording: "each `values*.yaml` (or each release) is one instance" — but the fixture's base `values.yaml` is defaults, not an instance. Fixed in `SKILL.md` Step 1 stack-layout bullet to distinguish base defaults from per-env instance files.

### F2 — Terraform stack rule didn't name the `*.tfvars` convention *(fixed)*

Old wording only listed Terraform workspaces and Terragrunt as instance-multiplication mechanisms. The fixture uses `envs/<env>.tfvars` passed via `-var-file`, which is the most common Terraform pattern. Fixed in `SKILL.md` Step 1 stack-layout bullet to name it explicitly.

### F3 — Multi-stack cataloging under one env axis *(no change — works as written)*

The fixture has three stacks all parameterized by `env`. Step 1's "which instance?" prompt reads as single-stack, but "instance = env" is cross-stack-aware under current wording. The presentation template lists all in-scope stacks together. No change needed.

### F4 — Inventory table width in chat *(no change — ergonomic, not a correctness issue)*

23 resources × 8 columns is large for a chat presentation but fine in the written doc. Could split into per-category sub-tables during the "Present and STOP" phase at Step 2, but that's an ergonomic tweak, not a correctness gap.

### F5 — Third-party SaaS classification *(no change — covered by §9)*

Step 5 §9 "Stack-Specific Tooling" already specifies a 1-line note per third-party tool outside `examples/`. Datadog / PagerDuty / Stripe / SendGrid / LaunchDarkly all slot in cleanly.

### F6 — No-declared-SLO fallback *(no change — Step 4 bullet 1 already handles it)*

When nothing in code declares an SLO (true for this fixture), Step 4's Anchor line says "no declared SLI — establish a baseline." Confirmed it works.

## What a produced doc would look like

`.culiops/service-discovery/widgetapi-prod.md` would contain:

- Header with commit SHA, date=2026-04-15, instance=prod, tools=Terraform/Helm.
- `## Overview` — fictional HTTP API, runs on EKS, env=prod in eu-west-1.
- `## Prerequisites` — `aws` v2, `kubectl` ≥ 1.28, `helm` ≥ 3.12; AWS auth → `aws eks update-kubeconfig --name widgetapi-prod`; least-privilege: AWS `ReadOnlyAccess` (or scoped) + Kubernetes `view` role in `widgetapi` namespace + Datadog read-only API key; mutations listed (kubectl rollout restart, helm rollback, kubectl scale).
- `## Resource Inventory` — 23 rows grouped by category (compute, storage, database, network, messaging, identity, edge, observability).
- `## Naming Patterns` — `widgetapi-${env}-<component>` with `{env}` placeholder.
- `## Identifying Dimensions` — env, region, pod/replica, CloudFront geography, DB primary vs replica.
- `## Dependency Graph` — platform → infra (cross-stack); helm → platform + infra (cross-stack); third-party upstream: Secrets Manager, Stripe, SendGrid, LaunchDarkly, Datadog; critical-path edges marked.
- `## Signal Envelopes` — mostly "not declared" (establish baseline); HPA target CPU 65% is the one declared saturation limit.
- `## Investigation Runbooks` — 5 trees (latency, 5xx, upload failures, async delay, auth failures).
- `## Stack-Specific Tooling` — `examples/aws.md` + `examples/kubernetes.md`; notes for Datadog/PagerDuty/Stripe/SendGrid/LaunchDarkly.
- `## Assumptions and Caveats` — drift note; no SLO declared; Helm image tag is env-specific (2026.04.1 in prod, 2026.04.1-rc3 in staging).
- `## Open Questions` — any raised during dry-run.
