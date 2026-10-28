# World index — nightly-job-not-deploy

The first matching row wins; `*` matches any text. A command that matches no row returns `_default.txt` (`{}` for a JSON API, no lines for a text command): no data, never an error. Profile `prod-read` is the only AWS profile; region `us-east-1` is implied when omitted.

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | Per-org facts. It has no timezone entry. |
| `ls * .culiops/sre-investigate*` | `_default.txt` | Only `environment.md` exists; no `profiles/`, `lessons.md` or `incidents/` yet. |
| `command -v agentbox-env` | `_default.txt` | No output, exit status 1 (not installed). |
| `aws sts get-caller-identity --profile prod-read*` | `sts-prod-read.json` | SSO read-only assumed role. |
| `aws iam get-role --profile prod-read * AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b*` | `iam-get-role.json` | Resolves the role ARN (with its path). |
| `aws iam simulate-principal-policy --profile prod-read *` | `iam-simulate-readonly.json` | Every write action evaluates to `implicitDeny`. |
| `aws cloudwatch describe-alarms --profile prod-read *orders-api*` | `cw-describe-alarms.json` | Alarm definition and current state. |
| `aws cloudwatch describe-alarm-history --profile prod-read *orders-api-5xx-high*` | `alarm-history.json` | 30 days of state changes. Timestamps are rendered with a `+09:00` offset. |
| `aws cloudwatch get-metric-data --profile prod-read * --start-time 2026-10-07*` | `cw-5xx-14d-1h.json` | Any ALB 5xx query for orders-api over the 14 days before now, period 3600. Hours with zero 5xx have no datapoint. |
| `aws cloudwatch get-metric-data --profile prod-read * --start-time 2026-10-21*` | `cw-5xx-incident-1m.json` | ALB 5xx, period 60, 2026-10-21 01:00–02:40 UTC. |
| `aws cloudwatch get-metric-data --profile prod-read * --start-time 2026-10-20*` | `cw-5xx-prev-day-1m.json` | Same query one day earlier. |
| `aws cloudwatch get-metric-data --profile prod-read * --start-time 2026-10-14*` | `cw-5xx-minus7d-1m.json` | Same query seven days earlier. |
| `aws ecs describe-services --profile prod-read * orders-api*` | `ecs-describe-services.json` | Deployments and service events. |
| `aws ecs describe-task-definition --profile prod-read * orders-api:41*` | `ecs-taskdef-41.json` | Previous revision. |
| `aws ecs describe-task-definition --profile prod-read * orders-api:42*` | `ecs-taskdef-42.json` | Current revision. |
| `gh release view * --repo example-org/orders-api*` | `gh-release-notes.txt` | Release notes of the deployed image tag. |
| `aws events list-rules --profile prod-read*` | `events-list-rules.json` | EventBridge rules on the default bus. |
| `aws events describe-rule --profile prod-read * orders-reconcile-nightly*` | `events-describe-rule-reconcile.json` | |
| `aws events list-targets-by-rule --profile prod-read * orders-reconcile-nightly*` | `events-targets-reconcile.json` | |
| `aws scheduler list-schedules --profile prod-read*` | `scheduler-list-schedules.json` | No EventBridge Scheduler schedules. |
| `aws ecs list-tasks --profile prod-read * events-rule/orders-reconcile-nightly*` | `ecs-list-tasks-reconcile.json` | Recently stopped task started by the rule. |
| `aws ecs list-tasks --profile prod-read * --family orders-reconcile*` | `ecs-list-tasks-reconcile.json` | |
| `aws ecs describe-tasks --profile prod-read * 7e4b1c90d2a84f61b3c5a6d7e8f90123*` | `ecs-describe-tasks-reconcile.json` | Start and stop times of tonight's run. |
| `aws cloudtrail lookup-events --profile prod-read *` | `cloudtrail-lookup-ecs.json` | ECS write events 2026-10-21 00:00–02:40 UTC. |
| `aws logs describe-log-groups --profile prod-read*` | `logs-describe-log-groups.json` | `storedBytes` and `retentionInDays` for the scan estimate. |
| `aws logs start-query --profile prod-read * /ecs/orders-api * ecs_task_revision*` | `li-start-revision-split.json` | Any 5xx count grouped by task revision. |
| `aws logs start-query --profile prod-read * /ecs/orders-api * error_code*` | `li-start-error-codes.json` | Any 5xx count grouped by error code (and route). |
| `aws logs start-query --profile prod-read * /ecs/orders-reconcile*` | `li-start-reconcile.json` | Any query on the reconcile job's log group. |
| `aws logs start-query --profile prod-read * /ecs/orders-api*` | `li-start-raw.json` | Any other orders-api query (raw lines around onset). |
| `aws logs get-query-results --profile prod-read * 8d1f2c4e-5a7b-4c3d-9e1f-0a2b3c4d5e6f*` | `li-results-revision-split.json` | 5xx per hour per task revision, 2026-10-19 00:00 → now. |
| `aws logs get-query-results --profile prod-read * 2b7e9a10-3c4d-4e5f-8a9b-0c1d2e3f4a5b*` | `li-results-error-codes.json` | Incident window 02:00–02:40 UTC. |
| `aws logs get-query-results --profile prod-read * c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b*` | `li-results-raw.json` | 8 sample lines, 02:01–02:19 UTC. |
| `aws logs get-query-results --profile prod-read * f0e1d2c3-b4a5-4968-8776-655443322110*` | `li-results-reconcile.json` | Reconcile job lines, tonight's run. |
| `aws logs stop-query *` | `_default.txt` | |
