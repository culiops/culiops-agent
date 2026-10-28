# Investigation: payments-worker prod: pods crash-loop on startup and payment jobs queue up

Run: payments-worker-prod-20261024-1128 · Mode: Fast · Window: 2026-10-24 09:28 to 11:28 UTC (11:28 to 13:28 CEST, UTC+2), the Fast two-hour default because no onset was given. The true onset is 10:52:21 UTC (12:52:21 CEST).
Access: prod-ops: write-capable: s3:PutObject, ecs:UpdateService allowed (simulation). The simulation returned no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack, so write capability for those three is unknown (gap). The boxed warning was shown. arn:aws:eks:us-east-1:111122223333:cluster/prod: no write verbs in payments.

## TL;DR

| Field | Value |
|---|---|
| Cause | Helm release revision 31 (10:52:20 UTC) applied the values change from commit d81e4b7 (#377), which renamed the ConfigMap key LEDGER_API_BASE_URL to LEDGER_BASE_URL. payments-worker 5.2.0 still requires LEDGER_API_BASE_URL, so it logs "required environment variable LEDGER_API_BASE_URL is not set", exits 1 at startup, and all 3 pods crash-loop. · label: Confirmed |
| Weakest link | The tie between the commit and the cluster. It rests on Helm's revision time, the 11-minute lag after the merge, and the live ConfigMap key names. No CI apply-run record was read. · Confirmed. Two things sit outside the chain and are only Assumed: what customers actually see, and whether a second problem sits behind this first fatal check. |
| Impact | 0 of 3 pods available since 10:52:21 UTC, ongoing at 11:28 UTC. The payments-jobs backlog was 5,989 at the 11:25 UTC sample (10 to 30 before the onset), growing about 197 messages per minute. The DLQ is at 0. |
| Severity | SEV1 (suggested) because the core flow "payment capture and refunds processed by payments-worker" has no running consumer. The incident owner decides. |
| Pattern | unclassified · no alarm history, and the SQS 14-day, previous-window and 7-day pulls returned no data · Assumed |
| Recommended action | A human restores the setting the application expects. Either roll the Helm release back to revision 30, or re-add LEDGER_API_BASE_URL next to the new key and release again. Check the choice with `pre-flight` and hand it to a new session with `iac-change-execution`. Options and costs are under Follow-ups. |
| Time to cause | First `Likely` after wave 1 (rollout at 10:52, missing-variable log line). `Confirmed` after wave 2 (the diff and the live key names). Minutes of wall time are not measurable here because the clock call returned nothing. |
| Similar past incidents | no history yet (no `incidents/` or `lessons.md` under the output root) |

## Impact

- **Symptom:** payments-worker containers exit on startup and restart (CrashLoopBackOff, 11 restarts per pod, 149 to 151 BackOff events each). Queued payment jobs are not consumed. (W1-Q1, W1-Q4)
- **Affected:** prod, namespace payments. The Deployment shows 0 of 3 available, with the strategy set to Recreate. All three replicas fail alike, so the cause is shared, not one bad pod or node. The core flow is payment capture and refunds. (W1-Q4, W1-Q6)
- **Backlog:** payments-jobs read 14, 16, 10, 30 and 19 between 10:30 and 10:50 UTC. It reads 74 at 10:55, 1,060 at 11:00, and then rises about 986 per 5 minutes to 5,989 in the bucket starting 11:25. payments-jobs-dlq is 0 throughout. The first elevated sample trails the pod stop by about 3 minutes; the queue metric lags the queue, so the pods date the onset. (W1-Q7)
- **Start and end:** since 10:52:21 UTC (12:52:21 CEST), ongoing at 11:28 UTC (13:28 CEST), about 36 minutes.
- **Measured by:** Deployment availability and queue depth against the level just before the onset. The previous-window and 7-day baselines returned no data, and there is no SLO. The outage and the backlog are Confirmed. The customer-visible effect, delayed versus failed payments, is Assumed because no business counter exists.
- **Third party in the path:** none known. The ledger endpoint is configured by key name only, and its owner is not in the profile.

## Causal chain

1. Trigger: commit d81e4b7 (#377, merged 2026-10-24 10:41:41 UTC, 12:41:41 CEST) renamed the `values-prod.yaml` config key LEDGER_API_BASE_URL to LEDGER_BASE_URL. The value on both lines is identical, and no image, tag or chart-version line changed. It reached the cluster as Helm revision 31 at 10:52:20 UTC, with chart 2.3.1 and app 5.2.0 the same as revision 30. The live ConfigMap `payments-worker-config` now has LEDGER_BASE_URL and no LEDGER_API_BASE_URL. The Recreate rollout stopped the old pods at 10:52:21 and started the new ones at 10:52:33. · Confirmed · W0-Q5, W1-Q1, W1-Q3, W1-Q6, W2-Q1, W2-Q2
2. Mechanism: the container's own log shows the process loading configuration from the environment and then dying with "config: required environment variable LEDGER_API_BASE_URL is not set" (config/load.go:58), exit code 1. The variable is fed through `envFrom` from that ConfigMap, and the process dies before any network call. The first BackOff events came 42 to 45 seconds after revision 31 (10:53:02, 10:53:03, 10:53:05). The first crash line is no longer retained, so those events date the symptom. · Confirmed · W1-Q4, W1-Q5, W1-Q1, W2-Q2
3. Symptom: no consumer is left (0 of 3 available), so payments-jobs fills at its arrival rate of about 197 messages per minute while the DLQ stays at 0. · Confirmed · W1-Q6, W1-Q7. What customers see (delay versus failure) is Assumed.

Ruled out in this run, each with its disproof query:
- **A broken image or app version:** chart and app versions are equal at revisions 30 and 31, and no image line changed. (W1-Q3, W2-Q1)
- **The retry-budget argument from commit 27c4e91 (Helm revision 30, 2026-10-13):** that revision ran 11 days healthy. (W1-Q2, W1-Q3)
- **Out of memory or limits:** the last state is Reason Error with exit code 1, not 137. (W1-Q4)
- **Probe failures:** no Unhealthy events. (W1-Q1)
- **Image pull or scheduling:** the pods were scheduled and started. (W1-Q1)
- **Ledger API outage or credential:** the process exits at config load, before any network call. (W1-Q5) A bad ledger credential behind the config fault is not excluded (see Gaps).
- **A schedule:** no CronJobs, no scheduled EventBridge rules, no Scheduler schedules. (W1-Q9)
- **Node or eviction churn:** only the rollout's own Killing event at 10:52:21, and all replicas fail alike. (W1-Q1, W1-Q4)

CloudTrail returned no write events naming payments resources. The resource filter may hide events that list no resources. (W2-Q3, Likely none)

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| The payments-worker application source is not listed in environment.md (only the deploy repo). | `config/load.go:58` and the app's accepted variable names were not read. "5.2.0 requires LEDGER_API_BASE_URL" rests on the container's own fatal log. | Add the application repo and a local clone under `code:` in environment.md. |
| No log aggregator is listed; only `kubectl logs --previous` (last crash, 11:25:56). | The first crash line is not retained, so the timing leg uses the first BackOff events. The old pods' behaviour before 10:52 is unseen. | Add a Loki or CloudWatch Logs row under `datasources` in environment.md. |
| SQS pulls for the previous window, the 7 days earlier, and 14 days at 1h returned `{}`. The incident window returns points only from 10:30 UTC. | The recurrence class is unclassified. There is no 7-day baseline; "normal" is only the 10:30 to 10:50 sample (10 to 30). | Check the queue's metrics in the console for the last 14 days, and confirm the role may read AWS/SQS history. |
| No CI or apply-run record was read (`gh` and CI are not listed). | The tie "d81e4b7 became Helm revision 31" rests on live key names, Helm's revision time and the 11-minute lag. | Ask the owner of payments-deploy which pipeline run produced revision 31. |
| The ConfigMap's `managedFields` were not returned. | The exact time the ConfigMap changed is not read; Helm's revision time is used. | Ask a cluster admin to check object history if the exact time matters. |
| The IAM simulation gave no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack. | Write capability for those three actions is unknown. | Ask the platform team to review the PlatformOperator policies. |
| No SLO and no business counter for payment capture or refunds. | The customer-visible effect is Assumed. | Add `slo:` or `core_flows` entries to environment.md, or check the payments dashboard. |
| The queue attributes (retention, visibility timeout, redrive policy) were not read. | Whether a long outage risks message expiry or a DLQ redrive is unknown. The DLQ pairing is (unverified). | A human reads the queue attributes in the console. |
| The clone's last-fetch time is unknown (no fetch is allowed). | A commit newer than 10:41 UTC would be invisible. | Ask the owner whether anything landed after 10:41 UTC. |
| The Secret `payments-ledger-auth` was not read (by rule). | A credential problem behind the config problem cannot be excluded. H7 is Ruled out only for the crash. | After the config is fixed, a human watches the first restarted pod. |

open items need your input

## To confirm, a human would…

1. Read the application source at the 5.2.0 tag, or ask its owner, whether payments-worker accepts LEDGER_BASE_URL anywhere. If it reads only LEDGER_API_BASE_URL, the mechanism is confirmed from the code side. If it accepts both, look for another change.
2. Ask the payments-deploy owners which pipeline run produced Helm revision 31. Confirm it rendered d81e4b7 and that nobody edited the ConfigMap by hand.
3. Read payments-jobs' retention period, visibility timeout and redrive policy. Confirmation is a retention far longer than the outage and a redrive receive-count that a drain will not trip.
4. Check a payments dashboard, or ask the payment provider's contact, whether customers see delayed or failed payments. This confirms or corrects the SEV1 reading.
5. After a fix, watch the first restarted pod. The process stops at the first fatal check, so a second configuration or credential error could appear. It can only be seen after a restart, which is a change.
6. Ask the owners of the shared ledger client, the reason given for #377, whether other services read the old key name.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Restore the setting the running application expects. Two options for a human to weigh. (a) Roll the Helm release back to revision 30's values. This is the quickest, and the diff shows revision 31 changed only the key name, but it also undoes the rename the shared ledger client expects, and it restarts the pods again (already at zero consumers). (b) Re-add LEDGER_API_BASE_URL beside LEDGER_BASE_URL in `values-prod.yaml` and release again. This keeps the rename, but it costs a full merge-and-apply cycle (about 11 minutes last time) while the backlog grows about 197 messages per minute. Assess either with `pre-flight` and hand it to a new `iac-change-execution` session with this report path. After recovery, the backlog (5,989 and rising) drains at the workers' capacity; watch ledger API load and the DLQ. |
| Fix | Make the application accept both key names during a transition, then drop the old name once every environment has moved. Cost: a short period with two names to maintain. |
| Prevention | Change a config key and the application that reads it in the same release, or ship the application change first. Add a render-time check in the chart pipeline that every variable the application requires is produced by the rendered chart. |
| Prevention | Consider a rolling update instead of Recreate. Recreate stops every consumer before any new pod is proven healthy. A rolling update would have left two old pods consuming while the first new pod failed. Cost: two config versions run side by side during a rollout, and it needs a readiness signal that fails on this kind of startup error. |
| Prevention | Alert when the Deployment has 0 available replicas for several minutes, and when queue depth or the age of the oldest message keeps rising. No alert fired here; the run started from a chat message. |
| Observability gap | No log aggregator is listed, so the first crash line was lost. There is no SLO or business counter for payment capture, and the queue-age metric is not on a standing panel. |
| Observability gap | The recurrence class is unclassified for lack of history. No earlier occurrence is visible: the previous ReplicaSet ran 11 days and Helm shows one earlier revision. No alert-tuning item applies. |

## Cost

17 queries (tool calls) · 0 GB of logs · 8 CloudWatch metric requests · no X-Ray · about $0.0001 in metered charges (GetMetricData at $0.01 per 1,000 metrics requested; the rate is quoted from memory and not re-checked this run)

