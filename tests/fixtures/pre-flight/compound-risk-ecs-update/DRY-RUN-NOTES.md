# Dry-run of `pre-flight` against `compound-risk-ecs-update`

Simulated run of the 7-step skill against this fixture. Recorded on 2026-04-23.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Assessor loading | `assessors/iac-change.md` matched ecspresso diff output |
| Multi-Yellow escalation | 4 Yellow categories → escalated to Red soft block |
| Bundled change detection | 3 distinct changes in one deploy (image, scale, health check) amplify compound risk |
| Capacity reduction risk | Scaling from 4 to 2 tasks is a 50% capacity reduction |
| Health check change | Changing health check path can cause ALB to mark tasks unhealthy during rollout |

## Scoring detail

| # | Category | Score | Signal |
|---|----------|-------|--------|
| 1 | Blast radius | 🟡 | Health check path change affects ALB routing; if new path returns 404, all tasks marked unhealthy. Scale-down reduces redundancy. |
| 2 | Reversibility | 🟢 | ecspresso rollback available (`ecspresso rollback`); image tags are immutable in ECR; previous task definition revision preserved |
| 3 | Change velocity | 🟡 | Simulated: 1 commit in last 7 days (image update on Monday), this is the 2nd change |
| 4 | Dependency impact | 🟢 | No downstream consumers — searchapi is a leaf service |
| 5 | Timing context | 🟢 | Normal hours, no freeze, no incidents (from L2) |
| 6 | Operator familiarity | 🟡 | Operator answered: first time changing this service (from L2 Q4) |
| 7 | Observability readiness | 🟢 | CloudWatch alarms exist for ECS CPU/memory and ALB 5xx |
| 8 | Cost impact | 🟡 | 50% capacity reduction (4→2 tasks). Savings ~$X/month but risk of insufficient capacity during traffic spikes |
| 9 | Security posture | 🟢 | No IAM, network, or encryption changes |
| 10 | Resource health | 🟢 | Service healthy (from L2) |

**Yellow count: 4** (blast radius, change velocity, operator familiarity, cost impact)
**Multi-Yellow escalation triggered:** 4 >= 3 → **RED — SOFT BLOCK**

**Overall verdict: RED — SOFT BLOCK** (multi-Yellow escalation — compound risk)

## Mitigations the skill should recommend

1. **Split the changes:** Deploy the image update separately from the scale-down and health check change. Each change in isolation would not trigger escalation.
2. **Verify health check path:** Confirm `/healthz` endpoint exists in the `2026.04.2` image before deploying. A 404 on the health check will cause ECS to kill all tasks.
3. **Scale down gradually:** Consider 4→3 first, monitor, then 3→2 — rather than halving capacity in one step.
4. **Monitor after deploy:** Watch ALB target health and ECS task count for 15 minutes after deploy. Have `ecspresso rollback` ready.
5. **Consider staging first:** Since this is the operator's first change to this service, deploy to staging first to validate the health check path change.
