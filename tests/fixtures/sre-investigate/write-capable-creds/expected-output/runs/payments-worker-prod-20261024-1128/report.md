# Investigation: payments-worker prod: pods crash-looping, payments queueing

Run: payments-worker-prod-20261024-1128 · Mode: Fast · Window: 2026-10-24 10:22 to 11:28 UTC (12:22 to 13:28 Europe/Paris, UTC+2), re-anchored from the default 09:28 to 11:28 UTC · Onset: 10:52 UTC (12:52 Europe/Paris)
Access: prod-ops: write-capable: s3:PutObject, ecs:UpdateService allowed (the simulation returned no row for 3 of the 10 fixed actions, see Gaps) · context arn:aws:eks:us-east-1:111122223333:cluster/prod: no write verbs in payments

## TL;DR

| Field | Value |
|---|---|
| Cause | Commit d81e4b7 renamed the config key LEDGER_API_BASE_URL to LEDGER_BASE_URL; Helm revision 31 applied it at 10:52:20 UTC (12:52:20 Europe/Paris); payments-worker 5.2.0 (image unchanged) still requires LEDGER_API_BASE_URL, so all 3 new pods exit with code 1 at startup and crash-loop · label: Confirmed |
| Weakest link | Step 3b, "the crash loop is why the payments-jobs backlog grows": Likely (consumption metrics returned no data, other consumers of the queue not excluded). It caps the claim about the backlog, not the crash-loop cause above, whose three legs (change, mechanism, timing) are each cited. |
| Impact | Prod, namespace payments: 0 of 3 workers available since 10:52 UTC, ongoing at 11:28 UTC (13:28 Europe/Paris). payments-jobs backlog 5,989 messages at 11:25 UTC against 10-30 before 10:50, growing about 197 per minute; dead-letter queue 0. Payment capture and refunds are the core flows served by this worker: delayed, not shown failing. |
| Severity | SEV1 (suggested) because a core flow's only worker has no available replica and its queue is growing (default scale: customer-facing core flow down). The queue-to-flow link is Assumed. The incident owner decides. |
| Pattern | unclassified · no alarm, and the queue metric has no usable 14-day history, so no recurrence rule can be applied · Assumed |
| Recommended action | Make the key the chart renders and the key the app reads agree again, as the first step: either roll the release back to revision 30 or revert the rename, through the team's normal deploy path and after a pre-flight check (details under Follow-ups). Watch the backlog drain afterwards. |
| Time to cause | about 2 minutes to Likely and about 3 minutes to Confirmed (simulated clock: no `date -u` output, times assumed) |
| Similar past incidents | no history yet (no incidents/ directory, no lessons.md) |

## Impact

Symptom: payments-worker pods exit at startup with code 1 and sit in CrashLoopBackOff; the Deployment shows 0/3 available (W0-Q5, W1-Q4, W1-Q5). The first container start was at 10:52:36 UTC (12:52:36) and the first BackOff at 10:53:02 UTC (12:53:02) (W1-Q2); each pod has restarted 11 times by 11:28 UTC.

Queue: the SQS queue payments-jobs, which this worker is configured to read (ConfigMap key PAYMENTS_QUEUE_URL names it, W2-Q3), held 10 to 30 visible messages between 10:30 and 10:50 UTC, 74 at 10:55, 1,060 at 11:00 and 5,989 at 11:25 UTC (13:25 Europe/Paris), a steady rise of about 197 messages per minute; the dead-letter queue stayed at 0 (W1-Q7). The baseline is only 20 minutes of data, because the earlier windows returned empty replies (Gaps).

Window: 10:22 to 11:28 UTC (12:22 to 13:28 Europe/Paris), ongoing. Basis: no SLO, no load-balancer or APM metrics, no business counter exists for this service, so the impact on payment capture and refunds is Assumed; the pod and queue measurements are Confirmed. Third party in the path: none known; the ledger service the worker calls is internal and was not queried, owner unknown.

## Causal chain

1. Trigger: commit d81e4b7 (#377), "rename ledger endpoint key to match the shared ledger client", changes charts/payments-worker/values-prod.yaml so that, under config:, LEDGER_API_BASE_URL becomes LEDGER_BASE_URL; Helm revision 31 (same chart 2.3.1, same app 5.2.0, so a values-only change) was applied at 10:52:20 UTC and the old ReplicaSet was scaled to 0 at 10:52:21 (Recreate strategy) · Confirmed · W0-Q8, W1-Q3, W1-Q2, W2-Q2. The commit-to-revision tie is by time (only chart commit in 3 days, committed 10:41:41, no pipeline record read) and by content: the live ConfigMap carries exactly the post-change key set (W2-Q3).
2. Mechanism: the pods take their environment from ConfigMap payments-worker-config (envFrom, Optional: false); the live ConfigMap has LEDGER_BASE_URL and no LEDGER_API_BASE_URL (W2-Q3); the application logs `config: required environment variable LEDGER_API_BASE_URL is not set` and exits 1 about 19 ms after starting (W1-Q6, W1-Q5) · Confirmed. The log line is from each pod's latest restart (11:25:56 UTC); the first crash's line is not retrievable (no log store), but the container spec and exit code are identical on every restart.
3a. Symptom, pods: CrashLoopBackOff on 3 of 3 pods, first BackOff 10:53:02 to 10:53:05 UTC (12:53), Deployment 0/3 · Confirmed · W1-Q2, W0-Q5.
3b. Symptom, queueing: with no worker running, nothing drains payments-jobs and the backlog grows from 10:50 to 10:55 onward · Likely · W1-Q7, W2-Q3; W3-Q1 (consumption metrics) returned no data.

Old against new: new ReplicaSet 6d4f8a2b7c (revision 15): 3/3 pods crash-looping, with the mechanism in each pod's own previous-container log (W1-Q6). Old ReplicaSet 84c1e9d3f5 (revision 14, in service 11 days, Helm revision 30): 0/3 pods with Warning events in the retained events before it was scaled down (W1-Q2), backlog steady at 10 to 30 until 10:50 (W1-Q7), and the removed line in the commit shows the old values supplied LEDGER_API_BASE_URL (W2-Q2). The onset (first BackOff 10:53:02) is not earlier than the rollout (10:52:20), and no earlier occurrence is visible in the retained evidence (events are kept for one hour only).

Ruled out, with the query that showed it: probe failures (no probes configured, no Unhealthy events, W1-Q4, W1-Q2); image pull or scheduling (pods Scheduled and Started, W1-Q2); out of memory (Reason Error, exit code 1, no OOM event, W1-Q5); a ledger outage or timeout (the process exits before any network call, W1-Q6); evictions (none in the namespace events; node-level events were not read, W1-Q2); a schedule or scaling action (no CronJob, EventBridge rule or Scheduler schedule named payments*, no CloudTrail write events on payments resources, W2-Q4, W2-Q5; what triggered the apply is not visible). Credentials are ruled out as the cause of the observed exit only (W1-Q6); a second failure behind the first cannot be excluded because Secrets are not read.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| No consumption data: NumberOfMessagesSent, Received and Deleted for payments-jobs returned empty replies (W3-Q1); other consumers of the queue were not enumerated | Step 3b stays Likely | Look at the three metrics for payments-jobs in the CloudWatch console around 10:52 UTC, or ask the owning team which services read the queue |
| Queue depth for payments-jobs returned nothing for the previous window, the -7d window and the 14 days before the onset, and nothing before 10:30 UTC today (W1-Q7, W1-Q8, W2-Q1) | Baseline is 20 minutes; recurrence cannot be classified (`unclassified`); empty is not read as zero | Check whether the metric is retained for that queue; add a depth or age alarm with history |
| No log aggregator: only each pod's last terminated container is readable (W1-Q6); events are kept for one hour | The first crash's log line is not available; the "old revision ran without restarts" evidence is limited to the last ~24 minutes of events and the queue depth | Add a log store to environment.md, or look in the cluster's log pipeline for 10:52 to 10:53 UTC |
| Application source repo for payments-worker 5.2.0 is not in environment.md | The expected key name comes only from the log line; whether a newer app version reads LEDGER_BASE_URL is unknown | Name the app repo and a local clone in environment.md |
| No apply record read for payments-deploy; schedule listings limited to names starting with payments, CloudTrail cannot see in-cluster changes (W2-Q4, W2-Q5) | The deployed commit is tied to Helm revision 31 by time and by the live ConfigMap content; what triggered the 10:52 apply is unknown | Open the apply run or GitOps sync record for payments-deploy at 10:52 UTC |
| The IAM simulation returned no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack, and three rows that were not asked for (W0-Q2) | None on the cause; write capability is already established by the two allowed actions | Review the PlatformOperator policies; use a read-only role for incident work |

open items need your input

## To confirm, a human would…

1. Show that consumption stopped: in the CloudWatch console, check NumberOfMessagesDeleted and NumberOfMessagesReceived for payments-jobs; a drop to zero at about 10:52 UTC while NumberOfMessagesSent continues confirms step 3b, and deletes continuing from another consumer would mean only part of the backlog comes from this worker.
2. Read the application source at the 5.2.0 tag (the config loader named in the log, config/load.go) to confirm it requires LEDGER_API_BASE_URL, and find out whether a newer app version reads LEDGER_BASE_URL and was meant to ship with the chart change. This decides whether the right fix is to revert the rename or to ship the app change.
3. Open the apply run or sync record for payments-deploy at 10:52 UTC to see what triggered the apply and whether the chart change was tested against app 5.2.0.
4. Once the pods start again, confirm the first minutes of the new pods are clean: a person with the right access should check that the Secret behind LEDGER_API_TOKEN holds the key the pod references and that the internal ledger endpoint is reachable from the pods, because a second startup failure could be hidden behind the first. This run does not read Secrets or call the endpoint.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Make the key the chart renders and the key the app reads agree again. Two ways: roll the release back to revision 30 (fastest; the diff shows the rename is the only change in revision 31, so little else is undone, and with the Recreate strategy all pods restart together, which costs nothing extra while all three are already down), or revert the rename in values-prod.yaml and deploy it. If the intent is to adopt the shared ledger client's name, the app version that reads LEDGER_BASE_URL has to ship first or together. Check the choice with `pre-flight`, and hand any change to `iac-change-execution` in a new session with this report as context. |
| Fix | Plan for the recovery burst: roughly 6,000 or more messages (growing about 197 per minute while the pods are down) will be consumed at once at the worker's configured concurrency (PAYMENTS_WORKER_CONCURRENCY exists; its value was not read). Watch the internal ledger service and the dead-letter queue while the backlog drains; reducing the concurrency temporarily would protect the ledger at the cost of a slower drain. |
| Prevention | Add a check to the chart pipeline that renders the chart and compares the rendered environment variable names with the list of variables the app requires at startup, so a rename fails before it is applied. |
| Prevention | Consider a RollingUpdate strategy with a readiness or startup signal in place of Recreate, so a bad config leaves the old pods serving; the cost is two versions briefly consuming the same queue, so check first that the worker tolerates that. |
| Observability gap | No alert fired from the data this run could see: add alarms on queue age or depth for payments-jobs (with history beyond today), on Deployment availability and on pod restarts; add a log store so the first crash's line survives; define an SLO or a business counter for payment capture and refunds so impact can be sized from data. |
| Observability gap | Incident work ran on PlatformOperator, which can put S3 objects and update ECS services, and the EKS binding can read Secrets (`*.*` get/list/watch). Give on-call investigators a read-only role and the built-in view binding. |

## Cost

18 evidence queries (plus 4 access checks in wave 0) · 0 GB of logs scanned · 15 CloudWatch metric requests · no X-Ray or other metered units · well under 0.01 USD in metered charges
