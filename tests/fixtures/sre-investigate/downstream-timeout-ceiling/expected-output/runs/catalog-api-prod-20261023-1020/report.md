
# Investigation: catalog-api prod: p95 latency stuck at about 5 s on GET /products/{id}

Run: catalog-api-prod-20261023-1020 · Mode: Fast · Window: 2026-10-23 09:30 to 10:20 UTC (06:30 to 07:20 America/Sao_Paulo)

## TL;DR

| Field | Value |
|---|---|
| Cause | catalog-api's call to api.pricing.example.com has waited out a 5 s client timeout since 09:31 UTC (06:31 local); `GET /products/{id}` waits on it, then serves a cached price. The delay originates at or behind that host, not in catalog-api. · label: Likely |
| Weakest link | Where the delay starts: the pricing service itself or the network path to it. Nothing readable shows the pricing side or the path (no owner, status route, NAT or DNS data), and for a downstream the label cannot go above Likely. · Likely. The mechanism link (calls wait the full 5000 ms) is Confirmed. |
| Impact | About 20% of product-page requests (25,914 in 15 minutes, 10:05 to 10:20 UTC) wait 5 s and are served a cached price; about 0.5% show the product without a price. Service p95 4.93 s against 0.42 s. 5xx and request rate are flat. Ongoing at 10:20 UTC (07:20 local). |
| Severity | SEV2 because a core flow (product page) is significantly degraded, about 11 to 12 times baseline p95, but still answering with 5xx not elevated. If the owner counts the 7% of all requests that hit a failed pricing lookup as failing, SEV1's 5% line is crossed. The incident owner decides. |
| Pattern | unclassified · Prometheus returned 6 h only and the 14-day pulls were empty; p95 never exceeded 0.46 s in the 5.2 h before onset · gap, no label |
| Recommended action | Reach whoever owns api.pricing.example.com now (the contact route is not recorded) with the 09:31 UTC onset and the 5.00 s client-side timeouts, and ask whether they see slow or hung requests. Meanwhile consider lowering the pricing client timeout or adding a circuit breaker, so product pages fall back to the cached price well before 5 s, at the cost of serving cached (possibly stale) prices to more requests; ask the commerce owner whether serving 20% of product views from cache is acceptable. Do not add capacity to catalog-api for this: pods are idle (about 0.2 CPU core each) and the wait is on the downstream. Assess any change with `pre-flight` first. |
| Time to cause | 2 minutes to the first Likely (10:22 UTC); 4 minutes to the Confirmed mechanism link (10:24 UTC). |
| Similar past incidents | none: no history yet (no incidents/ directory) |

## Impact

Symptom: service p95 4.93 s and p99 4.99 s (median over 09:35 to 10:20) against 0.42 s and 0.89 s in the previous window, and 0.42 s and 0.89 s in the same window 7 days back (W1-Q8, W1-Q9, W1-Q11, W1-Q12). p50 is unchanged at 0.11 s (W1-Q6). `GET /products/{id}` p95 is 4.97 s against 0.44 s 7 days back (W1-Q15, W1-Q16). Request rate is flat at about 410 req/s (409 against 412, W1-Q13) and the 5xx share is flat at about 0.2% (W1-Q14).

Affected: prod, all 6 pods alike (W1-Q5, P1-Q3). Only the product-page route moved; it carries 144 of 410 req/s (W1-Q17). In the 15 minutes to 10:20 UTC, 25,914 log lines report a failed pricing lookup after 5000 ms with a cached price served (W2-Q1), which is about 20% of product-page requests and about 7% of all requests (arithmetic on W2-Q1 and the 10:20 rates in W1-Q17). 611 lines say the product was shown without a price, about 0.5% of product-page requests. 9 lines say reviews-api returned 503 and the reviews block was hidden; whether the 611 and the 9 are new is unknown (no baseline scan). Customer-facing.

Start and status: p95 stepped from 0.40 s to 4.97 s at 09:31 UTC (06:31 local), one minute before the alert's `activeAt` of 09:32:00Z. Ongoing at 10:20 UTC (W1-Q8, W0-Q7). Basis: request metrics against baseline (environment.md names no SLO), Confirmed.

Third party in the path: api.pricing.example.com is the slow peer. Its owner and contact route are not recorded. It shares the domain of the org's internal hosts, which suggests an internal team; unconfirmed. The run cannot contact it.

## Causal chain

Mode is Fast, so the "why it became an incident" part is not run; go deep for it.

1. Trigger: the delay originates at or behind api.pricing.example.com, from about 09:31 UTC · Likely · W1-Q20 (that peer's client-span p95 0.21 s to 5.00 s; reviews-api, database and cache flat), W1-Q21 (0.20 s the same window 7 days back), W1-Q1 to W1-Q5 and W1-Q13 (no deploy, no load change, idle pods). What changed on the pricing side or on the path was not observed.
2. Mechanism: product-page requests wait the full 5000 ms on that call, then fall back to a cached price (or show no price) · Confirmed · W2-Q1 (25,914 lines "pricing lookup failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) after 5000ms; serving cached price" in 15 minutes), W2-Q2 (5 of 5 sampled slow traces are GET /products/{id} with a 5.0003 to 5.0005 s client span to that host, status error), W1-Q20. That the 5 s is a configured client timeout, and that requests then complete from cache (which would explain the flat 5xx share), rest on the log text, not on code that was read: Likely.
3. Symptom: p95 4.93 s and p99 4.99 s service-wide, `GET /products/{id}` p95 4.97 s, 5xx, rate and p50 unchanged · Confirmed · W1-Q8, W1-Q9, W1-Q15, W1-Q6, W1-Q13, W1-Q14.

Consequence, not cause: the HPA scaled catalog-api from 4 to 6 pods at about 09:32 UTC because in-flight requests rose above target (W1-Q3); that is after the 09:31 onset, and the p95 did not move (Likely).

Ruled out:
- Bad deploy or rollout: the last Helm upgrade was 2026-10-14 07:58 UTC (chart 2.6.1, image 1.31.2), nine days earlier; all 6 pods run the same 9-day-old ReplicaSet with 0 restarts (W1-Q1, W1-Q2, W1-Q4, P1-Q3).
- Capacity: the HPA sits at 6 of 12 replicas and each pod uses about 0.2 CPU core (P1-Q4, W1-Q5); p50 and the other three routes are unchanged. CPU throttling series were not queried.
- Traffic spike: request rate flat against the previous window (W1-Q13, W1-Q17). The 7-day-back rate was not pulled.
- A single bad pod: CPU, memory and restarts are uniform across the 6 pods (W1-Q5); per-pod latency was not pulled.

Still standing, in rank order:
1. The pricing service is degraded or down (H6) · Assumed · needs the owner's view (see To confirm).
2. The network path to the pricing host (NAT or egress, DNS) (H5) · Assumed · not tested; the log text "awaiting headers" cannot tell a slow connect from a slow response.
3. A configuration change without a rollout, such as the pricing client's URL or timeout (H8) · Assumed · ConfigMap change times were not read.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Nothing readable from the pricing side: no metrics, status route or owner for api.pricing.example.com | Caps the cause at Likely; H6 stays Assumed | Name the owner and a status or contact route in environment.md; ask that owner whether they see slow or hung requests since 09:31 UTC |
| Network path to the pricing host not tested (NAT gateway id not discovered, no CloudWatch metrics, no DNS check) | H5 stays Assumed and cannot be separated from H6 | A person reads NAT gateway ErrorPortAllocation and PacketsDropCount for 09:25 to 09:40 UTC on the cluster's egress path; add the NAT gateway id to the profile so Deep mode can run it |
| 14-day and 30-day history empty (alert history, in-flight gauge) and p90 empty; Prometheus returned 6 h only | Recurrence is unclassified; "has this happened before" is unanswered | Confirm Prometheus retention and add a p95 recording rule and an alert-history source to environment.md |
| No baseline for the log messages (a second scan of about 1.8 GB needs your approval) | Whether the 611 "shown without price" and 9 "reviews-api 503" lines are new is unknown | Approve a baseline scan of the same 15-minute clock window 7 days back |
| App code, the pricing client's timeout and its fallback were not read (`gh` returned `{}`; no local clone listed) | "5 s is a configured timeout" and "requests complete from a cached price" are Likely, from log text | Add a local clone path to environment.md, or confirm `gh` read access to example-org/catalog-api and example-org/catalog-deploy |
| CloudTrail, EventBridge and Scheduler replies were empty (`{}`) and the CronJob list printed nothing | "No schedule or AWS-side write near 09:31 UTC" is Assumed, not shown | A person repeats the same lookups with the account's own tools |
| Per-pod latency, 7-day-back rate and 5xx baselines, and per-peer call rate were not available | "Pods alike" rests on CPU, memory and restarts; volume is judged against the same day's previous window | Add the pod label and a rate recording rule to the profile |
| Write check: 3 of 10 fixed actions returned no row; the Kubernetes binding grants get/list/watch on everything including Secrets | Read-only is shown for 7 AWS actions only | Use the built-in `view` ClusterRole and a tighter AWS read policy for incident work |
| No Grafana, Sentry, ticket system, wiki, SLO or business counters in environment.md | No deploy annotations, error-tracker issues or SLO burn; the alert's runbook was not read | List the backends in environment.md |

Open items need your input.

## To confirm, a human would…

1. Ask the owner of api.pricing.example.com (and check its public status page if it is a vendor) whether its latency or availability changed at 09:31 UTC. A degradation starting at 09:31 UTC confirms H6; a healthy pricing service points to H5.
2. Read the NAT gateway metrics ErrorPortAllocation and PacketsDropCount, and DNS resolution errors, for the cluster's egress path around 09:31 UTC. Non-zero values aligned with the onset would confirm H5; baseline values would refute it.
3. Read the pricing client's timeout and fallback code in example-org/catalog-api at image 1.31.2, and the Helm values for the pricing URL and timeout in example-org/catalog-deploy. A 5000 ms timeout with a cached-price fallback confirms the mechanism details; a value or URL changed near 09:31 UTC would make H8 the cause.
4. Compare the ConfigMap change times (managed fields) in namespace catalog with 09:31 UTC.
5. Ask the commerce owner how stale the cached price can be and whether it is acceptable to show it for about 20% of product views. This decides how urgent the mitigation is.
6. Run the same Logs Insights count for the same clock window 7 days back to see whether the "shown without price" and "reviews-api 503" lines are new.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Once the pricing owner has a cause, fix it there. In catalog-api, consider a shorter pricing timeout with a circuit breaker so slow pricing costs a few hundred milliseconds instead of 5 s; the cost is more requests served from cached, possibly stale, prices. Assess it with `pre-flight` before applying, in a separate session. |
| Prevention | Consider alerting on the pricing client span's p95 and on the share of requests logging a failed pricing lookup, which would have shown this at 09:31 UTC instead of waiting for the 10-minute service p95 rule (the page came about 11 minutes after the onset). |
| Prevention | Consider whether the HPA should scale on in-flight requests when the wait is on a downstream: it added 2 pods that did not help, at the cost of extra pods and extra load on the pricing host if that host is struggling. |
| Observability gap | No per-peer call-rate series (W1-Q22 empty), no p90, no 14-day history, no recording rule for p95, no pod label in the latency series, and no record of who owns api.pricing.example.com. Recurrence was unclassified because of this. |

## Cost

42 queries · 1.8 GB of logs · 0 CloudWatch metric requests · about 47 GB inspected by Tempo (no cost model) · about $0.01 in metered charges (1.8 GB at the Logs Insights list price of $0.005 per GB, not re-checked this run)
