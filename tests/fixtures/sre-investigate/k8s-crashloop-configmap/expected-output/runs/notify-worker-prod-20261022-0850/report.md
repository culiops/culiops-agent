
# Investigation: notify-worker prod: all pods crash-looping, emails not being sent

Run: notify-worker-prod-20261022-0850 · Mode: Fast · Window: 2026-10-22 06:50-08:50 UTC (06:50-08:50 local; the local zone is UTC per environment.md)

## TL;DR

| Field | Value |
|---|---|
| Cause | Helm release 12 (08:14:20 UTC) shipped a values change that renamed the ConfigMap key `NOTIFY_SMTP_RELAY_HOST` to `SMTP_RELAY_HOST`; notify-worker 3.8.1 still requires `NOTIFY_SMTP_RELAY_HOST`, exits at start-up on all 3 pods, and CrashLoopBackOff follows · label: Confirmed |
| Weakest link | None of the three chain links is below Confirmed. The least direct one is the tie between merged commit `3f9a1c2` and release 12: it rests on the live ConfigMap's key set and the release time (11 minutes after the merge), not on a pipeline apply record (gap G5). Separately, "emails are not delivered" is Likely: no delivery counter exists (gap G4). |
| Impact | 0 of 3 workers available since about 08:14 UTC (36 minutes at report time), still ongoing; `notify-outbound` backlog grew from 16 (08:10) to 9,660 (08:45), about 318 messages per minute, DLQ at 0; transactional email (order confirmations, password resets) is waiting in the queue. Customers affected: Assumed. |
| Severity | SEV1 (suggested) because a customer-facing core flow (transactional email) is down: no worker consumes. The incident owner decides. |
| Pattern | unclassified · the 14-day and baseline pulls returned no data and there is no alarm history (gap G3) · Assumed. Only one change sits near the onset; the shape is a step (consumption stops) with a linear backlog ramp. |
| Recommended action | A human restores a working config for the worker: either put back the key name the app reads, or roll back to Helm release 11 (the only difference in release 12 is the key rename). See Follow-ups for the trade-offs; assess with `pre-flight` first. |
| Time to cause | First Likely after wave 1 (log line plus release time), Confirmed after wave 3 (3 waves, 38 read-only calls); wall-clock minutes were not measured in this run. |
| Similar past incidents | no history yet (`incidents/` does not exist) |

## Impact

- Symptom: all 3 `notify-worker` pods are in CrashLoopBackOff with 11 restarts each; the `notify-outbound` queue is no longer drained (W0-Q14, W0-Q15, W1-Q7, W1-Q8). Confirmed.
- Scale: visible messages 7-27 at 07:50-08:10, then 120 at 08:15 and +1,590 every 5 minutes to 9,660 at 08:45; DLQ 0 throughout (W1-Q8, W1-Q12). The steady rise equals the arrival rate (about 318 per minute) with zero consumption. Confirmed for the series; the 06:50-07:45 part of the window and every baseline window returned no data (G3).
- Start: 08:14 UTC. Release 12 at 08:14:20, first new pod 08:14:33, first rise in queue depth at 08:15 (W1-Q6, W1-Q4, W1-Q8). Ongoing: yes at 08:50 UTC.
- Flow: transactional email (core flow in environment.md). That emails are not reaching customers is Likely (inferred from 0/3 consumers and the backlog; no delivery counter, G4). How many customers: Assumed.
- Why every pod went at once: the Deployment uses the Recreate strategy, so the old pods were stopped before the new ones started (W1-Q3, W1-Q7).
- Third party in the path: the SMTP relay (host is set through the ConfigMap). Nothing in the evidence implicates it; no contact route is in the profile.

## Causal chain

1. Trigger: commit `3f9a1c2` ("align config key names with the shared SMTP chart", #214, merged 08:03:41 UTC) renames the values key `NOTIFY_SMTP_RELAY_HOST` to `SMTP_RELAY_HOST` in `charts/notify-worker/values-prod.yaml`; Helm release 12 is applied at 08:14:20 UTC with the same chart (1.8.0) and app version (3.8.1) as release 11 · Confirmed · W3-Q1, W2-Q1, W1-Q6, W0-Q18
2. Mechanism: the live ConfigMap `notify-worker-config` has the keys `NOTIFY_FROM_ADDRESS`, `NOTIFY_QUEUE_URL`, `NOTIFY_WORKER_CONCURRENCY` and `SMTP_RELAY_HOST`, and no `NOTIFY_SMTP_RELAY_HOST`; the app logs `config: required environment variable NOTIFY_SMTP_RELAY_HOST is not set` (config/load.go:58) and exits with code 1, 19 ms after start, on all three pods (the previous-container logs of each) · Confirmed · W2-Q2, W1-Q5, W2-Q4, W2-Q5, W1-Q4
3. Symptom: with every container exiting, the Deployment has 0 of 3 available, restarts back off (CrashLoopBackOff), and `notify-outbound` stops being consumed: depth leaves its 7-27 level at 08:15 and climbs to 9,660 by 08:45 · Confirmed · W1-Q7, W0-Q15, W1-Q8, W1-Q12

Timing fits: release 12 at 08:14:20, first new pod 08:14:33, queue depth leaves baseline at 08:15. The crash is not a quirk of one pod (3 pods on 3 nodes fail identically).

Ruled out, with the query behind each: a broken image or chart (the commit touches only the values key; chart and app version are the same in releases 11 and 12; W3-Q1, W1-Q6); a missing or wrong SMTP password Secret (the container started 12 times and the fatal names a different variable; W1-Q4, W1-Q5); OOM or limits (reason Error, exit code 1, not OOMKilled or 137; W1-Q4); probe, image pull or scheduling failures (pods scheduled, image present, no probes defined; W1-Q3, W1-Q7); node churn (three nodes, same failure; W1-Q3); an SMTP relay or SQS outage as the crash cause (the process dies during config load, before any network call; W1-Q5); a scheduled job (no CronJobs; W2-Q3).

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| G1 AWS write-check: the simulation reply lacked 3 of the 10 requested actions (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) | none on this investigation; "no broad write found" covers 7 of 10 actions | re-run the simulation, or have the role owner confirm the role is ReadOnlyAccess |
| G2 No log backend in environment.md | only the last crash of each pod is visible; no log history or counts | add a log datasource to environment.md |
| G3 SQS pulls returned no data for the previous window, -7d and both 14-day pulls, and none for 06:50-07:45 | recurrence is unclassified (Assumed); backlog size compared only with 80 minutes before onset | check the queue's metric retention and dimensions in the CloudWatch console |
| G4 No delivery counter, SLO or request metrics | customers or emails affected is Assumed; non-delivery is Likely | add a flow counter or SLO source to environment.md |
| G5 Pipeline record for release 12 not read | who or what applied release 12, and the commit-to-release tie, rest on cluster state and timing | ask the `notify-deploy` owners for the deploy job run |
| G6 Old ReplicaSet image not read directly | "image unchanged" rests on the commit diff and identical chart and app version | compare the two ReplicaSets' images |
| G7 Alarm coverage on `notify-outbound` not checked | detection delay unknown | list the queue's alarms in the CloudWatch console |
| G8 App code not read | the required variable name comes from the app's own log line | read `config/load.go` at tag 3.8.1 with read-only `gh` |
| G9 `notify-deploy` clone freshness and default branch name not verified | later commits could be missing | confirm against the remote with `gh` |

Open items need your input.

## To confirm, a human would…

1. Ask the `notify-deploy` owners (the commit author is the `platform-dev` team) for the deploy job run that applied release 12, to close the commit-to-release tie (G5). A pipeline record showing release 12 built from `3f9a1c2` would settle it.
2. Check that the app at tag 3.8.1 reads only `NOTIFY_SMTP_RELAY_HOST` (config/load.go near line 58), and whether a newer app version accepts the new name from the shared SMTP chart. If the shared chart name is the intended one, the rename belongs after an app release that accepts it.
3. After workers run again, watch the first start of each pod and the queue: the backlog should fall and the DLQ should stay at 0. A new error after start-up (relay connection, authentication with the `notify-smtp` Secret) would be a second, separate fault that this run could not test read-only.
4. Look in the mail provider or relay logs to see whether any email left during the outage by another path, and what a drain of about 10,000 or more queued messages at once does to the relay's rate limits. Decide with the business whether stale messages, such as expired password-reset links, should be sent.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Restore a working config, owner's choice. Option 1, roll back to Helm release 11: the quickest, and the diff shows release 12 changed nothing else, but it leaves the intended rename undone and the workers on the old key. Option 2, a new release that restores the key name the app reads: keeps the release history moving forward, but needs a merge and review first, so it is slower. Either way, assess it with `pre-flight` and apply it in a separate session with `iac-change-execution`, using this report as context. |
| Fix | After recovery, expect the backlog to drain at the workers' concurrency (set by `NOTIFY_WORKER_CONCURRENCY`, 3 pods); consider the relay's limits before letting it drain at full speed, at the cost of a longer delay for the queued emails. |
| Prevention | Rename config keys in two steps: first release an app version that accepts both names, then change the values. Cost: two releases instead of one. |
| Prevention | Add a CI check that the rendered ConfigMap contains every variable the app requires, so a key rename fails before merge. Cost: the app has to publish its list of required variables. |
| Prevention | Consider the RollingUpdate strategy instead of Recreate with a readiness signal: the old pods would have stayed up while the new ones crashed. Cost: two revisions run side by side during a rollout, which matters if the consumers must not overlap. The pod template has no probes today. |
| Observability gap | No alarm on `notify-outbound` depth or age was found in the evidence (not checked, G7), no email-sent counter, and no log backend: add an age-of-oldest-message alarm and a sent-email counter so a stopped worker is seen within minutes. |

## Cost

38 read-only calls (6 of them metered) · 0 GB of logs scanned · 6 CloudWatch metric requests · no other metered units · under $0.01 in metered charges
