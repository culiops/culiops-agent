---
cloud: aws
action: rightsize
resource_type: rds-instance
applies_when: action == "rightsize" AND resource matches "arn:aws:rds:*:db:*"
---

# Verify: Rightsize RDS instance

Scope: standalone and Multi-AZ **DB instances**. Aurora and DB-cluster members are out of scope (Query 1 routes them to ❔).

## Required IAM
- `rds:DescribeDBInstances`
- `rds:DescribeDBParameters` (max_connections formula)
- `ec2:DescribeInstanceTypes` (RAM / vCPU of the current and target class)
- `cloudwatch:GetMetricData`
- `cloudwatch:DescribeAlarms`
- `compute-optimizer:GetRDSDatabaseRecommendations`

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`). Apply the **Metrics rule** to every CloudWatch query below. `cloudformation` → ❔ `unsupported-owner`. `unmanaged` → "re-apply old IaC" rollback unavailable (Reversibility 🟡). Terraform: cite `code:<path:line>` of `instance_class`; code ≠ live class → drift row.
1. `aws rds describe-db-instances --db-instance-identifier <id> --query 'DBInstances[].[DBInstanceClass,MultiAZ,Engine,EngineVersion,DBClusterIdentifier,ReadReplicaSourceDBInstanceIdentifier,ReadReplicaDBInstanceIdentifiers,DBParameterGroups[0].DBParameterGroupName]'` — current class, Multi-AZ (resize outage), engine, cluster membership, replica topology, parameter group.
   - **`Engine` starts with `aurora`, or `DBClusterIdentifier` is non-null → ❔ `aurora-or-cluster-out-of-scope`** and stop. A writer class change is a failover, Serverless v2 is ACU-based (not a class), and cluster members are sized together; this playbook's thresholds do not apply.
2. `aws ec2 describe-instance-types --instance-types <current-class-without-db.-prefix> <target-class-without-db.-prefix> --query 'InstanceTypes[].[InstanceType,VCpuInfo.DefaultVCpus,MemoryInfo.SizeInMiB]'` — RAM / vCPU for the projections (the `db.` prefix maps to the EC2 type of the same name for most classes; verify per class — RDS reserves part of RAM for the OS and engine).
3. **Utilization (one call, 30d @ 3600s = 720 points per query).** Percentiles need `get-metric-data` `Stat: "p95"` (or `get-metric-statistics --extended-statistics`, which cannot be combined with `--statistics`):

   ```
   aws cloudwatch get-metric-data --start-time <now-30d> --end-time <now> --scan-by TimestampAscending --metric-data-queries '[
   {"Id":"cpuavg","MetricStat":{"Metric":{"Namespace":"AWS/RDS","MetricName":"CPUUtilization","Dimensions":[{"Name":"DBInstanceIdentifier","Value":"<id>"}]},"Period":3600,"Stat":"Average"}},
   {"Id":"cpumax","MetricStat":{"Metric":{"Namespace":"AWS/RDS","MetricName":"CPUUtilization","Dimensions":[{"Name":"DBInstanceIdentifier","Value":"<id>"}]},"Period":3600,"Stat":"Maximum"}},
   {"Id":"cpup95","MetricStat":{"Metric":{"Namespace":"AWS/RDS","MetricName":"CPUUtilization","Dimensions":[{"Name":"DBInstanceIdentifier","Value":"<id>"}]},"Period":3600,"Stat":"p95"}},
   {"Id":"freemem","MetricStat":{"Metric":{"Namespace":"AWS/RDS","MetricName":"FreeableMemory","Dimensions":[{"Name":"DBInstanceIdentifier","Value":"<id>"}]},"Period":3600,"Stat":"Minimum"}},
   {"Id":"conns","MetricStat":{"Metric":{"Namespace":"AWS/RDS","MetricName":"DatabaseConnections","Dimensions":[{"Name":"DBInstanceIdentifier","Value":"<id>"}]},"Period":3600,"Stat":"Maximum"}},
   {"Id":"swap","MetricStat":{"Metric":{"Namespace":"AWS/RDS","MetricName":"SwapUsage","Dimensions":[{"Name":"DBInstanceIdentifier","Value":"<id>"}]},"Period":3600,"Stat":"Maximum"}}]'
   ```

   - If the class is `db.t*`: add `CPUCreditBalance` (`Minimum`) and, for unlimited mode, `CPUSurplusCreditBalance`.
   - If this instance is a replica or has replicas: add `ReplicaLag` (`Maximum`) for each replica.
4. `aws cloudwatch describe-alarms --state-value ALARM --query "MetricAlarms[?Dimensions[?Name=='DBInstanceIdentifier' && Value=='<id>']].[AlarmName,MetricName]"` — active alarms on this instance (metric-math alarms carry dimensions inside `Metrics[]`; scan those too).
5. `aws rds describe-db-parameters --db-parameter-group-name <pg> --query "Parameters[?ParameterName=='max_connections'].[ParameterValue,ApplyMethod]"` — in default groups `max_connections` is usually a formula of class memory, so it **changes with the class**: recompute for the target (parameter name is engine-specific; verify).
6. `aws compute-optimizer get-rds-database-recommendations --resource-arns <arn>` — Compute Optimizer rationale if available (check its lookback window against the 30d requirement).

## Evidence thresholds

Thresholds are skill defaults (policy, not AWS guidance); a looser threshold goes to `Gaps` and the item cannot reach 🟢 on it. "Req" = required: ⚪ on a required row forces Evidence ⚪ → 🔴.

| Signal | Req | 🟢 Threshold (safe to downsize) | 🚫 Trigger (do not downsize) |
|--------|-----|-------------------------------|-------------------------------|
| 30d mean of hourly CPU `Average` | required | < 30% of current class capacity | n/a (low CPU alone is not a 🚫; high CPU is) |
| 30d hourly CPU `p95`, projected onto new class (`pct × current_vCPUs / target_vCPUs`) | required | < 60% | ≥ 85% |
| 30d hourly CPU `Maximum`, projected onto new class | required | < 75% | ≥ 90% |
| 30d minimum `FreeableMemory` → projected free on new class: `(target_RAM − (current_RAM − min_free)) / target_RAM` | required | > 25% | < 10% (about to OOM after downsize) |
| 30d `SwapUsage` (Maximum) | optional | ≈ 0 | sustained growth — already memory-starved |
| 30d peak `DatabaseConnections` vs new class's `max_connections` (Query 5, recomputed) | required | < 70% | ≥ 95% |
| **`db.t*` burstable** (current or target): 30d `CPUCreditBalance` minimum / target baseline | required if `db.t*` | balance stays well above 0 and projected mean CPU ≤ target baseline | balance ≈ 0 (already throttled — observed CPU understates demand), or sustained above baseline (surplus-credit charges in unlimited mode) |
| Replica lag (`ReplicaLag` Maximum) if replicas involved | required if replica / has replicas | stays low with headroom | already lagging — a smaller class will worsen it |
| Active alarms on this instance (Query 4) | required | 0 | ≥ 1 alarm in ALARM state |

`FreeableMemory` is low by design on engines that cache aggressively; judge the **trend and `SwapUsage`**, and remember buffer-pool / shared-buffer parameters often scale with class memory.

## Attachment (Dimension 2 / 4 input)

| Signal | Query | Effect |
|--------|-------|--------|
| Read replicas (`ReadReplicaDBInstanceIdentifiers`) | 1 | ≥ 1 → Blast stays 🔴. Replica class must stay ≥ source class to avoid lag (and if a replica is the promotion target). **Order:** downsize the source first, then replicas; never leave a replica smaller than its source |
| This instance is itself a replica (`ReadReplicaSourceDBInstanceIdentifier`) | 1 | it serves reads: check `ReplicaLag` and the consumers' read endpoints; resizing it must not drop below the source's class unless the lag row is 🟢 |
| Multi-AZ | 1 | resize fails over — brief outage on the writer path |
| IaC / catalog consumers (Dim 4) | `code:` | per Dimension 4 thresholds |

## Reversibility classification
- **Default:** 🟢 reversible when Ownership is `terraform` — re-apply old IaC restores the original class. Multi-AZ resize updates the standby, then fails over (typically 60–120 s); single-AZ is unavailable while the class changes, for a time proportional to recovery (docs: https://repost.aws/knowledge-center/rds-performance-impact).
- **`unmanaged`:** 🟡 — manual `modify-db-instance` back to the old class; no IaC to re-apply.

## Blast radius classification
- **Default:** 🔴 — RDS instances are typically depended on by many services. Bump down to 🟡 only if catalog confirms a single-consumer service AND no replicas.

## Rollback note (informational, shown in plan)
"Re-apply old IaC to restore the original DB instance class (`unmanaged`: `modify-db-instance --db-instance-class <old>`). Multi-AZ resize fails over to the standby (brief read-write outage); single-AZ is unavailable while the class changes (docs: https://repost.aws/knowledge-center/rds-performance-impact). Defer to the maintenance window with `apply_immediately = false` (Terraform) / `--no-apply-immediately` if outage timing matters. Take a manual snapshot before the resize for the fastest rollback path. Parameter-group values derived from class memory (e.g. `max_connections`) change with the class and change back on rollback."
