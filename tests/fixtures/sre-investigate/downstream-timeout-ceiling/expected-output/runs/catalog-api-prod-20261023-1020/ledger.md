# Ledger: catalog-api prod 20261023-1020

Mode: Fast
Budget used: 42 query-log rows (environment.md sets no query total, so none to pass; counted anyway) · 1.8 GB Logs Insights scanned (estimate 1.8 GB; the one query over the 0.5 GB ask threshold was approved by the operator) · 0 CloudWatch metric requests · other metered units: none (Tempo inspected about 47 GB across W1-Q20, W1-Q21 and W2-Q2; no cost model for it)

## Problem

| Field | Value |
|---|---|
| What | Reporter: "catalog-api latency alert in prod has been firing for about 50 minutes. Can you also pull what errors it is logging? Fast mode." Restated: p95 of `http_server_request_duration_seconds` for catalog-api above the 2 s alert rule (measured 4.93 s), and the error messages catalog-api logs during the incident. |
| Where | catalog-api, prod, EKS cluster `prod` (us-east-1, account 111122223333), namespace `catalog`. Siblings: 6 replicas (pods `catalog-api-6b9d7c5f48-*`, HPA 4 to 12); no regions, shards or tenants. |
| When | Reported: "about 50 minutes" before now (10:20 UTC), so about 09:30 UTC (relative time, no zone needed). True onset: 09:31 UTC (p95 steps from 0.398 s to 4.967 s, W1-Q8). Alert `activeAt` 09:32:00Z (W0-Q7). Ongoing at 10:20 UTC. |
| Who is affected | Customers calling `GET /products/{id}` (product-page core flow, about 35% of requests). About 20% of those requests waited the full 5 s in the last 15 minutes (W2-Q1 with W1-Q17); about 0.5% were shown without a price. |
| Trigger | Prometheus alert `CatalogApiLatencyHigh` (severity page; labels service=catalog-api, namespace=catalog), firing, activeAt 09:32:00Z, value 4.952 s, summary "p95 latency above 2s for 10 minutes". Link: none (no Grafana URL in environment.md). The alert's runbook URL is context only and was not opened. |
| Mitigations already applied | none known. The HPA scaled 4 to 6 replicas at about 09:32 UTC on its own (W1-Q3); that is automatic scaling, not a mitigation, and it did not change the p95. |
| Assumptions made at intake | (1) The 50 minutes is relative, anchored on now = 10:20:00 UTC; incident window 09:30 to 10:20 UTC. (2) Local zone America/Sao_Paulo (UTC-3, no daylight saving), taken from environment.md. (3) environment.md has no query or GB totals, only the 0.5 GB Logs Insights ask threshold, so that is the only budget rule applied. (4) Scope = service catalog-api, prod, context and namespace from environment.md. (5) No `agentbox-env` on the machine (command -v failed), so nothing about Culibox was printed. (6) "Firing for about 50 minutes" is read against activeAt 09:32:00Z; with the rule's 10-minute `for` the page itself would have come at about 09:42 UTC (inferred from the summary text, not read from the rule). |

## Access

| Profile or context | Identity (principal and role) | Write-check | Notes |
|---|---|---|---|
| prod-read | account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly (session name not recorded) | no write allowed: 7 of the 10 fixed actions returned a row, all implicitDeny (W0-Q3). Gap: ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack returned no row (the reply held three other actions, also implicitDeny). Informational notice printed; no boxed warning. | Session valid. environment.md lists no token_env for any backend (Prometheus and Tempo are network-restricted, `$PROM_URL`, `$TEMPO_URL`), so no token-presence check applied. |
| arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace catalog | user is the assumed role AWSReservedSSO_ReadOnly via aws-iam-authenticator, group eks-readonly | no write verbs in catalog (W0-Q6): only `create` on selfsubjectreviews, selfsubjectaccessreviews, selfsubjectrulesreviews (excluded) and get/list/watch on `*.*` | The `*.*` get/list/watch grant is wider than the built-in `view` ClusterRole (it includes Secrets). The run does not read Secret objects. |

Code repos: not read (see Code repos).

## Impact

| Field | Value |
|---|---|
| Symptom | Service p95 4.93 s and p99 4.99 s (previous window 0.42 s and 0.89 s; 7 days back 0.42 s and 0.89 s); p50 unchanged at 0.11 s. `GET /products/{id}` p95 4.97 s against 0.44 s 7 days back. Calls from catalog-api to api.pricing.example.com sit at 5.00 s p95 against 0.21 s. In the last 15 minutes 25,914 log lines say the pricing lookup failed after 5000 ms and a cached price was served. |
| Affected | prod, all 6 pods alike. Only `GET /products/{id}` moved (144 of 410 req/s, about 35%): the product-page core flow. /search 0.38 s, /products/{id}/reviews 0.21 s, /categories 0.08 s unchanged. Request rate flat (about 410 req/s) and 5xx share flat (about 0.2%). Customer-facing. 25,914 timeouts in 15 minutes is about 20% of product-page requests and about 7% of all requests (arithmetic on W2-Q1 and W1-Q17, rates at 10:20 UTC). 611 lines (about 0.5% of product-page requests) show the product without a price. |
| Since / ongoing | 09:31 UTC (06:31 local), ongoing at 10:20 UTC |
| Suggested severity | SEV2 because a core flow (product page) is significantly degraded (about 11 to 12 times baseline p95) while still answering and 5xx are not elevated. SEV1 needs the flow down or more than 5% of requests failing; if the owner counts the 7% of all requests that hit a failed pricing lookup (served from cache) as failing, SEV1's 5% line is crossed. The incident owner decides. |
| Basis | request metrics against baseline (environment.md names no SLO) · W1-Q6, W1-Q8, W1-Q9, W1-Q10 to W1-Q17, W2-Q1 · label: Confirmed |
| Third party in the path | api.pricing.example.com is the slow peer. Its owner and contact route are not recorded in environment.md or the profile. It shares the domain of the org's own internal hosts, which hints at an internal team; unconfirmed. The run cannot contact it; a human has to. |

## Windows (UTC)

| Window | From | To |
|---|---|---|
| Incident | 2026-10-23 09:30:00 | 2026-10-23 10:20:00 |
| Baseline (previous) | 2026-10-23 08:40:00 | 2026-10-23 09:30:00 |
| Baseline (-7d) | 2026-10-16 09:30:00 | 2026-10-16 10:20:00 (queried as `offset 7d` on the 10-23 window, or as the shifted window in Tempo) |

## Recurrence

| Field | Value |
|---|---|
| Alarm transitions (30d, UTC) | Not available. The Prometheus alerts API returns current state only (W0-Q7: one alert, no siblings); the `ALERTS` series pull for 14 days came back as an empty matrix (W1-Q18). No CloudWatch alarm is involved. |
| Signal, 14d at 1h resolution | Not available. `max_over_time(http_server_requests_in_flight[1h])` (saturation signal, chosen because a 14-day latency quantile has no recording rule and exceeds the 12 h quantile cap) came back as an empty matrix (W1-Q19). What exists: 5.2 h of pre-onset data at 1-minute resolution (04:20 to 09:30 on the day): p95 median 0.425 s, max 0.460 s; incident p95 4.93 s. |
| Coverage | Prometheus range answers returned 04:20 to 10:20 on 2026-10-23 only (361 points, W1-Q6 to W1-Q14, W1-Q8 for p95). 14-day hourly pulls returned nothing for series that exist; cause unknown (retention or a server limit). |
| Class | unclassified · shape: ceiling (p95 and p99 flat at 4.93 s and 4.99 s while p50 is unchanged), arrived as a step at 09:31 |
| Reason | No other occurrence can be read; the only history is 5.2 h before the onset in which p95 never exceeded 0.46 s. Neither `scheduled`, `chronic`, `recurring` nor `sudden` can be shown from that, so the class is unclassified and the missing history is a gap. |
| Label and queries | not applicable (gap) · W1-Q18, W1-Q19, W1-Q8 |

## Timeline

| When (UTC) | What happened | Where it came from | Deeplink or query ID |
|---|---|---|---|
| 2026-10-14 07:58:03 (as printed by Helm, zone not printed; ReplicaSet age 9d fits UTC) | Helm release revision 22 deployed: chart catalog-api-2.6.1, app 1.31.2. The last change to catalog-api. | helm history | W1-Q4 |
| 2026-10-23 09:30 | p95 0.398 s (baseline) | Prometheus | W1-Q8 |
| 09:31 | p95 steps to 4.967 s, p99 to 4.986 s; p50, request rate and 5xx unchanged | Prometheus | W1-Q8, W1-Q9, W1-Q6, W1-Q13, W1-Q14 |
| 09:30 to 09:35 bucket | api.pricing.example.com client-span p95 0.21 s to 5.00 s (5-minute step; first 5.00 s sample 09:35) | Tempo | W1-Q20 |
| 09:32:00 | Alert CatalogApiLatencyHigh activeAt | Prometheus alerts API | W0-Q7 |
| about 09:32 | HPA SuccessfulRescale 4 to 6 (pods metric http_requests_in_flight above target); pod kx9vn started (event age 48m at 10:20, plus or minus 1 min) | kubectl events | W1-Q3 |
| about 09:33 | pod p6wfj scheduled and started (event age 47m) | kubectl events | W1-Q3 |
| about 09:42 | Alert would move to firing after its 10-minute `for` (inferred) | reporter and alert summary | W0-Q7 |
| 10:02 to 10:14 | Five sampled slow traces, all GET /products/{id}, each with a 5.00 s client span to api.pricing.example.com, status error | Tempo | W2-Q2 |
| 10:05 to 10:20 | 25,914 log lines "pricing lookup failed ... after 5000ms; serving cached price" | Logs Insights | W2-Q1 |
| 10:20 | p95 4.93 s, ongoing | Prometheus | W1-Q8 |
| about 09:30 (reporter) | Alert "has been firing for about 50 minutes" (from the reporter, not a query) | reporter | - |

## Hypotheses

| ID | Statement | Expected if true | Falsification query | Model | Label |
|---|---|---|---|---|---|
| H1 | The delay sits in catalog-api's call to api.pricing.example.com: calls wait out a 5 s client timeout, `GET /products/{id}` waits on them. | ceiling shape; that peer's client-span p95 at about 5 s while other peers are at baseline; only the route that calls it slows; timeout log lines | that peer's client-span p95 at baseline refutes it (W1-Q20 against W1-Q21); sampled slow traces whose time sits outside that span refute it (W2-Q2) | main | Likely (mechanism Confirmed; origin behind the call is not observed) |
| H2 | Capacity: pods or autoscaler at a limit | CPU or in-flight pinned, HPA at max, rate up, all routes slow | HPA at max or CPU saturated (P1-Q4, W1-Q5), rate against previous window (W1-Q13) | main | Ruled out (CPU throttling series not queried; p50 and the other routes unaffected) |
| H3 | Bad deploy or rollout | onset as a new revision takes traffic; new pods fail where old ones do not | onset earlier or later than any rollout refutes it (W1-Q1, W1-Q2, W1-Q4) | main | Ruled out (no revision since 2026-10-14; all 6 pods on the same 9-day-old ReplicaSet; 0 restarts) |
| H4 | Traffic spike or bot | volume shape: request count up | request count against the previous window (W1-Q13, W1-Q17) | main | Ruled out (409 against 412 req/s median; per-route rates sum to 410 req/s) |
| H5 | Network path to the pricing host (NAT or egress, DNS) | failures only on calls leaving the network; port-allocation errors or drops | NAT ErrorPortAllocation and PacketsDropCount at baseline refute it | main | Assumed (not tested: NAT gateway id not discovered, no CloudWatch metrics in this Fast run) |
| H6 | The pricing service itself is degraded or down | the same peer-level slowdown, seen from its side | the pricing service's own latency and errors at baseline refute it | main | Assumed (its metrics, status route and owner are not readable from here) |
| H7 | Local pod or node cause | one pod out of line with its peers | per-pod restarts, CPU, memory (P1-Q3, W1-Q5) | main | Ruled out for CPU, memory and restarts (per-pod latency not pulled) |
| H8 | Config change without a rollout (ConfigMap, pricing client URL or timeout) | change time near 09:31 | ConfigMap managed-fields times | main | Assumed (not checked: ConfigMap names not discovered) |

- H1 status: supported · evidence: W1-Q20, W1-Q21, W1-Q22 (empty), W1-Q15, W1-Q16, W2-Q1, W2-Q2 · note: main session, Fast mode; the falsification queries ran first (W1-Q20 against W1-Q21, then W2-Q2) and did not refute it.
- H2 status: refuted · evidence: P1-Q4, W1-Q5, W1-Q3, W1-Q13 · note: HPA at 6 of 12 replicas; the scale-up came at about 09:32, after the 09:31 onset, so it is a consequence (Likely).
- H3 status: refuted · evidence: W1-Q1, W1-Q2, W1-Q4, P1-Q3 · note: app code was not read because no deploy sits near the onset.
- H4 status: refuted · evidence: W1-Q13, W1-Q17 · note: the 7-day-back rate baseline was not pulled (no row for it in the backend; see Gaps).
- H5 status: open · evidence: none · note: the log text "Client.Timeout exceeded while awaiting headers" can come from a slow connect or a slow response, so it does not separate H5 from H6.
- H6 status: open · evidence: none · note: needs the owner of api.pricing.example.com.
- H7 status: refuted for CPU, memory and restarts · evidence: W1-Q5, P1-Q3.
- H8 status: open · evidence: none.

## Code repos

Not read. No deploy sits near the onset, so no app diff was needed. The IaC and Helm values repo `example-org/catalog-deploy` was tried through `gh` (W2-Q7) and returned `{}` rather than a commit list, which is a gap, not an absence of commits. `example-org/catalog-api` was not read (no local clone listed in environment.md; deployed image 1.31.2 from W1-Q3 and W1-Q4).

| Repo | Default branch | Origin SHA | Fetched (UTC) | Deployed commit(s) |
|---|---|---|---|---|
| example-org/catalog-api | not read | not read | not read | image 1.31.2 (commit not resolved) |
| example-org/catalog-deploy | not read | not read | not read | chart catalog-api-2.6.1 (Helm revision 22) |

## Query log

All rows are read-only. Times in the Start column are the wave's first `date -u` output. The data is fixed at now = 10:20:00 UTC. Identifiers: marked verified (2026-10-23) once a query in this run returned data for them. Link column: no Grafana or console URL is configured; replay with the command shown.

| ID | Start (UTC) | Source | Range | Est. cost | Result |
|---|---|---|---|---|---|
| W0-Q1 | 10:20:07 | AWS CLI, profile prod-read: `aws sts get-caller-identity --profile prod-read --output json` (and the same with `--query Arn --output text`) | now | free | account 111122223333 matches environment.md; assumed role AWSReservedSSO_ReadOnly · Confirmed |
| W0-Q2 | 10:20:07 | `aws iam get-role --profile prod-read --role-name "$role" --query Role.Arn --output text` | now | free | role ARN resolved, path /aws-reserved/sso.amazonaws.com/ · Confirmed |
| W0-Q3 | 10:20:07 | `aws iam simulate-principal-policy --profile prod-read --policy-source-arn "$role_arn" --action-names <the 10 fixed actions> --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text` | now | free | 10 rows, all implicitDeny; 3 requested actions have no row (gap) · Confirmed (limited) |
| W0-Q4 | 10:20:07 | `kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod` | now | free | role AWSReservedSSO_ReadOnly, group eks-readonly · Confirmed |
| W0-Q5 | 10:20:07 | `kubectl config current-context` | now | free | the same context ARN · Confirmed |
| W0-Q6 | 10:20:07 | `kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace catalog` | now | free | no write verbs; get/list/watch on `*.*` · Confirmed |
| W0-Q7 | 10:20:07 | Prometheus (`$PROM_URL`): `GET /api/v1/alerts` | now | free | one alert, CatalogApiLatencyHigh, firing, activeAt 09:32:00Z, value 4.952 · Confirmed |
| W0-Q8 | 10:20:07 | CloudWatch Logs, prod-read us-east-1: `describe-log-groups --log-group-name-prefix "/eks/prod/catalog"` + jq estimate; group `/eks/prod/catalog-api` (verified) | 10:05 to 10:20 (900 s) | free | 2.42 TB stored, retention 14 d, class STANDARD; estimate 1.8 GB for 15 min (172.8 GB per day) · Confirmed |
| P1-Q1 | 10:20:09 | helper (cheapest tier): Tempo `GET /api/v2/search/tags` (start 1792747800, end 1792750800) | 09:30 to 10:20 | free | tag names only; resource scope has `service.name`; span scope has `server.address`, `http.route`, `db.system` · Confirmed (names only; service name value still unverified) |
| P1-Q2 | 10:20:09 | helper: Prometheus `GET /api/v1/label/__name__/values` (start, end as above) | 09:30 to 10:20 | free | 12 names incl. `http_server_request_duration_seconds_{bucket,count,sum}`, `http_server_requests_in_flight`, `kube_deployment_status_replicas`; no `ALERTS` name listed · Confirmed |
| P1-Q3 | 10:20:09 | helper: `kubectl get pods -n catalog` | now | free | 6 pods Running, 0 restarts; 4 aged 9d, 2 aged 48m and 47m · Confirmed |
| P1-Q4 | 10:20:09 | helper: `kubectl get hpa -n catalog` | now | free | catalog-api, Deployment/catalog-api, TARGETS 58/40, min 4, max 12, 6 replicas · Confirmed |
| P1-Q5 | 10:20:09 | helper: `kubectl get deployment,service,ingress -n catalog` | now | free | no output; not used for identification (pods and HPA already name the workload) · no label |
| W1-Q1 | 10:20:41 | `kubectl --context <ctx> -n catalog rollout history deployment/catalog-api` | current | free | revisions 17 (chart 2.6.0, image 1.31.1) and 18 (chart 2.6.1, image 1.31.2); no time column · Confirmed |
| W1-Q2 | 10:20:41 | `kubectl --context <ctx> -n catalog get rs --sort-by=.metadata.creationTimestamp` (selector not discovered, so none) | current | free | catalog-api-58f4d6b7c9 0 desired, age 16d; catalog-api-6b9d7c5f48 6 ready, age 9d · Confirmed |
| W1-Q3 | 10:20:41 | `kubectl --context <ctx> -n catalog get events --sort-by=.lastTimestamp` | events live about 1 h | free | only Normal events: HPA SuccessfulRescale to 6 at 48m, ScalingReplicaSet 4 to 6, two pods scheduled and started (48m, 47m); no Warning events · Confirmed |
| W1-Q4 | 10:20:41 | `helm history catalog-api --kube-context <ctx> -n catalog --max 10` | all | free | rev 21 2026-10-07 08:12:40 superseded (chart 2.6.0); rev 22 2026-10-14 07:58:03 deployed (chart 2.6.1, app 1.31.2); zone not printed (the 9d ReplicaSet age fits UTC) · Confirmed |
| W1-Q5 | 10:20:41 | `kubectl --context <ctx> -n catalog top pods` | current | free | 6 pods 187 to 224m CPU, 349 to 391Mi memory; no outlier · Confirmed |
| W1-Q6 | 10:20:41 | Prometheus: `histogram_quantile(0.5, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[5m])))`, label service verified | 08:40 to 10:20 range, step 60 s (361 points returned from 04:20) | free | p50 median 0.110 s previous, 0.109 s incident · Confirmed |
| W1-Q7 | 10:20:41 | Prometheus: same with 0.9 (p90) | same | free | empty matrix, no series. Selector verified by W1-Q6; no explanation. p90 is a gap; p50 and p95 bracket it · no label |
| W1-Q8 | 10:20:41 | Prometheus: same with 0.95 (p95) | same | free | p95 0.398 s at 09:30, 4.967 s at 09:31; median 0.418 s previous, 4.934 s over 09:35 to 10:20; max before onset 0.460 s · Confirmed |
| W1-Q9 | 10:20:41 | Prometheus: same with 0.99 (p99) | same | free | p99 median 0.892 s previous, 4.991 s incident (max 4.999) · Confirmed |
| W1-Q10 | 10:20:41 | Prometheus: p50 query with `[5m] offset 7d` inside the rate | same, values from 2026-10-16 | free | p50 median 0.109 s in the 09:30 to 10:20 window one week back · Confirmed |
| W1-Q11 | 10:20:41 | Prometheus: p95 with `offset 7d` | same | free | p95 median 0.424 s (max 0.464) one week back · Confirmed |
| W1-Q12 | 10:20:41 | Prometheus: p99 with `offset 7d` | same | free | p99 median 0.891 s (max 0.968) one week back · Confirmed |
| W1-Q13 | 10:20:41 | Prometheus: `sum(rate(http_server_request_duration_seconds_count{service="catalog-api"}[5m]))` | same | free | request rate median 412 req/s previous, 409 incident (range 398 to 422): flat · Confirmed |
| W1-Q14 | 10:20:41 | Prometheus: ratio of `rate(...count{service="catalog-api", status=~"5.."}[5m])` to the total rate (label status verified) | same | free | 5xx share median 0.21% previous, 0.23% incident (max 0.27%): flat · Confirmed |
| W1-Q15 | 10:20:41 | Prometheus instant: `histogram_quantile(0.95, sum by (le, route) (rate(...bucket{service="catalog-api"}[30m])))` (label route verified) | evaluated 10:20 over 09:50 to 10:20 | free | /products/{id} 4.968 s; /search 0.381; /products/{id}/reviews 0.214; /categories 0.083; /healthz 0.004 · Confirmed |
| W1-Q16 | 10:20:41 | Prometheus instant: same with `offset 7d` | same, one week back | free | /products/{id} 0.441 s; /search 0.372; reviews 0.207; categories 0.079; healthz 0.004 · Confirmed |
| W1-Q17 | 10:20:41 | Prometheus instant: `sum by (route) (rate(...count{service="catalog-api"}[30m]))` | evaluated 10:20 | free | /products/{id} 144.2 req/s; /search 121.7; /categories 83.9; reviews 58.3; /healthz 2.0 (sum 410.1) · Confirmed |
| W1-Q18 | 10:20:41 | Prometheus recurrence: `max_over_time(ALERTS{alertname="CatalogApiLatencyHigh", alertstate="firing"}[1h])` | 2026-10-09 09:30 to 2026-10-23 10:20, step 3600 | free | empty matrix; alert history not available · gap |
| W1-Q19 | 10:20:41 | Prometheus recurrence: `max_over_time(http_server_requests_in_flight{service="catalog-api"}[1h])` | 2026-10-09 09:30 to 2026-10-23 09:30, step 3600 | free | empty matrix; 14-day history not available (saturation signal chosen; latency 14 d exceeds the quantile cap) · gap |
| W1-Q20 | 10:20:41 | Tempo metrics: `{ resource.service.name = "catalog-api" && span:kind = client } \| quantile_over_time(span:duration, .95) by (span.server.address)` (service name verified) | 08:40 to 10:20, step 300 s; inspected 18.7 GB | none | api.pricing.example.com 0.21 s before, 5.00 s from the 09:35 sample (median 4.999 s over 09:30 to 10:20); reviews-api.catalog.svc.cluster.local 0.06, catalog-db.internal.example.com 0.004, catalog-cache.internal.example.com 0.001: flat · Confirmed |
| W1-Q21 | 10:20:41 | Tempo metrics: same query, window shifted back 7 days | 2026-10-16 08:40 to 10:20, step 300 s | none | pricing 0.20 s median in the matching window; the other peers the same as today's baseline · Confirmed |
| W1-Q22 | 10:20:41 | Tempo metrics: `{ resource.service.name = "catalog-api" && span:kind = client } \| rate() by (span.server.address)` | 08:40 to 10:20 | none | empty series, 0 jobs; call rate per peer not available · gap |
| W2-Q1 | 10:22:15 | Logs Insights, prod-read us-east-1, group `/eks/prod/catalog-api` (verified): `filter @message like /ERROR\|Error\|error\|Exception\|exception\|Timeout\|timeout\|timed out\|deadline\|failed/ \| stats count(*) as n by message \| sort n desc \| limit 20`; start-query then one get-query-results | 10:05 to 10:20 (operator-approved narrowing) | 1.8 GB estimated (threshold 0.5 GB, approved) | complete; 1.8 GB scanned, ratio 1.00 to the estimate; 26,534 matching lines: 25,914 "pricing lookup failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) after 5000ms; serving cached price"; 611 "pricing cache miss; product shown without price"; 9 "reviews-api returned 503; reviews block hidden". Result columns came back as `msg` and `count(*)`, not `message` and `n`. Raw: raw/li-5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9.json · Confirmed |
| W2-Q2 | 10:22:15 | Tempo search: `{ resource.service.name = "catalog-api" && (span:status = error \|\| span:duration > 1500ms) }`, limit 20 | 10:00 to 10:20 | none | 5 traces (10:02:24, 10:05:04, 10:08:11, 10:11:47, 10:14:27), all GET /products/{id}, root 5.00 to 5.03 s; each holds one client span GET to api.pricing.example.com of 5.0003 to 5.0005 s, status error. 5 samples (under 20): mechanism only, no shares · Likely for the sample as a whole; it supports the Confirmed mechanism with W2-Q1 |
| W2-Q3 | 10:22:15 | `kubectl --context <ctx> get cronjobs -A -o custom-columns=...` | current | free | no output: no CronJob listed · Assumed (empty output only) |
| W2-Q4 | 10:22:15 | `aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text` | current | free | reply `{}`; no scheduled rule listed · Assumed |
| W2-Q5 | 10:22:15 | `aws scheduler list-schedules --profile prod-read --region us-east-1 ...` | current | free | reply `{}`; no schedule listed · Assumed |
| W2-Q6 | 10:22:15 | `TZ=UTC aws cloudtrail lookup-events` ReadOnly=false, us-east-1, filter on resource names containing "catalog" | 07:31 to 09:46 (onset minus 2 h to plus 15 min) | free | reply `{}` (no Events key): no write event returned; not read as proof, since the pricing host is not an AWS resource and the resource-name filter is unverified · Assumed |
| W2-Q7 | 10:22:15 | `gh api` commits of `example-org/catalog-deploy`, 2026-10-20 09:31 to 2026-10-23 10:20 | 3 days before onset to now | free | reply `{}` instead of a commit list: unreadable (access or no result); IaC history not read · gap |

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Nothing readable from the pricing side: no metrics, status route or owner for api.pricing.example.com (H6) | Caps the cause at Likely: the delay is shown at the call, but whether it originates in the pricing service or on the path to it is not observed | Name the owner and a status or contact route in environment.md; ask that owner whether they see slow or hung requests since 09:31 UTC |
| Network path to the pricing host not tested: NAT gateway id not discovered, no CloudWatch metrics queried, no DNS check (H5) | H5 stays Assumed; it cannot be separated from H6 | A person with access reads NAT gateway ErrorPortAllocation and PacketsDropCount for 09:25 to 09:40 UTC on the cluster's egress path; Deep mode can add it once the NAT gateway id is in the profile |
| 14-day and 30-day history empty (W1-Q18, W1-Q19) and p90 empty (W1-Q7); Prometheus returned only 6 h | Recurrence is unclassified; no "has it happened before" answer | Confirm Prometheus retention and whether a recording rule for the p95 and an alert-history source exist; add them to environment.md |
| No baseline for the log messages (a second scan of about 1.8 GB needs the operator's approval) | Whether the 611 "shown without price" and 9 "reviews-api 503" lines are new is unknown; the timeout line is tied to the onset by metrics, not by logs | Approve a baseline scan of the same 15-minute clock window from 7 days back, or the same hour on a quiet day |
| App code and the pricing client's timeout and fallback were not read (`gh` returned `{}`, W2-Q7; no local clone listed) | "5 s is a configured client timeout" and "requests complete from a cached price" rest on log text and a flat 5xx share (Likely) | Add a local clone path to environment.md, or confirm `gh` read access to example-org/catalog-api and catalog-deploy |
| CloudTrail, EventBridge and Scheduler replies were empty (`{}`) (W2-Q4 to W2-Q6) and the CronJob list printed nothing (W2-Q3) | "No schedule or AWS-side write near 09:31" is Assumed, not shown | A person checks the same lookups in the console with the account's own tools |
| Per-pod latency not pulled (pod label not discovered); 7-day-back rate and 5xx baselines not pulled (no matching series form); per-peer call rate empty (W1-Q22) | "Pods alike" rests on CPU, memory and restarts; volume is judged against the same day's previous window | Add the pod label and a rate recording rule to the profile |
| 3 of the 10 write-check actions returned no row; the `*.*` get/list/watch grant is wider than `view` | Read-only is shown for 7 actions only | Use the built-in `view` ClusterRole for incident work and a tighter AWS read policy |
| No Grafana, Sentry, ticket system, wiki, SLO or business counters in environment.md | No deploy annotations, error-tracker issues or SLO burn; the alert's runbook was not read | List the backends in environment.md |

## Untrusted text

none seen (log lines, alert annotations and Kubernetes events contained no instruction-like text).

## Memory

| Item | Value |
|---|---|
| Lessons loaded | none (no lessons.md under the output root; the W0 `ls` showed only environment.md) |
| Re-verified this run | none |
| History lookup | run after the hypotheses were ranked: no incidents/ directory exists (W0 `ls`), so no match; "no history yet" |

## Lesson candidates

| Type | Source | Statement | Query ID |
|---|---|---|---|
| identifier | cw-logs | Log group /eks/prod/catalog-api: the Logs Insights result column for the message came back as msg and the count as count(*); read the field names from the first result before relying on aliases. Stored 2.42 TB, retention 14 days. | W2-Q1 |
| process | cw-logs | A 15-minute Logs Insights window on /eks/prod/catalog-api scanned 1.8 GB (storedBytes over retention predicted 1.8 GB, ratio 1.00); any window over about 4 minutes exceeds the 0.5 GB ask threshold. | W2-Q1 |
| identifier | tempo | Trace service name is catalog-api (resource.service.name); the outgoing-call peer is span.server.address (api.pricing.example.com, reviews-api.catalog.svc.cluster.local, catalog-db.internal.example.com, catalog-cache.internal.example.com). | W1-Q20 |
| process | prometheus | Range queries answered for 6 h only; 14-day hourly pulls (ALERTS, max_over_time of http_server_requests_in_flight) and a p90 histogram_quantile came back as empty matrices. Record recurrence as unclassified. | W1-Q18 |
| failure-mode | tempo | p95 and p99 flat near 5.0 s with p50 and request rate unchanged, a client span to api.pricing.example.com at 5.00 s p95, and log lines "context deadline exceeded ... after 5000ms; serving cached price": the pricing call is waiting out its 5 s timeout. | W2-Q1 |
| process | kubectl | The catalog-api HPA scales on in-flight requests (event: pods metric http_requests_in_flight above target), so a downstream wait triggers a scale-up after the onset; read it as a consequence, not a cause. | W1-Q3 |
