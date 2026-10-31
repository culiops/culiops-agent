# Ledger: static.example.com prod 20260412-1121

Mode: Fast
Budget used (final): 4 data queries / 20 (free control-plane reads are logged, not counted: 20 AWS/gh reads plus the local status check) · 0 log GB / 2 · 34 CloudWatch metric requests / 100 (30 golden + 4 recurrence) · no other metered units. Waves used: 0, 1, 2 of the Fast cap (wave 3 not needed: every remaining check needs origin-side access or would touch the service).
(Budgets: environment.md has no budgets section; neutral defaults from environment.template.md used.)

## Problem

| Field | Value |
|---|---|
| What | Reporter: "Users are getting errors on images from static.example.com since about 10:10 UTC today." Measurable restatement: elevated error rate (status class not stated by the reporter) on CloudFront distribution E3EXAMPLEDIST responses, from about 10:10 UTC. |
| Where | prod, CloudFront distribution E3EXAMPLEDIST (alias static.example.com), origin origin-static.example.com. Siblings: none (single distribution, `Region=Global`). |
| When | Reported: "since about 10:10 UTC today" (2026-04-12). True onset: not yet measured (wave 1). Request made about 11:20 UTC. |
| Who is affected | Visitors loading images and assets for shop.example.com pages (core flow named in environment.md). Share affected: not yet measured. |
| Trigger | Operator message in chat. No alarm exists for this distribution (W0-Q5). No ticket. |
| Mitigations already applied | none known (not stated by the operator). |
| Assumptions made at intake | (1) "10:10 UTC" has an explicit zone, so it is used as given (window rule 1); window = 10:10 to now (11:20 UTC), no 30-minute pre-roll. (2) environment.md has no timezone; the operator answered "UTC" in chat, so local time in the report equals UTC. (3) The status class of the errors was not stated; wave 1 reads 4xx, 5xx and the per-code rates. (4) "Images" is read as static assets served by this distribution; the specific paths are unknown. (5) Simulated current time = 2026-04-12 11:21 UTC; window end 11:20:00 (last full minute). |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read | account 111122223333 (matches environment.md `prod`), role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` | partly checked (gap): no listed action is allowed, but ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack returned no usable result | Session valid. The reply held 10 rows, all `implicitDeny`, but 3 of them were for actions not on the fixed list (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy) and did not count. Boxed warning not shown (nothing `allowed`). No token variables listed in environment.md. Culibox: `agentbox-env` absent, nothing said. |
| Kubernetes | none listed | not applicable | no kube write-check |

## Impact

| Field | Value |
|---|---|
| Symptom | 5xx responses from static.example.com: 5xxErrorRate 6.24% (10:20-11:19 mean) against 0.040% in the previous window; 504 is about 87% of the 5xx (5.43% against 0.020%), plus 502 0.56% and 503 0.25%; OriginLatency about 9,120 ms (average) against about 89 ms. 4xx unchanged (1.21% against 1.20%). |
| Affected | All paths on the one distribution (asset delivery for shop.example.com pages, a core flow named in environment.md); no per-path or per-edge split is available (access logs are not readable by this run). About 6% of viewer requests fail with a 5xx; about 32,000 5xx responses in the first 70 minutes (rate x Requests per minute). Customer-facing. Request volume is normal (+2.1% against the previous window). |
| Since / ongoing | 2026-04-12 10:12 UTC (first minute with 5xx above baseline, W1-Q1); reporter said about 10:10. Ongoing: yes (last 10 minutes mean 6.09%, last point 11:19). |
| Suggested severity | SEV1 (default scale; environment.md names the core flow but gives no scale of its own) because a customer-facing core flow (asset delivery for shop.example.com) is degraded and more than 5% of requests fail (6.2% 5xx, plus 1.2% baseline 4xx). The incident owner decides. |
| Basis | CloudFront request and error metrics against the baseline (no SLO named) · W1-Q1, W1-Q2, W1-Q4 · Confirmed (metrics themselves show the rate; the 5% threshold is met in every minute from 10:16) |
| Third party in the path | none known |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-04-12 10:10:00 | 2026-04-12 11:20:00 |
| Baseline (previous) | 2026-04-12 09:00:00 | 2026-04-12 10:10:00 |
| Baseline (−7d) | 2026-04-05 10:10:00 | 2026-04-05 11:20:00 |

Re-anchored: no. The window came from an explicit-zone time (rule 1), and W1-Q1 puts the true onset at 10:12, 2 minutes after the stated 10:10 and inside the incident window, so there is nothing to move. The -7d window at Period 60 returned no datapoints (W1-Q3); the -7d comparison uses the hourly points of the recurrence pull (W1-Q4) for 04-05 10:00 and 11:00.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | none: no CloudWatch alarm exists for this distribution (W0-Q5), so no alarm history and no sibling alarms |
| Signal, 14d at 1h resolution | 5xxErrorRate (Average per hour; a percentage), 504ErrorRate (Average), OriginLatency (Average; hides tails), Requests (Sum). Baseline = the 191 hourly points 04-04 11:00 to 04-12 09:00 (the 10:00 point contains incident minutes and is left out; hours at or above incident level are none). 5xxErrorRate: median 0.0401 · p95 0.0413 · max 0.0528 (04-08 03:00) · incident hourly peak 6.24. 504ErrorRate: median 0.0200 · p95 0.0207 · max 0.0264 · incident 5.43. OriginLatency: median 88.1 ms · p95 89.5 ms · max 89.9 ms · incident 9,120 ms. Requests: median 361,743 · p95 467,742 · max 560,521 (04-09 19:00) · incident peak 477,840 (inside the normal range). |
| Coverage | Hourly points returned: 2026-04-04 11:00 to 2026-04-12 10:00 (192 points per metric), about 8 days of the 14 requested. One-minute points: 2026-04-11 11:20 to 04-12 11:20 only. No alarm history (no alarm). The hour-level "time of day" test is hour-level only. |
| Class | sudden (provisional, on the 8 days returned) · shape: step (error rate steps at 10:12, 10:14 and 10:16 then holds; OriginLatency ramps 10:12 to about 10:20 and holds) |
| Reason | No hour in 8 days is above 3x the median on any of the four signals, and the incident peak is about 118x the 8-day maximum for 5xxErrorRate (6.24 against 0.0528) and 101x for OriginLatency, so it is neither scheduled, chronic nor recurring on this data. The rule's alarm-history leg cannot be checked (no alarm) and days 9 to 14 were not returned, so an earlier occurrence cannot be excluded. Requests are in the normal range, which rules out "normal for this signal". |
| Label and queries | Likely (hourly points only, 8 of 14 days, no alarm history) · W1-Q4 (and W1-Q1 for the minute-level onset) |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-02-18 09:41:12 | Distribution E3EXAMPLEDIST last modified (LastModifiedTime); CloudTrail UpdateDistribution by deploy-bot at the same second; no write to the distribution since | cloudfront get-distribution; CloudTrail | W0-H2, W2-Q2 |
| 2026-04-12 ~10:10 | Errors begin, per the reporter (from the reporter, not from a query) | operator | n/a |
| 2026-04-12 10:11 | Last normal minute: 5xxErrorRate 0.049%, OriginLatency 82.5 ms | CloudWatch AWS/CloudFront | W1-Q1 |
| 2026-04-12 10:12 | First bad minute: 5xxErrorRate 0.43%, 504ErrorRate 0.215%, OriginLatency 261 ms (onset) | CloudWatch AWS/CloudFront | W1-Q1 |
| 2026-04-12 10:13 | OriginLatency 1,744 ms | CloudWatch AWS/CloudFront | W1-Q1 |
| 2026-04-12 10:14 | 5xxErrorRate 2.05% (504 1.78%) | CloudWatch AWS/CloudFront | W1-Q1 |
| 2026-04-12 10:16 | 5xxErrorRate 5.85% (504 5.09%); above 5% from here | CloudWatch AWS/CloudFront | W1-Q1 |
| 2026-04-12 10:20 | OriginLatency about 8,900 ms; plateau begins (5xx about 6.2%, OriginLatency about 9,100 ms) | CloudWatch AWS/CloudFront | W1-Q1 |
| 2026-04-12 11:19 | Last minute read: 5xxErrorRate 5.70%, OriginLatency 9,064 ms; still failing | CloudWatch AWS/CloudFront | W1-Q1 |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | CloudFront's fetches from origin-static.example.com became slow or stopped answering at 10:12 UTC, because of a fault at the origin or on the network path between CloudFront and the origin (the origin's own state is not visible to this run) | OriginLatency up and 504ErrorRate dominant from the same minute; 502 and 503 rising with it; edge Requests and 4xx unchanged; no change on the CloudFront side | OriginLatency and 504/502/503 at baseline during the incident window (would refute): ran in wave 1 (W1-Q1 against W1-Q2) | main | Likely |
| H2 | A change on the CloudFront side at about 10:12 (distribution, origin or cache settings, cache or origin request policy, invalidation) started the failures | A write event on the distribution or its policies in CloudTrail within about 10:12 +/- 15 min; distribution LastModifiedTime near the onset; a new invalidation | Distribution `LastModifiedTime` older than the onset (W0-H2), and no CloudTrail write events (`ReadOnly=false`) from 08:12 to 10:27 in us-east-1 (wave 2: W2-Q1, W2-Q2) | main | Ruled out |
| H3 | A traffic spike or bot raised load at the edge (and so at the origin) | Requests per minute well above the previous window and the same hours a week earlier; volume step at 10:12 | Requests against the previous window, the -7d hours and the 8-day hourly range (flat would refute): ran in wave 1 (W1-Q1, Q2, Q4) | main | Ruled out (edge volume only; origin-bound volume Assumed) |
| H4 | A deploy, config change or scheduled job at the origin (code or assets from example-org/static-assets, or the origin's infrastructure) at about 10:10 slowed it | A commit, workflow run or deploy from about 2 h before to 15 min after the onset; an origin latency step aligned with it | No commit, workflow run or deploy in the repo between 08:12 and 10:27 (would refute, but only if the read returns data): wave 2 (W2-Q3, W2-Q4 returned nothing) | main | Assumed |

Below the table, one line per hypothesis:

- H1 status: supported (effect leg) / open (cause leg) · evidence: W1-Q1, W1-Q2, W1-Q4 · note: Fast mode, no workers; model tier `main`. Not refuted by its falsification query; the CloudFront-observed leg (CloudFront waiting on the origin) is supported, the "origin or path" split and the reason for the degradation have no evidence yet.
- H2 status: refuted · evidence: W0-H2 (LastModifiedTime 2026-02-18T09:41:12Z, 53 days before the onset), W2-Q1 (no write event 08:12-10:27), W2-Q2 (last distribution write 2026-02-18) · note: covers us-east-1/global CloudTrail only; a change to the origin's own infrastructure in another Region would not appear.
- H3 status: refuted for edge volume · evidence: W1-Q1 (Requests +2.1% against previous), W1-Q4 (04-12 10:00 hour 476,941 requests against 04-05 10:00 478,639; peak sits inside the 8-day p95 to max range) · note: "more of the traffic reaching the origin" (100 - CacheHitRate went from 5.9% to 8.7%, which includes the failed fetches) cannot be measured without origin or access-log data: Assumed.
- H4 status: open · evidence: none (W2-Q3, W2-Q4 returned empty replies) · note: a repo read that returns nothing cannot refute it; stays Assumed.

Not on the list: certificate or credential expiry at the origin (a TLS failure would give quick 502s and no latency rise; 502 is only about 9% of the 5xx and OriginLatency rose about 100 times, so it fits badly, but the certificate dates cannot be read without contacting the origin; it goes under "To confirm"); DNS for the origin (same reason); AWS-side health (not readable from this profile; "To confirm").

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/static-assets | not returned (empty reply to `gh api`, W0-H7) | n/a | n/a | not read (wave 2) |

## Query log

W0 started 11:21:07. Rows marked (free) are control-plane reads: logged, not counted against the 20-query budget. Helper rows are prefixed H.

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 11:21:07 | `aws sts get-caller-identity --profile prod-read` | now | free | account 111122223333 = environment.md `prod`; role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b. Confirmed. |
| W0-Q2 | 11:21:07 | `aws iam get-role --profile prod-read --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` | now | free | role ARN resolved (reserved SSO path). Confirmed. |
| W0-Q3 | 11:21:07 | `aws iam simulate-principal-policy --profile prod-read` (10 fixed write actions) | now | free | 10 rows, all implicitDeny, 3 of the fixed actions missing from the reply (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack); outcome partly checked (gap). |
| W0-Q4 | 11:21:07 | `aws logs describe-log-groups --profile prod-read --region us-east-1 --log-group-name-prefix /ecs/static` | n/a | free | empty reply: no CloudWatch log group for the service. Gap. |
| W0-Q5 | 11:21:07 | `aws cloudwatch describe-alarms --profile prod-read --region us-east-1` filtered to namespace AWS/CloudFront | now | free | no alarm for this distribution. Confirmed (absence at read time). |
| W0-Q6 | 11:21:07 | `analytics/bin/logs-status` | n/a | free | `S3 log module: off (not configured)` |
| W0-H1 | 11:21:40 | `aws cloudfront list-distributions --profile prod-read` | now | free | one distribution E3EXAMPLEDIST, alias static.example.com, origin origin-static.example.com, no web ACL. Confirmed. |
| W0-H2 | 11:21:40 | `aws cloudfront get-distribution --profile prod-read --id E3EXAMPLEDIST` | now | free | LastModified 2026-02-18T09:41:12Z; origin read timeout 30 s, 3 attempts, connect timeout 10 s; 504 cached 10 s; logging to S3 `example-edge-logs/cf/static/`. Confirmed. |
| W0-H3 | 11:21:40 | `aws cloudfront get-monitoring-subscription --profile prod-read --distribution-id E3EXAMPLEDIST` | now | free | additional metrics Enabled. Confirmed. |
| W0-H4 | 11:21:40 | `aws cloudwatch list-metrics --profile prod-read --region us-east-1 --namespace AWS/CloudFront` | n/a | free | 10 metrics listed, dimensions DistributionId + Region=Global. |
| W0-H5 | 11:21:40 | `aws ecs list-clusters --profile prod-read --region us-east-1` | now | free | empty reply (not a list shape); origin compute not discovered. |
| W0-H6 | 11:21:40 | `aws elbv2 describe-load-balancers --profile prod-read --region us-east-1` | now | free | empty reply; no load balancer discovered. |
| W0-H7 | 11:21:40 | `gh api repos/example-org/static-assets` (default_branch) | now | free | empty reply; repo identity and default branch unverified. |
| W1-Q1 | 11:23:02 | `aws cloudwatch get-metric-data --profile prod-read --region us-east-1` file `raw/q-golden-60.json` (10 AWS/CloudFront metrics, DistributionId=E3EXAMPLEDIST, Region=Global) | incident 2026-04-12 10:10-11:20, Period 60 | 10 metric requests; actual 10, 70 points each, 0 NaN | 5xx 0.04% to 6.24% from 10:12 (onset), 504 dominant, OriginLatency 89 to 9,120 ms, 4xx flat, Requests +2.1%, CacheHitRate 94.06% to 91.30%. Confirmed (the metrics show it). file: raw/m-golden-incident.json · link: `aws cloudwatch get-metric-data` with the file and window |
| W1-Q2 | 11:23:02 | same query file | previous 2026-04-12 09:00-10:10, Period 60 | 10 metric requests; 70 points each | baseline: 5xx 0.040%, 504 0.020%, 4xx 1.20%, OriginLatency 89 ms, CacheHitRate 94.06%, 544,958 requests. file: raw/m-golden-previous.json |
| W1-Q3 | 11:23:02 | same query file | -7d 2026-04-05 10:10-11:20, Period 60 | 10 metric requests; billed as requested | empty reply `{}` (outside the one-minute data the API returned); the -7d comparison comes from the hourly points in W1-Q4 for the 10:00 and 11:00 hours. file: raw/m-golden-minus7d.json. Gap (partial). |
| W1-Q4 | 11:23:02 | `aws cloudwatch get-metric-data` file `raw/q-recur-3600.json` (Requests Sum, 5xxErrorRate, 504ErrorRate, OriginLatency Average) | 2026-03-29 10:10 to 2026-04-12 10:10, Period 3600 | 4 metric requests; 192 points per metric, first 04-04 11:00 | 8 days returned, not 14. No hour near incident level in 191 baseline hours; class sudden (provisional). Same hours at -7d normal (5xx 0.0414/0.0387, OriginLatency 88.9/87.9 ms). file: raw/m-recur-14d-cw.json |
| W1-Q5 | 11:23:02 | `aws events list-rules --profile prod-read --region us-east-1` (schedule rules only) | now | free | empty reply: nothing listed |
| W1-Q6 | 11:23:02 | `aws scheduler list-schedules --profile prod-read --region us-east-1` | now | free | empty reply: nothing listed |
| W1-Q7 | 11:23:02 | `aws ssm describe-maintenance-windows --profile prod-read --region us-east-1` | now | free | empty reply: nothing listed |
| W1-Q8 | 11:23:02 | `aws cloudfront list-invalidations --profile prod-read --distribution-id E3EXAMPLEDIST` | now | free | empty reply: no invalidation items returned |
| W2-Q1 | 11:27:40 | `aws cloudtrail lookup-events --profile prod-read --region us-east-1` ReadOnly=false, all services, fields EventTime/EventSource/EventName/Username/EventId only | 2026-04-12 08:12-10:27 | free | no events (`Events` empty). No write event in us-east-1 or global scope in the window. Confirmed (for what CloudTrail records in that Region). |
| W2-Q2 | 11:27:40 | `aws cloudtrail lookup-events --profile prod-read --region us-east-1` ResourceName=E3EXAMPLEDIST | 2026-01-12 11:27 to 2026-04-12 11:27 (90 d) | free | one event: 2026-02-18 09:41:12 UpdateDistribution by deploy-bot; none since. Confirmed. |
| W2-Q3 | 11:27:40 | `gh api repos/example-org/static-assets/commits?since=2026-04-12T08:12:00Z&until=2026-04-12T10:27:00Z` | 08:12-10:27 | free | empty reply, no list; repo access unverified. Gap. |
| W2-Q4 | 11:27:40 | `gh run list --repo example-org/static-assets --created 2026-04-12..2026-04-12` | 2026-04-12 | free | empty reply, no list. Gap. |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Write capability of `prod-read` only partly checked: the simulation reply lacked ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (W0-Q3) | None on the findings; the run is read-only regardless. A report must not call these credentials read-only. | Ask the account owner to confirm that role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` is a read-only permission set. |
| No CloudWatch log group for the service (W0-Q4). CloudFront access logs are delivered to S3 (`example-edge-logs`, prefix `cf/static/`), which this run cannot read | Which URLs, status codes, edge locations, user agents or clients are failing is `Assumed` or left out. | A human can read the distribution's access logs for the window, or its real-time/standard log fields, in their own session. |
| No alarm exists for the distribution (W0-Q5) | No alarm history, so recurrence comes from the metric pull only; the true detection time of this incident is unknown. | Observability gap, see report follow-ups. |
| Origin compute not discoverable from `prod-read` (W0-H5, H6): nothing about what serves `origin-static.example.com` | The cause behind origin-side symptoms (if wave 1 shows them) can be at most `Likely`/`Assumed`. | The owning team of the origin; read access to its account/region. |
| `gh` read of example-org/static-assets returned an empty reply (W0-H7) | Application/asset deploys at the origin cannot be tied to the onset yet. | Confirm `gh` access to the repo, or give a local clone path in environment.md. |
| Only 8 of the 14 requested days of hourly points were returned (W1-Q4); the -7d one-minute window returned nothing (W1-Q3) | Recurrence class is `sudden` at most `Likely`; a repeat in days 9 to 14 cannot be excluded. The -7d comparison is hourly only, and 4xx and CacheHitRate have no -7d value. | Read the same metrics for the older days in the CloudWatch console, or run the pull from a profile with the full retention. |
| Schedule and invalidation listings came back as empty replies (W1-Q5 to W1-Q8) | "No schedule fired near 10:12" is not established: the replies carry no list at all, and only this account/Region is covered. A scheduled job at the origin is not visible. | Ask the origin's owner for cron/batch jobs and deploys around 10:10 to 10:15 UTC. |
| IaC repo for the distribution is not known; repo reads returned nothing (W0-H7, W2-Q3, W2-Q4) | H4 (origin-side deploy/config/job) can neither be supported nor refuted; "merged is not applied" cannot be checked. | Name the repo that deploys the origin and its apply pipeline in environment.md, or confirm `gh` access to example-org/static-assets, or a person with origin access lists changes and cron jobs for 10:00 to 10:20 UTC. |
| CloudTrail was read for us-east-1 and global events only (W2-Q1, W2-Q2) | A change to the origin's infrastructure in another Region or account is not covered. | A person with access to the origin's account/Region checks its CloudTrail and deploy history. |
| AWS service health (AWS Health events and dashboard) for CloudFront and the origin's Region was not read: no source for it is listed in environment.md | An AWS-side cause is not excluded; it caps H1's "origin or path" link at `Likely`. | A person opens the AWS Health Dashboard (account and public events) for 10:00 to 11:20 UTC. |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (no lessons.md) |
| Re-verified this run | none |
| History lookup | Run after the ranked hypotheses existed: `grep -rIl -i -E 'static|cloudfront|E3EXAMPLEDIST|origin-static|504' .culiops/sre-investigate/incidents/` returned no files (the directory does not exist, ls-01); `grep -h 'failure-mode' .culiops/sre-investigate/lessons.md` returned nothing (no lessons.md). No `from-history:` entries. |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | aws | `iam simulate-principal-policy` answered 10 rows but only 7 of the 10 requested actions (3 requested ones missing, 3 unrequested ones present): compare the reply with the requested list before writing "read-only confirmed". | W0-Q3 |
| process | cloudwatch | A 14-day hourly get-metric-data pull ending at the incident start still returns the hour that contains the first incident minutes; leave that point out of the baseline. | W1-Q4 |
| process | cloudwatch | AWS/CloudFront through prod-read: Period 60 returned points for the last 24 hours only (the -7d window came back empty) and hourly points for about 8 days; use hourly points for the -7d comparison and expect 8 of 14 days. | W1-Q3 |
| identifier | cloudwatch | CloudFront distribution E3EXAMPLEDIST (static.example.com): AWS/CloudFront, dimensions DistributionId=E3EXAMPLEDIST and Region=Global, read in us-east-1 with prod-read; returned data. | W1-Q1 |
| identifier | github | `gh api` / `gh run list` on example-org/static-assets returned empty replies three times: repo name or read access unverified. | W2-Q3 |
| noise | cloudwatch | E3EXAMPLEDIST 4xxErrorRate normally runs about 1.2% per minute (1.10 to 1.30) and 5xxErrorRate about 0.04% (8-day hourly max 0.053). | W1-Q2 |
