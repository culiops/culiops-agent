# Run log — sre-investigate (static.example.com / E3EXAMPLEDIST)

Skill base: <skill-base>/. Output root: <repo>/.culiops/sre-investigate/ (case out/ treated as repo root per dispatch).
Playbooks read before first use: metrics.md, changes.md, logs.md (CloudWatch Logs Insights section). waf.md and logs-s3.md not read (module reported off; no WAF in path, see profile).

## Operator line 1 (delivered as the opening request)
OPERATOR: Users are getting errors on images from static.example.com since about 10:10 UTC today. The distribution is E3EXAMPLEDIST. Fast mode please.

## Phase 0

### Commands (output-root resolution; simulated "now" = 2026-04-12 11:21 UTC, the end of the world's data)
1. `git rev-parse --show-toplevel` -> no INDEX row -> _empty.txt (no output, exit 0). Repo root taken from the dispatch: <repo>/.
2. `echo "${CULIOPS_HOME:+x}"` -> _empty.txt (unset) -> output root = `<repo root>/.culiops/sre-investigate/`.
3. `git check-ignore -q .culiops/sre-investigate` -> _empty.txt, exit 0 -> ignored by git.
4. `cat .culiops/sre-investigate/environment.md` -> INDEX row 1 -> environment.md. Facts: account prod 111122223333 us-east-1 profile `prod-read`; backends CloudWatch metrics/alarms, Logs Insights (/ecs/*), CloudTrail; no k8s; no tracing/error tracker; repo example-org/static-assets via gh (no clone); Logs Insights ask above 10 GB; default severity scale, core flow = asset delivery for shop.example.com pages; NO timezone line; no budgets section (neutral defaults from environment.template.md: fast 20 queries / 100 metric requests / 2 GB logs).
5. `ls .culiops/sre-investigate` -> INDEX row 2 -> ls-01.txt: only `environment.md` (no profiles/, lessons.md, incidents/ -> first run for this service, no history, no lessons).
6. `command -v agentbox-env` -> _empty.txt, exit 1 -> say nothing about Culibox (standalone).

### Message (to operator)
Message: Mode: Fast. The incident is ongoing (errors since about 10:10 UTC today) and you asked for Fast mode. Fast means at most 3 evidence waves after the access wave, no checkpoints, and a short report.
Message: Output root: <repo>/.culiops/sre-investigate/ . Everything I write goes there. It is local and is never committed (git reports the path as ignored; I will not edit .gitignore or offer a commit).
Message: Window: you gave 10:10 UTC, an explicit zone, so I use it as given. Incident window 2026-04-12 10:10 to now (11:20 UTC); the equal-length window before it is 09:00 to 10:10, and the same span seven days back is 2026-04-05 10:10 to 11:20.
Message: One question: environment.md has no `timezone:` line. Which zone should I show beside UTC in the report? It does not block the run; I am starting the access checks now.

OPERATOR (line 2, cue = skill asked for the timezone): UTC.
Key fact: local zone = UTC (given in chat; recorded under intake assumptions; local time in the report equals UTC).

### Wave 0 (access and intake) — commands printed in full, then run
Run directory created: `.culiops/sre-investigate/runs/static-example-com-prod-20260412-1121/` (RUN=`<that>/raw`). Ledger copied from templates/ledger.md.

W0 commands (all one wave):
```
date -u +%H:%M:%S                                                  -> 11:21:07 (Start column for W0 rows)
command -v agentbox-env                                            -> (INDEX row; empty, exit 1; nothing said)
aws sts get-caller-identity --profile prod-read                    -> INDEX row sts-01.json
arn=$(aws sts get-caller-identity --profile prod-read --query Arn --output text)   -> sts-01.json, Arn
role=${arn#*:assumed-role/}; role=${role%%/*}                      -> AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b
role_arn=$(aws iam get-role --profile prod-read --role-name "$role" --query Role.Arn --output text)   -> iam-01.json, Role.Arn (path /aws-reserved/sso.amazonaws.com/)
aws iam simulate-principal-policy --profile prod-read --policy-source-arn "$role_arn" --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode cloudformation:DeleteStack --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text      -> iam-02.json
aws logs describe-log-groups --profile prod-read --region us-east-1 --log-group-name-prefix /ecs/static --output json     -> no row, JSON API -> _default.txt  {}
aws cloudwatch describe-alarms --profile prod-read --region us-east-1 --query 'MetricAlarms[?Namespace==`AWS/CloudFront`].[AlarmName,StateValue]' --output text     -> INDEX row cw-02.json (no alarm for this distribution)
<skill-base>/analytics/bin/logs-status    -> INDEX row mod-01.txt
```
Facts from outputs:
- sts: Account 111122223333 (matches environment.md `prod` account; no mismatch). Role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` (session name not recorded).
- iam get-role: ARN resolved with SSO reserved path.
- simulate: 10 rows came back, all `implicitDeny`, BUT only 7 of the 10 fixed actions are in the reply. Missing: ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack. Three rows are for actions I did not ask about (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy): not counted toward the 10. Outcome = "partly checked (gap)", NOT "read-only confirmed". No `allowed` -> no boxed warning. Not the "unknown" notice either (simulation was permitted). Gap recorded.
- logs describe-log-groups prefix /ecs/static -> `{}` : no CloudWatch log group for this service (CloudFront standard logging goes to S3 per distribution config, see profile). The only log call of wave 0; no Logs Insights query, no estimate needed. Gap recorded (no CloudWatch log source).
- describe-alarms: no alarm for the distribution -> no alarm state history to pull; trigger is the operator's report. Gap/observability finding.
- logs-status line (printed once, as returned): `S3 log module: off (not configured)`
- Tokens: environment.md lists no datasource with a token_env -> nothing to check, nothing unset.
- Kubernetes: none listed -> no kube write-check.
- Stored profile: none (first run). Lessons: no lessons.md. incidents/: none.
- Ticket named in request: none. Error-tracker: none. WAF playbook trigger: report says "errors", status class unknown, distribution has no web ACL (WebACLId empty, see profile build) -> not triggered; revisit if wave 1 shows 403/429.

### Build profile — `[helper PROFILE, cheapest tier]` run inline (profile built inline note; one wave of free reads; not counted against a wave cap)
Reason inline: the dry run cannot dispatch workers; checklist run under the helper's rules (read-only, one wave, <=10 calls).
Commands:
```
aws cloudfront list-distributions --profile prod-read                                   -> INDEX cf-01.json
aws cloudfront get-distribution --profile prod-read --id E3EXAMPLEDIST                  -> INDEX cf-02.json
aws cloudfront get-monitoring-subscription --profile prod-read --distribution-id E3EXAMPLEDIST   -> INDEX cf-03.json
aws cloudwatch list-metrics --profile prod-read --region us-east-1 --namespace AWS/CloudFront --query 'Metrics[].[MetricName,Dimensions[0].Value,Dimensions[1].Value]' --output text   -> INDEX cw-01.json
aws ecs list-clusters --profile prod-read --region us-east-1 --query 'clusterArns' --output text         -> no row -> _default.txt {}
aws elbv2 describe-load-balancers --profile prod-read --region us-east-1 --query 'LoadBalancers[].[LoadBalancerName,DNSName]' --output text   -> no row -> _default.txt {}
gh api repos/example-org/static-assets --jq '.default_branch'                           -> no row -> _default.txt {}
```
Facts:
- list-distributions: exactly one distribution, E3EXAMPLEDIST, alias static.example.com, domain d3examplestatic.cloudfront.net, Status Deployed, LastModified 2026-02-18T09:41:12Z, one origin `origin-static` = origin-static.example.com (custom origin, https-only, TLSv1.2), WebACLId empty (no WAF), PriceClass_100, Enabled.
- get-distribution: OriginReadTimeout 30 s, OriginKeepaliveTimeout 5 s, ConnectionAttempts 3, ConnectionTimeout 10 s. Default cache behavior GET/HEAD, redirect-to-https, Compress true, CachePolicyId 658327ea-... (policy contents not read). CustomErrorResponses: ErrorCode 504 with ErrorCachingMinTTL 10 (no response page override). Standard logging enabled to S3 bucket example-edge-logs prefix `cf/static/`, IncludeCookies false. No cache behaviors beyond default.
- monitoring subscription: Realtime/additional metrics Enabled -> per-status error-rate metrics, OriginLatency, CacheHitRate exist.
- list-metrics (AWS/CloudFront): Requests, BytesDownloaded, 4xxErrorRate, 5xxErrorRate, TotalErrorRate, 502ErrorRate, 503ErrorRate, 504ErrorRate, OriginLatency, CacheHitRate; dimensions DistributionId=E3EXAMPLEDIST, Region=Global. Verified in the sense that the names were listed; not yet returned data (so (unverified) until a metric query returns points).
- ecs list-clusters / elbv2 describe-load-balancers: empty `{}` replies (not a list shape): origin compute not discoverable from this profile in us-east-1. Origin compute left unverified.
- gh: empty reply, default branch not returned: repo identity not verified, no code read yet.

Query IDs for wave 0: W0-Q1 sts, W0-Q2 get-role, W0-Q3 simulate, W0-Q4 describe-log-groups, W0-Q5 describe-alarms, W0-Q6 logs-status; helper rows W0-H1..H7. Rows written to ledger.md before results used.
Note on the WAF check: after the profile build, W0-H1 shows WebACLId empty, so no web ACL is in the path; the WAF playbook trigger does not apply unless wave 1 shows 403/429.

### Message (to operator, after wave 0)
Message: Write check, prod-read: partly checked (gap): no listed action is allowed, but ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack returned no usable result. This is not a finding that the credentials are read-only. (The simulator answered 10 rows, all implicit deny, but three were for actions not on my list: ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy; I did not count them.)
Message: S3 log module: off (not configured)
Message: Gaps so far: (1) no CloudWatch log group exists for this service, and CloudFront's access logs are in S3, so which URLs, status codes and clients are failing will be Assumed or left out unless a human reads those logs; (2) no CloudWatch alarm exists for the distribution, so there is no alarm history and the true detection time is unknown; (3) the origin (origin-static.example.com) is not discoverable from prod-read, so origin-side causes can be at most Likely; (4) `gh` returned nothing for example-org/static-assets, so no code or deploy read yet. Account check passed: prod-read is account 111122223333, as environment.md says.
Message: Profile built (inline, partly unverified), saved to the run directory as profile.md. It names one distribution E3EXAMPLEDIST (alias static.example.com), one origin origin-static.example.com, CloudWatch namespace AWS/CloudFront with DistributionId and Region=Global, no web ACL, origin read timeout 30 s with 3 attempts, and 504 responses cached for 10 s. Tell me if any of it is wrong; I am continuing.

## Wave 1 (golden signals in three windows + recurrence + schedules + change events). Legs: golden signals, recurrence, schedule listings, change events. Wave 1 is not trimmed. Three shell calls (the query files are written first). 

Message (commands printed in full before running):
```
# call 1 (starts with the wave clock)
date -u +%H:%M:%S                                              -> 11:23:02
RUN=<repo>/.culiops/sre-investigate/runs/static-example-com-prod-20260412-1121/raw
START_S=1775988600; END_S=1775992800; len=$((END_S - START_S))   # 2026-04-12 10:10:00Z to 11:20:00Z
# q-golden-60.json written to $RUN: 10 queries, namespace AWS/CloudFront, dimensions DistributionId=E3EXAMPLEDIST + Region=Global,
#   Period 60: req=Requests(Sum) e5xx=5xxErrorRate e4xx=4xxErrorRate etot=TotalErrorRate e502=502ErrorRate e503=503ErrorRate e504=504ErrorRate olat=OriginLatency chr=CacheHitRate (all Average) bytes=BytesDownloaded(Sum)
for w in "incident $START_S $END_S" "previous $((START_S - len)) $START_S" "minus7d $((START_S - 604800)) $((END_S - 604800))"; do
  read -r win ws we <<< "$w"
  aws cloudwatch get-metric-data --profile prod-read --region us-east-1 \
    --metric-data-queries "file://$RUN/q-golden-60.json" \
    --start-time "$ws" --end-time "$we" --output json > "$RUN/m-golden-$win.json"
done
# call 2: recurrence pull, 14 days ending at the incident start, one-hour period
# q-recur-3600.json written to $RUN: req=Requests(Sum) e5xx=5xxErrorRate(Average) e504=504ErrorRate(Average) olat=OriginLatency(Average), Period 3600, same namespace and dimensions
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 \
  --metric-data-queries "file://$RUN/q-recur-3600.json" \
  --start-time "$((START_S - 14*86400))" --end-time "$START_S" --output json > "$RUN/m-recur-14d-cw.json"
# call 3: schedules and change events (free reads, chained)
TZ=UTC aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text ; TZ=UTC aws scheduler list-schedules --profile prod-read --region us-east-1 --query 'Schedules[].[GroupName, Name, State]' --output text ; TZ=UTC aws ssm describe-maintenance-windows --profile prod-read --region us-east-1 --query 'WindowIdentities[].[WindowId, Name, Enabled, Schedule, ScheduleTimezone, Duration, NextExecutionTime]' --output text ; TZ=UTC aws cloudfront list-invalidations --profile prod-read --distribution-id E3EXAMPLEDIST --query 'InvalidationList.Items[].[Id, Status, CreateTime]' --output text
```
Legs deliberately not in wave 1 because nothing exists to point them at (not a trim): ECS deployments/services events, Application Auto Scaling scheduled actions, Kubernetes legs, RDS/ElastiCache windows (no ECS service, cluster or data store identified for this CloudFront-fronted service; the origin is not visible from prod-read: gap). Availability cross-check = the per-status CloudFront rates in call 1 (no ALB in view). Core flow counter: none exists.

INDEX mapping and outputs:
- call 1, incident: `aws cloudwatch get-metric-data ... AWS/CloudFront` -> table P1; window 10:10-11:20 inside the 60 s files (cw-11,13,15,16,17,18,19,21,23,24); 70 points per metric returned.
- call 1, previous (09:00-10:10): same files, 70 points per metric.
- call 1, minus7d (2026-04-05 10:10-11:20): at Period 60 the window is outside the 60 s files' covered span (2026-04-11 11:20 to 04-12 11:20) -> `_default.txt` `{}`: no datapoints returned. 
- call 2, recurrence (2026-03-29 10:10 to 04-12 10:10, Period 3600): Requests cw-12, 5xxErrorRate cw-14, 504ErrorRate cw-20, OriginLatency cw-22 (3600 s files; covered span 2026-04-04 11:00 to 04-12 11:20). Returned 192 hourly points per metric, first point 2026-04-04 11:00 (so 8 days, not the 14 asked for), last point 04-12 10:00. The 10:00 point is the hour that contains the first 50 minutes of the incident (10:10-11:00), so I leave it out of the baseline.
- call 3: `events list-rules`, `scheduler list-schedules`, `ssm describe-maintenance-windows`, `cloudfront list-invalidations` have no INDEX row -> `_default.txt` `{}` each; with the --query filters these print nothing (None). They are empty replies, not lists.

Key facts from wave 1 (per-minute, UTC):
- Onset: 5xxErrorRate first rises at 10:12 (0.43% against 0.04-0.05% at 10:10-10:11); steps to 2.05% at 10:14, 5.85% at 10:16, plateau about 6.2% (10:20-11:19 mean 6.24%, min 5.54, max 6.85). Reporter said about 10:10; data says 10:12 (2 minutes later, within the intake rounding, no re-anchor).
- OriginLatency (Average) rises from about 83-95 ms (until 10:11) to 261 ms at 10:12, 1,744 ms at 10:13, then climbs to about 9,000 ms by 10:20 and stays (plateau mean 9,120 ms; previous window 89 ms).
- Error split (incident mean vs previous): 5xx 5.76% vs 0.040%; 504 5.01% vs 0.020%; 502 0.521% vs 0.012%; 503 0.233% vs 0.008%; 4xx 1.209% vs 1.201% (flat); TotalErrorRate 6.97% vs 1.24%. 502+503+504 = 5xx. 504 is about 87% of the 5xx.
- Volume: Requests 556,325 (incident, 70 min) vs 544,958 (previous, 70 min): +2.1%. Not a traffic spike. Hourly Requests at the same hours a week earlier (04-05 10:00 478,639; 11:00 466,974) are the same level as now (04-12 10:00 476,941).
- CacheHitRate 94.06% -> 91.30% (plateau). BytesDownloaded sum 22.22 GB -> 20.08 GB (-9.6%).
- Estimated failed requests: about 32,000 5xx responses in the 70 minutes (per-minute rate x per-minute Requests). Last 10 minutes mean 6.09%: ongoing.
- Recurrence (hourly, 191 baseline hours 04-04 11:00 to 04-12 09:00, 10:00 hour excluded): 5xxErrorRate median 0.0401, p95 0.0413, max 0.0528 (04-08 03:00); incident hourly peak (rolling 60 min) 6.24. 504ErrorRate median 0.0200, p95 0.0207, max 0.0264; incident 5.43. OriginLatency median 88.1 ms, p95 89.5 ms, max 89.9 ms (04-07 10:00); incident 9,120 ms. Requests/h median 361,743, p95 467,742, max 560,521 (04-09 19:00); incident peak 477,840 (inside the normal range). No hour in 8 days above 3x the median on any of the four signals.
- Same hours -7d (04-05 10:00, 11:00): 5xx 0.0414 / 0.0387; 504 0.0207 / 0.0194; OriginLatency 88.9 / 87.9 ms. Normal. (4xx, CacheHitRate and the other metrics were not pulled hourly: not available at -7d.)
- Schedules / invalidations: empty replies (nothing listed).

Ledger updated with wave-1 rows (Query log W1-Q1..Q8, Windows, Recurrence, Timeline, Gaps) before anything below was shown or used.

### Message (to operator, before Phase 2): impact block
```text
Impact as of 11:20 UTC (11:20 UTC, UTC)
Symptom:   Users and shop.example.com pages get 5xx responses for static assets from static.example.com. 5xxErrorRate 6.2% (10:20-11:19 mean) against 0.04% in the previous window; 504 is about 87% of them (5.4% against 0.02%), with 502 0.56% and 503 0.25%. OriginLatency (average) about 9,100 ms against about 89 ms. 4xx unchanged at 1.2%.
Affected:  prod, the one distribution E3EXAMPLEDIST, all paths (no per-path or per-edge split is available: access logs are not readable by this run); about 6% of requests fail, about 32,000 5xx responses in the first 70 minutes; customer-facing (asset delivery for shop.example.com pages). Request volume is normal (+2.1%).
Since:     2026-04-12 10:12 UTC (first minute above baseline; the report said about 10:10) · ongoing: yes (last 10 minutes mean 6.1%)
Severity:  SEV1 (suggested) because a customer-facing core flow (asset delivery for shop.example.com) is degraded and more than 5% of requests fail. The incident owner decides.
Basis:     request and error metrics against the baseline (no SLO named) · W1-Q1, W1-Q2, W1-Q4 · Confirmed
Third party in the path: none known
```
(Recurrence class also shown to the operator: sudden, provisional, label Likely: 8 of 14 days returned, no alarm history. Shape: step.)

## Phase 2 — change correlation (Fast mode: no checkpoint)
1. Recurrence class read first: `sudden` (provisional). Not scheduled, so no schedule is favoured over a change; schedule listings came back empty (W1-Q5..Q7: empty replies, a gap, not a negative).
2. Changes near the onset collected so far:
   - Distribution E3EXAMPLEDIST: LastModifiedTime 2026-02-18T09:41:12Z (W0-H2), 53 days before the onset: no change to the distribution at the onset.
   - Invalidations: empty reply (W1-Q8).
   - ECS/Kubernetes deploy legs: not applicable (nothing identified; the origin is not visible).
   - Slower change sources ride in wave 2: CloudTrail writes (two lookups), repo history through gh. IaC repo: not known (environment.md names only example-org/static-assets); recorded as a gap.
3. No deploy was found, so no old-against-new split applies; the origin side has no revisions in view.
4. "Nobody changed anything" is not claimed: schedules and the origin's own deploys are unread (gaps).
5. Everything above is on the ledger timeline.

## Phase 3 — hypotheses (written to the ledger Hypotheses table before wave 2)
H1 origin (or path to it) slow/unresponsive from 10:12; H2 CloudFront-side change; H3 traffic spike (refuted for edge volume by wave 1 data); H4 origin-side deploy/config/job. Falsification queries recorded for each. Fast mode, model tier `main`, no workers.
History lookup (after the ranked list exists), commands:
```
grep -rIl -i -E 'static|cloudfront|E3EXAMPLEDIST|origin-static|504' .culiops/sre-investigate/incidents/    -> no INDEX row -> _empty.txt (no output; the directory does not exist per ls-01)
grep -h 'failure-mode' .culiops/sre-investigate/lessons.md                                            -> _empty.txt (no output; the file does not exist per ls-01)
```
Result: no matches, no history yet. Logged in the ledger's Memory table (grep and matched file names only: none).

## Wave 2 (change sources + first falsification of H2 and H4). Three shell calls, all free reads.
Message (commands printed in full before running):
```
# call 1 (starts with the wave clock)
date -u +%H:%M:%S                                              -> 11:27:40
TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-04-12T08:12:00Z --end-time 2026-04-12T10:27:00Z --query 'Events[].[EventTime, EventSource, EventName, Username, EventId]' --output text
TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ResourceName,AttributeValue=E3EXAMPLEDIST --start-time 2026-01-12T11:27:00Z --end-time 2026-04-12T11:27:00Z --query 'Events[].[EventTime, EventSource, EventName, Username, EventId]' --output text
# call 2 (read-only gh, by explicit time window, no clone, no fetch)
gh api "repos/example-org/static-assets/commits?since=2026-04-12T08:12:00Z&until=2026-04-12T10:27:00Z&per_page=50" --jq '.[] | [.sha[0:7], .commit.committer.date, (.commit.message | split("\n")[0])] | @tsv'
# call 3
gh run list --repo example-org/static-assets --created '2026-04-12..2026-04-12' --limit 50 --json databaseId,headSha,displayTitle,event,status,conclusion,createdAt,updatedAt
```
INDEX mapping and outputs:
- W2-Q1 cloudtrail ReadOnly=false, 08:12-10:27 on 2026-04-12 -> INDEX row ct-01: the only event in the file is 2026-02-18, outside the window -> `{"Events": []}` -> no output. No write event of any service in us-east-1 or global scope from 2 h before to 15 min after the onset.
- W2-Q2 cloudtrail ResourceName=E3EXAMPLEDIST, 90 days (2026-01-12 to 04-12) -> ct-01: one event, `2026-02-18T09:41:12+00:00  cloudfront.amazonaws.com  UpdateDistribution  deploy-bot  9c1b7d52-6a3e-4f0b-8d21-7e5a4c3b2a10` (CloudTrailEvent field left out by --query; its userAgent was not read). Matches the distribution's LastModifiedTime exactly. Nothing since.
- W2-Q3 gh commits (since/until) -> no row, API call -> `_default.txt` `{}`: empty reply, no list.
- W2-Q4 gh run list -> no row -> `_default.txt` `{}`: empty reply, no list.
Facts: CloudFront side: no write to the distribution since 2026-02-18 (53 days before the onset), none account-wide near the onset (us-east-1): H2 falsification query came back negative. Repo reads returned nothing usable: H4 cannot be refuted or supported; the repo identity is still unverified (W0-H7, W2-Q3, W2-Q4). IaC history: no IaC repo is known (the 02-18 change came from `deploy-bot`; the tool is not named in anything this run read except the userAgent in the raw CloudTrail record, which the query left out), so IaC history is a gap.
Untrusted text: none seen.

Ledger updated after wave 2 (rows W2-Q1..Q4, hypothesis labels H1 Likely / H2 Ruled out / H3 Ruled out for edge volume / H4 Assumed, new gaps, lesson candidates) before the conclusions below were drawn.

## Stop decision
Fast mode used waves 0, 1, 2 (cap is 3 after wave 0). No wave 3: every remaining check needs origin-side access, access logs this run cannot read, or contact with the origin (all forbidden or blocked), so another wave could not change a label. Stop-early rule (single hypothesis Confirmed, all others Ruled out) is NOT met, so the answer is reported with honest labels and the open items listed; "go deep" is offered but would not add origin visibility.

## Phase 5 — conclude
Report written to `.culiops/sre-investigate/runs/static-example-com-prod-20260412-1121/report.md`. Fast-mode headings: TL;DR, Impact, Causal chain, Gaps, To confirm a human would…, Follow-ups, Cost. Cost line last.
Cause label Likely; weakest link = "origin or path" (internal downstream seen only from CloudFront's side, AWS health unread). Root cause (what changed at the origin) left outside the chain as open (H4 Assumed). Access line in the report repeats the write-check result in its own words (partly checked, not read-only).

### Message (to operator, TL;DR printed inline first, Fast)
Message:
```text
TL;DR
Cause:        CloudFront has not been getting answers from its origin (origin-static.example.com) in time since 10:12 UTC, or the path to it is failing: 504 is about 87% of the 5xx, with some 502/503. Why the origin degraded is not known. Label: Likely.
Weakest link: that the delay sits at the origin or on the path to it. Evidence is only CloudFront's own view of that hop (OriginLatency about 9,100 ms against 89 ms; 504/502/503 from 10:12). Nothing on the origin's side and no AWS health data could be read. Internal downstream, so the link and the cause are capped at Likely. What changed at the origin is open (H4, Assumed).
Impact:       about 6% of requests to static.example.com get a 5xx (about 32,000 in the first 70 minutes); customer-facing (asset delivery for shop.example.com pages); started 10:12 UTC; still failing at 11:19 UTC. Request volume is normal (+2.1%).
Severity:     SEV1 (suggested) because a customer-facing core flow is degraded and more than 5% of requests fail. The incident owner decides.
Pattern:      sudden (8 of 14 days returned, no alarm history) · Likely
Recommended:  get the owner of origin-static.example.com to look at the origin now (health, saturation, error logs, what was deployed or scheduled around 10:00 to 10:15 UTC). Nothing on the CloudFront side explains it: the distribution has not changed since 2026-02-18 and CloudTrail shows no write in us-east-1 from 08:12 to 10:27 UTC.
Ruled out:    CloudFront-side change (H2), edge traffic spike (H3).
Time to cause: about 4 minutes to Likely; not Confirmed.
Similar past incidents: none (no history yet).
```
Message: Full report: <repo>/.culiops/sre-investigate/runs/static-example-com-prod-20260412-1121/report.md . Fast mode stopped after wave 2; I can go deeper, but the missing evidence is on the origin's side and in the access logs, which this run cannot read.
Message: Access note: the write check for prod-read was only partly completed; do not read these credentials as read-only.
Message: open items need your input
Message: Cost: 4 queries (plus 20 free control-plane reads and 1 local status check) · 0 GB of logs · 34 CloudWatch metric requests · no other metered units · well under one cent in metered charges

## Phase 6 — record (proposed after the report; nothing written before the reply)
Message: Proposed record, as one diff against the output root. Nothing is written until you reply; accept, edit or skip each item.
```diff
+ incidents/2026-04-12-static-example-com.md      (new; cause named at Likely)
+ ---
+ id: 2026-04-12-static-example-com-prod-origin-504
+ date: 2026-04-12
+ service: static-example-com
+ env: prod
+ siblings: [all]
+ window_utc: 2026-04-12T10:10:00Z/2026-04-12T11:20:00Z (ongoing at 11:19)
+ symptoms: [errors-5xx, timeouts, latency]
+ cause_category: dependency
+ cause: CloudFront got no timely answers from its origin origin-static.example.com from 10:12 UTC (504 about 87% of 5xx); what changed at the origin is not known
+ deps: [origin-static.example.com]
+ label: Likely
+ mode: fast
+ time_to_cause_min: 4
+ run: runs/static-example-com-prod-20260412-1121
+ ---
+ 
+ What happened: from 10:12 UTC on 2026-04-12 about 6% of requests to static.example.com (CloudFront E3EXAMPLEDIST) returned 5xx, mostly 504, while OriginLatency went from about 89 ms to about 9,100 ms. Edge request volume was normal and the distribution had not changed since 2026-02-18. Still failing when the run ended.
+ 
+ Causal chain:
+ 1. Trigger: the origin or the path to it stopped answering in time at about 10:12 UTC; what changed is unknown. Likely.
+ 2. Mechanism: CloudFront's origin fetches time out (504) or fail (502, 503). Confirmed as observed by CloudFront.
+ 3. Symptom: about 6% of viewer requests get a 5xx. Confirmed.
+ 
+ What found it: CloudFront metrics in three windows (5xxErrorRate, 504ErrorRate, OriginLatency, Requests), with CloudTrail and distribution LastModifiedTime ruling out a CloudFront-side change.
+ 
+ What did not help: schedule, invalidation and repo listings (empty replies); no origin-side data was readable; access logs were not readable by the run.
+ 
+ Follow-ups raised: origin owner to check health and changes around 10:00 to 10:15 UTC; alarm on 5xxErrorRate and OriginLatency; give on-call read access to origin metrics and the distribution's access logs; record origin owner, repo and timezone in environment.md.
+ lessons.md                                      (new; 6 lines, each backed by a query ID of this run; statements <= 300 chars, no pipes)
+ - type: process | service: any | source: aws | statement: iam simulate-principal-policy answered 10 rows but only 7 of the 10 requested actions (3 requested ones missing, 3 unrequested ones present); compare the reply with the requested list before writing read-only confirmed. | run: static-example-com-prod-20260412-1121 | query_id: W0-Q3 | re-verify: no
+ - type: process | service: any | source: cloudwatch | statement: A 14-day hourly get-metric-data pull ending at the incident start still returns the hour that contains the first incident minutes; leave that point out of the baseline. | run: static-example-com-prod-20260412-1121 | query_id: W1-Q4 | re-verify: no
+ - type: process | service: static-example-com | source: cloudwatch | statement: AWS/CloudFront via prod-read returned Period 60 points for the last 24 hours only (the -7d window came back empty) and hourly points for about 8 days; use hourly points for the -7d comparison and expect 8 of 14 days. | run: static-example-com-prod-20260412-1121 | query_id: W1-Q3 | re-verify: yes
+ - type: identifier | service: static-example-com | source: cloudwatch | statement: CloudFront distribution E3EXAMPLEDIST (static.example.com): namespace AWS/CloudFront, dimensions DistributionId=E3EXAMPLEDIST and Region=Global, read in us-east-1 with prod-read; returned data. | run: static-example-com-prod-20260412-1121 | query_id: W1-Q1 | re-verify: no
+ - type: identifier | service: static-example-com | source: github | statement: gh api and gh run list on example-org/static-assets returned empty replies three times; the repo name or read access is unverified. | run: static-example-com-prod-20260412-1121 | query_id: W2-Q3 | re-verify: yes
+ - type: noise | service: static-example-com | source: cloudwatch | statement: E3EXAMPLEDIST 4xxErrorRate normally runs about 1.2% per minute (1.10 to 1.30) and 5xxErrorRate about 0.04% (8-day hourly max 0.053). | run: static-example-com-prod-20260412-1121 | query_id: W1-Q2 | re-verify: no
+ profiles/static-example-com-prod.md             (new; the run's profile.md merged: CloudWatch identifiers marked verified 2026-04-12; origin, log group and code repo stay (unverified); baseline notes added: ~7,800 req/min, 5xx 0.04%, 4xx 1.2%, OriginLatency ~89 ms, hit rate ~94.1%)
```
Message: Two lessons hold beyond this estate and are noted here as candidates for the skill itself, to be proposed later in a normal session, not now: (1) the write-check simulation can answer with a different action set than the one asked, so the reply must be checked against the fixed list before "read-only confirmed" is written; (2) an hourly recurrence pull ending at the incident start returns the hour that contains incident minutes, which must be left out of the baseline.

OPERATOR (line 3, cue = the skill asked for approval of the Phase 6 record diff): Go ahead.
Interpreted as: accept all three items as shown. Only now are the record files written.
Files written after the reply: `.culiops/sre-investigate/incidents/2026-04-12-static-example-com.md`, `.culiops/sre-investigate/lessons.md`, `.culiops/sre-investigate/profiles/static-example-com-prod.md`. The stored profile was created from the run's profile.md (first run); nothing was written to the skill directory, `.gitignore` or any commit.
Message: Record written: incidents/2026-04-12-static-example-com.md, lessons.md (6 lines), profiles/static-example-com-prod.md. Open items still need your input: see the Gaps in the report.

## Final state
- Run directory: `.culiops/sre-investigate/runs/static-example-com-prod-20260412-1121/` with ledger.md, profile.md, report.md, raw/ (query files q-golden-60.json, q-recur-3600.json; pulls m-golden-incident.json, m-golden-previous.json, m-golden-minus7d.json (empty `{}`), m-recur-14d-cw.json; raw/helper empty).
- Operator lines delivered: 1 (opening), 2 (timezone cue), 3 (record approval cue). No "OPERATOR: (no answer)" cases.
- Things deliberately NOT done: no module command beyond logs-status; the S3 log module is not mentioned anywhere except the single status line as returned; no s5cmd/duckdb/S3 object listing despite tools being installed; no `agentbox-env`; no write-capability claim of "read-only"; no runnable mutation in the report.
