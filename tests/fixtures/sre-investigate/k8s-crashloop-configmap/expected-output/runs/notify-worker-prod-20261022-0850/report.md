# Investigation: notify-worker prod: pods crash-looping at startup, email queue not consumed

Run: notify-worker-prod-20261022-0850 · Mode: Fast · Window: 2026-10-22 06:50:00Z to 08:50:00Z (06:50 to 08:50 local, zone UTC per environment.md)
Access: `prod-read`: read-only confirmed (simulation) for the 7 listed write actions the reply covered, none allowed; write capability unknown (gap) for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack, which returned no row. `arn:aws:eks:us-east-1:111122223333:cluster/prod`: no write verbs in notify (note: the identity can read all resources, Secrets included; none was read).

## TL;DR

| Field | Value |
|---|---|
| Cause | Commit `3f9a1c2` (08:03:41Z) renamed the Helm values key `NOTIFY_SMTP_RELAY_HOST` to `SMTP_RELAY_HOST`. Helm revision 12 (08:14:20Z) put the renamed key into ConfigMap `notify-worker-config`. notify-worker 3.8.1 still requires `NOTIFY_SMTP_RELAY_HOST`, so it exits with code 1 at startup on all 3 pods. The Deployment's `Recreate` strategy had already stopped the healthy pods. · label: Confirmed |
| Weakest link | The mechanism is read from the latest restart (08:47:56Z), because `kubectl logs --previous` keeps only the newest container. The log of the first crash (08:14:36Z) is gone. The link stays Confirmed: the pod template and ConfigMap are unchanged since 08:14:20Z, all 3 pods show 11 identical exit-1 restarts, and event first-timestamps give the timing. Separately, "no email is delivered by any path" is Likely, not measured (no delivery-side metric is configured). |
| Impact | prod, all 3 replicas unavailable since 08:14:21Z, ongoing. Queue `notify-outbound` backlog was 9,660 at 08:45 (7-27 before 08:15) and grows about 318 per minute. The dead-letter queue is 0. |
| Severity | SEV1 (suggested) because a customer-facing core flow from environment.md (transactional email) is down: no worker consumes the queue. The incident owner decides. |
| Pattern | `unclassified` · no alarm history, and the previous-window, -7d and 14-day pulls returned no data · Assumed. Shape: step in pod state at 08:14, ramp in the backlog from 08:15. |
| Recommended action | A human should restore the config key name the running app expects, through the normal change path and assessed with `pre-flight` first. Either undo the rename for the prod release, or carry both key names until the app accepts the new one. Undoing it postpones the alignment with the shared SMTP chart. Carrying both leaves a duplicate key to remove later. When workers return they will face a backlog of roughly 10,000 messages and growing, so check the SMTP relay's limits first. |
| Time to cause | Not measurable (simulated clock). First Likely after wave 1 (Helm revision 12 at 08:14:20Z against the first failing start at 08:14:36Z). Mechanism seen in wave 2, Confirmed in wave 3. |
| Similar past incidents | no history yet (no `incidents/` directory exists) |

## Impact

Symptom: notify-worker pods crash-loop and never become ready, so nothing consumes queue `notify-outbound`. The reporter says emails are not going out. Affected: prod, namespace notify, all 3 replicas (0/3 available, 11 restarts each, same ReplicaSet `notify-worker-5c8d7b9f4c`) (W1-Q1, W1-Q4). Core flow: transactional email (order confirmations, password resets).

The backlog was 7-27 messages between 07:50 and 08:10Z. It was 16 at 08:10, 120 at 08:15, then rose by about 1,590 every 5 minutes to 9,660 at 08:45. The dead-letter queue stayed at 0 throughout (W1-Q6). The last healthy pod stopped at 08:14:21Z and the first failing start was 08:14:36Z (W1-Q2). The incident is ongoing as of 08:50Z.

Basis:
- Confirmed: nothing consumes the queue (W1-Q1, W1-Q2, W1-Q6, W3-Q3).
- Likely: no email leaves by any path. No sent-count or relay metric is configured, so this is inferred from the unconsumed queue.
- Baselines for the previous window, the -7d window and 14 days returned no datapoints (W1-Q6, W1-Q7). That is a gap, not zero.

Third party in the path: none identified. The SMTP relay is a downstream of the worker, but no query reached it, because the process dies before connecting. No contact route is recorded in the profile. The run cannot contact vendors.

## Causal chain

1. Trigger: commit `3f9a1c2` (2026-10-22 08:03:41Z, "align config key names with the shared SMTP chart (#214)") renamed one key in the `config:` block of `charts/notify-worker/values-prod.yaml`. Helm release `notify-worker` went to revision 12 at 08:14:20Z with the same chart (1.8.0) and app version (3.8.1) as revision 11. The live ConfigMap now holds `SMTP_RELAY_HOST` and not `NOTIFY_SMTP_RELAY_HOST` (current state). · Confirmed · W2-Q3, W3-Q1, W3-Q2, W0-Q10, W1-Q5. Merged is not applied: the pipeline apply record was not read; the Helm revision time and the live ConfigMap stand in.
2. Mechanism: the app (tag 3.8.1, unchanged) loads its configuration from the environment. It logs fatal `config: required environment variable NOTIFY_SMTP_RELAY_HOST is not set` at config/load.go:58 and exits with code 1 in the same second it starts (08:47:56Z restart). Kubelet restarts it with back-off, giving CrashLoopBackOff on all 3 pods, 11 restarts each. Timing: Helm 08:14:20 → old pod killed 08:14:21 → new pods scheduled 08:14:33 → first container start 08:14:36 → first BackOff 08:15:02 to :05 → backlog steps up at 08:15. · Confirmed · W2-Q1, W2-Q2, W1-Q1, W1-Q2
3. Symptom: with strategy `Recreate`, the old ReplicaSet went to 0 at 08:14:21, 12 seconds before the new pods existed. Since then the Deployment has 0 of 3 available, nothing consumes `notify-outbound`, and the backlog grows. · Confirmed · W3-Q3, W1-Q2, W1-Q6

Hypotheses ruled out in this run (each with the query that refuted it):
- New image or code defect: chart and app version are identical in revisions 11 and 12, and the error is a config error (W1-Q5, W2-Q2). The old ReplicaSet's image itself was not read.
- OOMKilled: last state is `Error`, exit code 1, not OOMKilled (W2-Q1).
- Probe failures: no `Unhealthy` events and no probes configured (W1-Q2, W2-Q1).
- Image pull or scheduling failure: pods were `Scheduled` and `Started` (W1-Q2).
- Node or instance churn: ruled out at pod and namespace scope only; the process exits by itself (W1-Q2, W2-Q2). Node object events were not read.
- SMTP relay or another dependency down: the process fails before any network use (W2-Q2). Relay health after startup stays Assumed.
- Scheduled job: no CronJobs and no scheduled EventBridge rules returned (W2-Q4).
- Change by an AWS-level write: no matching CloudTrail writes for EKS, SQS, Secrets Manager or SSM from 06:14 to 08:30Z (W2-Q5).

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Baselines: the previous window, -7d window and the 14-day 1-hour pull returned empty objects; no alarm history exists (W1-Q6, W1-Q7) | Recurrence is `unclassified`. "Normal backlog" rests on a 20-minute sample (07:50-08:10). No claim about earlier occurrences. The crash timing is not weakened (it comes from events). | Ask the queue's owner for the usual `notify-outbound` backlog, or check why the SQS metrics returned nothing for those days. |
| No delivery-side signal: environment.md lists no email-sent counter, relay metric or provider backend | "Emails are not going out" is Likely, not measured. Another delivery path is Assumed absent. | Add a datasource for the sending counter or relay to environment.md, or have the owner check the mail provider's sent log. |
| Logs: only `kubectl logs --previous`, which keeps the latest terminated container (08:47:56Z); no log backend is listed | The first crash (08:14:36Z) has no log in hand. Its cause is Assumed identical, supported by the unchanged template and ConfigMap. | If pod logs are shipped anywhere, query the first start after 08:14:33Z. |
| Pipeline apply record for commit `3f9a1c2` (PR #214) not read; deploy clone freshness and default branch unknown (all refs searched, no fetch) | The apply is tied by the live ConfigMap keys and Helm revision 12, not by a CI run. | Open the deploy pipeline run for PR #214 and compare its time with 08:14:20Z. |
| Node object events and the Kubernetes API audit log not read; CloudTrail does not log Kubernetes writes | Node churn is excluded at pod scope only. Who or what ran the Helm upgrade at 08:14:20Z is unknown. | Ask the team who or which pipeline ran the upgrade; read the EKS audit log if enabled. |
| Application code at the deployed ref (example-org/notify-worker, 3.8.1) not read | Which names the 3.8.1 loader accepts is unchecked. This does not change the crash explanation, only the fix options. | Read config/load.go at the 3.8.1 tag with a read-only `gh` call. |
| Write capability unknown (gap), prod-read: the simulation reply had no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack, and had rows for three actions that were not asked | The Access line cannot say "none of the 10 broad write actions is allowed". It says 7 of 10 evaluated, none allowed. No effect on any cause. | Ask the account owner to confirm the role is read-only, or re-run the simulation from an identity that has `iam:SimulatePrincipalPolicy`. |

## To confirm, a human would…

1. Read the app's config loader (config/load.go at the 3.8.1 tag in example-org/notify-worker) and see whether it accepts only `NOTIFY_SMTP_RELAY_HOST` or both names. If only the old name, the rename in PR #214 explains the crash completely and the fix is a revert or a bridge. If both are accepted, something else on the failing path needs a second look.
2. Open the deploy pipeline run for PR #214. Confirm it applied revision 12 at about 08:14:20Z, and find out who or what triggered it.
3. Look at the mail provider's or SMTP relay's sent log and any sent counter for 08:00-08:50Z. This confirms whether any email left after 08:14. Right now non-delivery is inferred from the unconsumed queue.
4. Read `ApproximateAgeOfOldestMessage` for `notify-outbound`. This shows how many minutes of mail are delayed. The run did not spend a wave on it.
5. Read the old ReplicaSet `notify-worker-7f6b8c5d2e` (names only) and confirm its image tag equals 3.8.1. The run relied on the Helm app version for this.
6. After the key is restored, watch the first pod start. Confirm it reaches the SMTP relay with the credentials from Secret `notify-smtp`, and that the draining backlog stays inside the relay's rate limits. The run could not test this, because the process dies before connecting.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Restore the key name that notify-worker 3.8.1 reads for the prod release. Either revert the rename from PR #214 for prod, or carry both `NOTIFY_SMTP_RELAY_HOST` and `SMTP_RELAY_HOST` until the app is changed to accept the new name. The first postpones alignment with the shared SMTP chart. The second leaves a duplicate key to clean up later. Assess it with `pre-flight` first, then hand it to `iac-change-execution` in a new session with this report as context. |
| Prevention | Add a check before merge that renders the chart and compares the ConfigMap key names with the environment variables the app requires. The cost is keeping that required-variable list current. |
| Prevention | Replace the `Recreate` strategy with a rolling update plus a readiness probe, so a revision that crashes at startup never replaces the last healthy pods. The cost is that old and new pods consume the queue at the same time during a rollout (this only matters if the worker is not safe to run twice) and that extra capacity is needed. |
| Prevention | Bind the on-call identity to a narrower role (the built-in `view` ClusterRole). The current group can read Secrets. |
| Observability gap | No alarm or alert was named in the request, and none was found by this run. The incident was noticed by a person about 36 minutes after the onset (08:14 to about 08:50Z). Consider alerts on `pods available = 0` or CrashLoopBackOff and on queue backlog or oldest-message age. |
| Observability gap | No delivery-side email counter and no pod-log backend exist in environment.md, so the first-crash log is lost on each restart. Consider adding both. |
| Observability gap | No `service-discovery` catalog exists for notify-worker. Consider running `service-discovery` after the incident so the next run has a dependency map. |

## Cost

19 queries · 0 GB of logs · 8 CloudWatch metric requests · no other metered units · well under one cent in metered charges (GetMetricData only; rate per the CloudWatch pricing page, not re-read this session). The 6 free Phase 0 identity and write-check calls are not counted; counting them, the run made 25 calls.
