# Traces playbook

Backends: Tempo (its HTTP API, the Grafana datasource proxy, or a Grafana MCP server) · span metrics in Prometheus (Tempo metrics-generator) · X-Ray (AWS CLI)
verified: docs-only

**Purpose.** Traces answer which endpoints are slow or failing, where the time inside a slow request goes (database, HTTP dependency, cache, local work), which error types belong to which transaction, and what an individual bad request looked like. They are sampled, so they are best at ratios, shapes and breakdowns; totals come from the metrics playbook.

## Cost ladder

Cheapest first.

1. **Span metrics or RED recording rules.** If the org runs Tempo's metrics-generator (or an equivalent), per-endpoint and per-dependency rate, errors and duration already sit in Prometheus as `traces_spanmetrics_calls_total` and the `traces_spanmetrics_latency` histogram, labelled by default with `service`, `span_name`, `span_kind` and `status_code`. Query them like any metric.
2. **Trace aggregations.** TraceQL metrics on Tempo; grouped trace summaries on X-Ray. One aggregation answers what twenty samples would only hint at.
3. **Samples.** Search for at most 20–30 traces matching a narrow filter in a narrow window, then fetch a few by ID.
4. **Single traces.** One trace by ID, to read the waterfall of a request already known to be representative.

**Always filter on time range and service name.** Never search without a service, and never with a leading wildcard.

**Caps.** Windows come from `budgets.windows` in `environment.md`: `trace_aggregation` (default 24h) and `trace_samples` (default 1h). Also keep the timeline step at 1 min or more (5 min past 6h) and group on at most 20 values. X-Ray bills traces retrieved and scanned, so its windows stay at the incident plus one baseline.

**Variables.** `START_S`/`END_S` are the ledger's window in epoch seconds, `RUN` the run directory. `TEMPO` is the Tempo base URL or `$GRAFANA_URL/api/datasources/proxy/uid/<datasource-uid>`; `PROM` likewise for Prometheus. `$GRAFANA_SERVICE_ACCOUNT_TOKEN` stands in for the `token_env` named in `environment.md`. A Grafana MCP server takes the same TraceQL strings.

**Confirm the service name first.** Trace service names are case-sensitive exact strings and wildcards match nothing. Ask Tempo which names exist in the window; if the expected one is absent, a search for slow traces without a service filter, limited to a few results, shows what the service is actually called.

```bash
curl -sG "$TEMPO/api/v2/search/tag/resource.service.name/values" \
  -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode "start=$START_S" --data-urlencode "end=$END_S" | jq -r '.tagValues[].value'
```
<!-- doc: https://grafana.com/docs/tempo/latest/api_docs/ -->

Note that this endpoint ignores an invalid `q` filter and returns the unfiltered list without an error; check your filter if the list looks too long.

## Latency per endpoint

p95 and failures per endpoint for the service, then a one-minute timeline of the worst ones.

Span metrics (cheapest). `span_kind` takes the values `SPAN_KIND_SERVER`, `SPAN_KIND_CLIENT`, `SPAN_KIND_INTERNAL`, `SPAN_KIND_PRODUCER` and `SPAN_KIND_CONSUMER`; filter on the server kind so outgoing calls are not ranked as endpoints:

```bash
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query=topk(10, histogram_quantile(0.95, sum by (le, span_name) (rate(traces_spanmetrics_latency_bucket{service="checkout-api", span_kind="SPAN_KIND_SERVER"}[30m]))))' \
  --data-urlencode "time=$END_S"
```
<!-- doc: https://grafana.com/docs/tempo/latest/metrics-from-traces/span-metrics/span-metrics-metrics-generator/ -->
<!-- doc: https://prometheus.io/docs/prometheus/latest/querying/functions/ -->

TraceQL metrics, p95 and error rate per server span name, one-minute step:

```bash
for q in '{ resource.service.name = "checkout-api" && span:kind = server } | quantile_over_time(span:duration, .95) by (span:name)' \
         '{ resource.service.name = "checkout-api" && span:kind = server && span:status = error } | rate() by (span:name)'; do
  curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
    --data-urlencode "q=$q" --data-urlencode "start=$START_S" --data-urlencode "end=$END_S" --data-urlencode "step=1m"
done
```
<!-- doc: https://grafana.com/docs/tempo/latest/traceql/metrics-queries/functions/ -->
<!-- doc: https://grafana.com/docs/tempo/latest/api_docs/ -->

X-Ray: first list the service names X-Ray knows in the window (the name in `service("...")` is the segment name, often not the metrics or log identifier):

```bash
aws xray get-service-graph --profile <profile> --region <region> \
  --start-time "$START_S" --end-time "$END_S" --query 'Services[].[Name,Type]' --output text
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/xray/get-service-graph.html -->

Then group the trace summaries locally:

```bash
aws xray get-trace-summaries --profile <profile> --region <region> \
  --start-time "$START_S" --end-time "$END_S" \
  --filter-expression 'service("checkout-api")' --output json > "$RUN/xr-summaries.json"
jq -r '
  [.TraceSummaries[]
   | {ep: ((.Http.HttpMethod // "-") + " " + ((.Http.HttpURL // "-")
           | sub("^https?://[^/]+"; "") | sub("\\?.*$"; "") | gsub("/[0-9]+"; "/N"))),
      rt: .ResponseTime, fault: (.HasFault // false)}]
  | group_by(.ep)
  | map({ep: .[0].ep, n: length, faults: (map(select(.fault)) | length),
         p95_s: (map(.rt) | sort | .[((length * 0.95) | floor)])})
  | sort_by(-.p95_s) | .[:10][] | [.ep, .n, .faults, .p95_s] | @tsv' "$RUN/xr-summaries.json"
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/xray/get-trace-summaries.html -->
<!-- doc: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html -->

Numeric path segments are folded to `/N` so that one endpoint is not split into thousands of URLs. X-Ray durations are seconds. For a per-minute X-Ray timeline, use the load balancer or application metrics; summaries are a sample.

Once the slow endpoint is known, check its own call rate (metrics playbook, drill-down rung 2) before reading its latency as "got slower": the same p95 with twice the calls is a volume problem.

## Slow downstream

Which dependency the slow requests wait on.

Tempo, client spans of the service grouped by name (a client span is an outgoing call: database statement, HTTP request, cache command):

```bash
curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'q={ resource.service.name = "checkout-api" && span:kind = client } | quantile_over_time(span:duration, .95) by (span:name)' \
  --data-urlencode "start=$START_S" --data-urlencode "end=$END_S" --data-urlencode "step=1m"
```
<!-- doc: https://grafana.com/docs/tempo/latest/traceql/metrics-queries/functions/ -->

With span metrics instead, use the same p95 query as for endpoints with `span_kind="SPAN_KIND_CLIENT"` and `by (le, span_name)`. Run the TraceQL query with `| rate() by (span:name)` beside it: a dependency whose p95 is flat but whose call rate jumped is a volume or fan-out problem, not a slow dependency. Group by `span.db.system` or by the peer attribute your instrumentation sets when span names are too fine-grained; discover the attribute with the tag-values endpoint first.

X-Ray, the services that X-Ray itself names as the response-time root cause of slow traces:

```bash
aws xray get-trace-summaries --profile <profile> --region <region> \
  --start-time "$START_S" --end-time "$END_S" \
  --filter-expression 'service("checkout-api") AND responsetime > <seconds>' --output json \
| jq -r '[.TraceSummaries[].ResponseTimeRootCauses[]?.Services[]?
          | "\(.Name) [\(.Type // "-")]"] | group_by(.) | map([length, .[0]]) | sort_by(-.[0])[] | @tsv'
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/xray/get-trace-summaries.html -->

## Queries per request (N+1)

A request can get slow without any single call getting slow: it makes more calls. The test is the number of database (or other dependency) spans per request for the slow endpoint, compared between the incident window and a baseline window.

- **Incident against baseline.** Same endpoint, same filter, two windows: the incident and the same window 7 days earlier (or the previous equal window if the code changed this week).
- **At least 20 samples per window.** Span counts vary between requests of one endpoint (cache hits, pagination, feature flags). Fewer than 20 traces per window is not enough to say "more spans", and never enough to say "the DB is not traced".
- **Read p50, p95 and max** of spans per trace, not the mean.
- **Many spans, each as fast as before, is N+1.** A flat DB p95 does not rule out the DB: forty fast queries cost more than four. The dependency is not cleared until the span count is also flat.

Aggregate first, with span metrics: dependency calls per endpoint call, incident against −7d (run once as written, once with `offset 7d` inside both range selectors):

```bash
curl -sG "$PROM/api/v1/query" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'query=sum(increase(traces_spanmetrics_calls_total{service="checkout-api", span_name=~"<db span name pattern>"}[30m])) / sum(increase(traces_spanmetrics_calls_total{service="checkout-api", span_name="<endpoint span name>"}[30m]))' \
  --data-urlencode "time=$END_S"
```
<!-- doc: https://grafana.com/docs/tempo/latest/metrics-from-traces/span-metrics/span-metrics-metrics-generator/ -->

This ratio is service-wide, so it only points at the endpoint when that endpoint dominates the dependency calls. Confirm per request with samples.

Tempo samples: up to 30 traces of the endpoint per window, each fetched by ID, counting spans that carry a `db.system` attribute (older semantic conventions) or `db.system.name` (newer ones); if your instrumentation marks database spans differently, discover the attribute with the tag-values endpoint first:

```bash
for w in "incident $START_S $END_S" "baseline $((START_S - 604800)) $((END_S - 604800))"; do
  read -r win ws we <<< "$w"
  curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
    --data-urlencode 'q={ resource.service.name = "checkout-api" && span:kind = server && span:name = "<endpoint span name>" }' \
    --data-urlencode "start=$ws" --data-urlencode "end=$we" --data-urlencode "limit=30" \
  | jq -r '.traces[].traceID' > "$RUN/tr-ids-$win.txt"
  while read -r id; do
    curl -sG "$TEMPO/api/v2/traces/$id" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
      --data-urlencode "start=$(( ws - 3600 ))" --data-urlencode "end=$(( we + 3600 ))" \
    | jq -c --arg w "$win" --arg id "$id" \
        '{w: $w, id: $id, db: ([.. | objects | select((has("spanId") or has("spanID")) and any(.attributes[]?; .key | startswith("db.system")))] | length)}'
  done < "$RUN/tr-ids-$win.txt"
done | tee "$RUN/tr-db-spans.jsonl" \
| jq -s 'group_by(.w) | map((map(.db) | sort) as $v
    | {window: .[0].w, traces: ($v | length), p50: $v[(($v | length) / 2 | floor)],
       p95: $v[((($v | length) * 0.95) | floor)], max: ($v | max)})'
```
<!-- doc: https://grafana.com/docs/tempo/latest/api_docs/ -->
<!-- doc: https://jqlang.org/manual/ -->

The trace fetch is padded by an hour on each side because Tempo only searches the blocks inside `start`/`end` and can return a partial trace otherwise. To find the heaviest requests directly, TraceQL can count matching spans within one trace: `{ resource.service.name = "checkout-api" && span.db.system =~ ".+" } | count() > 25`.
<!-- doc: https://grafana.com/docs/tempo/latest/traceql/construct-traceql-queries/ -->

X-Ray samples: up to 30 trace IDs per window, fetched five at a time (the API limit), counting subsegments that carry an `sql` block:

```bash
aws xray get-trace-summaries --profile <profile> --region <region> \
  --start-time "$START_S" --end-time "$END_S" \
  --filter-expression 'service("checkout-api") AND http.url CONTAINS "<path>"' \
  --max-items 30 --query 'TraceSummaries[].Id' --output text | tr '\t' '\n' > "$RUN/xr-ids-incident.txt"
xargs -n 5 aws xray batch-get-traces --profile <profile> --region <region> --output json --trace-ids \
  < "$RUN/xr-ids-incident.txt" \
| jq -s '[.[].Traces[] | {id: .Id, sql: ([.Segments[].Document | fromjson | .. | objects | select(has("sql"))] | length)}]
         | (map(.sql) | sort) as $v | {traces: ($v | length), p50: $v[(($v | length) / 2 | floor)],
           p95: $v[((($v | length) * 0.95) | floor)], max: ($v | max)}'
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/xray/batch-get-traces.html -->
<!-- doc: https://docs.aws.amazon.com/xray/latest/api/API_BatchGetTraces.html -->
<!-- doc: https://docs.aws.amazon.com/xray/latest/devguide/xray-api-segmentdocuments.html -->

Repeat with the baseline window. Segment documents arrive as JSON strings, hence `fromjson`; subsegments nest, hence the recursive `..`. HTTP or cache fan-out is counted the same way with `select(.namespace == "remote")`.

## Error samples

After the aggregates, pull a few failing requests to read: at most 20, narrow window, failure filter.

```bash
curl -sG "$TEMPO/api/search" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'q={ resource.service.name = "checkout-api" && (span:status = error || span:duration > 1500ms) }' \
  --data-urlencode "start=$START_S" --data-urlencode "end=$END_S" --data-urlencode "limit=20" \
| jq -r '.traces[] | [.traceID, .rootTraceName, .durationMs] | @tsv'
```
<!-- doc: https://grafana.com/docs/tempo/latest/traceql/construct-traceql-queries/ -->
<!-- doc: https://grafana.com/docs/tempo/latest/api_docs/ -->

On X-Ray, the same with `--filter-expression 'service("checkout-api") { fault = true }'` and `--max-items 20`. Error types grouped per transaction belong to the errors playbook.

## Gotchas

- **Sampling means ratios, not totals.** A trace backend sees a fraction of requests, often with a different fraction for errors. Use trace counts for shares, shapes and breakdowns; quote totals from load-balancer or application metrics, and check the trace counts' shape against `RequestCount` before trusting it.
- **Units differ per backend and per field.** X-Ray durations are seconds. Tempo search results give `durationMs` for a trace and `durationNanos` for a span; TraceQL takes durations with units (`2s`, `100ms`). Span-metric histograms are in seconds. Other APMs use microseconds. Convert before comparing with an alarm threshold.
- **Service names are exact.** Case-sensitive, no wildcards, and often different from the metrics or log identifier for the same service. Discover, record in the profile, and mark `(unverified)` until a query has returned it.
- **Fewer than 20 samples proves nothing** about span counts, and an absent span type in a few traces does not mean the dependency is untraced.
- **A partial trace looks like a fast trace.** Fetch by ID with a padded window, and treat a trace whose root span is missing as incomplete.
- **X-Ray Transaction Search.** When it is enabled, `batch-get-traces` cannot find traces, because they are not indexed in X-Ray. Record a gap and use the CloudWatch side instead.
- **Trace timestamps are span start times.** A request that started before onset can carry the failure that defines it; widen the sample window by the request's own duration.

## What to write in the ledger

One row per query:

- query ID, backend, the exact TraceQL, PromQL or X-Ray filter expression;
- window in UTC, and for comparisons which window is incident and which is baseline;
- sample size per window, and whether it reached 20;
- the result in one line with its unit, with its confidence label (a sampled ratio is at best Likely until metrics agree);
- the service name used, verified or `(unverified)`;
- deeplinks for a human: a Grafana Explore link with the trace datasource UID and query, the Tempo trace view for each trace ID quoted, or the X-Ray console link for the trace.
