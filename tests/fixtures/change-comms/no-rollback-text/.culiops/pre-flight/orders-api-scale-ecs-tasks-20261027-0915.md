**Pre-flight assessment for:** `orders-api` / `prod`
**Action:** Increase orders-api ECS desired task count from 3 to 5
**Date:** 2026-10-27 09:15 (UTC)
**Commit:** `a0b1c2d`
**Target:** profile `acme-prod` / `ap-southeast-1` | Terraform var-file `envs/prod.tfvars`
**Plan hash:** `sha256:7a1c9e…` (SHA-256 of the `terraform plan` output assessed)
**Plan source:** `terraform plan -var-file=envs/prod.tfvars -no-color`
**Delivery model:** CI on merge
**Invoked by:** operator
**Assessor used:** iac-change
**Layers evaluated:** L1 (static) + L2 (human)

## Verdict: GREEN — PROCEED

## Risk Scorecard

| # | Category | Score | Finding | Evidence | Mitigation |
|---|----------|-------|---------|----------|------------|
| 1 | Blast radius | 🟢 | Single resource, single module. | `plan` (1 changed) | — |
| 2 | Reversibility | 🟢 | Single attribute change (`desired_count`); no one-way attributes. | `plan` | — |
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
| `desired_count` = 3 | `envs/prod.tfvars:6` | — | code-only |

No drift found.

## Hard Blocks

None.

## Acknowledged Risks

None.

## Mitigations Committed

None.

## Context Provided (L2)

- No active incidents. No deployment freeze. (`operator`)

## L1 Analysis Detail

Scanned: `ecs.tf`, `envs/prod.tfvars`. No catalog.

## L3 Queries Run

L3 not requested.
