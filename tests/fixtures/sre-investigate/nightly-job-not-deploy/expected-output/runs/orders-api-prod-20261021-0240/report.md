# Investigation: orders-api prod: 5xx bursts at 02:00 UTC from lock waits while the nightly reconcile job runs

Run: orders-api-prod-20261021-0240 · Mode: Fast · Window: 2026-10-21 01:30 to 02:40 UTC (10:30 to 11:40 JST) · Onset: 02:01 UTC (11:01 JST)
Access: prod-read: no write action allowed in the 7 actions the simulation answered (all implicitDeny); write capability unknown (gap) for the other 3 of the 10 (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack returned no row). This is not "read-only confirmed".

## TL;DR

| Field | Value |
|---|---|
| Cause | The nightly reconcile job (EventBridge rule `orders-reconcile-nightly`, 02:00 UTC) locks about 1.18 million `orders` rows for about 20 minutes. orders-api writes (`POST /orders`, `PATCH /orders/{id}`) wait out the 50-second database lock-wait limit and return HTTP 500. · label: Likely |
| Weakest link | The mechanism: the job's locks are what orders-api waits on · Likely. No database-side view shows the blocked statements, and only 6 error lines were sampled, so the lock-wait share of the 438 5xx is not counted. The trigger (schedule, RunTask 02:00:02) and the symptom (5xx counts) are Confirmed. |
| Impact | 438 target 5xx from 02:01 to 02:19 UTC (11:01 to 11:19 JST), peak 55/min at 02:04. Over: the alarm has been OK since 02:12 UTC and there is no datapoint after 02:19. The failing share of requests is not measurable (RequestCount did not return). |
| Severity | SEV2 (suggested) because a prod service behind a public-named ALB returned up to 55 5xx/min for about 19 minutes, with both core flows among the failures. SEV1 could not be shown because the failing share is unknown. The incident owner decides. |
| Pattern | scheduled · six alarm episodes within +/-15 min of 02:04 UTC in 14 days, 5xx peak in the 02:00 hour on 14 of 14 prior days, and the burst follows the job's start time · Confirmed |
| Recommended action | Do not roll back the release: the same burst happened on every earlier revision. Ask the reconcile job's owner and the database owner to confirm which session holds the locks for 02:00 to 02:20 UTC, then change how the job reads the orders table (see Follow-ups). Assess any change with `pre-flight` and apply it in a separate session. |
| Time to cause | About 8 minutes of run time (nominal clock) to the first Likely (wave 2). Confirmed not reached. |
| Similar past incidents | none (no history yet). This is at least the 15th daily burst in the data (10-07 to 10-21) and the 6th alarm in 14 days, so a permanent fix is the first follow-up. |

## Impact

- **Symptom.** 438 target 5xx between 02:01 and 02:19 UTC, peaking at 55/min at 02:04. The 70 minutes before had 3 (W1-Q3). The same time window a week earlier had 459, peaking at 57/min at 02:09 (W1-Q3).
- **Sampled failures (W2-Q5).**
  - HTTP 500 `ER_LOCK_WAIT_TIMEOUT` after about 50 s on `POST /orders` ("insert order_lines") and `PATCH /orders/{id}` ("update orders set status"). These are the two core flows in `environment.md`.
  - One 502 on `POST /orders`: `ECONNRESET` calling the payments service.
  - One `GET /orders` that returned 200 after 8.1 s.
- **Scope.** Prod orders-api behind ALB prod-public, all 6 tasks, one target group.
- **Not measured.** Failing share of requests, because RequestCount did not return (gap). Whether the ALB is customer-facing is `Assumed` (inferred from its name).
- **Since and ongoing.** Onset 02:01 UTC. Not ongoing: last non-zero minute 02:19, none from 02:20 to 02:40. `HTTPCode_Target_5XX_Count` is reported only when non-zero, so absence means 0.
- **Basis.** ALB target 5xx counts against the previous window and a week earlier (W1-Q3), Confirmed for the counts. The failing share is `Assumed`.
- **Third party in the path.** None known. A payments service is called via an env var named `PAYMENTS_URL`; its owner and contact are not in the profile.

## Causal chain

1. **Trigger:** the rule `orders-reconcile-nightly` (`cron(0 2 * * ? *)`, UTC, ENABLED) starts the `orders-reconcile:7` task. RunTask was at 02:00:02, the container ran 02:00:09 to 02:19:52 (exit 0), and the job logged "locking orders rows created 2026-10-20 (estimated 1,184,000 rows)" with `SELECT ... FOR UPDATE`. It committed all 1,184,212 rows at 02:19:48. · Confirmed · W1-Q6, W2-Q2, W2-Q3, W2-Q4, W3-Q1
2. **Mechanism:** the job's row locks make orders-api writes wait past the roughly 50 s lock-wait limit. They fail with `ER_LOCK_WAIT_TIMEOUT`, which becomes HTTP 500. · Likely · W2-Q5, W3-Q1
   - The first sampled error is at 02:01:13 after a 50.0 s wait, so waiting began at about 02:00:23. That is 11 s after the job logged its start.
   - The burst ends at 02:19, as the job commits at 02:19:48.
   - On the two days the job started late, the burst moved with it. On 10-14 the job started at 02:05:02 and the burst began at 02:06. On 10-16 it started at 02:01:02 and the alarm fired at 02:05 instead of 02:04. On all six alarm days the alarm time equals the job start plus 4 minutes (W1-Q3, W1-Q5, W2-Q4).
   - This is capped at Likely: the database was not queried for the lock holder, and the lock-wait share of the 438 5xx was not counted.
3. **Symptom:** 438 target 5xx from 02:01 to 02:19 UTC, with `POST /orders` and `PATCH /orders/{id}` failing. · Confirmed · W1-Q3, W2-Q5

**Ruled out**
- **The release (task definition `orders-api:42`, rollout 01:22:07 to 01:31:40 UTC): Ruled out.**
  - The rollout finished 29 minutes before the onset.
  - Revision 42 had 1 target 5xx between rollout completion and the onset (W1-Q3).
  - The same 02:00-hour burst occurred on every one of the 14 earlier days, before revision 42 existed (W1-Q4):

    | Revision era | 5xx in the 02:00 hour |
    |---|---|
    | before revision 40 was registered (10-07) | 88 |
    | revision 40, 10-08 to 10-14 | 421, 61, 117, 386, 74, 52, 455 |
    | revision 41, 10-15 to 10-20 | 133, 398, 69, 104, 412, 96 |
    | revision 42, first run (10-21) | 438 |

  - The revision-in-service dates come from registration and UpdateService times (W2-Q1, W2-Q4), not from per-task counts.
  - The release diff was not read (the `gh` compare reply was empty). That does not change this verdict, because the failure predates the release.
- **A fixed-clock database backup or maintenance window: Ruled out.** The burst moved with the job's start (10-14, 10-16). The window itself could not be read.
- **Task, node or scaling churn: Ruled out.** There were no stopped tasks, no ECS service events after 01:31:40, and 6 of 6 tasks were running and healthy (W1-Q1, W1-Q2, W1-Q6). CPU and memory saturation were not read.

**Still open, in rank order**
1. Database lock contention as the mechanism (H3): Likely, as above.
2. The HTTP client library bump in the release (#1185) causing payments resets (H7): Assumed. One 502 was sampled, and the 29 minutes before the onset on revision 42 had 1 5xx in total.
3. A traffic spike or unknown daily caller (H5): Assumed. RequestCount is missing and nothing in the data points to volume.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| The write-check answered 7 of 10 actions; 3 returned no row (W0-Q2) | The access line cannot say "read-only confirmed". The run stayed read-only. | Ask the owner of the SSO permission set to confirm it is ReadOnlyAccess or tighter. |
| Aurora `orders-db` not listed (describe-db-clusters returned `{}`); no database metrics or lock view | The lock holder cannot be identified from the database side, so the mechanism stays Likely. The backup window was not read. | Confirm the cluster identifier and region with the owner and add it to `environment.md`. A database owner can read lock waits and Performance Insights for 02:00 to 02:20 UTC. |
| The golden-signal batch returned only the 5xx series; RequestCount, `HTTPCode_ELB_5XX_Count`, healthy and unhealthy host counts and p95 latency had no entry and no message (W1-Q3) | The failing share (the SEV1 test), the app-versus-ALB comparison, unhealthy targets and latency are unread. A traffic hypothesis cannot be tested. | Read RequestCount, TargetResponseTime and UnHealthyHostCount for 01:30 to 02:40 UTC in the CloudWatch console, or ask whether `prod-read` may call GetMetricData for them. |
| `gh` compare of 2026.10.14-2...2026.10.21-1 returned `{}` (W2-Q1) | Whether the release touches the order-write path or the payments client is unknown (it affects H7, not the H2 verdict). | Read the diff of PRs #1182, #1185 and #1187 on GitHub. |
| Environment variable values are not read by design; only names were compared across revisions 40, 41 and 42 (identical) | A changed value, such as a pool size, would not be visible. | The service owner compares DB_POOL_SIZE and the reconcile settings across revisions. |
| No tracing, error tracker, SLO, core-flow counter or IaC repo in `environment.md`; no `timezone` (answered in chat as Asia/Tokyo, UTC+9) | Per-endpoint latency, span counts, issue first-seen and IaC history could not be checked. | Connect these in `environment.md`, and add `timezone: Asia/Tokyo`. |
| Alarm history holds about 14 days (oldest item 10-08, although 30 were asked); Application Auto Scaling replies were empty; CloudTrail shows no UpdateService for revision 40 on 10-07 although it was registered that day | The pattern rests on 6 alarm episodes plus the hourly series and 15 RunTask events. "No scaling change" is `Assumed`. The revision in service on 10-08 to 10-13 is inferred (affects only the H2 table). | Ask the owner whether the service has a scalable target, and check the pipeline's deployment history. |
| The Logs Insights scan was about 16x the stored-bytes estimate (0.481 GB reported against 0.030 GB); the lock-wait share of the 438 5xx was not counted within the 2 GB Fast budget | Only 6 lines were sampled, which caps the mechanism link. | Raise the Fast log budget, or run an error-code count for 02:00 to 02:20 UTC. |

Open items need your input.

## To confirm, a human would…

1. Ask the database owner to open the engine's lock-wait view or Performance Insights for 02:00 to 02:20 UTC. If the sessions blocking the `order_lines` and `orders` statements belong to the reconcile job's transaction, the mechanism is confirmed. If another session holds the locks, the cause is refuted.
2. Ask the reconcile job's owner whether `SELECT ... FOR UPDATE` over the previous day's orders is one transaction for the whole run (the log says "committed 1184212 rows" once at the end), and what the values of the batch-size and lock-mode settings are (only their names were read).
3. Ask the payments service's owning team whether connection resets were seen at 02:07:30 UTC, and since the 01:31 rollout. A rise only on revision 42 would make the client library bump (H7) a separate, release-related problem.
4. Read RequestCount for the incident window in the CloudWatch console to compute the failing share of `POST /orders` and `PATCH /orders/{id}`. That settles SEV1 versus SEV2.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Make the nightly reconcile job stop blocking order writes. Options: commit in the 5,000-row batches it already reads instead of holding locks across about 1.18 million rows, read the previous day's rows without row locks, or move the run to a quieter period. The cost is a longer run, or a weaker consistency guarantee if rows change between batches, which the job's owner has to accept. This is the permanent fix and comes first: the burst has recurred daily since at least 10-07, with 6 alarm episodes in 14 days. Assess the change with `pre-flight` and apply it through `iac-change-execution` in a new session, with this report as context. |
| Fix | Consider whether `POST /orders` and `PATCH /orders/{id}` should give up sooner than the 50-second database lock wait, with a retry. The cost is that errors show earlier and more retries reach the database during the job. |
| Prevention | Put the reconcile schedule and this pattern in the alarm description and the on-call runbook, so a page at 11:00 JST is not read as a release regression (it was this time). The alarm already fires only on larger days (6 of 14), so a threshold change is not needed for noise, but the page carries no pointer to the job. |
| Observability gap | RequestCount, latency and healthy-host counts were not readable in this run. There is no database metric or lock view (Aurora not listed). There is no tracing, no error-code counter metric, and no core-flow counter. The Logs Insights size estimate runs 16x low for `/ecs/orders-api`. `environment.md` has no timezone, budgets or SLO. Running `service-discovery` for this service would document the reconcile job and the data store dependency. |

## Cost

18 queries · 0.481 GB of logs scanned · 19 CloudWatch metric requests · no other metered units · about $0.003 in metered charges (my estimate from CloudWatch list prices, not checked against a bill)
