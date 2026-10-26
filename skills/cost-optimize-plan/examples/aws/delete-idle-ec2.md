---
cloud: aws
action: delete
resource_type: ec2-instance
applies_when: action == "delete" AND resource matches "i-*"
---

# Verify: Delete idle EC2 instance

## Required IAM
- `ec2:DescribeInstances`
- `ec2:DescribeAddresses`
- `cloudwatch:GetMetricData`
- `cloudtrail:LookupEvents`

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`). Apply the **Metrics rule** to every CloudWatch query below. Ownership `asg` / `eks-nodegroup` / `karpenter` → ❔ `owned-by-<owner>` and stop: terminating a member is undone by the owner replacing it; the real change is the ASG / nodegroup / NodePool / launch template. `cloudformation` → ❔ `unsupported-owner`. `unmanaged` → "re-apply old IaC" rollback is unavailable.
1. `aws ec2 describe-instances --instance-ids <id>` — captures `State.Name`, `StateTransitionReason`, `BlockDeviceMappings[].Ebs.DeleteOnTermination` (every volume, not just root), network interfaces / Elastic IP association, and tags. Success is the "describe succeeded" precondition for treating empty metrics as zero.
2. **If `running`** — activity metrics (one call, 90d @ 3600s; 2,160 datapoints per metric exceeds the 1,440 `get-metric-statistics` cap, so use `get-metric-data`):

   ```
   aws cloudwatch get-metric-data --start-time <now-90d> --end-time <now> --scan-by TimestampAscending --metric-data-queries '[
    {"Id":"cpu","MetricStat":{"Metric":{"Namespace":"AWS/EC2","MetricName":"CPUUtilization","Dimensions":[{"Name":"InstanceId","Value":"<id>"}]},"Period":3600,"Stat":"Average"}},
    {"Id":"cpumax","MetricStat":{"Metric":{"Namespace":"AWS/EC2","MetricName":"CPUUtilization","Dimensions":[{"Name":"InstanceId","Value":"<id>"}]},"Period":3600,"Stat":"Maximum"}},
    {"Id":"netin","MetricStat":{"Metric":{"Namespace":"AWS/EC2","MetricName":"NetworkIn","Dimensions":[{"Name":"InstanceId","Value":"<id>"}]},"Period":3600,"Stat":"Sum"}},
    {"Id":"netout","MetricStat":{"Metric":{"Namespace":"AWS/EC2","MetricName":"NetworkOut","Dimensions":[{"Name":"InstanceId","Value":"<id>"}]},"Period":3600,"Stat":"Sum"}}]'
   ```

   CPU alone misses network-served or I/O-bound workloads, so `NetworkIn` and `NetworkOut` are both required.
3. Session / lifecycle history (CloudTrail `lookup-events` returns **management events only, last 90 days**; one lookup attribute per call). SSH logins and `ConsoleLogin` are **not** recorded against an instance ID — do not look them up:
   - SSM sessions: `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=StartSession --start-time <now-90d> --query "Events[?contains(CloudTrailEvent, '<id>')]"` — the instance is in `requestParameters.target`, so filter client-side.
   - Lifecycle: `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<id> --start-time <now-90d> --query "Events[?EventName=='StartInstances'||EventName=='StopInstances'||EventName=='RunInstances']"`.
   - (Optional, verify) `SendSSHPublicKey` events (EC2 Instance Connect) filtered the same way as `StartSession`.
   - Anything older than 90d is ⚪ for this playbook (needs a trail in S3 / CloudTrail Lake, not queried here).
4. Elastic IP: `aws ec2 describe-addresses --filters Name=instance-id,Values=<id>` — **attachment**.

> **Window (Principle 3):** delete reads 60–180d at hourly granularity (90d used here; CloudTrail covers at most 90d). Judge the distribution: a nightly batch job shows as a recurring hourly spike that a daily average hides.

## Evidence thresholds

**`running` instance:**

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| 90d hourly CPU `Average` | required | mean < 2% AND no hour ≥ 10% | any hour ≥ 50% in the last 30d, or a recurring pattern (nightly / weekly job) |
| 90d hourly `NetworkIn` (Sum) | required | every hour < 1 MB | any hour ≥ 100 MB in the last 30d, or recurring hours above noise floor |
| 90d hourly `NetworkOut` (Sum) | required | every hour < 1 MB | same rule |
| `StartSession` events targeting this instance, last 90d | required | none | any — humans are using it |
| `StartInstances` / `StopInstances` events, last 90d | optional | none | any in the last 30d — someone is operating it (a scheduled start/stop pair is a schedule, not usage: check cadence) |
| `Instances[0].State.Name` | required | `running` | `pending`, `shutting-down` — in transition, re-check |

Values between the 🟢 and 🚫 thresholds → row not 🟢 (a delete needs Evidence 🟢 to land anywhere but 🔴 / 🔵). Subtract keep-alive noise (SSM agent, CloudWatch agent, monitoring pollers) from the network floor (Principle 1 rule 2) — tell: uniform, periodic, workload-independent cadence.

**`stopped` instance — idle-ambiguous.** CPU / network rows return no datapoints (expected; not "idle"). A stopped instance may be stopped for DR, seasonal use, or a pending migration — metrics cannot distinguish decommissioned from paused; only the owner can. **`State.Name` alone is NOT sufficient evidence.** Score the delete as idle-ambiguous → route to 🔵 (owner confirmation), even with Evidence 🟢:

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| Stopped duration (`StateTransitionReason` date if present — verify format; else CloudTrail `StopInstances`) | required | stopped ≥ 60d continuously | `StartInstances` in the last 30d (it is being cycled) |
| `StartSession` / `StartInstances` events, last 90d | required | none | any in the last 30d |

Principle 2 for stopped instances: the saving is only the attached EBS volumes (and any EIP). Compare with a reversible step first (AMI + snapshots, then delete the instance and volumes later).

## Attachment (Dimension 2 / 4 input)

| Signal | Query | Effect |
|--------|-------|--------|
| Elastic IP associated | 4 | ≥ 1 → Blast ≥ 🟡; referenced by DNS or partner allowlist → Blast 🔴. Terminating disassociates but does not release the EIP — it stays allocated and billed |
| Registered in an ELB target group | method in `rightsize-ec2.md` Query 6 (optional sweep) | ≥ 1 → Blast ≥ 🟡 |
| IaC references (Dim 4 grep for the instance ID / its `aws_instance`) | `code:` | per Dimension 4 thresholds |

## Reversibility classification
- **Default:** 🔴 irreversible. Termination destroys instance-store volumes; the instance ID cannot be reused. Any EBS volume with `DeleteOnTermination=true` — **including the root volume (the default for root)** — is destroyed with the instance and its data is lost.
- **Mitigated → 🟡:** a recent AMI exists (rebuild ~10–20 min RTO) AND every data-bearing volume is either covered by that AMI / a recent snapshot or has `DeleteOnTermination=false`. Check the flag per volume from Query 1.

## Blast radius classification
- **Default:** 🟡 — see the Attachment table (EIP, target group). Confirm via Query 1 / 4 before acting.

## Rollback note (informational, shown in plan)
"Termination is irreversible. Root and other volumes with `DeleteOnTermination=true` are destroyed with the instance — their data is only recoverable from a snapshot/AMI taken beforehand. If a volume has `DeleteOnTermination=false` it persists (and keeps billing) and a new instance can be launched from it, but the original instance ID is gone. Before terminating: confirm which EIP is associated (it is disassociated, not released, on termination), and capture a final AMI for the fastest restore path. If Ownership is `unmanaged`, there is no IaC to re-apply."
