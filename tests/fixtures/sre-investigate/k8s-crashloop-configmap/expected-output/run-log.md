# Run log: sre-investigate, case-a (notify-worker, prod)

Run directory: `notify-worker-prod-20261022-0850`
Output root used for writes (stands for `.culiops/sre-investigate/`): `out/`

Simulation notes that apply to the whole run:

- Commands were not executed. Each command was matched against `world/INDEX.md` and only the mapped file was read. `_default.txt` / `_empty.txt` were used for unmatched commands, as the INDEX rules say.
- `date -u` has no INDEX row, so it returned nothing. "Now" is 08:50:00 UTC on 2026-10-22, taken from the INDEX note that event ages are relative to 08:50:00 UTC (and consistent with pod age 35m since 08:14:33). All Start times in the ledger carry an asterisk for that reason.
- World files read, and the command that mapped each one: sts-01 (W0-Q1, W0-Q2), iam-01 (W0-Q2), iam-02 (W0-Q2), k8s-01 (W0-Q3), k8s-02 (W0-Q3), k8s-03 (W0-Q4), ls-01 (pre-wave), environment.md (pre-wave), k8s-12 / k8s-13 (W0-Q5), sqs-01 (W0-Q6), git-01 (W0-Q7), k8s-04 (W1-Q1), k8s-06 (W1-Q2), k8s-10 (W1-Q3), k8s-11 (W1-Q4), k8s-14 (W1-Q5), helm-01 (W1-Q6), cw-01 and cw-02 (W1-Q8, incident window), k8s-07 (W2-Q1), k8s-08 (W2-Q2), k8s-09 (W2-Q3), git-02 (W2-Q4). `_empty.txt` and `_default.txt` for the unmatched calls listed below. No other world file was opened. The files k8s-05, k8s-15, k8s-16, git-03, helm-02, helm-03 were never read (no command of mine mapped to them; `helm get values` was deliberately not run).
- Operator lines: only line 1 exists in `operator-script.md`. It was given as the opening request. No later line was received, because no later line has a cue that could happen in this run (the script has only one line).

## Operator line received

1. (at the start) `notify-worker pods in prod are crash-looping and emails aren't going out. Fast mode.`

## Phase 0, step 1-3: output root, environment, mode

Commands (printed in the first message below, then run):

| # | Command | Mapped to | Key facts |
|---|---|---|---|
| a | `command -v agentbox-env` | `_empty.txt` (exit 1) | Culibox absent; nothing said about Culibox |
| b | `echo "${CULIOPS_HOME:-}"` | `_empty.txt` | CULIOPS_HOME unset: root is `.culiops/sre-investigate/` at the repo root |
| c | `git rev-parse --show-toplevel` | `_empty.txt` | printed nothing; the case directory is taken as the repo root (noted to the operator) |
| d | `git check-ignore -q .culiops/sre-investigate` | `_empty.txt` (exit 0) | ignored by git |
| e | `ls .culiops/sre-investigate` | `ls-01.txt` | only `environment.md`; no `profiles/`, `lessons.md`, `incidents/` |
| f | `cat .culiops/sre-investigate/environment.md` | `environment.md` | timezone UTC; profile prod-read (111122223333, us-east-1); context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, ns `notify`; kubectl/Helm + CloudWatch metrics only; no token env vars; no budgets (template Fast defaults apply); helm values repo `example-org/notify-deploy` clone `~/src/notify-deploy`; app code `example-org/notify-worker` via gh; core flow = transactional email |
| g | `date -u +%Y%m%d-%H%M` | `_empty.txt` | no output; clock taken from the case reference time (see notes) |

### Message 1 (first message, verbatim)

```text
Mode: Fast. You said so, and the crash loop is ongoing.

Phase 0 commands, run before wave 0:
  command -v agentbox-env
  echo "${CULIOPS_HOME:-}"
  git rev-parse --show-toplevel
  git check-ignore -q .culiops/sre-investigate
  ls .culiops/sre-investigate
  cat .culiops/sre-investigate/environment.md
  date -u +%Y%m%d-%H%M

Output root: .culiops/sre-investigate/ at the repo root. It is local and is never committed. `git check-ignore -q` exited 0, so git already ignores it. (`git rev-parse --show-toplevel` printed nothing here, so I took the current directory as the repo root.)

I read .culiops/sre-investigate/environment.md: timezone UTC; AWS profile prod-read (account 111122223333, us-east-1); Kubernetes context arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace notify; CloudWatch metrics and kubectl/Helm only (no log backend, no token-based backend); core flow = transactional email. Nothing else exists under the root yet (no profile, lessons or incident history), so the service profile is built from scratch.

Window: you gave no onset, so the Fast default applies: the last two hours, 2026-10-22 06:50 to 08:50 UTC (local time is UTC per environment.md). The shell clock returned nothing here, so "now" (08:50:00 UTC) is taken from the case's reference time. If wave 1 shows a true onset far from this window I will re-anchor on it.

Run directory: .culiops/sre-investigate/runs/notify-worker-prod-20261022-0850/ (ledger.md, profile.md, raw/).
```

## Phase 0, step 4-5: run directory, ledger, problem statement

Files written: `runs/notify-worker-prod-20261022-0850/ledger.md` (copy of the template, Problem filled in: what / where / when / who / trigger = chat report / mitigations "none known" / assumptions: default two-hour window, zone UTC from environment.md, now = 08:50:00 UTC, template Fast budgets), `raw/`.

## Wave 0 (access and intake)

Printed in full, then run (the same text as sent to the operator):

```text
Wave 0 (access and intake). RUN=.culiops/sre-investigate/runs/notify-worker-prod-20261022-0850/raw
CTX=arn:aws:eks:us-east-1:111122223333:cluster/prod

Call 1
date -u +%H:%M:%S; aws sts get-caller-identity --profile prod-read --region us-east-1 --output json

Call 2 (AWS write-check, fixed list of 10 actions)
arn=$(aws sts get-caller-identity --profile prod-read --region us-east-1 --query Arn --output text)
role=${arn#*:assumed-role/}; role=${role%%/*}
role_arn=$(aws iam get-role --profile prod-read --region us-east-1 --role-name "$role" --query Role.Arn --output text)
aws iam simulate-principal-policy --profile prod-read --region us-east-1 \
  --policy-source-arn "$role_arn" \
  --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances \
    ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy \
    iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode \
    cloudformation:DeleteStack \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text

Call 3
kubectl auth whoami --context "$CTX"; kubectl config current-context

Call 4 (Kubernetes write-check)
kubectl auth can-i --list --context "$CTX" --namespace notify

Not run in wave 0, and why: no token-based backend is listed (no token check); no log source is listed (no log probe); no stored profile or lessons exist; the trigger is a report, not an alarm (no alarm history); no error tracker, ticket, WAF symptom.
```

| ID | Command | Mapped to | Key facts |
|---|---|---|---|
| W0-Q1 | call 1 | `sts-01.json` (`date` unmatched, no output) | Account 111122223333 = environment.md; assumed-role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b (session name not recorded) |
| W0-Q2 | call 2 | `sts-01.json`, `iam-01.json`, `iam-02.json` | role path `/aws-reserved/sso.amazonaws.com/`; simulation rows: s3:PutObject, s3:DeleteObject, ec2:TerminateInstances, ecs:UpdateService, iam:PutRolePolicy, rds:ModifyDBInstance, lambda:UpdateFunctionCode = implicitDeny (7 of my 10); no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack; three rows I did not ask for (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy) = implicitDeny. No `allowed` anywhere, so no boxed warning. The missing rows are recorded as a gap. |
| W0-Q3 | call 3 | `k8s-02.txt`, `k8s-01.txt` | user = role ReadOnly, groups eks-readonly + system:authenticated; current context = the environment.md context |
| W0-Q4 | call 4 | `k8s-03.txt` | rows: create on selfsubjectreviews / selfsubjectaccessreviews / selfsubjectrulesreviews (excluded by the skill's rule); `*.*` get list watch (read-only, includes Secrets); non-resource URLs get. No write verbs. No boxed warning. |

### Message 2 (after wave 0, verbatim)

```text
Write check, prod-read: read-only confirmed (simulation): none of the broad write actions came back allowed. Limit: only 7 of the 10 requested actions returned a row (all implicitDeny). ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack returned no row, and the reply held three actions I did not ask for (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy; also implicitDeny). I recorded that as a gap. This is not a full proof; resource-scoped writes are not covered.

Write check, arn:aws:eks:us-east-1:111122223333:cluster/prod / notify: no write verbs in notify (the only `create` rows are the three access-review APIs, which do not count). One thing to know: the binding allows get/list/watch on all resources, which includes Secrets. I will not read any Secret.

Identity: prod-read = account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly_*; the Kubernetes user is the same role, group eks-readonly.

Gaps so far: (1) three simulation rows missing, above; (2) environment.md lists no log backend, so logs are limited to kubectl pod logs (current and previous container only).
```

Ledger: Access table, Gaps, Memory (no lessons, no incidents dir) written (ledger v1).

## Build profile (helper, TASK: PROFILE, cheapest tier, simulated inline)

Dispatch: `TASK: PROFILE`, Service notify-worker, Environment prod, identifier lessons "none", `model` at the cheapest tier (passed explicitly). The helper ran one wave of three calls (counted as W0-Q5..Q7, no wave cap used). While it ran, the IaC history call (W0-Q7) was the change-correlation query that needs no identifiers, so it was shared with wave 1.

[helper, cheapest tier] Commands printed and run:

```text
kubectl --context "$CTX" -n notify get deploy; kubectl --context "$CTX" -n notify get svc,ingress,hpa; kubectl --context "$CTX" -n notify get configmap
aws sqs list-queues --profile prod-read --region us-east-1
git -C ~/src/notify-deploy log origin/HEAD -n 10 -- charts/notify-worker
```

| ID | Mapped to | Key facts |
|---|---|---|
| W0-Q5 | `k8s-12.txt` (get deploy), `_empty.txt` (get svc,ingress,hpa: no INDEX row), `k8s-13.txt` (get configmap) | Deployment notify-worker READY 0/3, UP-TO-DATE 3, AVAILABLE 0, age 211d; svc/ingress/hpa: no output; ConfigMaps kube-root-ca.crt and notify-worker-config (4 keys) |
| W0-Q6 | `sqs-01.json` | queues notify-outbound, notify-outbound-dlq |
| W0-Q7 | `git-01.txt` | 3f9a1c2 (author date Thu Oct 22 08:03:41 2026 +0000) "notify-worker: align config key names with the shared SMTP chart (#214)"; 9e8d7c6 (Wed Oct 7 09:51:09 2026) "raise concurrency to 8 (#201)" |

Helper returned the profile (Status partly unverified; queue names (unverified) until a metric returned data; svc/ingress/hpa and every backend not in environment.md marked (unverified)). The main session re-applied Constraint 14 (no promotion without data) and wrote `profile.md` (v1). It was updated later as data arrived (log label, sidecar, compute, queues, code row, baseline) after wave 1 and wave 2.

### Message 3 (profile shown, verbatim)

```text
Service profile built (continuing without waiting; tell me if anything is wrong):
- notify-worker, prod. Cluster context arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace notify, profile prod-read, us-east-1.
- Compute: Deployment notify-worker (0/3 ready, verified), ConfigMaps notify-worker-config (4 keys) and kube-root-ca.crt (verified). No Service, Ingress or HPA output (unverified).
- Queues: notify-outbound and notify-outbound-dlq, listed by SQS (unverified until a metric returns data).
- IaC: example-org/notify-deploy, clone ~/src/notify-deploy, path charts/notify-worker (verified by git log). App code example-org/notify-worker via gh (not queried yet).
- Logs: no log backend; only kubectl logs. Traces, Prometheus, error tracker, dashboards: none listed.
- Sibling set: the Deployment's replicas (pod-template-hash tells revisions apart).
- Core flow: transactional email, critical.
```

## Wave 1

### Message 4 (commands printed in full, verbatim)

```text
Wave 1 (changes, golden signals, recurrence). RUN=.culiops/sre-investigate/runs/notify-worker-prod-20261022-0850/raw
CTX=arn:aws:eks:us-east-1:111122223333:cluster/prod
Eight calls, within the ten-call guide. Windows for this wave are the default ones: incident 2026-10-22T06:50:00Z-08:50:00Z, previous 04:50:00Z-06:50:00Z, minus 7 days 2026-10-15T06:50:00Z-08:50:00Z, recurrence 14 days ending 2026-10-22T06:50:00Z at one-hour resolution.

Call 1
date -u +%H:%M:%S; kubectl --context "$CTX" -n notify get pods -o wide | tee "$RUN/k-pods.txt"

Call 2
kubectl --context "$CTX" -n notify get events --sort-by=.lastTimestamp -o json | jq -r '.items[] | [(.firstTimestamp // .eventTime), .lastTimestamp, (.count // .series.count // 1), .reason, .involvedObject.name, (.message // "" | .[:300])] | @tsv' > "$RUN/k-events.tsv"

Call 3
kubectl --context "$CTX" -n notify rollout history deployment/notify-worker

Call 4
kubectl --context "$CTX" -n notify get rs --sort-by=.metadata.creationTimestamp

Call 5
kubectl --context "$CTX" -n notify describe deploy notify-worker

Call 6
helm history notify-worker --kube-context "$CTX" -n notify --max 10

Call 7
kubectl --context "$CTX" get cronjobs -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,SCHEDULE:.spec.schedule,TZ:.spec.timeZone,SUSPEND:.spec.suspend,LAST:.status.lastScheduleTime'

Call 8
cat > "$RUN/q-sqs-300.json" <<'EOF'
[ {"Id": "backlog", "MetricStat": {"Period": 300, "Stat": "Maximum", "Metric": {"Namespace": "AWS/SQS", "MetricName": "ApproximateNumberOfMessagesVisible", "Dimensions": [{"Name": "QueueName", "Value": "notify-outbound"}]}}},
  {"Id": "dlq", "MetricStat": {"Period": 300, "Stat": "Maximum", "Metric": {"Namespace": "AWS/SQS", "MetricName": "ApproximateNumberOfMessagesVisible", "Dimensions": [{"Name": "QueueName", "Value": "notify-outbound-dlq"}]}}} ]
EOF
sed 's/"Period": 300/"Period": 3600/' "$RUN/q-sqs-300.json" > "$RUN/q-sqs-3600.json"
for w in "incident 2026-10-22T06:50:00Z 2026-10-22T08:50:00Z q-sqs-300" "previous 2026-10-22T04:50:00Z 2026-10-22T06:50:00Z q-sqs-300" "minus7d 2026-10-15T06:50:00Z 2026-10-15T08:50:00Z q-sqs-300" "recur14d 2026-10-08T06:50:00Z 2026-10-22T06:50:00Z q-sqs-3600"; do
  read -r win ws we q <<< "$w"
  TZ=UTC aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries "file://$RUN/$q.json" --start-time "$ws" --end-time "$we" --output json > "$RUN/m-sqs-$win.json"
done

Notes: Period 300 because SQS publishes its queue metrics every five minutes. Call 8 requests 8 metric requests in total. The pod logs and `describe pod` wait for wave 2 because the pod names are only known after call 1. No Helm values or manifests are read (`helm get values` is not run).
```

### Wave 1 results (commands in order, mapped file, key facts)

| ID | Mapped to | Key facts |
|---|---|---|
| W1-Q1 | `k8s-04.txt` | 3 pods `notify-worker-5c8d7b9f4c-{8wq2d,jt6kz,x4p9n}`, READY 0/1, CrashLoopBackOff, 11 restarts each, age 35m |
| W1-Q2 | `k8s-06.json` | 08:14:21 scale-down of RS 7f6b8c5d2e (3 to 0) + Killing event; 08:14:33 scale-up RS 5c8d7b9f4c to 3, Scheduled; first Started 08:14:36 (12 starts by 08:47:56); first BackOff 08:15:02/03/05, counts 151/149/150, last 08:49:20/38/51. No FailedScheduling, ErrImagePull, Unhealthy, OOM, node events. Wrote `raw/k-events.tsv` (names, counts, times; no config values). |
| W1-Q3 | `k8s-10.txt` | revisions 6 and 7 |
| W1-Q4 | `k8s-11.txt` | RS 5c8d7b9f4c 3/3/0 ready 35m; RS 7f6b8c5d2e 0/0/0, 15d |
| W1-Q5 | `k8s-14.txt` | strategy Recreate; image tag 3.8.1; env from ConfigMap notify-worker-config; selector `app.kubernetes.io/instance` + `app.kubernetes.io/name`; Helm-managed; 0 available; no probe lines |
| W1-Q6 | `helm-01.txt` | rev 11 Oct 7 10:02:18 superseded; rev 12 Oct 22 08:14:20 deployed; chart notify-worker-1.8.0 and app 3.8.1 in both |
| W1-Q7 | `_empty.txt` (no INDEX row for cronjobs) | no output; recorded as "no CronJob listed, unverified whether empty or filtered" |
| W1-Q8 | incident: `cw-01.json` (notify-outbound), `cw-02.json` (notify-outbound-dlq); previous, minus7d, recur14d: `_default.txt` (`{}`) because the windows do not overlap the covered 07:50-08:45 | backlog 11, 13, 7, 27, 16, 120, 1710, 3300, 4890, 6480, 8070, 9660 (07:50 to 08:45, step 5 min); DLQ 0 on all 12 points; the other three windows returned no data. Wrote `raw/m-sqs-incident.tsv`. 8 metric requests. |

Phase 1 reading after wave 1:
- Siblings: 3 of 3 replicas fail together, so a shared cause (config or image), not per-pod capacity. Shape: step (0 ready at one minute, from 08:14:21), then a ramp in the queue.
- Re-anchor rule: the window came from the Fast default; the true onset 08:14:21 is 84 minutes after the window start and 36 minutes before now, so wave 2 re-anchors.
- Recurrence: no alarm, and the 14-day pull returned nothing, so classification waits for the re-anchored pull in wave 2.
- Ledger v2 written (query rows W1-Q1..Q8, Impact, Timeline, Recurrence pending, Windows note, Gaps): all rows are in `ledger.md` before the results are used below.

### Message 5 (verbatim)

```text
Wave 1 done (8 calls). What it shows:
- All 3 notify-worker pods are CrashLoopBackOff (0/3 ready, 11 restarts each). The Deployment uses the Recreate strategy: at 08:14:21 UTC the old ReplicaSet was taken from 3 pods to 0, and the new ReplicaSet's pods (hash 5c8d7b9f4c) started at 08:14:33-08:14:36 and have crashed since (first BackOff 08:15:02).
- Helm revision 12 was deployed at 08:14:20 UTC; chart version and image tag (3.8.1) are the same as revision 11, so the pod template changed through its config. The IaC repo has a commit from 08:03 UTC today touching charts/notify-worker ("align config key names with the shared SMTP chart (#214)").
- The outbound queue notify-outbound went from 16 messages (08:10) to 120 (08:15) to 9,660 (08:45): about +318 per minute; the DLQ is at 0.
- No CronJob listed; no scheduling, image-pull, probe or OOM events.
- CloudWatch returned no datapoints for the earlier windows (previous, minus 7 days, 14 days); there is no baseline yet.
The true onset is 08:14:21 UTC, 84 minutes after my default window starts, so I re-anchor the windows in the next wave.

Impact as of 08:50 UTC (08:50 local, UTC per environment.md)
Symptom:   All 3 notify-worker pods are CrashLoopBackOff (0/3 ready, 11 restarts each); the outbound email queue is not being drained: notify-outbound 16 messages at 08:10, 120 at 08:15, 9,660 at 08:45 (about +318/min); DLQ 0.
Affected:  prod, 3 of 3 replicas; core flow transactional email (customer-facing). Emails not being sent is inferred from the unconsumed queue; there is no sent-mail counter.
Since:     08:14:21 UTC (old pods stopped; first BackOff 08:15:02) · ongoing: yes
Severity:  SEV1 (suggested) because a customer-facing core flow (transactional email) has no worker available. The incident owner decides.
Basis:     Assumed (no SLO, no APM or load-balancer metrics in environment.md; queue depth and pod availability are the proxies) · W1-Q1, W1-Q8 · pod availability Confirmed, email non-delivery Likely
Third party in the path: none identified for the failure; the SMTP relay is on the send path, no contact route is recorded in environment.md.
```

## Phase 2 / Phase 3 (between wave 1 and wave 2)

- Recurrence first: no class yet (wave 2 pull); no `scheduled` sign (W1-Q7 empty; onset 1 s after the Helm upgrade).
- The Helm upgrade (08:14:20) and the 08:03 commit are the candidate change. Old-against-new split planned before any label: per-pod form (Recreate replaced every pod).
- Hypotheses written with falsification queries and ranked H1..H6 (ledger Hypotheses table). History lookup after ranking: `incidents/` does not exist (seen in the pre-wave listing), so no grep ran and there are no `from-history:` entries. No docs search (known failure mode not unfamiliar; no wiki access listed). Fast mode: no checkpoints.

### Message 6 (hypotheses and wave 2 commands, verbatim)

```text
Hypotheses, ranked (Fast mode: no checkpoint, so I go straight on). Each one carries the query that would disprove it.
H1  The prod values change in commit 3f9a1c2 (config key NOTIFY_SMTP_RELAY_HOST renamed to SMTP_RELAY_HOST), applied by Helm revision 12 at 08:14:20, leaves the new pods without a variable that notify-worker 3.8.1 needs, so each exits at startup. Disproved by: old pods failing the same way, an onset before 08:14:20, a different error in the previous-container log, or the live ConfigMap still holding the old key.
H2  Image pull or scheduling failure. Disproved by: pods Scheduled and Started (events).
H3  OOM or resource-limit kill. Disproved by: a termination reason other than OOMKilled / exit 137.
H4  Probe failures. Disproved by: no probes defined, no Unhealthy events.
H5  A dependency (SMTP relay, SQS, the notify-smtp secret) failing at startup. Disproved by: the process dying before any network call.
H6  A scheduled job or node churn. Disproved by: no CronJob, no node events, onset tied to the Helm upgrade.
The deploy is only a candidate until the old-against-new split is done; wave 2 runs that split together with the first disproving queries.

Wave 2 (disproving queries, change detail, re-anchored recurrence). RUN=.culiops/sre-investigate/runs/notify-worker-prod-20261022-0850/raw
CTX=arn:aws:eks:us-east-1:111122223333:cluster/prod
New windows (re-anchored on the onset 08:14:21 UTC; wave 1 keeps its old windows): incident 2026-10-22T07:44:00Z-08:50:00Z (inside wave 1's incident window, so it is reused, not re-run), previous 2026-10-22T06:38:00Z-07:44:00Z, minus 7 days 2026-10-15T07:44:00Z-08:50:00Z, recurrence 14 days 2026-10-08T08:14:21Z-2026-10-22T08:14:21Z.

Call 1
date -u +%H:%M:%S; for p in notify-worker-5c8d7b9f4c-8wq2d notify-worker-5c8d7b9f4c-jt6kz notify-worker-5c8d7b9f4c-x4p9n; do kubectl --context "$CTX" -n notify describe pod "$p"; done

Call 2
for p in notify-worker-5c8d7b9f4c-8wq2d notify-worker-5c8d7b9f4c-jt6kz notify-worker-5c8d7b9f4c-x4p9n; do kubectl --context "$CTX" -n notify logs "$p" -c notify-worker --previous --timestamps; done > "$RUN/k-previous-logs.txt"

Call 3
kubectl --context "$CTX" -n notify get configmap notify-worker-config -o json | jq -r '.data | keys[]' > "$RUN/c-configmap-keys.txt"; kubectl --context "$CTX" -n notify get configmap notify-worker-config -o jsonpath='{range .metadata.managedFields[*]}{.manager}{"\t"}{.operation}{"\t"}{.time}{"\n"}{end}'

Call 4
git -C ~/src/notify-deploy show 3f9a1c2 --format='%H %aI %s' -- charts/notify-worker/values-prod.yaml | sed -E 's/^([ +-][[:space:]]*[A-Za-z_][A-Za-z_0-9]*:)[[:space:]].*/\1 <value omitted>/' > "$RUN/c-iac-diff-names.txt"

Call 5
for w in "previous 2026-10-22T06:38:00Z 2026-10-22T07:44:00Z q-sqs-300" "minus7d 2026-10-15T07:44:00Z 2026-10-15T08:50:00Z q-sqs-300" "recur14d-reanchored 2026-10-08T08:14:21Z 2026-10-22T08:14:21Z q-sqs-3600"; do
  read -r win ws we q <<< "$w"
  TZ=UTC aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries "file://$RUN/$q.json" --start-time "$ws" --end-time "$we" --output json > "$RUN/m-sqs-$win.json"
done

Notes: config values are never stored: call 3 keeps key names only and call 4 strips the values from the diff. App code is not read: the image tag (3.8.1) is the same in both Helm revisions, so there is no app diff to read.
```

## Wave 2

| ID | Mapped to | Key facts |
|---|---|---|
| W2-Q1 | `k8s-07.txt` (describe pod, "same content for each pod apart from its name") | State Waiting CrashLoopBackOff; Last State Terminated, Reason Error, Exit Code 1, Started and Finished 08:47:56; Restart Count 11; memory limit 256Mi / request 128Mi, cpu limit 500m; env from ConfigMap notify-worker-config; SMTP_PASSWORD from key `password` of secret notify-smtp (reference only); annotation checksum/config; events Started x12 over 35m, BackOff x151 over 34m |
| W2-Q2 | `k8s-08.txt` (logs `--previous`, any pod) | per pod: "notify-worker 3.8.1 starting" 08:47:56.102, "loading configuration from environment" .118, fatal "config: required environment variable NOTIFY_SMTP_RELAY_HOST is not set" at config/load.go:58, .121 (19 ms after start). Same lines for all 3 pods in the world. Only the latest crash is readable. Wrote `raw/k-previous-logs.txt`. |
| W2-Q3 | `k8s-09.yaml` (configmap by name; the jsonpath call maps to the same file, which has no managedFields) | data keys NOTIFY_FROM_ADDRESS, NOTIFY_QUEUE_URL, NOTIFY_WORKER_CONCURRENCY, SMTP_RELAY_HOST; NOTIFY_SMTP_RELAY_HOST absent. Values deliberately not recorded or copied. managedFields: nothing returned. Wrote `raw/c-configmap-keys.txt`. |
| W2-Q4 | `git-02.txt` (show 3f9a1c2) | values-prod.yaml `config:` block: key NOTIFY_SMTP_RELAY_HOST removed, key SMTP_RELAY_HOST added, other keys unchanged. The sed in my command strips values; only names were kept in `raw/c-iac-diff-names.txt`. |
| W2-Q5 | `_default.txt` for previous and minus7d (`{}`: windows do not overlap 07:50-08:45); 14d re-anchored overlaps 07:50-08:14 and returns only the points inside it (`cw-01.json` / `cw-02.json` rows 07:50 to 08:10), rolled to hourly Maximum: 2 hourly points (07:00 bucket 13, 08:00 bucket 27; DLQ 0) of 336 | no baseline. 6 metric requests. |

Phase 2/3/4 reading:
- Old-against-new (per-pod form), before any label: new RS 5c8d7b9f4c: 3/3 pods crash-looping, mechanism in each pod's previous-container log; old RS 7f6b8c5d2e: 0 BackOff / Unhealthy events in the retained events (about 07:50-08:14:21; only Normal Killing at 08:14:21), queue flat at 7-27 until 08:10; onset not earlier than the rollout (backlog 16 at 08:10, first BackOff 08:15:02); no per-revision log counts (no log backend), which is recorded as a gap.
- Change leg: diff on the failing path (W2-Q4), apply record (Helm revision 12, W1-Q6), live ConfigMap shows the post-state of the commit (W2-Q3). Mechanism leg: W2-Q2 (+ W2-Q1 exit code 1). Timing leg: first Started 08:14:36, first BackOff 08:15:02-05, first bad queue sample 08:15 (W1-Q2, W1-Q8), 42-45 s after the upgrade.
- H2..H6 refuted (queries in the ledger); H1 supported. Stop-early rule met: one hypothesis Confirmed, all other plausible ones Ruled out. No wave 3 (2 of 3 Fast waves used). Query count 20 of 20, metric requests 14 of 100, 0 GB logs.
- Recurrence class: `unclassified` (2 of 336 hourly points, no alarm history); recorded as a gap.
- Untrusted text: none seen (the log lines are program output; none reads as an instruction).
- Ledger v3 written: query rows W2-Q1..Q5, Hypotheses (labels), Code repos, Recurrence, Windows (re-anchored), Gaps, Memory, Lesson candidates. Profile updated (log label, sidecar, compute, queues verified; Code row; baseline).

### Message 7 (after wave 2, verbatim)

```text
Wave 2 done (5 calls). Found it.
- Each of the 3 crashing pods logs, in its previous container, a fatal error 19 ms after start: "config: required environment variable NOTIFY_SMTP_RELAY_HOST is not set" (config/load.go:58, notify-worker 3.8.1). Exit code 1, not OOMKilled.
- The live ConfigMap notify-worker-config has the key SMTP_RELAY_HOST and no NOTIFY_SMTP_RELAY_HOST. Commit 3f9a1c2 (#214) renamed exactly that key in charts/notify-worker/values-prod.yaml, and Helm revision 12 applied it at 08:14:20 UTC. Same image tag 3.8.1 in both Helm revisions, so no app change.
- Old against new: new ReplicaSet 5c8d7b9f4c has 3 of 3 pods crash-looping; the old ReplicaSet 7f6b8c5d2e shows 0 BackOff or Unhealthy events in the retained events (about 07:50 to 08:14:21) and the queue stayed at 7-27 messages until 08:10. The first BackOff (08:15:02) comes after the rollout, not before.
- Ruled out: image pull and scheduling, OOM, probes, a dependency failing at startup (the process dies before any network call), a CronJob or node event.
- Recurrence: unclassified. The earlier CloudWatch windows (previous, minus 7 days, 14 days) returned no data, so there is no baseline. That is recorded as a gap.
I stop here: one cause is Confirmed and the others are Ruled out.
```

## Phase 5: conclude

Report saved separately. Fast-mode headings used: TL;DR, Impact, Causal chain, Gaps, To confirm, Follow-ups, Cost. The ruled-out list and the timeline sit inside the Causal chain section.

### Message 8 (TL;DR printed inline, verbatim)

```text
TL;DR
Cause: the prod values change in commit 3f9a1c2 (#214) renamed the config key NOTIFY_SMTP_RELAY_HOST to SMTP_RELAY_HOST; Helm revision 12 applied it at 08:14:20 UTC, and notify-worker 3.8.1 exits at startup because it still requires NOTIFY_SMTP_RELAY_HOST. · Confirmed
Weakest link: the old-revision side of the old-against-new split (no per-revision logs; it rests on the absence of events and a flat queue). The mechanism itself needs no old-side evidence: the crash log names the missing variable and the live ConfigMap lacks it. Separately, "emails are not being delivered" is Likely (inferred from the unconsumed queue; no sent-mail signal).
Impact: all 3 workers down since 08:14:21 UTC, ongoing; outbound queue 9,660 messages at 08:45 and growing about 318 per minute; DLQ 0. SEV1 suggested (a core flow has no worker); the incident owner decides.
Recommended action: a human restores the variable name the running app expects (revert the rename in the prod values, or roll the release back to revision 11), after checking it with pre-flight; then decide what to do with the stale backlog.
Report: .culiops/sre-investigate/runs/notify-worker-prod-20261022-0850/report.md
Open items need your input (gaps are listed in the report).
Cost: 20 queries · 0 GB of logs · 14 CloudWatch metric requests · no other metered units · about $0 in metered charges
```

## Phase 6: record

### Message 9 (proposed diff, verbatim; nothing written because the operator never replied)

```text
Proposed record (nothing is written until you reply; you can accept, edit or skip each item):

1. incidents/2026-10-22-notify-worker.md (new)
   front matter:
     id: 2026-10-22-notify-worker-prod-values-key-rename
     date: 2026-10-22
     service: notify-worker
     env: prod
     siblings: [all]
     window_utc: 2026-10-22T08:14:21Z/ongoing
     symptoms: [crash-restart, queue-backlog, unavailable]
     cause_category: config
     cause: prod Helm values renamed config key NOTIFY_SMTP_RELAY_HOST to SMTP_RELAY_HOST; notify-worker 3.8.1 requires the old name and exits at startup
     deps: [sqs notify-outbound, smtp relay]
     label: Confirmed
     mode: fast
     time_to_cause_min: null
     run: runs/notify-worker-prod-20261022-0850
   body: what happened, causal chain with labels, what found it (previous-container log + live ConfigMap keys), what did not help (CronJob and event checks), follow-ups.

2. lessons.md (new file), one line each, built from the ledger's Lesson candidates:
   - type: process | service: any | source: aws | statement: iam simulate-principal-policy reply can omit requested actions and add others; compare returned action names with the requested list before saying all 10 were evaluated | run: notify-worker-prod-20261022-0850 | query_id: W0-Q2 | re-verify: no
   - type: process | service: any | source: kubectl | statement: kubectl logs --previous holds only the latest crash of a container; date a crash loop's onset from the event firstTimestamp, not from the readable log | run: notify-worker-prod-20261022-0850 | query_id: W2-Q2 | re-verify: no
   - type: process | service: any | source: kubectl | statement: kubectl auth can-i --list showed *.* get/list/watch for the ReadOnly role, which includes Secrets; the view ClusterRole would not | run: notify-worker-prod-20261022-0850 | query_id: W0-Q4 | re-verify: no
   - type: process | service: notify-worker | source: cloudwatch | statement: get-metric-data on the notify SQS queues returned datapoints only for 07:50-08:45 on the incident day; empty earlier ranges are a coverage gap, not zero traffic | run: notify-worker-prod-20261022-0850 | query_id: W1-Q8 | re-verify: yes
   - type: identifier | service: notify-worker | source: kubectl | statement: namespace notify, Deployment, container and Helm release are all named notify-worker; selector app.kubernetes.io/name=notify-worker plus app.kubernetes.io/instance=notify-worker | run: notify-worker-prod-20261022-0850 | query_id: W1-Q5 | re-verify: no
   - type: identifier | service: notify-worker | source: cloudwatch | statement: SQS queues notify-outbound and notify-outbound-dlq in us-east-1 (profile prod-read), QueueName dimension | run: notify-worker-prod-20261022-0850 | query_id: W1-Q8 | re-verify: no
   - type: failure-mode | service: notify-worker | source: git | statement: notify-worker 3.8.1 exits at startup with "required environment variable <NAME> is not set" (config/load.go:58) when a chart values key is renamed; compare key names in values-prod.yaml with the live ConfigMap keys | run: notify-worker-prod-20261022-0850 | query_id: W2-Q2 | re-verify: no
   No confirm/re-verify/contradict/drop updates: lessons.md did not exist.

3. profiles/notify-worker-prod.md (new): the run's profile.md as it stands (identity, sibling set, identifiers with verified marks: log access via kubectl logs, compute, queues verified; Code row with the Helm-records-no-commit note; dependencies; baseline note).

Candidates for the skill itself (noted, not part of this diff): the write-check should compare the simulation's returned action names with the requested list; the Kubernetes write-check could flag `*.*` read access as Secret-readable.
```

No operator reply arrived, so by Phase 6 step 2 nothing was written: no `incidents/`, no `lessons.md`, no `profiles/` file.

## Files written (all under the case `out/` directory)

- `out/runs/notify-worker-prod-20261022-0850/ledger.md` (written after wave 0, updated after wave 1, updated after wave 2)
- `out/runs/notify-worker-prod-20261022-0850/profile.md` (written after the helper returned, updated after wave 2)
- `out/runs/notify-worker-prod-20261022-0850/raw/k-pods.txt`
- `out/runs/notify-worker-prod-20261022-0850/raw/k-events.tsv`
- `out/runs/notify-worker-prod-20261022-0850/raw/m-sqs-incident.tsv`
- `out/runs/notify-worker-prod-20261022-0850/raw/k-previous-logs.txt`
- `out/runs/notify-worker-prod-20261022-0850/raw/c-configmap-keys.txt` (key names only)
- `out/runs/notify-worker-prod-20261022-0850/raw/c-iac-diff-names.txt` (key names only)
- `out/run-log.md` (this file)
- `report.md`: report saved separately.
- Not written, by rule: `environment.md` (already existed), `incidents/`, `lessons.md`, `profiles/` (Phase 6: no reply).
- Outside the case directory: two throwaway Python helper scripts in the scratchpad were used only to apply text edits to the ledger and profile above.

## Deviations and notes worth a reviewer's attention

1. The clock: `date -u` is not in the INDEX, so Start times are indicative (08:50:00 UTC for every wave); the world is frozen at 08:50.
2. The simulation reply did not match the skill's fixed list of 10 actions (3 missing, 3 unrequested). I stated "read-only confirmed" only with that limit and recorded a gap, instead of claiming all 10 were evaluated.
3. `can-i --list` shows `*.*` get/list/watch, so the identity can read Secrets. No Secret was read; `describe pod` shows the secret reference by name only.
4. `helm get values`, `helm get manifest` and Secret reads were never run. Config values (relay host, queue URL, from address) appear nowhere in my files: only key names.
5. W1-Q7 (`get cronjobs -A`) had no INDEX row, so it returned empty output; I treated it as "no CronJob listed, unverified". The schedule hypothesis is ruled out mainly by the Helm timing and the logged mechanism.
6. The world returned the same `--previous` log content (same timestamp) for each of the three pods; I recorded it as such.
7. The budget counts every tool invocation as one query: 20 of 20, so a third wave would have needed a question to the operator.
