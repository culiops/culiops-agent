**IaC change execution for:** `orders-api` / `prod`
**Change:** `Resize RDS orders-db from db.t3.medium to db.t3.large`
**Date:** `2026-10-27 10:15`
**Commit:** `d9e0f1a`
**IaC tool(s):** `Terraform`
**Execution path:** PR
**Pre-flight record:** `.culiops/pre-flight/orders-api-resize-rds-20261027-1000.md`

## Research Summary

No service-discovery catalog (`none — proceeding without catalog`). Delivery model: CI applies on merge (GitHub Actions `terraform-apply`). Env selection: `-var-file=envs/prod.tfvars`. Target: profile `acme-prod`, region `ap-southeast-1` (checked with `aws sts get-caller-identity`). Repo: `github.com/acme/orders-infra`.

## Evidence

| Fact | Code evidence | Live evidence | Match? |
|------|---------------|---------------|--------|
| `orders-db` instance class | `code: envs/prod.tfvars:12` → `db.t3.medium` | `code-only — not live-verified` | ⚠️ unverified |

## Change Plan

**Phase 1 of 1: Resize orders-db**
- Files: `envs/prod.tfvars`, `rds.tf`
- Resources affected: 1 to replace (`aws_db_instance.orders`)
- Rollback path: not applicable, nothing was applied

**Execution path:** PR

## Execution Log

### Phase 1: Resize orders-db
- Files changed: `envs/prod.tfvars`, `rds.tf`
- Plan output summary: 1 to add, 0 to change, 1 to destroy
- Plan hash: `sha256:7a1c9e…`
- Pre-flight verdict: RED — HARD BLOCK (replace of orders-db)
- Execution: aborted at GATE — pre-flight RED (replace of orders-db)
- Verification: n/a — nothing applied

## Outcome

aborted

## Ticket Reference

https://acme.atlassian.net/browse/OPS-123
