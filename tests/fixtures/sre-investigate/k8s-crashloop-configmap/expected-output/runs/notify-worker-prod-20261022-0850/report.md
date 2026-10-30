# Investigation: notify-worker prod: all workers crash-looping after a config key rename, outbound email queue not drained

Run: notify-worker-prod-20261022-0850 · Mode: Fast · Window: 2026-10-22 07:44 to 08:50 UTC (07:44 to 08:50 local; zone is UTC) · Onset: 2026-10-22 08:14:21 UTC (08:14:21 local)
Access: prod-read: read-only confirmed (simulation): none of the broad write actions came back allowed; only 7 of the 10 requested actions returned a row (all implicitDeny), and 3 returned no row (write capability only partly checked, gap) · arn:aws:eks:us-east-1:111122223333:cluster/prod: no write verbs in notify

## TL;DR

| Field | Value |
|---|---|
| Cause | The prod values file renamed the config key `NOTIFY_SMTP_RELAY_HOST` to `SMTP_RELAY_HOST` (commit 3f9a1c2, #214). Helm revision 12 applied it at 08:14:20 UTC. notify-worker 3.8.1 still requires `NOTIFY_SMTP_RELAY_HOST`, so every new pod exits at startup and crash-loops. · label: Confirmed |
| Weakest link | The old-revision side of the old-against-new split. There are no per-revision logs, so it rests on the absence of events and a flat queue. The mechanism does not depend on it, because the crash log names the missing variable and the live ConfigMap lacks it. Separately, "emails are not being delivered" is Likely: it is inferred from the unconsumed queue, with no sent-mail signal. |
| Impact | All 3 workers have been down since 08:14:21 UTC and the outage is ongoing. The outbound queue held 9,660 messages at 08:45 and grows by about 318 per minute. The DLQ is at 0. |
| Severity | SEV1 because a customer-facing core flow (transactional email) has no worker available. The incident owner decides. |
| Pattern | unclassified · no alarm history, and the 14-day pull returned 2 of 336 hourly points · Assumed. Shape: step. |
| Recommended action | A human should restore the variable name the running app expects. Either revert the rename in the prod values, or roll the release back to revision 11. Check it with `pre-flight` first, then decide what to do with the stale backlog (see Follow-ups). |
| Time to cause | Likely after wave 1 (8 calls). Confirmed after wave 2 (5 calls). Wall-clock minutes were not measured in this simulation. |
| Similar past incidents | no history yet (`incidents/` does not exist) |

## Impact

- **Symptom:** All 3 notify-worker pods are in CrashLoopBackOff (0/3 ready, 11 restarts each; W1-Q1). `notify-outbound` visible messages went 16 (08:10), 120 (08:15), 1,710 (08:20), 9,660 (08:45), about +318/min. The DLQ stayed at 0 (W1-Q8).
- **Affected:** prod only, 3 of 3 replicas. The core flow is transactional email (order confirmations, password resets), which is customer-facing. That emails are not going out is Likely: the queue is not being consumed and no worker is available, but there is no sent-mail counter.
- **Since / ongoing:** 08:14:21 UTC (08:14:21 local). The old pods were stopped then, and the first BackOff came at 08:15:02. Still ongoing at 08:50.
- **How measured:** The magnitude is Assumed. environment.md names no SLO and no APM or load-balancer metrics, so queue depth and pod availability are the proxies. Pod availability of 0/3 is Confirmed.
- **Third party in the path:** none identified for the failure. The SMTP relay is on the send path but is not involved in the crash. No contact route is recorded for it.

## Causal chain

1. **Trigger:** The commit 3f9a1c2 "align config key names with the shared SMTP chart (#214)" (author date 08:03:41 UTC) removes the key `NOTIFY_SMTP_RELAY_HOST` from `charts/notify-worker/values-prod.yaml` and adds `SMTP_RELAY_HOST`. Other keys are unchanged. Helm revision 12 was deployed at 08:14:20 UTC with the same chart (1.8.0) and the same image (3.8.1) as revision 11. The live ConfigMap `notify-worker-config` holds `SMTP_RELAY_HOST` and lacks `NOTIFY_SMTP_RELAY_HOST`, which ties the commit to what actually ran. · Confirmed · W0-Q7, W2-Q4, W1-Q6, W2-Q3
2. **Mechanism:** The Deployment uses the Recreate strategy. At 08:14:21 the old ReplicaSet went from 3 pods to 0, and the new one (`5c8d7b9f4c`) started at 08:14:33-08:14:36. Each new pod's previous-container log shows `config: required environment variable NOTIFY_SMTP_RELAY_HOST is not set` (config/load.go:58), 19 ms after start. The last state is Reason Error, exit code 1 (not OOMKilled). Kubelet back-off events started at 08:15:02-08:15:05 and reached 149-151 per pod by 08:49. · Confirmed · W2-Q2, W2-Q1, W1-Q2, W1-Q5
   - **Old against new:** The new revision (RS `notify-worker-5c8d7b9f4c`, Deployment revision 7) has 3 of 3 pods crash-looping, each with the mechanism in its own previous-container log. The old revision (RS `notify-worker-7f6b8c5d2e`, Deployment revision 6, 15 days old) shows 0 BackOff or Unhealthy events in the retained events (about 07:50 to 08:14:21). Its only event is the normal Killing at 08:14:21, and the queue stayed at 7-27 messages from 07:50 to 08:10 (W1-Q2, W1-Q8). The onset is not earlier than the rollout: the backlog was 16 at 08:10 and the first BackOff came at 08:15:02. The deploy is therefore kept in, not cleared.
3. **Symptom:** 0 of 3 pods are available. The queue is not drained: backlog 16 (08:10), 120 (08:15), 9,660 (08:45), DLQ 0. · Confirmed · W1-Q1, W1-Q4, W1-Q8. Email non-delivery follows from this and is Likely.

Timeline (times are UTC; local time is identical):

| UTC | Event | Query |
|---|---|---|
| 08:03:41 | Commit 3f9a1c2 (author date) | W0-Q7 |
| 08:14:20 | Helm revision 12 deployed | W1-Q6 |
| 08:14:21 | Old ReplicaSet scaled to 0, old pod killed | W1-Q2 |
| 08:14:33-08:14:36 | New pods scheduled and first started | W1-Q2 |
| 08:15:02-08:15:05 | First BackOff on each new pod | W1-Q2 |
| 08:15 | Queue backlog 120, up from 16 at 08:10 | W1-Q8 |
| 08:47:56 | Latest crash of one pod: the fatal config line | W2-Q2 |
| 08:50 | Operator report | chat |

Ruled out (each with the query that showed it):
- **Image pull or scheduling:** the pods were Scheduled and Started, with no FailedScheduling or ErrImagePull events (W1-Q2, W2-Q1).
- **OOM or resource kill:** the last state is Reason Error with exit code 1, not OOMKilled or 137, and there are no OOM events (W2-Q1, W1-Q2).
- **Probe failures:** no probes are defined and there are no Unhealthy events (W1-Q5, W1-Q2).
- **Dependency failing at startup (SMTP relay, SQS, `notify-smtp` secret):** the process dies at config load before any network call, and the secret reference resolved because the container started (W2-Q2, W1-Q2).
- **Scheduled job or node churn:** no CronJob was listed and there are no node events. The onset is 1 s after the Helm upgrade (W1-Q7, W1-Q2, W1-Q6). The empty CronJob listing is unverified, so the Helm timing and the logged mechanism carry this ruling.

No other hypothesis is still standing.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Write capability only partly checked: 3 of the 10 simulated actions (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) returned no row, and the reply held 3 unrequested rows (W0-Q2) | "Read-only" holds for 7 actions only. No claim about the cause changes. | Re-run the simulation by hand with the fixed list, or confirm with the IAM owner that the role is read-only. |
| No log backend in environment.md; only the current and previous container logs | The first crash's log and the old pods' logs are gone. There are no log counts per revision, so the old side of the split rests on events and queue depth. | Add a log backend (a CloudWatch log group or a Loki instance) to environment.md. |
| No CloudWatch datapoints outside 07:50-08:45 UTC today (W1-Q8, W2-Q5) | No baseline, no -7d comparison, no recurrence statistics. The class is `unclassified`. | Check in the console whether the SQS queue metrics exist for earlier ranges. Ask the metrics owner whether retention or queue activity explains it. |
| No SLO, APM or load-balancer request metrics, and no sent-mail counter | Impact magnitude is Assumed. "Emails are not going out" is Likely. | Name an SLO or a sent-mail counter in environment.md, or look at the mail relay's own send log. |
| ConfigMap write time not returned (W2-Q3) | The apply time rests on Helm revision 12 (08:14:20), not on the object's own history. | Read the object's managed-fields metadata with a binding that returns it. |
| Producer send rate not pulled | The backlog growth cannot be split between producer volume and missing consumers. Drain time cannot be estimated. The crash cause is unaffected. | Pull the sent and deleted counts for `notify-outbound` over the last day. |
| The pipeline run that applied commit 3f9a1c2 is not read (workflow name unknown, not guessed) | The commit is tied to the release by the ConfigMap keys and Helm timing, but the actor and run are unknown. | Ask the owner of PR #214 (platform-dev) for the pipeline run of about 08:14 UTC. |
| App source `example-org/notify-worker` not read | The requirement for `NOTIFY_SMTP_RELAY_HOST` at 3.8.1 is shown by the crash log, not by code at the deployed ref. | Read `config/load.go` at the 3.8.1 tag. |

Open items need your input.

## To confirm, a human would…

1. Look at the mail relay's own send log or dashboard and check that nothing has been sent since about 08:14 UTC. That would turn "emails are not going out" from Likely to Confirmed. Sends continuing through some other consumer would refute it.
2. Open `config/load.go` around line 58 at the 3.8.1 tag and confirm it requires `NOTIFY_SMTP_RELAY_HOST` with no fallback to `SMTP_RELAY_HOST`. Also ask the owner of PR #214 which app version, if any, is meant to read the new name.
3. Ask the owner of PR #214 which pipeline run applied the change at 08:14 UTC, to date the trigger by its own record.
4. Check the queue's retention, visibility and DLQ redrive settings, and the sent rate. Together these tell whether the backlog can be drained safely once consumers return, or whether older messages (such as password resets) should be dropped.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Restore the variable name the running app expects. Revert the rename in the prod values so the chart again provides `NOTIFY_SMTP_RELAY_HOST`, or roll the release back to its previous revision (11). A rollback also reverts anything else released in revision 12; the diff shows only this key. Either route replaces all pods again. Check it with `pre-flight`, then hand it to `iac-change-execution` in a new session with this report as context. |
| Fix | Plan the backlog. About 10,000 messages are waiting and the count grows by about 318 per minute. Once workers are back they will send everything queued. Decide up front whether time-sensitive mails (password resets, order confirmations) that are an hour or more old should still go out, and check that queue retention and DLQ settings do not drop or redrive them unexpectedly. |
| Fix (longer term) | Align the app and the shared SMTP chart: ship an app version that reads the new key name, or both names, and test it before the chart renames the key. The cost is a release of the app before the chart change, and a time window where both names must be accepted. |
| Prevention | Check in CI or on a staging rollout that every environment variable name the app requires exists in the rendered config, and have the rollout reach Ready in staging before prod. |
| Prevention | The Recreate strategy removed every old pod before any new pod proved healthy. Consider a rolling update with a readiness probe, so a bad revision stalls while old pods keep consuming. The cost is two versions running together for a short time, which is only acceptable if the worker tolerates overlap. |
| Observability gap | This was reported by a person. Consider alerts on queue depth or age and on replicas unavailable for more than a few minutes, and a sent-mail counter. |
| Observability gap | There is no log backend, so a crash loop's first crash is not readable. Adding one would keep the early logs and allow per-revision counts. |
| Access | The Kubernetes identity used can read all resources including Secrets. Consider the built-in `view` role for incident work. |

## Cost

20 queries · 0 GB of logs · 14 CloudWatch metric requests · no other metered units · about $0 in metered charges
