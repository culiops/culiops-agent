---
cloud: aws
action: delete
resource_type: ec2-instance
applies_when: action == "delete" AND resource matches "i-*"
---

# Verify: Delete idle EC2 instance

## Required IAM
- `ec2:DescribeInstances`
- `cloudwatch:GetMetricStatistics`
- `cloudtrail:LookupEvents`

## Queries

1. `aws ec2 describe-instances --instance-ids <id>` — confirms current state, attached EBS volumes, Elastic IP associations, and tags.
2. `aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=<id> --start-time <now-14d> --end-time <now> --period 86400 --statistics Average Maximum` — 14-day CPU utilization (daily granularity).
3. `aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name NetworkIn --dimensions Name=InstanceId,Value=<id> --start-time <now-14d> --end-time <now> --period 86400 --statistics Sum` — 14-day inbound network traffic.
4. `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<id> --start-time <now-14d>` — login events, `ConsoleLogin`, `StartInstances`, or `RunInstances` history.

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|------------|
| 14d average CPU utilization | < 2% | ≥ 50% on any day |
| 14d daily NetworkIn | < 1 MB/day on all days | ≥ 100 MB/day on any day |
| `ConsoleLogin` or `StartInstances` events in last 14d | none | any |
| `Instances[0].State.Name` | `stopped` or `running` with all metrics idle | `pending` or `shutting-down` |

## Reversibility classification
- **Default:** 🔴 irreversible. Termination destroys instance-store volumes permanently; the original instance ID cannot be reused.
- **Mitigated:** 🟡 if the root EBS has `DeleteOnTermination=false` AND a recent AMI exists — instance can be rebuilt from the AMI, ~10–20 min RTO.

## Blast radius classification
- **Default:** 🟡 — the instance may hold an associated Elastic IP referenced by DNS or partner allowlists. Confirm EIP association via `describe-instances` before acting.

## Rollback note (informational, shown in plan)
"Termination is irreversible. If the root EBS has `DeleteOnTermination=false`, the volume persists and a new instance can be launched from it, but the original instance ID is gone. Before terminating, confirm no Elastic IP is associated (or disassociate it first) and capture a final AMI for fastest restore path."
