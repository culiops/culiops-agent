# Investigation log: sre-investigate, case-a (notify-worker prod)

Run id: `notify-worker-prod-20261022-0850` · Mode: Fast · Output root (simulated): `out/` (stands for `.culiops/sre-investigate/`) · CTX below stands for the full context name `arn:aws:eks:us-east-1:111122223333:cluster/prod` (always typed in full in the printed commands).

## Setup notes

- Read `skills/sre-investigate/SKILL.md`, `access/standalone.md`, `environment.template.md`, `templates/{ledger,report,profile,lesson,incident}.md`, `playbooks/{changes,infra-state,metrics,logs}.md`, `agents/helper.md`. Playbooks for errors, traces, waf, external, other-backends were not needed (no such backend in environment.md, no WAF symptom, no ticket).
- Before starting I ran one directory listing of the case folder (`ls -R`) to see file names. That is a shell command beyond file reading; it opened no world file. No world file was opened unless a command of the run mapped to it.
- Clock: `date -u +%H:%M:%S` has no INDEX row, so it prints nothing in the simulation. All Start times use 08:50:00 UTC, the reference time in `world/INDEX.md` (event ages are relative to it). The calendar date 2026-10-22 comes from the SQS window in the INDEX notes and the Helm release time.
- Not run on purpose: `helm get values` (the playbook forbids it: it prints rendered values), any Secret read, `kubectl exec`, `port-forward`, `agentbox-env`. World files `helm-02.yaml`, `k8s-06.json`, `k8s-15.yaml`, `k8s-16.yaml`, `git-03.txt` were never opened.

## Operator lines

| # | Line | When received |
|---|---|---|
| 1 | `notify-worker pods in prod are crash-looping and emails aren't going out. Fast mode.` | at the start (opening request) |

The script has only line 1, so no later cue exists. No reply to the Phase 6 diff ever arrived, so nothing was recorded (no `incidents/`, `lessons.md` or `profiles/` write).

## Phase 0: output root, environment, mode

Commands (root resolution, run before the first message), each mapped by INDEX rules:

| Command | World file | Key facts |
|---|---|---|
| `printf '%s\n' "${CULIOPS_HOME:-}"` | `_empty.txt` (no row) | empty: `CULIOPS_HOME` unset, root is `.culiops/sre-investigate/` |
| `git check-ignore -q .culiops/sre-investigate` | `_empty.txt` (no row) | exit 0, no output: ignored |
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | UTC; account 111122223333, profile `prod-read`, us-east-1; context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, ns `notify`; backends kubectl/Helm and CloudWatch SQS; Helm values repo `example-org/notify-deploy` at `~/src/notify-deploy`; app code `example-org/notify-worker` via `gh`; Logs Insights ask above 10 GB; default severity scale; core flow = transactional email |
| `ls .culiops/sre-investigate` | `ls-01.txt` | only `environment.md` (no profiles/, lessons.md, incidents/) |

### Message 1 (verbatim)

```text
Mode: Fast. You describe pods crash-looping right now, so this is live triage: access checks, then at most three read-only query waves, no checkpoints.

Output root: .culiops/sre-investigate/ at the repo root (CULIOPS_HOME is unset). It is local and is never committed; git check-ignore confirms .culiops/sre-investigate is ignored here. Every file of this run goes under .culiops/sre-investigate/runs/notify-worker-prod-20261022-0850/.

I found .culiops/sre-investigate/environment.md (timezone UTC, profile prod-read, the prod cluster context, namespace notify). It sets no per-mode query budgets, so I use the template's Fast defaults (20 queries, 2 GB of logs, 100 CloudWatch metric requests) and count only metered calls against them.
```

### Message 2 (verbatim): wave 0 commands, printed before running

```text
Wave 0: access and intake, read-only. Part A runs first; Part B needs the role name from Part A.

Part A
date -u +%H:%M:%S
command -v agentbox-env
aws sts get-caller-identity --profile prod-read
kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod
kubectl config current-context
kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace notify
cat .culiops/sre-investigate/lessons.md
cat .culiops/sre-investigate/profiles/notify-worker-prod.md

Part B
aws iam get-role --profile prod-read --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b --query Role.Arn --output text
aws iam simulate-principal-policy --profile prod-read --policy-source-arn arn:aws:iam::111122223333:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode cloudformation:DeleteStack --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text

No token-based backend is listed in environment.md, so there is no token check. No log backend is listed either, so there is no log probe.
```

### Wave 0 commands and results (query log W0-Q1 to W0-Q13 in the ledger)

| Query | Command | World file | Key facts |
|---|---|---|---|
| W0-Q1 | `date -u +%H:%M:%S` | `_empty.txt` | no output; clock taken from INDEX note (08:50:00) |
| W0-Q7 | `command -v agentbox-env` | `_empty.txt` | exit 1: standalone, nothing printed about Culibox |
| W0-Q8 | `aws sts get-caller-identity --profile prod-read` | `sts-01.json` | Account 111122223333 (matches environment.md); assumed role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` (session name not recorded) |
| W0-Q9 | `kubectl auth whoami --context CTX` | `k8s-02.txt` | same assumed role, group `eks-readonly` |
| W0-Q10 | `kubectl config current-context` | `k8s-01.txt` | the prod context: it is current |
| W0-Q11 | `kubectl auth can-i --list --context CTX --namespace notify` | `k8s-03.txt` | `*.*` [get list watch]; `create` only on selfsubjectreviews, selfsubjectaccessreviews, selfsubjectrulesreviews (excluded); no write verb |
| W0-Q5 | `cat .culiops/sre-investigate/lessons.md` | none (rule: unnamed path) | No such file or directory, exit 1 |
| W0-Q6 | `cat .culiops/sre-investigate/profiles/notify-worker-prod.md` | none (rule: unnamed path) | No such file or directory, exit 1: build a profile |
| W0-Q12 | `aws iam get-role ... --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` | `iam-01.json` | path `/aws-reserved/sso.amazonaws.com/`, role ARN resolved |
| W0-Q13 | `aws iam simulate-principal-policy ...` (10 fixed actions) | `iam-02.json` | 10 rows, all `implicitDeny`; but rows are s3:PutObject, s3:DeleteObject, ec2:TerminateInstances, ec2:ModifyInstanceAttribute, ecs:UpdateService, ecs:StopTask, iam:PutRolePolicy, iam:AttachRolePolicy, rds:ModifyDBInstance, lambda:UpdateFunctionCode. Missing versus the request: ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack. Treated as a gap for those three, no boxed warning (nothing allowed), and not worded as a full "read-only confirmed". |

Window and intake: no onset given, so Fast default (rule 6.5): last two hours, 06:50-08:50 UTC; baselines 04:50-06:50 and 2026-10-15 06:50-08:50. Zone UTC from environment.md. The run directory and ledger were created; the ledger was written after wave 0.

### Message 3 (verbatim): after wave 0

```text
Write check, prod-read (account 111122223333, role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b): none of the evaluated actions is allowed; 7 of the 10 write actions came back implicitDeny. The other 3 I asked about (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) returned no result, and the reply listed 3 actions I did not ask about, so those 3 are a gap. This is not a full proof; resource-scoped writes are not covered.
Write check, Kubernetes context for cluster prod, namespace notify: no write verbs. The only create rows are the three self-review APIs, which change nothing. Note: the role can get, list and watch every resource, which is broader than the built-in view role (it includes Secrets); I will not read Secrets.

Gaps so far: no log backend in environment.md, so app logs come only from kubectl logs --previous (G2); the AWS write check is incomplete for 3 actions (G1).

Window: you gave no onset, so I use the Fast default, the last two hours: 06:50 to 08:50 UTC (08:50 local; your zone is UTC per environment.md). Baselines: 04:50-06:50 UTC and 2026-10-15 06:50-08:50 UTC. No stored profile or lessons exist for this service, so I build the profile now.
```

## Build profile (helper TASK: PROFILE, cheapest tier, simulated inline)

### Message 4 (verbatim): discovery commands

```text
Profile build (helper, cheapest tier). Discovery commands, all read-only:

kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get deployments
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get pods
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get services,ingresses,hpa
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get configmap
helm list --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify
aws sqs list-queues --profile prod-read --region us-east-1 --queue-name-prefix notify

Not queried because environment.md lists no such backend: log labels, trace or APM names, Prometheus jobs, dashboards, error tracker.
```

| Query | Command | World file | Key facts |
|---|---|---|---|
| W0-Q14 | `kubectl ... -n notify get deployments` | `k8s-12.txt` | `notify-worker` READY 0/3, up-to-date 3, available 0, age 211d |
| W0-Q15 | `kubectl ... -n notify get pods` | `k8s-04.txt` | 3 pods `notify-worker-5c8d7b9f4c-{8wq2d, jt6kz, x4p9n}` CrashLoopBackOff, 11 restarts each, age 35m |
| W0-Q16 | `kubectl ... -n notify get services,ingresses,hpa` | `_empty.txt` | no output: none |
| W0-Q17 | `kubectl ... -n notify get configmap` | `k8s-13.txt` | `kube-root-ca.crt`, `notify-worker-config` (4 keys) |
| W0-Q18 | `helm list --kube-context CTX -n notify` | `helm-03.txt` | release `notify-worker` revision 12, updated 2026-10-22 08:14:20 UTC, deployed, chart notify-worker-1.8.0, app 3.8.1 |
| W0-Q19 | `aws sqs list-queues ... --queue-name-prefix notify` | `sqs-01.json` | `notify-outbound`, `notify-outbound-dlq` |

### Message 5 (verbatim): profile shown, run continues

```text
Profile built (partly unverified), saved to the run directory as profile.md. Corrections welcome; I continue without waiting.
- Service notify-worker, prod: Deployment notify-worker in namespace notify (3 replicas, one ReplicaSet at a time, no regions or shards), Helm release notify-worker (chart 1.8.0, app 3.8.1, revision 12).
- Config: ConfigMap notify-worker-config (4 keys); the SMTP password comes from a Secret (by name only).
- Queues: SQS notify-outbound and notify-outbound-dlq in us-east-1 (verified). No Service, Ingress or HPA in the namespace (verified).
- Helm values repo: example-org/notify-deploy, clone at ~/src/notify-deploy (to be verified in wave 2); app code: example-org/notify-worker (unverified, read through gh later if needed).
- Core flow: transactional email (critical). No SLO, dashboards, log backend or error tracker are known.
```

## Phase 1: wave 1 (change, signal and recurrence legs, all run)

### Message 6 (verbatim): wave 1 commands, printed before running

```text
Wave 1 (13 calls: the fixed legs for change events, the three signal windows and the recurrence pulls need more than ten; the deployments, pods, ConfigMaps, Helm release and queue names are reused from wave 0).

date -u +%H:%M:%S
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify rollout history deployment/notify-worker
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get rs --sort-by=.metadata.creationTimestamp
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get events --sort-by=.lastTimestamp
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify describe pod notify-worker-5c8d7b9f4c-8wq2d
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify logs notify-worker-5c8d7b9f4c-8wq2d --previous --timestamps --tail=50
helm history notify-worker --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify --max 10
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify describe deployment notify-worker

aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries '[{"Id":"backlog","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"notify-outbound"}]},"Period":300,"Stat":"Maximum"}}]' --start-time 2026-10-22T06:50:00Z --end-time 2026-10-22T08:50:00Z
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries '[{"Id":"backlog","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"notify-outbound"}]},"Period":300,"Stat":"Maximum"}}]' --start-time 2026-10-22T04:50:00Z --end-time 2026-10-22T06:50:00Z
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries '[{"Id":"backlog","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"notify-outbound"}]},"Period":300,"Stat":"Maximum"}}]' --start-time 2026-10-15T06:50:00Z --end-time 2026-10-15T08:50:00Z
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries '[{"Id":"backlog","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"notify-outbound"}]},"Period":3600,"Stat":"Maximum"}}]' --start-time 2026-10-08T06:50:00Z --end-time 2026-10-22T06:50:00Z
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries '[{"Id":"m1","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"notify-outbound-dlq"}]},"Period":300,"Stat":"Maximum"}}]' --start-time 2026-10-22T06:50:00Z --end-time 2026-10-22T08:50:00Z
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries '[{"Id":"m1","MetricStat":{"Metric":{"Namespace":"AWS/SQS","MetricName":"ApproximateNumberOfMessagesVisible","Dimensions":[{"Name":"QueueName","Value":"notify-outbound-dlq"}]},"Period":3600,"Stat":"Maximum"}}]' --start-time 2026-10-08T06:50:00Z --end-time 2026-10-22T06:50:00Z

CloudWatch cost: 6 metric requests (of 100). The previous-container log read is bounded (one pod, 50 lines) and sits in this wave because it is lost at the next restart. The Period is 300 because SQS publishes 5-minute data.
```

| Query | Command | World file | Key facts |
|---|---|---|---|
| W1-Q1 | `rollout history deployment/notify-worker` | `k8s-10.txt` | revisions 6 and 7, change-cause none |
| W1-Q2 | `get rs --sort-by=.metadata.creationTimestamp` | `k8s-11.txt` | `5c8d7b9f4c` desired 3, ready 0, 35m; `7f6b8c5d2e` 0/0, 15d |
| W1-Q3 | `get events --sort-by=.lastTimestamp` | `k8s-05.txt` | at 35m: old RS scaled 3 to 0 (3 Killing), new RS to 3, 3 pods scheduled on 3 nodes; then BackOff on all three; image already present; no probe, pull or scheduling warnings |
| W1-Q4 | `describe pod ...-8wq2d` | `k8s-07.txt` | start 08:14:33; Last State Terminated, reason Error, exit code 1, 08:47:56; 11 restarts; limits 500m / 256Mi; env from ConfigMap `notify-worker-config`; `SMTP_PASSWORD` from Secret `notify-smtp` key `password` (names only); annotation `checksum/config` |
| W1-Q5 | `logs ...-8wq2d --previous --timestamps --tail=50` | `k8s-08.txt` | 3 lines; fatal `config: required environment variable NOTIFY_SMTP_RELAY_HOST is not set` (config/load.go:58), 08:47:56.121 (19 ms after start). Saved to `raw/w1-q5-logs-previous-8wq2d.txt`. No instruction-like text. |
| W1-Q6 | `helm history notify-worker ...` | `helm-01.txt` | rev 11 2026-10-07 10:02:18 superseded; rev 12 2026-10-22 08:14:20 deployed; both chart 1.8.0, app 3.8.1 |
| W1-Q7 | `describe deployment notify-worker` | `k8s-14.txt` | strategy Recreate; 3 desired, 0 available; no probes listed; image tag 3.8.1; env from ConfigMap; revision 7 |
| W1-Q8 | CloudWatch notify-outbound, incident 06:50-08:50 | `cw-01.json` | 12 points 07:50-08:45: 11, 13, 7, 27, 16, 120, 1710, 3300, 4890, 6480, 8070, 9660; none before 07:50 |
| W1-Q9 | CloudWatch notify-outbound, previous 04:50-06:50 | `_default.txt` | `{}` (no data) |
| W1-Q10 | CloudWatch notify-outbound, -7d | `_default.txt` | `{}` |
| W1-Q11 | CloudWatch notify-outbound, 14d at 3600 | `_default.txt` | `{}` |
| W1-Q12 | CloudWatch notify-outbound-dlq, incident | `cw-02.json` | 12 points 07:50-08:45, all 0 |
| W1-Q13 | CloudWatch notify-outbound-dlq, 14d at 3600 | `_default.txt` | `{}` |

Reading: all three pods fail together (shared cause, no per-instance capacity checks). Shape: consumption stops about 08:14 (step); backlog rises exactly 1,590 per 5 minutes after 08:15. Recurrence: unclassified (no data, no alarm). Business counter for the core flow: none defined, so none run (gap G4). Availability cross-check: not applicable (no HTTP 5xx path).

### Message 7 (verbatim): impact block, before Phase 2

```text
Impact as of 08:50 UTC (08:50 local, UTC per environment.md)
Symptom:   all 3 notify-worker pods are in CrashLoopBackOff (0/3 ready, 11 restarts each); the notify-outbound queue is no longer drained, so transactional email is not being sent
Affected:  prod, namespace notify, 3 of 3 replicas (single deployment, no siblings); core flow transactional email (order confirmations, password resets), customer-facing; the dead-letter queue stays at 0, so messages are waiting, not failing
Since:     08:14 UTC (Helm release 12 at 08:14:20, first new pod 08:14:33, queue depth leaves its 7-27 level at 08:15) · ongoing: yes
Severity:  SEV1 (suggested) because a customer-facing core flow is down: no worker is consuming
Basis:     workload state and queue depth, W1-Q4, W1-Q7, W1-Q8, W1-Q12 · Confirmed that consumers are 0/3 and the backlog grows by about 318 messages per minute (16 at 08:10, 9,660 at 08:45); Likely that emails are not delivered (no delivery counter); the number of customers affected is Assumed (no SLO or request metrics; the previous-window and -7d baselines returned no data)
Third party in path: the SMTP relay (host is set through config); nothing implicates it so far; no contact route in the profile, and this run cannot contact vendors
```

Recurrence class: unclassified (Assumed), because the 14-day and baseline pulls returned nothing and no alarm history exists. Time of day of the one change: 08:14 UTC, not on a schedule I can see.

## Phase 2 / 3: change collection and hypotheses

Change list near the onset (all on the ledger timeline): Helm release 12 at 08:14:20 (W1-Q6); rollout of ReplicaSet `5c8d7b9f4c` from about 08:14 (W1-Q2, W1-Q3); pod template annotation `checksum/config` present (config changes roll the pods). Schedules: CronJobs listed in wave 2; no scaling groups in the evidence. CloudTrail: not queried; Helm and Kubernetes changes do not appear there (gap G5).

Ranked hypotheses (written after wave 1, with their falsification queries; full table in the ledger): H1 config key rename in release 12 (ConfigMap key names lack `NOTIFY_SMTP_RELAY_HOST`); H2 broken image or chart; H3 SMTP password Secret; H4 OOM or limits; H5 probe, pull or scheduling; H6 node churn; H7 SMTP relay or SQS outage; H8 scheduled job.

History lookup (after ranking): `grep -rEl 'notify-worker|crash-restart|queue-backlog' .culiops/sre-investigate/incidents/` mapped to `_empty.txt` (no output); the directory does not exist, so no `from-history:` leads. No wiki or runbook route is configured, so no docs lookup.

## Phase 2 continued: wave 2 (slow change sources and first falsification queries)

### Message 8 (verbatim)

```text
Ranked hypotheses (details in the ledger). H1: release 12 renamed a config key the app requires (the worker exits at start-up). Then, much less likely: H2 a broken image or chart, H3 the SMTP password Secret, H4 out-of-memory, H5 probe, image-pull or scheduling failure, H6 node churn, H7 an SMTP relay or SQS outage, H8 a scheduled job. Falsification comes first; H1 is refuted if the ConfigMap still has NOTIFY_SMTP_RELAY_HOST, if another pod dies with a different message, or if the crashes predate 08:14.

Wave 2 (5 calls: change history and the first falsification queries).

date -u +%H:%M:%S
git -C ~/src/notify-deploy log origin/main --since=2026-10-07T00:00:00Z --until=2026-10-22T09:00:00Z --date=iso-strict --format='%h %cI %an %s' -- charts/notify-worker
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify get configmap notify-worker-config -o json | jq '.data | keys'
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod get cronjobs -A
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify logs notify-worker-5c8d7b9f4c-jt6kz --previous --timestamps --tail=50
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n notify logs notify-worker-5c8d7b9f4c-x4p9n --previous --timestamps --tail=50

The git range starts at the previous release (2026-10-07) because release 11 is the last known-good state. The ConfigMap is read as key names only; values are not recorded.
```

| Query | Command | World file | Key facts |
|---|---|---|---|
| W2-Q1 | `git -C ~/src/notify-deploy log origin/main ... -- charts/notify-worker` | `git-01.txt` | `3f9a1c2` Thu 2026-10-22 08:03:41 +0000 "notify-worker: align config key names with the shared SMTP chart (#214)"; `9e8d7c6` Wed 2026-10-07 09:51:09 +0000 "notify-worker: raise concurrency to 8 (#201)"; author `platform-dev` |
| W2-Q2 | `kubectl ... get configmap notify-worker-config -o json \| jq '.data \| keys'` | `k8s-09.yaml` | keys NOTIFY_FROM_ADDRESS, NOTIFY_QUEUE_URL, NOTIFY_WORKER_CONCURRENCY, SMTP_RELAY_HOST; no NOTIFY_SMTP_RELAY_HOST. The file contains values; none was recorded. |
| W2-Q3 | `kubectl --context CTX get cronjobs -A` | `_empty.txt` | no output: no CronJobs |
| W2-Q4 | `logs ...-jt6kz --previous` | `k8s-08.txt` | same fatal message |
| W2-Q5 | `logs ...-x4p9n --previous` | `k8s-08.txt` | same fatal message |

Ledger updated after wave 2 (hypotheses, code repos, query log). Stop-early rule: H1 supported, H2-H8 each with a negative falsification (H2 awaits the commit diff), so one more small wave.

## Wave 3

### Message 9 (verbatim)

```text
Wave 3 (1 call): the diff of the commit that release 12 carries, to rule the image and chart in or out.

date -u +%H:%M:%S
git -C ~/src/notify-deploy show 3f9a1c2
```

| Query | Command | World file | Key facts |
|---|---|---|---|
| W3-Q1 | `git -C ~/src/notify-deploy show 3f9a1c2` | `git-02.txt` | one file, `charts/notify-worker/values-prod.yaml`: key `NOTIFY_SMTP_RELAY_HOST` removed, `SMTP_RELAY_HOST` added with the same value; no image, chart or other key changed |

Fast mode ends after the third wave. H1 Confirmed (change: W3-Q1; mechanism: W1-Q5, W2-Q4, W2-Q5, W2-Q2; timing: W1-Q6, W1-Q4, W1-Q8). H2 to H8 ruled out. The ledger and `profile.md` were finalised; the Lesson candidates table was filled.

## Phase 5: conclude

### Message 10 (verbatim): TL;DR printed in chat first

```text
TL;DR
Cause: Helm release 12 (08:14:20 UTC) carried a values change that renamed the ConfigMap key NOTIFY_SMTP_RELAY_HOST to SMTP_RELAY_HOST. notify-worker 3.8.1 still requires NOTIFY_SMTP_RELAY_HOST, exits at start-up on all 3 pods, and CrashLoopBackOff follows. Label: Confirmed (change W3-Q1, mechanism W1-Q5/W2-Q2/W2-Q4/W2-Q5, timing W1-Q6/W1-Q4/W1-Q8).
Weakest link: no chain link is below Confirmed. The least direct is the tie between merged commit 3f9a1c2 and release 12 (live ConfigMap keys plus release time, no pipeline record read). Separately, "emails are not delivered" is Likely: there is no delivery counter.
Impact: 0 of 3 workers since about 08:14 UTC, still ongoing; notify-outbound backlog 16 (08:10) to 9,660 (08:45), about 318 messages per minute, dead-letter queue at 0. Suggested SEV1 (transactional email down); you decide.
Recommended action: a human restores a working config: either put back the key name the app reads, or roll back to Helm release 11 (release 12 changed nothing else). Rollback is quicker but leaves the intended rename undone; a new release is slower but keeps history moving forward. Assess with pre-flight first. I changed nothing.
Pattern: unclassified (the 14-day and baseline queries returned no data).

Full report: .culiops/sre-investigate/runs/notify-worker-prod-20261022-0850/report.md
Open items need your input.

Cost: 38 read-only calls (6 metered) · 0 GB of logs scanned · 6 CloudWatch metric requests · under $0.01 in metered charges
```

## Phase 6: record

### Message 11 (verbatim): proposed diff, then wait

```text
Proposed additions (nothing is written until you reply; you can accept, edit or skip each item):

1. incidents/2026-10-22-notify-worker.md (new)
   ---
   id: 2026-10-22-notify-worker-prod-config-key-rename
   date: 2026-10-22
   service: notify-worker
   env: prod
   siblings: [all]
   window_utc: 2026-10-22T08:14:20Z/ongoing
   symptoms: [crash-restart, queue-backlog]
   cause_category: config
   cause: Helm release 12 renamed the ConfigMap key NOTIFY_SMTP_RELAY_HOST that the app requires, so all pods exit at start-up
   deps: [sqs-notify-outbound, smtp-relay]
   label: Confirmed
   mode: fast
   time_to_cause_min: null
   run: runs/notify-worker-prod-20261022-0850
   ---
   Body: what happened, causal chain with labels, what found it (kubectl logs --previous plus the ConfigMap key names), what did not help (the 14-day SQS pull returned no data), follow-ups.

2. lessons.md (new file, 3 lines, each backed by a query of this run)
   - type: failure-mode | service: notify-worker | source: kubectl | statement: CrashLoopBackOff right after a values-only Helm release (chart and image unchanged): kubectl logs --previous names the missing environment variable; compare it with the ConfigMap key names and the values diff | run: notify-worker-prod-20261022-0850 | query_id: W1-Q5 | re-verify: no
   - type: identifier | service: notify-worker | source: kubectl | statement: Deployment notify-worker in namespace notify, Helm release notify-worker, queues notify-outbound and notify-outbound-dlq; no log backend, logs only through kubectl logs --previous | run: notify-worker-prod-20261022-0850 | query_id: W0-Q14 | re-verify: no
   - type: process | service: notify-worker | source: cloudwatch | statement: SQS get-metric-data for notify-outbound returned points only for 07:50-08:45 and nothing for the previous, -7d and 14d windows; treat as a coverage gap and check retention before trusting any baseline | run: notify-worker-prod-20261022-0850 | query_id: W1-Q11 | re-verify: yes

3. profiles/notify-worker-prod.md (new): the run's profile.md as the stored profile (identifiers verified: Deployment, Helm release, ConfigMap, queues, container name, IaC chart path; unverified: code repo default branch, data stores).

No candidate for the skill itself, except one observation: when the write-check simulation reply names different actions than the ones requested, record a gap per missing action (done here, G1).
```

Waited for a reply; none arrived (the operator script has no further line). Per the skill, no reply means no write: `incidents/`, `lessons.md` and `profiles/` were not created.

## Files written

All under the simulated output root (`out/`):

- `runs/notify-worker-prod-20261022-0850/ledger.md` (created after wave 0, updated after waves 1, 2 and 3 with targeted edits; the H1 and H2 final labels were entered in the wave-2 update, with W3-Q1 evidence added once wave 3 returned)
- `runs/notify-worker-prod-20261022-0850/profile.md` (written after the profile build; the IaC row mark and the `NOTIFY_SMTP_RELAY_HOST` dependency note were filled from waves 2 and 3 and are in the saved version)
- `runs/notify-worker-prod-20261022-0850/raw/w1-q5-logs-previous-8wq2d.txt`
- `runs/notify-worker-prod-20261022-0850/raw/w1-q8-q12-sqs-incident.tsv`
- `run-log.md` (this file)
- `runs/notify-worker-prod-20261022-0850/report.md` (report saved separately; the text is also in the Appendix below)

## Discrepancies and judgement calls worth a look

1. The simulation reply (`iam-02.json`) names different actions than the ten requested; handled as a per-action gap, wording adapted from the skill's "read-only confirmed" template.
2. The 14-day, previous and -7d CloudWatch windows fall outside the INDEX's covered window (07:50-08:45) and returned `{}`. Recorded as a coverage gap, not as zero, so recurrence is `unclassified` rather than guessed.
3. Impact basis: environment.md has no SLO or request metrics, so the strict source order gives "Assumed"; I used workload state and queue depth as direct (Confirmed) evidence for "consumers down" and kept the customer-level impact Assumed.
4. "Queries" budget: counted only metered calls (6 CloudWatch metric requests) because environment.md sets no per-mode totals; 38 read-only calls were made in all.
5. Wave 1 held 13 calls, noted as above ten because of its fixed legs.
6. The ConfigMap file returned by the world contains values (relay host, queue URL, from address); none of them was written into any file or message.

## Appendix: report.md content

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
