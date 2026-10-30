# Other backends (mapped)

Backends: Datadog · New Relic · Elastic APM
verified: docs-only

**Purpose.** These backends are mapped, not first-class: the method of the metrics, logs, traces, errors and changes playbooks applies unchanged, and the tables below translate each signal to where it lives and an equivalent query. Windows are the ledger's UTC window; tokens come from the `token_env` named in `environment.md` (names only; the examples use stand-in names). X-Ray is first-class and lives in the traces playbook.

## Datadog

Queries go to the site's API host (`https://api.<site>`, for example `api.datadoghq.com` or `api.datadoghq.eu`). Reads need the API key in the `DD-API-KEY` header and an application key in `DD-APPLICATION-KEY` (or a bearer access token), both from env vars: `curl -sG "https://api.<site>/api/v1/query" -H "DD-API-KEY: ${<DD_API_KEY_ENV>}" -H "DD-APPLICATION-KEY: ${<DD_APP_KEY_ENV>}" --data-urlencode "from=$START_S" --data-urlencode "to=$END_S" --data-urlencode 'query=<query>'`. The logs aggregate call is a `POST` that only reads.

| Signal | Where | Equivalent query | Gotcha |
|---|---|---|---|
| Rate and errors per endpoint | APM trace metrics `trace.<span_name>.hits` and `.errors` (counts) | `sum:trace.<span_name>.errors{service:<service>,env:<env>} by {resource_name,http.status_code}.as_count()` | Trace metrics are computed from all traffic before ingestion sampling, except with OpenTelemetry SDK or app-side sampling, where they are sampled too. |
| Latency percentiles | Distribution metric `trace.<span_name>` | `p95:trace.<span_name>{service:<service>,env:<env>}` | Use the distribution; `trace.<span_name>.duration` is a legacy gauge. Never average percentiles across tags. |
| Log counts and patterns | Logs aggregate API, `POST /api/v2/logs/analytics/aggregate` | body: `filter.query` `service:<service> status:error`, `filter.from`/`to` in epoch ms, `compute` `count`, `group_by` a facet with a `limit` | Indexed logs only; the product of `group_by` limits may not exceed 10,000. |
| Deploys | The `version` tag (unified service tagging) on trace metrics, traces and logs | `sum:trace.<span_name>.hits{service:<service>,env:<env>} by {version}.as_count()` | A version that is not tagged is invisible here; fall back to the changes playbook. |

<!-- doc: https://docs.datadoghq.com/api/latest/metrics/query-timeseries-points.md -->
<!-- doc: https://docs.datadoghq.com/logs/guide/access-your-log-data-programmatically/ -->
<!-- doc: https://docs.datadoghq.com/tracing/metrics/metrics_namespace/ -->
<!-- doc: https://docs.datadoghq.com/api/latest/logs/aggregate-events.md -->
<!-- doc: https://docs.datadoghq.com/tracing/services/deployment_tracking/ -->

## New Relic

NRQL is sent through NerdGraph: `POST https://api.newrelic.com/graphql` (EU: `api.eu.newrelic.com`) with the user key in the `API-Key` header and the body `{ actor { account(id: <account-id>) { nrql(query: "<NRQL>") { results } } } }`. Quoted datetimes in `SINCE`/`UNTIL` are UTC unless they carry an offset.

| Signal | Where | Equivalent query | Gotcha |
|---|---|---|---|
| Latency and throughput per endpoint | `Transaction` events | `SELECT percentile(duration, 95), count(*) FROM Transaction WHERE appName = '<service>' FACET name SINCE '<START>' UNTIL '<END>' TIMESERIES 1 minute` | `duration` is in seconds. Transaction events are sampled per agent harvest, so read ratios and shapes here and totals from metric data. |
| Errors by type | `TransactionError` events | `SELECT count(*) FROM TransactionError WHERE appName = '<service>' FACET error.class SINCE '<START>' UNTIL '<END>'` | Errors can be configured as ignored or expected, so counts do not match failed transactions. |
| Queries per request, slow downstream | `Transaction` attributes `databaseCallCount`, `databaseDuration`, `externalDuration` | `SELECT average(databaseCallCount), percentile(databaseDuration, 95), percentile(externalDuration, 95) FROM Transaction WHERE appName = '<service>' FACET name SINCE '<START>' UNTIL '<END>'` | Durations in seconds (Elastic uses microseconds): state the unit with every number. |
| Deploys and changes | `Deployment` and `ChangeTrackingEvent` events | `FROM Deployment, ChangeTrackingEvent SELECT entity.name, version, timestamp SINCE '<START>' UNTIL '<END>'` | Only changes someone recorded; an unrecorded deploy needs the changes playbook. |

<!-- doc: https://docs.newrelic.com/docs/apis/nerdgraph/get-started/introduction-new-relic-nerdgraph/ -->
<!-- doc: https://docs.newrelic.com/docs/apis/nerdgraph/examples/nerdgraph-nrql-tutorial/ -->
<!-- doc: https://docs.newrelic.com/docs/nrql/nrql-syntax-clauses-functions/ -->
<!-- doc: https://docs.newrelic.com/docs/query-your-data/nrql-new-relic-query-language/get-started/introduction-nrql-tutorial/ -->
<!-- doc: https://docs.newrelic.com/docs/data-apis/understand-data/event-data/new-relic-event-limits-sampling/ -->
<!-- doc: https://docs.newrelic.com/docs/data-apis/understand-data/event-data/events-reported-apm/ -->
<!-- doc: https://docs.newrelic.com/docs/change-tracking/change-tracking-view-analyze/ -->

## Elastic APM

ES|QL goes to `POST <elasticsearch-url>/_query` with `Authorization: ApiKey $<ENV_VAR>` and the query in the `query` field. Every query below starts with `FROM <data stream>` and a filter on `@timestamp >= "<START>" AND @timestamp < "<END>"`, shown here as `…`.

| Signal | Where | Equivalent query | Gotcha |
|---|---|---|---|
| Latency per endpoint | `traces-apm*`, transaction documents | `FROM traces-apm* \| WHERE service.name == "<service>" AND processor.event == "transaction" AND … \| STATS p95 = PERCENTILE(transaction.duration.us, 95), n = COUNT(*) BY transaction.name` | Microseconds. With head-based sampling, latency and throughput are estimated from sampled events only; with tail-based sampling they come from all events. |
| Errors by group | `logs-apm.error-*` | `FROM logs-apm.error-* \| WHERE service.name == "<service>" AND … \| STATS n = COUNT(*) BY error.grouping_key, error.exception.type` | Compare with the baseline window before calling a group new. |
| Slow downstream | `traces-apm*`, span documents | `FROM traces-apm* \| WHERE service.name == "<service>" AND processor.event == "span" AND … \| STATS p95 = PERCENTILE(span.duration.us, 95), n = COUNT(*) BY span.destination.service.resource` | Spans of unsampled traces are dropped, so span counts are not totals. |
| Deploys | `service.version` on transactions and errors | `FROM traces-apm* \| WHERE service.name == "<service>" AND … \| STATS n = COUNT(*) BY service.version, minute = BUCKET(@timestamp, 1 minute)` | The version must be set by the agent; otherwise use the changes playbook. |

<!-- doc: https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-esql-query -->
<!-- doc: https://www.elastic.co/docs/solutions/observability/apm/data-streams -->
<!-- doc: https://www.elastic.co/guide/en/apm/server/current/exported-fields-apm-transaction.html -->
<!-- doc: https://www.elastic.co/guide/en/apm/server/current/exported-fields-apm-span.html -->
<!-- doc: https://www.elastic.co/guide/en/apm/server/current/exported-fields-apm-error.html -->
<!-- doc: https://www.elastic.co/docs/reference/query-languages/esql/functions-operators/grouping-functions/bucket -->
<!-- doc: https://www.elastic.co/guide/en/observability/8.19/apm-sampling.html -->
