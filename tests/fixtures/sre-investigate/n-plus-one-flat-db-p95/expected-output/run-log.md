# Run log: sre-investigate, case-e (orders-api, prod)

Run directory: `orders-api-prod-20261020-1530`
Output root used (simulated): `.culiops/sre-investigate/`, mapped to `out/` (so `runs/orders-api-prod-20261020-1530/ledger.md` is `out/runs/orders-api-prod-20261020-1530/ledger.md`).
Mode: Deep. Operator lines received: 4 (see "Operator lines" at the end).

Conventions in this log: every command is shown as it was printed to the operator; "-> world/<file>" is the canned file the command mapped to (`world/INDEX.md` rules); "returned" lists the key facts. A command whose pattern matched no row got `_default.txt` (JSON API, `{}`) or `_empty.txt` (text command, no output). `date -u` returned nothing every time, so the simulated clock is 15:30 UTC (the newest Prometheus sample) and the Start times in the ledger are indicative. Local time = Australia/Brisbane = UTC+10 (environment.md).

Operator line 1 (opening request, received at the start): "GET /orders on orders-api in prod has been slow since early this afternoon UTC and the p95 alert keeps firing. Deep mode please, I want this one written up properly."

---

## Phase 0: access, mode, intake

Skill files read first: SKILL.md, access/standalone.md, environment.template.md, templates/{ledger,profile,report,incident,lesson}.md, agents/{helper,evidence}.md, playbooks/{metrics,changes,traces}.md (before their first query).

### Step 1 and 2: output root, environment, Culibox (setup commands, not queries)

| # | Command | World file | Returned |
|---|---|---|---|
| S1 | `echo "${CULIOPS_HOME:-}"` | `_empty.txt` | nothing: `CULIOPS_HOME` unset or empty, so the root is `.culiops/sre-investigate/` at the repo root |
| S2 | `git rev-parse --show-toplevel` | `_empty.txt` | nothing printed; the case directory stands for the repo root |
| S3 | `git check-ignore -q .culiops/sre-investigate` | `_empty.txt` | no output, exit 0: the path is ignored by git |
| S4 | `ls .culiops/sre-investigate` | `ls-01.txt` | `environment.md`, `incidents` (no `profiles/`, no `lessons.md`, no `runs/`) |
| S5 | `ls .culiops/sre-investigate/incidents` | `ls-02.txt` | `2026-08-14-orders-api.md`, `2026-09-30-catalog-api.md` (file names only; contents not opened until Phase 3) |
| S6 | `cat .culiops/sre-investigate/environment.md` | `environment.md` | timezone Australia/Brisbane (UTC+10); account prod 111122223333, us-east-1, profile `prod-read`; context `arn:aws:eks:us-east-1:111122223333:cluster/prod`, namespace `orders`; Prometheus `prom-prod`, Loki `loki-prod`, Tempo `tempo-prod` via Grafana `https://grafana.example.com`, token env `GRAFANA_SERVICE_ACCOUNT_TOKEN`; CloudWatch for RDS; repo `example-org/orders-api`, clone `~/src/orders-api` (tags v2.14.0, v2.15.0); budgets: Loki ask above 20 GB, no query totals; severity default; core flows: checkout `POST /orders`, order history `GET /orders` |
| S7 | `command -v agentbox-env` | `_empty.txt` | nothing, exit 1: Culibox absent, so nothing is said about it |

### Step 3 to 6: mode, run directory, problem statement, window

Mode: Deep (the reporter asked for it; the incident is also still ongoing). Run directory `runs/orders-api-prod-20261020-1530` created, ledger copied from the template, `RUN=<run directory>/raw`. Window rule applied: rule 1 (an explicit zone, UTC) with a rough time of day, so the rough time is anchored at 13:00 UTC and the window opens 30 minutes earlier: 12:30 to 15:30 UTC.

**Message 1 to the operator (first message), verbatim:**

```text
sre-investigate, Deep mode (RCA). You asked for Deep and a proper write-up, so I run phases 0 to 3 myself, stop at two checkpoints for you, and use one evidence worker per hypothesis in phase 4. The incident is still ongoing, so the window runs to now.

Output root: .culiops/sre-investigate/ at the repo root (CULIOPS_HOME is not set). It is local and is never committed; `git check-ignore -q .culiops/sre-investigate` exited 0, so git already ignores it. I read .culiops/sre-investigate/environment.md: timezone Australia/Brisbane (UTC+10), AWS profile prod-read (account 111122223333), kube context arn:aws:eks:us-east-1:111122223333:cluster/prod (namespace orders), Prometheus, Loki and Tempo through Grafana, app repo example-org/orders-api with a local clone at ~/src/orders-api. There is no stored profile or lessons file for orders-api yet, so this is a first run for the service and I will build a profile.

Window: you said "early this afternoon UTC". The zone is explicit, so I use it as given. It is a rough time, so I anchor it at 13:00 UTC on 2026-10-20 and open the window 30 minutes earlier: 12:30 to 15:30 UTC (22:30 on 20 Oct to 01:30 on 21 Oct, Australia/Brisbane). `date -u` printed nothing here, so "now" is 15:30 UTC, the newest Prometheus sample. Run directory: runs/orders-api-prod-20261020-1530.
```

Ledger stage A written (Problem, Access placeholders, Windows, Query log, Gaps).

### Wave 0 (printed in full, then run)

```bash
date -u +%H:%M:%S
id=$(aws sts get-caller-identity --profile prod-read --output json); echo "$id"
arn=$(echo "$id" | jq -r .Arn); role=${arn#*:assumed-role/}; role=${role%%/*}
role_arn=$(aws iam get-role --profile prod-read --role-name "$role" --query Role.Arn --output text)
aws iam simulate-principal-policy --profile prod-read \
  --policy-source-arn "$role_arn" \
  --action-names s3:PutObject s3:DeleteObject ec2:TerminateInstances \
    ec2:AuthorizeSecurityGroupIngress ecs:UpdateService iam:PutRolePolicy \
    iam:CreateAccessKey rds:ModifyDBInstance lambda:UpdateFunctionCode \
    cloudformation:DeleteStack \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text
kubectl auth whoami --context arn:aws:eks:us-east-1:111122223333:cluster/prod
kubectl config current-context
kubectl auth can-i --list --context arn:aws:eks:us-east-1:111122223333:cluster/prod --namespace orders
[ -n "${GRAFANA_SERVICE_ACCOUNT_TOKEN:+x}" ] && echo "GRAFANA_SERVICE_ACCOUNT_TOKEN: set" || echo "GRAFANA_SERVICE_ACCOUNT_TOKEN: unset"
curl -sG "https://grafana.example.com/api/annotations" \
  -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode "type=alert" --data-urlencode "from=1789918200000" \
  --data-urlencode "to=1792510200000" --data-urlencode "limit=100"
```

(The log probe of wave 0 waits for the profile build, as the skill says for a first run on a label-based log backend.)

| ID | Command | World file | Key facts returned |
|---|---|---|---|
| (clock) | `date -u +%H:%M:%S` | `_empty.txt` | nothing; simulated clock 15:30 |
| W0-Q1 | `aws sts get-caller-identity --profile prod-read` | `sts-01.json` | Account 111122223333 (equals environment.md); `assumed-role/AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b/<session>` (session name never recorded) |
| W0-Q2 | `aws iam get-role ...` | `iam-01.json` | role ARN with path `/aws-reserved/sso.amazonaws.com/` |
| W0-Q3 | `aws iam simulate-principal-policy ...` | `iam-02.json` | 10 rows, all `implicitDeny`, but the actions are not the fixed list: present = s3:PutObject, s3:DeleteObject, ec2:TerminateInstances, ecs:UpdateService, iam:PutRolePolicy, rds:ModifyDBInstance, lambda:UpdateFunctionCode (7); missing = ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey, cloudformation:DeleteStack (3); foreign = ec2:ModifyInstanceAttribute, ecs:StopTask, iam:AttachRolePolicy (3) |
| W0-Q4 | `kubectl auth whoami --context ...` | `k8s-02.txt` | same SSO ReadOnly role, groups `eks-readonly`, `system:authenticated` |
| W0-Q5 | `kubectl config current-context` | `k8s-01.txt` | `arn:aws:eks:us-east-1:111122223333:cluster/prod` (the environment.md context) |
| W0-Q6 | `kubectl auth can-i --list ... --namespace orders` | `k8s-03.txt` | `*.*` [get list watch]; `create` only on selfsubjectreviews, selfsubjectaccessreviews, selfsubjectrulesreviews (excluded by the rule); non-resource URLs get only. No write verbs |
| W0-Q7 | token presence | `env-01.txt` | `x`: `GRAFANA_SERVICE_ACCOUNT_TOKEN` is set |
| W0-Q8 | Grafana annotations `type=alert`, 30 days | `_default.txt` | `{}`: no alert history |

Ledger Access table and Gaps updated (stage A) before anything else used the results.

**Message 2 (after wave 0), verbatim:**

```text
Wave 0 done.

Write checks:
- prod-read (account 111122223333, role AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b): Write check, prod-read: none of the actions that came back is allowed, but the check is incomplete. The simulation returned rows for 7 of the 10 fixed write actions (all implicitDeny) and no row for ec2:AuthorizeSecurityGroupIngress, iam:CreateAccessKey or cloudformation:DeleteStack. Write capability unknown (gap) for those three, so I am not calling these credentials read-only. No boxed warning, because nothing came back allowed.
- Kubernetes context prod, namespace orders: no write verbs in orders (the only creates are on the three self-review APIs, which do not count). Side note: the grant is get/list/watch on all resources, which includes Secrets. This run never reads Secret objects.
- GRAFANA_SERVICE_ACCOUNT_TOKEN is set.

Gaps so far: (1) no alert history: you did not name the alert, there is no ALERTS series in Prometheus, and the Grafana annotations API returned nothing for the last 30 days; (2) the AWS write-check gap above. The log-size probe runs after the profile build.
```

---

## Build profile (first run for orders-api prod)

No stored profile, so a helper was dispatched (`TASK: PROFILE`, cheapest tier, identifier lessons: none, RUN `raw/helper`). No identifier-free change query was started alongside it: environment.md lists no IaC repo, and the cluster listings are part of the helper's checklist.

### [helper TASK: PROFILE, cheapest tier] wave 1 (discovery)

```bash
LOKI=https://grafana.example.com/api/datasources/proxy/uid/loki-prod
TEMPO=https://grafana.example.com/api/datasources/proxy/uid/tempo-prod
PROM=https://grafana.example.com/api/datasources/proxy/uid/prom-prod
CTX=arn:aws:eks:us-east-1:111122223333:cluster/prod
curl -sG "$LOKI/loki/api/v1/labels" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "$LOKI/loki/api/v1/label/app/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "$LOKI/loki/api/v1/label/namespace/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "$LOKI/loki/api/v1/label/container/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "$TEMPO/api/v2/search/tags" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "$TEMPO/api/v2/search/tag/resource.service.name/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792506600" --data-urlencode "end=1792510200"
curl -sG "$PROM/api/v1/label/__name__/values" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN"
curl -sG "https://grafana.example.com/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "query=orders" --data-urlencode "type=dash-db"
kubectl --context "$CTX" -n orders get pods
kubectl --context "$CTX" -n orders get deploy,svc,ingress,hpa
aws rds describe-db-instances --profile prod-read --region us-east-1 --query "DBInstances[?contains(DBInstanceIdentifier, 'orders')].{id: DBInstanceIdentifier, class: DBInstanceClass, engine: Engine, version: EngineVersion, status: DBInstanceStatus, multiAz: MultiAZ}" --output json
git -C ~/src/orders-api tag
gh api repos/example-org/orders-api --jq .default_branch
ls .culiops/service-discovery
```

| ID | Command | World file | Key facts returned |
|---|---|---|---|
| PB-Q1 | Loki `/labels` | `loki-01.json` | `app`, `container`, `namespace`, `stream` |
| PB-Q2 | Loki `label/app/values` | `loki-02.json` | catalog-api, notify-worker, orders, orders-reconcile, payments-worker (no `orders-api`) |
| PB-Q3 | Loki `label/namespace/values` | `loki-03.json` | catalog, notify, orders, payments |
| PB-Q4 | Loki `label/container/values` | `loki-04.json` | api, worker |
| PB-Q5 | Tempo `/api/v2/search/tags` | `tempo-06.json` | resource: k8s.namespace.name, k8s.pod.name, service.name, service.version; span: db.statement, db.system, http.request.method, http.response.status_code, http.route, server.address |
| PB-Q6 | Tempo tag values `resource.service.name` | `_default.txt` | `{}` |
| PB-Q7 | Prometheus `label/__name__/values` | `prom-09.json` | db_client_connections_{pending_requests,usage}, db_client_operation_duration_seconds_{bucket,count,sum}, container_cpu_usage_seconds_total, http_server_request_duration_seconds_{bucket,count,sum}, kube_deployment_status_replicas, up. No `ALERTS`, no cfs throttling, no resource-limit series |
| PB-Q8 | Grafana dashboard search `orders` | `_default.txt` | `{}`: none found |
| PB-Q9 | `kubectl get pods -n orders` | `k8s-04.txt` | 3 pods `orders-api-7c9b6d8f5d-{4kq2m,9vx7t,tz5wp}`, 1/1 Running, 0 restarts, age 145m / 144m / 144m |
| PB-Q10 | `kubectl get deploy,svc,ingress,hpa -n orders` | `_empty.txt` | no output |
| PB-Q11 | `aws rds describe-db-instances` (filter `orders`) | `rds-01.json` | `orders-db`, db.r6g.2xlarge, postgres 16.6, available, Multi-AZ, Performance Insights off |
| PB-Q12 | `git -C ~/src/orders-api tag` | `git-03.txt` | v2.12.0, v2.13.0, v2.13.1, v2.14.0, v2.15.0 |
| PB-Q13 | `gh api repos/example-org/orders-api --jq .default_branch` | `_default.txt` | `{}`: default branch unknown |
| PB-Q14 | `ls .culiops/service-discovery` | (no row) | `No such file or directory`, exit 1: no service-discovery catalog |

### [helper TASK: PROFILE, cheapest tier] wave 2 (verification)

```bash
curl -sG "$LOKI/loki/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query={app="orders"}' --data-urlencode "start=1792509300" --data-urlencode "end=1792510200" --data-urlencode "limit=8" --data-urlencode "direction=backward"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=rate(http_server_request_duration_seconds_count{service="orders-api"}[5m])' --data-urlencode "start=1792490400" --data-urlencode "end=1792510200" --data-urlencode "step=120"
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" }' --data-urlencode "start=1792506600" --data-urlencode "end=1792510200" --data-urlencode "limit=5"
```

| ID | Command | World file | Key facts returned |
|---|---|---|---|
| PB-Q15 | Loki `{app="orders"}`, 8 lines | `loki-05.json` | one stream `{app="orders", namespace="orders", container="api", stream="stdout"}`, 8 `request completed` lines for `GET /orders` (status 200, 286 to 751 ms, page_size=50) at 15:18 to 15:19 UTC; no pod label; 48.2 MB processed |
| PB-Q16 | Prometheus request-count rate | `prom-07.json` | one series `{service="orders-api", route="/orders", method="GET"}`, 166 points (10:00 to 15:30 at 120 s), 52 to 61 req/s, mean 56.5 before 13:08 and 56.1 after: the label `service="orders-api"` returns data |
| PB-Q17 | Tempo bare search `service.name = orders-api` | `tempo-07.json` | `traces: []`: zero traces, so the trace service name stays `(unverified)` for the helper |

Helper returned the profile (marks: Prometheus `service="orders-api"` verified; Tempo `orders-api` unverified; Loki `app="orders"` unverified because its value differs from the service name and the stream has no pod label, so no tie; the lines look like the service's traffic, which is a lead, not a tie). Helper cost: 17 list/read calls in 2 waves. Main session re-applied Constraint 14's tie rule: Loki stays `(unverified)`.

### Wave 0 log probe (after the profile build, on discovered label `app="orders"`)

```bash
curl -sG "$LOKI/loki/api/v1/index/stats" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query={app="orders"}' --data-urlencode "start=1792509300" --data-urlencode "end=1792510200"
```

| W0-Q9 | Loki index stats, `app="orders"`, 15 minutes | `_default.txt` | `{}`: no estimate. Treated as metered; the measured size of the helper sample (48.2 MB for 8 lines) is far under the 20 GB ask limit, and no further log query is planned |

Run profile written to `runs/orders-api-prod-20261020-1530/profile.md` (final version in the out directory; updated after wave 1 when W1-Q17 verified the Tempo name).

**Message 3 (profile shown, run continues), verbatim:**

```text
Profile for orders-api prod (built by a helper, shown for correction; the run continues):
- Compute: namespace orders, Deployment orders-api, 3 pods on ReplicaSet orders-api-7c9b6d8f5d, Helm release orders-api (chart orders-api-4.2.0). No HPA, Service or Ingress came back from the listing (absence not proven).
- Metrics (Prometheus prom-prod): service="orders-api", metrics http_server_request_duration_seconds_* (labels method, route; no status label), db_client_operation_duration_seconds_*, db_client_connections_*, container_cpu_usage_seconds_total. No ALERTS series.
- Traces (Tempo tempo-prod): service name orders-api (not yet verified: a bare search returned nothing).
- Logs (Loki loki-prod): app="orders", namespace="orders", container="api" (unverified: the label value differs from the service name and the stream has no pod label, so I treat those lines as a lead only; app="orders-reconcile" is a different workload).
- Data store: RDS orders-db (PostgreSQL 16.6, db.r6g.2xlarge, Multi-AZ).
- Code: example-org/orders-api, image tag vX.Y.Z = git tag vX.Y.Z (v2.14.0 and v2.15.0 exist locally); default branch unknown.
- No dashboards, error tracker, IaC repo, tickets or service-discovery catalog found. Core flows: GET /orders and POST /orders.
Tell me if any of this is wrong.
```

---

## Phase 1: scope, impact and severity

### Wave 1 (printed in full, then run; 21 queries in 8 shell calls, above ten because the fixed legs need it)

Windows used by every query: incident 12:30 to 15:30 UTC (epoch 1792499400 to 1792510200), previous 09:30 to 12:30 (1792488600 to 1792499400; Prometheus holds data from 10:00 only), -7d 2026-10-13 12:30 to 15:30 (by `offset 7d`). Step 120 s.

```bash
# shell call 1: change events (first call of the wave begins with the clock)
date -u +%H:%M:%S
CTX=arn:aws:eks:us-east-1:111122223333:cluster/prod
kubectl --context "$CTX" -n orders get events --sort-by=.lastTimestamp
kubectl --context "$CTX" -n orders get rs --sort-by=.metadata.creationTimestamp -o custom-columns='NAME:.metadata.name,REVISION:.metadata.annotations.deployment\.kubernetes\.io/revision,CREATED:.metadata.creationTimestamp,DESIRED:.spec.replicas,READY:.status.readyReplicas'
kubectl --context "$CTX" -n orders rollout history deployment/orders-api
helm history orders-api --kube-context "$CTX" -n orders --max 10

# shell call 2: per-endpoint p95, three windows (instants)
PROM=https://grafana.example.com/api/datasources/proxy/uid/prom-prod
Q='histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[5m])))'
QO='histogram_quantile(0.95, sum by (le, method, route) (rate(http_server_request_duration_seconds_bucket{service="orders-api"}[5m] offset 7d)))'
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "query=$Q"  --data-urlencode "time=1792510200"
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "query=$Q"  --data-urlencode "time=1792499400"
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "query=$QO" --data-urlencode "time=1792510200"

# shell call 3: GET /orders p50 and p95, incident plus previous in one range, and the same range 7 days back
for q in 0.95 0.5; do
  curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
    --data-urlencode "query=histogram_quantile($q, sum by (le) (rate(http_server_request_duration_seconds_bucket{service=\"orders-api\", route=\"/orders\", method=\"GET\"}[5m])))" \
    --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
  curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
    --data-urlencode "query=histogram_quantile($q, sum by (le) (rate(http_server_request_duration_seconds_bucket{service=\"orders-api\", route=\"/orders\", method=\"GET\"}[5m] offset 7d)))" \
    --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
done

# shell call 4: p90 and p99 of the alerting signal
for q in 0.90 0.99; do
  curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
    --data-urlencode "query=histogram_quantile($q, sum by (le) (rate(http_server_request_duration_seconds_bucket{service=\"orders-api\", route=\"/orders\", method=\"GET\"}[5m])))" \
    --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
done

# shell call 5: call rate of the endpoint against the -7d window, and DB operations (the incident-window request rate is PB-Q16, reused)
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=rate(http_server_request_duration_seconds_count{service="orders-api", route="/orders"}[5m] offset 7d)' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (db_system) (rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m]))' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (db_system) (rate(db_client_operation_duration_seconds_count{service="orders-api"}[5m] offset 7d))' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"

# shell call 6: saturation (CPU per pod, DB pool)
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="orders", pod=~"orders-api-.*"}[5m]))' --data-urlencode "start=1792499400" --data-urlencode "end=1792510200" --data-urlencode "step=600"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query={__name__=~"db_client_connections_(usage|pending_requests)", service="orders-api"}' --data-urlencode "start=1792488600" --data-urlencode "end=1792510200" --data-urlencode "step=120"

# shell call 7: slow-downstream aggregation (Tempo TraceQL metrics, DB spans) and the recurrence pull (14 days ending at the incident start, hourly)
TEMPO=https://grafana.example.com/api/datasources/proxy/uid/tempo-prod
curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span.db.system =~ ".+" } | quantile_over_time(duration, .95)' --data-urlencode "start=1792490400" --data-urlencode "end=1792510200" --data-urlencode "step=15m"
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (db_system) (increase(db_client_operation_duration_seconds_count{service="orders-api"}[1h]))' --data-urlencode "start=1791289800" --data-urlencode "end=1792499400" --data-urlencode "step=3600"

# shell call 8: deploy markers
curl -sG "https://grafana.example.com/api/annotations" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "from=1792499400000" --data-urlencode "to=1792510200000" --data-urlencode "limit=100"
```

Notes on the plan: the volume check for the incident window reuses PB-Q16 (`reused PB-Q16`). The per-pod latency split was not pulled (replicas share one ReplicaSet; per-pod CPU is the sibling comparison); recorded as a gap. Errors are not computable (no status label).

| ID | Command (short) | World file | Key facts returned |
|---|---|---|---|
| W1-Q1 | `kubectl get events -n orders` | `k8s-05.txt` | "No resources found in orders namespace." (events older than 1h TTL gone) |
| W1-Q2 | `kubectl get rs -n orders` | `k8s-06.txt` | `orders-api-5f8d9c7b6a` desired 0, age 13d; `orders-api-7c9b6d8f5d` desired/current/ready 3, age 145m (table shows AGE only) |
| W1-Q3 | `kubectl rollout history deployment/orders-api` | `k8s-07.txt` | rev 23 helm upgrade (chart orders-api-4.2.0, image v2.14.0); rev 24 helm upgrade (chart orders-api-4.2.0, image v2.15.0) |
| W1-Q4 | `helm history orders-api` | `helm-01.txt` | rev 23 Wed Oct 7 09:40:12 2026 superseded v2.14.0; rev 24 Tue Oct 20 13:04:50 2026 deployed v2.15.0; no zone printed |
| W1-Q5 | per-route p95 at 15:30 | `prom-03.json` | GET /orders 0.712; GET /orders/{id} 0.064; POST /orders 0.142; PATCH /orders/{id} 0.088; /healthz 0.003 |
| W1-Q6 | per-route p95 at 12:30 | `prom-04.json` | 0.181; 0.061; 0.139; 0.091; 0.003 |
| W1-Q7 | per-route p95, offset 7d | `prom-14.json` | 0.181; 0.061; 0.139; 0.091; 0.003 |
| W1-Q8 | p95 `GET /orders` range | `prom-01.json` | 166 points 10:00 to 15:30; 94 points to 13:06 within 0.160 to 0.200; 72 points from 13:08 within 0.661 to 0.755; 13:06 = 0.163, 13:08 = 0.716 |
| W1-Q9 | p50 `GET /orders` range | `prom-02.json` | 0.080 to 0.100 to 13:06; 0.281 to 0.339 from 13:08 |
| W1-Q10 | p95 range, offset 7d | `prom-11.json` | 166 points, 0.160 to 0.200 throughout (2026-10-13) |
| W1-Q11 | p50 range, offset 7d | `prom-12.json` | 166 points, 0.080 to 0.100 throughout |
| W1-Q12 | p90 range | `prom-10.json` | empty matrix (gap) |
| W1-Q13 | p99 range | `prom-10.json` | empty matrix (gap) |
| W1-Q14 | request rate offset 7d | `prom-07.json` | the identical 166 points as PB-Q16, same timestamps and values; an offset query cannot be identical to the unshifted one, so it is unusable (gap) |
| W1-Q15 | DB operations rate | `prom-05.json` | 380.1/s mean to 13:06 (361 to 401); 3952/s mean from 13:10 (3821 to 4089); 13:06 = 365.5, 13:08 = 4031.1 (10.4 times) |
| W1-Q16 | DB operations rate offset 7d | `prom-13.json` | 355 to 404/s throughout (mean 379), 2026-10-13 |
| W1-Q17 | Tempo TraceQL metrics, DB span p95 | `tempo-01.json` | series `span.db.system=postgresql`: 3.9 to 4.4 ms at all 23 steps, before and after 13:08 (also verifies the Tempo service name) |
| W1-Q18 | CPU per pod | `prom-08.json` | 3 pods, first point 13:08, 0.52 to 0.64 cores, means 0.583 / 0.580 / 0.594 |
| W1-Q19 | pool used and pending | `prom-06.json` | `used` 14 to 19 before, 17 to 24 after; `pending_requests` 0 in all 166 points |
| W1-Q20 | recurrence pull, DB operations hourly | `prom-05.json` | only the 10:00 to 12:30 part of today overlaps: 1.37M per hour at 10:00, 11:00, 12:00; nothing before 10:00 |
| W1-Q21 | Grafana annotations (deploy markers) | `_default.txt` | `{}` |

Ledger rows for W1 written to `ledger.md` (query log, timeline entries, gaps, windows, recurrence) before the results were used below.

### Phase 1 reading

- Siblings: the sibling set is the 3 replicas of one ReplicaSet; per-pod CPU is the same (0.58 to 0.59 cores) so no single pod stands out; all members moved together because they all run the new revision. Other routes of the same service are flat.
- Golden signals: latency step at 13:08 (p95 3.9 times, p50 3.4 times); traffic flat (PB-Q16); errors not computable; saturation: pool pending 0, pods steady.
- Shape: step. Not a ceiling (p50 moved). Not volume (call rate 56.5 to 56.1 req/s, but DB operations 10.4 times). A step in DB calls with flat request count points at per-request DB work, so the next waves include the span count per request (wave 2).
- Recurrence: class `unclassified` (no alarm history; 3 of 336 hourly points; latency recurrence not pullable). The same clock window seven days earlier was clean (W1-Q10, W1-Q11, W1-Q16).
- Known noise: none known.
- Impact source: no SLO named, so request metrics against the baseline.

**Message 4 (impact block, shown before Phase 2), verbatim:**

```text
Impact as of 15:30 UTC (01:30 on 21 Oct local, Australia/Brisbane)
Symptom:   GET /orders p95 0.181 s -> 0.712 s (3.9x), p50 about 0.09 s -> 0.31 s; request rate unchanged at about 56/s. No errors measured (the HTTP histogram has no status label).
Affected:  prod orders-api, all 3 replicas; only GET /orders (other routes flat); customer-facing, core flow "order history".
Since:     13:08 UTC (23:08 local; last clean sample 13:06) · ongoing: yes
Severity:  SEV2 (suggested) because a core flow is significantly degraded (about 4x slower at p95) with no failures measured.
Basis:     request metrics against baseline (previous window and -7d) · W1-Q5..Q11, PB-Q16 · Confirmed for latency; error impact Assumed
Third party in the path: none
```

---

## Phase 2: change correlation

Recurrence first: class `unclassified`, shape `step` (no scheduled pattern can be read; nothing in the data repeats). Schedules are still listed, before looking for a person.

### Wave 2 (printed in full, then run; 12 queries in 5 shell calls)

```bash
# shell call 1
date -u +%H:%M:%S
git -C ~/src/orders-api log --oneline v2.14.0..v2.15.0
git -C ~/src/orders-api diff v2.14.0..v2.15.0
git -C ~/src/orders-api rev-parse --verify --end-of-options 'v2.15.0^{commit}'

# shell call 2: schedules, platform events, writes (onset taken as the rollout, about 13:05; window = onset-2h to onset+15m)
CTX=arn:aws:eks:us-east-1:111122223333:cluster/prod
kubectl --context "$CTX" get cronjobs -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,SCHEDULE:.spec.schedule,TZ:.spec.timeZone,SUSPEND:.spec.suspend,LAST:.status.lastScheduleTime'
aws events list-rules --profile prod-read --region us-east-1 --query 'Rules[?ScheduleExpression].[Name, State, ScheduleExpression]' --output text
aws scheduler list-schedules --profile prod-read --region us-east-1 --query 'Schedules[].[GroupName, Name, State]' --output text
TZ=UTC aws cloudtrail lookup-events --profile prod-read --region us-east-1 --lookup-attributes AttributeKey=ReadOnly,AttributeValue=false --start-time 2026-10-20T11:05:00Z --end-time 2026-10-20T13:20:00Z --query "Events[].[EventTime,EventSource,EventName]" --output text
aws rds describe-events --profile prod-read --region us-east-1 --source-type db-instance --source-identifier orders-db --start-time 2026-10-20T11:05:00Z --end-time 2026-10-20T13:20:00Z --query 'Events[].[Date,Message]' --output text

# shell call 3: old against new, span counts per request (24 to 30 traces per window; the first window is the new revision, the second the old one)
TEMPO=https://grafana.example.com/api/datasources/proxy/uid/tempo-prod
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span:kind = server && span:name = "GET /orders" } >> { span:kind = client }' --data-urlencode "start=1792506600" --data-urlencode "end=1792510200" --data-urlencode "limit=30"
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span:kind = server && span:name = "GET /orders" } >> { span:kind = client }' --data-urlencode "start=1792494000" --data-urlencode "end=1792497600" --data-urlencode "limit=30"

# shell call 4: one representative trace per window, by ID from those searches (window padded by an hour each side)
curl -sG "$TEMPO/api/v2/traces/e3ea7a3906419b466a28541306cc5ee1" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792503000" --data-urlencode "end=1792513800"
curl -sG "$TEMPO/api/v2/traces/65345f5f8176033524bc88af3bd43f6f" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode "start=1792490400" --data-urlencode "end=1792501200"
```

| ID | Command (short) | World file | Key facts returned |
|---|---|---|---|
| (clock) | `date -u` | `_empty.txt` | nothing |
| W2-Q1 | `git log --oneline v2.14.0..v2.15.0` | `git-01.txt` | a4c1e9b 2026-10-19 "orders: load items per order in list handler (#2211)"; 7be20d4 2026-10-19 "orders: return shipment ETA on order detail (#2208)"; 3f9d6a1 2026-10-16 "deps: bump structlog to 25.4.0 (#2203)" |
| W2-Q2 | `git diff v2.14.0..v2.15.0` | `git-02.txt` | `list_orders.py`: `repo.list_orders_with_items(customer_id, limit=limit)` replaced by `repo.list_orders(...)` plus `for order in orders: order.items = repo.list_items(order.id)`; `order_detail.py`: adds `shipment_eta`; `pyproject.toml`: structlog 25.3.0 to 25.4.0 |
| W2-Q12 | `git rev-parse --verify v2.15.0^{commit}` | `_empty.txt` | nothing printed: SHA not resolved (gap); tag names used as refs |
| W2-Q3 | `kubectl get cronjobs -A` | `_empty.txt` | no output |
| W2-Q4 | `aws events list-rules` | `_default.txt` | `{}` |
| W2-Q5 | `aws scheduler list-schedules` | `_default.txt` | `{}` |
| W2-Q6 | `aws cloudtrail lookup-events` (writes) | `_default.txt` | `{}` |
| W2-Q7 | `aws rds describe-events` | `_default.txt` | `{}` |
| W2-Q8 | Tempo structural search, 14:30 to 15:30 | `tempo-02.json` | 24 traces, root `GET /orders`; descendant spans (`matched`) per trace sorted: 9, 14, 18, 22, 27, 31, 33, 36, 38, 39, 40, 41, 41, 42, 44, 47, 49, 51, 52 x6; p50 41, p95 52, max 52; trace duration p50 342 ms, p95 422 ms; span names `SELECT orders`, `SELECT order_items` |
| W2-Q9 | Tempo structural search, 11:00 to 12:00 | `tempo-03.json` | 24 traces; descendants per trace: 2, 2, 3 x18, 4 x4; p50 3, max 4; duration p50 110 ms, p95 165 ms |
| W2-Q10 | Tempo trace `e3ea7a39...` (14:48) | `tempo-09.json` | 152 ms: `GET auth-api /verify` 3.4 ms, `SELECT orders` 3.05 ms, then 12 serial `SELECT order_items` of 2.9 to 4.5 ms; status 200 |
| W2-Q11 | Tempo trace `65345f5f...` (11:00) | `tempo-10.json` | 109 ms: `GET auth-api /verify` 3.8 ms and one `SELECT orders JOIN order_items` 3.05 ms; status 200 |

Ledger rows for wave 2 written (stage B) before the results below were used.

### Change list (every change near the onset, with its UTC time and source)

- 13:04:50 (zone not printed by Helm; cross-checked) Helm revision 24, chart orders-api-4.2.0 (unchanged from revision 23), app v2.15.0, "Upgrade complete". New ReplicaSet orders-api-7c9b6d8f5d, pods about 145 minutes old at about 15:30, old ReplicaSet at 0 (W1-Q2, W1-Q3, W1-Q4).
- Release v2.15.0 contains three commits (W2-Q1, W2-Q2): a4c1e9b touches `orders_api/handlers/list_orders.py`, the handler of the failing route: **on the failing path**. 7be20d4 touches `order_detail.py` (`GET /orders/{id}`, which stayed at 0.061 to 0.064 s: not on the failing path). 3f9d6a1 bumps structlog on every route, and the other routes stayed flat (W1-Q5..Q7): no sign it matters.
- Schedules (CronJobs, EventBridge rules, Scheduler): nothing returned (W2-Q3..Q5; a `{}` is not proof of absence). Scaling: no HPA listed; replicas desired = ready = 3. Platform: no RDS events (W2-Q7), no deploy markers (W1-Q21), no CloudTrail writes returned (W2-Q6), Kubernetes events expired (W1-Q1). IaC history: no IaC repo is configured (gap). Direct dependencies: orders-db has no events; auth-api (found in traces) has no deploy record this role can read.
- Old against new (Phase 2 step 3, before any label): **new revision (v2.15.0, 13:08 to 15:30): 72 of 72 p95 samples at 0.661 s or more, 24 of 24 sampled traces with 9 to 52 descendant spans (p50 41). Old revision (v2.14.0, the last window before replacement, 10:00 to 13:06): 0 of 94 samples above 0.200 s, 24 of 24 sampled traces with 2 to 4 descendants (p50 3). Earlier occurrences while only the old revision ran: none in the covered data (0 of 166 samples above 0.200 s on 2026-10-13).** The onset is later than the rollout start, not earlier. So the deploy is kept in as a candidate; no label yet (Deep mode: labels come from the worker verdicts).
- Run profile: Tempo service name `orders-api` now marked verified (W1-Q17 and W2-Q8 returned data); Loki `app="orders"` stays unverified; auth-api added as a downstream (seen in W2-Q10, W2-Q11).

### Deep checkpoint 1

**Message 5 (checkpoint 1), verbatim:**

```text
Checkpoint 1 (phases 0 to 2 are done; nothing has been labelled yet).

Windows (UTC, local = Australia/Brisbane, UTC+10)
- Incident 2026-10-20 12:30 to 15:30 (22:30 to 01:30 local), ongoing. True onset 13:08 UTC (23:08 local): last clean sample 13:06, first elevated 13:08. No re-anchor needed (8 minutes from your "early afternoon").
- Previous 09:30 to 12:30 (Prometheus only has data from 10:00); -7d 2026-10-13 12:30 to 15:30.

Blast radius: only GET /orders (p95 0.181 -> 0.712 s, p50 0.09 -> 0.31 s). POST /orders, GET /orders/{id}, PATCH /orders/{id} and /healthz are flat. All 3 replicas move together (one ReplicaSet). Request rate is unchanged (about 56/s) but database operations jumped from about 380/s to about 3,950/s at the same minute (10.4x), with per-call database latency flat at about 4 ms and the pool not waiting.

Recurrence: unclassified, shape step. There is no alert history (alert name not given, no ALERTS series) and Prometheus returned only 3 of 336 hourly points for the 14-day pull. The same clock window a week earlier was clean.

Changes near the onset
- 13:04:50 Helm revision 24: orders-api v2.14.0 -> v2.15.0 (same chart 4.2.0), all 3 pods replaced (about 145 minutes old at 15:30). Helm prints no zone, so I cross-checked it against pod age and the 13:08 metric step: they agree to about 3 minutes.
- v2.15.0 holds 3 commits. a4c1e9b (#2211) rewrites the GET /orders list handler to call a per-order items query and is on the failing path. #2208 (order detail) and the structlog bump (#2203) are not.
- No schedules, CloudTrail writes, RDS events, HPA or deploy markers came back; Kubernetes events had expired. There is no IaC repo in environment.md.
- Old against new: new revision 72/72 p95 samples above 0.66 s and 24/24 sampled traces with 9 to 52 downstream spans; old revision 0/94 samples above 0.20 s and 24/24 traces with 2 to 4 spans.

Run profile: as shown earlier, plus Tempo service name orders-api now verified and auth-api added as a downstream.

Two questions: (1) Is the window right? (2) Did anything change that I cannot see, such as a manual action, a configuration change outside the chart, a vendor issue, or an auth-api change?
```

**Operator line 2 (received at checkpoint 1):** "Agreed, go on."

---

## Phase 3: hypotheses

Ranked from this run's own data first (impact, shape, change list), before any history was read:

1. H1 bad deploy (v2.15.0): fits the onset to the minute and the failing path.
2. H2 N+1 in the list handler: explains the step in DB calls with flat request rate and flat per-call latency.
3. H3 database itself slow (CPU, locks): DB operations rose 10 times, so DB load rose; the question is whether the DB got slow.
4. H4 connection exhaustion / pool cap.
5. H5 pod capacity (3 replicas, no HPA seen).
6. H6 traffic spike or bot.
7. H7 downstream slow (orders-db or auth-api).

Not added: `sched:` entries (the class is not `scheduled` and no schedule was listed); instance or node churn (0 restarts, no events); cache evictions (no cache found); certificate expiry, DNS, NAT (no errors measured).

### History lookup (only after the ranked list existed)

```bash
grep -rn -E '^(service|deps):.*(orders-api|orders-db)' .culiops/sre-investigate/incidents
grep -rn -E '^symptoms:.*latency' .culiops/sre-investigate/incidents
cat .culiops/sre-investigate/incidents/2026-08-14-orders-api.md
```

| Command | World file | Returned |
|---|---|---|
| grep service/deps | (grep applied to `incidents/`) | `2026-08-14-orders-api.md:3: service: orders-api` and `:7: deps: [orders-db]` |
| grep symptoms | (grep applied to `incidents/`) | `2026-08-14-orders-api.md:5: symptoms: [latency, p95, "GET /orders", "POST /orders"]` |
| `cat incidents/2026-08-14-orders-api.md` | `incidents/2026-08-14-orders-api.md` | opened only to write the lead's hypothesis; its content is not logged in the ledger's Memory table (file name and matched fields only) |

`2026-09-30-catalog-api.md` did not match. No `lessons.md` exists, so there are no `failure-mode` lines. No wiki or runbook access is configured, so no docs lookup. The match became its own hypothesis `from-history:2026-08-14-orders-api` (written by the main session, overlapping H4); it starts with no label.

Model tiers decided now: H2 on the stronger tier (three signals to correlate: spans, metrics and code, and the expected quantitative conflict); the rest on the default tier. Ledger stage B written (hypotheses, Memory, lesson candidates).

### Deep checkpoint 2

**Message 6 (checkpoint 2), verbatim:**

```text
Checkpoint 2: ranked hypotheses and how each will be tested (falsification query first). Nothing is labelled yet; one evidence worker per hypothesis will run after your reply.

1. H1 Bad deploy: the v2.15.0 rollout (Helm revision 24) caused the GET /orders slowdown. Falsification: old-against-new split; an onset before 13:04:50, or the old revision equally slow, refutes it. (default tier)
2. H2 N+1: the v2.15.0 list handler issues one items query per order. Falsification: descendant spans per GET /orders request, 24 traces per window, 14:30-15:30 against 11:00-12:00; equal counts refute it. Also reads the code at v2.15.0. (stronger tier)
3. H3 orders-db itself is slow (CPU, locks, credits). Falsification: RDS CPU, read latency and connections at baseline, together with a flat per-request query count. (default)
4. H4 Connection exhaustion at the pool cap. Falsification: pending_requests at zero and used far from any cap. (default)
5. from-history:2026-08-14-orders-api, a lead from a past orders-api latency incident (a pool-size or configuration change leaves the orders-db pool exhausted; overlaps H4). Falsification: pending_requests at zero throughout and the chart version unchanged across the rollout. (default)
6. H5 Pod capacity: the 3 replicas are CPU-bound or throttled with no autoscaler. Falsification: desired = ready and no throttling; HPA absent or below max. (default)
7. H6 Traffic spike or bot. Falsification: request count against the previous window and -7d. (default)
8. H7 A downstream (orders-db or auth-api) is slow or timing out. Falsification: downstream span p95 at baseline. (default)

Budget: 35 of the 60 query ceiling is used; the remaining 25 are split 3 per worker. You can add, drop or re-rank anything before I spend them.
```

**Operator line 3 (received at checkpoint 2):** "Fine, continue."

---

## Phase 4: evidence (wave 3, one worker per hypothesis, all dispatched in one message)

Dispatch (every call passes `model` explicitly): H2 on the stronger tier; H1, H3, H4, from-history, H5, H6 and H7 on the default tier. Each gets the full prompt from `agents/evidence.md` with: its own ID, statement, expected evidence and falsification query (the from-history worker gets only the line I wrote, never the incident file or its label); `RUN=<run directory>/raw/<ID>`; the three windows; the run's `profile.md` (not the stored one); budget share 3 queries, 0 GB of logs, 62 CloudWatch metric requests, 3 waves; lessons: none. Workers may read only the ledger's Windows, Query log and Gaps sections and their own hypothesis row. The simulated workers below follow exactly that.

### [evidence H1, default tier]

Read: environment.md; playbooks/changes.md (Old against new, App code at the deployed ref); the run's profile.md; ledger Windows, Query log, Gaps, row H1. Falsification run first, from the existing rows (`reused`): is the onset earlier than the rollout, or is the old revision equally slow?

```text
VERDICT: H1 | Confirmed
summary: Only the new revision is slow. GET /orders p95 was 0.160 to 0.200 s in all 94 samples of the old revision (v2.14.0, 10:00 to 13:06 today) and in all 166 samples on 2026-10-13; it is 0.661 to 0.755 s in all 72 samples of the new revision (v2.15.0, 13:08 to 15:30). The first elevated sample (13:08) comes after the rollout (Helm revision 24, 13:04:50), not before it. Per revision: new 72/72 samples slow and 24/24 sampled traces with 9 to 52 downstream spans; old 0/94 samples slow and 24/24 sampled traces with 2 to 4. Of the three commits in the release only a4c1e9b (list handler, #2211) is on the failing path; #2208 (order detail) and #2203 (structlog) sit on routes or paths that stayed flat. Change, mechanism and timing are all cited below.
weakest_link: the old and new revisions never ran side by side (all 3 pods were replaced within about a minute), so the split is sequential; the rollout start rests on Helm's zone-less UPDATED value and pod age, cross-checked to about 3 minutes against the UTC step at 13:08 (Confirmed at that resolution)

evidence:
- Onset after the rollout: last clean p95 sample 13:06 (0.163 s), first elevated 13:08 (0.716 s); Helm revision 24 at 13:04:50 [prometheus, W1-Q8, 09:30 to 15:30; helm, W1-Q4] link: Grafana Explore prom-prod, query as in the ledger
- Old revision never slow in the covered data: 94 of 94 samples at or below 0.200 s today before the rollout, 166 of 166 on 2026-10-13 [prometheus, W1-Q8, W1-Q10] link: same
- New revision slow on every sample: 72 of 72 at or above 0.661 s [prometheus, W1-Q8, 13:08 to 15:30] link: same
- Same split in the requests themselves: 24 sampled traces on the new revision window have 9 to 52 descendant spans (p50 41), 24 on the old window have 2 to 4 (p50 3); one trace each shows 12 per-order SELECTs against one joined SELECT [tempo, W2-Q8, W2-Q9, W2-Q10, W2-Q11] link: Tempo trace view for e3ea7a39... and 65345f5f...
- Mechanism visible in metrics at the same minute: database operations 365.5/s at 13:06, 4031.1/s at 13:08 with request rate flat at about 56/s [prometheus, W1-Q15, PB-Q16, 09:30 to 15:30] link: Grafana Explore prom-prod
- Change on the failing path: a4c1e9b replaces one joined query by a per-order loop in orders_api/handlers/list_orders.py; the other two commits are not on it: GET /orders/{id} p95 0.061 to 0.064 s, POST /orders 0.139 to 0.142 s, PATCH 0.091 to 0.088 s [git, W2-Q1, W2-Q2; prometheus, W1-Q5, W1-Q6] link: git diff v2.14.0..v2.15.0 in the clone
- Pods: 3 of 3 new pods Running, 0 restarts; ReplicaSet 7c9b6d8f5d 3 ready, the old one at 0 [kubectl, PB-Q9, W1-Q2]

timeline:
- 13:04:50 — Helm revision 24 (v2.15.0, chart unchanged) — helm W1-Q4
- about 13:05 — ReplicaSet orders-api-7c9b6d8f5d, 3 pods about 144 to 145 minutes old at about 15:30 — kubectl W1-Q2, PB-Q9
- 13:06 / 13:08 — last clean / first elevated p95 sample — prometheus W1-Q8

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| (none new) | | every claim reused ledger rows W1-Q2, W1-Q4, W1-Q5, W1-Q6, W1-Q8, W1-Q10, W1-Q15, W2-Q1, W2-Q2, W2-Q8..Q11, PB-Q9, PB-Q16 | | | |

gaps:
- Helm UPDATED prints no zone and kubectl showed AGE only (no creationTimestamp) — rollout start dated to about 3 minutes by cross-check, not by a UTC stamp
- No IaC repo and Helm values are not read by design — a values change shipped in the same release would not be visible; the chart version is the same in revisions 23 and 24
- No per-pod latency — a single-pod outlier is not excluded, but all pods run one ReplicaSet and CPU is the same

untrusted_text:
- none

to_confirm_by_human:
- Read the creationTimestamp of ReplicaSet orders-api-7c9b6d8f5d, or the CD pipeline's deploy record, to date the rollout in UTC.
- Compare the chart values files at the two releases to confirm no configuration change shipped with the code.

lesson_candidates:
- none

cost: 0 queries, 0 GB of logs scanned, 0 CloudWatch metric requests, none
```

Dispatcher check: `Confirmed` cites W2-Q8 and W2-Q10 (spans in the window) and W1-Q15 (the mechanism at the onset), so no escalation.

### [evidence H2, escalated tier]

(Started on the stronger tier by the dispatcher rules; this is not an escalation of a default-tier verdict.) Read: environment.md; playbooks/traces.md (Queries per request, N+1) and changes.md (the slow-endpoint code section); the run's profile.md; ledger Windows, Query log, Gaps, row H2. Falsification first: spans per request equal between windows? The ledger already holds 24 traces per window (W2-Q8, W2-Q9, at least 20 each), so they are reused; then the code at the deployed ref.

Worker commands (RUN=raw/H2):

```bash
git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py
git -C ~/src/orders-api show v2.15.0:orders_api/repository.py
```

| Worker ID | Command | World file | Key facts returned |
|---|---|---|---|
| H2-Q1 | `git show v2.15.0:orders_api/handlers/list_orders.py` | `../repo/orders_api/handlers/list_orders.py` | line 13: `limit = min(int(...), 50)`; lines 15 to 18: `orders = repo.list_orders(...)` then `for order in orders: order.items = repo.list_items(order.id)`; docstring says each order carries its line items |
| H2-Q2 | `git show v2.15.0:orders_api/repository.py` | `../repo/orders_api/repository.py` | `list_items` (lines 44 to 47) executes ITEMS_SQL (one `WHERE order_id = ...` query, lines 22 to 26) inside its own `with self.pool.connection()`; `list_orders_with_items` (lines 38 to 42, SQL lines 11 to 20) is one LEFT JOIN round trip, "used by the list handler up to v2.14.0" |

Local arithmetic (python3 -I over the pulled search results): trace duration against descendant spans, 48 traces (24 + 24): duration = 100.8 ms + 5.8 ms per span, r = 0.979. Sample means: 38.9 descendants (new) against 3.1 (old), +35.8 per request; one descendant per trace is the auth-api call, so DB spans are 37.9 against about 2.1.

```text
VERDICT: H2 | Confirmed
summary: The v2.15.0 list handler runs one items query per order. Per GET /orders request, descendant spans (the auth-api call plus database spans) are 9 to 52 (p50 41, p95 52) on the new revision against 2 to 4 (p50 3) on the old one, 24 traces each; the largest new count (52 = auth call + 1 orders query + 50 item queries) equals 1 + the page cap of 50 in the code. Each span is as fast as before (database span p95 3.9 to 4.4 ms before and after 13:08), the fetched new trace shows 12 serial item queries of 2.9 to 4.5 ms against one joined query on the old trace, and trace duration follows span count (about 101 ms + 5.8 ms per span, r = 0.98, n = 48), which accounts for the p50 move from about 110 ms to about 342 ms. Database operations rose 10.4 times at 13:08 with a flat request rate, and the pool never waited.
weakest_link: attribution of the latency to the span count comes from 48 sampled traces with an unknown sampling rate; it agrees with the independent 13:08 metric step in p50, p95 and database operations (Confirmed)

evidence:
- Spans per request differ: new window p50 41, p95 52, max 52; old window p50 3, p95 4, max 4; 24 traces each (at least 20) [tempo, W2-Q8, W2-Q9, 14:30 to 15:30 against 11:00 to 12:00] link: Tempo search with the structural query in the ledger
- Per-trace shape: new trace e3ea7a39... = auth-api verify + SELECT orders + 12 x SELECT order_items; old trace 65345f5f... = auth-api verify + one SELECT orders JOIN order_items [tempo, W2-Q10, W2-Q11] link: Tempo trace view
- Each database span is as fast as before: p95 3.9 to 4.4 ms at all 23 steps, 10:00 to 15:30 [tempo, W1-Q17] link: Tempo metrics query in the ledger
- Code at the deployed ref: the loop calls list_items(order.id) per order, capped at 50 orders; list_items takes its own pool connection per call; the previous call was one LEFT JOIN round trip [git, H2-Q1, H2-Q2, tag v2.15.0] link: git show in the clone
- Metrics agree: database operations 380/s to 3,952/s (10.4 times) stepping at 13:08, request rate 56.5 to 56.1 req/s, pool pending_requests 0 in 166 of 166 samples [prometheus, W1-Q15, PB-Q16, W1-Q19] link: Grafana Explore prom-prod
- Same window on 2026-10-13: database operations 355 to 404/s [prometheus, W1-Q16]

timeline:
- 2026-10-19 — a4c1e9b "load items per order in list handler (#2211)" merged — git W2-Q1
- 13:04:50 — release v2.15.0 rolled out — helm W1-Q4
- 13:08 — first sample with 10.4 times the database operations and the slower p50 and p95 — prometheus W1-Q15, W1-Q8

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H2-Q1 | git | `git -C ~/src/orders-api show v2.15.0:orders_api/handlers/list_orders.py` | tag v2.15.0 | free | per-order loop on lines 15 to 18; cap 50 on line 13. link: file in the clone |
| H2-Q2 | git | `git -C ~/src/orders-api show v2.15.0:orders_api/repository.py` | tag v2.15.0 | free | list_items runs one query per call with its own pool connection (lines 44 to 47); the joined read is lines 38 to 42. link: file in the clone |

gaps:
- Size not reconciled: +3,572 operations/s at 56.1 req/s is +63.7 per request, but the code and the traces allow at most 51 database spans per request (1 + 50), and the sampled mean (+35.8 per request) explains only about 56% of the metric increase (about +2,000/s) — mechanism shown directly, exact size of the extra work not
- Old traces show 2 to 4 descendants where the code reads one joined query plus the auth call (2) — the extra 0 to 2 spans in some old traces are not explained
- Sampling rate of the traces is unknown

untrusted_text:
- none

to_confirm_by_human:
- Ask the owning team what db_client_operation_duration_seconds_count counts (statements only, or also pool checkouts or transaction statements) and whether other routes changed their query counts, to reconcile the size.
- In a non-production environment, reproduce a list request for a customer with 50 orders and count the queries issued (a reproduction is not done by this run).

lesson_candidates:
- process (tempo) A structural TraceQL search reports matched as every descendant span, including non-DB client spans such as the auth-api verify call; subtract them before reading DB-span counts. — W2-Q8

cost: 2 queries, 0 GB of logs scanned, 0 CloudWatch metric requests, none
```

### [evidence H3, default tier]

Read: environment.md; playbooks/metrics.md (AWS saturation and dependency metrics); profile.md; ledger Windows, Query log, Gaps, row H3. Falsification first: RDS CPU, read latency and connections at baseline refute it, but only together with a flat per-request query count; the per-request count is NOT flat (W2-Q8, W2-Q9), so a flat DB metric alone would not clear the DB. The query asks the database's own view.

```bash
RUN=<run directory>/raw/H3; mkdir -p "$RUN"
# q-rds-300.json: three entries, Id cpu / readlat / conns, Namespace AWS/RDS, Dimensions [DBInstanceIdentifier=orders-db], Period 300, Stat Average,
#   MetricName CPUUtilization / ReadLatency / DatabaseConnections
aws cloudwatch get-metric-data --profile prod-read --region us-east-1 --metric-data-queries "file://$RUN/q-rds-300.json" --start-time 2026-10-20T10:00:00Z --end-time 2026-10-20T15:30:00Z --output json > "$RUN/m-rds.json"
```

| Worker ID | Command | World file | Key facts returned |
|---|---|---|---|
| H3-Q1 | `aws cloudwatch get-metric-data` (AWS/RDS, orders-db, 5 min) | `cw-01.json` | status Complete, 67 points per metric. CPUUtilization: 10:00 to 13:00 buckets (37) mean 24.5% (21.2 to 26.9); 13:05 bucket 23.9%; 13:10 to 15:30 buckets (29) mean 40.4% (37.1 to 44.0). ReadLatency: 0.59 ms before and after (0.52 to 0.67). DatabaseConnections: mean 41.7 (40 to 44) before, 46.1 (43 to 48) after. No messages |

```text
VERDICT: H3 | Ruled out
summary: The database did not become slow. Read latency is 0.59 ms before and after the onset, connections move from about 42 to about 46, and per-call database spans stay at about 4 ms (reused). CPU rose from about 24% to about 40% (maximum 44%), which is the cost of roughly ten times more queries, not a saturated or locked database; the rise starts in the 13:10 bucket, one 5-minute bucket after the application-side step at 13:08 (the 13:05 bucket is still at baseline), so it follows the application and does not lead it. Because the per-request query count is not flat (reused W2-Q8, W2-Q9), the flat read latency alone would not have cleared the database; what clears it is that the extra time is accounted for by the span count (reused: trace duration about 101 ms + 5.8 ms per span).
weakest_link: lock waits and deadlocks were not measured (only CPU, read latency and connections), and RDS values are 5-minute averages (Ruled out for a slow database; the DB remains a capacity concern at its new 40% CPU)

evidence:
- RDS CPU 24.5% (37 buckets, 10:00 to 13:00) against 40.4% (29 buckets, 13:10 to 15:30), maximum 44.0%; the 13:05 bucket is 23.9% [cloudwatch, H3-Q1, 10:00 to 15:30] link: CloudWatch console, AWS/RDS, DBInstanceIdentifier=orders-db
- ReadLatency 0.59 ms before and 0.59 ms after (0.52 to 0.67 ms throughout) [cloudwatch, H3-Q1] link: same
- DatabaseConnections 41.7 to 46.1 [cloudwatch, H3-Q1] link: same
- Per-call database span p95 3.9 to 4.4 ms before and after [tempo, W1-Q17, reused]
- Per-request span count is up (p50 3 to 41) [tempo, W2-Q8, W2-Q9, reused]

timeline:
- 13:08 — application-side step (database operations 10.4 times) — prometheus W1-Q15 (reused)
- 13:10 — first RDS bucket with CPU 41.3% — cloudwatch H3-Q1

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H3-Q1 | cloudwatch | get-metric-data AWS/RDS orders-db CPUUtilization, ReadLatency, DatabaseConnections, Period 300, Average | 10:00 to 15:30 | 3 metric requests | CPU 24.5% to 40.4% (max 44.0%); ReadLatency flat 0.59 ms; connections 41.7 to 46.1. link: CloudWatch console, AWS/RDS |

gaps:
- Lock waits and deadlocks not pulled — a lock problem is excluded only through the flat read latency and the span-time accounting
- db.r6g.2xlarge is not a burstable class, so no CPU credit balance was requested

untrusted_text:
- none

to_confirm_by_human:
- If the team wants the lock question closed, read the database's lock-wait view in a Performance Insights session; Performance Insights is off for this instance (rds describe), so enabling it is a change for the owner.

lesson_candidates:
- process (cloudwatch) RDS CPU in 5-minute buckets stepped one bucket (13:10) after the app-side step (13:08); DB-side metrics trail app-side steps, so do not use them to date an onset. — H3-Q1

cost: 1 query, 0 GB of logs scanned, 3 CloudWatch metric requests, none
```

### [evidence H4, default tier]

Read: environment.md; playbooks/metrics.md (connection pools note); profile.md; ledger Windows, Query log, Gaps, row H4. Falsification first, from the existing row W1-Q19.

```text
VERDICT: H4 | Ruled out
summary: The pool never waited. pending_requests is 0 in all 166 samples (09:30 to 15:30 window, data from 10:00) and used rises only from 14 to 19 before the onset to 17 to 24 after. No pool cap is known, but waiting is what exhaustion looks like and none appears in any of the 72 samples after 13:08; the latency step is also uniform across p50 and p95 (about 3.4 to 3.9 times), where pool queueing would add a tail. The code takes a pool connection per query, so ten times more checkouts raise churn (used 16 to 21) but not waiting.
weakest_link: the pool gauges are sampled every 2 minutes and the pool maximum is unknown, so a brief burst of waiting could hide between samples; none is visible over 2 hours 22 minutes (Ruled out for sustained exhaustion)

evidence:
- pending_requests 0 in 166 of 166 samples [prometheus, W1-Q19, 09:30 to 15:30, step 120 s] link: Grafana Explore prom-prod
- used 14 to 19 before 13:08 (mean 16.3), 17 to 24 after (mean 20.6) [prometheus, W1-Q19] link: same
- No pool-wait errors counted: the error rate is not available (no status label), so this is a gap, not a negative [see gaps]

timeline:
- 13:08 — pool used steps up slightly, pending stays 0 — prometheus W1-Q19

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| (none new) | | reused W1-Q19, W2-Q8, W2-Q9 | | | |

gaps:
- Pool maximum size not read (no config source) — "used far from the cap" cannot be quantified
- No pool-wait or connect-timeout counter in the metric list — only the sampled gauge speaks

untrusted_text:
- none

to_confirm_by_human:
- Ask the owner for the configured pool maximum for the orders-db pool to put a number on the headroom.

lesson_candidates:
- none

cost: 0 queries, 0 GB of logs scanned, 0 CloudWatch metric requests, none
```

### [evidence from-history:2026-08-14-orders-api, default tier]

Received only: "A pool-size or configuration change left the orders-db pool exhausted (a lead from history; overlaps H4). Expected: pending_requests above zero for the window; a chart or values change at the onset. Falsification: pending_requests at zero throughout, and the chart version unchanged across the rollout." It did not receive the incident file, its body or its label. Read: environment.md; profile.md; ledger Windows, Query log, Gaps, its own row. Falsification first, from rows W1-Q19 and W1-Q4.

```text
VERDICT: from-history:2026-08-14-orders-api | Ruled out
summary: pending_requests is 0 in all 166 samples, so the pool was never exhausted in this window, and the Helm chart is orders-api-4.2.0 in both revisions 23 and 24, so no chart-version change accompanied the rollout. The chart's values files were not read (Helm values are not printed by design), so a pool-size change inside the values is not seen directly; but a smaller pool would show as waiting, and nothing waits.
weakest_link: the values of the Helm release are not visible, so "no pool-size change" is inferred from the absence of waiting rather than read (Ruled out for the exhaustion effect)

evidence:
- pending_requests 0 in 166 of 166 samples; used 14 to 24 [prometheus, W1-Q19, 09:30 to 15:30] link: Grafana Explore prom-prod
- Chart orders-api-4.2.0 in revision 23 (2026-10-07) and revision 24 (2026-10-20 13:04:50) [helm, W1-Q4] link: helm history in the cluster

timeline:
- 13:04:50 — Helm revision 24, chart unchanged — helm W1-Q4

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| (none new) | | reused W1-Q19, W1-Q4 | | | |

gaps:
- Helm values not read (by design) — a pool-size setting change is not directly visible

untrusted_text:
- none

to_confirm_by_human:
- Compare the release's values files in git at the two revisions for the pool-size setting.

lesson_candidates:
- none

cost: 0 queries, 0 GB of logs scanned, 0 CloudWatch metric requests, none
```

### [evidence H5, default tier]

Read: environment.md; playbooks/metrics.md (Drill-down ladder, Kubernetes signals) and infra-state.md; profile.md; ledger Windows, Query log, Gaps, row H5. Falsification first: desired = ready and no throttling; HPA absent or below max.

```bash
CTX=arn:aws:eks:us-east-1:111122223333:cluster/prod
kubectl --context "$CTX" -n orders get deploy orders-api -o json | jq '[.spec.template.spec.containers[] | {name, resources}]'
kubectl --context "$CTX" -n orders get hpa
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'query=sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="orders"}[5m])) / sum by (pod) (rate(container_cpu_cfs_periods_total{namespace="orders"}[5m]))' --data-urlencode "start=1792499400" --data-urlencode "end=1792510200" --data-urlencode "step=600"
```

| Worker ID | Command | World file | Key facts returned |
|---|---|---|---|
| H5-Q1 | `kubectl get deploy orders-api -o json` (containers' resources) | `_empty.txt` | no output (CPU limits unreadable) |
| H5-Q2 | `kubectl get hpa -n orders` | `_empty.txt` | no output (no HPA listed) |
| H5-Q3 | PromQL CPU throttling share | `prom-10.json` | empty matrix; the throttling series are not in the metric-name list (PB-Q7) |

```text
VERDICT: H5 | inconclusive
summary: Not refuted and not supported. Replicas are steady at desired = current = ready = 3, all pods Running with 0 restarts, and CPU per pod sits at 0.52 to 0.64 cores with no ramp, which does not look like a saturation curve; but the CPU limit, the HPA and the throttling counters could not be read, and the CPU series starts at 13:08 so there is no pre-incident baseline. The extra queries per request would raise CPU per request, so a capacity effect on top of the N+1 cannot be excluded.
weakest_link: no CPU limit, no throttling series and no pre-incident CPU baseline (nothing in the data supports or contradicts the capacity hypothesis)

evidence:
- desired = current = ready = 3, 0 restarts [kubectl, W1-Q2, PB-Q9, reused]
- CPU 0.52 to 0.64 cores per pod from 13:08, equal across the 3 pods [prometheus, W1-Q18, reused]
- No HPA listed [kubectl, H5-Q2] ; no throttling series exported [prometheus, H5-Q3]

timeline:
- 13:08 — first CPU sample of the new pods, 0.58 cores each — prometheus W1-Q18

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H5-Q1 | kubectl | `kubectl ... get deploy orders-api -o json \| jq '[.spec.template.spec.containers[] \| {name, resources}]'` | now | free | no output. link: the same command |
| H5-Q2 | kubectl | `kubectl ... -n orders get hpa` | now | free | no output. link: the same command |
| H5-Q3 | prometheus | throttled periods / periods per pod | 12:30 to 15:30 | cheap | empty matrix. link: Grafana Explore prom-prod |

gaps:
- CPU limit not readable — cannot say how close 0.58 cores is to the limit
- Throttling and resource-limit series not exported — the usual capacity test is unavailable
- No CPU baseline before 13:08 — cannot compare per-request CPU

untrusted_text:
- none

to_confirm_by_human:
- Read the Deployment's CPU request and limit and the container's throttling statistics for the last three hours.

lesson_candidates:
- process (prometheus) No cfs throttling, container-limit or kubectl top data is available for namespace orders; capacity hypotheses there cannot be tested with metrics. — H5-Q3

cost: 3 queries, 0 GB of logs scanned, 0 CloudWatch metric requests, none
```

**Dispatcher (main session):** an `inconclusive` default-tier verdict may be escalated once. Re-dispatching H5 on the stronger tier with the PREVIOUS VERDICT block and its query table, targeting exactly the named gap (CPU headroom).

### [evidence H5, escalated tier]

Read the previous verdict first; does not repeat H5-Q1 to H5-Q3. Targets: live CPU figures.

```bash
kubectl --context arn:aws:eks:us-east-1:111122223333:cluster/prod -n orders top pods
```

| Worker ID | Command | World file | Key facts returned |
|---|---|---|---|
| H5-Q4 | `kubectl -n orders top pods` | `_empty.txt` | no output (no metrics API answer) |

```text
VERDICT: H5 | inconclusive
summary: The gap named by the previous verdict cannot be closed with read-only access here: the Deployment's resources, the HPA, the throttling series and kubectl top all return nothing. The indirect reading stays: replicas steady at 3 ready, no restarts, CPU 0.52 to 0.64 cores per pod with no ramp, p50 and p95 moving together in a single step the minute the code changed. That favours a code cause over a capacity cause, but it is a reading, not a query result, so the hypothesis stays open.
weakest_link: no readable CPU limit or throttling figure (nothing in the data supports or contradicts the hypothesis directly)

evidence:
- as the previous verdict, plus kubectl top pods returned nothing [kubectl, H5-Q4]

timeline:
- (none new)

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H5-Q4 | kubectl | `kubectl ... -n orders top pods` | now | free | no output. link: the same command |

gaps:
- same as the previous verdict; escalation did not add data

untrusted_text:
- none

to_confirm_by_human:
- Read the Deployment's CPU request and limit and the throttling counters, as in the previous verdict.

lesson_candidates:
- none

cost: 1 query, 0 GB of logs scanned, 0 CloudWatch metric requests, none
```

Dispatcher: an inconclusive stronger-tier verdict stays open with its gaps; no further escalation.

### [evidence H6, default tier]

Read: environment.md; playbooks/metrics.md (Drill-down ladder, volume or speed); profile.md; ledger Windows, Query log, Gaps, row H6. Falsification first: request count against the previous window and -7d.

```text
VERDICT: H6 | Ruled out
summary: Request volume did not change. GET /orders runs at 56.5 req/s before 13:08 and 56.1 req/s after (52 to 61 across the whole range), with no step at the onset, while latency and database operations stepped. The -7d comparison is not usable (the offset query returned the unshifted series), so the reading rests on the previous window, 3 hours long.
weakest_link: no usable -7d request-rate series; the previous-window comparison (about 3 hours) carries the conclusion (Ruled out)

evidence:
- 166 request-rate points, 52 to 61 req/s, mean 56.5 (to 13:06) and 56.1 (from 13:10); no step at 13:08 [prometheus, PB-Q16, 10:00 to 15:30, reused] link: Grafana Explore prom-prod
- The -7d series is identical to the unshifted one, so it is not used [prometheus, W1-Q14, reused]
- Latency and database operations step at 13:08 while the call count does not [prometheus, W1-Q8, W1-Q15, reused]

timeline:
- 13:08 — latency and database operations step; request rate unchanged — prometheus PB-Q16, W1-Q8, W1-Q15

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| (none new) | | reused PB-Q16, W1-Q8, W1-Q14, W1-Q15 | | | |

gaps:
- No -7d request-rate series — weekday/hour effects not excluded, but no step exists at the onset
- No client or path breakdown of requests — concentration on a few clients cannot be checked, and is not needed with a flat total

untrusted_text:
- none

to_confirm_by_human:
- Look at the request-rate panel for 2026-10-13 12:30 to 15:30 to close the -7d comparison.

lesson_candidates:
- none

cost: 0 queries, 0 GB of logs scanned, 0 CloudWatch metric requests, none
```

### [evidence H7, default tier]

Read: environment.md; playbooks/traces.md (Slow downstream); profile.md; ledger Windows, Query log, Gaps, row H7. Falsification first, from the existing rows (database spans), then the second downstream.

```bash
curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" --data-urlencode 'q={ resource.service.name = "orders-api" && span:kind = client && span.server.address = "auth-api.auth.svc.cluster.local" } | quantile_over_time(duration, .95)' --data-urlencode "start=1792490400" --data-urlencode "end=1792510200" --data-urlencode "step=15m"
```

| Worker ID | Command | World file | Key facts returned |
|---|---|---|---|
| H7-Q1 | Tempo TraceQL metrics, auth-api client spans, p95 | `tempo-08.json` | `series: []`, 0 jobs: no series |

```text
VERDICT: H7 | Ruled out
summary: A ceiling shape is not present: p50 moved as much as p95 (0.09 to 0.31 s and 0.18 to 0.71 s), so requests are not waiting out one downstream timeout. orders-db: per-call span p95 is 3.9 to 4.4 ms before and after the onset. auth-api: its latency series is not available (the metrics query returned nothing), but the two fetched traces show 3.4 ms (new) and 3.8 ms (old) for the verify call, and the fit of trace duration on span count (about 101 ms + 5.8 ms per span, 48 traces) leaves the same fixed part before and after, so no extra wait attributable to anything other than the added database spans appears.
weakest_link: auth-api's own latency series is missing (two traces and the duration fit speak for it; orders-db is measured directly)

evidence:
- DB span p95 3.9 to 4.4 ms at all 23 steps [tempo, W1-Q17, reused] link: Tempo metrics query in the ledger
- p50 and p95 both moved (no ceiling) [prometheus, W1-Q8, W1-Q9, reused]
- auth-api verify span 3.4 ms (new) and 3.8 ms (old) in one trace each [tempo, W2-Q10, W2-Q11, reused]
- Duration = 100.8 ms + 5.8 ms per span, r = 0.98: fixed part about 101 ms in both windows [tempo, W2-Q8, W2-Q9, reused]
- auth-api client-span metrics query: no series [tempo, H7-Q1]

timeline:
- (none)

queries:
| ID | Source | Query | Range (UTC) | Est. cost | Result |
|---|---|---|---|---|---|
| H7-Q1 | tempo | TraceQL metrics, client spans to auth-api.auth.svc.cluster.local, quantile_over_time(duration, .95) | 10:00 to 15:30 step 15 m | cheap | no series (the attribute filter may not match how the spans store the address). link: Tempo metrics query in the ledger |

gaps:
- auth-api p95 series unavailable — auth-api cleared by indirect evidence only
- p90 and p99 unavailable (reused gap)

untrusted_text:
- none

to_confirm_by_human:
- Ask the auth-api owners whether their verify latency or error rate moved between 13:00 and 15:30.

lesson_candidates:
- process (tempo) A TraceQL metrics query on the auth-api client spans returned no series although two traces show them; an empty metrics result is not "no calls". — H7-Q1

cost: 1 query, 0 GB of logs scanned, 0 CloudWatch metric requests, none
```

### Merge (main session)

- Worker query IDs renumbered to wave 3: H2-Q1 -> W3-Q1, H2-Q2 -> W3-Q2, H3-Q1 -> W3-Q3, H5-Q1 -> W3-Q4, H5-Q2 -> W3-Q5, H5-Q3 -> W3-Q6, H7-Q1 -> W3-Q7, H5-Q4 -> W3-Q8. Total counted queries 43 of 60; CloudWatch metric requests 3 of 500; Loki 0.05 GB.
- Labels applied from the verdicts: H1 Confirmed, H2 Confirmed, H3 Ruled out, H4 Ruled out, from-history Ruled out, H5 Assumed (inconclusive twice, open), H6 Ruled out, H7 Ruled out. No label exceeds its weakest link as named.
- `lesson_candidates` copied to the ledger's Lesson candidates (the tempo `matched`, cloudwatch bucket, prometheus throttling and tempo auth-api lines). `untrusted_text`: none from any worker; nothing to flag.
- Ledger stage C written: hypotheses labels, query rows W3-Q1..Q8, timeline row 13:10, gaps (size not reconciled, auth-api series), lesson candidates.

**Message 7 (after the merge), verbatim:**

```text
Phase 4 is done: 8 workers returned (H2 ran on the stronger tier from the start; H5 was inconclusive on the default tier and stayed inconclusive when re-run on the stronger tier). No text in any log line, trace, commit or tool output read like an instruction, so nothing to flag as a suspected prompt injection. Writing the report now.
```

---

## Phase 5: conclude

Causal chain: (1) Trigger: release v2.15.0 rolled out at about 13:05 UTC, containing a4c1e9b: Confirmed (W1-Q3, W1-Q4, W1-Q2, W2-Q2, W3-Q1). (2) Mechanism: the list handler now issues 1 + up to 50 serial queries per request instead of one joined query: Confirmed (W2-Q8..Q11, W1-Q15, W1-Q17, W3-Q2). (3) Symptom: p95 0.18 -> 0.71 s, p50 0.09 -> 0.31 s: Confirmed (W1-Q8, W1-Q9, duration fit). All other hypotheses: Ruled out except H5 (Assumed, open). Third parties: none in the path. History: 2026-08-14-orders-api was matched and tested as a lead; Ruled out, so this is not a repeat of the same cause. Fixes and mitigations are written as prose only.

`report.md`: report saved separately.

**Message 8 (TL;DR, Deep mode), verbatim:**

```text
TL;DR
- Cause: release v2.15.0 (Helm revision 24, about 13:05 UTC) rewrote the GET /orders list handler (commit a4c1e9b, #2211) from one joined query to one query per order, so each request now makes up to 51 serial database queries instead of one · Confirmed.
- Weakest link: the old and new revisions never ran side by side (all 3 pods were replaced within about a minute) and the rollout start comes from Helm's zone-less time cross-checked with pod age against the UTC step at 13:08, to about 3 minutes · still Confirmed at that resolution. The exact size of the extra database work is not reconciled with the metrics (see Gaps); that does not change the cause.
- Impact: GET /orders p95 0.181 s -> 0.712 s (3.9x), p50 0.09 -> 0.31 s, request rate unchanged at about 56/s, other routes flat, no errors measured. Since 13:08 UTC (23:08 local), ongoing at 15:30 UTC. Suggested SEV2; the incident owner decides.
- Recommended action: a human decides between rolling orders-api back to v2.14.0 as a stop-gap (it also withdraws the shipment ETA on order detail that shipped in the same release) and shipping a fix that loads the page's items in one round trip again; check either with pre-flight first.
- Ruled out: database slowness (read latency flat, CPU 24% -> 40%), pool exhaustion (pending 0), traffic spike (flat), slow downstream (flat ~4 ms per query), and the past-incident lead. Still open: pod CPU capacity (Assumed, data not readable).
Full report: .culiops/sre-investigate/runs/orders-api-prod-20261020-1530/report.md. Open items need your input (the gaps are listed in the report, each with its fix).
Cost: 43 counted queries · 0.05 GB of logs · 3 CloudWatch metric requests · about $0.00 in metered charges.
```

---

## Phase 6: record

Proposed after the report, never before. Nothing written until the reply.

**Message 9 (record diff), verbatim:**

```text
Proposed record (nothing is written until you reply). Three new files under .culiops/sre-investigate/, no existing file changes:

1) incidents/2026-10-20-orders-api.md   (new; this run named a cause at Confirmed)
+ ---
+ id: 2026-10-20-orders-api-prod-list-orders-n-plus-1
+ date: 2026-10-20
+ service: orders-api
+ env: prod
+ siblings: [all]
+ window_utc: 2026-10-20T13:08Z/2026-10-20T15:30Z
+ symptoms: [latency]
+ cause_category: deploy
+ cause: release v2.15.0 changed the GET /orders list handler to one items query per order (N+1): about 10 times more database operations and p95 0.18 s -> 0.71 s
+ deps: [orders-db, auth-api]
+ label: Confirmed
+ mode: deep
+ time_to_cause_min: null
+ run: runs/orders-api-prod-20261020-1530
+ ---
+ (body: what happened, causal chain with labels, what found it, what did not help, follow-ups raised)

2) lessons.md   (new, 11 lines, each backed by a query ID of this run; no lesson contradicts an existing one because none exists)
+ - type: process | service: any | source: tempo | statement: A bare TraceQL search on a service name can return no traces while TraceQL metrics and structural searches on the same name return data; do not read an empty bare search as a wrong service name. | run: orders-api-prod-20261020-1530 | query_id: PB-Q17 | re-verify: no
+ - type: process | service: any | source: aws | statement: An IAM policy simulation for the SSO ReadOnly role returned rows for 7 of the 10 fixed actions plus 3 not on the list; a missing row is a gap, not a pass. | run: orders-api-prod-20261020-1530 | query_id: W0-Q3 | re-verify: no
+ - type: identifier | service: orders-api | source: loki | statement: Loki streams for orders-api are labelled app="orders", namespace="orders", container="api"; the stream has no pod label, so the tie to the orders-api pods is unverified. | run: orders-api-prod-20261020-1530 | query_id: PB-Q15 | re-verify: no
+ - type: process | service: any | source: prometheus | statement: An offset 7d rate on a request counter returned the same series as the unshifted query; compare an offset result with the unshifted one before trusting it. | run: orders-api-prod-20261020-1530 | query_id: W1-Q14 | re-verify: no
+ - type: process | service: orders-api | source: prometheus | statement: 14-day hourly pulls for orders-api returned samples only from 10:00 UTC on the run day and no latency recording rule exists; plan latency recurrence from alert history. | run: orders-api-prod-20261020-1530 | query_id: W1-Q20 | re-verify: no
+ - type: process | service: any | source: helm | statement: helm history prints UPDATED without a zone; confirm the rollout time with the ReplicaSet creationTimestamp, which is UTC. | run: orders-api-prod-20261020-1530 | query_id: W1-Q4 | re-verify: no
+ - type: failure-mode | service: orders-api | source: tempo | statement: GET /orders p50 and p95 step together with flat request rate, flat per-call DB latency (about 4 ms) and DB operations/s up about 10 times after a deploy: look for a per-row query loop and count descendant spans per request. | run: orders-api-prod-20261020-1530 | query_id: W2-Q8 | re-verify: no
+ - type: process | service: any | source: tempo | statement: A structural TraceQL search reports matched as every descendant span, including non-DB client spans such as the auth-api verify call; subtract them before reading DB-span counts. | run: orders-api-prod-20261020-1530 | query_id: W2-Q8 | re-verify: no
+ - type: process | service: orders-api | source: cloudwatch | statement: RDS CPU in 5-minute buckets stepped one bucket after the app-side step; DB-side metrics trail app-side steps, so do not use them to date an onset. | run: orders-api-prod-20261020-1530 | query_id: W3-Q3 | re-verify: no
+ - type: process | service: orders-api | source: prometheus | statement: No cfs throttling, container-limit or kubectl top data is available for namespace orders; capacity hypotheses there cannot be tested with metrics. | run: orders-api-prod-20261020-1530 | query_id: W3-Q6 | re-verify: no
+ - type: process | service: orders-api | source: tempo | statement: A TraceQL metrics query on the auth-api client spans returned no series although two traces show them; an empty metrics result is not "no calls". | run: orders-api-prod-20261020-1530 | query_id: W3-Q7 | re-verify: no

3) profiles/orders-api-prod.md   (new: this run's profile.md, first run for the service)
+ identifiers added: Prometheus service="orders-api" (verified 2026-10-20), Tempo service name orders-api (verified 2026-10-20), RDS orders-db (verified), Deployment/Helm release orders-api (verified), git tag rule v<semver> (verified)
+ identifiers left unverified: Loki app="orders" / namespace="orders" / container="api" (no tie to the pods), default branch of example-org/orders-api, load balancing, HPA/Ingress absence
+ dependencies: orders-db, auth-api (new, seen in traces)
+ stale identifiers: none; differences between backends: service name orders-api in Prometheus and Tempo, app="orders" in Loki

Note for the skill itself (not written anywhere now): an IAM simulation reply that lists different actions than the fixed list should be treated as a gap per action, as done here.

Reply to accept, edit or skip each item.
```

**Operator line 4 (received when shown the proposed record diff):** "Yes, write them."

Files written after the reply (output root = `out/`):

- `out/incidents/2026-10-20-orders-api.md`
- `out/lessons.md`
- `out/profiles/orders-api-prod.md`

**Message 10 (after writing), verbatim:**

```text
Written under .culiops/sre-investigate/: incidents/2026-10-20-orders-api.md, lessons.md (11 lines) and profiles/orders-api-prod.md. Nothing was committed or staged. Fixes go through pre-flight and a separate session (iac-change-execution or your app pipeline), with the report as context.
```

---

## Files written (all under the case `out/` directory)

- `out/runs/orders-api-prod-20261020-1530/ledger.md` (stage A after wave 0 and the profile build, stage B after wave 2 and Phase 3, stage C after the merge; the file holds the final stage)
- `out/runs/orders-api-prod-20261020-1530/profile.md` (run profile; written after the build and updated after wave 2)
- `out/incidents/2026-10-20-orders-api.md`, `out/lessons.md`, `out/profiles/orders-api-prod.md` (after the Phase 6 reply)
- `out/run-log.md` (this file)
- `report.md`: report saved separately.
- NOT written: `raw/` pulls (named in the ledger's Result cells, not materialised in the simulation); `environment.md` (already existed).

## Operator lines

1. Start (opening request): "GET /orders on orders-api in prod has been slow since early this afternoon UTC and the p95 alert keeps firing. Deep mode please, I want this one written up properly."
2. At checkpoint 1: "Agreed, go on."
3. At checkpoint 2: "Fine, continue."
4. At the Phase 6 diff: "Yes, write them."

## Deviations and judgment calls worth a second look

- Budget counting: environment.md has no query totals; the template's deep totals were used as a self-imposed ceiling and only data reads were counted (43), not the 7 access checks and 17 discovery list calls (67 logged calls in all).
- I listed `incidents/` (file names only) together with the output-root listing, before the ranked hypotheses existed; contents were opened only in Phase 3, after the ranking.
- The AWS write-check reply did not match the fixed action list; handled as a per-action gap, not as "read-only confirmed".
- The `-7d` request-rate query came back identical to the unshifted one and was discarded.
- Wave 1 had 21 queries (above ten) because its fixed legs require them.
- `date -u` returned nothing in this environment; "now" is the newest Prometheus sample, so the Start column of the query log is indicative.

