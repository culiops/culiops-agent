# Dry-run of `pre-flight` against `compound-risk-ecs-update`

Simulated run of the 7-step skill against this fixture. Recorded on 2026-04-23; re-run 2026-10-26 against the evidence rule and the cost-vs-capacity rule; re-run 2026-10-27 against the decision-evidence rules.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Assessor loading | `assessors/iac-change.md` matched ecspresso diff output |
| Multi-Yellow escalation | 3 Yellow categories → escalated to Red soft block |
| Bundled change detection | 3 distinct changes in one deploy (image, scale, health check) amplify compound risk |
| Capacity reduction risk | Scaling from 4 to 2 tasks is a 50% capacity reduction — scored under blast radius; cost is Green (a decrease) |
| Health check change | The container `healthCheck` (task definition) path changes; if `/healthz` fails, ECS kills the new tasks and the deployment stalls or rolls back. The ALB target-group check is a separate setting |
| Secrets in diff | `ecspresso diff` prints task-definition env values in plaintext — record names only |
| Evidence rule | Category 10 Green cites live `ecs describe-services` + firing-alarm check (L3 approved) |
| Reversibility needs evidence for the behaviour | Green on category 2 for in-place attribute changes needs `docs:` or `live:` that each change can be undone. `docs:` https://github.com/kayac/ecspresso (Rollback section, read 2026-10-27): "rolls back a service to the previous task definition revision". It says nothing about desired count, so that change is restored by re-deploying the previous service definition from git (`code:`), as before, with `docs:` https://docs.aws.amazon.com/boto3/latest/reference/services/ecs/client/update_service.html, read 2026-10-27: a new `desiredCount` adds to or subtracts from the number of tasks. Image tag immutability is a live fact: `live:6` `aws ecr describe-repositories` → `imageTagMutability` |
| Dependency impact is not Green from memory | "Leaf service" was recalled, not shown. No catalog, and no query can list callers that reach the service through the load balancer → ⚪ |
| Fresh eyes | Verdict is RED — soft block, so it is not required: the operator must acknowledge each Red with a reason. Record line: `Fresh eyes: not required (verdict RED — soft block)` |

## Scoring detail

| # | Category | Score | Signal |
|---|----------|-------|--------|
| 1 | Blast radius | 🟡 | Scale-down 4→2 halves capacity and redundancy; if the new container health-check path fails, ECS replaces tasks in a loop (`plan:5-7`, `plan:14-16`) |
| 2 | Reversibility | 🟢 | `ecspresso rollback` restores the previous task definition (image + health check) (`docs:` ecspresso README, Rollback, read 2026-10-27); tags are immutable (`live:6`); the desired count needs the previous service definition re-deployed from git (`code:`; `docs:` ECS `UpdateService`, read 2026-10-27) — both known, scripted paths |
| 3 | Change velocity | 🟡 | Simulated: 1 commit in last 7 days (image update on Monday), this is the 2nd change |
| 4 | Dependency impact | ⚪ | No catalog. Nothing in the repo (`code`) or in a live query shows that nothing consumes the service, and callers through the load balancer are invisible to both |
| 5 | Timing context | 🟢 | Normal hours, no freeze, no incidents (from L2) |
| 6 | Operator familiarity | 🟡 | Operator answered: first time changing this service (from L2 Q4) |
| 7 | Observability readiness | 🟢 | CloudWatch alarms for ECS CPU/memory and ALB 5xx exist in the IaC and live, with `ActionsEnabled: true` (`live:5`) |
| 8 | Cost impact | 🟢 | Cost decreases (4→2 tasks). Capacity risk scored under blast radius |
| 9 | Security posture | 🟢 | No IAM, network, or encryption changes |
| 10 | Resource health | 🟢 | `live:2` 4/4 running, 0 pending; `live:4` no alarm in `ALARM` on the service |
| 11 | Application compatibility | ⚪ | Container `healthCheck` path `/health` → `/healthz` (`plan:14-16`) is an app-facing change; no app source given at Q8 → unknown whether image `2026.04.2` serves `/healthz` |

**Yellow + ⚪ count: 5** (blast radius, change velocity, operator familiarity; ⚪ dependency impact, application compatibility)
**Multi-Yellow escalation triggered:** 5 >= 3 → **RED — SOFT BLOCK**

Record header: Plan hash `sha256:ef96fe1da0f5310e450c54d6978c86f032d787fccffef4b73b36ed783659c911` (SHA-256 of `plan-output.txt`), target account `<plan account>` / `us-east-1`.

**Overall verdict: RED — SOFT BLOCK** (multi-Yellow escalation — compound risk)

## Mitigations the skill should recommend

1. **Split the changes:** Deploy the image update separately from the scale-down and health check change. Each change in isolation would not trigger escalation.
2. **Verify health check path:** Confirm `/healthz` endpoint exists in the `2026.04.2` image before deploying. A 404 on the health check will cause ECS to kill all tasks.
3. **Scale down gradually:** Consider 4→3 first, monitor, then 3→2 — rather than halving capacity in one step.
4. **Monitor after deploy:** Watch ALB target health and ECS task count for 15 minutes after deploy. Have `ecspresso rollback` ready.
5. **Consider staging first:** Since this is the operator's first change to this service, deploy to staging first to validate the health check path change.
