# Metrics playbook

Backends: CloudWatch (metrics, metric math, alarm history) · Prometheus (its HTTP API, the Grafana datasource proxy, or a Grafana MCP server), including kube-state-metrics and cAdvisor series · Grafana annotations · kubectl
verified: docs-only

**Purpose.** Metrics are the cheapest way to answer five questions: how much traffic, how many failures, how slow, how saturated, and since when. They give the true onset (often minutes before the alert), the shape of the change, and whether the incident level is unusual at all. They never give the mechanism; that comes from logs and traces.

## Cost ladder

Cheapest first. Stop at the rung that answers the question.

1. **Queries someone already trusts.** A dashboard panel or an SLO recording rule named in `environment.md` (`slo:`) is re-run with the ledger's fixed window, never with the dashboard's relative range.
2. **Discovery.** Confirm the metric names, label values and CloudWatch dimension values before the first real query (see [Discover identifiers first](#discover-identifiers-first)). A query against a guessed identifier returns nothing, and nothing looks like health.
3. **Batched CloudWatch reads.** One `get-metric-data` call carries the related metrics of one question (around ten). GetMetricData is billed per metric requested, also when Grafana makes the call, so request only metrics a hypothesis needs and add them to `budgets.<mode>.cloudwatch_metric_requests`.
4. **Prometheus range queries.** Aggregate with `by (...)` on every high-cardinality metric. Quantiles over long windows come from recording rules; computing `histogram_quantile` over many hours of a large histogram is the expensive query to avoid. The widest raw `histogram_quantile` range is `budgets.windows.prom_quantile_range` in `environment.md` (neutral default 12h); a wider one asks first.
5. **kubectl.** Current state only. It shows what is true now, not what was true at onset, so it confirms or locates; it never dates.

Every recipe below uses the ledger's fixed window: `START`/`END` as RFC 3339 UTC (`2026-01-15T07:40:00Z`), `START_S`/`END_S` as epoch seconds, and `RUN` as the run directory. `PROM` is either the Prometheus base URL or `$GRAFANA_URL/api/datasources/proxy/uid/<datasource-uid>`. The token variable is the `token_env` from `environment.md`; `$GRAFANA_SERVICE_ACCOUNT_TOKEN` stands in for it here. A Grafana MCP server takes the same PromQL strings; only the transport differs.

## Discover identifiers first

Prometheus label values for one label, limited to the series of one job:

```bash
curl -sG "$PROM/api/v1/label/service/values" \
  -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'match[]={job="<job>"}' \
  --data-urlencode "start=$START" --data-urlencode "end=$END" | jq -r '.data[]'
```
<!-- doc: https://prometheus.io/docs/prometheus/latest/querying/api/ -->

Metric names that exist for a service, with a positive name matcher so the query stays bounded:

```bash
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query=count by (__name__) ({__name__=~".*(request|http|rpc).*", job="<job>"})' \
  --data-urlencode "time=$END" | jq -r '.data.result[].metric.__name__'
```
<!-- doc: https://prometheus.io/docs/prometheus/latest/querying/basics/ -->

CloudWatch dimension values for one metric (only metrics that reported in the past two weeks are listed):

```bash
aws cloudwatch list-metrics --profile <profile> --region <region> \
  --namespace AWS/ApplicationELB --metric-name RequestCount \
  --query 'Metrics[].Dimensions' --output json
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/list-metrics.html -->

Write each confirmed identifier into the service profile. An identifier you expected but did not see stays marked `(unverified)`.

## Windows and step

- **Step.** `step = max(60, range_seconds / 300)`. It keeps every range near 300 points, so a 6h range gets a 72 s step and a 1h range stays at 60 s.
- **Three windows, one wave.** The same query runs for the incident window, the equal-length window just before it, and the incident window shifted back 7 days. Run all three in the same wave; the comparison is the result, a single window is not.
- **CloudWatch period follows retention.** One-minute data exists for 15 days, five-minute data for 63 days, hourly data for 455 days. A window that starts more than 15 days ago needs `Period` ≥ 300; more than 63 days ago, `Period` 3600. Check the number of datapoints returned against the number expected before trusting a flat line.

```bash
step=$(( (END_S - START_S) / 300 )); [ "$step" -lt 60 ] && step=60
len=$(( END_S - START_S ))
for w in "incident $START_S $END_S" "previous $((START_S - len)) $START_S" "minus7d $((START_S - 604800)) $((END_S - 604800))"; do
  read -r win ws we <<< "$w"
  curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
    --data-urlencode 'query=sum by (route) (rate(http_requests_total{service="<service>", code=~"5.."}[5m]))' \
    --data-urlencode "start=$ws" --data-urlencode "end=$we" --data-urlencode "step=$step" \
    > "$RUN/m-5xx-$win.json"
done
```
<!-- doc: https://prometheus.io/docs/prometheus/latest/querying/api/ -->

`http_requests_total`, `service`, `route` and `code` are placeholders for whatever discovery returned. The CloudWatch form is the same loop around one query file (see [GetMetricData to a table (jq)](#getmetricdata-to-a-table-jq)):

```bash
for w in "incident $START_S $END_S" "previous $((START_S - len)) $START_S" "minus7d $((START_S - 604800)) $((END_S - 604800))"; do
  read -r win ws we <<< "$w"
  aws cloudwatch get-metric-data --profile <profile> --region <region> \
    --metric-data-queries "file://$RUN/q-golden-60.json" \
    --start-time "$ws" --end-time "$we" --output json > "$RUN/m-golden-$win.json"
done
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-data.html -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-parameters-types.html -->

## Recurrence (14d × 1h)

Run in the first metric wave, never as a wave of its own and never against a log backend. It feeds the recurrence classification in SKILL.md (scheduled, chronic, recurring, sudden, unclassified).

**The pull.** The main signal, and the same signal on each sibling in the same call, over the 14 days ending at the incident start, at a one-hour resolution; the incident window itself is pulled separately at its normal step. That is 336 points per metric, one CloudWatch metric request each.

**Pick the statistic per signal.** The hourly value must summarise the whole hour:

| Signal | CloudWatch (`Period` 3600) | Prometheus (`step=1h`) |
|---|---|---|
| Counter (requests, errors) | `Sum` | `increase(x[1h])` |
| Gauge that already holds a per-minute count | `Sum` | `sum_over_time(x[1h])` (never `rate` or `increase`: it is not a counter) |
| Latency | `Maximum` or `p99` | a recording rule for the quantile, wrapped in `max_over_time(rule[1h])` |
| Saturation (CPU, connections, queue age) | `Maximum` | `max_over_time(x[1h])` |

Whole-hour expressions only. `rate(x[5m])` evaluated at a one-hour step samples one five-minute slice per hour and misses every spike that falls between slices. With no recording rule for the latency quantile, the fallback is a subquery such as `max_over_time((histogram_quantile(0.95, sum by (le) (rate(x_bucket[5m]))))[1h:5m])` over the 14 days, but only for a small histogram and within `prom_quantile_range`; otherwise record the latency recurrence as a gap and use the error or saturation signal.

```bash
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query=sum by (service) (increase(http_requests_total{service=~"checkout-api|checkout-api-canary", code=~"5.."}[1h]))' \
  --data-urlencode "start=$((START_S - 14*86400))" --data-urlencode "end=$START_S" \
  --data-urlencode "step=3600" > "$RUN/m-recur-14d.json"
```
<!-- doc: https://prometheus.io/docs/prometheus/latest/querying/functions/ -->

**Baseline statistics.** Take the median and p95 over the 14 days of hourly points, leaving out the incident itself and every hour that was already at incident level (`$LEVEL`, the incident's peak hourly value). Take the maximum over every hour before the incident, earlier spikes included: it is what "≥ 2× the 14-day max" is measured against, and leaving earlier spikes out would make a repeat look `sudden`.

```bash
jq --argjson level "$LEVEL" --argjson inc "$START_S" '
  [.data.result[] | {s: (.metric.service // "all"),
     all: [.values[] | select(.[0] < $inc) | (.[1] | tonumber)],
     v: [.values[] | select((.[0] < $inc) and ((.[1] | tonumber) < $level)) | (.[1] | tonumber)] | sort}]
  | map({series: .s, hours: (.v | length),
         median: (.v[((.v | length) / 2 | floor)]),
         p95: (.v[(((.v | length) * 0.95) | floor)]),
         max: (.all | max)})' "$RUN/m-recur-14d.json"
```
<!-- doc: https://jqlang.org/manual/ -->

CloudWatch: one query file with `Period` 3600 and the statistic from the table above, one entry per signal and per sibling (`Id`s such as `main_err`, `canary_err`; an `Id` starts with a lowercase letter). A count metric reported only when non-zero (here `HTTPCode_Target_5XX_Count`) has no datapoint in a quiet hour, which would leave median and p95 computed over the error hours alone; pull it raw with `"ReturnData": false` and return `FILL(raw, 0)` instead. Latency is never filled: an hour with no requests has no latency, not zero latency. The pull ends at the incident start, so no incident hour needs filtering out; `$LEVELS` maps each `Id` to its incident level.

```bash
cat > "$RUN/q-recur-3600.json" <<'EOF'
[ {"Id": "main_err_raw", "ReturnData": false, "MetricStat": {"Period": 3600, "Stat": "Sum",
    "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "HTTPCode_Target_5XX_Count",
      "Dimensions": [{"Name": "LoadBalancer", "Value": "app/<lb-name>/<lb-id>"}, {"Name": "TargetGroup", "Value": "targetgroup/<tg-name>/<tg-id>"}]}}},
  {"Id": "main_err", "Expression": "FILL(main_err_raw, 0)", "Period": 3600, "Label": "5xx per hour, zero-filled"},
  {"Id": "main_p99", "MetricStat": {"Period": 3600, "Stat": "p99",
    "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "TargetResponseTime",
      "Dimensions": [{"Name": "LoadBalancer", "Value": "app/<lb-name>/<lb-id>"}, {"Name": "TargetGroup", "Value": "targetgroup/<tg-name>/<tg-id>"}]}}} ]
EOF
aws cloudwatch get-metric-data --profile <profile> --region <region> \
  --metric-data-queries "file://$RUN/q-recur-3600.json" \
  --start-time "$((START_S - 14*86400))" --end-time "$START_S" --output json > "$RUN/m-recur-14d-cw.json"
jq --argjson levels "$LEVELS" '.MetricDataResults[] | .Id as $id
  | {id: $id, status: .StatusCode, returned: (.Values | length), all: .Values,
     v: ([.Values[] | select(. < ($levels[$id] // infinite))] | sort)}
  | {id, status, returned, hours: (.v | length), median: .v[((.v | length) / 2 | floor)],
     p95: .v[(((.v | length) * 0.95) | floor)], max: (.all | max)}' "$RUN/m-recur-14d-cw.json"
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-data.html -->
<!-- doc: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/using-metric-math.html -->
<!-- doc: https://jqlang.org/manual/ -->

`LEVELS` is a JSON object, for example `'{"main_err": 85, "main_p99": 3.7}'`. 14 days at `Period` 3600 is 336 points per `Id`. For a filled `Id`, `returned` below 336 means the raw metric itself has no data for part of the range; a filled `Id` that comes back empty had no datapoint at all in 14 days, which is either a counter that never fired (baseline zero) or a wrong dimension, so check the identifier before reading it as zero. For an unfilled `Id` (latency, saturation), `returned` below 336 is the number of hours with traffic, and the statistics cover those hours only.

**Alarm state history, both directions.** Pull every transition, into and out of `ALARM`, for 30 days. One line per transition gives the occurrence count, the time of day of each, and the share of time spent in `ALARM`. The CLI paginates automatically. Hundreds of transitions mean the alarm flaps: classify as chronic, and say so.

**Timestamps come back in local time.** The CLI may print alarm-history timestamps with the operator machine's UTC offset (`2026-03-04T18:07:31.250000+05:30`). Convert every one to UTC before bucketing by hour; a local-time bucket shifts the "same time every day" pattern by the offset and can fake or hide a schedule. `fromdateiso8601` in jq accepts only the `Z` form, so the recipe parses the offset itself:

```bash
aws cloudwatch describe-alarm-history --profile <profile> --region <region> \
  --alarm-name "<alarm-name>" --history-item-type StateUpdate \
  --start-date "$((START_S - 30*86400))" --end-date "$END_S" --output json \
| jq -r '
  def epoch:
    capture("^(?<d>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8})(\\.[0-9]+)?(?<z>Z|[+-][0-9]{2}:?[0-9]{2})$") as $t
    | ($t.d + "Z" | fromdateiso8601)
      - (if $t.z == "Z" then 0 else
           ($t.z | capture("(?<s>[+-])(?<h>[0-9]{2}):?(?<m>[0-9]{2})")
            | ((.h | tonumber) * 3600 + (.m | tonumber) * 60) * (if .s == "+" then 1 else -1 end))
         end);
  .AlarmHistoryItems[]
  | (.Timestamp | epoch) as $u
  | [($u | todate), ($u - $u % 3600 | strftime("%H:00")), .AlarmName,
     ((.HistoryData | fromjson? | "\(.oldState.stateValue)>\(.newState.stateValue)") // .HistorySummary)]
  | @tsv' > "$RUN/alarm-history-utc.tsv"
awk -F'\t' '$4 ~ />ALARM$/ {print $2}' "$RUN/alarm-history-utc.tsv" | sort | uniq -c | sort -rn
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/describe-alarm-history.html -->
<!-- doc: https://jqlang.org/manual/ -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-parameters-types.html -->

The first column is the exact UTC time, which the ±15 min "same time of day" test needs; the second is the whole-hour bucket.

**Many siblings.** When one call per alarm would exceed the wave, make one call without `--alarm-name`, with `--max-items`, and filter on the sibling prefix in `--query`. `--max-items` limits the items read across all alarms of the account, and the prefix filter is applied only afterwards, so record the items returned and the oldest timestamp seen: anything older is a coverage gap, not an absence.

**Prometheus and Grafana alert history.** Prometheus keeps a synthetic `ALERTS` series while an alert is pending or firing; its 14-day hourly shape is a cheap occurrence history, limited by Prometheus retention:

```bash
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query=max_over_time(ALERTS{alertname="<alert>", alertstate="firing"}[1h])' \
  --data-urlencode "start=$((START_S - 14*86400))" --data-urlencode "end=$END_S" --data-urlencode "step=3600"
```
<!-- doc: https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/ -->

Grafana-managed alerts that record state history as annotations are read with the annotations API (epoch milliseconds; the default `limit` is 100, so set it explicitly and record how many items came back):

```bash
curl -sG "$GRAFANA_URL/api/annotations" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode "type=alert" --data-urlencode "from=$(( (START_S - 30*86400) * 1000 ))" \
  --data-urlencode "to=$(( END_S * 1000 ))" --data-urlencode "limit=100"
```
<!-- doc: https://grafana.com/docs/grafana/latest/developers/http_api/annotations/ -->

If state history is kept in Loki instead, query it through the logs playbook's cost ladder.

**Five-minute drill-down.** Only when three or more days share the same hour and alarm history gives no minute-level times. Put it in a wave that runs anyway. If a Fast run has used its waves, classify on the hourly data alone and state that the time-of-day match is hour-level (Likely, not Confirmed).

**Coverage.** Retention differs per backend and per server, and per-server query limits still apply. Record the coverage each source actually returned (first and last timestamp, points), not the coverage you asked for.

## Availability cross-check

**SLO burn first, if `environment.md` names an SLO.** Burn rate is the window's error ratio divided by the error budget (`1 − target`). Compute it per sibling over a short and a long window (5m and 1h): `<slo_objective>` is the SLO's target as a fraction (0.999), read from the SLO definition that `slo:` in `environment.md` points to. Both windows high means the burn is current and sustained; only the short one means a spike. The first sibling to cross gives the onset, and the set of siblings above 1 gives the blast radius. Build the ratio from summed counts over the window, never from averaged rates, and allow for the exporter's lag at the window's end.

```bash
for r in 5m 1h; do
  curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
    --data-urlencode "query=(sum by (sibling) (increase(<bad_counter>{service=\"<service>\"}[$r])) / sum by (sibling) (increase(<total_counter>{service=\"<service>\"}[$r]))) / (1 - <slo_objective>)" \
    --data-urlencode "start=$START" --data-urlencode "end=$END" --data-urlencode "step=$step" > "$RUN/m-burn-$r.json"
done
```
<!-- doc: https://prometheus.io/docs/prometheus/latest/querying/functions/ -->

The application's own 5xx ratio and the load balancer's view of the same traffic should agree. Pull both for the same window, with the load-balancer side shifted by a minute or two if the application metric lags its source.

| App 5xx / errors | LB target 5xx | Reading |
|---|---|---|
| High | High, same shape | Agreement: the 5xx claim can be labelled Confirmed. |
| High errors, low 5xx | Clean | Failures that never become 5xx (exceptions handled, `outcome=failure`, bad payloads). An application failure, not agreement. |
| Clean | LB-generated 5xx high (`HTTPCode_ELB_5XX_Count`), or unhealthy targets | The load balancer itself, or requests that never reached the application: no healthy targets, connection errors, timeouts at the LB. |

On AWS, one query file answers all three rows. Metric math treats missing values as 0, and `HTTPCode_ELB_5XX_Count` is only reported when non-zero, so a gap in it means none:

```json
[ {"Id": "req",   "ReturnData": false, "MetricStat": {"Period": 60, "Stat": "Sum",
    "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "RequestCount",
      "Dimensions": [{"Name": "LoadBalancer", "Value": "app/<lb-name>/<lb-id>"}, {"Name": "TargetGroup", "Value": "targetgroup/<tg-name>/<tg-id>"}]}}},
  {"Id": "t5xx",  "ReturnData": false, "MetricStat": {"Period": 60, "Stat": "Sum",
    "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "HTTPCode_Target_5XX_Count",
      "Dimensions": [{"Name": "LoadBalancer", "Value": "app/<lb-name>/<lb-id>"}, {"Name": "TargetGroup", "Value": "targetgroup/<tg-name>/<tg-id>"}]}}},
  {"Id": "t5xx_pct", "Expression": "100 * t5xx / req", "Label": "target 5xx %"},
  {"Id": "elb5xx", "MetricStat": {"Period": 60, "Stat": "Sum",
    "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "HTTPCode_ELB_5XX_Count",
      "Dimensions": [{"Name": "LoadBalancer", "Value": "app/<lb-name>/<lb-id>"}]}}},
  {"Id": "unhealthy", "MetricStat": {"Period": 60, "Stat": "Minimum",
    "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "UnHealthyHostCount",
      "Dimensions": [{"Name": "LoadBalancer", "Value": "app/<lb-name>/<lb-id>"}, {"Name": "TargetGroup", "Value": "targetgroup/<tg-name>/<tg-id>"}]}}},
  {"Id": "p95",   "MetricStat": {"Period": 60, "Stat": "p95",
    "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "TargetResponseTime",
      "Dimensions": [{"Name": "LoadBalancer", "Value": "app/<lb-name>/<lb-id>"}, {"Name": "TargetGroup", "Value": "targetgroup/<tg-name>/<tg-id>"}]}}} ]
```
<!-- doc: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html -->
<!-- doc: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/using-metric-math.html -->

`UnHealthyHostCount` with `Minimum` is non-zero only when every LB node counts at least one unhealthy target (not necessarily the same one). Add `TargetConnectionErrorCount` (Sum) when the third row is the candidate.

On Kubernetes, the ingress controller or service mesh plays the load balancer. For ingress-nginx the counter is `nginx_ingress_controller_requests` and the latency histogram `nginx_ingress_controller_request_duration_seconds`. The label set varies by version and configuration, so confirm the label names with `/api/v1/series` before using them; when the scrape job has `honor_labels: false`, the controller's own `namespace` label arrives renamed to `exported_namespace`. The 5xx ratio:

```bash
curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query=100 * sum(rate(nginx_ingress_controller_requests{namespace="<namespace>", ingress="<ingress>", status=~"5.."}[5m])) / sum(rate(nginx_ingress_controller_requests{namespace="<namespace>", ingress="<ingress>"}[5m]))' \
  --data-urlencode "start=$START" --data-urlencode "end=$END" --data-urlencode "step=$step"
```
<!-- doc: https://kubernetes.github.io/ingress-nginx/user-guide/monitoring/ -->
<!-- doc: https://prometheus.io/docs/prometheus/latest/configuration/configuration/ -->

Rate and latency complete the RED view; run them beside the ratio:

```bash
for q in 'sum(rate(nginx_ingress_controller_requests{namespace="<namespace>", ingress="<ingress>"}[5m]))' \
         'histogram_quantile(0.95, sum by (le) (rate(nginx_ingress_controller_request_duration_seconds_bucket{namespace="<namespace>", ingress="<ingress>"}[5m])))'; do
  curl -sG "$PROM/api/v1/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
    --data-urlencode "query=$q" --data-urlencode "start=$START" --data-urlencode "end=$END" --data-urlencode "step=$step"
done
```
<!-- doc: https://kubernetes.github.io/ingress-nginx/user-guide/monitoring/ -->
<!-- doc: https://prometheus.io/docs/prometheus/latest/querying/functions/ -->

"Requests never reached the application" on Kubernetes means no ready endpoints behind the Service. Current state only:

```bash
kubectl get endpointslices -n <namespace> -l kubernetes.io/service-name=<service> \
  -o jsonpath='{range .items[*].endpoints[*]}{.addresses[0]}{" ready="}{.conditions.ready}{" terminating="}{.conditions.terminating}{"\n"}{end}'
```
<!-- doc: https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/ -->

Rules for reading the comparison:

- Compare latency as p95 values. Two SLOs' attainment percentages are not comparable: a request-based SLO and a period-based SLO over the same traffic can disagree, and a strict-threshold sibling can be green in one and red in the other.
- An SLO usually covers one entry path. Check that it covers every ingress path the traffic uses before letting it size the impact.
- APM or span-derived request counts usually run a little below load-balancer counts. Compare ratios between the two, never totals.

## Business metrics

If `environment.md` lists `core_flows` with a counter, compare that counter for the incident window against the same window 7 days earlier, not against the previous window: hour of day, day of week and campaigns dominate business traffic. Business counters catch failures that HTTP status hides, such as a step that returns 200 with a failed outcome.

- **Two queries, not one.** Run `increase(x[W])` at the window end, and the same expression with `offset 7d`, as two separate queries. Joining them with `or` drops the right-hand series whose labels match the left side, so the −7d value silently disappears.
- **Timeline.** `increase(x[5m])` at `step=300` gives the shape.
- **Split by the counter's key dimensions** (method, channel, client version, region) when the drop is partial. One value carrying the whole drop names the failing dependency or release.
- **A business drop with healthy HTTP signals** points at application logic, a payment or other third-party dependency, or a client release, not at capacity.
- **Check the pipeline before the drop.** A counter carried by one exporter, agent or UDP path goes flat when that path breaks. Confirm the exporter is up and its own error counters are flat before reading "zero" as an outage.

```bash
for q in 'sum by (method) (increase(<flow_counter>{service="<service>"}[30m]))' \
         'sum by (method) (increase(<flow_counter>{service="<service>"}[30m] offset 7d))'; do
  curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
    --data-urlencode "query=$q" --data-urlencode "time=$END"
done
```
<!-- doc: https://prometheus.io/docs/prometheus/latest/querying/basics/ -->

Discovery when the flow has no counter named yet: the `count by (__name__)` query in [Discover identifiers first](#discover-identifiers-first) with the flow's vocabulary in the name matcher, or, on AWS, `aws cloudwatch list-metrics --namespace <custom-namespace>`. Record what you find in the profile.

## Drill-down ladder

Endpoint → dependency → host. On Kubernetes, the host step is the pod, then the node. Each rung narrows the next query; skip none.

**1. Which endpoint.** Top endpoints by 5xx responses, and separately top endpoints by the application's error counter (which also counts failures returned with a non-5xx status). Run them as two queries: adding the two vectors drops every endpoint that appears in only one of them.

```bash
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query=topk(10, sum by (route) (increase(http_requests_total{service="<service>", code=~"5.."}[30m])))' \
  --data-urlencode "time=$END"
```
<!-- doc: https://prometheus.io/docs/prometheus/latest/querying/operators/ -->

For latency, rank by the worst p95 in the window, `topk(10, max_over_time(<p95 recording rule>{service="<service>"}[30m]))`. Never add or average p95 values across endpoints or pods; a percentile of a sum is not a sum of percentiles. A top-N list can miss an endpoint, so once one is suspected, query it by name. For a latency alarm, also pull p50 and p90 of the alerting sibling beside its p95: p95 and p99 flat at one value while p50 is unchanged is a ceiling, usually a downstream timeout, not general slowness.

**2. Is it volume or speed.** Pull the suspect endpoint's own call rate per sibling, incident against baseline. Calls up with per-call latency flat means more work arrived (find the caller); calls flat with latency up means the calls got slower. Matching steps on every sibling at once usually mean one caller fanning out.

**3. Which dependency.** Dependency error rate is errors divided by calls whose outcome is known, not by all calls: calls that timed out without an outcome dilute the rate. Compare each dependency's p95 against the −7d window. Span metrics (traces playbook) and APM give the per-dependency view where the application exports none.

**4. Which host or pod.** Break 5xx and p95 down by instance. One outlier among healthy peers means a local cause (that host, that pod, that node); every peer moving together means a shared cause.

Kubernetes signals for the pod and node rung, all through Prometheus (kube-state-metrics and cAdvisor):

| Question | Expression |
|---|---|
| Restarts in the window | `sum by (pod) (increase(kube_pod_container_status_restarts_total{namespace="<namespace>"}[30m]))` |
| Last termination was OOMKilled | `max by (pod, container) (kube_pod_container_status_last_terminated_reason{namespace="<namespace>", reason="OOMKilled"})` |
| CPU throttling share | `sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{namespace="<namespace>"}[5m])) / sum by (pod) (rate(container_cpu_cfs_periods_total{namespace="<namespace>"}[5m]))` |
| Memory against limit | `max by (pod, container) (container_memory_working_set_bytes{namespace="<namespace>", container!=""}) / (max by (pod, container) (container_spec_memory_limit_bytes{namespace="<namespace>", container!=""}) > 0)` (containers without a limit drop out instead of dividing by zero) |
| Pods stuck Pending | `sum by (pod) (kube_pod_status_phase{namespace="<namespace>", phase="Pending"})` |
| HPA pinned at max | `kube_horizontalpodautoscaler_status_current_replicas{namespace="<namespace>"} >= on (namespace, horizontalpodautoscaler) kube_horizontalpodautoscaler_spec_max_replicas` |

<!-- doc: https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/pod-metrics.md -->
<!-- doc: https://github.com/kubernetes/kube-state-metrics/blob/main/docs/metrics/workload/horizontalpodautoscaler-metrics.md -->
<!-- doc: https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md -->

The current state behind those numbers, with the last termination reason and time per container:

```bash
kubectl get pods -n <namespace> -l <selector> -o json \
| jq -r '.items[] | .metadata.name as $p | .spec.nodeName as $n | .status.containerStatuses[]?
    | [$p, $n, .name, .restartCount, (.lastState.terminated.reason // "-"), (.lastState.terminated.finishedAt // "-")] | @tsv'
```
<!-- doc: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.34/#containerstatus-v1-core -->

Common AWS saturation and dependency metrics for the same rungs (CloudWatch namespace in brackets; statistic in parentheses):

| Layer | Metrics |
|---|---|
| ECS [`AWS/ECS`, `ECS/ContainerInsights`] | `CPUUtilization`, `MemoryUtilization` (Maximum and Average); `RunningTaskCount` against `DesiredTaskCount` |
| RDS / Aurora [`AWS/RDS`] | `DatabaseConnections`, `CPUUtilization`, `FreeableMemory`, `ReadLatency`, `WriteLatency`, `Deadlocks`; on burstable classes `CPUCreditBalance` |
| ElastiCache [`AWS/ElastiCache`] | `EngineCPUUtilization`, `CurrConnections`, `Evictions`, `DatabaseMemoryUsagePercentage` |
| NAT gateway [`AWS/NATGateway`] | `ErrorPortAllocation`, `PacketsDropCount`, `BytesOutToDestination` |
| SQS [`AWS/SQS`] | `ApproximateAgeOfOldestMessage`, `ApproximateNumberOfMessagesVisible`, `NumberOfMessagesSent` against `NumberOfMessagesDeleted` |
| Kinesis [`AWS/Kinesis`] | `IncomingRecords`, `GetRecords.IteratorAgeMilliseconds`, `ReadProvisionedThroughputExceeded`, `WriteProvisionedThroughputExceeded` |
| Lambda [`AWS/Lambda`] | `Errors`, `Throttles`, `Duration` (p95), `ConcurrentExecutions`, `IteratorAge` |

<!-- doc: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/aws-services-cloudwatch-metrics.html -->
<!-- doc: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-metrics-ECS.html -->

Connection pools and poolers: the "used" gauge is sampled and its ceiling is `used + free`. The real signal that a cap was hit is the failure or connect-timeout counter, not the gauge touching a line.

## GetMetricData to a table (jq)

Write each query set to a file in the run directory, one file per `Period` (`q-golden-60.json`, `q-recur-3600.json`), and pass it with `--metric-data-queries file://`. Keep the JSON output, then turn it into one row per timestamp and one column per query `Id`:

```bash
jq -r '
  def epoch:
    if type == "number" then floor else
      capture("^(?<d>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8})(\\.[0-9]+)?(?<z>Z|[+-][0-9]{2}:?[0-9]{2})$") as $t
      | ($t.d + "Z" | fromdateiso8601)
        - (if $t.z == "Z" then 0 else
             ($t.z | capture("(?<s>[+-])(?<h>[0-9]{2}):?(?<m>[0-9]{2})")
              | ((.h | tonumber) * 3600 + (.m | tonumber) * 60) * (if .s == "+" then 1 else -1 end))
           end)
    end;
  [.MetricDataResults[] | {id: .Id, pts: ([.Timestamps, .Values] | transpose
     | map({key: (.[0] | epoch | tostring), value: .[1]}) | from_entries)}] as $cols
  | ([$cols[].pts | keys[]] | unique | map(tonumber) | sort) as $ts
  | (if ($ts | length) > 0 and (($ts[0] | strftime("%F")) != ($ts[-1] | strftime("%F")))
     then "%m-%d %H:%M" else "%H:%M" end) as $fmt
  | (["utc"] + [$cols[].id] | @tsv),
    ($ts[] as $t | [($t | strftime($fmt))] + [$cols[] | (.pts[$t | tostring] // "NaN" | tostring)] | @tsv)
' "$RUN/m-golden-incident.json" | column -t
jq -e '.NextToken // empty' "$RUN/m-golden-incident.json" > /dev/null && echo "warning: output truncated (NextToken present)" >&2
jq -r '.MetricDataResults[] | select(.StatusCode != "Complete") | "\(.Id) \(.StatusCode) \([.Messages[]?.Value] | join("; "))"' "$RUN/m-golden-incident.json" >&2
```
<!-- doc: https://jqlang.org/manual/ -->
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-data.html -->

- Timestamps are printed in UTC whatever offset the CLI used. The date is added (`MM-DD`) only when the range crosses midnight UTC.
- `NaN` marks a timestamp where that query has no datapoint. Whether that means zero depends on the metric's reporting criteria (see Gotchas).
- A `NextToken` in the output means the result was cut; re-run without `--max-items` or narrow the query. A `StatusCode` other than `Complete` (`PartialData`, `Forbidden`, `InternalError`) means that column is incomplete or missing; record it as a gap, with its message.

## Gotchas

- **Identifiers differ across backends.** The service can be `checkout-api` in Prometheus labels, `checkout` in a log group name and `checkout-api-prod` in a CloudWatch dimension. Discover label values, dimension values and log group names; never build one from another. An identifier you have not seen in a discovery result stays `(unverified)` in the profile, and a query against it that returns nothing proves nothing.
- **No data is not zero.** Most empty results come from a mistyped label value, a wrong dimension or the wrong region. Check the identifier before concluding "no errors". The exception is a metric documented as reported only when non-zero (`HTTPCode_ELB_5XX_Count`, `TargetResponseTime`): there, a gap is zero. Read the metric's reporting criteria.
- **Zero is not unused.** A queue with no traffic or a function with no invocations may still be wired to a consumer, an event source mapping or a subscription. Check what consumes it, and ask the owner, before calling it dead.
- **Averages hide tails.** `TargetResponseTime` Average can stay flat while p99 doubles. Use p95/p99.
- **Never sum or average percentiles,** across pods, endpoints or siblings. Re-aggregate from histogram buckets or compare maxima.
- **No long-range quantiles.** `histogram_quantile` across days is slow and costly. Read a recording rule instead, or log the gap.
- **Sampled gauges miss bursts.** A gauge scraped every 60 s can miss a burst that filled a pool for twenty seconds. Use failure counters.
- **A failed scrape is a gap, not zero traffic.** Check `up` for the target before reading a hole as an outage.
- **Derived metrics lag their source.** An exporter or recording rule describes events a minute or two before its timestamp. Shift before lining it up with load-balancer data, logs or deploy times.
- **Units differ.** Latency may be seconds in one backend, milliseconds or microseconds in another, and alert thresholds in a third unit. Read the unit before comparing.
- **Know what an error metric counts.** Some exclude 4xx; some "error" totals include slow requests. Neither is an error rate until you have checked.
- **Top-N derived metrics miss the tail.** A per-endpoint metric built from a top-N aggregation drops rare endpoints; service-level totals stay exact.
- **Matching `__name__` by regex inside a range function** (`rate({__name__=~"a|b"}[5m])`) drops the name, which can leave duplicate label sets and fail the query. Query each metric by name.
- **`or` and arithmetic drop series.** Binary operators keep only matching label sets; `or` adds right-hand series only where no left-hand series has the same labels.
- **High-cardinality selectors need `by (...)`.** An unaggregated selector over a per-pod or per-path metric can return thousands of series.
- **Never fetch an exporter's endpoint directly** when its scrape itself runs expensive queries. Read the scraped series from Prometheus.

## What to write in the ledger

One row per query:

- query ID, backend, and the exact expression or query file name;
- window in UTC, step or `Period`, and which of the three windows it is;
- CloudWatch metric requests spent, against the budget;
- coverage actually returned (first and last timestamp, datapoints, `NaN` count);
- the result in one line, with its confidence label;
- every identifier used, marked verified or `(unverified)`;
- a deeplink for a human: a Grafana Explore link with the datasource UID, the exact query and the fixed window, or the CloudWatch console link for the same metrics.

Recurrence adds: the statistic used per signal, median/p95/max of the 14-day hourly values, the alarm transitions in UTC, the coverage of alarm history, and the classification with its reason.
