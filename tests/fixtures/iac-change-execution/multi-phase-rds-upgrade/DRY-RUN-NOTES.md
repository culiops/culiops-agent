# Dry-run of `iac-change-execution` against `multi-phase-rds-upgrade`

Expected skill behaviour at each step. Recorded for pre-dry-run reference; "Gaps surfaced" and "Fixes applied" are filled in during the actual dry-run.

## Step 1 — Research

**Input:** operator request — "Increase max_connections to 200 for paymentapi prod RDS, then reboot so it takes effect."

**Expected behaviour:**

| Check | Expected outcome |
|-------|-----------------|
| Catalog lookup | Finds `.culiops/service-discovery/paymentapi-prod.md` — reads signal envelopes and dependency graph |
| Catalog signal note | Reads the note about connections alarm firing frequently at threshold=80 vs limit=100 |
| Tool detection | Finds `main.tf`, `variables.tf` → identifies Terraform |
| Naming pattern | Reads catalog: `paymentapi-{role}-{env}` — no inference needed |
| Reboot requirement | Recognises `max_connections` is a dynamic parameter (`apply_method = "pending-reboot"` by default); understands a reboot is required |
| Alarm threshold analysis | Reads `aws_cloudwatch_metric_alarm.paymentapi_db_connections` threshold=80 vs current limit=100 (80%). Notes new limit=200 → proportional threshold=160 |
| Direct apply flag | Operator specifies `--direct-apply` (maintenance window context); skill records execution path as direct apply |
| tfvars location | Finds `envs/prod.tfvars` |

## Step 2 — Plan

**Expected output:**

```
Phase 1 of 2 — IaC (terraform apply):
  Modify: aws_db_parameter_group.paymentapi  (max_connections: "100" → "200")
  Modify: aws_cloudwatch_metric_alarm.paymentapi_db_connections  (threshold: 80 → 160)
  Add:    (none)
  Destroy:(none)

Phase 2 of 2 — Operational (AWS CLI):
  Command: aws rds reboot-db-instance \
             --db-instance-identifier paymentapi-db-prod \
             --region ap-southeast-1
  Rationale: max_connections is a static/pending-reboot parameter; reboot required for change to take effect.
  Impact: brief connection interruption (~30s); Multi-AZ failover will occur automatically.

Execution path: direct apply (operator override)
Pre-flight: required before Phase 1 apply
```

## Step 3 — Implement

**Expected behaviour:**

- Modifies `main.tf`:
  - `aws_db_parameter_group.paymentapi`: changes `max_connections` value from `"100"` to `"200"` and sets `apply_method = "pending-reboot"`
  - `aws_cloudwatch_metric_alarm.paymentapi_db_connections`: updates `threshold` from `80` to `160` and updates `alarm_description` to reflect new limit
- Does NOT modify `aws_cloudwatch_metric_alarm.paymentapi_db_cpu` (CPU alarm is unrelated)
- Phase 2 command is documented (in plan output or operator note) but not written as IaC

## Step 4 — Code review gate

**Expected behaviour:**

- Skill surfaces the diff for operator review
- Operator verifies: param group change + alarm threshold update; approves

## Step 5 — Pre-flight

**Expected behaviour:**

- Skill invokes `pre-flight` with context: multi-phase, RDS parameter group + reboot, paymentapi, ap-southeast-1
- Phase 1 score: likely **Amber** — modifying a live RDS parameter group, even without immediate impact, warrants caution
- Phase 2 score: likely **Amber/Red** — reboot causes brief connection interruption; Multi-AZ limits impact but ECS tasks will see momentary errors
- Skill reads verdict before proceeding to Phase 1 apply
- Operator acknowledges Amber/Red risks before direct apply proceeds

## Step 6 — Execute (direct apply path)

**Phase 1:**
```
terraform plan -var-file=envs/prod.tfvars -out=tfplan
terraform apply tfplan
```

**Gate between phases:**
- Skill pauses; operator confirms parameter group is active (`aws rds describe-db-instances`)
- Operator confirms maintenance window is active

**Phase 2:**
```
aws rds reboot-db-instance \
  --db-instance-identifier paymentapi-db-prod \
  --region ap-southeast-1
```

Post-reboot validation:
```
aws rds describe-db-instances \
  --db-instance-identifier paymentapi-db-prod \
  --query 'DBInstances[0].DBParameterGroups[0].ParameterApplyStatus'
# Expected: "in-sync"
```

## Key multi-phase tests

| Test | What it verifies |
|------|-----------------|
| Multi-phase detection | Skill produces a 2-phase plan (not a single apply) |
| Phase 2 as operational command | Phase 2 is `aws rds reboot-db-instance`, not `terraform apply` |
| Catalog consumption | Skill reads `.culiops/service-discovery/paymentapi-prod.md` and uses signal envelopes |
| Alarm threshold proportional update | Connections alarm threshold updated from 80 to 160 (80% of new limit=200) |
| Direct apply risk escalation | Direct apply path surfaces elevated risk; pre-flight is Amber/Red; operator must acknowledge |
| Inter-phase gate | Skill pauses between Phase 1 and Phase 2 for operator confirmation |

## Gaps surfaced

_(to be filled during actual dry-run)_

## Fixes applied

_(to be filled during actual dry-run)_
