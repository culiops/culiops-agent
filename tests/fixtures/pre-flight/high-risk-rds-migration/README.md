# high-risk-rds-migration — pre-flight fixture

A Terraform change that destroys an RDS instance and replaces it with an Aurora cluster. Expected outcome: multiple Reds, including hard blocks.

## What's modelled

`userdb` — a shared PostgreSQL RDS instance in `us-east-1` used by three downstream services (`userapi`, `authapi`, `billingapi`). The change migrates from single-instance RDS to Aurora cluster.

## The proposed change

1. Destroy `aws_db_instance.main` (existing PostgreSQL 14 RDS instance)
2. Create `aws_rds_cluster.main` (new Aurora PostgreSQL cluster)
3. Create `aws_rds_cluster_instance.main` (Aurora instance)
4. Create `aws_iam_role.aurora_monitoring` (new IAM role for Enhanced Monitoring)
5. Modify `aws_security_group_rule.db_ingress` (widen to include Aurora port)

## Expected pre-flight scores

Multiple Reds:
- Blast radius: **Red** (shared database used by 3 services, user-facing data path)
- Reversibility: **Red + HARD BLOCK** (data migration — old RDS instance destroyed with data)
- Change velocity: Yellow (2 changes in last 7 days — recent schema migration)
- Dependency impact: **Red** (3 downstream services have hard dependency on this database)
- Timing context: Green (normal hours, no freeze, no incidents)
- Operator familiarity: Yellow (first time migrating RDS to Aurora)
- Observability readiness: Yellow (RDS alarms exist but no Aurora-specific alarms in the plan)
- Cost impact: Yellow (Aurora pricing differs from RDS — moderate cost change)
- Security posture: Yellow (new IAM role, security group modification — within VPC)
- Resource health: Green (service is healthy)

Overall: **RED — HARD BLOCK** (irreversible data change)

## What this fixture exercises

- **Multiple Red scores:** verifies the skill handles compounding Reds correctly
- **Hard block on reversibility:** `destroy` of stateful `aws_db_instance` is irreversible data loss
- **Dependency impact from shared infrastructure:** 3 downstream services affected
- **Actionable mitigations:** skill must recommend: take RDS snapshot, notify downstream teams, consider parallel-run strategy (expand-and-contract)
