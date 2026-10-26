**Pre-flight assessment for:** `orders-api` / `prod`
**Action:** Resize RDS orders-db from db.t3.medium to db.t3.large
**Date:** 2026-10-27 10:00 (UTC)
**Commit:** `e7f8a9b`
**Target:** profile `acme-prod` / `ap-southeast-1` | Terraform var-file `envs/prod.tfvars`
**Plan hash:** `sha256:7a1c9e…` (SHA-256 of the `terraform plan` output assessed)
**Plan source:** `terraform plan -var-file=envs/prod.tfvars -no-color`
**Delivery model:** CI on merge
**Invoked by:** operator
**Assessor used:** iac-change
**Layers evaluated:** L1 (static) + L2 (human)

## Verdict: YELLOW — PROCEED WITH CAUTION

## Risk Scorecard

| # | Category | Score | Finding | Evidence | Mitigation |
|---|----------|-------|---------|----------|------------|
| 1 | Blast radius | 🟡 | Single DB instance, but it is the primary datastore for orders-api. Instance class change triggers a Multi-AZ failover. | `plan` (1 changed: `aws_db_instance.orders`) | Apply in a low-traffic window |
| 2 | Reversibility | 🟡 | Reverting the class is possible but triggers a second failover. | `plan`, `code:envs/prod.tfvars:12` | Keep revert PR ready |
| 3 | Change velocity | 🟢 | No changes to this module in the past 14 days. | `git log` | — |
| 4 | Dependency impact | 🟢 | Consumers unaffected by this change. | `code:main.tf` | — |
| 5 | Timing context | 🟢 | Business hours, no incident, no freeze. | `operator` (Q1–Q3) | — |
| 6 | Operator familiarity | 🟢 | Operator has made this kind of change before. | `operator` (Q4–Q5) | — |
| 7 | Observability readiness | 🟢 | Dashboards and alarms exist for the service. | `code:monitoring.tf` | — |
| 8 | Cost impact | 🟢 | Negligible monthly delta. | `code` | — |
| 9 | Security posture | 🟢 | No IAM, network or encryption changes. | `plan` | — |
| 10 | Resource health | 🟢 | No live health concerns known. | `operator` | — |

## Evidence

| Fact | Code / plan | Live | Match |
|------|-------------|------|-------|
| `orders-db` class = db.t3.medium | `envs/prod.tfvars:12` | — | code-only (live read not requested) |
| Multi-AZ enabled | `envs/prod.tfvars:14` | — | code-only |

No drift found.

## Hard Blocks

None.

## Acknowledged Risks

- Blast radius 🟡 and Reversibility 🟡: operator acknowledged a short failover blip. (`operator`)

## Mitigations Committed

- Apply in an agreed low-traffic window. (`operator`)

## Context Provided (L2)

- No active incidents. No deployment freeze. Not peak hours. (`operator`)
- Operator has resized RDS instances before. (`operator`)

## L1 Analysis Detail

Scanned: `main.tf`, `rds.tf`, `envs/prod.tfvars`. No catalog. Git history: no changes to `rds.tf` in 14 days.

## L3 Queries Run

L3 not requested.
