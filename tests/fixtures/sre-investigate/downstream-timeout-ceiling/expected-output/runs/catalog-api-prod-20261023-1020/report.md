# Investigation: catalog-api prod: product-page p95 stuck at 5 s on pricing-call timeouts

Run: catalog-api-prod-20261023-1020 · Mode: Fast · Window: 2026-10-23 09:30–10:20 UTC (06:30–07:20 America/Sao_Paulo) · Onset: 09:31 UTC (06:31 America/Sao_Paulo)
Access: prod-read: no action allowed. 7 of the 10 broad write actions evaluated implicitDeny. 3 of 10 (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) returned no result, so write capability is not fully checked (gap). This is not "read-only confirmed", and no boxed warning applied because nothing was allowed. · arn:aws:eks:us-east-1:111122223333:cluster/prod: no write verbs in catalog

## TL;DR

| Field | Value |
|---|---|
| Cause | catalog-api's calls to api.pricing.example.com stopped completing within its 5000 ms client timeout at about 09:31 UTC (06:31 local). Each timed-out lookup holds a `GET /products/{id}` request for 5 s and then serves a cached price · label: Likely |
| Weakest link | Why the calls stall. The pricing host being slow on its own side, the network path to it, or a runtime change on the catalog-api side cannot be told apart from here. The host's owner (vendor or internal) is unknown, and a downstream cause is at most Likely without that side's confirmation · Likely (the split between the three explanations is Assumed). The later links (5000 ms timeout, cached-price fallback, slow product page) are Confirmed. |
| Impact | `/products/{id}` p95 is 4.97 s against 0.44 s a week ago. About 20% of its requests wait 5 s and get a cached price (28.8 timeout lines/s against 144 req/s, assuming one line per request). 611 product views in 15 minutes had no price. 5xx did not rise and search is unaffected. Ongoing at the last data, 10:20 UTC (07:20 local). |
| Severity | SEV2 (suggested) because the product page, a core flow, is significantly degraded but not down. The incident owner decides. |
| Pattern | unclassified · the alert-history pull was empty and about 5 h of signal came back for a 14-day request · Assumed |
| Recommended action | Ask the owner of api.pricing.example.com, or read its status page, to say whether it has been slow or unreachable since about 09:31 UTC. The alert's runbook may name the owner (not read). In parallel, have someone with a shell inside the cluster network time DNS, connect, TLS and first byte to that host from a pod and compare with another external destination, to separate the provider from the network path. Do not rely on scaling catalog-api out as the fix: the extra pods only hold more 5-second calls. Whether to keep serving cached prices or hide the price block meanwhile is a product decision, because cached prices may be stale. Check any mitigation with `pre-flight` first. |
| Time to cause | First Likely about 2 minutes in (10:22 UTC, wave 1). Mechanism Confirmed about 5 minutes in (10:25 UTC, wave 2). The cause as a whole stays Likely. |
| Similar past incidents | no history yet (no incident files, no lessons) |

## Impact

- **Symptom.**
  - Service p95 is 4.93 s (median 09:31–10:20) against 0.42 s in the previous window and 0.43 s a week earlier. p99 is 4.99 s against 0.89 s.
  - p50 is unchanged at 0.11 s, and request rate is flat (409 against 412 req/s).
  - The 5xx share is flat (0.23% against 0.21%), inside the 0.15–0.27% it has had since 04:20 (W1-Q3, W1-Q4).
- **Scope.**
  - Only `GET /products/{id}` is slow: p95 4.968 s against 0.441 s a week ago (W1-Q5). It carries 144.2 of 410.1 req/s (35%).
  - `/search` (0.381 s against 0.372 s), `/products/{id}/reviews` (0.214 against 0.207), `/categories` (0.083 against 0.079) and `/healthz` are at baseline.
  - The product page is a listed core flow and is degraded. Search is not affected.
  - The metrics are service-wide. A per-pod latency split returned nothing (W2-Q3), and `kubectl top` shows no outlier pod (W1-Q2).
- **Customer-visible detail (W2-Q1, 10:05–10:20 UTC).**
  - 25,914 "pricing lookup failed … after 5000ms; serving cached price" lines, about 28.8 per s.
  - 611 "pricing cache miss; product shown without price" lines, about 0.47% of the route's requests.
  - Both figures assume one line per `/products/{id}` request. The message carries no route.
  - Whether the cached prices served can be stale is unknown.
- **Window.** The step is at 09:31 UTC (06:31 local), and the alert became active at 09:32 UTC (06:32 local). It was still ongoing at 10:20 UTC (07:20 local).
- **Basis.** Request metrics against baseline (no SLO is named in environment.md) · Confirmed. The −7d baselines for request rate, 5xx share and per-route rate came back empty, so those comparisons use the previous window only.
- **Third party in the path.** api.pricing.example.com is the slow dependency. Whether it is a vendor or an internal team is not recorded in environment.md or the profile, so there is no contact route. The run cannot contact vendors; a human has to.

## Causal chain

1. Trigger: calls to api.pricing.example.com stopped returning within 5 s at about 09:31 UTC.
   - Client side: Confirmed (W1-Q6, W2-Q2). Pricing client-span p95 went from 0.21 s to 5.0005 s at the 09:35 sample and stayed at 4.9965–5.0012 s through 10:20. All 5 sampled slow `/products/{id}` traces (5.004–5.030 s each) spend 5.0003–5.0005 s in one pricing client span with status error.
   - Why the calls stall: Likely at best, as the downstream or provider-side stall (H1). The split among the three explanations is Assumed. No query reaches inside the host or the egress path.
2. Mechanism: the pricing client times out at 5000 ms and serves a cached price. The request waits the full 5 s but still succeeds, so 5xx do not rise · Confirmed · W2-Q1, W1-Q6, W2-Q2.
   - The app's own log line says "after 5000ms; serving cached price" (25,914 lines in 15 min).
   - 611 further lines read "pricing cache miss; product shown without price".
3. Symptom: `/products/{id}` p95 4.97 s. Service p95 and p99 are pinned at 4.93–5.00 s while p50 is unchanged. The HPA scaled 4 to 6 at about 09:32 on `http_requests_in_flight`, after the step, so it is a result and not a cause · Confirmed · W1-Q3, W1-Q5, W1-Q4, W1-Q2.

Explanations still standing, in rank order:
- **H1 (leading):** the pricing host is slow or unresponsive on its side · Likely.
- **H2:** the network path to it broke (NAT, DNS, security group or route) · Assumed.
  - The log message does not say whether the stall was in connect, TLS or first byte.
  - The NAT-gateway list, the CloudTrail EC2 lookup and the EventBridge rule list all came back empty (W2-Q4, W2-Q5).
  - Only one external host appears in the spans, so there is no comparison group.
- **H3:** a runtime change on the catalog-api side with no rollout (config, flag or the pricing client's settings) · Assumed.
  - The pods have been unchanged for 9 days.
  - No ConfigMap was visible to this role, and the onset instant is outside the one affordable log window.
- **H8 (low rank):** the database or queries per request · Assumed, not cleared.
  - DB p95 is flat at 4 ms.
  - The 5 sampled slow requests leave no time for it, but n=5 is below the 20 needed for span-count claims.
  - The call-rate-by-address query returned no series (W1-Q6).

Ruled out:
- **H4, bad deploy:** the last rollout is Helm revision 22 on 2026-10-14 07:58 UTC (chart 2.6.1, image 1.31.2), 9 days before the onset (W1-Q1). Old-versus-new split: not applicable, since no revision changed near the onset. The one revision, ReplicaSet 6b9d7c5f48, runs 6 of 6 pods including the 2 HPA-added ones with 0 restarts. It served normally from 04:20 to 09:30 today (p95 0.39–0.46 s) and failed after 09:31 with no revision change.
- **H5, capacity:** pod CPU is 187–224m, memory 349–391Mi, HPA is at 6 of 12, and p50 and four routes are unchanged (W1-Q2, W0-Q21, W1-Q5). Memory limits and CPU throttling were not read.
- **H6, traffic spike:** 408.9 against 412.4 req/s in the previous window (W1-Q4). The −7d comparison is a gap.
- **H7, reviews-api and cache slow:** client-span p95 is flat (W1-Q6).
- **H9, scheduled job:** no CronJobs in `catalog` and no EventBridge rules returned (W2-Q4). EventBridge Scheduler, SSM maintenance windows and the provider's own timers were not read.
- **H10, node churn:** no restarts, evictions or Warning events from about 09:20, which covers the onset (W1-Q2).

What the service is logging (your question, W2-Q1, 10:05–10:20 UTC):

| Count | Message |
|---|---|
| 25,914 | pricing lookup failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) after 5000ms; serving cached price |
| 611 | pricing cache miss; product shown without price |
| 9 | reviews-api returned 503; reviews block hidden |

The third line is a small unexplained finding. There is no baseline log window, so it cannot be called noise. reviews-api's client p95 and the reviews route p95 are normal, and it is not part of the chain.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Write capability not fully checked: 3 of the 10 simulated actions (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) returned no result (W0-Q8) | None on the evidence; the run is read-only regardless. The report cannot say "read-only confirmed". | Confirm in chat that prod-read is a read-only role (recorded as operator-asserted), or re-run the check once the simulator evaluates those three actions |
| App code and IaC unreadable: `gh api` returns `{}` and no local clone is listed (W0-Q25, W2-Q6) | Any code or Helm-values claim, including that 5000 ms is the configured timeout and that the cached-price fallback is deliberate, rests on the app's own log line only (Assumed beyond that) | Add a read-only GitHub token or a local clone of example-org/catalog-api and example-org/catalog-deploy to environment.md |
| Owner of api.pricing.example.com unknown (vendor or internal), with no status page or contact in environment.md or the profile | The pricing link is at most Likely; vendor status cannot be checked | Name the owner and status page in the profile |
| No −7d baseline for request rate, 5xx share and per-route call rate: queries returned empty (W1-Q4, W1-Q5) | Volume and error comparisons use the previous window only; H6 is ruled out on that basis | Check whether Prometheus keeps 7+ days of these series; add a recording rule |
| Recurrence cannot be classified: the ALERTS pull returned empty and about 5 h of signal came back for a 14-day request (W1-Q7); the 14-day latency pull is over the 12 h quantile cap with no recording rule | The pattern is `unclassified` (Assumed); a repeat or schedule cannot be excluded from history | Read the alert's history in the alerting UI; add a recording rule for p95 |
| Per-pod latency not available: the p95-by-pod query returned empty (W2-Q3) | Local-versus-shared rests on service-wide metrics and `kubectl top` (no outlier) | Add a `pod` label to the latency histogram or a recording rule |
| NAT gateways, EventBridge rules and CloudTrail EC2 writes returned empty replies (W2-Q4, W2-Q5) | H2 cannot be tested; "nobody changed anything" is not concluded | Confirm the role may call ec2:DescribeNatGateways, cloudtrail:LookupEvents and events:ListRules, then re-run |
| Tempo call-rate by server.address returned no series (W1-Q6) | Span count per request cannot be compared, so H8 is not cleared | Enable span metrics or query a TraceQL count per trace |
| Only one Logs Insights window was affordable (10:05–10:20): no baseline before 09:31 and no first-occurrence time for the timeout line | Whether the message existed at a lower rate before the onset is not shown by logs (Tempo shows pricing p95 at 0.21 s before 09:30). The 9 reviews-api 503 lines cannot be classed as noise or new. | Approve another window (about 1.8 GB per 15 min) before 09:31, or use a Deep run with a larger budget |
| Runbook URL on the alert not read; no wiki access configured | Runbook content is not used | Add wiki read access to environment.md |

open items need your input

## To confirm, a human would…

1. Ask the owner of api.pricing.example.com, or read its public status page, whether it was slow, degraded or had an incident from about 09:31 UTC (06:31 local). A matching window supports H1. Healthy, normal latency throughout points to H2 or H3.
2. From a shell inside the cluster network (the run may not exec, curl or port-forward), time DNS resolution, connect, TLS and first byte to that host from a pod. A stall before connect supports H2, and a stall after connect with no response supports H1.
3. Repeat the timing against another external destination from the same pods, and against the pricing host from a pod on another node or availability zone. If every external destination is slow, suspect the egress path (NAT port allocation, packet drops, DNS). If only pricing is slow, suspect the provider.
4. Look at the NAT gateway's port-allocation error and dropped-packet metrics for the cluster's egress path, and at security-group, route-table and network ACL changes around 09:31 UTC. The run's own lookups returned empty replies.
5. Ask the catalog-api team whether any runtime setting changed at about 09:31 UTC (the pricing client's timeout, endpoint or credentials, a feature flag, or the cached-price fallback). Have them read example-org/catalog-api at image 1.31.2 and the Helm values in example-org/catalog-deploy to confirm the 5000 ms setting. A change would support H3.
6. Read the runbook linked from the alert for the owner and escalation route.
7. Ask the product owner whether the cached prices served can be wrong or stale, and whether the 611 product views shown without a price in 15 minutes matter commercially.
8. If a baseline matters, approve a second Logs Insights window ending just before 09:31 UTC to see whether the timeout line existed before the onset. This costs about 1.8 GB of scan per 15 minutes.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Once the owner of api.pricing.example.com identifies and fixes its side, or the network path is repaired, the latency clears. Meanwhile consider a shorter pricing timeout together with a circuit breaker or a negative cache, so a failing dependency costs milliseconds instead of 5 s. The trade-off is serving cached or missing prices more often, which is a product call. |
| Prevention | Consider alerting on the pricing client's own timeout rate or latency, so the page names the dependency and not just service p95. Reconsider scaling the HPA on in-flight requests alone: during a slow dependency it adds pods that each hold more 5-second calls, and it may add load on the pricing host if that host is capacity-limited. |
| Observability gap | Prometheus has no span metrics, no recording rule for p95, no per-pod label on the latency histogram, and 7+ day baselines for rate, 5xx and route rate came back empty. The alert history was not retrievable. Record the pricing host's owner and status page in the service profile. The Insights message field is `msg`, not `message`. |

Every fix or mitigation above should be assessed with `pre-flight` before it is applied, in a separate session. Nothing was changed by this run.

## Cost

14 queries · 1.8 GB of logs · 0 CloudWatch metric requests · no other metered units · about $0.01 in metered charges (1.8 GB of Logs Insights scan; rate from the CloudWatch pricing page, not looked up in this run)
