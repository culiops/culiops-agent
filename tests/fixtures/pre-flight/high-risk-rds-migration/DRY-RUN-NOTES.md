# Dry-run of `pre-flight` against `high-risk-rds-migration`

Simulated run of the 7-step skill against this fixture. Recorded on 2026-04-23.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Assessor loading | `assessors/iac-change.md` matched Terraform plan output |
| Hard block on reversibility | `aws_db_instance.main` destroy = irreversible data loss → Red + hard block |
| Shared infrastructure blast radius | `outputs.tf` shows 3 downstream consumers (`userapi`, `authapi`, `billingapi`) → Red |
| Dependency impact from outputs | `db_endpoint` output consumed by 3 services → Red |
| Security posture (Yellow) | New IAM role `aurora_monitoring` uses AWS managed policy (scoped), SG rule update stays within VPC → Yellow |
| Cost impact (Yellow) | Aurora pricing differs from RDS single-instance (generally higher per-hour, but scales better) → Yellow |
| Change velocity (Yellow) | Simulated: 2 commits in last 7 days (recent schema migration prep) → Yellow |
| Operator familiarity (Yellow) | Operator answered: first time migrating RDS→Aurora (Q5 variant) → Yellow |
| Observability readiness (Yellow) | Existing RDS alarms won't work on Aurora — new alarms not in the plan → Yellow |
| Multi-Yellow escalation | 5 Yellow categories → triggers Red soft block escalation (in addition to the hard blocks) |
| Actionable mitigations | Skill must recommend: (1) take final RDS snapshot, (2) run parallel Aurora cluster before destroying RDS, (3) notify downstream teams, (4) add Aurora-specific CloudWatch alarms |

## Scoring detail

| # | Category | Score | Signal |
|---|----------|-------|--------|
| 1 | Blast radius | 🔴 | Shared database with 3 downstream consumers, user-facing data path |
| 2 | Reversibility | 🔴 HARD BLOCK | `destroy` of `aws_db_instance.main` — stateful resource, data loss |
| 3 | Change velocity | 🟡 | 2 commits in last 7 days to this directory |
| 4 | Dependency impact | 🔴 | `outputs.tf` exports `db_endpoint` consumed by 3 services |
| 5 | Timing context | 🟢 | Normal hours, no freeze, no incidents (from L2) |
| 6 | Operator familiarity | 🟡 | First time with RDS→Aurora migration (from L2) |
| 7 | Observability readiness | 🟡 | Existing RDS alarms don't cover Aurora; no Aurora alarms in plan |
| 8 | Cost impact | 🟡 | Aurora pricing change — moderate, predictable |
| 9 | Security posture | 🟡 | New IAM role (AWS managed policy); SG rule update within VPC |
| 10 | Resource health | 🟢 | Service healthy (from L2) |

**Overall verdict: RED — HARD BLOCK** (irreversible data change on category 2)

## Mitigations the skill should recommend

1. **Before applying:** Take a manual RDS snapshot (`aws rds create-db-snapshot`) as a safety net
2. **Consider expand-and-contract:** Create the Aurora cluster first (separate apply), migrate data, verify, THEN destroy the old RDS instance in a second apply
3. **Notify downstream teams:** `userapi`, `authapi`, `billingapi` all consume `db_endpoint` — they need to update connection strings
4. **Add Aurora monitoring:** Include `aws_cloudwatch_metric_alarm` resources for Aurora-specific metrics (CPU, connections, replication lag) in this or a follow-up change
5. **Schedule during low-traffic window:** Even though timing is currently Green, a data migration should target the lowest-traffic period
