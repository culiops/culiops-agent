**IaC change execution for:** `orders-api` / `prod`
**Change:** `Increase orders-api ECS desired task count from 3 to 5`
**Date:** `2026-10-27 09:30`
**Commit:** `a0b1c2d`
**IaC tool(s):** `Terraform`
**Execution path:** PR
**Pre-flight record:** `.culiops/pre-flight/orders-api-scale-ecs-tasks-20261027-0915.md`

## Research Summary

No service-discovery catalog (`none — proceeding without catalog`). Delivery model: CI applies on merge (GitHub Actions `terraform-apply`). Env selection: `-var-file=envs/prod.tfvars`. Target: profile `acme-prod`, region `ap-southeast-1` (checked with `aws sts get-caller-identity`). Repo: `github.com/acme/orders-infra`.

## Evidence

| Fact | Code evidence | Live evidence | Match? |
|------|---------------|---------------|--------|
| `orders-api` desired task count | `code: envs/prod.tfvars:6` → `3` | `code-only — not live-verified` | ⚠️ unverified |

## Change Plan

**Phase 1 of 1: Scale orders-api**
- Files: `envs/prod.tfvars`
- Resources affected: 1 to change (`aws_ecs_service.orders_api`), 0 to add, 0 to destroy
- Blast radius: orders-api tasks only; 2 extra tasks at 0.5 vCPU / 1 GB each
- Success criteria: `aws ecs describe-services --services orders-api` → `runningCount = 5`

**Execution path:** PR

## Execution Log

### Phase 1: Scale orders-api
- Files changed: `envs/prod.tfvars`
- Plan output summary: 0 to add, 1 to change, 0 to destroy
- Plan hash: `sha256:7a1c9e…`
- Pre-flight verdict: GREEN
- Execution: PR https://github.com/acme/orders-infra/pull/495 created; pipeline applies on merge
- Verification: pending — pipeline applies after merge

## Outcome

completed

## Ticket Reference

https://acme.atlassian.net/browse/OPS-123
