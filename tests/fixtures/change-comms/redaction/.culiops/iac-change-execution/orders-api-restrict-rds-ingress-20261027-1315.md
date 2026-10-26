**IaC change execution for:** `orders-api` / `prod`
**Change:** `Restrict orders-db security group ingress to the app subnets`
**Date:** `2026-10-27 13:15`
**Commit:** `1a2b3c4`
**IaC tool(s):** `Terraform`
**Execution path:** PR
**Pre-flight record:** `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md`

## Research Summary

No service-discovery catalog. Delivery model: CI applies on merge. Env selection: `-var-file=envs/prod.tfvars`. Target: account `123456789012`, region `ap-southeast-1`. Pre-change snapshots are exported to bucket `orders-backup-123456789012`. Repo: `github.com/acme/orders-infra`. The CI job pulls the shared module repo with token `ghp_FAKEtokenFAKEtokenFAKE0000`.

## Evidence

| Fact | Code evidence | Live evidence | Match? |
|------|---------------|---------------|--------|
| Current ingress source | `code: envs/prod.tfvars:22` → `0.0.0.0/0` | `code-only — not live-verified` | ⚠️ unverified |
| Bastion host used by operators | `code: envs/prod.tfvars:24` → `10.20.30.40` | `code-only — not live-verified` | ⚠️ unverified |
| Hard-coded credential in `scripts/deploy.sh:4` | `AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE` | — | UNVERIFIED — flagged to operator, out of scope for this change |
| CI secret in `.github/workflows/apply.yml:31` | `AWS_SECRET_ACCESS_KEY=FAKEfakeFAKEfakeFAKEfakeFAKEfakeFAKEfake` | — | UNVERIFIED — flagged to operator, out of scope for this change |

## Change Plan

**Phase 1 of 1: Restrict ingress**
- Files: `envs/prod.tfvars`, `rds.tf`
- Resources affected: 1 to change (`aws_security_group_rule.orders_db_ingress`) on `arn:aws:rds:ap-southeast-1:123456789012:db:orders-db`
- Blast radius: connectivity between orders-api and `orders-db`; source narrows from `0.0.0.0/0` to `10.20.0.0/16`, bastion `10.20.30.40` keeps access
- Rollback path: revert PR #490 and re-apply, ~10 min
- Success criteria: `aws rds describe-db-instances --db-instance-identifier orders-db` → `DBInstanceStatus = available`; orders-api error rate unchanged; connection check `psql postgres://orders_app:NotARealPassw0rd@orders-db.internal:5432/orders -c 'select 1'` → `1`

**Execution path:** PR

## Execution Log

### Phase 1: Restrict ingress
- Files changed: `envs/prod.tfvars`, `rds.tf`
- Plan output summary: 0 to add, 1 to change, 0 to destroy
- Plan hash: `sha256:7a1c9e…`
- Pre-flight verdict: YELLOW — PROCEED WITH CAUTION (security posture acknowledged)
- Execution: PR https://github.com/acme/orders-infra/pull/490 created; pipeline applies on merge
- Verification: pending — pipeline applies after merge

## Outcome

completed

## Ticket Reference

https://acme.atlassian.net/browse/OPS-123
