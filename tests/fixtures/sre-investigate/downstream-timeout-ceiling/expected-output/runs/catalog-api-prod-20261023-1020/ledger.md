# Ledger: catalog-api prod 20261023-1020

Mode: Fast
Budget used: 14 / 20 queries (counted: calls to metric, log, trace, cluster and code backends; identity, write-check, discovery and local reads not counted - assumption, environment.md sets only the Insights threshold, other budgets are the template's neutral Fast defaults) · 1.8 / 2 GB log scanned (one Logs Insights query, estimate 1.8 GB, actual bytesScanned 1.8e9, ratio 1.00; approved by the operator after the ask) · 0 / 100 CloudWatch metric requests

## Problem

| Field | Value |
|---|---|
| What | Reporter: "catalog-api latency alert in prod has been firing for about 50 minutes", and asks which errors it is logging. Measurable restatement: alert `CatalogApiLatencyHigh` (p95 > 2 s for 10 min) firing, value 4.95 s. |
| Where | catalog-api, prod, EKS cluster `prod`, namespace `catalog`, 6 pods (replicas are the only siblings; no regions/shards) |
| When | Reported "about 50 minutes" before 10:20 UTC (relative time). Alert `activeAt` 2026-10-23 09:32:00Z (06:32 America/Sao_Paulo). True onset: 09:31 UTC (06:31 local), the minute p95 stepped from 0.40 s to 4.97 s (W1-Q3). |
| Who is affected | requests to GET /products/{id} (about 35% of traffic, 144 of 410 req/s): p95 4.97 s vs 0.44 s a week ago; other routes at baseline; 5xx share unchanged (W1-Q3, W1-Q4, W1-Q5) |
| Trigger | Prometheus alert `CatalogApiLatencyHigh`, labels namespace=catalog, service=catalog-api, severity=page (W0-Q13); annotation runbook_url exists, not read |
| Mitigations already applied | none known |
| Assumptions made at intake | (1) Window from a relative time: incident 09:30-10:20 UTC (06:30-07:20 America/Sao_Paulo, zone from environment.md), previous 08:40-09:30 UTC, -7d 2026-10-16 09:30-10:20 UTC. (2) Budgets other than the Insights ask threshold (0.5 GB) are the template's neutral Fast defaults. (3) Budget unit: one query = one call to a metric/log/trace/cluster/code backend. (4) Repo root = case directory; output root `.culiops/sre-investigate/`, ignored by git (W0-Q2). (5) Wave 0 data is evaluated at 10:20 UTC. |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read | account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b | no action allowed: 7 of the 10 broad write actions evaluated implicitDeny; 3 of 10 (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) returned no result -> write capability not fully checked (gap). Not "read-only confirmed". No boxed warning (nothing allowed). | session valid; simulator also returned 3 rows not asked for (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy, implicitDeny), ignored; no token variables listed in environment.md; Culibox not detected (`command -v agentbox-env` failed, nothing said) |
| arn:aws:eks:us-east-1:111122223333:cluster/prod (namespace catalog) | Kubernetes identity = role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b, group eks-readonly | no write verbs in catalog | `*.*` is get/list/watch; `create` only on the three self-review resources (not counted) |

## Impact

| Field | Value |
|---|---|
| Symptom | p95 of catalog-api 4.93 s (median 09:31-10:20) vs 0.42 s previous window and 0.43 s a week earlier; p99 4.99 s vs 0.89 s; p50 unchanged at 0.11 s; request rate flat (409 vs 412 req/s); 5xx share flat (0.23% vs 0.21%) |
| Affected | prod catalog-api, service-wide metrics; route GET /products/{id} p95 4.968 s (-7d 0.441 s) is the only slow route; /search 0.381 s (0.372), /products/{id}/reviews 0.214 (0.207), /categories 0.083 (0.079), /healthz 0.004 (0.004) are at baseline. /products/{id} = 144.2 of 410.1 req/s (35%). Core flow product page degraded; search unaffected. |
| Since / ongoing | 2026-10-23 09:31 UTC (06:31 America/Sao_Paulo); ongoing at 10:20 (p95 4.932 s) |
| Suggested severity | SEV2 because a core flow (product page) is significantly degraded but not down: success rate unchanged, search unaffected. Incident owner decides. |
| Basis | W1-Q3, W1-Q4, W1-Q5 · label: Confirmed (request metrics against baseline, no SLO named). -7d baselines for rate, 5xx share and route rate returned empty (W1-Q4, W1-Q5): those comparisons use the previous window only. |
| Customer-visible detail | From the app's own log lines in 10:05-10:20 (W2-Q1): 25,914 pricing timeouts served with a cached price (about 28.8 per s, about 20% of the route's 144.2 req/s if one line is one /products/{id} request - Assumed, the message has no route); 611 "product shown without price" (about 0.47% of the route's requests, same assumption). Whether cached prices can be stale is unknown. |
| Third party in the path | api.pricing.example.com is the slow dependency (W1-Q6, W2-Q2); vendor or internal owner unknown, no contact route in environment.md or the profile. The run cannot contact vendors; a human has to. |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-23 09:30:00 | 2026-10-23 10:20:00 |
| Baseline (previous) | 2026-10-23 08:40:00 | 2026-10-23 09:30:00 |
| Baseline (−7d) | 2026-10-16 09:30:00 | 2026-10-16 10:20:00 |

Re-anchored: no. The window came from a relative time (rule 3) and the onset, 09:31 UTC (W1-Q3), is inside it and one minute after its start.

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | not available: the `ALERTS{alertname="CatalogApiLatencyHigh"}` pull over 14 d to 09:30 returned an empty matrix (W1-Q7). Empty means either never fired in the retained range or ALERTS is not retained/queryable here; the two cannot be told apart. No sibling alarms exist (single environment). No CloudWatch alarm is involved. |
| Signal, 14d at 1h resolution | latency p95 not pulled for 14 d (histogram_quantile that wide exceeds the 12 h cap and no recording rule exists: gap). 5xx share (hourly increase ratio) returned 6 points, 04:30-09:30 UTC: median 0.0021, max 0.0026, incident 0.0023 (flat). For scale, minute-level p95 latency 04:20-09:29 (W1-Q3): median 0.425 s, p95 0.456 s, max 0.46 s; incident peak 4.97 s. |
| Coverage | Prometheus: about 5 h of data returned for a 14 d request (first point 04:20 UTC today, W1-Q7 and W1-Q3). ALERTS: none returned. CloudWatch alarm history: not applicable. |
| Class | unclassified · shape: step and ceiling |
| Reason | no occurrence history (empty ALERTS pull) and 5 h instead of 14 d of signal, so none of scheduled / chronic / recurring / sudden can be applied by the rules. If the empty ALERTS pull meant "never fired", the incident peak (4.97 s) is more than 10 times the 5-hour maximum (0.46 s) and the class would be `sudden`; that is not established. Recorded as a gap. |
| Label and queries | Assumed (coverage gap) · W1-Q3, W1-Q7 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-07 08:12:40 | Helm revision 21: chart catalog-api-2.6.0, image 1.31.1 (superseded) | helm history (output has no zone; read as UTC, assumption) | W1-Q1 |
| 2026-10-14 07:58:03 | Helm revision 22: chart catalog-api-2.6.1, image 1.31.2 (deployed); ReplicaSet 6b9d7c5f48 created (age 9d); last rollout, 9 days before the onset | helm history, rollout history, get rs | W1-Q1 |
| 2026-10-23 04:20-09:30 | p95 stable 0.39-0.46 s, p50 0.10-0.12 s, rate about 411 req/s, 5xx share 0.15-0.27% | Prometheus | W1-Q3, W1-Q4 |
| 2026-10-23 09:30 | last normal samples: p95 0.398 s; pricing client-span p95 0.21 s (5-min sample) | Prometheus, Tempo | W1-Q3, W1-Q6 |
| 2026-10-23 ~09:30 | "firing about 50 minutes" (reporter, not a query) | operator | operator line 1 |
| 2026-10-23 09:31 | p95 0.398 -> 4.967 s in one 60 s step; p99 0.888 -> 4.986 s (onset) | Prometheus | W1-Q3 |
| 2026-10-23 ~09:32 | HPA SuccessfulRescale 4 -> 6 "pods metric http_requests_in_flight above target"; pods kx9vn (48 m) and p6wfj (47 m) started on the existing ReplicaSet (event ages relative to 10:20, minute precision, single occurrences) | kubectl events | W1-Q2, W0-Q20 |
| 2026-10-23 09:32:00 | alert CatalogApiLatencyHigh active | Prometheus alerts API | W0-Q13 |
| 2026-10-23 09:35 | first 5-min sample with pricing client-span p95 = 5.0005 s; stays 4.9965-5.0012 s to 10:20; other three dependencies flat | Tempo | W1-Q6 |
| 2026-10-23 10:02:24, 10:05:04, 10:08:11, 10:11:47, 10:14:27 | five sampled slow traces of GET /products/{id}, 5.004-5.030 s each, 5.0003-5.0005 s of it in one client span to api.pricing.example.com (status error) | Tempo search | W2-Q2 |
| 2026-10-23 10:05-10:20 | 25,914 "pricing lookup failed ... after 5000ms; serving cached price", 611 "pricing cache miss; product shown without price", 9 "reviews-api returned 503; reviews block hidden" | CloudWatch Logs Insights | W2-Q1 |
| 2026-10-23 10:20 | p95 4.932 s, p99 4.989 s; /products/{id} p95 4.968 s; HPA 58/40 at 6 replicas | Prometheus, kubectl | W1-Q3, W1-Q5, W0-Q21 |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | Calls from catalog-api to api.pricing.example.com wait out a roughly 5 s timeout because that host is slow or unresponsive on its own side, slowing GET /products/{id} | pricing client-span p95 rises to the timeout at the onset; slow traces dominated by that span; timeout messages in the logs; other dependencies flat | pricing client-span p95 at baseline in the window (W1-Q6) | main | Likely |
| H2 | The network path from the pods to api.pricing.example.com broke (NAT port allocation, DNS, security group or route change) | failures only on calls leaving the network; connect (not read) timeouts or DNS errors; NAT errors or a network write in CloudTrail near 09:31 | NAT ErrorPortAllocation / PacketsDropCount at baseline; no DNS or connect errors; no network write near the onset | main | Assumed |
| H3 | A runtime change on the catalog-api side with no rollout (config re-read, feature flag, pricing client setting) | step at one instant with no pod restart; a config-reload or flag message in the logs | ConfigMap / flag change time not near 09:31, no such message | main | Assumed |
| H4 | Bad deploy or config rollout of catalog-api | errors or latency start as the new revision takes traffic; new pods fail where old ones do not | onset earlier than the rollout, or old revision failing the same way | main | Ruled out |
| H5 | Capacity: catalog-api CPU, memory or autoscaler at max | CPU/memory near limits, HPA pinned at max, all routes slow, p50 up | headroom throughout, other routes and p50 unchanged | main | Ruled out |
| H6 | Traffic spike or bot | request rate up against previous window and -7d, concentrated on a few paths | no rise against the previous window | main | Ruled out |
| H7 | reviews-api or catalog-cache slow | their client-span p95 up at the onset | their own p95 at baseline | main | Ruled out |
| H8 | catalog-db slow, or more queries per request (N+1) on /products/{id} | DB span count per request up even with a flat per-call p95 | span count per request flat (requires a call-rate-by-address query) | main | Assumed (not cleared) |
| H9 | `sched:` a timer fires near 09:31 (CronJob, EventBridge rule, scaling action) | job/rule fire time within 15 min of 09:31 | schedule listings show no fire near the onset | main | Ruled out |
| H10 | Node, instance or Spot churn | restarts, evictions, node terminations within 10 min of the onset | none in the retained events | main | Ruled out |

- H1 status: supported (client side) · evidence: W1-Q6, W2-Q1, W2-Q2, W1-Q3, W1-Q5 · note: top rank; the timeout at 5000 ms and the slow requests' time spent in the pricing call are Confirmed, but why the host stops answering is not visible from here and its owner (vendor or internal) is unknown, so the cause caps at Likely (downstream rule)
- H2 status: open · evidence: W2-Q1 message (does not say which stage stalled), W2-Q5 (NAT list and CloudTrail replies empty) · note: only one external host in the spans, so no comparison group; neither refuted nor supported
- H3 status: open · evidence: W2-Q1 (no reload/flag message among the 3 messages in 10:05-10:20), W2-Q4 (no ConfigMap visible), W2-Q6 (gh empty) · note: pods unchanged for 9 days, so any change was a runtime one; the onset instant (09:31) is outside the log window, so the logs cannot show it
- H4 status: refuted · evidence: W1-Q1, W0-Q20, W1-Q3 · old-vs-new split: not a candidate (not near the onset): new revision n/a; the single revision (6b9d7c5f48, 6/6 pods incl. the 2 HPA-added) served normally 04:20-09:30 today (p95 0.39-0.46 s) and failed after 09:31 with no revision change; last rollout 9 days before the onset
- H5 status: refuted · evidence: W1-Q2, W0-Q21, W1-Q3, W1-Q5 · note: memory limits and CPU throttling were not read; ruled out on headroom (HPA 6 of 12, CPU 187-224m), unchanged p50 and four unchanged routes
- H6 status: refuted · evidence: W1-Q4 · note: against the previous window only (-7d came back empty)
- H7 status: refuted · evidence: W1-Q6
- H8 status: open, low rank · evidence: W1-Q6 (p95 flat 0.004 s), W1-Q6 rate query empty, W2-Q2 (5 of 5 sampled slow requests spend 99.5-99.9% of their duration in the pricing span) · note: a flat p95 alone does not clear the DB and n=5 is below the 20 samples needed for span-count claims, so it is not labelled Ruled out
- H9 status: refuted for listed sources · evidence: W2-Q4 (no CronJobs in catalog, no EventBridge rules returned) · note: EventBridge Scheduler, SSM maintenance windows and the provider's own timers were not read; recurrence is unclassified, so history cannot add to this
- H10 status: refuted · evidence: W1-Q2, W0-Q20 · note: events cover from about 09:20, so the onset is inside coverage
- History: no incidents or lessons exist (W1-L1, W1-L2), so there are no `from-history:` entries.

## Code repos

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/catalog-api | unknown (`gh api` returned `{}`) | unknown | n/a | not resolved |

## Query log

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 10:20:03 | local: `git rev-parse --show-toplevel` | n/a | free | no output (case dir taken as repo root) |
| W0-Q2 | 10:20:03 | local: `git check-ignore -q .culiops/sre-investigate` | n/a | free | exit 0: ignored |
| W0-Q3 | 10:20:03 | local: `cat .culiops/sre-investigate/environment.md` | n/a | free | read; Confirmed (file) |
| W0-Q4 | 10:20:03 | local: `ls .culiops/sre-investigate` | n/a | free | only environment.md: no profile, lessons or incidents |
| W0-Q5 | 10:20:03 | local: `command -v agentbox-env` | n/a | free | not found |
| W0-Q6 | 10:20:31 | aws sts get-caller-identity, profile prod-read | n/a | free | account 111122223333, role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b |
| W0-Q7 | 10:20:31 | aws iam get-role, profile prod-read, role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b | n/a | free | role ARN under /aws-reserved/sso.amazonaws.com/ |
| W0-Q8 | 10:20:31 | aws iam simulate-principal-policy, profile prod-read, 10 fixed actions | n/a | free | 7 asked actions implicitDeny; 3 asked actions no row (gap); 3 unasked rows ignored |
| W0-Q9 | 10:20:31 | kubectl auth whoami, context cluster/prod | n/a | free | role AWSReservedSSO_ReadOnly_..., group eks-readonly |
| W0-Q10 | 10:20:31 | kubectl config current-context | n/a | free | cluster/prod |
| W0-Q11 | 10:20:31 | kubectl auth can-i --list, context cluster/prod, ns catalog | n/a | free | no write verbs in catalog |
| W0-Q12 | 10:20:31 | aws logs describe-log-groups prefix /eks/prod/catalog, prod-read, us-east-1 | est. window 900 s | free | `/eks/prod/catalog-api` 2.42 TB, 14 d: ~1.8 GB per 15 min, ~6 GB per 50 min; ratio to actual: n/a (no scan yet) |
| W0-Q13 | 10:20:31 | GET $PROM_URL/api/v1/alerts | now | free | CatalogApiLatencyHigh firing, value 4.952, activeAt 09:32:00Z. Confirmed (query result) |
| W0-Q14 | 10:20:55 | helper: describe-log-groups prefix /eks/prod/catalog | n/a | free | same single group |
| W0-Q15 | 10:20:55 | helper: Tempo tag values resource.service.name | 09:20-10:20 | free | `{}` |
| W0-Q16 | 10:20:55 | helper: Tempo search/tags | n/a | free | attribute names (server.address, http.route, db.system, service.name ...) |
| W0-Q17 | 10:20:55 | helper: Tempo search `{ resource.service.name = "catalog-api" }` limit 5 (name `(unverified)`) | 09:20-10:20 | free | 0 traces, inspectedTraces 0 |
| W0-Q18 | 10:20:55 | helper: Prometheus label values `service` | n/a | free | `{}` |
| W0-Q19 | 10:20:55 | helper: Prometheus metric names | n/a | free | 12 names; no span metrics / cAdvisor / kube_pod_owner |
| W0-Q20 | 10:20:55 | helper: kubectl get pods, ns catalog | now | free | 6 pods, 0 restarts; 4 are 9d old, 2 are 47-48m old |
| W0-Q21 | 10:20:55 | helper: kubectl get hpa, ns catalog | now | free | catalog-api 58/40, min 4, max 12, 6 replicas |
| W0-Q22 | 10:20:55 | helper: kubectl get deployments,services,ingresses, ns catalog | now | free | no output |
| W0-Q23 | 10:20:55 | helper: helm list, ns catalog | now | free | no output |
| W0-Q24 | 10:20:55 | helper: ls .culiops/service-discovery | n/a | free | No such file or directory |
| W0-Q25 | 10:20:55 | helper: gh api repos/example-org/catalog-api | n/a | free | `{}` (gap) |
| W1-Q1 | 10:21:48 | kubectl (context cluster/prod, ns catalog): rollout history deployment/catalog-api; get rs --sort-by=.metadata.creationTimestamp; helm history catalog-api -n catalog --max 10 (release `catalog-api` verified by this call) | now | free | rev 17 (2.6.0, 1.31.1), rev 18 (2.6.1, 1.31.2); rs 6b9d7c5f48 6/6 age 9d, rs 58f4d6b7c9 0 age 16d; helm rev 22 deployed 2026-10-14 07:58:03, 9 days before onset. Confirmed (query result) |
| W1-Q2 | 10:21:48 | kubectl get events --sort-by=.lastTimestamp; kubectl top pods (ns catalog) | events cover ~09:20-10:20; top: now | free | HPA 4 -> 6 at ~09:32, 2 pods scheduled/started, no Warning events; CPU 187-224m, memory 349-391Mi. Confirmed |
| W1-Q3 | 10:21:48 | Prometheus: histogram_quantile(q, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[5m] [offset 7d]))), q = 0.5, 0.9, 0.95, 0.99, step 60 s | 08:40-10:20 (previous + incident) and -7d | free | p50 flat 0.11 s; p95 0.4175 -> 4.934 s (median; -7d 0.4255), step at 09:31; p99 0.8915 -> 4.991 s (-7d 0.891); p90 empty (not used). Confirmed. Labels `service` verified |
| W1-Q4 | 10:21:48 | Prometheus: sum(rate(..._count{service="catalog-api"}[5m])) and 5xx ratio with status=~"5..", step 60 s, now and offset 7d | 08:40-10:20 | free | rate 412.4 -> 408.9 req/s (flat); 5xx share 0.0021 -> 0.0023 (flat); both -7d queries empty (gap) |
| W1-Q5 | 10:21:48 | Prometheus instant at 10:20: histogram_quantile(0.95, sum by (le, route) (rate(..._bucket{service="catalog-api"}[30m]))) and sum by (route) (rate(..._count[30m])), now and offset 7d | 09:50-10:20 | free | /products/{id} p95 4.968 s vs 0.441 s; other routes at baseline; route rates sum to 410.1; route-rate -7d empty (gap). Confirmed. Route labels verified |
| W1-Q6 | 10:21:48 | Tempo TraceQL metrics: { resource.service.name = "catalog-api" && span:kind = client } \| quantile_over_time(span:duration, .95) by (span.server.address), step 300 s, now and -7d; and \| rate() by (span.server.address) | 08:40-10:20 and 2026-10-16 08:40-10:20 | free | api.pricing.example.com p95 0.21 s -> 5.00 s from 09:35 sample; reviews-api 0.057, db 0.004, cache 0.001 flat; -7d pricing 0.20 s; rate query returned no series (gap). Confirmed for the latency step; `catalog-api` trace name verified |
| W1-Q7 | 10:21:48 | Prometheus query_range: max_over_time(ALERTS{alertname="CatalogApiLatencyHigh", alertstate="firing"}[1h]); 5xx share increase[1h] ratio; 14 d to 09:30 at step 3600 | 2026-10-09 09:30 to 2026-10-23 09:30 | free | ALERTS: empty; 5xx share: 6 points only (04:30-09:30). Coverage gap |
| W1-L1 | 10:22:20 | local grep of incidents/ front matter (service, deps, symptom words) | n/a | free | no output (no history) |
| W1-L2 | 10:22:20 | local grep failure-mode in lessons.md | n/a | free | no output (no file) |
| W2-Q1 | 10:24:40 | CloudWatch Logs Insights, prod-read, us-east-1, group /eks/prod/catalog-api: stats count(*) as n by message \| sort n desc \| limit 25 (field `message` was `(unverified)`; the result column is `msg`) | 10:05-10:20 | est. 1.8 GB (above the 0.5 GB ask threshold: operator asked and said yes for the last 15 minutes); actual bytesScanned 1.8e9, ratio actual/estimate 1.00; completed | 3 messages: pricing timeout (after 5000ms, serving cached price) 25,914; pricing cache miss, product shown without price 611; reviews-api 503, reviews hidden 9; recordsMatched 26,534. Confirmed for the mechanism on the client side. link: console Logs Insights with this query and window |
| W2-Q2 | 10:24:40 | Tempo search: { resource.service.name = "catalog-api" && (span:status = error \|\| span:duration > 1500ms) }, limit 20 | 10:00-10:20 | free | 5 traces (48,211 inspected), all GET /products/{id}, 5.004-5.030 s, each with a 5.0003-5.0005 s client span to api.pricing.example.com, status error; n=5 (<20), used for time share only. Confirmed for these 5 |
| W2-Q3 | 10:24:40 | Prometheus: histogram_quantile(0.95, sum by (le, pod) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[10m]))) at 10:20 (label `pod` unverified) | 10:10-10:20 | free | empty matrix: no per-pod latency |
| W2-Q4 | 10:24:40 | kubectl get cronjobs; kubectl get configmaps (ns catalog); aws events list-rules (Rules[?ScheduleExpression]) | now | free | no CronJobs, no ConfigMaps visible, no EventBridge rules returned |
| W2-Q5 | 10:24:40 | aws ec2 describe-nat-gateways; aws cloudtrail lookup-events ReadOnly=false, EventSource ec2.amazonaws.com | 07:31-09:46 | free | both `{}`: no NAT gateway listed, no Events array; inconclusive, not "nobody changed anything" |
| W2-Q6 | 10:24:40 | gh api repos/example-org/catalog-deploy/commits?since=2026-10-20T09:31:00Z (read-only) | 2026-10-20 to 2026-10-23 | free | `{}` (gap) |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Write capability not fully checked: 3 of the 10 simulated actions (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) returned no result (W0-Q8) | none on the evidence; the run is read-only regardless. The report cannot say "read-only confirmed". | confirm in chat that prod-read is a read-only role (recorded as operator-asserted), or re-run the check once the simulator evaluates those three actions |
| App code and IaC unreadable: `gh api` returns `{}` and no local clone is listed (W0-Q25) | any claim about a code or Helm-values change, and the "5 s is a client timeout" inference, is at most Assumed | add a read-only GitHub token or a local clone of example-org/catalog-api and example-org/catalog-deploy to environment.md |
| No -7d baseline for request rate, 5xx share and per-route call rate: the queries returned empty (W1-Q4, W1-Q5) | volume and error comparisons use the previous window only; H6 is ruled out on that basis | check whether Prometheus retains 7+ days of these series; add a recording rule |
| Recurrence cannot be classified: ALERTS pull empty and about 5 h of signal for a 14 d request (W1-Q7); latency 14 d not pulled (over the 12 h quantile cap, no recording rule) | recurrence class is `unclassified` (Assumed); a schedule or repeat cannot be excluded from history | read the alert's history in the alerting UI; add a recording rule for the p95 |
| p90 quantile query returned an empty matrix (W1-Q3) | none: p50, p95, p99 carry the ceiling test | none needed |
| Tempo call-rate by server.address returned no series (W1-Q6) | span count per request cannot be compared, so H8 (database / N+1) is not cleared | enable span metrics or query a TraceQL count per trace |
| Kubernetes events table showed ages, not first-seen timestamps (W1-Q2) | timing of the HPA event is minute-level (about 09:32) | none needed |
| Per-pod latency not available: the p95-by-pod query returned an empty matrix (W2-Q3) | local-versus-shared at pod level rests on `kubectl top` (no outlier, W1-Q2) and on service-wide metrics | add a `pod` label to the latency histogram, or use a recording rule |
| NAT gateways, EventBridge rules and CloudTrail EC2 writes returned empty replies (W2-Q4, W2-Q5) | H2 (network path) cannot be tested; "nobody changed anything" is not concluded | confirm the role may call ec2:DescribeNatGateways, cloudtrail:LookupEvents and events:ListRules, and re-run |
| Only one Logs Insights window was affordable (10:05-10:20); no log baseline before 09:31 and no first-occurrence time of the timeout line | whether the timeout message existed at a lower rate before the onset is not shown by logs (Tempo shows pricing p95 at 0.21 s before 09:30); the 9 reviews-api 503 lines cannot be classed as noise or new | approve another Insights window (about 1.8 GB per 15 minutes) before 09:31, or use a wider-budget Deep run |
| Runbook URL on the alert not read: no wiki access configured | runbook content is not used | add wiki read access to environment.md |
| Owner of api.pricing.example.com unknown (vendor or internal team), no status page or contact in environment.md or the profile | the pricing link is at most Likely; vendor status cannot be checked | name the owner and status page in the profile |

## Untrusted text

none seen

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (`lessons.md` does not exist) |
| Re-verified this run | none |
| History lookup | after the ranked hypotheses existed: `grep -r -l -E "catalog-api|api.pricing.example.com|latency" .culiops/sre-investigate/incidents/` (W1-L1) and a read of the `failure-mode` lines of `lessons.md` (W1-L2): no output; no matched files, no `from-history:` entries |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| process | aws | The IAM simulator reply may not contain the actions asked for (3 of 10 missing, 3 unasked rows returned): count rows against the asked list before writing "read-only confirmed" | W0-Q8 |
| identifier | prometheus | Latency histogram is http_server_request_duration_seconds with labels service and route; there are no span metrics, so per-dependency latency comes from Tempo TraceQL metrics by span.server.address | W1-Q3 |
| process | prometheus | Offset-7d queries on request rate, 5xx share and route rate, and 14-day pulls of ALERTS and 5xx share, came back empty or with about 5 h of points, although offset 7d works for the latency histogram; treat them as gaps (not as retention facts) and baseline against the previous window | W1-Q4 |
| identifier | tempo | Trace service name is catalog-api (resource.service.name); the peer is the span attribute server.address; the tag-values and unfiltered search calls returned nothing before a TraceQL metrics query returned data | W1-Q6 |
| identifier | cw-logs | In /eks/prod/catalog-api the message field is `msg` (Insights result column), not `message`; discover it with a free get-log-group-fields call before the first stats query | W2-Q1 |
| process | tempo | A time-bounded Tempo search can return a trace that started before the requested start (one trace 2.5 min early); check trace start times against the window before counting | W2-Q2 |
