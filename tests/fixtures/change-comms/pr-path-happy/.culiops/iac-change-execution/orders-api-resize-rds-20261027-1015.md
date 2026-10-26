**IaC change execution for:** `orders-api` / `prod`
**Change:** `Resize RDS orders-db from db.t3.medium to db.t3.large`
**Date:** `2026-10-27 10:15`
**Commit:** `e7f8a9b`
**IaC tool(s):** `Terraform`
**Execution path:** PR
**Pre-flight record:** `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`

## Research Summary

No service-discovery catalog (`none — proceeding without catalog`). Delivery model: CI applies on merge (GitHub Actions `terraform-apply`). Env selection: `-var-file=envs/prod.tfvars`. Target: profile `acme-prod`, region `ap-southeast-1` (checked with `aws sts get-caller-identity`). Repo: `github.com/acme/orders-infra`.

## Evidence

| Fact | Code evidence | Live evidence | Match? |
|------|---------------|---------------|--------|
| `orders-db` instance class | `code: envs/prod.tfvars:12` → `db.t3.medium` | `code-only — not live-verified` | ⚠️ unverified |
| `orders-db` Multi-AZ | `code: envs/prod.tfvars:14` → `true` | `code-only — not live-verified` | ⚠️ unverified |

## Change Plan

**Phase 1 of 1: Resize orders-db**
- Files: `envs/prod.tfvars`
- Resources affected: 1 to change (`aws_db_instance.orders`), 0 to add, 0 to destroy
- Blast radius: orders-api depends on `orders-db`; Multi-AZ failover during the class change
- Rollback path: revert PR #482 and re-apply, ~10 min
- Success criteria: `aws rds describe-db-instances --db-instance-identifier orders-db` → `DBInstanceClass = db.t3.large`, `DBInstanceStatus = available`

**Execution path:** PR

## Execution Log

### Phase 1: Resize orders-db
- Files changed: `envs/prod.tfvars`
- Plan output summary: 0 to add, 1 to change, 0 to destroy
- Plan hash: `sha256:7a1c9e…`
- Pre-flight verdict: YELLOW — PROCEED WITH CAUTION (blast radius and reversibility acknowledged: short failover blip)
- Execution: PR https://github.com/acme/orders-infra/pull/482 created; pipeline applies on merge
- Verification: pending — pipeline applies after merge

## Outcome

completed

## Ticket Reference

https://acme.atlassian.net/browse/OPS-123
