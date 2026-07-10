---
cloud: aws
action: rightsize
resource_type: ec2-instance
applies_when: action == "rightsize" AND resource matches "i-*"
---

# Verify: Rightsize EC2 instance

## Required IAM
- `ec2:DescribeInstances`
- `cloudwatch:GetMetricStatistics`
- `compute-optimizer:GetEC2InstanceRecommendations` (if Compute Optimizer enabled; preferred over manual computation)
- `elasticloadbalancing:DescribeTargetGroups`
- `elasticloadbalancing:DescribeTargetHealth`

## Queries

1. `aws ec2 describe-instances --instance-ids <id> --query 'Reservations[].Instances[].[InstanceType,LaunchTime,Tags]'` — current type and age.
2. `aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=<id> --start-time <now-30d> --end-time <now> --period 86400 --statistics Average,Maximum` — 30d CPU avg + peak.
3. `aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name NetworkIn --dimensions Name=InstanceId,Value=<id> --start-time <now-30d> --end-time <now> --period 86400 --statistics Average,Maximum` — network baseline (catches network-bound workloads that pin a small instance).
4. `aws cloudwatch get-metric-statistics --namespace CWAgent --metric-name mem_used_percent --dimensions Name=InstanceId,Value=<id> --start-time <now-30d> --end-time <now> --period 86400 --statistics Average,Maximum` — memory baseline if CloudWatch agent installed. Returns no datapoints if not installed → score ⚪.
5. `aws compute-optimizer get-ec2-instance-recommendations --instance-arns <arn>` — if Compute Optimizer is the source of the upstream recommendation, fetch the rationale.
6. `aws elbv2 describe-target-health --target-group-arn <each-tg>` — confirm instance is in known target groups (for blast-radius dependency count).

## Evidence thresholds

| Signal | 🟢 Threshold (safe to downsize) | 🚫 Trigger (do not downsize) |
|--------|-------------------------------|-------------------------------|
| 30d avg CPU | < 30% of current instance class capacity | n/a (low CPU alone is not a 🚫; high CPU is) |
| 30d peak CPU | < 75% on recommended new class | ≥ 90% on recommended new class — at risk of saturation post-downsize |
| 30d peak NetworkIn | < 50% of new class's bandwidth | ≥ 90% — network-bound |
| 30d peak memory (if available) | < 75% on new class | ≥ 90% on new class |
| Active alarms on this instance | 0 | ≥ 1 alarm in ALARM state |

## Reversibility classification
- **Default:** 🟢 reversible — re-apply old IaC restores the larger instance type. Requires a stop/start (downtime ~2-5min) per resize.

## Blast radius classification
- **Default:** 🟡 — touches a live resource; if instance is in an ALB target group with a single target, the resize stop/start is an outage. Default to 🟡; bump to 🟢 if catalog confirms ≥ 2 healthy targets OR auto-scaling group with `MinSize ≥ 2`.

## Rollback note (informational, shown in plan)
"Re-apply old IaC to restore original instance type. Stop/start required for type change — service must tolerate ~2-5min downtime OR be behind an ALB with redundancy. Pre-resize: take an AMI for fastest restore if rollback becomes urgent."
