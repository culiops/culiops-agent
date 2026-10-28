# Run log: catalog-api prod (case-g), run directory `catalog-api-prod-20261023-1020`

Simulation conventions used throughout
- "World" clock: INDEX.md evaluates everything at 2026-10-23 10:20 UTC, so `date -u` (no INDEX row) is taken as 10:20 UTC on that date; the run directory name uses it. Wave start times below are only for the Start column; every data window stays on the fixed ledger window ending 10:20:00 UTC.
- Output root = `.culiops/sre-investigate/` at the repo root (the case directory). Writes were redirected to `out/` with the same relative layout (so `out/runs/catalog-api-prod-20261023-1020/ledger.md` stands for `.culiops/sre-investigate/runs/.../ledger.md`).
- Commands with no INDEX row got `_empty.txt` (text commands) or `_default.txt` (`{}`, JSON API calls), per INDEX rule 7.
- Offset-7d, p90, per-pod, hourly-14d and instant-at-another-time Prometheus queries: no INDEX row names them, and no row's window covers the week-earlier clock for rate/5xx/route-rate, so they got `prom-14.json` (empty matrix). I did not reuse today's data as a stand-in for a -7d baseline.
- Budget unit (my assumption, stated to the operator): one "query" = one call to a metric, log, trace, cluster or code backend. Identity, write-checks, identifier discovery and local file reads are not counted. Budgets other than the Insights ask threshold are not in environment.md, so the template's neutral Fast defaults apply (20 queries, 2 GB logs, 100 CloudWatch metric requests; soft limit 1 GB; windows: patterns 2h, log metric 12h, raw 30m).

Operator lines received
1. (at start) `catalog-api latency alert in prod has been firing for about 50 minutes. Can you also pull what errors it is logging? Fast mode.`

---

## Phase 0 steps 1-2: output root, environment, mode detection (tool call before the first message)

Printed, then run (no wave number; query IDs W0-Q1..Q5):

```text
git rev-parse --show-toplevel
git check-ignore -q .culiops/sre-investigate
cat .culiops/sre-investigate/environment.md
ls .culiops/sre-investigate
command -v agentbox-env
```

| ID | Command | World file | Key facts returned |
|---|---|---|---|
| W0-Q1 | `git rev-parse --show-toplevel` | no INDEX row -> `_empty.txt` | no output; the case directory is taken as the repo root (the task statement says it stands for the team's repo) |
| W0-Q2 | `git check-ignore -q .culiops/sre-investigate` | no INDEX row -> `_empty.txt` | no output, exit 0 = ignored by git |
| W0-Q3 | `cat .culiops/sre-investigate/environment.md` | `environment.md` | timezone America/Sao_Paulo (UTC-3); account prod 111122223333 us-east-1 profile `prod-read`; kube context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `catalog`; Prometheus `$PROM_URL` (no token), Tempo `$TEMPO_URL` (no token), CloudWatch Logs group `/eks/prod/<service>`, kubectl/Helm; code `example-org/catalog-api` via gh, Helm values `example-org/catalog-deploy`; Insights ask threshold 0.5 GB; default severity scale; core flows `GET /products/{id}`, `GET /search` |
| W0-Q4 | `ls .culiops/sre-investigate` | `ls-01.txt` | only `environment.md`: no `profiles/`, `lessons.md`, `incidents/` -> first run for this service, no history |
| W0-Q5 | `command -v agentbox-env` | `_empty.txt` (INDEX: exit status 1) | not found -> Culibox notice NOT printed, nothing said about Culibox |

CULIOPS_HOME: the INDEX only knows the repo-local path, so the repo-local output root is used. Mode: ongoing alert + operator said "Fast mode" -> Fast.

## Message 1 to the operator (verbatim)

```text
Mode: Fast. The alert has been firing for about 50 minutes and you asked for Fast, so this is live triage: access checks first, then at most three query waves, no checkpoints. I will stop and ask only for a Logs Insights query over your 0.5 GB threshold, or for a query that would take the run past its budget.

Output root: .culiops/sre-investigate/ at the repo root (environment.md found there). Everything this run writes goes under it, in runs/catalog-api-prod-20261023-1020/. It is local and is never committed; git check-ignore says it is already ignored, so I am not touching .gitignore.

Window: "about 50 minutes" is a relative time, so it is anchored on now (10:20 UTC) and needs no zone.
  Incident            2026-10-23 09:30-10:20 UTC  (06:30-07:20 America/Sao_Paulo, UTC-3, from environment.md)
  Baseline, previous  2026-10-23 08:40-09:30 UTC
  Baseline, -7d       2026-10-16 09:30-10:20 UTC

Assumptions (also in the ledger): environment.md sets only the Logs Insights threshold, so the other budgets are the template's neutral Fast defaults: 20 queries, 2 GB of logs scanned, 100 CloudWatch metric requests; a log query over 1 GB is narrowed first; window caps are 2h for patterns, 12h for log counts, 30 min for raw lines. I count a "query" as one call to a metric, log, trace or cluster backend; identity checks, write-checks, identifier discovery and local reads are not counted.

Wave 0 (access, intake, one log-size probe, the alert itself). Every command, in full:

# call 1: identity, role lookup, write-check simulation (prod-read)
date -u +%H:%M:%S
aws sts get-caller-identity --profile prod-read --output json > "$RUN/raw/sts.json"
arn=$(jq -r .Arn "$RUN/raw/sts.json")
role=${arn#*:assumed-role/}; role=${role%%/*}
role_arn=$(aws iam get-role --profile prod-read --role-name "$role" --query Role.Arn --output text)
aws iam simulate-principal-policy --profile prod-read \
  --policy-source-arn "$role_arn" \
  --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances \
    ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy \
    iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode \
    cloudformation:DeleteStack \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text

# call 2: Kubernetes identity and write-check
kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod
kubectl config current-context
kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace catalog

# call 3: log-size probe (list by prefix, then estimate for the last 15 minutes; no log data is read)
aws logs describe-log-groups --profile prod-read --region us-east-1 \
  --log-group-name-prefix "/eks/prod/catalog" --output json \
| jq -r --argjson win 900 --argjson now "$(date +%s)" '
    .logGroups[]
    | (.retentionInDays // null) as $r
    | (($now - .creationTime / 1000) | floor) as $age
    | (if $r then ([$r * 86400, $age] | min) else $age end) as $span
    | [.logGroupName, (.logGroupClass // "-"), ($r // "none"),
       ((.storedBytes / 1e9 * 100 | round) / 100),
       ((.storedBytes * $win / $span / 1e9 * 1000 | round) / 1000)]
    | @tsv'

# call 4: the alert that fired (Prometheus, no token)
curl -sG "$PROM_URL/api/v1/alerts"

Token check: environment.md lists no token_env for any backend (Prometheus and Tempo are network-restricted), so there is nothing to check. No error tracker, ticket or WAF leg applies.
```

## Wave 0 (start 10:20:31 UTC) - commands, mapped files, facts

| ID | Command | World file | Key facts |
|---|---|---|---|
| W0-Q6 | `aws sts get-caller-identity --profile prod-read` | `sts-01.json` | Account 111122223333 = environment.md (no mismatch); assumed-role `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` (session name not recorded) |
| W0-Q7 | `aws iam get-role --profile prod-read --role-name AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b --query Role.Arn --output text` | `iam-01.json` | role ARN under path `/aws-reserved/sso.amazonaws.com/` (hand-built ARN would have failed) |
| W0-Q8 | `aws iam simulate-principal-policy ... (10 actions)` | `iam-02.json` | 10 result rows, all `implicitDeny`, BUT the action set differs from the 10 I asked: returned s3:PutObject, s3:DeleteObject, ec2:TerminateInstances, ecs:UpdateService, iam:PutRolePolicy, rds:ModifyDBInstance, lambda:UpdateFunctionCode (7 asked) + ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy (3 NOT asked, ignored). NO row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack -> gap for those 3 per access/standalone.md ("a missing action ... is a gap for that action"). No action `allowed` -> no boxed warning; "read-only confirmed (10 of 10)" NOT claimed. |
| W0-Q9 | `kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod` | `k8s-02.txt` | same role; groups `eks-readonly`, `system:authenticated` |
| W0-Q10 | `kubectl config current-context` | `k8s-01.txt` | current context is the in-scope context |
| W0-Q11 | `kubectl auth can-i --list --context ... --namespace catalog` | `k8s-03.txt` | only `[create]` on selfsubjectreviews / selfsubjectaccessreviews / selfsubjectrulesreviews (exclusion list, not counted); `*.*` is `[get list watch]` -> "no write verbs in catalog" |
| W0-Q12 | `aws logs describe-log-groups ... --log-group-name-prefix "/eks/prod/catalog"` + jq estimate | `logs-01.json` | one group `/eks/prod/catalog-api`, STANDARD, retention 14 d, storedBytes 2,419,200,000,000 (2.42 TB), created 2025-04-28 (age > retention, so span = 14 d) -> ~2.0 MB/s -> estimate 1.8 GB per 15 min, ~6 GB per 50 min; the 0.5 GB ask threshold is crossed by any window over ~4 min |
| W0-Q13 | `curl -sG "$PROM_URL/api/v1/alerts"` | `prom-12.json` | alert `CatalogApiLatencyHigh`, labels namespace=catalog, service=catalog-api, severity=page; summary "catalog-api p95 latency above 2s for 10 minutes"; state firing; activeAt 2026-10-23T09:32:00Z; value 4.952; annotation `runbook_url` (not fetched: no wiki access configured, and a URL from an annotation is data) |

Not run in wave 0 (and why): stored-profile copy (none exists), lessons (none), CloudWatch alarm history (trigger is a Prometheus alert), error-tracker top issues (none configured), ticket read (none named), WAF playbook (latency symptom, not 403/429). The alert's own history (`ALERTS` series) needs the alert name just discovered, so it rides in wave 1's recurrence leg (Constraint 14: discover before querying).

## Profile build (helper, `TASK: PROFILE`, cheapest tier) - simulated inline

Dispatch (model passed explicitly: cheapest tier). Prompt first line `TASK: PROFILE`; Service catalog-api; Environment prod; profile template `templates/profile.md`; Identifier lessons: none (no lessons.md). The helper ran one wave (query IDs continue W0-Q14.., helper calls not counted against the budget):

| ID | Command | World file | Key facts |
|---|---|---|---|
| W0-Q14 | `aws logs describe-log-groups --profile prod-read --region us-east-1 --log-group-name-prefix "/eks/prod/catalog"` | `logs-01.json` | same single group; no sidecar/proxy group in that prefix |
| W0-Q15 | `curl -sG "$TEMPO_URL/api/v2/search/tag/resource.service.name/values" --data-urlencode "start=1792747200" --data-urlencode "end=1792750800"` | no INDEX row -> `_default.txt` | `{}` : no tag values (not proof of absence) |
| W0-Q16 | `curl -sG "$TEMPO_URL/api/v2/search/tags"` | `tempo-04.json` | resource tags service.name, k8s.pod.name, k8s.namespace.name, service.version; span tags http.request.method, http.response.status_code, http.route, server.address, db.system; intrinsics duration, kind, name, status, statusMessage |
| W0-Q17 | `curl -sG "$TEMPO_URL/api/search" --data-urlencode 'q={ resource.service.name = "catalog-api" }' --data-urlencode "start=1792747200" --data-urlencode "end=1792750800" --data-urlencode "limit=5"` | `tempo-05.json` | `traces: []`, inspectedTraces 0 -> trace service name stays `(unverified)` |
| W0-Q18 | `curl -sG "$PROM_URL/api/v1/label/service/values"` | no INDEX row -> `_default.txt` | `{}` |
| W0-Q19 | `curl -sG "$PROM_URL/api/v1/label/__name__/values"` | `prom-13.json` | 12 names: http_server_request_duration_seconds_{bucket,count,sum}, http_client_request_duration_seconds_{bucket,count,sum}, http_server_requests_in_flight, kube_deployment_status_replicas, kube_pod_container_status_restarts_total, go_goroutines, process_cpu_seconds_total, up. No span metrics, no cAdvisor, no kube_pod_owner |
| W0-Q20 | `kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog get pods` | `k8s-04.txt` | 6 pods catalog-api-6b9d7c5f48-*, all Running 1/1, RESTARTS 0; four are 9d old, kx9vn is 48m, p6wfj is 47m |
| W0-Q21 | `kubectl --context ... -n catalog get hpa` | `k8s-06.txt` | HPA catalog-api -> Deployment/catalog-api, TARGETS 58/40, min 4, max 12, replicas 6, age 211d |
| W0-Q22 | `kubectl --context ... -n catalog get deployments,services,ingresses` | no INDEX row -> `_empty.txt` | no output (Deployment/Service/Ingress names stay unverified) |
| W0-Q23 | `helm list --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog` | INDEX: `helm list` -> `_empty.txt` | no output (release name unverified) |
| W0-Q24 | `ls .culiops/service-discovery` | no row -> "No such file or directory", exit 1 | no service-discovery catalog |
| W0-Q25 | `gh api repos/example-org/catalog-api` | no INDEX row -> `_default.txt` | `{}`: default branch not returned; app repo unreadable in this run (gap) |

Helper returned the profile (written by the main session to `runs/catalog-api-prod-20261023-1020/profile.md`; the helper's `verified` marks were re-checked against Constraint 14: the log group name equals the service name so it keeps `verified`; the trace service name stays `(unverified)`; the `message` field was never returned by a call so it stays `(unverified)`).

Ledger written after wave 0 and the profile build: `runs/catalog-api-prod-20261023-1020/ledger.md` (Problem, Access, Windows, Gaps, query-log rows W0-Q1..Q25) and `.../profile.md`.

## Message 2 to the operator (verbatim): wave 0 results, profile, wave 1 commands

```text
Wave 0 done (10:20:31 UTC).

Identity: prod-read is account 111122223333 (matches environment.md), role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b, session valid. The Kubernetes context is the same role, group eks-readonly.

Write-check, prod-read: informational notice, not the warning. No action came back "allowed". 7 of the 10 broad write actions came back implicitDeny (s3:PutObject, s3:DeleteObject, ec2:TerminateInstances, ecs:UpdateService, iam:PutRolePolicy, rds:ModifyDBInstance, lambda:UpdateFunctionCode). The other 3 (ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack) came back with no row, and the reply carried 3 actions I did not ask about (ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy, all implicitDeny) that I ignored. So I am not writing "read-only confirmed": the 3 missing actions are a gap, and the simulation never covers resource-scoped writes. The role name looks like a ReadOnly permission set, but I do not infer read-only from a name. If you can confirm in chat that prod-read is read-only, I will record that as operator-asserted. The run only reads either way.

Write-check, arn:aws:eks:us-east-1:111122223333:cluster/prod, namespace catalog: no write verbs in catalog (the only create rights are the default self-review ones; everything else is get/list/watch).

Tokens: environment.md lists none (Prometheus and Tempo are network-restricted), so nothing to check.

The alert: CatalogApiLatencyHigh (severity page), "catalog-api p95 latency above 2s for 10 minutes", value 4.95 s now, active since 09:32:00 UTC (06:32 local), still firing. It carries a runbook_url annotation; no wiki access is configured, so I have not read it.

Log probe: the only group under /eks/prod/catalog is /eks/prod/catalog-api (14-day retention, 2.42 TB stored, about 2 MB/s). Estimated Logs Insights scan: about 1.8 GB for the last 15 minutes and about 6 GB for 50 minutes. Anything longer than about 4 minutes is over your 0.5 GB threshold, so the log query will need your OK. I will ask once wave 1 tells me what to look for.

First run for catalog-api/prod: no stored profile, lessons or incident history exist. A helper (cheapest model) built the profile; the run continues while you read it, tell me if a name is wrong.

  Namespace catalog; pods catalog-api-6b9d7c5f48-* (6, no restarts); HPA catalog-api min 4, max 12, now 58/40 with 6 replicas.
  Logs: CloudWatch group /eks/prod/catalog-api (verified); field "message" (unverified).
  Metrics: http_server_request_duration_seconds_{bucket,count,sum}, label service="catalog-api" (label values unverified until a query returns them). No span metrics exist in Prometheus.
  Traces: Tempo, resource.service.name "catalog-api" (unverified: a search for that exact name returned 0 traces).
  Code: example-org/catalog-api and Helm values in example-org/catalog-deploy (unreadable so far: gh returned nothing).
  Not found: Deployment/Service/Ingress/Helm release names (kubectl and helm printed nothing), dashboards, error tracker, service-discovery notes.

Gaps so far: write capability partly unknown (3 of 10 actions); app code and IaC unreadable through gh; trace service name unverified.

Wave 1 (change events, golden signals with p50/p90/p95/p99, per-route latency and call rate, slow-downstream breakdown, recurrence pull). Pods and the HPA are reused from W0-Q20/Q21. Every command, in full:

# call 1: deploy record
date -u +%H:%M:%S
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog rollout history deployment/catalog-api
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog get rs --sort-by=.metadata.creationTimestamp
helm history catalog-api --kube-context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog --max 10

# call 2: events (short-lived) and saturation
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog get events --sort-by=.lastTimestamp
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog top pods

# call 3: latency quantiles, incident and previous window in one range (08:40-10:20 UTC), now and one week earlier
for q in 0.5 0.9 0.95 0.99; do
  for off in "" " offset 7d"; do
    curl -sG "$PROM_URL/api/v1/query_range" \
      --data-urlencode "query=histogram_quantile($q, sum by (le) (rate(http_server_request_duration_seconds_bucket{service=\"catalog-api\"}[5m]${off})))" \
      --data-urlencode "start=1792744800" --data-urlencode "end=1792750800" --data-urlencode "step=60" \
      > "$RUN/raw/m-lat-q${q}${off// /_}.json"
  done
done

# call 4: request rate and 5xx share, now and one week earlier
for off in "" " offset 7d"; do
  curl -sG "$PROM_URL/api/v1/query_range" \
    --data-urlencode "query=sum(rate(http_server_request_duration_seconds_count{service=\"catalog-api\"}[5m]${off}))" \
    --data-urlencode "start=1792744800" --data-urlencode "end=1792750800" --data-urlencode "step=60" \
    > "$RUN/raw/m-rate${off// /_}.json"
  curl -sG "$PROM_URL/api/v1/query_range" \
    --data-urlencode "query=sum(rate(http_server_request_duration_seconds_count{service=\"catalog-api\", status=~\"5..\"}[5m]${off})) / sum(rate(http_server_request_duration_seconds_count{service=\"catalog-api\"}[5m]${off}))" \
    --data-urlencode "start=1792744800" --data-urlencode "end=1792750800" --data-urlencode "step=60" \
    > "$RUN/raw/m-5xx-share${off// /_}.json"
done

# call 5: per-route p95 and call rate at 10:20 UTC (30m rate window), now and one week earlier
for off in "" " offset 7d"; do
  curl -sG "$PROM_URL/api/v1/query" \
    --data-urlencode "query=histogram_quantile(0.95, sum by (le, route) (rate(http_server_request_duration_seconds_bucket{service=\"catalog-api\"}[30m]${off})))" \
    --data-urlencode "time=1792750800" > "$RUN/raw/m-route-p95${off// /_}.json"
  curl -sG "$PROM_URL/api/v1/query" \
    --data-urlencode "query=sum by (route) (rate(http_server_request_duration_seconds_count{service=\"catalog-api\"}[30m]${off}))" \
    --data-urlencode "time=1792750800" > "$RUN/raw/m-route-rate${off// /_}.json"
done

# call 6: slow-downstream breakdown, client spans by peer address (Tempo; 5-minute step), now and one week earlier, plus call rate
for w in "now 1792744800 1792750800" "minus7d 1792140000 1792146000"; do
  read -r win ws we <<< "$w"
  curl -sG "$TEMPO_URL/api/metrics/query_range" \
    --data-urlencode 'q={ resource.service.name = "catalog-api" && span:kind = client } | quantile_over_time(span:duration, .95) by (span.server.address)' \
    --data-urlencode "start=$ws" --data-urlencode "end=$we" --data-urlencode "step=300" > "$RUN/raw/t-client-p95-$win.json"
done
curl -sG "$TEMPO_URL/api/metrics/query_range" \
  --data-urlencode 'q={ resource.service.name = "catalog-api" && span:kind = client } | rate() by (span.server.address)' \
  --data-urlencode "start=1792744800" --data-urlencode "end=1792750800" --data-urlencode "step=300" > "$RUN/raw/t-client-rate-now.json"

# call 7: recurrence pull, 14 days ending at the incident start (09:30 UTC), one-hour step
curl -sG "$PROM_URL/api/v1/query_range" \
  --data-urlencode 'query=max_over_time(ALERTS{alertname="CatalogApiLatencyHigh", alertstate="firing"}[1h])' \
  --data-urlencode "start=1791538200" --data-urlencode "end=1792747800" --data-urlencode "step=3600" > "$RUN/raw/m-recur-alerts-14d.json"
curl -sG "$PROM_URL/api/v1/query_range" \
  --data-urlencode 'query=sum(increase(http_server_request_duration_seconds_count{service="catalog-api", status=~"5.."}[1h])) / sum(increase(http_server_request_duration_seconds_count{service="catalog-api"}[1h]))' \
  --data-urlencode "start=1791538200" --data-urlencode "end=1792747800" --data-urlencode "step=3600" > "$RUN/raw/m-recur-5xx-14d.json"

Not in this wave: a 14-day latency pull (a histogram_quantile that wide is over the 12h cap and would need a recording rule, which this Prometheus does not list; I will record that as a gap), and any log query.
```

## Wave 1 (start 10:21:48 UTC) - commands, mapped files, key facts

Reused from wave 0: pods and HPA (W0-Q20, W0-Q21). Seven calls, budget now 8 / 20.

| ID | Sub-command | World file | Key facts returned |
|---|---|---|---|
| W1-Q1 | `kubectl ... rollout history deployment/catalog-api` | `k8s-08.txt` | revision 17 (chart catalog-api-2.6.0, image 1.31.1), revision 18 (chart 2.6.1, image 1.31.2) |
| W1-Q1 | `kubectl ... get rs --sort-by=.metadata.creationTimestamp` | `k8s-09.txt` | `catalog-api-58f4d6b7c9` desired 0, age 16d; `catalog-api-6b9d7c5f48` desired/current/ready 6, age 9d |
| W1-Q1 | `helm history catalog-api --kube-context ... -n catalog --max 10` | `helm-01.txt` | rev 21 Wed Oct 7 08:12:40 2026 superseded (2.6.0 / 1.31.1); rev 22 Wed Oct 14 07:58:03 2026 deployed (2.6.1 / 1.31.2). Release name `catalog-api` now verified; Helm timestamps carry no zone in the output, read as UTC (assumption noted in ledger) |
| W1-Q2 | `kubectl ... get events --sort-by=.lastTimestamp` | `k8s-05.txt` | default table with LAST SEEN ages relative to 10:20: 48m HPA SuccessfulRescale "New size: 6; reason: pods metric http_requests_in_flight above target"; 48m ScalingReplicaSet 4 -> 6 on rs 6b9d7c5f48; 48m kx9vn scheduled/pulled (image 1.31.2 already present)/started on ip-192-0-2-87; 47m p6wfj scheduled/started on ip-192-0-2-21. No Warning events, no Unhealthy/BackOff/Killing/Evicted/FailedScheduling. No repeat counts shown, so each is a single occurrence (first = last seen within a minute). Events cover from ~09:20 (1 h TTL), so the onset is inside coverage |
| W1-Q2 | `kubectl ... top pods` | `k8s-07.txt` | CPU 187-224m, memory 349-391Mi per pod; the two new pods are not outliers |
| W1-Q3 | p50 now / offset 7d | `prom-01.json` / `prom-04.json` | previous median 0.110 s, incident 0.109 s, -7d 0.1085 s: unchanged |
| W1-Q3 | p90 now / offset 7d | no INDEX row -> `prom-14.json` x2 | empty matrix: no data, not used (not read as zero) |
| W1-Q3 | p95 now / offset 7d | `prom-02.json` / `prom-05.json` | 09:30 0.398 s -> 09:31 4.967 s in one step; incident (09:31-10:20) median 4.934 s (4.91-4.969); previous median 0.4175 s (0.391-0.457); -7d 0.4255 s (0.383-0.464); 10:20 value 4.932 s vs -7d 0.395 s |
| W1-Q3 | p99 now / offset 7d | `prom-03.json` / `prom-06.json` | incident median 4.991 s (4.982-4.999); previous 0.8915 s; -7d 0.891 s; 10:20 4.989 s |
| W1-Q4 | request rate now / offset 7d | `prom-07.json` / no row -> `prom-14.json` | previous median 412.4 req/s (399.3-422.9); incident 408.9 (398.1-422.1): flat. -7d: empty (gap) |
| W1-Q4 | 5xx share now / offset 7d | `prom-08.json` / no row -> `prom-14.json` | previous median 0.0021; incident 0.0023 (0.0015-0.0027): flat. -7d: empty (gap) |
| W1-Q5 | per-route p95 at 10:20 now / offset 7d | `prom-09.json` / `prom-10.json` | /products/{id} 4.968 s (-7d 0.441); /search 0.381 (0.372); /products/{id}/reviews 0.214 (0.207); /categories 0.083 (0.079); /healthz 0.004 (0.004). Route label values now verified |
| W1-Q5 | per-route call rate at 10:20 now / offset 7d | `prom-11.json` / no row -> `prom-14.json` | /products/{id} 144.2 rps, /search 121.7, /products/{id}/reviews 58.3, /categories 83.9, /healthz 2.0 (sum 410.1 = total rate, consistent). -7d: empty (gap) |
| W1-Q6 | Tempo client-span p95 by server.address, now | `tempo-01.json` | api.pricing.example.com: 0.21 s until the 09:30 sample, 5.0005 s at 09:35 and 4.9965-5.0012 s through 10:20 (incident median 4.999). reviews-api.catalog.svc.cluster.local ~0.057 s; catalog-db.internal.example.com ~0.004 s; catalog-cache.internal.example.com ~0.001 s: all flat. Trace service name `catalog-api` now verified (returned data) |
| W1-Q6 | same, window one week earlier | `tempo-02.json` | pricing 0.200 s median (0.194-0.228) in the -7d incident window; others the same as now |
| W1-Q6 | Tempo client-span rate by server.address | no row for rate -> `tempo-06.json` | `series: []`: no call-rate data (so span count per request cannot be compared) |
| W1-Q7 | ALERTS series, 14 d to 09:30 UTC, 1 h step | no row -> `prom-14.json` | empty matrix: either the alert never fired in the retained range or ALERTS is not retained/queryable; cannot tell |
| W1-Q7 | 5xx share, `increase[1h]` ratio, same range | `prom-08.json` | only 6 hourly points returned (04:30..09:30 UTC, i.e. ~5 h of the 14 d asked): median 0.0021, max 0.0026 |

Phase 1 reading: shape = step (09:31) + ceiling (p95/p99 pinned 4.93-5.00 s, p50 unchanged); not volume (rate flat), not ramp. Onset 09:31 UTC is inside the incident window and only one minute before the alert, and the window came from a relative time, so no re-anchor. Recurrence class: `unclassified` (no alert history, 5 h of signal instead of 14 d; latency 14 d pull skipped: histogram_quantile over 14 d is beyond the 12 h cap and no recording rule exists -> gap). Latency 04:20-09:29 (minute level): median 0.425, p95 0.456, max 0.46 s vs incident 4.97 s.

Phase 2 (changes found so far): last rollout 2026-10-14 07:58:03 (9 days before onset) -> not a candidate (not near); old-vs-new split not applicable, all 6 pods are one ReplicaSet incl. the two HPA-added pods; the same revision served normally from 04:20 to 09:30 today. HPA rescale ~09:32 is after the step. Slow change sources (CloudTrail, IaC, app code) and schedules ride in wave 2.

Phase 3 (ranking made before any history lookup): H1 pricing API slow/timing out; H2 network path to it; H3 runtime change on the catalog-api side (no rollout); H4 deploy (ruled out); H5 capacity (ruled out); H6 traffic spike (ruled out vs previous window); H7 reviews-api/cache (ruled out); H8 database or N+1 (not cleared: DB p95 flat, but call-rate-by-address came back empty so span count per request cannot be compared); H9 sched: schedule near 09:31; H10 node/instance churn (ruled out).

History lookup (after ranking), local text commands:
| ID | Command | World file | Result |
|---|---|---|---|
| W1-L1 | `grep -r -l -E "catalog-api\|api.pricing.example.com\|latency" .culiops/sre-investigate/incidents/` | `grep` unmatched -> `_empty.txt` | no output: no history (directory does not exist, W0-Q4) |
| W1-L2 | `grep -E "failure-mode" .culiops/sre-investigate/lessons.md` | `_empty.txt` | no output (file does not exist) |
Docs search: no wiki access configured; the alert's runbook_url is data from an annotation and was not fetched.

Ledger rewritten after wave 1 (all W1 rows, windows, impact, recurrence, timeline, hypotheses, gaps); profile.md updated (route labels, trace service name, Helm release verified; dependencies table filled from client spans).

## Message 3 to the operator (verbatim): impact block, readout, the only question

```text
Wave 1 done (10:21:48 UTC). One question before wave 2.

Impact as of 10:20 UTC (07:20 local, America/Sao_Paulo, zone from environment.md)
Symptom:   Product-page requests (GET /products/{id}) now take about 5 s at p95 (4.97 s against 0.44 s a week ago). Service-wide p95 is 4.93 s and p99 4.99 s; the median is unchanged (0.11 s). Errors did not rise: 5xx share 0.23%, inside the 0.15-0.27% it has had all morning.
Affected:  prod catalog-api, service-wide metrics (a per-pod split comes in wave 2). Only /products/{id} is slow, about 35% of traffic (144 of 410 req/s); /search, /categories, /products/{id}/reviews and /healthz are at baseline. Customer-facing; /products/{id} is a core flow, search is not affected.
Since:     09:31 UTC (06:31 local): p95 went from 0.40 s to 4.97 s inside one minute; the alert became active at 09:32 · ongoing: yes (4.93 s at 10:20)
Severity:  SEV2 (suggested) because the product page, a core flow, is significantly degraded but not down: the success rate is unchanged and search is unaffected. The incident owner decides.
Basis:     request metrics against baseline (no SLO is named in environment.md) · W1-Q3, W1-Q4, W1-Q5 · Confirmed. The -7d baselines for request rate, 5xx share and per-route rate came back empty, so those comparisons use the previous window only.
Third party in the path: api.pricing.example.com is the slow dependency (below). Whether it is a vendor or an internal team is not in environment.md or the profile, so I cannot give a contact route; the run cannot contact vendors.

What the data says
- Shape: step plus ceiling. p95 and p99 sit at 4.93-5.00 s while p50 is unchanged; the step is at 09:31, a minute before the alert. It is not volume: 410 req/s before and after.
- Where the time goes: client spans from catalog-api to api.pricing.example.com went from p95 0.21 s to 5.00 s and stay at 5.0 s from the 09:35 sample on. The other three dependencies did not move (reviews-api 0.06 s, catalog-db 0.004 s, catalog-cache 0.001 s). A p95 stuck at 5.00 s looks like a 5-second client timeout, but I have not read the code or config, so that is an inference.
- Changes near the onset: no deploy. The last rollout is Helm revision 22 on 2026-10-14 07:58 UTC (chart 2.6.1, image 1.31.2), nine days earlier, and all 6 pods are one ReplicaSet (6b9d7c5f48) with no restarts. The one event at the onset is the HPA scaling 4 to 6 at about 09:32 ("http_requests_in_flight above target"): it comes after the step, so it is a result, not a cause. Pod CPU is 187-224m, memory 349-391Mi, and there are no Warning events.
- Recurrence: unclassified. Prometheus returned nothing for the alert's own history and only about 5 hours of the signal exist there, not 14 days (gap). For scale, the p95 never went above 0.46 s in the 5 hours before 09:30.

Ranked hypotheses, each with the query that would disprove it (no past incidents exist to consult)
1. api.pricing.example.com is slow or timing out on its side. Not refuted by W1-Q6; next I look at slow traces and the log messages.
2. The network path to it broke (NAT, DNS, security group). It is the only external host in the spans, so there is nothing to compare it with; next: NAT metrics, network writes in CloudTrail, connect-versus-read timeouts in the logs.
3. A runtime change on the catalog-api side with no rollout (config, flag, or the pricing client's settings); next: the log messages. Config objects are mostly not visible to this role.
Ruled out so far: a bad deploy (the same revision served normally from 04:20 to 09:30 today), capacity (CPU and memory low, HPA at 6 of 12, p50 unchanged), a traffic spike (rate flat), reviews-api and cache (flat), node churn (no restarts or evictions in the retained events). Still open and not yet testable: the database (its p95 is flat at 4 ms, but the call-rate query for spans returned nothing, so I cannot yet compare queries per request).

The question: you asked what errors it is logging, and I want to run one Logs Insights query for that.
  Log group:  /eks/prod/catalog-api (us-east-1, profile prod-read)
  Window:     last 15 minutes, 10:05-10:20 UTC
  Query:      stats count(*) as n by message | sort n desc | limit 25
  Estimate:   about 1.8 GB scanned (stored bytes over 14-day retention; it assumes even ingest, so it can be off either way). Your threshold is 0.5 GB and the Fast budget is 2 GB, so this uses about 90% of the log budget and is the only log query the run can afford without asking again.
  Narrowing:  filters do not reduce what is scanned, only the window does. A 4-minute window would fit under 0.5 GB but is too thin to rank messages; 30 or 60 minutes would be about 3.6 or 7.2 GB, over the budget.
  Cost:       Logs Insights bills per GB scanned; current prices are at https://aws.amazon.com/cloudwatch/pricing/
Shall I run it for the last 15 minutes?
```

Operator line 2 received here (cue: the Logs Insights approval question above):
2. `OK, run it for the last 15 minutes.`

## Message 4 to the operator (verbatim): wave 2 commands

```text
Thanks. Running exactly the approved query (/eks/prod/catalog-api, 10:05-10:20 UTC, estimate 1.8 GB, one heavy log query) in wave 2, together with the first falsification queries and the slower change sources. Every command, in full:

# call 1: the approved Logs Insights query (start, poll up to about 2 minutes, stop it if it is still running)
date -u +%H:%M:%S
qid=$(aws logs start-query --profile prod-read --region us-east-1 \
  --log-group-names "/eks/prod/catalog-api" --start-time 1792749900 --end-time 1792750800 \
  --query-string 'stats count(*) as n by message | sort n desc | limit 25' \
  --query queryId --output text)
deadline=$(( $(date +%s) + 120 ))
while :; do
  aws logs get-query-results --profile prod-read --region us-east-1 --query-id "$qid" --output json > "$RUN/raw/li-$qid.json"
  case "$(jq -r .status "$RUN/raw/li-$qid.json")" in Complete|Failed|Cancelled|Timeout|Unknown) break ;; esac
  if [ "$(date +%s)" -ge "$deadline" ]; then aws logs stop-query --profile prod-read --region us-east-1 --query-id "$qid"; break; fi
  sleep 5
done
jq '.statistics' "$RUN/raw/li-$qid.json"

# call 2: slow or failing traces of catalog-api, 10:00-10:20 UTC, at most 20
curl -sG "$TEMPO_URL/api/search" \
  --data-urlencode 'q={ resource.service.name = "catalog-api" && (span:status = error || span:duration > 1500ms) }' \
  --data-urlencode "start=1792749600" --data-urlencode "end=1792750800" --data-urlencode "limit=20" \
  > "$RUN/raw/t-slow-samples.json"

# call 3: pod rung, p95 per pod at 10:20 UTC
curl -sG "$PROM_URL/api/v1/query" \
  --data-urlencode 'query=histogram_quantile(0.95, sum by (le, pod) (rate(http_server_request_duration_seconds_bucket{service="catalog-api"}[10m])))' \
  --data-urlencode "time=1792750800" > "$RUN/raw/m-pod-p95.json"

# call 4: timers and config objects that could explain a change with no rollout
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog get cronjobs
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n catalog get configmaps
aws events list-rules --profile prod-read --region us-east-1 \
  --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text

# call 5: network path to the external host: NAT gateways, and EC2 write events in CloudTrail from 2 h before the onset to 15 min after
aws ec2 describe-nat-gateways --profile prod-read --region us-east-1 \
  --query 'NatGateways[].[NatGatewayId, State, VpcId]' --output text
TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 \
  --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false \
  --start-time 2026-10-23T07:31:00Z --end-time 2026-10-23T09:46:00Z \
  --query "Events[?contains(EventSource, 'ec2.amazonaws.com')].[EventTime, EventSource, EventName, EventId]" --output text

# call 6: Helm-values repo history for the last three days (read-only)
gh api "repos/example-org/catalog-deploy/commits?since=2026-10-20T09:31:00Z&until=2026-10-23T10:31:00Z" \
  --jq '.[] | [.sha[0:7], .commit.committer.date, (.commit.message | split("\n")[0])] | @tsv'

Not run: a second log query (the first uses 1.8 of the 2 GB log budget; another would need your approval), and anything that touches the service or the pricing host (curl, DNS lookups from a pod, exec), which this skill forbids.
```

## Wave 2 (start 10:24:40 UTC) - mapped files and key facts

Budget after this wave: 14 / 20 queries; 1.8 / 2 GB logs.

| ID | Command | World file | Key facts |
|---|---|---|---|
| W2-Q1 | `aws logs start-query ... --log-group-names "/eks/prod/catalog-api" --start-time 1792749900 --end-time 1792750800 --query-string 'stats count(*) as n by message \| sort n desc \| limit 25'` | P1 row (stats count(*) by message, no bin, 10:05-10:20) -> `logs-02.json` | queryId `5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9` |
| W2-Q1 | `aws logs get-query-results --query-id 5e6f7a8b-9c0d-4e1f-a2b3-c4d5e6f7a8b9` | P2 row -> `logs-12.json` | status Complete; recordsMatched 26,534; bytesScanned 1.8e9 (1.8 GB; actual / estimate = 1.00); 3 messages: (1) "pricing lookup failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) after 5000ms; serving cached price" 25,914; (2) "pricing cache miss; product shown without price" 611; (3) "reviews-api returned 503; reviews block hidden" 9. NOTE: the result column is named `msg`, not `message` as in my query: the real field is `msg` (my `message` was an unverified guess); lesson candidate. No instruction-like text in any message. |
| W2-Q2 | Tempo search, 10:00-10:20, `span:status = error \|\| span:duration > 1500ms`, limit 20 | `tempo-03.json` | 5 traces (inspected 48,211), all root `GET /products/{id}`, durations 5.004-5.030 s; each holds one client span `GET` to server.address api.pricing.example.com of 5.0003-5.0005 s with status error (99.5-99.9% of the request); trace starts 10:02:24, 10:05:04, 10:08:11, 10:11:47, 10:14:27 (the first starts 2.5 min before my 10:05 intent but inside the 10:00 window sent). Sample is 5, below the 20 needed for span-count claims, so used only for where the time goes in slow requests |
| W2-Q3 | Prometheus p95 by (le, pod) at 10:20 | no INDEX row (grouping by pod differs from the listed queries) -> `prom-14.json` | empty matrix: no per-pod latency (label `pod` on the histogram unverified); pod rung falls back to `kubectl top` (W1-Q2: no outlier) |
| W2-Q4 | `kubectl ... -n catalog get cronjobs` | no row -> `_empty.txt` | no output: no CronJobs listed in catalog |
| W2-Q4 | `kubectl ... -n catalog get configmaps` | no row -> `_empty.txt` | no output: no ConfigMap visible (cannot date a config change) |
| W2-Q4 | `aws events list-rules ... --query ...` | no row -> `_default.txt` | `{}`: no Rules array, no EventBridge schedule returned |
| W2-Q5 | `aws ec2 describe-nat-gateways ...` | no row -> `_default.txt` | `{}`: no NAT gateway returned (egress path unknown; NAT metrics cannot be named) |
| W2-Q5 | `aws cloudtrail lookup-events ... ReadOnly=false 07:31-09:46 UTC ... ec2.amazonaws.com` | no row -> `_default.txt` | `{}`: no Events array. Not read as "nobody changed anything" (empty reply, window not re-run without the filter); recorded as inconclusive |
| W2-Q6 | `gh api repos/example-org/catalog-deploy/commits?since=...` | no row -> `_default.txt` | `{}`: not readable / no commits returned; same gap as W0-Q25. `repos/example-org/catalog-api` not re-queried (already `{}`) |

Readout: the timeout is the app's own configured value (5000 ms in its log line); the slow requests spend essentially all their time in the pricing call; the fallback is a cached price (success, so no 5xx). 25,914 timeout lines / 900 s = 28.8 per s, about 20% of /products/{id}'s 144.2 req/s (Assumed: the message carries no route, but only that route is slow) and 7% of all requests, enough to put p95 and p99 at the ceiling while p90 and p50 stay off it. 611 "product shown without price" lines in 15 min (0.47% of /products/{id} requests if one line is one request). 9 reviews-api 503 lines: no baseline log window (budget), reviews-api client p95 and the reviews route p95 are normal, so it is left as an unexplained minor finding, not discounted as noise (no noise lesson). The Go-style message "Client.Timeout exceeded while awaiting headers" does not say whether the stall was in connect, TLS or waiting for the first byte, so it does not separate H1 (provider slow) from H2 (path).

Hypothesis outcomes after wave 2: H1 Likely (downstream timeout confirmed on the client side; the provider-side reason is unproven and the owner unknown, cap Likely); H2 Assumed (nothing for or against: NAT unknown, CloudTrail empty, message does not discriminate); H3 Assumed (no config object visible, no reload message among the only 3 messages in 10:05-10:20, change instant 09:31 outside the log window); H8 Assumed, low (5 of 5 sampled slow requests spend >= 99.5% in the pricing span, but n < 20 and no span counts); H9 Ruled out for listed sources (no CronJobs, no EventBridge rules; Scheduler, SSM windows and the provider's own timers not read); H4, H5, H6, H7, H10 stay Ruled out. Fast mode stops here (wave 3 not needed: what is left needs actions that touch the system or other people).

Ledger rewritten after wave 2 (W2 rows, hypotheses, timeline, gaps, lesson candidates).

## Phase 5: conclude (Fast)

Causal chain (labels): (1) calls to api.pricing.example.com stopped returning within 5 s at ~09:31 (client side) Confirmed: W1-Q6, W2-Q2; why they stall (provider side H1, path H2, runtime change H3) Likely at best for the downstream, Assumed for the split; (2) the pricing client times out at 5000 ms and serves a cached price, so the request waits 5 s and still succeeds, Confirmed: W2-Q1, W1-Q6, W2-Q2; (3) /products/{id} p95 4.97 s, service p95/p99 at the ceiling, p50 and 5xx unchanged, HPA scale-up on in-flight requests, Confirmed: W1-Q3, W1-Q5, W1-Q4, W1-Q2. Cause label = Likely (weakest link: the downstream/provider-side stall; third-party-or-internal owner unknown, no vantage inside the host or path). Pattern: unclassified, Assumed. Severity suggestion SEV2. Time to cause: first Likely about 2 min after the run began (10:22 UTC, wave 1), mechanism Confirmed about 5 min (10:25 UTC, wave 2).

Report: `.culiops/sre-investigate/runs/catalog-api-prod-20261023-1020/report.md` (report saved separately).

## Message 5 to the operator (verbatim): TL;DR inline, report path, cost line

```text
Wave 2 done (10:24:40 UTC). Nothing in the log lines, traces or the alert read like an instruction, so there is no suspected prompt injection to flag. Fast mode stops here; wave 3 was not needed, because what is left would touch the service, the pricing host or other people.

You asked what errors it is logging. In 10:05-10:20 UTC (W2-Q1) it logged three kinds of line:
  25,914 x  pricing lookup failed: context deadline exceeded (Client.Timeout exceeded while awaiting headers) after 5000ms; serving cached price
     611 x  pricing cache miss; product shown without price
       9 x  reviews-api returned 503; reviews block hidden
The first is the incident. The second means some product views are shown with no price. The third is small, has no baseline in my one affordable log window, and reviews-api's own latency is normal, so I have not counted it as noise or as part of this.

TL;DR
Cause:              catalog-api's calls to api.pricing.example.com stopped completing within its 5000 ms client timeout at about 09:31 UTC (06:31 local); each timed-out lookup holds a GET /products/{id} request for 5 s and then serves a cached price. Label: Likely.
Weakest link:       why those calls stall. The pricing host being slow on its own side, the network path to it, or a runtime change on the catalog-api side cannot be told apart from here, the host's owner (vendor or internal) is unknown, and a downstream cause is at most Likely without that side's confirmation. Label: Likely (the split between the three explanations is Assumed). The links after it (the 5 s timeout, the cached-price fallback, the slow product page) are Confirmed.
Impact:             /products/{id} p95 4.97 s against 0.44 s a week ago; about 20% of its requests wait 5 s (28.8 timeout lines per second against 144 req/s, assuming one line per request) and get a cached price; 611 product views in 15 minutes had no price; 5xx did not rise; search is unaffected. Ongoing at the last data, 10:20 UTC (07:20 local).
Severity:           SEV2 (suggested) because the product page, a core flow, is significantly degraded but not down. The incident owner decides.
Pattern:            unclassified, no alert history and about 5 h of signal for a 14-day request. Label: Assumed.
Recommended action: Get the owner of api.pricing.example.com, or its status page, to say whether it has been slow or unreachable since about 09:31 UTC; the alert's runbook may say who that is (I did not read it). In parallel, have someone with a shell inside the cluster network time DNS, connect, TLS and first byte to that host from a pod and compare with another external destination, to separate the provider from the network path. Do not scale catalog-api out as the fix: the extra pods only hold more 5-second calls. Whether to keep serving cached prices or hide the price block meanwhile is a product decision (cached prices may be stale). Check any mitigation with pre-flight first.
Time to cause:      first Likely about 2 minutes in (10:22 UTC, wave 1); the mechanism Confirmed about 5 minutes in (10:25 UTC, wave 2); the cause as a whole stays Likely.
Similar past incidents: no history yet (no incident files, no lessons).

Ruled out: a bad deploy (same revision fine from 04:20 to 09:30 today, last rollout 9 days earlier), capacity, a traffic spike, reviews-api and cache, node churn, timers visible to this role. Still standing, in rank order: the pricing host (leading), the network path, a runtime change on the catalog-api side, and the database at low rank (not cleared, 5 sampled slow requests show no room for it).

Report: .culiops/sre-investigate/runs/catalog-api-prod-20261023-1020/report.md (local, never committed). Say "go deep" for a full RCA once the incident is over; it keeps this run's ledger and query log.
Open items need your input.

Cost: 14 queries · 1.8 GB of logs · 0 CloudWatch metric requests · no other metered units · about $0.01 in metered charges (1.8 GB of Logs Insights scan; rate from the CloudWatch pricing page, not looked up in this run)
```

## Phase 6: record (proposed diff, shown after the output)

## Message 6 to the operator (verbatim)

```text
Record phase. Nothing is written until you reply; accept, edit or skip each item.

1. NEW incidents/2026-10-23-catalog-api.md (front matter, then a short body)
   id: 2026-10-23-catalog-api-prod-pricing-timeout
   date: 2026-10-23
   service: catalog-api
   env: prod
   siblings: [all]
   window_utc: 2026-10-23T09:31:00Z/ongoing at 2026-10-23T10:25:00Z
   symptoms: [latency, timeouts]
   cause_category: dependency
   cause: catalog-api calls to api.pricing.example.com stop completing within the 5000 ms client timeout; requests wait 5 s then serve a cached price
   deps: [api.pricing.example.com]
   label: Likely
   mode: fast
   time_to_cause_min: 2
   run: runs/catalog-api-prod-20261023-1020
   (cause_category is "dependency" because the owner is unknown; change it to "third-party" if the host is a vendor's. Body: what happened, causal chain with labels, dead ends: deploy, capacity, traffic, reviews-api.)

2. NEW lessons.md (each backed by a query of this run; none is a failure-mode lesson)
   - type: identifier | service: catalog-api | source: cw-logs | statement: In /eks/prod/catalog-api the message field is msg (Insights result column), not message; list the fields with a free get-log-group-fields call before the first stats query | run: catalog-api-prod-20261023-1020 | query_id: W2-Q1 | re-verify: no
   - type: identifier | service: catalog-api | source: prometheus | statement: Latency histogram is http_server_request_duration_seconds with labels service and route; there are no span metrics, so per-dependency latency comes from Tempo TraceQL metrics by span.server.address | run: catalog-api-prod-20261023-1020 | query_id: W1-Q3 | re-verify: no
   - type: identifier | service: catalog-api | source: tempo | statement: Trace service name is catalog-api (resource.service.name) and the peer is the span attribute server.address; tag-values and unfiltered searches returned nothing before a TraceQL metrics query returned data | run: catalog-api-prod-20261023-1020 | query_id: W1-Q6 | re-verify: yes
   - type: process | service: catalog-api | source: prometheus | statement: Offset-7d queries on request rate, 5xx share and route rate, and 14-day pulls of ALERTS and 5xx share, returned empty or about 5 h of points although offset 7d works for the latency histogram; treat as gaps and baseline against the previous window | run: catalog-api-prod-20261023-1020 | query_id: W1-Q4 | re-verify: yes
   - type: process | service: any | source: aws | statement: The IAM simulator reply may not contain the actions asked for (3 of 10 missing, 3 unasked rows returned); count rows against the asked list before writing read-only confirmed | run: catalog-api-prod-20261023-1020 | query_id: W0-Q8 | re-verify: no
   - type: process | service: any | source: tempo | statement: A time-bounded Tempo search can return a trace that started before the requested start (one trace 2.5 min early); check trace start times against the window before counting | run: catalog-api-prod-20261023-1020 | query_id: W2-Q2 | re-verify: no

3. NEW profiles/catalog-api-prod.md = this run's profile.md (log group and msg field, Prometheus metric and labels, Tempo name and server.address, Kubernetes objects and HPA, Helm release, the four dependencies with api.pricing.example.com's owner marked unknown, the stale identifier "message", baseline numbers).

Lessons that would hold beyond this estate (candidates for the skill itself, not for now): discover the Insights field name before the first stats query; check that the IAM simulation reply lists every action asked for before claiming read-only.

Reply with what to accept, edit or skip.
```

No operator reply to Message 6 arrived, so per the skill ("No reply means no write") nothing was written to `incidents/`, `lessons.md` or `profiles/`.

## Operator lines (summary)

1. At the start: `catalog-api latency alert in prod has been firing for about 50 minutes. Can you also pull what errors it is logging? Fast mode.` -> opening request.
2. After Message 3 (the Logs Insights ask, estimated 1.8 GB above the 0.5 GB threshold): `OK, run it for the last 15 minutes.` -> wave 2 ran the approved query unchanged.
No other operator line existed in the script; none was given. Nothing was said about Message 2's offer to record "operator-asserted read-only" or Message 6, so the 3 missing write-check actions stay a gap and nothing was recorded in Phase 6.

## Deviations and judgment calls worth knowing

- The IAM simulation reply did not match the 10 asked actions (3 missing, 3 unasked); treated as a per-action gap per access/standalone.md, no "read-only confirmed", no boxed warning (nothing `allowed`).
- The Insights group column came back as `msg` although the approved query said `message`; the field name was a marked-unverified guess (no free `get-log-group-fields` discovery call was run before the ask, which I should have done in the profile build). Recorded as a lesson candidate and stale identifier.
- Empty `_default`/`prom-14` replies (p90, offset-7d rate/5xx/route rate, ALERTS 14d, per-pod, NAT, EventBridge, CloudTrail, gh) were recorded as gaps, never as "zero" or "nobody changed anything"; H9 was ruled out only for the sources actually listed.
- Fast budget: 14 of 20 queries and 1.8 of 2 GB logs used (queries counted as backend calls; assumption stated to the operator in Message 1).
- Tempo returned one trace that started 2.5 min before the requested start; used only for time share, n=5 stated as below the 20 needed for span-count claims.
- Culibox: `command -v agentbox-env` failed, so nothing about Culibox was said. Secrets: none were present in any output used; the session name of the assumed role (which contains an email-like string) was not recorded anywhere.

## Files written (under `out/`, standing for `.culiops/sre-investigate/`)

- `run-log.md` (this file)
- `runs/catalog-api-prod-20261023-1020/ledger.md`
- `runs/catalog-api-prod-20261023-1020/profile.md`
- `runs/catalog-api-prod-20261023-1020/raw/` : 42 raw pulls (copies of the mapped world outputs under the file names the commands specified; includes `helper/`)
- `report.md`: report saved separately.
- NOT written: `incidents/`, `lessons.md`, `profiles/`, `environment.md` (already existed; nothing to copy)
