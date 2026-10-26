**Pre-flight assessment for:** `orders-api` / `prod`
**Action:** Restrict orders-db security group ingress to the app subnets
**Date:** 2026-10-27 13:00 (UTC)
**Commit:** `1a2b3c4`
**Target:** account `123456789012` / `ap-southeast-1` | Terraform var-file `envs/prod.tfvars`
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
| 1 | Blast radius | 🟡 | Security group rule change on the primary DB; a wrong CIDR would cut orders-api off from `orders-db`. | `plan` (1 changed: `aws_security_group_rule.orders_db_ingress`) | Verify connections after apply |
| 2 | Reversibility | 🟢 | No one-way attributes in the plan. | `plan` | — |
| 3 | Change velocity | 🟢 | No changes to this module in the past 14 days. | `git log` | — |
| 4 | Dependency impact | 🟢 | Consumers unaffected by this change. | `code:main.tf` | — |
| 5 | Timing context | 🟢 | Business hours, no incident, no freeze. | `operator` (Q1–Q3) | — |
| 6 | Operator familiarity | 🟢 | Operator has made this kind of change before. | `operator` (Q4–Q5) | — |
| 7 | Observability readiness | 🟢 | Dashboards and alarms exist for the service. | `code:monitoring.tf` | — |
| 8 | Cost impact | 🟢 | Negligible monthly delta. | `code` | — |
| 9 | Security posture | 🟡 | Ingress narrows from `0.0.0.0/0` to the app CIDR; a hard-coded access key was found in a deploy script (see Evidence). | `code:scripts/deploy.sh:4` | Rotate the key out of band |
| 10 | Resource health | 🟢 | No live health concerns known. | `operator` | — |

## Evidence

| Fact | Code / plan | Live | Match |
|------|-------------|------|-------|
| Target DB `arn:aws:rds:ap-southeast-1:123456789012:db:orders-db` | `plan` | — | code-only |
| Ingress source CIDR `10.20.0.0/16` | `envs/prod.tfvars:22` | — | code-only |
| Hard-coded credential `AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE` | `scripts/deploy.sh:4` | — | UNVERIFIED — finding, not part of this change |
| CI secret `AWS_SECRET_ACCESS_KEY=FAKEfakeFAKEfakeFAKEfakeFAKEfakeFAKEfake` | `.github/workflows/apply.yml:31` | — | UNVERIFIED — finding, not part of this change |

## Hard Blocks

None.

## Acknowledged Risks

- Security posture 🟡: operator will rotate the hard-coded key separately. (`operator`)

## Mitigations Committed

None.

## Context Provided (L2)

- No active incidents. No deployment freeze. (`operator`)

## L1 Analysis Detail

Scanned: `rds.tf`, `envs/prod.tfvars`, `scripts/deploy.sh`.

## L3 Queries Run

L3 not requested.
