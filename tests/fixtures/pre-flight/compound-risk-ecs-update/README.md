# compound-risk-ecs-update — pre-flight fixture

An ecspresso change that updates container image, scales down desired count, and modifies health check path. Each individual change is Yellow, but 3+ Yellows trigger multi-Yellow escalation to Red. Expected outcome: Red soft block via escalation.

## What's modelled

`searchapi` — a fictional ECS Fargate service in `us-east-1`. The service handles search queries for the main product. The operator is making their first change to this service.

## The proposed change

Three changes bundled in one deploy:
1. Update container image tag from `2026.04.1` to `2026.04.2`
2. Scale desired count from 4 to 2 (cost reduction)
3. Change health check path from `/health` to `/healthz`

## Expected pre-flight scores

Multiple Yellows → escalation:
- Blast radius: **Yellow** (health check path change affects ALB routing for the service)
- Reversibility: Green (ecspresso rollback available, image tags are immutable)
- Change velocity: **Yellow** (2nd change to this service this week — image update on Monday)
- Dependency impact: Green (no downstream consumers of this service's outputs)
- Timing context: Green (normal hours, no freeze, no incidents)
- Operator familiarity: **Yellow** (first time changing this specific service)
- Observability readiness: Green (CloudWatch alarms exist for the ECS service)
- Cost impact: **Yellow** (scaling from 4 to 2 tasks — 50% capacity reduction)
- Security posture: Green (no IAM/network/encryption changes)
- Resource health: Green (service is healthy)

4 Yellows → **multi-Yellow escalation → RED — SOFT BLOCK**

## What this fixture exercises

- **Multi-Yellow escalation rule:** verifies that 3+ Yellows escalate to Red soft block
- **ecspresso assessor path:** validates iac-change assessor works with ecspresso diff output
- **Bundled changes:** multiple changes in one deploy amplify compound risk
- **Capacity reduction risk:** scaling down during normal traffic is a capacity risk
