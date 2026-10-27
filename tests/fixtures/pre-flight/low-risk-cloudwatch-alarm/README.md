# low-risk-cloudwatch-alarm — pre-flight fixture

A Terraform change that adds a single CloudWatch alarm to an existing ECS service. Expected outcome: all Green.

## What's modelled

`orderapi` — a fictional ECS Fargate service in `us-east-1`. The service already exists and is stable. The change adds a CPU utilization alarm.

## The proposed change

Add one `aws_cloudwatch_metric_alarm` resource for CPU utilization on the existing `orderapi-prod` ECS service. No other resources are modified or destroyed.

## Expected pre-flight scores

All Green:
- Blast radius: Green (`plan:` one added alarm, single region, notify-only, so not app-facing: no disruption evidence needed)
- Reversibility: Green (`plan:` a pure addition of an alarm; no behaviour claim needed)
- Change velocity: Green (first change in 7+ days)
- Dependency impact: Green (`plan:` every changed resource is not-app-facing and no output / export changes)
- Timing context: Green (normal hours, no freeze, no incidents)
- Operator familiarity: Green (experienced with this service and Terraform)
- Observability readiness: Green (`plan:` the change only adds a notify-only alarm; `live:4` finds no existing alarm on this metric, so the plan creates an alarm and overwrites none. Confirming it exists and is enabled is a post-apply step)
- Cost impact: Green (`plan:` the only new resource is an alarm; priced from the AWS Price List file for `us-east-1`, publication 2026-10-07, read 2026-10-27: `CW:AlarmMonitorUsage` standard resolution, 0.10 USD per alarm)
- Security posture: Green (no IAM/network/encryption changes)
- Resource health: Green (live evidence — L3 approved: `ecs describe-services` running = desired, no alarm in `ALARM` on the service's dimensions)
- Application compatibility: Green once L3 shows the alarm only notifies: the `orderapi-alerts` subscription protocols are `email`, `email` (`plan: only not-app-facing attributes changed (notify-only alarm)`, `live`)

## What this fixture exercises

- **Assessor loading:** `iac-change.md` matches Terraform plan output
- **All-Green scoring:** verifies the skill can produce a clean "proceed" verdict
- **L1 analysis:** simple plan output with 1 addition, 0 modifications, 0 deletions
- **Observability readiness:** adding monitoring should improve, not degrade, the score
- **Evidence rule:** GREEN needs live health evidence. Variant: with L3 declined, resource health is ⚪ and the verdict is capped at **YELLOW**
- **Priced, not remembered:** the alarm exemption for cost needs a dated price lookup (`docs:` or the Price List), not a remembered figure
- **Live alarm check:** `describe-alarms-for-metric` with `ActionsEnabled` runs in the L3 batch before apply
- **Fresh eyes on YELLOW:** the L3-declined variant ends YELLOW, so a separate reviewer runs
