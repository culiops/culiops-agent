**IaC change execution for:** `orders-api` / `prod`
**Change:** `Rotate application log retention from 30 to 14 days`
**Date:** `2026-10-19 09:00`
**Commit:** `c3d4e5f`
**IaC tool(s):** `Terraform`
**Execution path:** PR
**Pre-flight record:** `invoked inline — verdict: GREEN`

## Research Summary

No service-discovery catalog (`none — proceeding without catalog`). Delivery model: CI applies on merge (GitHub Actions `terraform-apply`). Env selection: `-var-file=envs/prod.tfvars`. Target: profile `acme-prod`, region `ap-southeast-1` (checked with `aws sts get-caller-identity`). Repo: `github.com/acme/orders-infra`.

## Evidence

| Fact | Code evidence | Live evidence | Match? |
|------|---------------|---------------|--------|
| Log group retention | `code: logging.tf:8` → `30` | `code-only — not live-verified` | ⚠️ unverified |

## Change Plan

**Phase 1 of 1: Shorten log retention**
- Files: `logging.tf`
- Resources affected: 1 to change (`aws_cloudwatch_log_group.orders_api`)
- Rollback path: revert the PR and re-apply

**Execution path:** PR

## Execution Log

### Phase 1: Shorten log retention
- Files changed: `logging.tf`
- Plan output summary: 0 to add, 1 to change, 0 to destroy
- Plan hash: `sha256:3b5d7f…`
- Pre-flight verdict: GREEN
- Execution: aborted at GATE — operator cancelled; retention is shared with the audit log group and the owner objected
- Verification: n/a — nothing applied

## Outcome

aborted

## Ticket Reference

none
