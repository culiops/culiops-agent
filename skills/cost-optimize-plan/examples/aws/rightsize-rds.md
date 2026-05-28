---
cloud: aws
action: rightsize
resource_type: rds-instance
applies_when: action == "rightsize" AND resource matches "arn:aws:rds:*:db:*"
---

# Verify: Rightsize RDS instance

## Required IAM
- `rds:DescribeDBInstances`
- `cloudwatch:GetMetricStatistics`
- `compute-optimizer:GetRDSDatabaseRecommendations`

## Queries

1. `aws rds describe-db-instances --db-instance-identifier <id> --query 'DBInstances[].[DBInstanceClass,MultiAZ,Engine,EngineVersion]'` — current class + Multi-AZ status (matters for resize outage duration).
2. `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name CPUUtilization --dimensions Name=DBInstanceIdentifier,Value=<id> --start-time <now-14d> --end-time <now> --period 86400 --statistics Average,Maximum` — 14d CPU.
3. `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name FreeableMemory --dimensions Name=DBInstanceIdentifier,Value=<id> --start-time <now-14d> --end-time <now> --period 86400 --statistics Minimum` — 14d memory headroom (Minimum, because we want worst-case).
4. `aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name DatabaseConnections --dimensions Name=DBInstanceIdentifier,Value=<id> --start-time <now-14d> --end-time <now> --period 86400 --statistics Maximum` — peak connection count.
5. `aws compute-optimizer get-rds-database-recommendations --resource-arns <arn>` — Compute Optimizer rationale if available.

## Evidence thresholds

| Signal | 🟢 Threshold (safe to downsize) | 🚫 Trigger (do not downsize) |
|--------|-------------------------------|-------------------------------|
| 14d avg CPU | < 30% of current instance class capacity | n/a (low CPU alone is not a 🚫; high CPU is) |
| 14d peak CPU | < 75% on new class | ≥ 90% on new class |
| 14d Minimum FreeableMemory | > 25% of current class's RAM | < 10% of new class's RAM (about to OOM after downsize) |
| 14d peak DatabaseConnections | < 70% of new class's max_connections | ≥ 95% of new class's max_connections |
| Active alarms on this instance | 0 | ≥ 1 alarm in ALARM state |

## Reversibility classification
- **Default:** 🟢 reversible — re-apply old IaC restores the original class. For Multi-AZ instances, resize involves failover (~30s outage). For single-AZ, downtime is ~2-5min.

## Blast radius classification
- **Default:** 🔴 — RDS instances are typically depended on by many services. Bump down to 🟡 only if catalog confirms a single-consumer service.

## Rollback note (informational, shown in plan)
"Re-apply old IaC to restore the original DB instance class. Multi-AZ resize fails over to the standby (~30s read-write outage). Single-AZ resize requires ~2-5min downtime. Use `apply-immediately: false` to defer the change to the next maintenance window if outage timing matters. Take a manual snapshot before the resize for fastest rollback path."
