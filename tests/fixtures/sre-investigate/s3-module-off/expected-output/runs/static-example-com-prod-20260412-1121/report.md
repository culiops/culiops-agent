# Investigation: static.example.com prod: 5xx errors (mostly 504) since 10:12 UTC, origin not answering in time

Run: static-example-com-prod-20260412-1121 · Mode: Fast · Window: 10:10 to 11:20 UTC (10:10 to 11:20 local; the operator gave the local zone as UTC) · Onset: 10:12 UTC (10:12 local)
Access: prod-read: partly checked (gap): no listed action is allowed, but ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack returned no usable result. This is not a finding that the credentials are read-only.

## TL;DR

| Field | Value |
|---|---|
| Cause | CloudFront has not been getting answers from its origin, origin-static.example.com, in time since 10:12 UTC (or the network path to it is failing): fetches time out (504 is about 87% of the 5xx) or fail (502, 503). Why the origin degraded is not known. · label: Likely |
| Weakest link | That the delay sits at the origin or on the path to it. The only evidence is CloudFront's own view of that hop (OriginLatency about 9,100 ms against 89 ms, and the 504/502/503 rates, all from 10:12); nothing on the origin's side, and no AWS health data, could be read. This is an internal downstream, so the link is `Likely` and the cause is capped there. What changed at the origin at 10:12 is not a link of the chain: it is an open question (H4, `Assumed`, no evidence either way). |
| Impact | About 6% of requests to static.example.com get a 5xx (about 32,000 in the first 70 minutes), customer-facing (asset delivery for shop.example.com pages). Started 10:12 UTC, still failing at 11:19 UTC, the last minute read. Request volume is normal. |
| Severity | SEV1 (suggested) because a customer-facing core flow is degraded and more than 5% of requests fail. The incident owner decides. |
| Pattern | sudden · no hour in the 8 days of hourly points that came back is near this level (the incident hour is about 118 times the 8-day maximum 5xx rate); only 8 of the 14 days were returned and there is no alarm history · Likely |
| Recommended action | Get the owner of origin-static.example.com to look at the origin now: its health, saturation and error logs, and what was deployed, configured or scheduled around 10:00 to 10:15 UTC. Nothing found on the CloudFront side explains the failure, so changes there are not indicated as the fix. |
| Time to cause | About 4 minutes from the start of the run (11:21 UTC) to the first `Likely` (wave 1 data, about 11:25 UTC). The cause did not reach `Confirmed`, and the root cause was not reached. |
| Similar past incidents | none (no history yet: first run for this service) |

## Impact

- Symptom: 5xx responses for static assets from static.example.com. 5xxErrorRate was 6.24% (mean 10:20 to 11:19 UTC) against 0.040% in the previous 70 minutes. 504ErrorRate was 5.43% against 0.020%; 502ErrorRate 0.56% against 0.012%; 503ErrorRate 0.25% against 0.008%. OriginLatency (average) was about 9,120 ms against 89 ms. 4xxErrorRate did not move (1.21% against 1.20%). W1-Q1, W1-Q2. `Confirmed`.
- Who: visitors loading assets for shop.example.com pages through the one distribution E3EXAMPLEDIST, all paths. No split by path, edge location or client is possible because the access logs were not readable (see Gaps). Estimated 32,000 5xx responses in 70 minutes (per-minute error rate times per-minute Requests). `Confirmed` as an estimate from metrics.
- When: first bad minute 10:12 UTC (5xxErrorRate 0.43%; the minute before was 0.049%). The error rate steps up at 10:14 (2.05%) and 10:16 (5.85%) and then holds near 6%. OriginLatency rises from 261 ms at 10:12 to about 9,000 ms at 10:20 and holds. The reporter said about 10:10. W1-Q1. Ongoing: yes (last 10 minutes mean 6.09%).
- Volume: Requests were 556,325 against 544,958 in the previous window (+2.1%), and the same hours a week earlier were at the same level (04-05 10:00: 478,639; 04-12 10:00: 476,941). CacheHitRate fell from 94.06% to 91.30%, BytesDownloaded by 9.6%. W1-Q1, W1-Q2, W1-Q4.
- Third party in the path: none known. The origin is an internal downstream whose owner is not recorded in environment.md or the profile.

## Causal chain

1. Trigger: something at the origin, origin-static.example.com, or on the network path between CloudFront and the origin, changed state at about 10:12 UTC. What changed is not known. The CloudFront side did not change: the distribution was last modified on 2026-02-18 (W0-H2) and CloudTrail shows no write of any kind in us-east-1 from 08:12 to 10:27 UTC (W2-Q1) and none on the distribution since 2026-02-18 (W2-Q2). Edge traffic was normal (W1-Q1, W1-Q4). · `Likely` (internal downstream seen only from CloudFront's side; AWS-side health not read).
2. Mechanism: CloudFront's fetches to the origin exceed the origin response time (504, about 87% of the 5xx) or fail (502 and 503, about 9% and 4%), and the error is returned to the viewer. OriginLatency and 504ErrorRate leave their baselines in the same minute, 10:12. W1-Q1, W1-Q2. · `Confirmed` as what CloudFront observed.
3. Symptom: about 6% of viewer requests get a 5xx from 10:16 on, still ongoing. W1-Q1. · `Confirmed`.

The cause is capped at `Likely` by link 1. What changed at the origin is not a link of this chain: it is undetermined, and the only candidate (H4) stays `Assumed` below.

Hypotheses considered, in rank order:

| Hypothesis | Label | Basis |
|---|---|---|
| H1: the origin, or the path to it, stopped answering in time from 10:12 | Likely | W1-Q1 against W1-Q2 (the falsification query did not refute it); nothing readable on the origin's side |
| H4: a deploy, config change or scheduled job at the origin around 10:10 caused H1 | Assumed | no evidence either way: the repo reads returned empty replies (W2-Q3, W2-Q4), no origin infrastructure is visible, and the schedule listings came back empty (W1-Q5 to W1-Q7) |
| H2: a change on the CloudFront side (distribution, policies, invalidation) | Ruled out | LastModifiedTime 2026-02-18 (W0-H2); no CloudTrail write 08:12 to 10:27 (W2-Q1); last distribution write 2026-02-18 (W2-Q2); no invalidations listed (W1-Q8, an empty reply). This covers us-east-1 and global events only. |
| H3: a traffic spike or bot at the edge | Ruled out | Requests +2.1% against the previous window, level with the same hours a week earlier and inside the 8-day hourly range (W1-Q1, W1-Q2, W1-Q4). Load reaching the origin as a share of requests (100 minus CacheHitRate went from 5.9% to 8.7%, which includes the failed fetches) cannot be measured without access-log or origin data: `Assumed`. |

Certificate expiry or DNS at the origin was not tested (it would need contact with the origin). It fits badly: a TLS failure gives quick 502s and no latency rise, and here 502 is only about 9% of the 5xx while latency rose about 100 times.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Write capability of prod-read only partly checked (W0-Q3): the simulator's reply lacked ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack | None on the findings (the run only read). Do not read these credentials as read-only. | The account owner confirms that role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b is a read-only permission set. |
| No CloudWatch log group for the service (W0-Q4); CloudFront's access logs go to S3 (bucket example-edge-logs, prefix cf/static/, per the distribution config) and were not read | Which paths, edge locations, clients and edge result types (timeout against connection error) are failing is `Assumed`/left out. Link 1 cannot be narrowed to a path or a region of the edge. | A person with read access to that bucket queries the access logs for 10:00 to 11:20 UTC with their own tools, and the on-call role is given read access to them. |
| No CloudWatch alarm exists for the distribution (W0-Q5) | No alarm history; recurrence rests on metrics alone; the true detection time of this incident is unknown. | See Follow-ups. |
| The origin is not visible from prod-read (W0-H5, W0-H6): no ECS cluster or load balancer was listed, and no origin metrics or logs are configured | Everything about the origin's state and cause is `Assumed`; link 1 is capped at `Likely`. | The owning team of origin-static.example.com, or read access to its account and Region. |
| `gh` reads of example-org/static-assets returned empty replies (W0-H7, W2-Q3, W2-Q4) and no IaC repo is known | H4 can be neither supported nor refuted; "merged is not applied" cannot be checked. | Name the repo that deploys the origin in environment.md and confirm `gh` read access, or a person with origin access lists the changes. |
| Only 8 of the 14 requested days of hourly points came back, and the -7d one-minute window returned nothing (W1-Q3, W1-Q4) | The pattern is `sudden` at most `Likely`; a repeat in days 9 to 14 is not excluded; 4xx and CacheHitRate have no -7d value. | Read the same metrics for the older days in the CloudWatch console, or from a profile with the full history. |
| Schedule and invalidation listings came back as empty replies (W1-Q5 to W1-Q8) and CloudTrail was read for us-east-1 and global events only (W2-Q1, W2-Q2) | "No schedule, job or change near 10:12" is not established for the origin side. | The origin's owner lists cron jobs, batch runs, scaling and deploys for 10:00 to 10:20 UTC, including in other Regions and accounts. |
| AWS service health for CloudFront and the origin's Region was not read | An AWS-side cause is not excluded. | A person opens the AWS Health Dashboard for 10:00 to 11:20 UTC. |

open items need your input

## To confirm, a human would…

1. Look at the origin's own health for 10:00 to 11:20 UTC: CPU, memory, connections and request queueing, its error and latency logs, and the services it depends on. If its slow responses begin at about 10:12 UTC this confirms link 1; if it looked healthy and answered quickly, the delay is on the path or inside CloudFront and the cause should be re-ranked.
2. Ask the owner of origin-static.example.com (not recorded; ask who owns it) what was deployed, configured or scheduled around 10:00 to 10:15 UTC: a release, a cron or batch job, a backup, a scaling or instance-replacement event, a certificate or DNS change. A match turns H4 from `Assumed` into a candidate for the old-against-new check.
3. Read the distribution's access logs for the window (bucket example-edge-logs, prefix cf/static/) and split the failures by path, edge location and edge result type. Failures spread evenly across paths and locations would point at the origin as a whole; failures concentrated on some paths or locations would point at those objects or that part of the network.
4. Open the AWS Health Dashboard for CloudFront and for the origin's Region for 10:00 to 11:20 UTC. An event there would put an AWS-side cause ahead of H1.
5. Check the origin's TLS certificate validity dates and the DNS resolution of origin-static.example.com. This touches the origin's endpoint, so a person decides. A normal result is expected, because the failure shape (504 and high latency) does not look like a certificate or DNS fault.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Restore the origin's responsiveness; the origin owner has to find what changed at about 10:12 UTC. The permanent fix cannot be named until that is known. |
| Fix | While the origin is degraded, consider letting CloudFront serve stale copies of cached assets when the origin errors, through the cache headers the origin sends or the cache settings, at the cost that corrected assets reach visitors later and error responses may be held longer. Assess it with `pre-flight` before applying it. |
| Prevention | Add a CloudWatch alarm on the distribution's 5xxErrorRate (normal level about 0.04%, 8-day hourly maximum 0.053%) and on OriginLatency (normal about 89 ms), so a rise like this one pages within minutes instead of arriving as a user report. The cost is some alert noise if thresholds are set too close to the normal level. |
| Observability gap | No signal from the origin is available to the on-call role: give it read access to the origin's metrics and logs and to the distribution's access logs, and record the origin's owner, its repo and deploy pipeline in environment.md (which also has no timezone line). |
| Observability gap | The write-check of the on-call role could not be completed: confirm the role is read-only so a later run can state it. |

## Cost

4 queries (plus 20 free control-plane reads and 1 local status check) · 0 GB of logs · 34 CloudWatch metric requests · no other metered units · well under one cent in metered charges (34 GetMetricData metric requests; the published rate was not re-checked in this run)
