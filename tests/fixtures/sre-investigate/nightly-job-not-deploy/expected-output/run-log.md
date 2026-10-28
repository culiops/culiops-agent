# Run log: sre-investigate, case-c, orders-api prod

Run directory: `orders-api-prod-20261021-0240` (under the simulated output root `.culiops/sre-investigate/`, written here as `out/`). Mode: Fast (the operator said "Fast mode please"). Simulated "now": 2026-10-21 02:40 UTC (11:40 JST). `date -u` has no INDEX row (empty default), so wave Start times in the ledger are approximate (~02:40 wave 0, ~02:42 wave 1, ~02:44 wave 2, ~02:48 wave 3).

## Operator lines

| # | Line | When it was received | Cue |
|---|---|---|---|
| 1 | `orders-api in prod has been throwing 5xx since around 11 this morning. We shipped a release just before that. Fast mode please.` | Opening request | n/a |
| 2 | `Tokyo time, UTC+9.` | Right after message 1, while wave 0 was running | I asked which zone to read "around 11 this morning" in (environment.md has no `timezone`) |
| 3 | `Go ahead.` | **Never given** | The cue never happened: no Logs Insights query was estimated above `insights_ask_threshold_gb` (10 GB) after narrowing. Largest estimate 0.030 GB (reported `bytesScanned` 0.48 GB, an upper bound). I did not run the 14-day `error_code` / revision counts (about 30 GB estimate) and offered them under "go deep" instead. |

## Phase 0: output root, environment, mode, intake

### Setup commands (before the first message; simulated, all read-only)

| # | Command | World file | Key facts |
|---|---|---|---|
| S1 | `git rev-parse --show-toplevel` | `_empty.txt` (git, no row) | No output. The working directory is taken as the repo root (the INDEX paths are relative to it). |
| S2 | `echo "${CULIOPS_HOME:-}"` | `_empty.txt` (echo, no row) | Empty, so the output root is `.culiops/sre-investigate/` at the repo root. |
| S3 | `git check-ignore -q .culiops/sre-investigate; echo $?` | `_empty.txt` (git, no row) | Exit status 0 by the INDEX default: ignored by git. |
| S4 | `command -v agentbox-env` | `_empty.txt` (INDEX row, exit 1) | Fails: nothing printed about Culibox. |
| S5 | `ls .culiops/sre-investigate` | `ls-01.txt` | Only `environment.md`: no `profiles/`, `lessons.md`, `incidents/` or `runs/`. |
| S6 | `cat .culiops/sre-investigate/environment.md` | `environment.md` | Account prod 111122223333 us-east-1, profile `prod-read`; no Kubernetes; backends CloudWatch metrics/alarms, Logs Insights `/ecs/*`, CloudTrail; no tracing or error tracker; app source `example-org/orders-api` via `gh`, no clone; Logs Insights ask above 10 GB; default SEV scale; core flows checkout `POST /orders` and order status `PATCH /orders/{id}`. **No `timezone`. No token backends. Only the ask threshold is set under budgets.** |

Run directory and ledger created (`mkdir -p` of `runs/orders-api-prod-20261021-0240/`, ledger copied from the template).

### Message 1 (shown to the operator, verbatim)

```text
Mode: Fast. You said "Fast mode" and the 5xx is ongoing.
Output root: .culiops/sre-investigate/ (repo root). It is local and is never committed. `git check-ignore -q .culiops/sre-investigate` exited 0, so git ignores it.
environment.md found. Account prod (111122223333, us-east-1, profile prod-read). Backends: CloudWatch metrics and alarms, Logs Insights on /ecs/*, CloudTrail. No Kubernetes, tracing or error tracker. Code: example-org/orders-api through gh, no local clone.
Question: environment.md has no `timezone`. Which zone should I read "around 11 this morning" in?
While you answer I am running wave 0 (identity, write-check, log-group probe, alarm discovery). None of it depends on the incident window.
```

### Wave 0 (printed in full, then run)

Printed:

```text
W0-C1  date -u +%H:%M:%S; TZ=UTC aws sts get-caller-identity --profile prod-read --region us-east-1 --output json
W0-C2  arn=$(aws sts get-caller-identity --profile prod-read --query Arn --output text)
       role=${arn#*:assumed-role/}; role=${role%%/*}
       role_arn=$(aws iam get-role --profile prod-read --role-name "$role" --query Role.Arn --output text)
       aws iam simulate-principal-policy --profile prod-read --policy-source-arn "$role_arn" \
         --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode cloudformation:DeleteStack \
         --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text
W0-C3  aws logs describe-log-groups --profile prod-read --region us-east-1 --log-group-name-prefix "/ecs/orders-api" --output json
W0-C4  aws cloudwatch describe-alarms --profile prod-read --region us-east-1 --output json
Tokens: environment.md lists no token_env, so there is nothing to check.
Stored profile, lessons.md, incidents/: the output root holds only environment.md (ls), so none exist.
```

| Query ID | Command | World file | Key facts |
|---|---|---|---|
| (date) | `date -u +%H:%M:%S` | `_empty.txt` (no row) | No output; clock assumed 02:40 UTC. |
| W0-Q1 | `aws sts get-caller-identity` | `sts-01.json` | Account 111122223333 (matches), assumed role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b`. Session name not recorded. |
| W0-Q2 | `aws iam get-role` + `aws iam simulate-principal-policy` | `iam-01.json`, `iam-02.json` | Path `/aws-reserved/sso.amazonaws.com/`. Simulation: 7 of the 10 requested actions `implicitDeny`; **no row** for `ec2:AuthorizeSecurityGroupIngress`, `iam:CreateAccessKey`, `cloudformation:DeleteStack`; 3 unrequested rows (`ec2:ModifyInstanceAttribute`, `ecs:StopTask`, `iam:AttachRolePolicy`, all `implicitDeny`) ignored. No allowed action, so no boxed warning; not "read-only confirmed" because of the 3 missing rows. |
| W0-Q3 | `aws logs describe-log-groups --log-group-name-prefix "/ecs/orders-api"` | `logs-01.json` | `/ecs/orders-api` 64,424,509,440 bytes, 30 d retention, STANDARD; `/ecs/orders-reconcile` 1,073,741,824 bytes. Estimates: 15 min 0.022 GB, 70 min 0.104 GB, 14 d 30 GB. |
| W0-Q4 | `aws cloudwatch describe-alarms` | `cw-01.json` | One alarm `orders-api-5xx-high`: target 5xx Sum, period 60, threshold 25, 2 of 3, OK since 02:12 UTC (the CLI printed 11:12+09:00). LB `app/prod-public/50dc6c495c0c9188`, TG `targetgroup/orders-api/943f017f100becff`. |

### Message 2 (verbatim, after wave 0)

```text
Wave 0 results.
Identity: profile prod-read, account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b.
Write check, prod-read: none of the 7 actions that returned a row is allowed (all implicitDeny). The simulation returned no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack. I can't say "read-only confirmed". Write capability for those three is unknown (gap). This is not a finding that the credentials can write. I'm not inferring read-only from the role name.
Tokens: environment.md lists no token-based backend, so there is nothing to check.
Log source: /ecs/orders-api, 30-day retention, about 64.4 GB stored. A 15-minute scan estimates at about 0.02 GB.
Alarm: orders-api-5xx-high (target 5xx above 25/min) is in state OK, last changed 02:12 UTC. That doesn't match "still throwing 5xx". I'll check it against the metrics.
Gaps so far: no timezone in environment.md (asked above), the three missing write-check rows, no IaC repo or local clone configured, no tracing or error tracker.
```

**Operator line 2 received here:** `Tokyo time, UTC+9.` Recorded in the ledger as Asia/Tokyo (UTC+9, no DST), source: the user in chat (not environment.md, not the +09:00 the CLI printed).

Window (rule 2: rough time of day, local): anchor 11:00 JST = 02:00 UTC; window 01:30–02:40 UTC; previous 00:20–01:30; −7d 2026-10-14 01:30–02:40. Stated to the operator in message 3's tail (below).

## Build profile (no stored profile)

Helper `TASK: PROFILE`, cheapest tier, simulated inline following `agents/helper.md`. Prompt shown to the operator:

```text
TASK: PROFILE
Service: orders-api
Environment: prod
Profile template: <skill dir>/templates/profile.md
Identifier lessons (hints only, up to ten): none
(discovery checklist as in agents/helper.md; reuses W0-Q3 log groups and W0-Q4 alarm dimensions)
```

Helper wave, printed in full:

```text
H-1  aws ecs list-clusters --profile prod-read --region us-east-1 --output json
H-2  aws ecs list-services --profile prod-read --region us-east-1 --cluster <cluster from H-1> --output json
H-3  aws ecs list-task-definition-families --profile prod-read --region us-east-1 --status ACTIVE --output json
H-4  aws cloudwatch list-metrics --profile prod-read --region us-east-1 --namespace AWS/ApplicationELB --metric-name RequestCount --output json
H-5  aws elbv2 describe-target-groups --profile prod-read --region us-east-1 --query "TargetGroups[?contains(TargetGroupName,'orders')].[TargetGroupName,TargetGroupArn]" --output json
H-6  aws rds describe-db-clusters --profile prod-read --region us-east-1 --db-cluster-identifier orders-db --query 'DBClusters[0].DBClusterIdentifier' --output json
```

| Query ID | Command | World file | Key facts |
|---|---|---|---|
| W0-Q5 (H-1) | `aws ecs list-clusters` | `ecs-11.json` | cluster `prod` |
| W0-Q6 (H-2) | `aws ecs list-services --cluster prod` | `ecs-09.json` | service `orders-api` |
| W0-Q7 (H-3) | `aws ecs list-task-definition-families` | `ecs-10.json` | `orders-api`, `orders-migrate`, `orders-reconcile` |
| W0-Q8 (H-4) | `aws cloudwatch list-metrics --namespace AWS/ApplicationELB` | `cw-05.json` | 6 metrics on the TG/LB; no `HTTPCode_ELB_5XX_Count` |
| W0-Q9 (H-5) | `aws elbv2 describe-target-groups …` | `_default.txt` | `{}` |
| W0-Q10 (H-6) | `aws rds describe-db-clusters …` | `_default.txt` | `{}`; Aurora `orders-db` stays (unverified) |

Helper not asked for: IaC (none configured), dashboards (none), tracing/Prometheus (none).

### Message 3 (verbatim, profile shown and windows stated)

```text
Profile built for orders-api prod (shown; correct me as I go). Written to the run directory as profile.md.
- Compute: ECS cluster prod, service orders-api, task definition families orders-api, orders-migrate and orders-reconcile.
- Load balancer: ALB app/prod-public/50dc6c495c0c9188, target group targetgroup/orders-api/943f017f100becff. Metrics were listed, so these are verified.
- Logs: /ecs/orders-api in CloudWatch. It is listed but no line has been read yet.
- Alarm: orders-api-5xx-high.
- Not found: the target group and Aurora orders-db lookups returned nothing, so those identifiers stay (unverified). No IaC repo and no error tracker are configured.
- Siblings: none, a single service in one region.
Run directory: runs/orders-api-prod-20261021-0240/.
```

and, in the same turn: `Windows (UTC), from your Tokyo time: anchor 11:00 JST = 02:00 UTC. Incident 01:30-02:40, previous 00:20-01:30, −7d 2026-10-14 01:30-02:40.`

Files written so far: `runs/orders-api-prod-20261021-0240/profile.md`, `runs/orders-api-prod-20261021-0240/ledger.md` (wave 0 rows written before use).

## Phase 1: wave 1 (scope, impact, recurrence)

Printed in full (shown to the operator, verbatim):

```text
W1-Q1  date -u +%H:%M:%S; TZ=UTC aws ecs describe-services --profile prod-read --region us-east-1 --cluster prod --services orders-api --query 'services[0].{rollouts: deployments[].{state: status, progress: rolloutState, def: taskDefinition, since: createdAt, last: updatedAt, want: desiredCount, run: runningCount, deployment: id}, recentEvents: events[:30].{at: createdAt, msg: message}}' --output json > "$RUN/c-ecs-deployments.json"
W1-Q2  for st in RUNNING STOPPED; do arns=$(TZ=UTC aws ecs list-tasks --profile prod-read --region us-east-1 --cluster prod --service-name orders-api --desired-status "$st" --max-items 100 --query 'taskArns' --output text); [ -n "$arns" ] && [ "$arns" != "None" ] && TZ=UTC aws ecs describe-tasks --profile prod-read --region us-east-1 --cluster prod --tasks $arns --query 'tasks[].[taskArn, taskDefinitionArn, startedAt, stoppedAt]' --output text; done > "$RUN/c-task-revisions.tsv"
W1-Q3  TZ=UTC aws application-autoscaling describe-scheduled-actions --profile prod-read --region us-east-1 --service-namespace ecs --resource-id service/prod/orders-api --query 'ScheduledActions[].[ScheduledActionName, Schedule, Timezone, ScalableTargetAction.MinCapacity, ScalableTargetAction.MaxCapacity]' --output text
W1-Q4  TZ=UTC aws application-autoscaling describe-scaling-activities --profile prod-read --region us-east-1 --service-namespace ecs --resource-id service/prod/orders-api --max-results 50 --query 'ScalingActivities[].[StartTime, StatusCode, Description, Cause]' --output text
W1-Q5  (incident, golden + availability, period 60)  TZ=UTC aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://$RUN/q-golden-60.json --start-time 2026-10-21T01:30:00Z --end-time 2026-10-21T02:40:00Z --output json > "$RUN/m-golden-incident.json"
W1-Q6  (previous)  same, --start-time 2026-10-21T00:20:00Z --end-time 2026-10-21T01:30:00Z > "$RUN/m-golden-previous.json"
W1-Q7  (-7d)       same, --start-time 2026-10-14T01:30:00Z --end-time 2026-10-14T02:40:00Z > "$RUN/m-golden-minus7d.json"
        q-golden-60.json: req = RequestCount Sum; t5xx = HTTPCode_Target_5XX_Count Sum; t5xx_pct = 100 * t5xx / req; elb5xx = HTTPCode_ELB_5XX_Count Sum; unhealthy = UnHealthyHostCount Minimum; p95 = TargetResponseTime p95; all Period 60, Namespace AWS/ApplicationELB, Dimensions LoadBalancer app/prod-public/50dc6c495c0c9188 and TargetGroup targetgroup/orders-api/943f017f100becff (the elb5xx dimension is LoadBalancer only)
W1-Q8  (recurrence, 14d x 1h)  TZ=UTC aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://$RUN/q-recur-3600.json --start-time 2026-10-07T01:30:00Z --end-time 2026-10-21T01:30:00Z --output json > "$RUN/m-recur-14d-cw.json"
        q-recur-3600.json: main_err_raw = HTTPCode_Target_5XX_Count Sum Period 3600 (ReturnData false); main_err = FILL(main_err_raw, 0); main_req = RequestCount Sum Period 3600; main_p99 = TargetResponseTime p99 Period 3600; same dimensions
W1-Q9  TZ=UTC aws cloudwatch describe-alarm-history --profile prod-read --region us-east-1 --alarm-name "orders-api-5xx-high" --history-item-type StateUpdate --start-date 2026-09-21T02:40:00Z --end-date 2026-10-21T02:40:00Z --output json
Metric requests this wave: 5 metrics x 3 windows (15) + 3 for the recurrence pull = 18, against a budget of 100.
```

| Query ID | Command | World file | Key facts |
|---|---|---|---|
| W1-Q1 | `aws ecs describe-services … orders-api` | `ecs-01.json` | One deployment `ecs-svc/4417203958112934411`, PRIMARY, task def `orders-api:42`, created 01:22:07Z, COMPLETED 01:31:40Z, failedTasks 0, 6/6, circuit breaker on. Events: 6 (tasks started 01:22:31; 3 stopped 01:25:48; 3 stopped 01:29:12; steady 01:31:40; earlier steady 10-20 19:02:10). |
| W1-Q2 | `aws ecs list-tasks` RUNNING / STOPPED `--service-name orders-api`, `describe-tasks` | `ecs-04.json`, `ecs-07.json` (running); `ecs-08.json` (stopped, empty) | 6 running tasks all `orders-api:42`, started 01:23:09–01:23:29, HEALTHY. No stopped tasks listable. |
| W1-Q3 | `aws application-autoscaling describe-scheduled-actions` | `_default.txt` | `{}` |
| W1-Q4 | `aws application-autoscaling describe-scaling-activities` | `_default.txt` | `{}` |
| W1-Q5 / Q6 / Q7 | `aws cloudwatch get-metric-data … HTTPCode_Target_5XX_Count`, period 60 | `cw-04.json` (rows inside each window only) | Only the 5xx series came back (Id `m1`). Incident: sum 439, peak 55 at 02:04, episode 02:01–02:19. Previous: 3 (one per minute at 00:29, 01:24, 01:27). −7d: 459, episode 02:06–02:24, peak 57 at 02:09. RequestCount, ELB 5xx, UnHealthyHostCount, p95 not returned. |
| W1-Q8 | `aws cloudwatch get-metric-data … HTTPCode_Target_5XX_Count`, period 3600 | `cw-03.json` | Hourly, sparse, zero-filled locally: 336 hours, 233 non-zero; median 1, p95 6 (335 hours below the incident level), max 455 (10-14 02:00), incident hour 438. The 02:00 UTC hour is the top hour on 14 of 14 days (52–455). |
| W1-Q9 | `aws cloudwatch describe-alarm-history --alarm-name orders-api-5xx-high` | `cw-02.json` | 12 items back to 10-08 02:04Z. Into ALARM at 02:04 on 10-08, 10-11, 10-19, 10-21; 02:05 on 10-16; 02:09 on 10-14. Out of ALARM 02:11–02:17. |

Class: `scheduled` (rule 1). Shape: periodic. No re-anchor (true onset 02:01 UTC vs anchor 02:00).

### Message 4 (verbatim, impact block before Phase 2)

```text
Impact as of 02:40 UTC (11:40 JST, Asia/Tokyo from you)
Symptom:   HTTP 5xx from orders-api targets (ALB target-group 5xx count). Which endpoint or flow fails is not known yet; the metric has no path split.
Affected:  prod, single service, customer-facing. 439 target 5xx in 01:30-02:40 UTC, peak 55/min at 02:04 (alarm threshold 25/min). Previous window: 3. Same window a week ago (10-14): 459, peak 57/min. Share of requests failing: unknown, because RequestCount did not come back. Checkout and order-update flows not split out.
Since:     02:01 UTC (11:01 JST) · ongoing: no. The last elevated minute was 02:19 UTC (11:19 JST); the alarm has been OK since 02:12 UTC. This differs from "has been throwing 5xx": the errors stopped about 20 minutes ago.
Severity:  SEV3 (suggested, provisional) because the episode lasted about 19 minutes and is over. SEV1 or SEV2 cannot be excluded: the failing share and the affected flows are unknown. You decide.
Basis:     load-balancer target 5xx counts against baseline · W1-Q5, W1-Q6, W1-Q7, W1-Q9 · counts and timing Confirmed; request share and flow impact Assumed
Third party in the path: none known
```

followed (same turn) by:

```text
Wave 1 read, before I plan more.
- Recurrence: this is the same episode as other days. It starts at 02:01-02:09 UTC, ramps for about 3 minutes and decays over about 15. The 02:00 UTC hour is the top 5xx hour on 14 of 14 days. The alarm fired at 02:04-02:09 UTC on 10-08, 10-11, 10-14, 10-16, 10-19 and 10-21. Class: scheduled (Confirmed for the repeat, from minute-level alarm times). The cause is open.
- Your release: deployment ecs-svc/4417203958112934411 (orders-api:42) was created at 01:22:07 UTC and completed at 01:31:40 UTC, 29 minutes before the first error. The a-week-ago episode (10-14 02:06-02:24 UTC, 459 errors) had no release of today. I'm treating the release as a candidate, not a cause, and testing it with an old-against-new check.
- Gaps: only the 5xx series came back from the metric queries (no RequestCount, ELB 5xx, unhealthy hosts or latency). The six old tasks stopped at 01:25-01:29 are no longer listable.
- Windows: no re-anchor needed (true onset 02:01 UTC vs your 02:00 anchor).
```

(The severity in this block was later revised to SEV2 in the ledger after wave 2 showed both core flows among the failing routes.)

Ledger updated with wave 1 rows, impact, recurrence, timeline, gaps and a lesson candidate before anything above was said.

## Phase 2 and 3: change correlation and hypotheses

Change list (ledger timeline): the 01:22 deployment (candidate only), schedules (wave 2), scaling (none returned), no task churn after 01:31:40. Recurrence class `scheduled` placed the schedule ahead of the deploy.

Hypotheses written with falsification queries (ledger): H1 `sched:` nightly job (per candidate schedule after listing), H2 bad deploy, H3 traffic/bot, H4 DB lock/slow, H5 task churn (Ruled out from W1-Q1/W1-Q2 already). Fast mode: main session labels.

History lookup, after ranking (simulated):

| Command | World file | Result |
|---|---|---|
| `grep -ril -e orders-api -e errors-5xx -e orders-db .culiops/sre-investigate/incidents/` | `_empty.txt` | no output |
| `grep -h 'type: failure-mode' .culiops/sre-investigate/lessons.md` | `_empty.txt` | no output |

No matches, no `from-history:` entries. Logged in the ledger's Memory table.

### Message 5 (verbatim)

```text
Ranked hypotheses (full table in ledger.md, each with its falsification query):
1. H1 sched: a job or rule that fires about 02:00 UTC every day. Refuted if no schedule fires within 15 minutes of 02:00 UTC.
2. H2 bad deploy (orders-api:42). Refuted if the same episode ran on days before revision 42 existed.
3. H3 traffic spike or bot at 02:00. Refuted if request count is at baseline.
4. H4 database slow or locked at 02:00. No database metrics are readable in this run (the rds lookup returned nothing), so only the log side can be tested.
5. H5 task churn. Ruled out already: no service events after 01:31:40 and 6 of 6 tasks running since 01:23 (W1-Q1, W1-Q2).
History lookup (after ranking): no incidents/ or lessons.md exist, so no history entries.
```

## Phase 4: wave 2

Printed in full (verbatim):

```text
W2-Q1  date -u +%H:%M:%S; rules=$(TZ=UTC aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].Name' --output text); TZ=UTC aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text; for r in $rules; do TZ=UTC aws events describe-rule --profile prod-read --region us-east-1 --name "$r" --query '{name: Name, state: State, expression: ScheduleExpression}' --output json; TZ=UTC aws events list-targets-by-rule --profile prod-read --region us-east-1 --rule "$r" --query 'Targets[].{id: Id, arn: Arn, taskDef: EcsParameters.TaskDefinitionArn}' --output json; done
W2-Q2  TZ=UTC aws scheduler list-schedules --profile prod-read --region us-east-1 --query 'Schedules[].[GroupName, Name, State]' --output text   (get-schedule per result, only if it returns any)
W2-Q3  for td in orders-api:41 orders-api:42; do TZ=UTC aws ecs describe-task-definition --profile prod-read --region us-east-1 --task-definition "$td" --query 'taskDefinition.{revision: revision, registeredAt: registeredAt, cpu: cpu, memory: memory, containers: containerDefinitions[].{name: name, image: image, memory: memory, memoryReservation: memoryReservation, env: environment[].name, secrets: secrets[].name}}' --output json; done
W2-Q4  TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-21T00:01:00Z --end-time 2026-10-21T02:16:00Z --query "Events[?Resources[?contains(ResourceName || '', 'orders')]].[EventTime, EventSource, EventName, Username, EventId]" --output text
W2-Q5  TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateService --start-time 2026-10-07T00:00:00Z --end-time 2026-10-21T02:40:00Z --query "Events[?Resources[?contains(ResourceName || '', 'orders-api')]].[EventTime, EventSource, EventName, Username, EventId]" --output text
W2-Q6  gh release list --repo example-org/orders-api --limit 10; gh release view --repo example-org/orders-api
W2-Q7  (heavy log query, CloudWatch Logs Insights, log group /ecs/orders-api, window 2026-10-21 01:51:00Z–02:11:00Z, estimate 0.030 GB, limit 100 lines)
       qid=$(aws logs start-query --profile prod-read --region us-east-1 --log-group-names "/ecs/orders-api" --start-time 1792547460 --end-time 1792548660 --query-string 'fields @timestamp, @logStream, @message | filter @message like /ERROR|Error|Exception|Timeout|timed out|5[0-9][0-9]/ | sort @timestamp asc | limit 100' --query queryId --output text); then poll aws logs get-query-results --profile prod-read --region us-east-1 --query-id "$qid" every 5 s for at most 2 minutes, then aws logs stop-query only if still running
W2-Q8  TZ=UTC aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries file://$RUN/q-req-60.json --start-time 2026-10-21T01:30:00Z --end-time 2026-10-21T02:40:00Z --output json
        q-req-60.json: req = RequestCount Sum; elb5xx = HTTPCode_ELB_5XX_Count Sum; unhealthy = UnHealthyHostCount Minimum; p95 = TargetResponseTime p95; Period 60, same LB and TG dimensions (4 metric requests; asked again on its own because W1 returned only the 5xx series)
```

| Query ID | Command | World file | Key facts |
|---|---|---|---|
| W2-Q1 | `aws events list-rules` (+ `describe-rule`, `list-targets-by-rule` for scheduled rules) | `events-01.json`; `events-02.json` + `events-03.json` (orders-reconcile-nightly); `events-06.json` + `events-04.json` (catalog-sitemap-weekly) | `orders-reconcile-nightly` `cron(0 2 * * ? *)` ENABLED, target ECS cluster `prod`, task def `orders-reconcile:7`. `catalog-sitemap-weekly` `cron(30 3 ? * SUN *)`, Lambda `catalog-sitemap`. `orders-api-ecs-task-state` is an event-pattern rule, filtered out by the `ScheduleExpression` filter (its describe/targets files `events-07.json`, `events-05.json` were never opened). |
| W2-Q2 | `aws scheduler list-schedules` | `scheduler-01.json` | `Schedules: []` |
| W2-Q3 | `aws ecs describe-task-definition orders-api:41`, `orders-api:42` | `ecs-02.json`, `ecs-03.json` | Rev 41 image tag `2026.10.14-2`, registered 2026-10-14 03:10:44Z. Rev 42 image tag `2026.10.21-1`, registered 2026-10-21 01:21:58Z. Env var and secret **names** identical; values not recorded. |
| W2-Q4 | `aws cloudtrail lookup-events ReadOnly=false` 00:01–02:16 | `cloudtrail-01.json` (rows matching the lookup only) | `RunTask` 02:00:02Z (orders-reconcile:7, `ecsEventsRole-session`), `UpdateService` 01:22:07Z (`deploy-pipeline`). `RegisterTaskDefinition` 01:21:58Z has no resources and falls outside my resource filter. |
| W2-Q5 | `aws cloudtrail lookup-events EventName=UpdateService` 14 d | `cloudtrail-01.json` | 2 events: 2026-10-14 03:10:53Z (`orders-api:41`), 2026-10-21 01:22:07Z (`orders-api:42`). |
| W2-Q6 | `gh release list`, `gh release view` | `gh-02.txt`, `gh-01.txt` | Releases 2026.10.21-1 (Latest, created 01:18:02Z), 2026.10.14-2, 2026.10.07-1. Notes: confirmation email delivery date (#1182), http client bump 3.4.1 (#1185), admin pagination (#1187). Image tag = release tag. No instruction-like text. |
| W2-Q7 | Logs Insights `start-query` `/ecs/orders-api` raw lines, then `get-query-results` | `logs-04.json` (queryId `c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b`), `logs-14.json` | 6 rows inside 01:51–02:11 on 10-21: 4 x HTTP 500 `ER_LOCK_WAIT_TIMEOUT` (~50 s) on `POST /orders` (insert order_lines) at 02:01:13, 02:04:05, 02:10:18 and `PATCH /orders/{id}` (update orders set status) at 02:02:41; 1 x 502 `ECONNRESET` "payments call reset by peer" on POST /orders at 02:07:30; 1 x 200 "slow request" GET /orders 8,120 ms at 02:05:52. All `ecs_task_revision` 42. Reply also held 10-19 rows and later 10-21 rows outside my window: discarded. `bytesScanned` 481,221,632 reported (whole-reply window; upper bound). |
| W2-Q8 | `aws cloudwatch get-metric-data` RequestCount etc. | `_default.txt` | `{}`: no data. Gap remains. |

Disclosure: the single Read of `cloudtrail-01.json` (mapped by W2-Q4 and W2-Q5) showed all of its rows, including the nightly RunTask rows for 10-07 to 10-20. I did not use those until W3-Q1 mapped them. Likewise `logs-14.json` and `logs-15.json` contained rows outside the windows asked; only in-window rows were used.

### Message 6 (verbatim, after wave 2, plus wave 3 plan)

```text
Wave 2 results (all in ledger.md).
- A rule fires at 02:00 UTC every day: EventBridge orders-reconcile-nightly, cron(0 2 * * ? *), starts ECS task orders-reconcile:7 on cluster prod. CloudTrail shows its RunTask at 02:00:02 UTC today, 59 seconds before the first 5xx minute. The other schedule, catalog-sitemap-weekly, fires Sundays at 03:30 UTC and does not fit (today is a Wednesday). Ruled out.
- Your release is not the cause. Revision 42 was registered at 01:21:58 UTC and rolled out 01:22-01:31. Revision 41 (registered 2026-10-14 03:10:44 UTC) is the only other deploy in 14 days. The same 02:00 UTC episode ran 8 of 8 mornings before revision 41, 6 of 6 mornings on revision 41, and 1 of 1 on revision 42 (02:00-hour 5xx totals 52-455, 52-412 and 438). Environment variable and secret names are identical between the two revisions; only the image changed.
- Mechanism lead in the app log (sample, 5 error lines in 20 minutes): HTTP 500 after about 50 seconds with ER_LOCK_WAIT_TIMEOUT on POST /orders (insert order_lines) and PATCH /orders/{id} (update orders set status), plus one 502 ECONNRESET on a payments call. Both routes are your core flows. The first failing request began waiting at about 02:00:23 UTC, 21 seconds after the job started.
- Caveats: the log sample is 5 lines against 439 counted 5xx, so I can't say how much of the 5xx is lock waits. RequestCount did not come back a second time.
Wave 3 is the last wave in Fast mode. It reads the job's run time, its logs, its 14 nightly start times, and the release diff.
```

Corrections to message 6, noticed after it was shown: (a) the sampled-lines comparison should read "5 lines against 339 counted target 5xx in the same minutes (02:01–02:10)", not 439 (439 is the whole 70-minute window); the ledger and report use 339. (b) "52-412" for revision 41 should read "69-412" (revision 41 mornings: 133, 398, 69, 104, 412, 96); "52-455" for the revision before 41 is right for 10-07..10-14 (88, 421, 61, 117, 386, 74, 52, 455) but the earlier text mixed the two ranges. The ledger and report carry the per-day numbers. (c) "29 minutes before the first error" (message 4) is time from rollout completion to onset (01:31:40 to 02:01); from rollout start it is 39 minutes; the ledger states both.

## Phase 4: wave 3 (last Fast wave)

Printed in full (verbatim):

```text
W3-Q1  date -u +%H:%M:%S; TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=EventName,AttributeValue=RunTask --start-time 2026-10-07T00:00:00Z --end-time 2026-10-21T02:40:00Z --query "Events[?Resources[?contains(ResourceName || '', 'orders-reconcile')]].[EventTime, EventSource, EventName, Username, EventId]" --output text
W3-Q2  arns=$(TZ=UTC aws ecs list-tasks --profile prod-read --region us-east-1 --cluster prod --family orders-reconcile --desired-status STOPPED --max-items 100 --query 'taskArns' --output text); [ -n "$arns" ] && [ "$arns" != "None" ] && TZ=UTC aws ecs describe-tasks --profile prod-read --region us-east-1 --cluster prod --tasks $arns --query 'tasks[].{task: taskArn, taskDef: taskDefinitionArn, startedBy: startedBy, startedAt: startedAt, stoppedAt: stoppedAt, stopCode: stopCode, reason: stoppedReason, containers: containers[].{name: name, exit: exitCode, reason: reason}}' --output json
W3-Q3  (heavy log query, Logs Insights, log group /ecs/orders-reconcile, window 2026-10-21 01:58:00Z–02:28:00Z (30 min, at the raw-lines cap), estimate 0.0007 GB, limit 100 lines)
       qid=$(aws logs start-query --profile prod-read --region us-east-1 --log-group-names "/ecs/orders-reconcile" --start-time 1792547880 --end-time 1792549680 --query-string 'fields @timestamp, @message | sort @timestamp asc | limit 100' --query queryId --output text); then poll aws logs get-query-results --profile prod-read --region us-east-1 --query-id "$qid" every 5 s for at most 2 minutes
W3-Q4  gh api repos/example-org/orders-api/compare/2026.10.14-2...2026.10.21-1 --jq '{total: .total_commits, commits: [.commits[].commit.message | split("\n")[0]], files: [.files[] | {filename, status, changes}]}' > "$RUN/c-compare.json"
W3-Q5  for td in orders-reconcile:6 orders-reconcile:7; do TZ=UTC aws ecs describe-task-definition --profile prod-read --region us-east-1 --task-definition "$td" --query 'taskDefinition.{revision: revision, registeredAt: registeredAt, cpu: cpu, memory: memory, containers: containerDefinitions[].{name: name, image: image, env: environment[].name, secrets: secrets[].name}}' --output json; done
```

| Query ID | Command | World file | Key facts |
|---|---|---|---|
| W3-Q1 | `aws cloudtrail lookup-events EventName=RunTask` 14 d | `cloudtrail-01.json` (rows matching the lookup) | 15 RunTask on `orders-reconcile:7`: 02:00:02Z on 13 nights, 02:01:02 on 10-16, 02:05:02 on 10-14. First 5xx minute (3 or more) follows by 1 minute on 12 nights and 2 minutes on 3 nights (15 of 15); the onset moved with the fire time on 10-14 (02:06) and 10-16 (02:02). |
| W3-Q2 | `aws ecs list-tasks --family orders-reconcile --desired-status STOPPED`, `describe-tasks` | `ecs-05.json`, `ecs-06.json` | One stopped task: created 02:00:02.774, started 02:00:09.531, stopping 02:19:52.006, stopped 02:20:14.448, `EssentialContainerExited`, exit code 0, startedBy `events-rule/orders-reconcile-nightly`. |
| W3-Q3 | Logs Insights `/ecs/orders-reconcile` raw lines | `logs-05.json` (queryId `f0e1d2c3-b4a5-4968-8776-655443322110`), `logs-15.json` | In-window rows: 02:00:11.902 start, mode `SELECT ... FOR UPDATE`; 02:00:12.448 "locking orders rows created 2026-10-20 (estimated 1,184,000 rows)"; 02:09:37.215 progress 600000/1184212; 02:19:48.630 committed 1184212 rows; 02:19:51.877 done in 1179.9 s. 10-19 and 10-20 rows outside the window discarded. |
| W3-Q4 | `gh api …/compare/2026.10.14-2...2026.10.21-1` | `_default.txt` | `{}`: nothing returned; gap. |
| W3-Q5 | `aws ecs describe-task-definition orders-reconcile:6`, `:7` | `ecs-16.json`, `ecs-13.json` | Rev 6 image tag `2026.08.19-1` registered 2026-08-19, INACTIVE. Rev 7 image tag `2026.09.30-1` registered 2026-09-30 10:02:17Z. Env names identical (`DB_HOST`, `RECON_BATCH_SIZE`, `RECON_LOCK_MODE`); values not recorded. |

Untrusted text: none seen in any log line, release note or task output. No suspected prompt injection to flag.

Verdicts written to the ledger: H1 Likely (merged with H4), H1b Ruled out (W2-Q1), H2 Ruled out (W1-Q8, W2-Q3, W2-Q5), H5 Ruled out (W1-Q1, W1-Q2), H3 and H6 open at `Assumed`. Old-against-new quoted per revision: rev 42: 1/1 mornings, 438 target 5xx in the 02:00 hour; rev 41: 6/6 mornings (133, 398, 69, 104, 412, 96); the revision before 41: 8/8 mornings (88, 421, 61, 117, 386, 74, 52, 455).

## Phase 5: conclude

Fast mode, three waves used. No `from-history:` entries. Fixes written as prose only. The report (Fast sections: TL;DR, Impact, Causal chain, Gaps, To confirm, Follow-ups, Cost) is saved separately as `report.md`.

### Message 7 (verbatim, TL;DR printed inline)

```text
TL;DR (full report path: runs/orders-api-prod-20261021-0240/report.md)
Cause: the nightly reconcile job (EventBridge orders-reconcile-nightly, 02:00 UTC = 11:00 JST) holds row locks on about 1.18M order rows for about 20 minutes (SELECT ... FOR UPDATE), and orders-api writes (POST /orders, PATCH /orders/{id}) wait out the database lock limit (about 50 s) and return 500. Not your release. Label: Likely.
Weakest link: that the API's lock waits are waits on the job's locks. No database-side lock view was readable, and the log sample is 5 lines against 339 counted 5xx in the same minutes. Everything else in the chain is Confirmed on its own query. This caps the cause at Likely.
Impact: 439 target 5xx between 02:01 and 02:19 UTC (11:01-11:19 JST), peak 55/min at 02:04; over now (alarm OK since 02:12). The same episode ran on all 15 mornings from 10-07 to 10-21; the alarm paged 6 times in the 14 days of history. Failing share of requests: unknown.
Severity (suggested): SEV2, because both core flows are among the failing routes every morning; SEV1 if more than 5% of requests failed. You decide.
Recommended action: have the reconcile job's owners stop it from holding long row locks on live order data (smaller committed batches, a non-locking read, or a quiet hour), and treat the next 02:00 UTC run as a repeat until that is done. Changes go through pre-flight and a separate session.
Open: lock holder not seen from the database side; failing share unknown; one ECONNRESET to payments unexplained; why every 2-3 days the episode is about 4x larger.
open items need your input
Cost: 7 metered queries, about 0.48 GB of logs scanned, 22 metric requests.
```

## Phase 6: record

### Message 8 (verbatim, proposed diff; nothing written until the operator replies)

```text
Proposed record for runs/orders-api-prod-20261021-0240 (nothing is written until you reply; accept, edit or skip each item).

1. NEW incidents/2026-10-21-orders-api.md
---
id: 2026-10-21-orders-api-prod-reconcile-lock-waits
date: 2026-10-21
service: orders-api
env: prod
siblings: [all]
window_utc: 2026-10-21T02:01:00Z/2026-10-21T02:19:59Z
symptoms: [errors-5xx, timeouts]
cause_category: schedule
cause: nightly orders-reconcile job (02:00 UTC) holds row locks for about 20 minutes and orders-api writes time out on lock waits
deps: [orders-reconcile, orders-db]
label: Likely
mode: fast
time_to_cause_min: 5
run: runs/orders-api-prod-20261021-0240
---
Body: what happened; causal chain (trigger Confirmed, mechanism Confirmed per leg, lock-holder link Likely); what found it (per-night RunTask times against per-minute 5xx onsets, and the job's own log); what did not help (the release, the alarm threshold, the weekly sitemap rule); follow-ups raised.

2. NEW lessons.md (4 lines, from the ledger's Lesson candidates only)
- type: process | service: any | source: cloudwatch | statement: get-metric-data replies here carry one entry labelled HTTPCode_Target_5XX_Count with Id m1, not the Ids sent; check the returned Ids before reading a missing series as zero | run: orders-api-prod-20261021-0240 | query_id: W1-Q5 | re-verify: yes
- type: identifier | service: orders-api | source: cw-logs | statement: log group /ecs/orders-api holds JSON lines with level, status, route, error_code, msg, duration_ms and ecs_task_revision (the ECS task definition revision), usable for a per-revision split | run: orders-api-prod-20261021-0240 | query_id: W2-Q7 | re-verify: no
- type: process | service: orders-api | source: cw-logs | statement: lines with status 5xx in /ecs/orders-api are a thin sample of the ALB target 5xx count (5 lines against 339 in 01:51-02:11 UTC); size an incident from the ALB metric, not from log lines | run: orders-api-prod-20261021-0240 | query_id: W2-Q7 | re-verify: yes
- type: failure-mode | service: orders-api | source: cw-logs | statement: daily 02:00 UTC orders-reconcile-nightly runs SELECT ... FOR UPDATE on about 1.18M orders rows for about 19.7 min; POST /orders and PATCH /orders/{id} fail after about 50 s with ER_LOCK_WAIT_TIMEOUT, onset 1-2 min after RunTask | run: orders-api-prod-20261021-0240 | query_id: W3-Q3 | re-verify: no

3. NEW profiles/orders-api-prod.md = this run's profile.md: identifiers verified 2026-10-21 (ECS cluster/service, ALB and target group, log groups /ecs/orders-api and /ecs/orders-reconcile, alarm orders-api-5xx-high), image tag equals release tag, periodic job orders-reconcile-nightly (02:00 UTC, about 19-20 min), payments as a downstream; unverified: Aurora orders-db, target group lookup by elbv2, default branch. Stale identifiers: none.

Candidate for the skill itself (not for this repo, to be proposed later in a normal session): when a scheduled job's start time slips on some nights, check that the 5xx onset moves with it (EventName=RunTask lookups in CloudTrail give the fire times); this was the strongest timing check in this run.
```

No reply from the operator, so per Phase 6 nothing was written for items 1–3 (no `incidents/`, `lessons.md` or `profiles/` files exist in `out/`).

## Files written (all under `out/`)

- `runs/orders-api-prod-20261021-0240/profile.md` (the run's working profile)
- `runs/orders-api-prod-20261021-0240/ledger.md` (working record, updated after every wave and before results were used)
- `run-log.md` (this file)

`report.md`: report saved separately. Not written: `raw/` pulls (simulated; query results are summarised in the ledger rows), `environment.md` (no copy was needed), `incidents/`, `lessons.md`, `profiles/` (awaiting the operator's reply).

## World files opened (every one was mapped by a command above)

`INDEX.md`, `_empty.txt`, `ls-01.txt`, `environment.md`, `sts-01.json`, `iam-01.json`, `iam-02.json`, `logs-01.json`, `cw-01.json`, `ecs-11.json`, `ecs-10.json`, `cw-05.json`, `_default.txt`, `ecs-09.json`, `ecs-01.json`, `ecs-04.json`, `ecs-07.json`, `ecs-08.json`, `cw-02.json`, `cw-04.json`, `cw-03.json`, `events-01.json`, `scheduler-01.json`, `ecs-02.json`, `ecs-03.json`, `gh-02.txt`, `gh-01.txt`, `events-02.json`, `events-03.json`, `events-06.json`, `events-04.json`, `cloudtrail-01.json`, `logs-04.json`, `logs-14.json`, `ecs-05.json`, `ecs-06.json`, `logs-05.json`, `logs-15.json`, `ecs-16.json`, `ecs-13.json`. Never opened: `events-05.json`, `events-07.json`, `ecs-12.json`, `ecs-14.json`, `ecs-15.json`, `cw-06.json`, `logs-02.json`, `logs-03.json`, `logs-06.json`, `logs-12.json`, `logs-13.json`, `logs-16.json`, `logs-17.json`, `logs-18.json`, `logs-19.json`.

## Process notes

- The two world-file quirks noted as lesson candidates or gaps: the `get-metric-data` reply carried only the 5xx series (Id `m1`); the IAM simulation reply listed three unrequested actions and omitted three requested ones.
- Two corrections to my own shown messages are listed under message 6. They are repeated here because message 4's severity (SEV3, provisional) was revised to SEV2 in the ledger after wave 2: the revision is shown to the operator in message 7.
- Stopped orders-api tasks were gone by ~02:42 (about an hour after the 01:25–01:29 stops); the nightly job's stopped task (stopped 02:20) was still listable at ~02:48.
