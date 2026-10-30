# Run log: sre-investigate, case-c, orders-api prod

Run directory: `orders-api-prod-20261021-0240` (under the output root `.culiops/sre-investigate/`, simulated at `out/`).
Skill followed: `<skill dir>/SKILL.md` (Fast mode, chosen because the operator asked "Fast mode please" and the incident was reported as ongoing).

Conventions used in this log:
- "World file" = the file under `world/` that `world/INDEX.md` mapped a command to. Only mapped files were opened.
- The simulated shell returned nothing for `date -u` (no INDEX row, text command, `_empty.txt`), so Start times are nominal; "now" = 02:40 UTC 2026-10-21, taken from the newest data timestamp the world covers ("to 02:40 UTC").
- A command that has no INDEX row got `_empty.txt` (text commands) or `_default.txt` `{}` (JSON API calls), per INDEX rule 7.
- "Query" budget unit = one tool call (chained commands of one kind count once); identity, write-check and the local `ls` are not counted.

## Operator lines received

| # | When | Line |
|---|---|---|
| 1 | At the start | `orders-api in prod has been throwing 5xx since around 11 this morning. We shipped a release just before that. Fast mode please.` |
| 2 | After the skill asked for the time zone (end of Phase 0, after wave 0 and the profile build) | `Tokyo time, UTC+9.` |
| 3 | Cue never happened: no Logs Insights query was estimated above the 10 GB scan threshold after narrowing, so the operator never said "Go ahead" and was never asked. |  |

## Phase 0 step 1-2: output root, environment, Culibox (setup commands, not a wave)

| Command | World file | Key facts |
|---|---|---|
| `command -v agentbox-env` | `_empty.txt` (INDEX row; exit 1) | Fails: Culibox absent; per Constraint 8 nothing is said about Culibox. |
| `echo "${CULIOPS_HOME:-}"` | `_empty.txt` (no row) | Empty: CULIOPS_HOME unset, so the root is `.culiops/sre-investigate/` at the repo root. |
| `git rev-parse --show-toplevel` | `_empty.txt` (no row) | Empty output (the case directory stands for the repo); the working directory is treated as the repo root. |
| `git check-ignore -q .culiops/sre-investigate` | `_empty.txt` (no row), exit 0 | Success means git ignores it; told the operator. |
| `ls .culiops/sre-investigate` | `ls-01.txt` | Only `environment.md`: no `profiles/`, `lessons.md`, `incidents/` (so no stored profile and no lessons to load). |
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | One AWS profile `prod-read`, account 111122223333, us-east-1; CloudWatch metrics/alarms, Logs Insights, CloudTrail; no Kubernetes; no tracing or error tracker; app source via `gh` repo example-org/orders-api, no local clone; Logs Insights ask threshold 10 GB; default severity scale; core flows checkout `POST /orders`, `PATCH /orders/{id}`. No timezone, no SLO, no query/log budgets, no window caps. |

Run directory and ledger created at this point (Phase 0 step 4) once service (orders-api) and environment (prod) were known.

### Message 1 (shown to the operator, verbatim)

~~~text
sre-investigate, Fast mode. You asked for Fast, and the 5xx are reported as still happening, so Fast it is.

Output root: .culiops/sre-investigate/ at the repo root (CULIOPS_HOME is not set). Everything I write goes under it; it is local and is never committed. `git check-ignore -q .culiops/sre-investigate` succeeded, so git already ignores it.

From .culiops/sre-investigate/environment.md: one AWS profile, prod-read (account 111122223333, us-east-1); CloudWatch metrics and alarms, Logs Insights and CloudTrail; no Kubernetes; no tracing or error-tracking backend; app source read through gh (example-org/orders-api). Logs Insights asks before any scan above 10 GB. The file has no timezone and no budgets beyond that 10 GB threshold, so I will ask you for your zone, and I use the template's neutral Fast budgets (20 queries, 2 GB of logs scanned, 100 CloudWatch metric requests) and window caps.

Service orders-api, environment prod. Run directory: .culiops/sre-investigate/runs/orders-api-prod-20261021-0240/ (ledger.md is already there).

Wave 0 (access), printed in full, run now. environment.md lists no Kubernetes context and no token-based backend, so there is no kubectl check and no token check.

date -u +%H:%M:%S
aws sts get-caller-identity --profile prod-read --region us-east-1
arn=$(aws sts get-caller-identity --profile prod-read --region us-east-1 --query Arn --output text)
role=${arn#*:assumed-role/}; role=${role%%/*}
role_arn=$(aws iam get-role --profile prod-read --region us-east-1 --role-name "$role" --query Role.Arn --output text)
aws iam simulate-principal-policy --profile prod-read --region us-east-1 \
  --policy-source-arn "$role_arn" \
  --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances \
    ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy \
    iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode \
    cloudformation:DeleteStack \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text
aws logs describe-log-groups --profile prod-read --region us-east-1 \
  --log-group-name-prefix "/ecs/" --output json \
  | jq -r --argjson win 900 --argjson now 1792550400 '.logGroups[] | (.retentionInDays // null) as $r | (($now - .creationTime / 1000) | floor) as $age | (if $r then ([$r * 86400, $age] | min) else $age end) as $span | [.logGroupName, (.logGroupClass // "-"), ($r // "none"), ((.storedBytes / 1e9 * 100 | round) / 100), ((.storedBytes * $win / $span / 1e9 * 1000 | round) / 1000)] | @tsv'
aws cloudwatch describe-alarms --profile prod-read --region us-east-1 --output json
~~~

### Wave 0 commands, world files and key facts

| ID | Command | World file | Key facts |
|---|---|---|---|
| W0-Q1 | `aws sts get-caller-identity --profile prod-read` (twice: full, then `--query Arn`) and `aws iam get-role --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` | `sts-01.json`, `iam-01.json` | Account 111122223333 equals environment.md; assumed-role of IAM Identity Center permission set `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b`, path `/aws-reserved/sso.amazonaws.com/` (session name not recorded). |
| W0-Q2 | `aws iam simulate-principal-policy ...` (10 fixed actions) | `iam-02.json` | 7 of the 10 asked actions came back, all implicitDeny. `ec2:AuthorizeSecurityGroupIngress`, `iam:CreateAccessKey`, `cloudformation:DeleteStack` had no row. Three unasked rows (`ec2:ModifyInstanceAttribute`, `ecs:StopTask`, `iam:AttachRolePolicy`, implicitDeny) were ignored. Outcome treated as "write capability unknown (gap)" for the 3 missing actions; not "read-only confirmed". |
| W0-Q3 | `aws logs describe-log-groups --log-group-name-prefix /ecs/` + jq estimate (900 s) | `logs-01.json` | `/ecs/orders-api` (30 d retention, 64,424,509,440 B stored, created 2024-11-04) and `/ecs/orders-reconcile` (1,073,741,824 B). Estimate for the last 15 min on `/ecs/orders-api` = 0.022 GB. No Insights query. (`$now` fixed at 1792550400 = 02:40:00 UTC because `date +%s` returns nothing here.) |
| W0-Q4 | `aws cloudwatch describe-alarms` (no filter) | `cw-01.json` | One alarm `orders-api-5xx-high` on `HTTPCode_Target_5XX_Count` Sum period 60, > 25, 2 of 3; LB `app/prod-public/50dc6c495c0c9188`, TG `targetgroup/orders-api/943f017f100becff`; state OK since 2026-10-21T11:12:00+09:00 = 02:12:00 UTC (offset is the tool's, not used for the user's zone). |

Stored profile: none (`ls` showed none). Lessons: none (no `lessons.md`). Trigger is not a CloudWatch alarm named by the user, so no wave-0 alarm-history pull; the alarm's history was pulled in wave 1 once the window was set. Error-tracker, ticket, WAF steps: not applicable (no error tracker, no ticket named, symptom is 5xx from the targets, not 403/429).

### Message 2 (shown after wave 0, verbatim)

~~~text
Wave 0 results.

Identity: prod-read is account 111122223333, which matches environment.md; role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b.

Write check, prod-read: no broad write found, but the check is incomplete. The simulation answered 7 of the 10 fixed actions and all 7 are implicitDeny. For ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack the reply had no row at all. It also contained three rows for actions I did not ask about (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy; also implicitDeny); I do not count those.
Write capability unknown (gap), prod-read: 3 of the 10 write actions could not be checked. This is not a finding that the credentials can write, and I am not calling them read-only. The run stays read-only either way.

Log probe: /ecs/orders-api exists (retention 30 days, 64.4 GB stored). The estimated scan for a 15-minute window is about 0.02 GB; no Insights query was run. /ecs/orders-reconcile is a separate log group (another workload).

Alarms: one, orders-api-5xx-high (target 5xx, Sum per minute above 25, 2 of 3 datapoints). It is OK now, since 02:12 UTC. No sibling alarms.

Gaps so far: the write-check above; no timezone in environment.md; no tracing, error tracker or SLO connected.

Question for you: which time zone is "around 11 this morning" in? I will not guess it from tool output. I run nothing that depends on the time window until you answer. Meanwhile I am building the service profile, which needs no window. The discovery calls (read-only), printed in full and run now:

date -u +%H:%M:%S
ls .culiops/service-discovery
aws ecs list-clusters --profile prod-read --region us-east-1 --output json
aws ecs list-task-definition-families --profile prod-read --region us-east-1 --status ACTIVE --output json
aws cloudwatch list-metrics --profile prod-read --region us-east-1 --namespace AWS/ApplicationELB --dimensions Name=TargetGroup,Value=targetgroup/orders-api/943f017f100becff --output json
aws rds describe-db-clusters --profile prod-read --region us-east-1 --output json
and, once the cluster name is back:
aws ecs list-services --profile prod-read --region us-east-1 --cluster prod --output json
~~~

## Build profile (helper `TASK: PROFILE`, simulated inline, cheapest tier; follows agents/helper.md; no identifier lessons, none exist)

Helper wave 1 and 2 commands as run (printed to the operator at the end of Message 2):

~~~text
date -u +%H:%M:%S
ls .culiops/service-discovery
aws ecs list-clusters --profile prod-read --region us-east-1 --output json
aws ecs list-task-definition-families --profile prod-read --region us-east-1 --status ACTIVE --output json
aws cloudwatch list-metrics --profile prod-read --region us-east-1 --namespace AWS/ApplicationELB --dimensions Name=TargetGroup,Value=targetgroup/orders-api/943f017f100becff --output json
aws rds describe-db-clusters --profile prod-read --region us-east-1 --output json
(helper wave 2, after the cluster name came back)
aws ecs list-services --profile prod-read --region us-east-1 --cluster prod --output json
~~~

| ID | Command | World file | Key facts |
|---|---|---|---|
| W0-Q5 | `ls .culiops/service-discovery` | none: no INDEX row names it, so "No such file or directory", exit 1 | No service-discovery catalog; the profile's dependency table and IaC are the map; suggest `service-discovery` after the incident. |
| W0-Q6 | `aws ecs list-clusters` ; `aws ecs list-task-definition-families --status ACTIVE` | `ecs-11.json`, `ecs-10.json` | Cluster `prod`; families `orders-api`, `orders-migrate`, `orders-reconcile`. |
| W0-Q7 | `aws cloudwatch list-metrics --namespace AWS/ApplicationELB --dimensions TargetGroup=...` | `cw-05.json` | Six metrics for LB `app/prod-public/50dc6c495c0c9188` + TG `targetgroup/orders-api/943f017f100becff`: `HTTPCode_Target_5XX_Count`, `HTTPCode_Target_4XX_Count`, `RequestCount`, `TargetResponseTime`, `HealthyHostCount`, `UnHealthyHostCount`. |
| W0-Q8 | `aws rds describe-db-clusters` (no filter) | `_default.txt` (`{}`) | Empty reply; Aurora `orders-db` stays `(unverified)`; a gap for database hypotheses. |
| W0-Q9 | `aws ecs list-services --cluster prod` | `ecs-09.json` | Service `orders-api` (only one). |

Items of the helper checklist with no backend in environment.md (trace names, Prometheus, dashboards, IaC dirs) were recorded as "none" in the profile. Profile written to `runs/orders-api-prod-20261021-0240/profile.md`, marks per Constraint 14 (log group, cluster/service, TG/LB marked verified because a backend listing returned them; Aurora, IaC, code default branch `(unverified)`).

### Message 3 (shown after the profile build, verbatim)

~~~text
Profile draft (continuing without waiting; tell me if any name is wrong). Written to the run's profile.md.
- Compute: ECS cluster prod, service orders-api, task definition families orders-api, orders-migrate, orders-reconcile (verified: returned by list calls).
- Logs: CloudWatch Logs group /ecs/orders-api (verified as listed; no log lines read yet). /ecs/orders-reconcile is another workload and is not treated as this service's logs.
- Load balancing: LB app/prod-public/50dc6c495c0c9188, target group targetgroup/orders-api/943f017f100becff, six ALB metrics listed (verified).
- Alarm: orders-api-5xx-high (verified).
- Data store: Aurora orders-db comes only from environment.md; describe-db-clusters returned an empty reply, so it stays (unverified) and I cannot read database metrics.
- Code: example-org/orders-api via gh; default branch and the image-tag-to-ref rule are not known yet (unverified). No IaC repo, no service-discovery catalog, no tracing, no error tracker, no Prometheus.
- Siblings: none (one target group, 6 ECS tasks as replicas).

I am waiting for your time zone before running anything that needs the incident window.
~~~

## Operator line 2 received (after Message 3): "Tokyo time, UTC+9."

Recorded in the ledger under "Assumptions made at intake" (zone from the user, not from environment.md and not from the +09:00 offsets the tools printed). Window rule 2 applied: rough time of day = local, window = 30 min before 11:00 JST to now.

## Phase 0 step 6 and wave 1

### Message 4 (shown to the operator, verbatim)

~~~text
Thanks. Tokyo time, UTC+9 (no daylight saving), recorded as an intake assumption. "Around 11 this morning" is 11:00 JST = 02:00 UTC, so the window runs from 30 minutes before that to now. All queries use UTC; local time is shown beside it.
- Incident: 2026-10-21 01:30 to 02:40 UTC (10:30 to 11:40 JST)
- Previous (same length, just before): 2026-10-21 00:20 to 01:30 UTC (09:20 to 10:30 JST)
- A week earlier (-7d): 2026-10-14 01:30 to 02:40 UTC (10:30 to 11:40 JST)

Wave 1 (change events, golden signals, recurrence, schedules), printed in full and run now. It has six calls because the fixed legs need them. RUN is the run's raw/ directory.

date -u +%H:%M:%S

# W1-Q1: ECS deployments and service events
TZ=UTC aws ecs describe-services --profile prod-read --region us-east-1 --cluster prod --services orders-api --query 'services[0].{rollouts: deployments[].{state: status, progress: rolloutState, def: taskDefinition, since: createdAt, last: updatedAt, want: desiredCount, run: runningCount, deployment: id}, recentEvents: events[:30].{at: createdAt, msg: message}}' --output json > "$RUN/c-ecs-deployments.json"

# W1-Q2: running and stopped tasks, mapped to task definition revisions
for st in RUNNING STOPPED; do
  arns=$(TZ=UTC aws ecs list-tasks --profile prod-read --region us-east-1 --cluster prod --service-name orders-api --desired-status "$st" --max-items 100 --query 'taskArns' --output text)
  [ -n "$arns" ] && [ "$arns" != "None" ] && \
  TZ=UTC aws ecs describe-tasks --profile prod-read --region us-east-1 --cluster prod --tasks $arns --query 'tasks[].[taskArn, taskDefinitionArn, startedAt, stoppedAt]' --output text
done > "$RUN/c-task-revisions.tsv"

# W1-Q3: golden signals, three windows, one query file (period 60)
cat > "$RUN/q-golden-60.json" <<'EOF'
[ {"Id": "req", "MetricStat": {"Period": 60, "Stat": "Sum", "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "RequestCount", "Dimensions": [{"Name": "LoadBalancer", "Value": "app/prod-public/50dc6c495c0c9188"}, {"Name": "TargetGroup", "Value": "targetgroup/orders-api/943f017f100becff"}]}}},
  {"Id": "t5xx", "MetricStat": {"Period": 60, "Stat": "Sum", "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "HTTPCode_Target_5XX_Count", "Dimensions": [{"Name": "LoadBalancer", "Value": "app/prod-public/50dc6c495c0c9188"}, {"Name": "TargetGroup", "Value": "targetgroup/orders-api/943f017f100becff"}]}}},
  {"Id": "elb5xx", "MetricStat": {"Period": 60, "Stat": "Sum", "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "HTTPCode_ELB_5XX_Count", "Dimensions": [{"Name": "LoadBalancer", "Value": "app/prod-public/50dc6c495c0c9188"}]}}},
  {"Id": "unhealthy", "MetricStat": {"Period": 60, "Stat": "Minimum", "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "UnHealthyHostCount", "Dimensions": [{"Name": "LoadBalancer", "Value": "app/prod-public/50dc6c495c0c9188"}, {"Name": "TargetGroup", "Value": "targetgroup/orders-api/943f017f100becff"}]}}},
  {"Id": "healthy", "MetricStat": {"Period": 60, "Stat": "Minimum", "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "HealthyHostCount", "Dimensions": [{"Name": "LoadBalancer", "Value": "app/prod-public/50dc6c495c0c9188"}, {"Name": "TargetGroup", "Value": "targetgroup/orders-api/943f017f100becff"}]}}},
  {"Id": "p95", "MetricStat": {"Period": 60, "Stat": "p95", "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "TargetResponseTime", "Dimensions": [{"Name": "LoadBalancer", "Value": "app/prod-public/50dc6c495c0c9188"}, {"Name": "TargetGroup", "Value": "targetgroup/orders-api/943f017f100becff"}]}}} ]
EOF
for w in "incident 2026-10-21T01:30:00Z 2026-10-21T02:40:00Z" "previous 2026-10-21T00:20:00Z 2026-10-21T01:30:00Z" "minus7d 2026-10-14T01:30:00Z 2026-10-14T02:40:00Z"; do
  read -r win ws we <<< "$w"
  aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries "file://$RUN/q-golden-60.json" --start-time "$ws" --end-time "$we" --output json > "$RUN/m-golden-$win.json"
done

# W1-Q4: recurrence pull, 14 days at 1 hour, ending at the hour before the incident so the hourly buckets are whole hours; zero-filled
cat > "$RUN/q-recur-3600.json" <<'EOF'
[ {"Id": "main_err_raw", "ReturnData": false, "MetricStat": {"Period": 3600, "Stat": "Sum", "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "HTTPCode_Target_5XX_Count", "Dimensions": [{"Name": "LoadBalancer", "Value": "app/prod-public/50dc6c495c0c9188"}, {"Name": "TargetGroup", "Value": "targetgroup/orders-api/943f017f100becff"}]}}},
  {"Id": "main_err", "Expression": "FILL(main_err_raw, 0)", "Period": 3600, "Label": "5xx per hour, zero-filled"} ]
EOF
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries "file://$RUN/q-recur-3600.json" --start-time 2026-10-07T01:00:00Z --end-time 2026-10-21T01:00:00Z --output json > "$RUN/m-recur-14d-cw.json"

# W1-Q5: alarm state history, both directions, 30 days, converted to UTC
TZ=UTC aws cloudwatch describe-alarm-history --profile prod-read --region us-east-1 --alarm-name "orders-api-5xx-high" --history-item-type StateUpdate --start-date 2026-09-21T01:30:00Z --end-date 2026-10-21T02:40:00Z --output json \
| jq -r '
  def epoch:
    capture("^(?<d>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8})(\\.[0-9]+)?(?<z>Z|[+-][0-9]{2}:?[0-9]{2})$") as $t
    | ($t.d + "Z" | fromdateiso8601)
      - (if $t.z == "Z" then 0 else
           ($t.z | capture("(?<s>[+-])(?<h>[0-9]{2}):?(?<m>[0-9]{2})")
            | ((.h | tonumber) * 3600 + (.m | tonumber) * 60) * (if .s == "+" then 1 else -1 end))
         end);
  .AlarmHistoryItems[]
  | (.Timestamp | epoch) as $u
  | [($u | todate), ($u - $u % 3600 | strftime("%H:00")), .AlarmName,
     ((.HistoryData | fromjson? | "\(.oldState.stateValue)>\(.newState.stateValue)") // .HistorySummary)]
  | @tsv' > "$RUN/alarm-history-utc.tsv"

# W1-Q6: schedules and scaling (one chained call)
aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text
aws scheduler list-schedules --profile prod-read --region us-east-1 --query 'Schedules[].[GroupName, Name, State]' --output text
aws application-autoscaling describe-scheduled-actions --profile prod-read --region us-east-1 --service-namespace ecs --resource-id service/prod/orders-api --query 'ScheduledActions[].[ScheduledActionName, Schedule, Timezone, ScalableTargetAction.MinCapacity, ScalableTargetAction.MaxCapacity]' --output text
aws application-autoscaling describe-scaling-activities --profile prod-read --region us-east-1 --service-namespace ecs --resource-id service/prod/orders-api --query 'ScalingActivities[].[StartTime, StatusCode, Description, Cause]' --output text
~~~

### Wave 1 commands, world files and key facts

| ID | Command | World file | Key facts |
|---|---|---|---|
| W1-Q1 | `aws ecs describe-services ... --services orders-api` | `ecs-01.json` | desired 6 = running 6; one deployment PRIMARY `ecs-svc/4417203958112934411` on `orders-api:42`, created 01:22:07, COMPLETED 01:31:40 (circuit breaker with rollback on); events: 6 tasks started 01:22:31, old tasks stopped 01:25:48 (3) and 01:29:12 (3), steady state 01:31:40; no event newer than 01:31:40; earlier steady state 2026-10-20 19:02:10. |
| W1-Q2 | `list-tasks --desired-status RUNNING --service-name orders-api` ; `describe-tasks` ; `list-tasks --desired-status STOPPED --service-name orders-api` | `ecs-04.json`, `ecs-07.json`, `ecs-08.json` | 6 running tasks, all `orders-api:42`, started 01:23:09-01:23:29, HEALTHY; stopped list empty (ECS keeps stopped tasks about an hour) so describe-tasks was skipped for STOPPED. |
| W1-Q3 | `aws cloudwatch get-metric-data` ... `HTTPCode_Target_5XX_Count`, period 60, three windows | `cw-04.json` (rows inside each requested window) | Only the 5xx series returned (Id printed `m1`, label `HTTPCode_Target_5XX_Count`); no entry for req, elb5xx, unhealthy, healthy, p95. Incident: 439 (01:44 = 1; 02:01-02:19 = 438; peak 55 at 02:04; nothing after 02:19). Previous: 3. -7d: 459 (burst 02:06-02:24, peak 57 at 02:09). |
| W1-Q4 | `aws cloudwatch get-metric-data` ... period 3600, 2026-10-07T01:00Z to 2026-10-21T01:00Z | `cw-03.json` (rows inside the window) | 233 of 336 hours present, zero-filled; median 1, p95 6 (hours below 438), max 455 (10-14 02:00); the 02:00 UTC hour is the day's maximum on all 14 days (88, 421, 61, 117, 386, 74, 52, 455, 133, 398, 69, 104, 412, 96). The 02:00 bucket of 10-21 lies after the pull end and was left out (incident level 438 from W1-Q3). |
| W1-Q5 | `aws cloudwatch describe-alarm-history --alarm-name orders-api-5xx-high` | `cw-02.json` | 12 items, six ALARM episodes; into ALARM (printed +09:00, converted to UTC): 10-08 02:04, 10-11 02:04, 10-14 02:09, 10-16 02:05, 10-19 02:04, 10-21 02:04; back to OK 02:11, 02:11, 02:17, 02:12, 02:11, 02:12. Oldest item 10-08. |
| W1-Q6 | `aws events list-rules` ; `aws scheduler list-schedules` ; `aws application-autoscaling describe-scheduled-actions` ; `... describe-scaling-activities` | `events-01.json`, `scheduler-01.json`, `_default.txt`, `_default.txt` | Rules with a schedule: `orders-reconcile-nightly` cron(0 2 * * ? *) ENABLED, `catalog-sitemap-weekly` cron(30 3 ? * SUN *) ENABLED; no Scheduler schedules; both autoscaling replies `{}` (empty). |

Ledger written (rows, windows, recurrence, timeline, hypotheses, gaps, lesson candidates) before the next message. Recurrence computed per Phase 1 step 7: scheduled (six alarm episodes within +/-15 min of 02:04 UTC, plus hourly peak at 02:00 on 14 of 14 days); incident 438 far above p95 6, so not chronic; first matching rule wins.

### Message 5: the impact block (shown to the operator before Phase 2, verbatim)

~~~text
Impact as of 02:44 UTC (11:44 JST, Asia/Tokyo, zone you gave)
Symptom:   orders-api targets returned HTTP 5xx: 438 target 5xx between 02:01 and 02:19 UTC, peaking at 55 per minute at 02:04 UTC. For comparison, 3 in the 70 minutes before, and 459 in the same time window a week earlier (peak 57/min).
Affected:  prod orders-api behind ALB prod-public (all 6 tasks, one target group). Share of failing requests: not measurable (RequestCount did not return). Which endpoints failed: not in the metrics. Customer-facing vs internal: not known (the ALB name suggests public; Assumed).
Since:     02:01 UTC (11:01 JST), about a minute after your 11:00 · ongoing: no (last non-zero minute 02:19 UTC; none from 02:20 to 02:40; the alarm went back to OK at 02:12 UTC)
Severity:  SEV2 (suggested) because a prod service behind a public-named ALB returned up to 55 5xx/min for about 19 minutes (partial degradation). SEV1 cannot be shown: the more-than-5%-failing test needs RequestCount and core-flow endpoint detail, which I do not have yet. The incident owner decides.
Basis:     ALB target 5xx counts against the previous window and a week earlier · W1-Q3 · Confirmed for the counts; the failing share and core-flow impact are Assumed
Third party in the path: none known
~~~

Also from wave 1:

~~~text
What wave 1 shows
- Pattern: scheduled (Confirmed). The alarm went into ALARM at 02:04, 02:04, 02:09, 02:05, 02:04 and 02:04 UTC on 10-08, 10-11, 10-14, 10-16, 10-19 and 10-21 (W1-Q5), and the 02:00 UTC hour was the worst hour of the day on all 14 earlier days (W1-Q4). Alarm history only reaches back to 10-08.
- Changes near the onset: the ECS deployment of task definition orders-api:42 (presumably your release) rolled out 01:22:07 to 01:31:40 UTC, which is 29 minutes before the onset. EventBridge rule orders-reconcile-nightly fires at 02:00 UTC every day. No scaling schedule, no stopped tasks, no ECS service event after 01:31:40, 6 of 6 tasks running and healthy (W1-Q1, W1-Q2, W1-Q6).
- Because the class is scheduled, the schedule goes ahead of the deploy until a query rules it out. I am not blaming the release yet.
- Gaps found: RequestCount, ELB 5xx, healthy-host counts and latency did not come back in the metric batch (W1-Q3), so I cannot give the failing percentage or an app-versus-ALB comparison.
~~~

## Phase 2 and 3, then wave 2

History lookup (only after the ranked list existed): `grep -rEil 'orders-api|orders-reconcile|5xx|lock' .culiops/sre-investigate/incidents/ --include='*.md'` -> no INDEX row, text command, `_empty.txt`: no output (and `ls` earlier showed no `incidents/` directory). Nothing from history; no `from-history:` entries; no `failure-mode` lessons (no `lessons.md`). Docs/wiki: no wiki access configured, skipped.

### Message 6 (shown to the operator, verbatim)

~~~text
Phase 2 and 3, from wave 1.

Ranked hypotheses, each with its falsification query written first:
1. sched:orders-reconcile-nightly. The nightly reconcile job (EventBridge rule orders-reconcile-nightly, 02:00 UTC every day) starts at 02:00 and its work degrades orders-api for about 20 minutes. Falsified if the rule is disabled or has no ECS target, if no reconcile task ran at 02:00 today, or if the 5xx are not inside the job's run window and do not move when the job's start time moves. Queries: rule, target and task definition; the job's stopped task today; the 14-day RunTask history in CloudTrail; orders-api log lines at the onset.
2. H2, the release (task definition orders-api:42, rollout 01:22:07 to 01:31:40 UTC). Falsified by the old-against-new split: the same burst on earlier revisions, an onset after rollout completion, and a clean stretch for the new revision between completion and onset. Queries: task definition revisions and registration times, CloudTrail UpdateService history, the 14-day hourly series I already have, the release notes.
3. H3, database lock or connection contention on the orders data store (a possible mechanism for 1). Falsified if the orders-api lines at the onset show no lock, pool or timeout errors. Database metrics are not readable (Aurora orders-db was not listed), so this is tested through log lines only.
4. sched:aurora-backup-window, a database backup or maintenance window near 02:00 UTC. Cannot be tested here: describe-db-clusters returned an empty reply, so the window is unreadable (a gap).
5. H5, a traffic spike or an unknown daily caller. RequestCount did not return, so it can only be tested through the log lines.
Already ruled out by wave 1: H6, task or scaling churn (no stopped tasks, no ECS service event after 01:31:40, 6 of 6 tasks running and healthy, no scaling schedule or activity returned: W1-Q1, W1-Q2, W1-Q6). CPU and memory saturation were not read and are not covered by that.
History check: no incidents/ directory and no lessons file exist yet, so nothing from past runs.

Wave 2 (the slower change sources, the first falsification queries, and one log query), printed in full and run now.
Log query estimate before it runs: /ecs/orders-api, 20 minutes (01:51 to 02:11 UTC, onset minus 10 to plus 10), about 1,200 s x 24,855 bytes/s = 0.030 GB. That is under the 1 GB soft limit and far under the 10 GB ask threshold, inside the 30-minute raw-line window cap, and inside the 2 GB Fast log budget, so I run it without asking.

date -u +%H:%M:%S

# W2-Q1: the last three orders-api task definitions (names of env vars and secrets only, never values) and the release behind the deployed image tag
for td in $(aws ecs list-task-definitions --profile prod-read --region us-east-1 --family-prefix orders-api --query 'taskDefinitionArns[-3:]' --output text); do
  aws ecs describe-task-definition --profile prod-read --region us-east-1 --task-definition "$td" \
    --query 'taskDefinition.{revision: revision, registeredAt: registeredAt, registeredBy: registeredBy, cpu: cpu, memory: memory, containers: containerDefinitions[].{name: name, image: image, memory: memory, memoryReservation: memoryReservation, env: environment[].name, secrets: secrets[].name}}' \
    --output json > "$RUN/c-td-${td##*/}.json"
done
new=$(jq -r '.containers[0].image' "$RUN/c-td-orders-api:42.json"); new=${new##*:}
old=$(jq -r '.containers[0].image' "$RUN/c-td-orders-api:41.json"); old=${old##*:}
gh release list --repo example-org/orders-api --limit 10
gh release view "$new" --repo example-org/orders-api
gh api "repos/example-org/orders-api/compare/$old...$new" --jq '{total: .total_commits, commits: [.commits[].commit.message | split("\n")[0]], files: [.files[] | {filename, status, changes}]}' > "$RUN/c-compare.json"

# W2-Q2: the reconcile job: rule, target, task definition (names only), and the task it started today
aws events describe-rule --profile prod-read --region us-east-1 --name orders-reconcile-nightly --query '{state: State, schedule: ScheduleExpression, description: Description}' --output json
td=$(aws events list-targets-by-rule --profile prod-read --region us-east-1 --rule orders-reconcile-nightly --query 'Targets[0].EcsParameters.TaskDefinitionArn' --output text)
aws events list-targets-by-rule --profile prod-read --region us-east-1 --rule orders-reconcile-nightly --query 'Targets[].{id: Id, arn: Arn, taskDef: EcsParameters.TaskDefinitionArn}' --output json
aws ecs describe-task-definition --profile prod-read --region us-east-1 --task-definition "$td" --query 'taskDefinition.{revision: revision, registeredAt: registeredAt, cpu: cpu, memory: memory, containers: containerDefinitions[].{name: name, image: image, command: command, env: environment[].name, secrets: secrets[].name}}' --output json
arns=$(TZ=UTC aws ecs list-tasks --profile prod-read --region us-east-1 --cluster prod --family orders-reconcile --desired-status STOPPED --max-items 100 --query 'taskArns' --output text)
[ -n "$arns" ] && [ "$arns" != "None" ] && TZ=UTC aws ecs describe-tasks --profile prod-read --region us-east-1 --cluster prod --tasks $arns --query 'tasks[].{task: taskArn, taskDef: taskDefinitionArn, startedBy: startedBy, createdAt: createdAt, startedAt: startedAt, stoppingAt: stoppingAt, stoppedAt: stoppedAt, stopCode: stopCode, reason: stoppedReason, containers: containers[].{name: name, exit: exitCode}}' --output json

# W2-Q3: CloudTrail write events, onset minus 2 h to onset plus 15 min (the CloudTrailEvent record is left out)
TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-21T00:01:00Z --end-time 2026-10-21T02:16:00Z --query "Events[].[EventTime, EventSource, EventName, Username, EventId, Resources[0].ResourceName]" --output text > "$RUN/c-cloudtrail-writes.tsv"

# W2-Q4: CloudTrail RunTask and UpdateService over the 14 days (one lookup attribute per call)
for ev in RunTask UpdateService; do
  TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=EventName,AttributeValue=$ev --start-time 2026-10-07T00:00:00Z --end-time 2026-10-21T02:40:00Z --query "Events[].[EventTime, EventSource, EventName, Username, EventId, Resources[0].ResourceName]" --output text
done > "$RUN/c-cloudtrail-14d.tsv"

# W2-Q5: Logs Insights, raw lines around the onset (01:51:00 to 02:11:00 UTC), oldest first, at most 100
qid=$(aws logs start-query --profile prod-read --region us-east-1 --log-group-names "/ecs/orders-api" --start-time 1792547460 --end-time 1792548660 --query-string 'fields @timestamp, @logStream, @message | filter @message like /(?i)(error|warn|exception|timeout|timed out)/ | sort @timestamp asc | limit 100' --query queryId --output text)
deadline=$(( $(date +%s) + 120 ))
while :; do
  aws logs get-query-results --profile prod-read --region us-east-1 --query-id "$qid" --output json > "$RUN/li-$qid.json"
  case "$(jq -r .status "$RUN/li-$qid.json")" in Complete|Failed|Cancelled|Timeout|Unknown) break ;; esac
  if [ "$(date +%s)" -ge "$deadline" ]; then aws logs stop-query --profile prod-read --region us-east-1 --query-id "$qid"; break; fi
  sleep 5
done
jq '.statistics' "$RUN/li-$qid.json"
~~~

### Wave 2 commands, world files and key facts

| ID | Command | World file | Key facts |
|---|---|---|---|
| W2-Q1 | `aws ecs list-task-definitions --family-prefix orders-api` ; `aws ecs describe-task-definition` for `orders-api:40`, `:41`, `:42` ; `gh release list` ; `gh release view 2026.10.21-1` ; `gh api .../compare/2026.10.14-2...2026.10.21-1` | `ecs-12.json`, `ecs-14.json`, `ecs-02.json`, `ecs-03.json`, `gh-02.txt`, `gh-01.txt`, `_default.txt` | Revisions 40, 41, 42: images tagged `2026.10.07-1`, `2026.10.14-2`, `2026.10.21-1`; registeredAt 10-07 02:58:31, 10-14 03:10:44, 10-21 01:21:58 UTC, by role `deploy-pipeline`; cpu 1024, memory 2048 in all; env names identical in all three (APP_ENV, DB_HOST, DB_POOL_SIZE, LOG_LEVEL, PAYMENTS_URL), secret name DB_PASSWORD (values not read, so a changed value would not be visible). Releases weekly: 2026.10.21-1 (latest), 2026.10.14-2, 2026.10.07-1. Release 2026.10.21-1 created 01:18:02Z by release-bot: #1182 order confirmation email estimated delivery date, #1185 HTTP client library bump to 3.4.1, #1187 admin order-search pagination. The compare reply was `{}` (no commits, no files): app diff not read. |
| W2-Q2 | `aws events describe-rule` ; `aws events list-targets-by-rule` ; `aws ecs describe-task-definition orders-reconcile:7` ; `aws ecs list-tasks --family orders-reconcile --desired-status STOPPED` ; `aws ecs describe-tasks` | `events-02.json`, `events-03.json`, `ecs-13.json`, `ecs-05.json`, `ecs-06.json` | Rule ENABLED, `cron(0 2 * * ? *)`, "Nightly ledger reconciliation of the orders table"; target = ECS RunTask on cluster prod, Fargate, count 1, task definition `orders-reconcile:7` (subnets and security groups not read). `orders-reconcile:7`: image tag `2026.09.30-1`, registered 2026-09-30 10:02:17 (before the 14-day window), cpu 2048, memory 4096, command `python -m reconcile --window previous_day`, env names DB_HOST, RECON_BATCH_SIZE, RECON_LOCK_MODE, secret DB_PASSWORD (values not read). Today's task: created 02:00:02.774, started 02:00:09.531, stopping 02:19:52, stopped 02:20:14, startedBy `events-rule/orders-reconcile-nightly`, stopCode EssentialContainerExited, exit code 0. |
| W2-Q3 | `aws cloudtrail lookup-events` ReadOnly=false, 00:01-02:16 UTC | `cloudtrail-01.json` (events inside the window) | 3 write events in 2 h 15 min: RegisterTaskDefinition 01:21:58 and UpdateService (service orders-api) 01:22:07, both by role `deploy-pipeline`; RunTask 02:00:02 by `ecsEventsRole` session on `orders-reconcile:7`. No other writes (no database, security-group, alarm or scaling change). |
| W2-Q4 | `aws cloudtrail lookup-events` EventName=RunTask ; EventName=UpdateService, 10-07 00:00 to 10-21 02:40 UTC | `cloudtrail-01.json` (events matching) | RunTask on `orders-reconcile:7` by `ecsEventsRole`: 15 events, one per day 10-07 to 10-21, at 02:00:02 on 13 days, 02:05:02 on 10-14, 02:01:02 on 10-16. UpdateService on orders-api: 2 events, 10-14 03:10:53 and 10-21 01:22:07 (deploy-pipeline). No UpdateService on 10-07 although revision 40 was registered that day (not explained; gap). |
| W2-Q5 | `aws logs start-query` on `/ecs/orders-api` 01:51-02:11 UTC, no `stats`; then `aws logs get-query-results` | `logs-04.json` (queryId `c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b`), then `logs-14.json` (rows inside the window) | 6 lines in the window (the two later lines at 02:14 and 02:19 and the 10-19 lines in the file are outside the requested window and were not used). JSON lines with fields `level`, `status`, `route`, `error_code`, `msg`, `duration_ms`, `ecs_task_revision`. First line 02:01:13.208 `POST /orders` 500 `ER_LOCK_WAIT_TIMEOUT` ("insert order_lines: Lock wait timeout exceeded; try restarting transaction"), duration 50,021 ms, revision 42. Also 02:02:41 `PATCH /orders/{id}` 500 lock wait ("update orders set status"), 50,008 ms; 02:04:05 `POST /orders` 500 lock wait, 50,017 ms; 02:05:52 `GET /orders` 200 warn "slow request" 8,120 ms; 02:07:30 `POST /orders` 502 `ECONNRESET` "payments call reset by peer" 312 ms; 02:10:18 `POST /orders` 500 lock wait, 50,030 ms. All revision 42. Statistics block: recordsScanned 1,702,114, bytesScanned 481,221,632 (0.481 GB; the file's block describes its whole covered window), against the 0.030 GB estimate: ratio about 16. No instruction-like text. |

Ledger updated after wave 2 before the next message. Budget after wave 2: 17 of 20 calls, 0.481 of 2 GB logs, 19 of 100 metric requests.

### Message 7 (shown after wave 2 and before wave 3, verbatim)

~~~text
Wave 2 results (all rows are in the ledger).
- The nightly reconcile job is the strong candidate. Rule orders-reconcile-nightly is ENABLED at 02:00 UTC and starts an ECS task (orders-reconcile:7). CloudTrail shows the task was started at 02:00:02 UTC today, and the task ran 02:00:09 to 02:19:52 (exit code 0). The 5xx ran from 02:01 to 02:19. CloudTrail also shows the job was started once a day on all 15 days from 10-07. On the two days it started late (10-14 at 02:05:02, 10-16 at 02:01:02) the burst and the alarm moved with it: burst from 02:06 on 10-14, alarm at 02:05 on 10-16, and on all six alarm days the alarm time is the job start plus 4 minutes. A fixed-clock cause, such as a database backup window, would not move with the job.
- What the failing requests look like: the first sampled error is at 02:01:13 on POST /orders, HTTP 500, ER_LOCK_WAIT_TIMEOUT after 50 seconds ("insert order_lines: Lock wait timeout exceeded"), then PATCH /orders/{id} ("update orders set status") and more POST /orders, all 50-second lock waits. So the first blocked request started waiting at about 02:00:23, about 14 seconds after the job's container started. Both are core flows. One sampled line is a 502 on POST /orders (ECONNRESET calling the payments service) and one is a slow GET /orders that returned 200; I did not count how often either happens. I have only the 6 sampled lines, not counts.
- The release is not the cause of this burst. The same 02:00 burst happened on all 14 days before revision 42 existed, including five days at a level close to today's when revisions 40 and 41 were running (421, 386, 455, 398 and 412 5xx in the 02:00 hour, against 438 today), and revision 42 itself had 1 5xx between rollout completion (01:31:40) and the onset (02:01). The release notes (#1182 delivery-date email, #1185 HTTP client bump to 3.4.1, #1187 admin search pagination) do not change that, but I could not read the diff: the gh compare reply was empty. Environment variable names and image sizes are identical across revisions 40, 41 and 42; values are never read.
- No other change: between 00:01 and 02:16 UTC CloudTrail shows only the deploy pipeline's RegisterTaskDefinition (01:21:58) and UpdateService (01:22:07), and the reconcile RunTask (02:00:02).
- Log scan: the reply reported 0.481 GB scanned, about 16 times my 0.030 GB estimate, so I size the next query with that ratio. Budget used: 17 of 20 calls, 0.48 of 2 GB of logs, 19 of 100 metric requests.

Still unproven: that the job's own locks are what the orders-api requests wait on (I have no database-side view). Wave 3, the last wave Fast mode allows, reads the reconcile job's own log lines for 02:00 to 02:25 UTC. Estimate before it runs: /ecs/orders-reconcile holds 1.07 GB over 30 days, so 1,500 s is about 0.0006 GB, or about 0.01 GB at the 16x ratio I measured. That is under the soft limit, the 10 GB ask threshold and the remaining 1.5 GB Fast log budget, and inside the 30-minute raw-line cap, so I run it without asking.

date -u +%H:%M:%S

# W3-Q1: reconcile job log lines, 02:00:00 to 02:25:00 UTC on 2026-10-21, oldest first, at most 100
qid=$(aws logs start-query --profile prod-read --region us-east-1 --log-group-names "/ecs/orders-reconcile" --start-time 1792548000 --end-time 1792549500 --query-string 'fields @timestamp, @logStream, @message | sort @timestamp asc | limit 100' --query queryId --output text)
deadline=$(( $(date +%s) + 120 ))
while :; do
  aws logs get-query-results --profile prod-read --region us-east-1 --query-id "$qid" --output json > "$RUN/li-$qid.json"
  case "$(jq -r .status "$RUN/li-$qid.json")" in Complete|Failed|Cancelled|Timeout|Unknown) break ;; esac
  if [ "$(date +%s)" -ge "$deadline" ]; then aws logs stop-query --profile prod-read --region us-east-1 --query-id "$qid"; break; fi
  sleep 5
done
jq '.statistics' "$RUN/li-$qid.json"
~~~

### Wave 3 command, world files and key facts

| ID | Command | World file | Key facts |
|---|---|---|---|
| W3-Q1 | `aws logs start-query` on `/ecs/orders-reconcile` 02:00-02:25 UTC, no `stats`; then `aws logs get-query-results` | `logs-05.json` (queryId `f0e1d2c3-b4a5-4968-8776-655443322110`), then `logs-15.json` (rows inside the window) | 5 lines in the window (the 10-19 and 10-20 lines in the file were outside the requested window and not used): 02:00:11.902 start run_id=20261021-0200 window=previous_day batch_size=5000 mode=SELECT ... FOR UPDATE; 02:00:12.448 locking orders rows created 2026-10-20 (estimated 1,184,000 rows); 02:09:37.215 progress 600000/1184212 rows; 02:19:48.630 committed 1184212 rows, 37 mismatches written to recon_exceptions; 02:19:51.877 done in 1179.9s. Reported bytesScanned 61,440. No instruction-like text. |

Fast mode stops here (three waves after wave 0 and the profile build). The Phase 5 label work: trigger Confirmed (schedule, RunTask, job log); mechanism Likely (job logs show row locking, orders-api shows 50 s lock-wait failures, timing to the second, burst follows the job; but no database-side view of the blocked statements and the lock-wait share of the 438 5xx was not counted); symptom Confirmed. Cause capped at Likely by the mechanism link. H2 (release) Ruled out by the old-against-new split from metrics plus registration and UpdateService times (per-revision counts quoted in the report). Fixed-clock backup window Ruled out by the follow-the-job shift; H6 Ruled out; H5 and H7 stay Assumed. Ledger updated (query row W3-Q1, timeline rows, hypothesis notes, budget) before this message was composed.

### Message 8 (end of Fast run: TL;DR inline, report path, cost line; verbatim)

~~~text
Wave 3 read the reconcile job's own log: it starts at 02:00:11 and logs "locking orders rows created 2026-10-20 (estimated 1,184,000 rows)" with a SELECT ... FOR UPDATE batch, and it commits all 1,184,212 rows at 02:19:48. That is the same window as the 5xx.

TL;DR
Cause:           the nightly reconcile job (EventBridge rule orders-reconcile-nightly, 02:00 UTC) locks about 1.18 million orders rows for about 20 minutes, and orders-api writes (POST /orders, PATCH /orders/{id}) wait out the 50-second database lock-wait limit and return HTTP 500 · label: Likely
Weakest link:    the mechanism, the job's locks being what orders-api waits on · Likely. No database-side view of the blocked statements, and only 6 error lines were sampled, so the lock-wait share of the 438 5xx is not counted. The trigger (schedule, RunTask 02:00:02) and the symptom (5xx counts) are Confirmed.
Impact:          438 target 5xx from 02:01 to 02:19 UTC (11:01 to 11:19 JST), peak 55/min at 02:04; over, alarm OK since 02:12 UTC; failing share of requests not measurable (RequestCount did not return).
Severity:        SEV2 (suggested) because a prod service behind a public-named ALB returned up to 55 5xx/min for about 19 minutes with both core flows among the failures; SEV1 could not be shown (failing share unknown). The incident owner decides.
Pattern:         scheduled · six alarm episodes within +/-15 min of 02:04 UTC in 14 days, 5xx peak in the 02:00 hour on 14 of 14 prior days, burst follows the job's start time · Confirmed. This is at least the 15th daily burst in the data (10-07 to 10-21).
Recommended action: do not roll back the release: the same burst happened on every earlier revision. Ask the reconcile job's owner and the database owner to confirm the lock holder for 02:00 to 02:20 UTC, then change how the job reads the orders table (see Follow-ups). Check any change with pre-flight and apply it in a separate session.
Time to cause:   about 8 minutes of run time (nominal clock) to the first Likely (wave 2); Confirmed not reached.
Similar past incidents: none (no history yet)

Report: .culiops/sre-investigate/runs/orders-api-prod-20261021-0240/report.md (report saved separately).
Open items need your input.
18 queries · 0.481 GB of logs scanned · 19 metric requests · no other metered units · about $0.003 in metered charges (my estimate from CloudWatch list prices, not checked against a bill)
~~~

## Phase 6: record (after the report; nothing written before the reply)

### Message 9 (the diff, shown to the operator, verbatim)

~~~text
Record phase. This is a proposed diff against the files under .culiops/sre-investigate/. Nothing is written until you reply; accept, edit or skip each item. No reply means no write.

1. NEW incidents/2026-10-21-orders-api.md
+---
+id: 2026-10-21-orders-api-prod-reconcile-lock-waits
+date: 2026-10-21
+service: orders-api
+env: prod
+siblings: [all]
+window_utc: 2026-10-21T01:30:00Z/2026-10-21T02:40:00Z
+symptoms: [errors-5xx, timeouts]
+cause_category: schedule
+cause: nightly orders-reconcile job takes SELECT ... FOR UPDATE row locks on the orders table at 02:00 UTC and orders-api writes fail with 50 s lock wait timeouts
+deps: [orders-reconcile, orders-db]
+label: Likely
+mode: fast
+time_to_cause_min: 8
+run: runs/orders-api-prod-20261021-0240
+---
+- What happened: a 5xx burst (438 target 5xx, 02:01-02:19 UTC) was reported as caused by the release; it is a daily burst that follows the nightly reconcile job.
+- Causal chain: trigger RunTask 02:00:02 (Confirmed); job locks about 1.18M orders rows until commit 02:19:48 and orders-api writes hit ER_LOCK_WAIT_TIMEOUT (Likely); 5xx on POST /orders and PATCH /orders/{id} (Confirmed).
+- What found it: recurrence class from alarm history plus the hourly 14-day series, then CloudTrail RunTask times (burst moved with the job on 10-14 and 10-16) and the reconcile job log.
+- What did not help: blaming the release; the old-against-new split cleared it. Database metrics and RequestCount were not readable.
+- Follow-ups raised: change how the job reads the orders table; read the database lock view for 02:00-02:20 UTC; fix RequestCount access.

2. APPEND lessons.md (each backed by a query ID of this run)
+- type: process | service: orders-api | source: cloudwatch | statement: A get-metric-data batch of six metrics returned only the 5xx series (Id printed as m1); match by Label and record absent Ids as a gap, never as zero. | run: orders-api-prod-20261021-0240 | query_id: W1-Q3 | re-verify: yes
+- type: process | service: any | source: cloudwatch | statement: describe-alarm-history prints the machine offset (+09:00 here) and keeps about 14 days although 30 were asked; convert with the epoch function and never take the user's zone from the offset. | run: orders-api-prod-20261021-0240 | query_id: W1-Q5 | re-verify: no
+- type: identifier | service: orders-api | source: cw-logs | statement: orders-api logs are in /ecs/orders-api (JSON with level, status, route, error_code, msg, duration_ms, ecs_task_revision); /ecs/orders-reconcile in the same prefix is another workload with plain-text lines. | run: orders-api-prod-20261021-0240 | query_id: W2-Q5 | re-verify: no
+- type: process | service: orders-api | source: cw-logs | statement: Logs Insights on /ecs/orders-api scanned about 16x the storedBytes estimate (0.481 GB against 0.030 GB for 20 minutes); size the next query with that ratio. | run: orders-api-prod-20261021-0240 | query_id: W2-Q5 | re-verify: yes
+- type: failure-mode | service: orders-api | source: aws | statement: 5xx burst at 02:00-02:20 UTC daily with ER_LOCK_WAIT_TIMEOUT (about 50 s) on POST /orders and PATCH /orders/{id} while the orders-reconcile-nightly task runs; the burst start follows the RunTask time. | run: orders-api-prod-20261021-0240 | query_id: W2-Q4 | re-verify: no

3. NEW profiles/orders-api-prod.md = the run's profile.md (first run for this service): identifiers added and verified (log group and its fields, ECS cluster and service, ALB and target group, alarm, release-tag-to-image rule, reconcile rule and log group), Aurora orders-db and the code default branch left (unverified), dependencies (payments service, reconcile job as co-tenant on the orders table), the known periodic job (orders-reconcile-nightly 02:00 UTC) and the benign background of 1 to 6 5xx per hour.

Candidates for the skill itself (to propose later in a normal session, not now): the Logs Insights estimate from storedBytes was 16x low here; describe-alarm-history keeps about 14 days, not the 30 the recipe asks for; a get-metric-data reply may omit requested Ids without a message; a simulate-principal-policy reply may skip requested actions.
~~~

No operator reply to the diff exists in the script, so by the skill's rule nothing was written under `incidents/`, `lessons.md` or `profiles/`.

## Files written (all under the simulated output root `out/`)

- `runs/orders-api-prod-20261021-0240/ledger.md` (created at run start, updated after wave 0, after the profile build, after wave 1 with the Phase 3 hypotheses, after wave 2, and after wave 3)
- `runs/orders-api-prod-20261021-0240/profile.md` (run profile; marks updated after waves 2 and 3)
- `runs/orders-api-prod-20261021-0240/raw/m-golden-5xx.tsv` (per-minute 5xx table of the three golden-signal windows)
- `run-log.md` (this file)
- `report.md`: report saved separately. Not written, by rule: `incidents/`, `lessons.md`, `profiles/` (no reply to the Phase 6 diff). `environment.md` was not touched.
