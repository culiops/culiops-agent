# Run log: sre-investigate, case-d, payments-worker prod

Run directory: `payments-worker-prod-20261024-1128`
Simulated clock: 2026-10-24 11:28:00 UTC (13:28 Europe/Paris, UTC+2). `date -u` has no INDEX row (would return `_empty.txt`); the clock was taken from the INDEX note "ages are relative to 11:28:00 UTC".

## Operator lines received

| # | When | Line |
|---|---|---|
| 1 | session start (opening request) | `payments-worker pods in prod keep restarting and payments are queueing up. Fast mode, please.` |

No later lines exist in `operator-script.md` (only line 1).

## Phase 0: output root, environment, mode

Local checks before the first message (not metered, not backend queries):

| Command | World file | Key facts |
|---|---|---|
| `echo "${CULIOPS_HOME:-}"` | `_empty.txt` | CULIOPS_HOME unset, so output root = `.culiops/sre-investigate/` at the repo root |
| `git rev-parse --show-toplevel` | `_empty.txt` | empty output (case dir stands for the repo); root taken as the current directory |
| `git check-ignore -q .culiops/sre-investigate` | `_empty.txt` | exit 0 = ignored; no warning needed |
| `ls .culiops/sre-investigate` | `ls-01.txt` | only `environment.md` (no profiles/, lessons.md, incidents/, runs/) |
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | tz Europe/Paris (UTC+2 until 2026-10-25 01:00 UTC); one AWS profile `prod-ops` (account 111122223333, us-east-1); one kube context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `payments`; backends: kubectl/Helm and CloudWatch (SQS depth); Helm values repo `example-org/payments-deploy`, clone `~/src/payments-deploy`, path `charts/payments-worker/values-prod.yaml`; Logs Insights ask above 10 GB; default SEV scale; core flows = payment capture and refunds processed by payments-worker; no token env vars, no log/metric/trace backend |
| `command -v agentbox-env` | `_empty.txt` | exit 1, so nothing is said about Culibox (Constraint 8) |

Files written: run directory `out/runs/payments-worker-prod-20261024-1128/` (with `raw/helper/`), initial `ledger.md` (Problem table filled).

### Message 1 (verbatim)

```text
sre-investigate: payments-worker, prod.

Mode: Fast. The pods are restarting now and payments are queueing, so this is a live incident, and you asked for Fast. Fast means at most 3 query waves after access checks, no checkpoints, and a report with honest labels at the end; "go deep" afterwards keeps the same run.

Output root: .culiops/sre-investigate/ at the repo root (CULIOPS_HOME is not set). The run writes everything there (run directory runs/payments-worker-prod-20261024-1128/). It is local and is never committed; `.culiops/sre-investigate` is git-ignored here.

Window: you gave no onset, so I use the last two hours: 09:28-11:28 UTC (11:28-13:28 Europe/Paris, UTC+2). Zone comes from environment.md. If wave 1 shows an earlier or later true onset I will re-anchor on it and say so.

Sources in environment.md: kubectl and Helm on context arn:aws:eks:us-east-1:111122223333:cluster/prod (namespace payments), and CloudWatch SQS metrics through profile prod-ops. No log aggregator, Prometheus, trace store or error tracker is listed, so container logs will come from `kubectl logs --previous` only.

Wave 0 (access and identity), commands in full:

1. date -u +%H:%M:%S; aws sts get-caller-identity --profile prod-ops
2. arn=$(aws sts get-caller-identity --profile prod-ops --query Arn --output text); role=${arn#*:assumed-role/}; role=${role%%/*}; role_arn=$(aws iam get-role --profile prod-ops --role-name "$role" --query Role.Arn --output text); aws iam simulate-principal-policy --profile prod-ops --policy-source-arn "$role_arn" --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode cloudformation:DeleteStack --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text
3. kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod; kubectl config current-context
4. kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace payments

No token variables are listed, so there is no token check, and no log backend, so no log probe. There is no stored profile or lessons.md yet, so the service profile is built next.
```

### Wave 0 commands and results

| ID | Command | World file | Key facts |
|---|---|---|---|
| W0-Q1 | `date -u +%H:%M:%S; aws sts get-caller-identity --profile prod-ops` | `sts-01.json` (date: `_empty.txt`) | Account 111122223333 (matches env), assumed-role PlatformOperator |
| W0-Q2 | sts + `aws iam get-role` + `aws iam simulate-principal-policy` (policy-source-arn = role ARN, not the sts ARN) | `iam-01.json`, `iam-02.json` | Role ARN path `/`. Allowed: s3:PutObject, ecs:UpdateService. 7 implicitDeny. Three of the fixed ten missing from the reply (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack); three extra rows returned |
| W0-Q3 | `kubectl auth whoami ...; kubectl config current-context` | `k8s-02.txt`, `k8s-01.txt` | Same assumed role, groups eks-readonly; current context = prod |
| W0-Q4 | `kubectl auth can-i --list --context ... --namespace payments` | `k8s-03.txt` | No write verbs (only the three excluded selfsubject* creates); `*.*` get list watch |

Files written: `ledger.md` (Access, Query log W0, Gaps).

### Message 2 (verbatim, after wave 0)

```text
Wave 0 done.

+------------------------------------------------------------------+
| WARNING: WRITE-CAPABLE CREDENTIALS                               |
| Profile: prod-ops  Account: 111122223333  Role: PlatformOperator |
| Simulation allows: s3:PutObject, ecs:UpdateService               |
|                                                                  |
| This investigation is read-only and will not use these           |
| permissions, but the credentials could change the account.       |
| Use a read-only role (ReadOnlyAccess or tighter) for incident    |
| work, or Culibox when it is available. Continuing.               |
+------------------------------------------------------------------+

Kubernetes, context arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace payments: no write verbs seen (only the three self-review creates, which do not count). The identity can however get/list/watch every resource, Secrets included; the run will not open Secret objects.

Gaps so far:
- The IAM simulation did not return rows for 3 of the 10 fixed actions (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) and returned 3 I did not ask for. The warning above stands on the two actions that came back allowed.
- environment.md lists no log aggregator, Prometheus, trace store or error tracker. Logs come only from `kubectl logs --previous` and Kubernetes events (about an hour of retention), so I will read those first.

No stored service profile exists for payments-worker/prod, so I am building one now (discovery helper on the cheapest model), then wave 1.
```

## Build profile

No `profiles/payments-worker-prod.md` exists, so a helper was dispatched (`TASK: PROFILE`, cheapest tier, identifier lessons: none). Simulated inline, section label `[helper PROFILE, cheapest tier]`. It read environment.md, ran one wave, and returned the filled template with `(unverified)` marks. In parallel the main session started the IaC history read (needs no discovered identifier).

### [helper PROFILE, cheapest tier]

| ID | Command | World file | Key facts |
|---|---|---|---|
| W0-Q5 | `kubectl --context <ctx> -n payments get deploy; ... get pods; ... get configmap; ... get svc; ... get ingress; ... get hpa` (one chained call) | `k8s-12.txt`, `k8s-04.txt`, `k8s-13.txt`; svc/ingress/hpa: `_empty.txt` | Deployment payments-worker 0/3 ready, age 164d. 3 pods (hash 6d4f8a2b7c) all CrashLoopBackOff, 11 restarts, age 35m. ConfigMaps payments-worker-config (4 keys), kube-root-ca.crt. No svc/ingress/hpa |
| W0-Q6 | `aws sqs list-queues --profile prod-ops --region us-east-1 --queue-name-prefix payments` | `sqs-01.json` | payments-jobs, payments-jobs-dlq |
| W0-Q7 | `helm list --kube-context <ctx> -n payments` | `helm-03.txt` | release payments-worker rev 31, updated 2026-10-24 10:52:20 UTC, chart payments-worker-2.3.1, app 5.2.0 |
| (local) | `ls .culiops/service-discovery` | no row: "No such file or directory", exit 1 | no service-discovery catalog |

Helper discovery skipped (no such backend in environment.md): log labels, trace service name, Prometheus job, dashboards, ECS, RDS.

### Main session, parallel with the helper

| ID | Command | World file | Key facts |
|---|---|---|---|
| W0-Q8 | `git -C ~/src/payments-deploy log --remotes=origin --since=2026-10-21T11:28:00Z --until=2026-10-24T11:28:00Z --date=iso-strict --format='%h %cI %an %s' -- charts/payments-worker` | `git-01.txt` (only the commit inside my range returned) | d81e4b7 (#377) "rename ledger endpoint key to match the shared ledger client", committed 2026-10-24 10:41:41 UTC. The older commit 27c4e91 (#361, retry budget, 2026-10-13) is outside my 3-day range and was not returned |

Files written: `profile.md` (run profile; tie rule re-applied: the queue-consumer link and every identifier not returned by a query stay `(unverified)`), `ledger.md` (Code repos, Query log W0-Q5..Q8).

### Message 3 (verbatim, profile shown and wave 1 printed)

```text
Profile for payments-worker/prod (continuing without waiting; correct me if anything is off):

- Service: Deployment payments-worker in namespace payments, cluster prod, Helm release payments-worker (revision 31, chart payments-worker-2.3.1, app 5.2.0, applied 2026-10-24 10:52:20 UTC). Verified by queries.
- Replicas (the sibling set): 3 pods, payments-worker-6d4f8a2b7c-3mfk8, -q7c2z, -vn5tr, all CrashLoopBackOff with 11 restarts, age 35 min. Deployment shows 0/3 ready.
- Config: ConfigMap payments-worker-config (4 keys). No Service, Ingress or HPA in the namespace.
- Queues: payments-jobs and payments-jobs-dlq exist in us-east-1. That payments-worker consumes payments-jobs is (unverified): it is inferred from the name only.
- Code: Helm values in example-org/payments-deploy (local clone ~/src/payments-deploy). One commit in the last 3 days on charts/payments-worker: d81e4b7 (#377), 10:41:41 UTC, "rename ledger endpoint key to match the shared ledger client". It is a candidate only; nothing ties it to the failure yet.
- No logs, metrics or traces backend is known, so there is no request-level data; everything below comes from kubectl, Helm and SQS depth.

The first signs point at a change around 10:52 UTC, earlier than the start of the window I assumed (09:28). If wave 1 confirms it I will re-anchor the windows in wave 2.

Wave 1 (change events, golden signals, recurrence). Commands in full:

1. date -u +%H:%M:%S; kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments rollout history deployment/payments-worker; kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments get rs --sort-by=.metadata.creationTimestamp -o custom-columns='NAME:.metadata.name,REVISION:.metadata.annotations.deployment\.kubernetes\.io/revision,CREATED:.metadata.creationTimestamp,DESIRED:.spec.replicas,READY:.status.readyReplicas'
2. kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments get events --sort-by=.lastTimestamp -o json | jq -r '.items[] | [(.firstTimestamp // .eventTime), .lastTimestamp, (.count // .series.count // 1), .reason, .involvedObject.name, (.message // "" | .[:300])] | @tsv'
3. helm history payments-worker --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments --max 10
4. kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments describe deployment payments-worker
5. for p in payments-worker-6d4f8a2b7c-3mfk8 payments-worker-6d4f8a2b7c-q7c2z payments-worker-6d4f8a2b7c-vn5tr; do kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments describe pod "$p"; done
6. for p in payments-worker-6d4f8a2b7c-3mfk8 payments-worker-6d4f8a2b7c-q7c2z payments-worker-6d4f8a2b7c-vn5tr; do kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments logs "$p" --previous --tail=50; done
7. Queue depth, three windows (incident 09:28-11:28, previous 07:28-09:28, same span seven days back), both queues:
   for w in "2026-10-24T09:28:00Z 2026-10-24T11:28:00Z" "2026-10-24T07:28:00Z 2026-10-24T09:28:00Z" "2026-10-17T09:28:00Z 2026-10-17T11:28:00Z"; do set -- $w; aws cloudwatch get-metric-data --profile prod-ops --region us-east-1 --start-time "$1" --end-time "$2" --metric-data-queries '[{"Id":"jobs","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"payments-jobs"}]},"Period":300,"Stat":"Maximum"}},{"Id":"dlq","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"payments-jobs-dlq"}]},"Period":300,"Stat":"Maximum"}}]' --output json; done
8. Recurrence, 14 days at one hour ending at the assumed window start, Maximum (a saturation-type gauge):
   aws cloudwatch get-metric-data --profile prod-ops --region us-east-1 --start-time 2026-10-10T09:28:00Z --end-time 2026-10-24T09:28:00Z --metric-data-queries '[{"Id":"jobs","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"payments-jobs"}]},"Period":3600,"Stat":"Maximum"}},{"Id":"dlq","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"payments-jobs-dlq"}]},"Period":3600,"Stat":"Maximum"}}]' --output json

I print `describe` output for the deployment and pods but record environment variables by name only, never values. The IaC history read (git log) already ran in the profile step. CloudTrail, the app/values diff at the deployed ref, and the schedule listings go in wave 2.
```

## Wave 1 (change events, golden signals, recurrence)

Commands exactly as in Message 3 (printed in full before running). Start time: `date -u` returned nothing in the simulation; recorded as 11:29 (clock assumed).

| ID | Command (short) | World file | Key facts |
|---|---|---|---|
| W1-Q1 | `rollout history deployment/payments-worker`; `get rs --sort-by=...creationTimestamp -o custom-columns=...` | `k8s-10.txt`, `k8s-11.txt` | Deployment revisions 14, 15. RS 84c1e9d3f5 desired 0, age 11d. RS 6d4f8a2b7c desired 3, ready 0, age 35m |
| W1-Q2 | `get events --sort-by=.lastTimestamp -o json \| jq ...` | `k8s-06.json` | 10:52:21 old RS scaled to 0, old pod killed; 10:52:33 new RS scaled to 3; 10:52:36 first Started; BackOff first seen 10:53:02/03/05 on the three new pods (x151/149/150); no Unhealthy/OOM/Evicted/FailedScheduling/image-pull events; no Warning for old-hash pods |
| W1-Q3 | `helm history payments-worker ... --max 10` | `helm-01.txt` | rev 30 Oct 13 15:40:02 superseded, rev 31 Oct 24 10:52:20 deployed, same chart 2.3.1 / app 5.2.0 |
| W1-Q4 | `describe deployment payments-worker` | `k8s-14.txt` | Recreate strategy, 0/3 available, image :5.2.0, config via envFrom ConfigMap payments-worker-config, no probes |
| W1-Q5 | `describe pod` for each of the 3 pods | `k8s-07.txt` (same content for each, name differs) | Exit Code 1 Reason Error, last run 11:25:56, restart count 11, limits 256Mi, env var LEDGER_API_TOKEN from a Secret reference (name only recorded). Oddity: label pod-template-hash 5c8d7b9f4c vs RS hash 6d4f8a2b7c |
| W1-Q6 | `logs <pod> --previous --tail=50` for each pod | `k8s-08.txt` | fatal "config: required environment variable LEDGER_API_BASE_URL is not set" (config/load.go:58), 19 ms after "starting" |
| W1-Q7 | `get-metric-data` x3 windows, payments-jobs + payments-jobs-dlq, Period 300 Maximum | `cw-01.json` (payments-jobs), `cw-02.json` (DLQ) for the incident window; previous and -7d windows: no overlap with any row, `_default.txt` `{}` | backlog 10-30 at 10:30-10:50, 74 at 10:55, 1060 at 11:00, then +~986 per 5 min to 5989 at 11:25; DLQ 0 throughout; no points before 10:30; previous and -7d empty |
| W1-Q8 | `get-metric-data` 14 days ending 09:28, Period 3600 Maximum | no overlap, `_default.txt` `{}` | empty reply, no recurrence data |

Files written: `ledger.md` (Impact, Windows, Recurrence provisional, Timeline, Hypotheses, Code repos, Query log W1, Gaps, Lesson candidates) before wave results were used in chat. Mapping notes: `cw-01.json` was read for the `payments-jobs` request, `cw-02.json` for `payments-jobs-dlq`; the world has no rows for other windows.

### Message 4 (verbatim, after wave 1: impact block, change list, hypotheses, wave 2 printed)

```text
Wave 1 is in the ledger. No instruction-like text was found in any output.

Impact as of 11:29 UTC (13:29 local, Europe/Paris)
Symptom:   payments-worker pods exit at startup (exit code 1) and sit in CrashLoopBackOff; the Deployment shows 0/3 available; the payments-jobs queue backlog grows with nothing consuming it.
Affected:  prod, namespace payments, all 3 replicas. payments-jobs visible messages: 5,989 at 11:25 UTC against 10-30 between 10:30 and 10:50 (about +197 per minute since 10:55); dead-letter queue 0. Payment capture and refunds are the core flows served by this worker (environment.md): delayed rather than failed. Customer-facing: Assumed, because the queue-to-flow link is inferred from the name only.
Since:     10:52 UTC (12:52 Europe/Paris), first crash within a minute of the Helm upgrade · ongoing: yes
Severity:  SEV1 (suggested) because a core flow's only worker has 0 of 3 replicas available and its queue is growing (default scale: customer-facing core flow down). The incident owner decides.
Basis:     request/error metrics do not exist for this service (no SLO, no load balancer, no APM); queue depth and pod state are the only signals · W1-Q7, W1-Q4, W0-Q5 · measurements Confirmed, impact on payments Assumed; baseline is only 20 minutes
Third party in the path: none known

What wave 1 shows, with labels:
- Onset: Helm revision 31 was applied at 10:52:20 UTC, the old ReplicaSet was scaled to 0 at 10:52:21 (Recreate strategy), the new pods started at 10:52:36 and the first BackOff is at 10:53:02 (W0-Q7, W1-Q2, W1-Q3). Confirmed.
- Mechanism: every new pod's previous container logged, at its latest restart, `config: required environment variable LEDGER_API_BASE_URL is not set` and exited 1 about 19 ms after starting (W1-Q5, W1-Q6). Confirmed for the latest restart of each pod. There is no log store, so the first crash's line cannot be read.
- Ruled out so far: probe failures, image pull or scheduling, OOM (exit 1, Error), a ledger outage or timeout (the process dies before any network call), evictions (W1-Q2, W1-Q4, W1-Q5, W1-Q6). A Secret-related failure behind the first error cannot be excluded without reading Secrets, which this run does not do.
- Old against new: new ReplicaSet 6d4f8a2b7c, 3/3 pods crash-looping with the mechanism in each pod's own previous log. Old ReplicaSet 84c1e9d3f5 (revision 14, 11 days): 0/3 pods with BackOff or other Warning events in the retained events before it was scaled down, and the queue backlog stayed at 10-30 until 10:50 (the consumer link is unverified). The old pods' own logs are gone.
- Window: the true onset (10:52) is 84 minutes after the start of my default two-hour window (09:28). Wave 2 re-anchors to 10:22-11:28 UTC (12:22-13:28 Europe/Paris), and moves the previous and -7d windows and the recurrence pull with it. The queue-depth pulls for the previous window, the -7d window and the 14 days before returned empty replies (no points before 10:30 UTC today), so recurrence has no signal yet; I am not reading empty as zero.
- Recurrence: provisionally `unclassified` (no alarm, no usable 14-day signal).

Ranked hypotheses (each with its falsification query; the first one runs first):
H1 (top). The config change in Helm revision 31 (commit d81e4b7, "rename ledger endpoint key to match the shared ledger client") left LEDGER_API_BASE_URL unset in the new pods. Falsified if the live ConfigMap payments-worker-config does contain that key, or if the commit does not touch it.
H8. sched: a schedule (CronJob, EventBridge rule, Scheduler schedule) or an automated apply caused the 10:52 change. Falsified if no schedule exists or fires near 10:52. Recurrence is unclassified, so schedules are listed before blaming the commit.
H2-H7 are ruled out above (probes, image/scheduling, OOM, ledger outage, credentials as the observed cause, evictions); H6 keeps the Secret caveat.

Wave 2 (re-anchor, falsification, slower change sources). Commands in full:

1. date -u +%H:%M:%S; for w in "2026-10-24T09:16:00Z 2026-10-24T10:22:00Z 300" "2026-10-10T10:52:00Z 2026-10-24T10:52:00Z 3600"; do set -- $w; aws cloudwatch get-metric-data --profile prod-ops --region us-east-1 --start-time "$1" --end-time "$2" --metric-data-queries '[{"Id":"jobs","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"payments-jobs"}]},"Period":'"$3"',"Stat":"Maximum"}},{"Id":"dlq","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"payments-jobs-dlq"}]},"Period":'"$3"',"Stat":"Maximum"}}]' --output json; done
   (the re-anchored -7d window 2026-10-17 10:22-11:28 lies inside the -7d window already queried in W1-Q7, so that result is reused, not re-run)
2. git -C ~/src/payments-deploy show d81e4b7 -- charts/payments-worker
3. kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments get configmap payments-worker-config -o json | jq '{keys: (.data | keys), managedFields: [.metadata.managedFields[]? | {manager, operation, time}]}'
4. kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n payments get cronjob; aws events list-rules --profile prod-ops --region us-east-1 --name-prefix payments; aws scheduler list-schedules --profile prod-ops --region us-east-1 --name-prefix payments
5. TZ=UTC aws cloudtrail lookup-events --profile prod-ops --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-24T08:52:00Z --end-time 2026-10-24T11:07:00Z --query "Events[?Resources[?contains(ResourceName || '', 'payments')]].[EventTime, EventSource, EventName, EventId]" --output text
6. History lookup, now that the ranking exists (local file reads only): grep -ril -e payments-worker -e payments-jobs -e CrashLoopBackOff .culiops/sre-investigate/incidents/ ; grep -i failure-mode .culiops/sre-investigate/lessons.md

The ConfigMap is read as key names only (values are not recorded). CloudTrail does not log in-cluster Helm or kubectl changes, so an empty result there cannot exonerate an in-cluster apply; the Helm record and the git log are the apply evidence.
```

## Wave 2 (re-anchor, falsification, slower change sources)

Commands exactly as printed in Message 4. Start 11:31 (clock assumed). Ledger rows W2-Q1..Q5 written before the results were used.

| ID | Command (short) | World file | Key facts |
|---|---|---|---|
| W2-Q1 | `get-metric-data` x2 (previous 09:16-10:22 Period 300; 14d ending 10:52 Period 3600), payments-jobs + DLQ | previous: no overlap, `_default.txt` `{}`; 14d: overlaps 10:30-10:52, `cw-01.json` / `cw-02.json` clipped to 10:30-10:50 and aggregated to one hourly point with Maximum | previous empty; 14d = one point (hour 10:00Z) jobs 30, DLQ 0. The re-anchored -7d window is inside W1-Q7's -7d window, so reused (empty), not re-run. Simulation note: the INDEX says to sum points for a coarser period; for a Maximum-statistic gauge I took the maximum |
| W2-Q2 | `git -C ~/src/payments-deploy show d81e4b7 -- charts/payments-worker` | `git-02.txt` | values-prod.yaml, `config:`: key LEDGER_API_BASE_URL renamed to LEDGER_BASE_URL; other keys unchanged |
| W2-Q3 | `get configmap payments-worker-config -o json \| jq` (keys and managedFields only) | `k8s-09.yaml` (table P1, `payments-worker-config`) | keys: PAYMENTS_CURRENCY_DEFAULT, PAYMENTS_QUEUE_URL, PAYMENTS_WORKER_CONCURRENCY, LEDGER_BASE_URL; no LEDGER_API_BASE_URL; no managedFields in reply; PAYMENTS_QUEUE_URL names payments-jobs. Values withheld from the ledger |
| W2-Q4 | `get cronjob`; `aws events list-rules --name-prefix payments`; `aws scheduler list-schedules --name-prefix payments` | `_empty.txt`; `_default.txt` `{}`; `_default.txt` `{}` | no CronJobs, rules or schedules |
| W2-Q5 | `aws cloudtrail lookup-events` ReadOnly=false 08:52-11:07 | `_default.txt` `{}` | no matching write events |
| (local) | `grep -ril -e payments-worker -e payments-jobs -e CrashLoopBackOff .culiops/sre-investigate/incidents/`; `grep -i failure-mode .culiops/sre-investigate/lessons.md` | `_empty.txt` | no history, no lessons (ls-01 earlier showed neither exists) |

Results: H1 supported, H8 ruled out within scope. Re-anchored recurrence: `unclassified`.
Files written: `ledger.md` (Query log W2, Hypotheses, Recurrence, Memory, Gaps, Code repos), `profile.md` (queue link verified, ConfigMap keys by name, ledger downstream (unverified), schedules none).

### Message 5 (verbatim, after wave 2; wave 3 printed)

```text
Wave 2 is in the ledger. Windows re-anchored to 10:22-11:28 UTC (12:22-13:28 Europe/Paris); the new -7d window is inside the one already queried, so that result was reused. Nothing instruction-like found.

Falsification of H1 came back negative, i.e. the hypothesis survived:
- The commit d81e4b7 changes charts/payments-worker/values-prod.yaml: under config:, the key LEDGER_API_BASE_URL is renamed to LEDGER_BASE_URL (W2-Q2). Confirmed.
- The live ConfigMap payments-worker-config has the keys PAYMENTS_CURRENCY_DEFAULT, PAYMENTS_QUEUE_URL, PAYMENTS_WORKER_CONCURRENCY and LEDGER_BASE_URL, and no LEDGER_API_BASE_URL (W2-Q3). Confirmed (current state). The pods load that ConfigMap whole (envFrom, Optional: false), and the app logs that it requires LEDGER_API_BASE_URL (W1-Q6).
- Old against new: new ReplicaSet 6d4f8a2b7c, 3/3 pods crash-looping with the mechanism in each pod's own previous log; old ReplicaSet 84c1e9d3f5, 0/3 pods with Warning events in the retained events before scale-down, backlog steady at 10-30 until 10:50, and the pre-change values file supplied the old key name. Not earlier than the rollout: apply 10:52:20, first BackOff 10:53:02.
- Schedules (H8): no CronJob, EventBridge rule or Scheduler schedule named payments*, and no CloudTrail write events on payments resources (W2-Q4, W2-Q5). Ruled out within that scope; what triggered the Helm apply is not visible to me.
- History: nothing in incidents/ or lessons.md.

Cause so far: Confirmed for the crash loop (change, mechanism and timing all cited). One link is weaker: that the crash loop is why the backlog grows. The worker is configured for payments-jobs (PAYMENTS_QUEUE_URL), and growth starts between 10:50 and 10:55, but I have not shown that consumption stopped or that no other consumer exists. That link is Likely until wave 3 answers it.

Recurrence: `unclassified` (no alarm; the queue metric has one hourly point in 14 days). Gap recorded.

Wave 3 (last allowed wave in Fast mode): one query to try to disprove the backlog link. Command in full:

1. date -u +%H:%M:%S; aws cloudwatch get-metric-data --profile prod-ops --region us-east-1 --start-time 2026-10-24T10:22:00Z --end-time 2026-10-24T11:28:00Z --metric-data-queries '[{"Id":"sent","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"NumberOfMessagesSent","Dimensions":[{"Name":"QueueName","Value":"payments-jobs"}]},"Period":300,"Stat":"Sum"}},{"Id":"received","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"NumberOfMessagesReceived","Dimensions":[{"Name":"QueueName","Value":"payments-jobs"}]},"Period":300,"Stat":"Sum"}},{"Id":"deleted","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"NumberOfMessagesDeleted","Dimensions":[{"Name":"QueueName","Value":"payments-jobs"}]},"Period":300,"Stat":"Sum"}}]' --output json
```

## Wave 3 (Fast mode's last allowed wave)

Command exactly as printed in Message 5. Start 11:33 (clock assumed). Row W3-Q1 written to the ledger before the result was used.

| ID | Command (short) | World file | Key facts |
|---|---|---|---|
| W3-Q1 | `get-metric-data` NumberOfMessagesSent / Received / Deleted (Sum, 300) for payments-jobs, 10:22-11:28 | no INDEX row for these metric names, so `_default.txt` `{}` | empty reply; consumption not shown to stop; backlog link stays Likely; gap recorded |

Files written: `ledger.md` (W3 row, Gaps, Hypotheses note, Lesson candidates). Budget at end: 18/20 evidence queries (plus 4 access checks), 15/100 CloudWatch metric requests, 0 GB logs.

## Phase 5: conclude

Stop rule: Fast mode's third wave was used (waves 1, 2, 3 after wave 0 and the profile build). H1 reached Confirmed for the crash loop; H2 to H8 are Ruled out. `report.md` is at `out/runs/payments-worker-prod-20261024-1128/report.md` (report saved separately).

### Message 6 (verbatim, TL;DR inline, then path, then cost)

```text
Investigation finished: payments-worker prod.

TL;DR
Cause:             Commit d81e4b7 renamed the config key LEDGER_API_BASE_URL to LEDGER_BASE_URL; Helm revision 31 applied it at 10:52:20 UTC (12:52:20 Europe/Paris). payments-worker 5.2.0 (image unchanged) still requires LEDGER_API_BASE_URL, so all 3 new pods exit with code 1 at startup and crash-loop. Label: Confirmed.
Weakest link:      Step 3b, "the crash loop is why the payments-jobs backlog grows": Likely (consumption metrics returned no data; other consumers of the queue not excluded). It caps the claim about the backlog, not the crash-loop cause, whose change, mechanism and timing are each cited.
Impact:            Prod, namespace payments: 0 of 3 workers available since 10:52 UTC, ongoing at 11:28 UTC (13:28 Europe/Paris). payments-jobs backlog 5,989 messages at 11:25 UTC against 10-30 before 10:50, about +197 per minute; dead-letter queue 0.
Severity:          SEV1 (suggested): a core flow's only worker has no available replica and its queue is growing. The incident owner decides.
Pattern:           unclassified (no alarm, no usable 14-day history) · Assumed.
Recommended action: First, make the key the chart renders and the key the app reads agree again: roll the release back to revision 30 or revert the rename, through your normal deploy path after a pre-flight check. Then watch the backlog drain (about 6,000 messages and rising) and the ledger service while it does. Details in the report.

Report: .culiops/sre-investigate/runs/payments-worker-prod-20261024-1128/report.md
Ledger: .culiops/sre-investigate/runs/payments-worker-prod-20261024-1128/ledger.md

open items need your input (no consumption metrics, no log store, no app source repo, no apply record; see Gaps).

Cost: 18 evidence queries (plus 4 access checks) · 0 GB of logs scanned · 15 CloudWatch metric requests · well under 0.01 USD in metered charges
```

## Phase 6: record

### Message 7 (verbatim, diff proposal; nothing written)

```text
Record phase: proposed additions under .culiops/sre-investigate/. Nothing is written until you reply; accept, edit or skip each item.

1. NEW incidents/2026-10-24-payments-worker.md
+ ---
+ id: 2026-10-24-payments-worker-prod-config-key-rename
+ date: 2026-10-24
+ service: payments-worker
+ env: prod
+ siblings: [all]
+ window_utc: 2026-10-24T10:22:00Z/2026-10-24T11:28:00Z
+ symptoms: [crash-restart, queue-backlog]
+ cause_category: config
+ cause: Helm values key LEDGER_API_BASE_URL renamed to LEDGER_BASE_URL (commit d81e4b7, Helm revision 31) while app 5.2.0 requires the old name; every pod exits 1 at startup
+ deps: [payments-jobs, ledger-service]
+ label: Confirmed
+ mode: fast
+ time_to_cause_min: 3
+ run: runs/payments-worker-prod-20261024-1128
+ ---
+ What happened: a values-only Helm upgrade renamed a config key; the unchanged app could not find the key it requires and all 3 pods crash-looped from 10:52 UTC, so payments-jobs filled up.
+ Causal chain: trigger Confirmed (key rename applied in Helm revision 31) · mechanism Confirmed (fatal "required environment variable ... is not set", ConfigMap lacks the key) · symptom: pods crash-loop Confirmed, backlog Likely.
+ What found it: kubectl logs --previous on a crashing pod (W1-Q6), then the values diff and the live ConfigMap keys (W2-Q2, W2-Q3).
+ What did not help: queue-depth history (empty before 10:30), schedule and CloudTrail listings (empty).
+ Follow-ups raised: align key names or roll back; chart-pipeline check of required variables; queue age alarm; log store; read-only role for on-call.

2. NEW lessons.md (5 lines, each with its query ID; the time to cause above is from an assumed clock)
+ - type: failure-mode | service: payments-worker | source: kubectl | statement: a rename of a key under config in the Helm values file, with an unchanged app image, leaves a required env var unset; pods exit 1 within 20 ms and the previous-container log says required environment variable X is not set | run: payments-worker-prod-20261024-1128 | query_id: W1-Q6 | re-verify: no
+ - type: process | service: payments-worker | source: kubectl | statement: with no log store, kubectl logs --previous holds only the last terminated container of each pod, so read event firstTimestamp for the first occurrence of a crash | run: payments-worker-prod-20261024-1128 | query_id: W1-Q6 | re-verify: no
+ - type: identifier | service: payments-worker | source: kubectl | statement: pods carry label pod-template-hash=5c8d7b9f4c while the owning ReplicaSet and the pod names carry 6d4f8a2b7c; map pods to a ReplicaSet through Controlled By, not the label | run: payments-worker-prod-20261024-1128 | query_id: W1-Q5 | re-verify: yes
+ - type: process | service: any | source: aws | statement: the IAM simulation reply for the PlatformOperator role did not match the requested action list (3 requested actions missing, 3 unrequested rows); compare the reply rows with the fixed list | run: payments-worker-prod-20261024-1128 | query_id: W0-Q2 | re-verify: no
+ - type: process | service: payments-worker | source: cloudwatch | statement: payments-jobs queue-depth pulls return nothing before 10:30 UTC on 2026-10-24 and nothing for previous, -7d or 14-day windows, and NumberOfMessages Sent/Received/Deleted return empty replies; do not plan recurrence on queue depth | run: payments-worker-prod-20261024-1128 | query_id: W1-Q8 | re-verify: yes

3. NEW profiles/payments-worker-prod.md = this run's profile.md (copy), with: Deployment payments-worker (strategy Recreate), ConfigMap payments-worker-config (key names only), Helm release payments-worker, queues payments-jobs and payments-jobs-dlq (the worker is configured for payments-jobs, verified), internal ledger service downstream (unverified), no Service/Ingress/HPA/CronJob/schedule found, no log, metric or trace backend.

Candidate for the skill itself (not part of this diff, to be proposed in a normal session): check that an IAM simulation reply contains exactly the requested actions before reading it as a read-only or write result.
```

## Operator lines after the opening request

None. The script has only line 1, so Phase 6 received no reply and **nothing was written** to `incidents/`, `lessons.md` or `profiles/`.

## Files written (all under `out/`)

- `runs/payments-worker-prod-20261024-1128/ledger.md` (created in Phase 0, rewritten after wave 0, the profile step, and each wave)
- `runs/payments-worker-prod-20261024-1128/profile.md` (run profile, written after the helper returned; updated after wave 2)
- `runs/payments-worker-prod-20261024-1128/raw/` and `raw/helper/` (created, empty: no raw pull was saved; every result was small enough to read inline)
- `run-log.md` (this file)
- `report.md`: report saved separately.
- NOT written: `environment.md` (already existed), `incidents/`, `lessons.md`, `profiles/` (Phase 6, no operator reply)

## World files opened (each mapped by one of the commands above)

`environment.md`, `ls-01.txt`, `_empty.txt`, `_default.txt`, `sts-01.json`, `iam-01.json`, `iam-02.json`, `k8s-01.txt`, `k8s-02.txt`, `k8s-03.txt`, `k8s-12.txt`, `k8s-04.txt`, `k8s-13.txt`, `sqs-01.json`, `helm-03.txt`, `git-01.txt`, `k8s-10.txt`, `k8s-11.txt`, `k8s-06.json`, `helm-01.txt`, `k8s-14.txt`, `k8s-07.txt`, `k8s-08.txt`, `cw-01.json`, `cw-02.json`, `git-02.txt`, `k8s-09.yaml`.
Not opened (no command of mine mapped to them): `iam-03.txt`, `k8s-05.txt`, `k8s-15.yaml`, `k8s-16.yaml`, `git-03.txt`, `helm-02.yaml`. In particular `helm get values` was not run (the changes playbook forbids it; the values file was read from git instead).

## Simulation notes

- `date -u` has no INDEX row, so wave start times and "now" (11:28:00 UTC) come from the world's stated reference time, and times to cause are approximate.
- Each wave's commands were printed in a message (Messages 3, 4, 5) before the world files they map to were read; results were written to the ledger before being used in chat.
- Maximum was used to aggregate the clipped 5-minute SQS points into the hourly bucket of W2-Q1 (the INDEX says to sum for coarser periods; summing a gauge's maxima would be meaningless).
