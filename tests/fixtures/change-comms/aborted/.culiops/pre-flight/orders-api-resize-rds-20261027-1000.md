**Pre-flight assessment for:** `orders-api` / `prod`
**Action:** Resize RDS orders-db from db.t3.medium to db.t3.large
**Date:** 2026-10-27 10:00 (UTC)
**Commit:** `d9e0f1a`
**Target:** profile `acme-prod` / `ap-southeast-1` | Terraform var-file `envs/prod.tfvars`
**Plan hash:** `sha256:7a1c9e…` (SHA-256 of the `terraform plan` output assessed)
**Plan source:** `terraform plan -var-file=envs/prod.tfvars -no-color`
**Delivery model:** CI on merge
**Invoked by:** operator
**Assessor used:** iac-change
**Layers evaluated:** L1 (static) + L2 (human)

## Verdict: RED — HARD BLOCK

## Risk Scorecard

| # | Category | Score | Finding | Evidence | Mitigation |
|---|----------|-------|---------|----------|------------|
| 1 | Blast radius | 🔴 | Plan REPLACES `aws_db_instance.orders` (destroy and create) instead of modifying it in place. The primary datastore for orders-api would be deleted and recreated. | `plan` (1 to destroy, 1 to add: `aws_db_instance.orders` must be replaced) | Do not apply; find what forces replacement |
| 2 | Reversibility | 🔴 | A replaced instance loses its data unless restored from a snapshot; no snapshot configured in the plan. | `plan`, `code:rds.tf` | Take a manual snapshot first |
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
| Plan replaces `orders-db` | `plan` shows `-/+ aws_db_instance.orders (forces replacement)` | — | n/a |

## Hard Blocks

- Replace of `orders-db`: data-loss risk. No justification accepted by the operator.

## Acknowledged Risks

None.

## Mitigations Committed

None.

## Context Provided (L2)

- No active incidents. No deployment freeze. (`operator`)

## L1 Analysis Detail

Scanned: `main.tf`, `rds.tf`, `envs/prod.tfvars`. A changed `identifier` argument in the working tree forces replacement.

## L3 Queries Run

L3 not requested.
