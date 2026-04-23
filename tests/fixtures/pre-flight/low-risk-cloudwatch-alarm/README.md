# low-risk-cloudwatch-alarm — pre-flight fixture

A Terraform change that adds a single CloudWatch alarm to an existing ECS service. Expected outcome: all Green.

## What's modelled

`orderapi` — a fictional ECS Fargate service in `us-east-1`. The service already exists and is stable. The change adds a CPU utilization alarm.

## The proposed change

Add one `aws_cloudwatch_metric_alarm` resource for CPU utilization on the existing `orderapi-prod` ECS service. No other resources are modified or destroyed.

## Expected pre-flight scores

All Green:
- Blast radius: Green (single resource, single region, non-data-path)
- Reversibility: Green (alarm can be deleted trivially)
- Change velocity: Green (first change in 7+ days)
- Dependency impact: Green (no downstream dependencies on a CloudWatch alarm)
- Timing context: Green (normal hours, no freeze, no incidents)
- Operator familiarity: Green (experienced with this service and Terraform)
- Observability readiness: Green (adding monitoring improves observability)
- Cost impact: Green (CloudWatch alarm cost is negligible)
- Security posture: Green (no IAM/network/encryption changes)
- Resource health: Green (service is healthy, confirmed via L2)

## What this fixture exercises

- **Assessor loading:** `iac-change.md` matches Terraform plan output
- **All-Green scoring:** verifies the skill can produce a clean "proceed" verdict
- **L1 analysis:** simple plan output with 1 addition, 0 modifications, 0 deletions
- **Observability readiness:** adding monitoring should improve, not degrade, the score
