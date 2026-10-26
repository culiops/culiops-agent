---
cloud: aws
action: rightsize
resource_type: ec2-instance
applies_when: action == "rightsize" AND resource matches "i-*"
---

# Verify: Rightsize EC2 instance

## Required IAM
- `ec2:DescribeInstances`
- `ec2:DescribeInstanceTypes` (current vs target RAM, vCPU, network, architecture, burstable)
- `cloudwatch:GetMetricData`
- `cloudwatch:ListMetrics` (discover the CWAgent memory dimensions)
- `cloudwatch:DescribeAlarms`
- `compute-optimizer:GetEC2InstanceRecommendations` (if Compute Optimizer enabled; preferred over manual computation)
- `elasticloadbalancing:DescribeTargetGroups`
- `elasticloadbalancing:DescribeTargetHealth`
- `elasticloadbalancing:DescribeLoadBalancers` (classic ELB sweep, optional)

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`). Apply the **Metrics rule** to every CloudWatch query below. Ownership `asg` / `eks-nodegroup` / `karpenter` → ❔ `owned-by-<owner>` and stop: a resize of a member is reverted at the next scale event; the change belongs in the launch template / nodegroup / NodePool. `cloudformation` → ❔ `unsupported-owner`. `terraform`: cite `code:<path:line>` of the `instance_type`; if it differs from the live type (Query 1) → **drift row**: record code vs live, and re-base the saving on the live type. `unmanaged` → "re-apply old IaC" rollback unavailable (Reversibility 🟡: manual stop/modify/start).
1. `aws ec2 describe-instances --instance-ids <id> --query 'Reservations[].Instances[].[InstanceType,LaunchTime,Architecture,Monitoring.State,VpcId,Tags]'` — current type, age, architecture, monitoring granularity (`disabled` = basic, 5-min datapoints: hourly `Maximum` understates peaks), VPC for Query 6.
2. `aws ec2 describe-instance-types --instance-types <current> <target> --query 'InstanceTypes[].[InstanceType,VCpuInfo.DefaultVCpus,MemoryInfo.SizeInMiB,NetworkInfo.NetworkPerformance,ProcessorInfo.SupportedArchitectures,BurstablePerformanceSupported]'` — RAM / vCPU / network / architecture / burstable comparison for the target class (target from the upstream report or Compute Optimizer).
3. **Utilization (one call, 30d @ 3600s = 720 points per query).** `Stat` accepts percentiles (`p95`) in `get-metric-data`; with `get-metric-statistics`, percentiles require `--extended-statistics` and cannot be combined with `--statistics` in one call (CLI help):

   ```
   aws cloudwatch get-metric-data --start-time <now-30d> --end-time <now> --scan-by TimestampAscending --metric-data-queries '[
    {"Id":"cpuavg","MetricStat":{"Metric":{"Namespace":"AWS/EC2","MetricName":"CPUUtilization","Dimensions":[{"Name":"InstanceId","Value":"<id>"}]},"Period":3600,"Stat":"Average"}},
    {"Id":"cpumax","MetricStat":{"Metric":{"Namespace":"AWS/EC2","MetricName":"CPUUtilization","Dimensions":[{"Name":"InstanceId","Value":"<id>"}]},"Period":3600,"Stat":"Maximum"}},
    {"Id":"cpup95","MetricStat":{"Metric":{"Namespace":"AWS/EC2","MetricName":"CPUUtilization","Dimensions":[{"Name":"InstanceId","Value":"<id>"}]},"Period":3600,"Stat":"p95"}},
    {"Id":"netin","MetricStat":{"Metric":{"Namespace":"AWS/EC2","MetricName":"NetworkIn","Dimensions":[{"Name":"InstanceId","Value":"<id>"}]},"Period":3600,"Stat":"Sum"}},
    {"Id":"netout","MetricStat":{"Metric":{"Namespace":"AWS/EC2","MetricName":"NetworkOut","Dimensions":[{"Name":"InstanceId","Value":"<id>"}]},"Period":3600,"Stat":"Sum"}}]'
   ```

   Hourly `Sum / 3600` is an average rate, not a burst rate. Project CPU onto the target: `projected% ≈ observed% × current_vCPUs / target_vCPUs` (same family/generation; across families treat as an estimate and say so).
4. Memory (CloudWatch agent only): first `aws cloudwatch list-metrics --namespace CWAgent --metric-name mem_used_percent --dimensions Name=InstanceId,Value=<id>` — the agent often publishes extra dimensions (`ImageId`, `InstanceType`), and a query must match the dimension set **exactly**, so take the dimensions from this output. Then query `mem_used_percent` (`Average` and `Maximum`, 30d @ 3600s) with those dimensions. No metric listed → agent not installed → ⚪ (not zero). Windows hosts publish a different counter name (verify).
5. `aws compute-optimizer get-ec2-instance-recommendations --instance-arns <arn>` — if Compute Optimizer is the source of the upstream recommendation, fetch the rationale (and its lookback window — compare with the 30d requirement).
6. Target-group membership (no by-instance API exists; optional sweep): `aws elbv2 describe-target-groups --query "TargetGroups[?VpcId=='<vpc-id>'].TargetGroupArn"`, then for each `aws elbv2 describe-target-health --target-group-arn <tg> --targets Id=<id>` — a TG that does not contain the instance returns state `unused` / reason `Target.NotRegistered`; anything else is a membership. Classic ELBs: `aws elb describe-load-balancers --query "LoadBalancerDescriptions[?Instances[?InstanceId=='<id>']].LoadBalancerName"`. Skipping the sweep → membership ⚪ → Blast stays 🟡.
7. Active alarms: `aws cloudwatch describe-alarms --state-value ALARM --query "MetricAlarms[?Dimensions[?Name=='InstanceId' && Value=='<id>']].[AlarmName,MetricName]"` — filtered client-side. Metric-math alarms carry dimensions inside `Metrics[]`, not at top level, so also scan those if present.
8. (Only if the current or target class is a `t`-family) `CPUCreditBalance` (and `CPUSurplusCreditBalance` in unlimited mode), `Minimum`, 30d @ 3600s, same call shape as Query 3.

## Evidence thresholds

Thresholds are defaults; adjust only with operator-stated reasons. "Req" = required: ⚪ on a required row forces Evidence ⚪ → 🔴.

| Signal | Req | 🟢 Threshold (safe to downsize) | 🚫 Trigger (do not downsize) |
|--------|-----|-------------------------------|-------------------------------|
| 30d mean of hourly CPU `Average` | required | < 30% of current class capacity | n/a (low CPU alone is not a 🚫; high CPU is) |
| 30d hourly CPU `p95`, projected onto target | required | < 60% | ≥ 85% — sustained load would saturate the new class |
| 30d hourly CPU `Maximum`, projected onto target | required | < 75% | ≥ 90% — at risk of saturation post-downsize |
| 30d peak hourly `NetworkIn` / `NetworkOut` rate (Sum / 3600) | required | < 50% of the target class's baseline bandwidth | ≥ 90% — network-bound |
| 30d `mem_used_percent` `Maximum`, projected onto target (`pct × current_RAM / target_RAM`) | **required when target RAM < current RAM; optional otherwise** | < 75% | ≥ 90% |
| Burstable **target** (`t`-family): projected 30d mean CPU vs target baseline utilization (verify per size in the instance-type docs) | required if target is `t`-family | ≤ target baseline, credits never the constraint | sustained above baseline — credit drain / throttling, or surplus-credit charges in unlimited mode (can erase the saving) |
| Burstable **current** (`t`-family): 30d `CPUCreditBalance` minimum | required if current is `t`-family | balance stays well above 0 | reaches ≈ 0 — the instance is already throttled, so observed CPU understates demand |
| Active alarms on this instance (Query 7) | required | 0 | ≥ 1 alarm in ALARM state |

If memory is `required` and no CWAgent data exists → ⚪ → Evidence 🔴 (expect many downsizes to land in 🔴 until the agent is installed). Optional EBS check: smaller classes have lower EBS bandwidth/IOPS limits — compare `EBSReadBytes + EBSWriteBytes` (Nitro only) against the target's EBS baseline from Query 2 (`EbsInfo`; verify).

**Architecture change.** If the target's `SupportedArchitectures` excludes the instance's `Architecture` (x86_64 → arm64 Graviton, or back), it is **not an in-place resize**: it needs a different AMI and a rebuild. Note it, do not score it as a resize; park in ❔ (`arch-change-not-a-resize`) unless an arm64 AMI is confirmed and the operator wants it as a replace item.

## Attachment (Dimension 2 / 4 input)

| Signal | Query | Effect |
|--------|-------|--------|
| ELB target-group / classic ELB membership | 6 | this instance is the only healthy target → Blast 🔴 (the stop/start is an outage); ≥ 2 healthy targets → eligible for Blast 🟢 |
| Non-EIP public IPv4 | 1 (`PublicIpAddress`, no EIP) | the address changes on stop/start → Blast ≥ 🟡 if anything references it |
| IaC / catalog references (Dim 4) | `code:` | per Dimension 4 thresholds |

## Reversibility classification
- **Default:** 🟢 reversible when Ownership is `terraform` — re-apply old IaC restores the larger instance type. Requires a stop/start (downtime ~2-5 min) per resize.
- **`unmanaged`:** 🟡 — reversal is a manual stop / `modify-instance-attribute` / start; no IaC to re-apply.

## Blast radius classification
- **Default:** 🟡 — touches a live resource. See the Attachment table. Bump to 🟢 if catalog confirms ≥ 2 healthy targets (Query 6) and the instance is not in an ASG (ASG members are already ❔ at step 0).

## Rollback note (informational, shown in plan)
"Re-apply old IaC to restore the original instance type (`unmanaged`: stop, `modify-instance-attribute --instance-type`, start). Stop/start required for type change — service must tolerate ~2-5 min downtime OR be behind a load balancer with redundancy. A non-Elastic public IPv4 changes on stop/start. Pre-resize: take an AMI for the fastest restore if rollback becomes urgent."
