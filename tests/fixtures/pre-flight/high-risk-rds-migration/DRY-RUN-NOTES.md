# Dry-run of `pre-flight` against `high-risk-rds-migration`

Simulated run of the 7-step skill against this fixture. Recorded on 2026-04-23; re-run 2026-10-26 against the evidence rule.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Assessor loading | `assessors/iac-change.md` matched Terraform plan output |
| Hard block on reversibility | `aws_db_instance.main` destroy = irreversible data loss → Red + hard block. The resource was removed from config, so `skip_final_snapshot` comes from state and isn't in the plan → `UNVERIFIED`; L3 `describe-db-instances` (deletion protection, backup retention) + `describe-db-snapshots` (latest snapshot) recorded as recovery evidence. A snapshot doesn't lift the hard block |
| Brief ingress gap | `aws_security_group_rule.db_ingress` "will be recreated" → delete then create → brief DB connection gap → noted under blast radius |
| Evidence rule | Category 10 Green cites live checks (L3 approved), not L2 |
| Shared infrastructure blast radius | `outputs.tf` shows 3 downstream consumers (`userapi`, `authapi`, `billingapi`) → Red |
| Dependency impact from outputs | `db_endpoint` output consumed by 3 services → Red |
| Security posture (Red, hard block) | Old instance `storage_encrypted = true` (`plan:13`); new cluster sets no `storage_encrypted` / `kms_key_id` (`main.tf:4-19`); provider default for `provisioned` is `false` → encryption removal → hard block. The new IAM role (AWS managed policy) and the in-VPC SG rule change are minor next to it |
| Cost impact (Yellow) | Aurora pricing differs from RDS single-instance (generally higher per-hour, but scales better) → Yellow |
| Change velocity (Yellow) | Simulated: 2 commits in last 7 days (recent schema migration prep) → Yellow |
| Operator familiarity (Yellow) | Operator answered: first time migrating RDS→Aurora (Q5 variant) → Yellow |
| Observability readiness (Yellow) | Existing RDS alarms won't work on Aurora — new alarms not in the plan → Yellow |
| Multi-Yellow escalation | 4 Yellow + 1 ⚪ categories → triggers Red soft block escalation (in addition to the hard blocks) |
| Actionable mitigations | Skill must recommend: (1) take final RDS snapshot, (2) run parallel Aurora cluster before destroying RDS, (3) notify downstream teams, (4) add Aurora-specific CloudWatch alarms |

## Scoring detail

| # | Category | Score | Signal |
|---|----------|-------|--------|
| 1 | Blast radius | 🔴 | Shared database with 3 downstream consumers, user-facing data path; SG rule recreate → brief ingress gap (`plan:50-52`) |
| 2 | Reversibility | 🔴 HARD BLOCK | `destroy` of `aws_db_instance.main` — stateful resource, data loss (`plan:3-5`); final-snapshot behaviour `UNVERIFIED` |
| 3 | Change velocity | 🟡 | 2 commits in last 7 days to this directory |
| 4 | Dependency impact | 🔴 | `outputs.tf` exports `db_endpoint` consumed by 3 services |
| 5 | Timing context | 🟢 | Normal hours, no freeze, no incidents (from L2) |
| 6 | Operator familiarity | 🟡 | First time with RDS→Aurora migration (from L2) |
| 7 | Observability readiness | 🟡 | Existing RDS alarms don't cover Aurora; no Aurora alarms in plan |
| 8 | Cost impact | 🟡 | Aurora pricing change — moderate, predictable |
| 9 | Security posture | 🔴 HARD BLOCK | Encryption removal: `plan:13` vs `main.tf:4-19` (no `storage_encrypted`; provider default `false`) |
| 10 | Resource health | 🟢 | `live` instance `available`, CPU / connections within normal range, no alarm in `ALARM` |
| 11 | Application compatibility | ⚪ | Endpoint changes (`aws_db_instance.main` destroyed, new `aws_rds_cluster.main` endpoint); consumers' source not provided at Q8. Mitigation 3 (update connection strings) is the expand–contract step |

**Overall verdict: RED — HARD BLOCK** (irreversible data change on category 2; encryption removal on category 9)

## Verification pass (Step 5b, 2026-10-26)

A hard block fired, so a fresh-eyes review ran: a separate reviewer got the plan, code, live results, L2 answers and the rules, but not the scores. It agreed on the verdict and disagreed on two categories:
- Category 5: ⚪, because "not peak" is operator-stated with no live baseline. Accepted.
- Category 7: ⚪ rather than Red, because live alarm existence is unknown. Kept as Red under the assessor rule "no declared alerting on the changed resources", and the disagreement is shown to the operator.

The same run found the category 9 encryption removal that this fixture had scored Yellow. It also noted that the plan's `final_snapshot_identifier` (`plan:27`) carries the date the plan was produced, and that a `timestamp()`-based value changes on every plan.

Record header: Plan hash `sha256:e8ad15b35eb9e014e443947ef4dd8cc537f2d7305e5e788567baa3c9fc9633d8` (SHA-256 of `plan-output.txt`), target account `<plan account>` / `us-east-1`.

## Mitigations the skill should recommend

1. **Before applying (operator action — pre-flight never runs it):** Take a manual RDS snapshot (`aws rds create-db-snapshot`) as a safety net
2. **Consider expand-and-contract:** Create the Aurora cluster first (separate apply), migrate data, verify, THEN destroy the old RDS instance in a second apply
3. **Notify downstream teams:** `userapi`, `authapi`, `billingapi` all consume `db_endpoint` — they need to update connection strings
4. **Add Aurora monitoring:** Include `aws_cloudwatch_metric_alarm` resources for Aurora-specific metrics (CPU, connections, replication lag) in this or a follow-up change
5. **Schedule during low-traffic window:** Even though timing is currently Green, a data migration should target the lowest-traffic period
