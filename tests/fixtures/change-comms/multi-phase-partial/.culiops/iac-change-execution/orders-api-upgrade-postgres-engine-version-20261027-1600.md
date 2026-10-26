**IaC change execution for:** `orders-api` / `prod`
**Change:** `Upgrade RDS orders-db Postgres engine from 14.9 to 15.4`
**Date:** `2026-10-27 16:00`
**Commit:** `f5a6b7c`
**IaC tool(s):** `Terraform`
**Execution path:** PR
**Pre-flight record:** `invoked inline — verdict: YELLOW`

## Research Summary

No service-discovery catalog (`none — proceeding without catalog`). Delivery model: CI applies on merge (GitHub Actions `terraform-apply`). Env selection: `-var-file=envs/prod.tfvars`. Target: profile `acme-prod`, region `ap-southeast-1` (checked with `aws sts get-caller-identity`). Repo: `github.com/acme/orders-infra`. Multi-phase: expand-and-contract style upgrade with a snapshot first.

## Evidence

| Fact | Code evidence | Live evidence | Match? |
|------|---------------|---------------|--------|
| `orders-db` engine version | `code: envs/prod.tfvars:16` → `14.9` | `live: aws rds describe-db-instances …` → `14.9` | ✅ |
| Automated backups enabled | `code: envs/prod.tfvars:18` → `7` days | `live: …` → `7` | ✅ |

## Change Plan

**Phase 1 of 3: Snapshot orders-db**
- Files: `snapshot.tf`
- Resources affected: 1 to add (`aws_db_snapshot.pre_upgrade`)
- Rollback path: delete the snapshot resource; no effect on the running DB
- Success criteria: `aws rds describe-db-snapshots --db-snapshot-identifier orders-db-pre-upgrade` → `Status = available`

**Phase 2 of 3: Upgrade engine version**
- Files: `envs/prod.tfvars`
- Resources affected: 1 to change (`aws_db_instance.orders`), engine 14.9 → 15.4
- Rollback path: restore from the phase 1 snapshot into a new instance and repoint orders-api (hours, not minutes)
- Success criteria: `aws rds describe-db-instances …` → `EngineVersion = 15.4`, `DBInstanceStatus = available`

**Phase 3 of 3: Cleanup**
- Files: `snapshot.tf`, `envs/prod.tfvars`
- Resources affected: 1 to destroy (`aws_db_snapshot.pre_upgrade`) after a 7-day soak

**Execution path:** PR

## Execution Log

### Phase 1: Snapshot orders-db
- Files changed: `snapshot.tf`
- Plan output summary: 1 to add, 0 to change, 0 to destroy
- Plan hash: `sha256:11aa22…`
- Pre-flight verdict: GREEN
- Execution: PR https://github.com/acme/orders-infra/pull/501 created; merged, pipeline applied (operator-confirmed before phase 2)
- Verification: `aws rds describe-db-snapshots --db-snapshot-identifier orders-db-pre-upgrade` → `Status = available`

### Phase 2: Upgrade engine version
- Files changed: `envs/prod.tfvars`
- Plan output summary: 0 to add, 1 to change, 0 to destroy
- Plan hash: `sha256:33bb44…`
- Pre-flight verdict: YELLOW — PROCEED WITH CAUTION (downtime during engine upgrade acknowledged)
- Execution: PR https://github.com/acme/orders-infra/pull/502 created; pipeline applies on merge
- Verification: pending — pipeline applies after merge

### Phase 3: Cleanup
- Files changed: none yet
- Plan output summary: not planned
- Plan hash: n/a
- Pre-flight verdict: n/a
- Execution: not started
- Verification: n/a

## Outcome

partially completed (phase 2 of 3)

## Ticket Reference

https://acme.atlassian.net/browse/OPS-123
