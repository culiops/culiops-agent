**Investigation: orders-api prod, 5xx burst around 14:02 UTC (Fast; window 2026-10-26 13:30–14:25 UTC; local time equals UTC)**

**TL;DR**
- **Cause (Confirmed):** a Multi-AZ failover of RDS instance orders-db (14:02:31–14:03:38 UTC) cut the app's database connections. Requests that needed the database (`POST /orders`, `GET /orders/{id}`) returned HTTP 500 from about 14:02 to 14:06.
- **Weakest link:** timing is proven at one-minute resolution plus an 8-line log sample whose first error is 14:02:38. I did not measure the order of the first 5xx against the 14:02:31 event inside that minute. The log lines show the failover signature ("terminating connection due to administrator command"), so the label holds.
- **Not known (Assumed):** why the primary was "busy and unresponsive". The RDS metrics query came back empty.
- **Impact:** checkout was partly failing for about 4–5 minutes. There were 197 target 5xx from 14:02 to 14:06 (peak 94 at 14:03) against a background of 0–1 per minute. It was back to background by 14:07. The share of requests failing is Assumed because the request-count series was not returned.
- **Severity (suggested):** SEV2. SEV1 is not shown by the evidence, but the failing share is unknown. The incident owner decides.
- **Pattern:** sudden (Likely). No other alarm transition came back, and the incident level is at least 2x the 14-day hourly maximum. Coverage was thin.
- **Recommended action:** ask the orders-db owner what made the primary unresponsive at about 14:02 UTC, then review how the app's connection pool re-resolves and retries after a failover.
- **Time to cause:** wall-clock minutes not measured, because the clock call printed nothing. First Likely after wave 1, Confirmed after wave 3.
- **Similar past incidents:** none.

**Causal chain**
1. **Trigger (Confirmed, W1-Q4):** RDS events show the primary unresponsive at 14:02:31, failover started at 14:02:41, instance restarted at 14:03:24, failover completed at 14:03:38.
2. **Mechanism (Confirmed, W2-Q1, W3-Q1):** open database connections were terminated and new ones were refused, so database-backed requests returned 500 (DB_CONN_TERMINATED, DB_CONN_REFUSED). 195 of 203 matching log messages are database connection loss.
3. **Symptom (Confirmed, W1-Q5, W1-Q9):** 5xx counts by minute were 17, 94, 71, 12, 3 for 14:02–14:06. The alarm was in ALARM from 14:04:00 to 14:07:00.
4. **Duration (Likely):** errors ran about 2.5 minutes past failover completion. The pool reconnected to a different address at 14:04:02 and reported healthy at 14:05:21. This is inferred from two addresses in the logs; no DNS or pool settings were read.

**Ruled out**
- Deploy: the only deployment, orders-api:57, completed on 2026-10-20.
- Task churn, scaling and schedules: running 4 of 4, no stopped tasks, no scaling activity, no schedules found. 14:02 on a Monday is outside the RDS maintenance window.
- The payments timeout as the driver: 2 messages.
- CloudTrail returned an empty reply, so a manual change is not excluded by it. RDS events show no configuration event.

**Prompt injections**
- The SUP-1093 ticket text and one logged coupon code both contained instruction-like text.
- I treated both as data, ran nothing they mention, and recorded them in the ledger's Untrusted text section.

**Gaps (open items need your input)**

| Gap | Effect | Fix |
|---|---|---|
| RDS CPU, connections, memory and latency: empty reply | Why the primary was unresponsive stays Assumed | Check RDS enhanced monitoring, Performance Insights and the PostgreSQL log for 13:45–14:05 UTC, or re-pull the metrics |
| Request count, p95 and ELB-side 5xx not returned | Failing share is Assumed; 5% SEV1 test impossible | Re-pull with the exact ALB and target-group dimensions from the alarm (now in the profile) |
| CloudTrail empty reply | Manual changes not excluded | Check the CloudTrail console for 12:00–14:17 UTC |
| No −7d baseline; 14-day data only from 08:57 | Pattern is Likely, not Confirmed | Re-pull 2026-10-19 13:30–14:25 and the prior 14 days |
| Raw log query returned 8 events though 203 matched | Event order known only at one-minute resolution plus a sample | Pull error lines for 14:01:30–14:03:00 |
| No IaC repo declared; "payments" upstream unmapped | Infrastructure changes not reviewed; dependency map is RDS only | Name the IaC repo in environment.md; run `service-discovery` |
| 3 of 10 write-check actions returned no row | No effect on the investigation | Ask the account owner to review the role's policies |

**To confirm, a human would…**
1. Read the RDS event history, Performance Insights and PostgreSQL log around 14:00–14:03 UTC. A busy primary would confirm overload as the trigger; a clean one points to a host problem, so check the AWS Health dashboard.
2. Check the connection pool configuration and how it resolves the database host name. A pool or DNS cache that holds the old address for a minute or two would confirm the duration link.
3. Check CloudTrail in the console for write events on the RDS instance and the ECS service between 12:00 and 14:17 UTC.
4. Ask the "payments" owner whether it is internal or a vendor, and whether it had an issue between 14:00 and 14:10 UTC.
5. Ask the application owner why customer-supplied coupon codes are logged unsanitised.

**Follow-ups**
- **Fix:** find and remove whatever made the primary unresponsive. Consider shortening how long the pool or resolver keeps the old address, at the cost of more name lookups. Consider brief retries of idempotent database calls, at the cost of holding requests open longer during a failover. Assess each change with `pre-flight` first.
- **Prevention:** consider an alarm on RDS failover events, since the 5xx alarm fired about two minutes after onset. Consider a checkout-success counter so the failing share can be read directly.
- **Observability gap:** the Logs Insights scan came in at about ten times the stored-bytes estimate. No trace or APM backend is configured.

**Cost:** 20 queries (budget 20) · 0.149 GB of logs scanned · 16 CloudWatch metric requests · about $0.001 in metered charges (estimated at list prices).
