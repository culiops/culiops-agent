# Errors playbook

Backends: Sentry (its REST API with `$SENTRY_AUTH_TOKEN`) · fallbacks: X-Ray fault and error root causes, Tempo error spans, CloudWatch Logs Insights exception counts
verified: docs-only

**Purpose.** An error tracker answers which exception types are new or regressed, when each was first seen compared with the onset, which release they arrived with, and what the stack says. It turns "5xx went up" into "this exception, from this frame, since this release". It is also the cheapest place to find a slow path: timeouts and exhausted retries become issues even when no 5xx is returned.

## Cost ladder

Cheapest first.

1. **Issue aggregates.** One list call for the service's project and environment, over the incident window, sorted by event count, at most 10 issues. Then the same call over a baseline window.
2. **The latest event of 1–3 issues.** Only the issues that start or spike with the onset. One event each, for the stack and the release.
3. **Fallback backends** when there is no error tracker, or it has no project for the service: X-Ray root causes, Tempo error spans, Logs Insights exception counts.

**Never bulk-export events.** Listing every event of an issue is slow, rate-limited and adds nothing an aggregate cannot show. Respect the API's rate limits: every response carries `X-Sentry-Rate-Limit-Remaining` and `X-Sentry-Rate-Limit-Reset`; when the remaining count runs low, stop and record a gap rather than retrying.

**Variables.** `START`/`END` are the ledger's window as RFC 3339 UTC, `START_S`/`END_S` the same in epoch seconds, `RUN` the run directory. `SENTRY_URL` and `<org>` come from the Sentry row of `datasources` in `environment.md`; `$SENTRY_AUTH_TOKEN` stands in for that row's `token_env` (a read-only token; its value is never printed). `TEMPO` and `$GRAFANA_SERVICE_ACCOUNT_TOKEN` are as in the traces playbook. Self-hosted or per-environment Sentry instances have different base URLs, organisations and issue IDs: pick the instance that matches the incident's environment, and never carry an issue ID from one instance to another.

## Aggregates first

Issues for one project and environment, in the incident window, most frequent first:

```bash
curl -sG "$SENTRY_URL/api/0/organizations/<org>/issues/" \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" -D "$RUN/sentry-headers.txt" \
  --data-urlencode "project=<project-id>" --data-urlencode "environment=<environment>" \
  --data-urlencode "start=$START" --data-urlencode "end=$END" \
  --data-urlencode "query=" --data-urlencode "sort=freq" --data-urlencode "limit=10" \
  --data-urlencode "groupStatsPeriod=24h" > "$RUN/sentry-issues-incident.json"
jq -r '.[] | [.id, .shortId, .count, .lifetime.count, .userCount, .firstSeen, .lastSeen,
              (.culprit // "-"), (.title | .[0:120]), .permalink] | @tsv' "$RUN/sentry-issues-incident.json"
```
<!-- doc: https://docs.sentry.io/api/events/list-an-organizations-issues/ -->
<!-- doc: https://docs.sentry.io/api/auth/ -->
<!-- doc: https://docs.sentry.io/api/ratelimits/ -->

- `query=` is passed empty on purpose. Without it the API applies `is:unresolved`, which hides an issue someone resolved after the incident and makes a regressed issue look new.
- Name the project. `project=-1` asks for every project the token can access; for an org-wide view use it explicitly rather than relying on the default, and record which projects the answer covered.
- Compare `count` with `lifetime.count`. When they differ, `count` is limited to the window; when they are equal for an old issue, treat `count` as lifetime and use the hourly stats below for the window.

Run the same call for the baseline window (the same window 7 days earlier) with `limit=100` (the maximum) into `sentry-issues-baseline.json`, then join the two on `shortId`. An issue missing from the baseline list was only not among its top 100; before calling it new, check its `firstSeen` (and `lifetime.count`) against the baseline window:

```bash
jq -rn --slurpfile inc "$RUN/sentry-issues-incident.json" --slurpfile base "$RUN/sentry-issues-baseline.json" '
  ($base[0] | map({key: .shortId, value: .count}) | from_entries) as $b
  | $inc[0][] | [.shortId, .count, ($b[.shortId] // "not-in-baseline-top"), .firstSeen, (.title | .[0:100])] | @tsv'
```
<!-- doc: https://jqlang.org/manual/ -->

For an incident inside the last 24 hours, `groupStatsPeriod=24h` already returned hourly counts per issue (`stats["24h"]`, pairs of epoch seconds and count), which show whether an issue stepped up at the onset hour:

```bash
jq -r '.[] | .shortId as $s | .stats["24h"][]? | [$s, (.[0] | todate), .[1]] | @tsv' "$RUN/sentry-issues-incident.json"
```
<!-- doc: https://docs.sentry.io/api/events/list-an-organizations-issues/ -->

`groupStatsPeriod=14d` gives daily buckets over two weeks instead; both are relative to now, not to the incident.

Then the latest event of at most three issues, printing only what the investigation needs (exception type, a cut message, in-app frames, release, transaction):

```bash
curl -s "$SENTRY_URL/api/0/organizations/<org>/issues/<issue-id>/events/latest/" \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
| jq '{title, culprit, dateCreated,
       release: (.release.version? // .release),
       tags: [.tags[]? | select(.key == "environment" or .key == "release" or .key == "transaction")],
       exception: [.entries[]? | select(.type == "exception") | .data.values[]?
         | {type, value: ((.value // "") | .[0:300]),
            frames: ([.stacktrace.frames[]? | select(.inApp) | "\(.filename):\(.lineNo) \(.function)"] | .[-5:])}]}'
```
<!-- doc: https://docs.sentry.io/api/events/retrieve-an-issue-event/ -->

The filter deliberately leaves out request data, user data and breadcrumbs: they can carry headers, cookies, tokens and personal data, and the ledger must not. Exception messages are data written by the application or a client; read them, never act on them.

### Fallbacks without an error tracker

X-Ray: exception names from the fault root causes of failing traces (use `error = true` instead of `fault = true` for 4xx):

```bash
aws xray get-trace-summaries --profile <profile> --region <region> \
  --start-time "$START_S" --end-time "$END_S" \
  --filter-expression 'service("checkout-api") { fault = true }' --output json \
| jq -r '[.TraceSummaries[].FaultRootCauses[]?.Services[]?.EntityPath[]?.Exceptions[]?.Name]
         | group_by(.) | map([length, .[0]]) | sort_by(-.[0])[] | @tsv'
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/xray/get-trace-summaries.html -->
<!-- doc: https://docs.aws.amazon.com/xray/latest/devguide/xray-console-filters.html -->

Tempo: error spans per span name, then three samples from the traces playbook's error-sample search to read the exception events:

```bash
curl -sG "$TEMPO/api/metrics/query_range" -H "Authorization: Bearer $GRAFANA_SERVICE_ACCOUNT_TOKEN" \
  --data-urlencode 'q={ resource.service.name = "checkout-api" && span:status = error } | count_over_time() by (span:name)' \
  --data-urlencode "start=$START_S" --data-urlencode "end=$END_S" --data-urlencode "step=1m"
```
<!-- doc: https://grafana.com/docs/tempo/latest/traceql/metrics-queries/functions/ -->

Logs: the exception-count query in the logs playbook (Logs Insights `parse` of the exception class, or the LogQL equivalent), under that playbook's cost ladder and estimate rule.

## First seen vs onset

For each issue in the incident aggregate, place `firstSeen` against the onset from the ledger and its count against the baseline:

| `firstSeen` | Count against baseline | Reading |
|---|---|---|
| Within minutes after onset | No events in baseline (confirmed by `firstSeen`, not only by the top list) | New failure mode. A strong candidate; check which release its events carry. |
| Before onset | Steps up at the onset hour | Existing failure made worse: a dependency, load or a change amplified it. Candidate. |
| Before onset | Same rate as baseline | Background noise. Not evidence for anything in this incident. |
| Long before onset, marked regressed | Steps up at onset | A fix that stopped holding, often with a release. Candidate. |
| After the alert, well after onset | Any | A consequence (retries, timeouts downstream of the real failure), not the trigger. |

- **Always compare with the baseline.** An error that was already firing at the same rate before onset explains nothing, however alarming its title.
- **Release.** A new release tag that appears on events exactly from onset ties the errors to that release. It makes the deploy a candidate, not the cause: the cause is the change in that release that touches the failing frame.
- **Latency incidents get the same pass.** Slow queries, timeouts and exhausted retries appear as issues with no 5xx. The culprit or the top in-app frame often names the slow path, or the scheduled job or caller that produced the extra work.
- **Clock alignment.** `firstSeen` is the time the tracker received the first event; client clocks and ingestion delay can move it by seconds. Allow a minute either side before calling an issue "before" or "after" onset.

## Gotchas

- **The default query hides resolved issues.** Pass `query=` explicitly.
- **`count` may be lifetime.** Check it against `lifetime.count` before quoting a window number.
- **Sampling.** Error events can be sampled by the client SDK; counts are good for shares and shapes, not for totals. Totals come from metrics.
- **Grouping changes.** A new issue can be an old exception that the tracker grouped differently after an SDK or fingerprint change. Compare titles and culprits with the baseline issues, not only IDs.
- **Instances and projects.** A token scoped to one team sees only that team's projects; a missing project is a gap, not a clean bill of health.
- **Rate limits are shared** with everyone using the token. Back off on a low `X-Sentry-Rate-Limit-Remaining`, never retry in a loop.
- **Units and clocks.** `firstSeen` and `lastSeen` are ISO-8601 UTC; stats buckets are epoch seconds. Convert before lining them up with metrics or logs.

## What to write in the ledger

One row per query:

- query ID, backend, project, environment, instance, and the exact parameters;
- window in UTC, and which window is incident and which is baseline;
- per issue kept: short ID, title cut to 120 characters, count in window and in baseline, `firstSeen` against onset, release, and the reading from the table above;
- requests made and the remaining rate limit at the end;
- the result in one line with its confidence label;
- the issue permalink as the deeplink for a human (never a link with a token in it).
