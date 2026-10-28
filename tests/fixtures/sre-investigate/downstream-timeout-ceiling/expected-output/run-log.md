# Investigation log: sre-investigate, case-g, catalog-api prod

Simulation notes (read first)

- Case directory = the team's repo and machine. Output root used: `.culiops/sre-investigate/` at the repo root, written under `out/` with the same relative layout. Run directory: `out/runs/catalog-api-prod-20261023-1020/`.
- Simulated clock: the world is frozen at now = 2026-10-23 10:20:00 UTC (Prometheus instant files are evaluated at 10:20, event ages are relative to 10:20). `date -u` outputs below are simulated and only move by seconds to minutes.
- No shell command was run. Every command was looked up in `world/INDEX.md` and only the mapped file was read (some with a local `python3 -I` / `head` / `cat` read of that same mapped file, to summarize 361-point series). While planning I ran one `wc -c` over the world directory, which showed file sizes only; no unmapped file was opened.
- `report.md`: report saved separately; its text is also in Appendix A of this log. `ledger.md` and `profile.md` were written normally.
- No `repo/` directory exists in the case, so no local clone; code would be read only through `gh` (one attempt, W2-Q7).

## Operator lines received

| # | When | Line |
|---|---|---|
| 1 | at the start | `catalog-api latency alert in prod has been firing for about 50 minutes. Can you also pull what errors it is logging? Fast mode.` |
| 2 | after I asked to approve the over-threshold Logs Insights query (end of Phase 1 message) | `OK, run it for the last 15 minutes.` |

No third line exists in the script; the Phase 6 diff got no reply, so nothing was recorded.

## Phase 0: access, mode and intake

### Resolving the output root and reading environment.md (before the first message)

| # | Command | Mapped to | Key facts |
|---|---|---|---|
| R1 | `git rev-parse --show-toplevel` | `_empty.txt` (unmatched git command: no output, exit 0) | printed nothing; the working directory is taken as the repo root |
| R2 | `echo "${CULIOPS_HOME:-}"` | `_empty.txt` | empty: CULIOPS_HOME unset |
| R3 | `git check-ignore -q .culiops/sre-investigate` | `_empty.txt` (exit 0) | exit 0: the directory is ignored by git |
| R4 | `ls .culiops/sre-investigate` | `ls-01.txt` | only `environment.md`: no profiles/, lessons.md, incidents/ yet |
| R5 | `cat .culiops/sre-investigate/environment.md` | `environment.md` | timezone America/Sao_Paulo (UTC-3); profile prod-read (111122223333, us-east-1); context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace catalog; Prometheus `$PROM_URL`, Tempo `$TEMPO_URL` (no tokens), CloudWatch Logs group `/eks/prod/<service>`; repos example-org/catalog-api and example-org/catalog-deploy via gh; Logs Insights ask threshold 0.5 GB; core flows product page and search; default severity scale |
| R6 | `command -v agentbox-env` | `_empty.txt` (exit 1) | not found: nothing about Culibox is printed |

### Message 1 (first message, verbatim)

```text
Resolving the output root and reading environment.md (read-only):
  git rev-parse --show-toplevel
  echo "${CULIOPS_HOME:-}"
  git check-ignore -q .culiops/sre-investigate
  ls .culiops/sre-investigate
  cat .culiops/sre-investigate/environment.md
  command -v agentbox-env

sre-investigate: catalog-api (prod)

Mode: Fast (live triage). You asked for Fast, and the alert is still firing.
Output root: .culiops/sre-investigate/ at the repo root (CULIOPS_HOME is not set). Everything I write goes there. It is local and is never committed; git reports it as ignored.
Window: you gave a relative time ("firing for about 50 minutes"), so I anchor on now = 10:20 UTC (07:20 America/Sao_Paulo, the zone in environment.md). Incident window 09:30-10:20 UTC (06:30-07:20 local), compared with 08:40-09:30 UTC (previous) and the same span on 2026-10-16 (7 days back).
Your second ask (what errors it logs) is a CloudWatch Logs Insights query. Your threshold in environment.md is 0.5 GB per query, so I estimate the scan first and ask you before running anything above it.
Run directory: runs/catalog-api-prod-20261023-1020/ (ledger.md created from the template). Starting wave 0 (access and intake).
```

Files written at this point: `out/runs/catalog-api-prod-20261023-1020/ledger.md` (created; filled in as the waves landed, final version at the end).

### Wave 0

Message 2 (verbatim):

```text
Wave 0 (access and intake). Every command in full, sent together.

Call 1, AWS identity and write-check, profile prod-read:
  date -u +%H:%M:%S
  aws sts get-caller-identity --profile prod-read --output json
  arn=$(aws sts get-caller-identity --profile prod-read --query Arn --output text)
  role=${arn#*:assumed-role/}; role=${role%%/*}
  role_arn=$(aws iam get-role --profile prod-read --role-name "$role" --query Role.Arn --output text)
  aws iam simulate-principal-policy --profile prod-read --policy-source-arn "$role_arn" --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode cloudformation:DeleteStack --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text

Call 2, Kubernetes identity and write-check, context arn:aws:eks:us-east-1:111122223333:cluster/prod:
  kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod
  kubectl config current-context
  kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace catalog

Call 3, the alert that started this:
  curl -sG "$PROM_URL/api/v1/alerts"

Call 4, log probe (size estimate only, window = last 15 minutes, 10:05-10:20 UTC):
  aws logs describe-log-groups --profile prod-read --region us-east-1 --log-group-name-prefix "/eks/prod/catalog" --output json | jq -r --argjson win 900 --argjson now "$(date +%s)" '.logGroups[] | (.retentionInDays // null) as $r | (($now - .creationTime / 1000) | floor) as $age | (if $r then ([$r * 86400, $age] | min) else $age end) as $span | [.logGroupName, (.logGroupClass // "-"), ($r // "none"), ((.storedBytes / 1e9 * 100 | round) / 100), ((.storedBytes * $win / $span / 1e9 * 1000 | round) / 1000)] | @tsv'

No profile or lessons exist for catalog-api prod, so a profile helper (cheapest tier) runs in parallel with these:
  curl -sG "$TEMPO_URL/api/v2/search/tags" --data-urlencode "start=1792747800" --data-urlencode "end=1792750800"
  curl -sG "$PROM_URL/api/v1/label/__name__/values" --data-urlencode "start=1792747800" --data-urlencode "end=1792750800"
  kubectl get pods -n catalog --context arn:aws:eks:us-east-1:111122223333:cluster/prod
  kubectl get hpa -n catalog --context arn:aws:eks:us-east-1:111122223333:cluster/prod
  kubectl get deployment,service,ingress -n catalog --context arn:aws:eks:us-east-1:111122223333:cluster/prod
```

Commands in order, with mapping (date -u output 10:20:07 for the wave):

| ID | Command | Mapped to | Key facts returned |
|---|---|---|---|
| W0-Q1 | `aws sts get-caller-identity --profile prod-read` (JSON, and the `--query Arn` form) | `sts-01.json` | Account 111122223333 (matches environment.md); assumed-role AWSReservedSSO_ReadOnly; session name not recorded |
| W0-Q2 | `aws iam get-role ... --role-name "$role"` | `iam-01.json` | role ARN with path `/aws-reserved/sso.amazonaws.com/` |
| W0-Q3 | `aws iam simulate-principal-policy ...` | `iam-02.json` | 10 rows, all implicitDeny. Three requested actions have no row (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack); three unrequested ones appear (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy) |
| W0-Q4 | `kubectl auth whoami --context <arn>` | `k8s-02.txt` | user = assumed role AWSReservedSSO_ReadOnly, group eks-readonly |
| W0-Q5 | `kubectl config current-context` | `k8s-01.txt` | the same context ARN |
| W0-Q6 | `kubectl auth can-i --list --context <arn> --namespace catalog` | `k8s-03.txt` | creates only on selfsubjectreviews, selfsubjectaccessreviews, selfsubjectrulesreviews (excluded); `*.*` get/list/watch; no write verbs |
| W0-Q7 | `GET $PROM_URL/api/v1/alerts` | `prom-12.json` | one alert `CatalogApiLatencyHigh`, severity page, service catalog-api, namespace catalog, firing, activeAt 09:32:00Z, value 4.952, runbook_url in annotations (not opened) |
| W0-Q8 | `aws logs describe-log-groups ... --log-group-name-prefix "/eks/prod/catalog"` | `logs-01.json` | `/eks/prod/catalog-api`, STANDARD, retention 14 days, 2,419,200,000,000 bytes stored: estimate 1.8 GB for 15 min (older than 14 days, so span = 14 days) |
| P1-Q1 | Tempo `GET /api/v2/search/tags` | `tempo-04.json` | tag names only; resource scope has `service.name`; span scope has `server.address`, `http.route`, `db.system` |
| P1-Q2 | Prometheus `GET /api/v1/label/__name__/values` | `prom-13.json` | 12 metric names including the http_server_request_duration_seconds family, http_server_requests_in_flight; no `ALERTS` |
| P1-Q3 | `kubectl get pods -n catalog` | `k8s-04.txt` | 6 pods Running, 0 restarts; 4 aged 9d, 2 aged 48m and 47m, same ReplicaSet hash 6b9d7c5f48 |
| P1-Q4 | `kubectl get hpa -n catalog` | `k8s-06.txt` | catalog-api: TARGETS 58/40, min 4, max 12, 6 replicas |
| P1-Q5 | `kubectl get deployment,service,ingress -n catalog` | `_empty.txt` | no output; not used |

Not run in wave 0, with reason: token-presence check (environment.md lists no token_env); alarm state history (the trigger is a Prometheus alert whose name is only known after W0-Q7, so the `ALERTS` pull is in wave 1 with the recurrence pull); error-tracker top issues (none listed); ticket (none named); WAF playbook (not a 403/429 report); stored profile and lessons (R4 shows none).

Message 3 (after wave 0, verbatim):

```text
Wave 0 results

Access
- prod-read: account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly.
- Write check, prod-read: read-only confirmed (simulation) for the 7 requested actions that came back: none is allowed. This is not a full proof; resource-scoped writes are not covered.
- Gap on that check: the simulator returned no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey and cloudformation:DeleteStack (it returned three other actions, all denied, instead). So 3 of the 10 fixed actions are unevaluated.
- Kubernetes context arn:aws:eks:us-east-1:111122223333:cluster/prod: identity is the same role, group eks-readonly. Write check: no write verbs in catalog. Note: the binding allows get/list/watch on everything (*.*), Secrets included, which is wider than the built-in view ClusterRole. I will not read Secret objects.
- environment.md lists no token variables (Prometheus and Tempo are network-restricted), so there was no token check to make.

Trigger
- Prometheus alert CatalogApiLatencyHigh (severity page, service catalog-api, namespace catalog): firing, activeAt 09:32:00Z, value 4.952 s against its "p95 above 2s for 10 minutes" rule. It is the only alert returned, so there are no sibling alerts. Its runbook link is context only; I have not opened it.

Logs
- /eks/prod/catalog-api holds 2.42 TB with 14-day retention: about 1.8 GB per 15 minutes. That is above your 0.5 GB threshold, so the error query will need your OK.

Gaps so far
- First run for this service: no stored profile or lessons. Building a profile now.
- environment.md lists no Grafana, Sentry, ticket system, wiki, SLO or business counters, and no local code clone. So no deploy annotations, error-tracker issues or SLO burn, and app code only through gh.
```

Message 4 (profile, verbatim):

```text
Profile built by the helper (cheapest tier) and saved as the run's profile.md. The stored profile under profiles/ is only written after your reply in the record step. Tell me if any of this is wrong; I continue without waiting.
  Cluster and namespace: prod / catalog; Deployment and HPA catalog-api (min 4, max 12, 6 replicas now), 6 pods, 0 restarts
  Logs: CloudWatch group /eks/prod/catalog-api (verified)
  Metrics: http_server_request_duration_seconds with label service="catalog-api" (metric names verified; label values not yet)
  Traces: Tempo service name catalog-api (unverified until a query returns data for it)
  Sibling set: the 6 replicas (no regions or shards)
  Not found: dashboards, error tracker, ingress or load balancer, data stores, queues, local code clone
```

Files written: `out/runs/catalog-api-prod-20261023-1020/profile.md` (created; final version at the end of the run).

## Phase 1: scope, impact, severity (wave 1)

Message 5 (wave 1 printed, verbatim):

```text
Wave 1 (change events, golden signals over three windows, recurrence, siblings, slow downstream). Every command in full, sent together. The Logs Insights query is not in this batch; it is over your threshold and I ask after these results.

Call 1, change events (Kubernetes and Helm), context arn:aws:eks:us-east-1:111122223333:cluster/prod:
  date -u +%H:%M:%S
  kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog rollout history deployment/catalog-api
  kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog get rs --sort-by=.metadata.creationTimestamp
  kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog get events --sort-by=.lastTimestamp
  helm history catalog-api --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog --max 10
  kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog top pods
  (pods, restarts and HPA were read in wave 0 and are reused: P1-Q3, P1-Q4)

Call 2, Prometheus. Range queries use start=2026-10-23T08:40:00Z end=2026-10-23T10:20:00Z step=60 (previous + incident windows in one range, split when read); "offset 7d" gives the same window one week back:
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=histogram_quantile(0.5, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[5m])))' --data-urlencode "start=2026-10-23T08:40:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=60"
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=histogram_quantile(0.9, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[5m])))' --data-urlencode "start=2026-10-23T08:40:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=60"
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[5m])))' --data-urlencode "start=2026-10-23T08:40:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=60"
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[5m])))' --data-urlencode "start=2026-10-23T08:40:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=60"
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=histogram_quantile(0.5, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[5m] offset 7d)))' --data-urlencode "start=2026-10-23T08:40:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=60"
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[5m] offset 7d)))' --data-urlencode "start=2026-10-23T08:40:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=60"
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[5m] offset 7d)))' --data-urlencode "start=2026-10-23T08:40:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=60"
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=sum(rate(http_server_request_duration_seconds_count{service="catalog-api"}[5m]))' --data-urlencode "start=2026-10-23T08:40:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=60"
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=sum(rate(http_server_request_duration_seconds_count{service="catalog-api", status=~"5.."}[5m])) / sum(rate(http_server_request_duration_seconds_count{service="catalog-api"}[5m]))' --data-urlencode "start=2026-10-23T08:40:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=60"
  curl -sG "$PROM_URL/api/v1/query" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, route) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[30m])))' --data-urlencode "time=2026-10-23T10:20:00Z"
  curl -sG "$PROM_URL/api/v1/query" --data-urlencode 'query=histogram_quantile(0.95, sum by (le, route) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[30m] offset 7d)))' --data-urlencode "time=2026-10-23T10:20:00Z"
  curl -sG "$PROM_URL/api/v1/query" --data-urlencode 'query=sum by (route) (rate(http_server_request_duration_seconds_count{service="catalog-api"}[30m]))' --data-urlencode "time=2026-10-23T10:20:00Z"
  Recurrence pull (14 days at 1 h; a latency quantile over 14 days exceeds the 12 h quantile cap and no recording rule is known, so the alert history and a saturation gauge are used):
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=max_over_time(ALERTS{alertname="CatalogApiLatencyHigh", alertstate="firing"}[1h])' --data-urlencode "start=2026-10-09T09:30:00Z" --data-urlencode "end=2026-10-23T10:20:00Z" --data-urlencode "step=3600"
  curl -sG "$PROM_URL/api/v1/query_range" --data-urlencode 'query=max_over_time(http_server_requests_in_flight{service="catalog-api"}[1h])' --data-urlencode "start=2026-10-09T09:30:00Z" --data-urlencode "end=2026-10-23T09:30:00Z" --data-urlencode "step=3600"

Call 3, Tempo (slow downstream: client spans of catalog-api by peer address):
  curl -sG "$TEMPO_URL/api/metrics/query_range" --data-urlencode 'q={ resource.service.name = "catalog-api" && span:kind = client } | quantile_over_time(span:duration, .95) by (span.server.address)' --data-urlencode "start=1792744800" --data-urlencode "end=1792750800" --data-urlencode "step=300"
  curl -sG "$TEMPO_URL/api/metrics/query_range" --data-urlencode 'q={ resource.service.name = "catalog-api" && span:kind = client } | quantile_over_time(span:duration, .95) by (span.server.address)' --data-urlencode "start=1792140000" --data-urlencode "end=1792146000" --data-urlencode "step=300"
  curl -sG "$TEMPO_URL/api/metrics/query_range" --data-urlencode 'q={ resource.service.name = "catalog-api" && span:kind = client } | rate() by (span.server.address)' --data-urlencode "start=1792744800" --data-urlencode "end=1792750800" --data-urlencode "step=300"
```

Commands in order, with mapping (date -u output 10:20:41):

| ID | Command | Mapped to | Key facts returned |
|---|---|---|---|
| W1-Q1 | `kubectl ... rollout history deployment/catalog-api` | `k8s-08.txt` | revision 17 (chart 2.6.0, image 1.31.1), 18 (chart 2.6.1, image 1.31.2) |
| W1-Q2 | `kubectl ... get rs --sort-by=...` | `k8s-09.txt` | catalog-api-58f4d6b7c9 desired 0, age 16d; catalog-api-6b9d7c5f48 6 ready, age 9d |
| W1-Q3 | `kubectl ... get events --sort-by=.lastTimestamp` | `k8s-05.txt` | only Normal events 48m and 47m old: HPA SuccessfulRescale to 6 ("pods metric http_requests_in_flight above target"), ScalingReplicaSet 4 to 6, two pods scheduled and started. No Warning events |
| W1-Q4 | `helm history catalog-api ...` | `helm-01.txt` | rev 21 2026-10-07 08:12:40 superseded (2.6.0); rev 22 2026-10-14 07:58:03 deployed (2.6.1, app 1.31.2); zone not printed |
| W1-Q5 | `kubectl ... top pods` | `k8s-07.txt` | 6 pods 187-224m CPU, 349-391Mi |
| W1-Q6 | p50 range | `prom-01.json` | median 0.110 s previous, 0.109 s incident: flat |
| W1-Q7 | p90 range | `prom-14.json` (anything else) | empty matrix: gap |
| W1-Q8 | p95 range | `prom-02.json` | 0.398 s at 09:30, 4.967 s at 09:31; median 4.934 s over 09:35-10:20 against 0.418 s previous |
| W1-Q9 | p99 range | `prom-03.json` | median 4.991 s incident against 0.892 s previous |
| W1-Q10 | p50 range, offset 7d | `prom-04.json` | median 0.109 s one week back |
| W1-Q11 | p95 range, offset 7d | `prom-05.json` | median 0.424 s one week back |
| W1-Q12 | p99 range, offset 7d | `prom-06.json` | median 0.891 s one week back |
| W1-Q13 | request rate range | `prom-07.json` | 412 req/s previous, 409 incident: flat |
| W1-Q14 | 5xx share range | `prom-08.json` | 0.21% previous, 0.23% incident: flat |
| W1-Q15 | p95 by route, instant | `prom-09.json` | /products/{id} 4.968 s; /search 0.381; reviews 0.214; /categories 0.083; /healthz 0.004 |
| W1-Q16 | p95 by route, instant, offset 7d | `prom-10.json` | /products/{id} 0.441 s; /search 0.372; reviews 0.207; /categories 0.079; /healthz 0.004 |
| W1-Q17 | call rate by route, instant | `prom-11.json` | /products/{id} 144.2, /search 121.7, /categories 83.9, reviews 58.3, /healthz 2.0 req/s |
| W1-Q18 | ALERTS 14 d | `prom-14.json` | empty matrix: gap |
| W1-Q19 | in-flight gauge 14 d | `prom-14.json` | empty matrix: gap |
| W1-Q20 | Tempo client-span p95 by address | `tempo-01.json` | api.pricing.example.com 0.21 s to 5.00 s (first 5.00 s sample 09:35); reviews-api 0.06, catalog-db 0.004, catalog-cache 0.001 flat |
| W1-Q21 | same, 7 days back | `tempo-02.json` | pricing 0.20 s; others the same as today's baseline |
| W1-Q22 | Tempo `rate()` by address | `tempo-06.json` | empty series: gap |

Not run in wave 1: -7d request rate and 5xx (the backend has no form that returns a week-old rate; the same-day previous window is the baseline, recorded as a gap); availability cross-check against a load balancer (errors are not the symptom, no LB or ingress metrics listed); business counters (none named in environment.md); per-pod latency (pod label not discovered).

Message 6 (wave 1 results, impact block, read of the data, and the Logs Insights ask; verbatim):

```text
Wave 1 results (data fixed at 10:20 UTC; all times UTC)

Impact as of 10:20 UTC (07:20 local, America/Sao_Paulo)
Symptom:   catalog-api p95 4.93 s and p99 4.99 s (previous window 0.42 s and 0.89 s; 7 days back 0.42 s and 0.89 s). p50 unchanged at 0.11 s. GET /products/{id} p95 4.97 s against 0.44 s 7 days back. Calls from catalog-api to api.pricing.example.com sit at 5.00 s p95 against 0.21 s.
Affected:  prod, all 6 pods alike. Only GET /products/{id} moved (144 of 410 req/s, about 35%; the product-page core flow). /search 0.38 s, /products/{id}/reviews 0.21 s, /categories 0.08 s unchanged. Request rate flat (about 410 req/s) and 5xx share flat (about 0.2%). Customer-facing.
Since:     09:31 UTC (06:31 local), the minute p95 stepped from 0.40 s to 4.97 s; the alert's activeAt is 09:32:00Z · ongoing: yes
Severity:  SEV2 (suggested) because a core flow (product page) is significantly degraded, about 11 to 12 times baseline p95, while still answering with 5xx not elevated. SEV1 needs the flow down or more than 5% of requests failing. The incident owner decides.
Basis:     request metrics against baseline (environment.md names no SLO) · W1-Q6, W1-Q8, W1-Q9, W1-Q10-Q17 · Confirmed
Third party in the path: api.pricing.example.com is the slow peer. Its owner is not recorded anywhere I can read; the domain matches your internal hosts, which hints at an internal team, unconfirmed. I cannot contact it, a human has to.

What the data says
- Shape: ceiling. p95 and p99 are flat at about 4.93 s and 4.99 s while p50 is unchanged, and it arrived as a step at 09:31. Volume is out: request rate is flat (409 against 412 req/s).
- Siblings and downstream: of the four peers catalog-api calls, only api.pricing.example.com moved (p95 0.21 s to 5.00 s, first 5.00 s sample at 09:35 in 5-minute buckets). reviews-api (0.06 s), the database (0.004 s) and the cache (0.001 s) are flat against 7 days back. All 6 pods look alike (0.19-0.22 CPU cores, no restarts).
- Recurrence: unclassified. Prometheus answered for 6 hours only and the 14-day pulls came back empty; in the 5 hours before onset p95 never went above 0.46 s. A gap, noted.
- Changes so far (Phase 2): the last Helm upgrade was 2026-10-14 07:58 (chart 2.6.1, image 1.31.2), nine days before; all pods run that same ReplicaSet. The only event is the HPA scaling 4 to 6 pods at about 09:32, after the onset and because in-flight requests rose, so it is a consequence. Schedules, CloudTrail and IaC history come in wave 2.
- Hypotheses, ranked, each with the query that would kill it:
  1. The pricing call waits out a 5 s timeout (killed if that peer's p95 were at baseline, or if slow traces spent their time elsewhere). Not killed so far.
  2. Capacity or autoscaler limit (killed by headroom: HPA at 6 of 12, idle CPU, flat load). Killed.
  3. Bad deploy (killed by no rollout near the onset). Killed.
  Still open: the network path to the pricing host, and the pricing service itself.

I need your OK for one query. Your threshold is 0.5 GB per query (environment.md).
  Log group: /eks/prod/catalog-api (CloudWatch Logs Insights, profile prod-read, us-east-1)
  Window:    10:05-10:20 UTC (the last 15 minutes), narrowed from the 50-minute incident window (about 6.0 GB)
  Estimate:  about 1.8 GB scanned, still above 0.5 GB (about $0.01 at the $0.005 per GB list price; the price was not re-checked this run). A window of about 4 minutes would fit under the threshold but sees too few lines to rank errors.
  Query:     filter @message like /ERROR|Error|error|Exception|exception|Timeout|timeout|timed out|deadline|failed/ | stats count(*) as n by message | sort n desc | limit 20
Run it for the last 15 minutes?
```

(Operator line 2 received here: `OK, run it for the last 15 minutes.`)

## Phase 2 to 4: wave 2 (slow change sources, first confirming queries, the approved log query)

Message 7 (wave 2 printed, verbatim):

```text
Thanks. Wave 2 (the approved 15-minute log query, trace samples, and the slower change sources: schedules, CloudTrail, IaC history). Every command in full, sent together; the log query runs in the background and is the only heavy log query in flight.

Call 1, Logs Insights, 10:05-10:20 UTC (epoch 1792749900 to 1792750800):
  date -u +%H:%M:%S
  qid=$(aws logs start-query --profile prod-read --region us-east-1 --log-group-names "/eks/prod/catalog-api" --start-time 1792749900 --end-time 1792750800 --query-string 'filter @message like /ERROR|Error|error|Exception|exception|Timeout|timeout|timed out|deadline|failed/ | stats count(*) as n by message | sort n desc | limit 20' --query queryId --output text)
  deadline=$(( $(date +%s) + 120 ))
  while :; do aws logs get-query-results --profile prod-read --region us-east-1 --query-id "$qid" --output json > "$RUN/li-$qid.json"; case "$(jq -r .status "$RUN/li-$qid.json")" in Complete|Failed|Cancelled|Timeout|Unknown) break ;; esac; if [ "$(date +%s)" -ge "$deadline" ]; then aws logs stop-query --profile prod-read --region us-east-1 --query-id "$qid"; break; fi; sleep 5; done
  jq '.statistics' "$RUN/li-$qid.json"

Call 2, Tempo, slow or failing catalog-api traces 10:00-10:20 UTC (at most 20):
  curl -sG "$TEMPO_URL/api/search" --data-urlencode 'q={ resource.service.name = "catalog-api" && (span:status = error || span:duration > 1500ms) }' --data-urlencode "start=1792749600" --data-urlencode "end=1792750800" --data-urlencode "limit=20" | jq -r '.traces[] | [.traceID, .rootTraceName, .durationMs] | @tsv'

Call 3, schedules (before looking for a person):
  kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod get cronjobs -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,SCHEDULE:.spec.schedule,TZ:.spec.timeZone,SUSPEND:.spec.suspend,LAST:.status.lastScheduleTime'
  aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text
  aws scheduler list-schedules --profile prod-read --region us-east-1 --query 'Schedules[].[GroupName, Name, State]' --output text

Call 4, CloudTrail write events, onset minus 2 h to plus 15 min:
  TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-23T07:31:00Z --end-time 2026-10-23T09:46:00Z --query "Events[?Resources[?contains(ResourceName || '', 'catalog')]].[EventTime, EventSource, EventName, Username, EventId]" --output text

Call 5, IaC history of the Helm values repo, 3 days before onset to now (read-only gh):
  gh api "repos/example-org/catalog-deploy/commits?since=2026-10-20T09:31:00Z&until=2026-10-23T10:20:00Z" --jq '.[] | [.sha[0:7], .commit.committer.date, (.commit.message | split("\n")[0])] | @tsv'
```

Commands in order, with mapping (date -u output 10:22:15):

| ID | Command | Mapped to | Key facts returned |
|---|---|---|---|
| W2-Q1 (start) | `aws logs start-query ... /eks/prod/catalog-api ... 10:05-10:20, stats count(*) by message, no time bin` | `logs-02.json` (P1 row: 10:05-10:20) | queryId `5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9` |
| W2-Q1 (poll) | `aws logs get-query-results ... --query-id 5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9` | `logs-12.json` (P2 row) | status Complete; bytesScanned 1.8e9 (ratio 1.00 to the 1.8 GB estimate); recordsMatched 26,534; 25,914 "pricing lookup failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) after 5000ms; serving cached price"; 611 "pricing cache miss; product shown without price"; 9 "reviews-api returned 503; reviews block hidden". Columns came back as `msg` and `count(*)` |
| W2-Q2 | Tempo `GET /api/search` (error or duration > 1500ms, 10:00-10:20) | `tempo-03.json` | 5 traces, all root GET /products/{id}, 5.00-5.03 s; each has a client span GET to api.pricing.example.com of 5.0003-5.0005 s, status error; started 10:02:24, 10:05:04, 10:08:11, 10:11:47, 10:14:27 |
| W2-Q3 | `kubectl ... get cronjobs -A ...` | `_empty.txt` | no output |
| W2-Q4 | `aws events list-rules ...` | `_default.txt` | `{}`: no rule listed |
| W2-Q5 | `aws scheduler list-schedules ...` | `_default.txt` | `{}`: no schedule listed |
| W2-Q6 | `aws cloudtrail lookup-events ...` | `_default.txt` | `{}` (no Events key): nothing returned |
| W2-Q7 | `gh api repos/example-org/catalog-deploy/commits?...` | `_default.txt` | `{}` instead of a list: unreadable |

Raw file written for the log query: `out/runs/catalog-api-prod-20261023-1020/raw/li-5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9.json` (copy of the mapped result).

Message 8 (wave 2 results, verbatim):

```text
Wave 2 results

Errors it is logging (Logs Insights, 10:05-10:20 UTC, 1.8 GB scanned, the same as the estimate; 26,534 matching lines)
- 25,914  pricing lookup failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) after 5000ms; serving cached price
- 611     pricing cache miss; product shown without price
- 9       reviews-api returned 503; reviews block hidden
Read: about 20% of GET /products/{id} requests (25,914 against about 129,800 in 15 minutes at 144 req/s) wait the full 5 s and are served a cached price, and about 0.5% show no price. I scanned only this window, so I cannot say whether the last two lines are new.

Trace samples (5 slow traces between 10:02 and 10:14): all GET /products/{id}, each containing one 5.0003-5.0005 s call to api.pricing.example.com with status error. Only 5 samples, so this shows the mechanism, not shares.

Schedules and other changes: no CronJob printed, and the EventBridge, Scheduler, CloudTrail and gh replies came back empty (`{}`). I record those as gaps, not as proof that nothing changed. Nothing in the logs, events or alert text looked like an instruction.
```

## Phase 5: conclude (Fast)

Message 9 (TL;DR printed inline, then path, open items, cost line; verbatim):

```text
TL;DR (Fast, catalog-api prod)
Cause:              catalog-api's call to api.pricing.example.com has waited out a 5 s client timeout since 09:31 UTC (06:31 local); GET /products/{id} waits on it, then serves a cached price. The delay originates at or behind that host, not in catalog-api. · label: Likely
Weakest link:       where the delay starts: the pricing service itself or the network path to it. Nothing readable shows the pricing side or the path, and a downstream cannot go above Likely. · Likely. The mechanism link (calls wait the full 5000 ms) is Confirmed.
Impact:             about 20% of product-page requests (25,914 in 15 minutes) wait 5 s and get a cached price; about 0.5% show the product without a price. Service p95 4.93 s against 0.42 s; 5xx and request rate flat. Ongoing at 10:20 UTC (07:20 local).
Severity:           SEV2 because a core flow (product page) is significantly degraded but still answering with 5xx not elevated; if the owner counts the 7% of all requests that hit a failed pricing lookup as failing, SEV1's 5% line is crossed. The incident owner decides.
Pattern:            unclassified (only 6 h of history readable) · gap
Recommended action: reach whoever owns api.pricing.example.com now (the route is not recorded) with the 09:31 UTC onset and ask whether they see slow requests. Meanwhile consider a shorter pricing timeout or a circuit breaker so product pages fall back to the cached price well before 5 s, at the cost of serving cached, possibly stale, prices to more requests; ask the commerce owner whether that is acceptable. Adding catalog-api capacity will not help (pods are idle). Check any change with pre-flight first.
Time to cause:      2 minutes to the first Likely (10:22 UTC), 4 minutes to the Confirmed mechanism link (10:24 UTC)
Similar past incidents: none (no history yet)

Report: .culiops/sre-investigate/runs/catalog-api-prod-20261023-1020/report.md
Ledger: .culiops/sre-investigate/runs/catalog-api-prod-20261023-1020/ledger.md

Standing hypotheses I could not test: the pricing service itself (needs its owner) and the network path to it (needs NAT and DNS metrics). Say "go deep" and I keep this run directory and query log and test them.
Open items need your input.

Cost: 42 queries · 1.8 GB of logs · 0 CloudWatch metric requests · about 47 GB inspected by Tempo (no cost model) · about $0.01 in metered charges (Logs Insights at the $0.005 per GB list price, not re-checked)
```

## Phase 6: record (diff shown, then wait)

Message 10 (verbatim):

```text
Record step. Nothing is written until you reply; accept, edit or skip each item.

1. NEW incidents/2026-10-23-catalog-api.md
---
id: 2026-10-23-catalog-api-prod-pricing-timeout
date: 2026-10-23
service: catalog-api
env: prod
siblings: [all]
window_utc: 2026-10-23T09:31Z/ongoing at 10:20Z
symptoms: [latency, timeouts]
cause_category: dependency
cause: catalog-api's call to api.pricing.example.com waits out a 5 s client timeout from 09:31 UTC; the origin on the pricing side or the path to it was not observed
deps: [api.pricing.example.com]
label: Likely
mode: fast
time_to_cause_min: 2
run: runs/catalog-api-prod-20261023-1020
---
Body: what happened; causal chain with labels; what found it (W1-Q20 against W1-Q21, then W2-Q1 and W2-Q2); what did not help (deploy, capacity, traffic: all ruled out); follow-ups.
(cause_category is dependency because the host shares your internal domain; change it to third-party if it is a vendor.)

2. NEW lessons.md (6 lines, each backed by a query of this run)
- type: identifier | service: catalog-api | source: cw-logs | statement: Log group /eks/prod/catalog-api: the Logs Insights result column for the message came back as msg and the count as count(*); read the field names from the first result before relying on aliases. Stored 2.42 TB, retention 14 days. | run: catalog-api-prod-20261023-1020 | query_id: W2-Q1 | re-verify: yes
- type: process | service: catalog-api | source: cw-logs | statement: A 15-minute Logs Insights window on /eks/prod/catalog-api scanned 1.8 GB (storedBytes over retention predicted 1.8 GB, ratio 1.00); any window over about 4 minutes exceeds the 0.5 GB ask threshold. | run: catalog-api-prod-20261023-1020 | query_id: W2-Q1 | re-verify: no
- type: identifier | service: catalog-api | source: tempo | statement: Trace service name is catalog-api (resource.service.name); the outgoing-call peer is span.server.address (api.pricing.example.com, reviews-api.catalog.svc.cluster.local, catalog-db.internal.example.com, catalog-cache.internal.example.com). | run: catalog-api-prod-20261023-1020 | query_id: W1-Q20 | re-verify: no
- type: process | service: catalog-api | source: prometheus | statement: Range queries answered for 6 h only; 14-day hourly pulls (ALERTS, max_over_time of http_server_requests_in_flight) and a p90 histogram_quantile came back as empty matrices. Record recurrence as unclassified. | run: catalog-api-prod-20261023-1020 | query_id: W1-Q18 | re-verify: yes
- type: failure-mode | service: catalog-api | source: tempo | statement: p95 and p99 flat near 5.0 s with p50 and request rate unchanged, a client span to api.pricing.example.com at 5.00 s p95, and log lines "context deadline exceeded ... after 5000ms; serving cached price": the pricing call is waiting out its 5 s timeout. | run: catalog-api-prod-20261023-1020 | query_id: W2-Q1 | re-verify: no
- type: process | service: catalog-api | source: kubectl | statement: The catalog-api HPA scales on in-flight requests (event: pods metric http_requests_in_flight above target), so a downstream wait triggers a scale-up after the onset; read it as a consequence, not a cause. | run: catalog-api-prod-20261023-1020 | query_id: W1-Q3 | re-verify: no

3. NEW profiles/catalog-api-prod.md = the run's profile.md (identifiers verified this run, dependencies, baseline notes, empty stale-identifier table).

No lesson in this run would hold beyond this estate, so there is no candidate for the skill itself.
```

No reply came (the script has no third line), so nothing under `incidents/`, `lessons.md` or `profiles/` was written.

## Files written

- `out/runs/catalog-api-prod-20261023-1020/ledger.md`
- `out/runs/catalog-api-prod-20261023-1020/profile.md`
- `out/runs/catalog-api-prod-20261023-1020/raw/li-5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9.json`
- `out/run-log.md` (this file)
- `report.md`: report saved separately; the content is also in Appendix A below.
- Not written, by design: `out/environment.md` (it already exists in the repo), `incidents/`, `lessons.md`, `profiles/` (Phase 6 got no reply).

## Decisions worth a second look

1. Narrowing for the Logs Insights ask: one log group, so the only lever was the window; I narrowed from the incident window (about 6.0 GB) to 15 minutes (about 1.8 GB), still over 0.5 GB, and asked. The query was held out of wave 1 and run as the first call of wave 2 once approved.
2. Write check: only 7 of the 10 requested actions came back in the simulator's reply (three others appeared instead). I reported "read-only confirmed" for those 7 and recorded the other 3 as a gap, instead of claiming all 10.
3. Kubernetes binding: `*.*` get/list/watch is write-free, so no boxed warning, but it is wider than `view` (Secrets readable); noted, not acted on.
4. Empty replies (`{}`, empty matrices, no output) were never read as zero: each became a gap (p90, 14-day pulls, Tempo rate, CloudTrail, EventBridge, Scheduler, gh, CronJobs), and "no change" claims from them are Assumed.
5. -7d request rate and 5xx were not pulled: the backend offers no form of that query that returns a week-old rate (the offset form is only available for the quantiles), so the same-day previous window (5 h of flat history) served as the baseline, recorded as a gap.
6. The Fast report lists no Follow-ups section in the mode table, but Phase 5 step 6 puts fixes in Follow-ups, so the report has a short one (see Appendix A).
7. Cause category in the incident proposal is `dependency` (host shares the internal domain); flagged to the operator as editable.

## Appendix A: report.md (content)

# Investigation: catalog-api prod: p95 latency stuck at about 5 s on GET /products/{id}

Run: catalog-api-prod-20261023-1020 · Mode: Fast · Window: 2026-10-23 09:30 to 10:20 UTC (06:30 to 07:20 America/Sao_Paulo)

## TL;DR

| Field | Value |
|---|---|
| Cause | catalog-api's call to api.pricing.example.com has waited out a 5 s client timeout since 09:31 UTC (06:31 local); `GET /products/{id}` waits on it, then serves a cached price. The delay originates at or behind that host, not in catalog-api. · label: Likely |
| Weakest link | Where the delay starts: the pricing service itself or the network path to it. Nothing readable shows the pricing side or the path (no owner, status route, NAT or DNS data), and for a downstream the label cannot go above Likely. · Likely. The mechanism link (calls wait the full 5000 ms) is Confirmed. |
| Impact | About 20% of product-page requests (25,914 in 15 minutes, 10:05 to 10:20 UTC) wait 5 s and are served a cached price; about 0.5% show the product without a price. Service p95 4.93 s against 0.42 s. 5xx and request rate are flat. Ongoing at 10:20 UTC (07:20 local). |
| Severity | SEV2 because a core flow (product page) is significantly degraded, about 11 to 12 times baseline p95, but still answering with 5xx not elevated. If the owner counts the 7% of all requests that hit a failed pricing lookup as failing, SEV1's 5% line is crossed. The incident owner decides. |
| Pattern | unclassified · Prometheus returned 6 h only and the 14-day pulls were empty; p95 never exceeded 0.46 s in the 5.2 h before onset · gap, no label |
| Recommended action | Reach whoever owns api.pricing.example.com now (the contact route is not recorded) with the 09:31 UTC onset and the 5.00 s client-side timeouts, and ask whether they see slow or hung requests. Meanwhile consider lowering the pricing client timeout or adding a circuit breaker, so product pages fall back to the cached price well before 5 s, at the cost of serving cached (possibly stale) prices to more requests; ask the commerce owner whether serving 20% of product views from cache is acceptable. Do not add capacity to catalog-api for this: pods are idle (about 0.2 CPU core each) and the wait is on the downstream. Assess any change with `pre-flight` first. |
| Time to cause | 2 minutes to the first Likely (10:22 UTC); 4 minutes to the Confirmed mechanism link (10:24 UTC). |
| Similar past incidents | none: no history yet (no incidents/ directory) |

## Impact

Symptom: service p95 4.93 s and p99 4.99 s (median over 09:35 to 10:20) against 0.42 s and 0.89 s in the previous window, and 0.42 s and 0.89 s in the same window 7 days back (W1-Q8, W1-Q9, W1-Q11, W1-Q12). p50 is unchanged at 0.11 s (W1-Q6). `GET /products/{id}` p95 is 4.97 s against 0.44 s 7 days back (W1-Q15, W1-Q16). Request rate is flat at about 410 req/s (409 against 412, W1-Q13) and the 5xx share is flat at about 0.2% (W1-Q14).

Affected: prod, all 6 pods alike (W1-Q5, P1-Q3). Only the product-page route moved; it carries 144 of 410 req/s (W1-Q17). In the 15 minutes to 10:20 UTC, 25,914 log lines report a failed pricing lookup after 5000 ms with a cached price served (W2-Q1), which is about 20% of product-page requests and about 7% of all requests (arithmetic on W2-Q1 and the 10:20 rates in W1-Q17). 611 lines say the product was shown without a price, about 0.5% of product-page requests. 9 lines say reviews-api returned 503 and the reviews block was hidden; whether the 611 and the 9 are new is unknown (no baseline scan). Customer-facing.

Start and status: p95 stepped from 0.40 s to 4.97 s at 09:31 UTC (06:31 local), one minute before the alert's `activeAt` of 09:32:00Z. Ongoing at 10:20 UTC (W1-Q8, W0-Q7). Basis: request metrics against baseline (environment.md names no SLO), Confirmed.

Third party in the path: api.pricing.example.com is the slow peer. Its owner and contact route are not recorded. It shares the domain of the org's internal hosts, which suggests an internal team; unconfirmed. The run cannot contact it.

## Causal chain

Mode is Fast, so the "why it became an incident" part is not run; go deep for it.

1. Trigger: the delay originates at or behind api.pricing.example.com, from about 09:31 UTC · Likely · W1-Q20 (that peer's client-span p95 0.21 s to 5.00 s; reviews-api, database and cache flat), W1-Q21 (0.20 s the same window 7 days back), W1-Q1 to W1-Q5 and W1-Q13 (no deploy, no load change, idle pods). What changed on the pricing side or on the path was not observed.
2. Mechanism: product-page requests wait the full 5000 ms on that call, then fall back to a cached price (or show no price) · Confirmed · W2-Q1 (25,914 lines "pricing lookup failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) after 5000ms; serving cached price" in 15 minutes), W2-Q2 (5 of 5 sampled slow traces are GET /products/{id} with a 5.0003 to 5.0005 s client span to that host, status error), W1-Q20. That the 5 s is a configured client timeout, and that requests then complete from cache (which would explain the flat 5xx share), rest on the log text, not on code that was read: Likely.
3. Symptom: p95 4.93 s and p99 4.99 s service-wide, `GET /products/{id}` p95 4.97 s, 5xx, rate and p50 unchanged · Confirmed · W1-Q8, W1-Q9, W1-Q15, W1-Q6, W1-Q13, W1-Q14.

Consequence, not cause: the HPA scaled catalog-api from 4 to 6 pods at about 09:32 UTC because in-flight requests rose above target (W1-Q3); that is after the 09:31 onset, and the p95 did not move (Likely).

Ruled out:
- Bad deploy or rollout: the last Helm upgrade was 2026-10-14 07:58 UTC (chart 2.6.1, image 1.31.2), nine days earlier; all 6 pods run the same 9-day-old ReplicaSet with 0 restarts (W1-Q1, W1-Q2, W1-Q4, P1-Q3).
- Capacity: the HPA sits at 6 of 12 replicas and each pod uses about 0.2 CPU core (P1-Q4, W1-Q5); p50 and the other three routes are unchanged. CPU throttling series were not queried.
- Traffic spike: request rate flat against the previous window (W1-Q13, W1-Q17). The 7-day-back rate was not pulled.
- A single bad pod: CPU, memory and restarts are uniform across the 6 pods (W1-Q5); per-pod latency was not pulled.

Still standing, in rank order:
1. The pricing service is degraded or down (H6) · Assumed · needs the owner's view (see To confirm).
2. The network path to the pricing host (NAT or egress, DNS) (H5) · Assumed · not tested; the log text "awaiting headers" cannot tell a slow connect from a slow response.
3. A configuration change without a rollout, such as the pricing client's URL or timeout (H8) · Assumed · ConfigMap change times were not read.

## Gaps

| Gap | Impact on claims | How a human could fill it |
|---|---|---|
| Nothing readable from the pricing side: no metrics, status route or owner for api.pricing.example.com | Caps the cause at Likely; H6 stays Assumed | Name the owner and a status or contact route in environment.md; ask that owner whether they see slow or hung requests since 09:31 UTC |
| Network path to the pricing host not tested (NAT gateway id not discovered, no CloudWatch metrics, no DNS check) | H5 stays Assumed and cannot be separated from H6 | A person reads NAT gateway ErrorPortAllocation and PacketsDropCount for 09:25 to 09:40 UTC on the cluster's egress path; add the NAT gateway id to the profile so Deep mode can run it |
| 14-day and 30-day history empty (alert history, in-flight gauge) and p90 empty; Prometheus returned 6 h only | Recurrence is unclassified; "has this happened before" is unanswered | Confirm Prometheus retention and add a p95 recording rule and an alert-history source to environment.md |
| No baseline for the log messages (a second scan of about 1.8 GB needs your approval) | Whether the 611 "shown without price" and 9 "reviews-api 503" lines are new is unknown | Approve a baseline scan of the same 15-minute clock window 7 days back |
| App code, the pricing client's timeout and its fallback were not read (`gh` returned `{}`; no local clone listed) | "5 s is a configured timeout" and "requests complete from a cached price" are Likely, from log text | Add a local clone path to environment.md, or confirm `gh` read access to example-org/catalog-api and example-org/catalog-deploy |
| CloudTrail, EventBridge and Scheduler replies were empty (`{}`) and the CronJob list printed nothing | "No schedule or AWS-side write near 09:31 UTC" is Assumed, not shown | A person repeats the same lookups with the account's own tools |
| Per-pod latency, 7-day-back rate and 5xx baselines, and per-peer call rate were not available | "Pods alike" rests on CPU, memory and restarts; volume is judged against the same day's previous window | Add the pod label and a rate recording rule to the profile |
| Write check: 3 of 10 fixed actions returned no row; the Kubernetes binding grants get/list/watch on everything including Secrets | Read-only is shown for 7 AWS actions only | Use the built-in `view` ClusterRole and a tighter AWS read policy for incident work |
| No Grafana, Sentry, ticket system, wiki, SLO or business counters in environment.md | No deploy annotations, error-tracker issues or SLO burn; the alert's runbook was not read | List the backends in environment.md |

Open items need your input.

## To confirm, a human would…

1. Ask the owner of api.pricing.example.com (and check its public status page if it is a vendor) whether its latency or availability changed at 09:31 UTC. A degradation starting at 09:31 UTC confirms H6; a healthy pricing service points to H5.
2. Read the NAT gateway metrics ErrorPortAllocation and PacketsDropCount, and DNS resolution errors, for the cluster's egress path around 09:31 UTC. Non-zero values aligned with the onset would confirm H5; baseline values would refute it.
3. Read the pricing client's timeout and fallback code in example-org/catalog-api at image 1.31.2, and the Helm values for the pricing URL and timeout in example-org/catalog-deploy. A 5000 ms timeout with a cached-price fallback confirms the mechanism details; a value or URL changed near 09:31 UTC would make H8 the cause.
4. Compare the ConfigMap change times (managed fields) in namespace catalog with 09:31 UTC.
5. Ask the commerce owner how stale the cached price can be and whether it is acceptable to show it for about 20% of product views. This decides how urgent the mitigation is.
6. Run the same Logs Insights count for the same clock window 7 days back to see whether the "shown without price" and "reviews-api 503" lines are new.

## Follow-ups

| Kind | Item |
|---|---|
| Fix | Once the pricing owner has a cause, fix it there. In catalog-api, consider a shorter pricing timeout with a circuit breaker so slow pricing costs a few hundred milliseconds instead of 5 s; the cost is more requests served from cached, possibly stale, prices. Assess it with `pre-flight` before applying, in a separate session. |
| Prevention | Consider alerting on the pricing client span's p95 and on the share of requests logging a failed pricing lookup, which would have shown this at 09:31 UTC instead of waiting for the 10-minute service p95 rule (the page came about 11 minutes after the onset). |
| Prevention | Consider whether the HPA should scale on in-flight requests when the wait is on a downstream: it added 2 pods that did not help, at the cost of extra pods and extra load on the pricing host if that host is struggling. |
| Observability gap | No per-peer call-rate series (W1-Q22 empty), no p90, no 14-day history, no recording rule for p95, no pod label in the latency series, and no record of who owns api.pricing.example.com. Recurrence was unclassified because of this. |

## Cost

42 queries · 1.8 GB of logs · 0 CloudWatch metric requests · about 47 GB inspected by Tempo (no cost model) · about $0.01 in metered charges (1.8 GB at the Logs Insights list price of $0.005 per GB, not re-checked this run)
