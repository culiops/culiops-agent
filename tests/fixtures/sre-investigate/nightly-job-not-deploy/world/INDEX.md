# World index

## Matching rules

1. A pattern names the command words and the arguments that pick the row. Any other flags and arguments may come anywhere, in any order; `…` marks where they usually sit, and `*` inside a value matches any text.
2. `--profile`, `--region`, `--output`, `--query`, `--no-cli-pager`, `--color`, and kubectl's `-o`/`--sort-by`/`--field-selector` do not change which row matches, unless the row says so. A profile may be given as `--profile p`, `--profile=p` or `AWS_PROFILE=p`. Where a row needs an output format (`-o json`), it says so.
3. kubectl: the namespace may be given as `-n ns` or `--namespace ns`, before or after the verb. Resource kinds match their short, singular and plural names (`po`/`pod`/`pods`, `rs`/`replicaset`/`replicasets`, `deploy`/`deployment`).
4. Time windows: a row whose Notes give a covered window matches any request whose window overlaps it. Return only the points or rows inside the requested window (and sum them when the request asks for a coarser period or no time bin). A request whose window overlaps no row's window gets the default for its kind.
5. Query text (PromQL, LogQL, TraceQL, Logs Insights): a query matches when it asks for the same metric or fields with the same selectors, whatever the spelling (`0.5` = `0.50`, label order, whitespace, `sum by (le) (…)` = `sum(…) by (le)`), whether it is sent with `curl`, a CLI or an MCP tool.
6. The first matching row wins.
7. Defaults: an unmatched JSON API call returns `_default.txt` (`{}`); an unmatched text command (`kubectl`, `helm`, `git`, `grep`, `command -v`, `echo`) returns `_empty.txt` (no output, exit status 0 unless a row says otherwise). `cat` or `ls` of a path that no row names prints `No such file or directory` with exit status 1.

## Rows

`<…>` in a pattern is a parameter: the value comes from an earlier output, and the row's table (below the main table) gives the file for each value. A value not in the table returns the default for its kind.

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls` … `.culiops/sre-investigate` | `ls-01.txt` | |
| `command -v agentbox-env` | `_empty.txt` | Exit status 1. |
| `aws sts get-caller-identity` | `sts-01.json` | |
| `aws iam get-role` … `<role name from sts-01.json>` | `iam-01.json` | |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `aws cloudwatch describe-alarms` … | `cw-01.json` | Any name, prefix or state filter that includes this alarm; no filter returns the same. |
| `aws cloudwatch describe-alarm-history` … | `cw-02.json` | All history items the API returns for the account's alarms. |
| `aws cloudwatch list-metrics` … `AWS/ApplicationELB` | `cw-05.json` | |
| `aws cloudwatch get-metric-data` or `get-metric-statistics` … `HTTPCode_Target_5XX_Count`, period 86400 or more | `cw-06.json` | Sum, period 86400. Covers 2026-10-07 – 2026-10-21 (last day partial, to 02:40 UTC). |
| `aws cloudwatch get-metric-data` or `get-metric-statistics` … `HTTPCode_Target_5XX_Count`, period 3600 to 86399 | `cw-03.json` | Sum, period 3600. Covers 2026-10-07 00:00 – 2026-10-21 02:40 UTC. `get-metric-statistics` returns the same numbers in its own shape. |
| `aws cloudwatch get-metric-data` or `get-metric-statistics` … `HTTPCode_Target_5XX_Count`, period under 3600 | `cw-04.json` | Sum, period 60. Covers 2026-10-07 00:00 – 2026-10-21 02:40 UTC. |
| `aws ecs list-clusters` | `ecs-11.json` | |
| `aws ecs list-services` … `<cluster from ecs-11.json>` | `ecs-09.json` | |
| `aws ecs describe-services` … `orders-api` | `ecs-01.json` | |
| `aws ecs list-task-definition-families` | `ecs-10.json` | |
| `aws ecs list-task-definitions` … | `ecs-12.json` | Any family filter: return the matching ARNs. |
| `aws ecs describe-task-definition` … `<family or family:revision from ecs-10.json / ecs-12.json>` | table P1 | A family without a revision means its latest revision. |
| `aws ecs list-tasks` … `--desired-status STOPPED` … | table P2 | |
| `aws ecs list-tasks` … (running, the default) | table P3 | |
| `aws ecs describe-tasks` … `<task IDs from ecs-04.json / ecs-05.json>` | table P4 | Return the tasks requested. |
| `aws events list-rules` | `events-01.json` | |
| `aws events describe-rule` … `<rule name from events-01.json>` | table P5 | |
| `aws events list-targets-by-rule` … `<rule name from events-01.json>` | table P6 | |
| `aws scheduler list-schedules` | `scheduler-01.json` | |
| `aws cloudtrail lookup-events` … | `cloudtrail-01.json` | ECS management events. Covers 2026-10-07 00:00 – 2026-10-21 02:40 UTC. Return only events matching the lookup attributes; an attribute no event matches returns `{"Events": []}`. |
| `gh release list` … `example-org/orders-api` | `gh-02.txt` | |
| `gh release view` … `example-org/orders-api` | `gh-01.txt` | Latest release, or tag `2026.10.21-1`. |
| `aws logs describe-log-groups` … | `logs-01.json` | |
| `aws logs start-query` … `<log group from logs-01.json>` … `<query>` | table P7 | |
| `aws logs get-query-results` … `<queryId>` | table P8 | |
| `aws logs stop-query` … | `_default.txt` | |

**P1 — `describe-task-definition`**

| Value | File |
|---|---|
| `orders-api:40` | `ecs-14.json` |
| `orders-api:41` | `ecs-02.json` |
| `orders-api:42`, `orders-api` | `ecs-03.json` |
| `orders-migrate:3`, `orders-migrate` | `ecs-15.json` |
| `orders-reconcile:6` | `ecs-16.json` |
| `orders-reconcile:7`, `orders-reconcile` | `ecs-13.json` |

**P2 — `list-tasks --desired-status STOPPED`** (filters: cluster, `--family`, `--service-name`, `--started-by`)

| Filter | File |
|---|---|
| none, or a `--family` / `--started-by` value that the stopped task in `ecs-05.json` matches (its group and `startedBy` are in `ecs-06.json`) | `ecs-05.json` |
| any other filter (including `--service-name orders-api`, `--family orders-api`) | `ecs-08.json` |

**P3 — `list-tasks` (running)**

| Filter | File |
|---|---|
| none, `--service-name orders-api` or `--family orders-api` | `ecs-04.json` |
| any other filter | `ecs-08.json` |

**P4 — `describe-tasks`**

| Task ID | File |
|---|---|
| the ID in `ecs-05.json` | `ecs-06.json` |
| any ID in `ecs-04.json` | `ecs-07.json` |

**P5 — `describe-rule`**

| Rule | File |
|---|---|
| `catalog-sitemap-weekly` | `events-06.json` |
| `orders-api-ecs-task-state` | `events-07.json` |
| `orders-reconcile-nightly` | `events-02.json` |

**P6 — `list-targets-by-rule`**

| Rule | File |
|---|---|
| `catalog-sitemap-weekly` | `events-04.json` |
| `orders-api-ecs-task-state` | `events-05.json` |
| `orders-reconcile-nightly` | `events-03.json` |

**P7 — `start-query`** (a field name below is usable once it appears in a returned log line)

| Log group | Query | File (queryId) |
|---|---|---|
| `/ecs/orders-api` | `stats count(*)` by a revision field (`ecs_task_revision`), with or without a time bin | `logs-02.json` |
| `/ecs/orders-api` | `stats count(*)` by `error_code`, with or without a time bin | `logs-03.json` |
| `/ecs/orders-api` | no `stats` (fields, filter, sort, limit) | `logs-04.json` |
| `/ecs/orders-reconcile` | any | `logs-05.json` |
| any | anything else | `logs-06.json` |

**P8 — `get-query-results`**

| queryId | Query shape | File | Covers |
|---|---|---|---|
| `8d1f2c4e-5a7b-4c3d-9e1f-0a2b3c4d5e6f` | by revision, `bin(1h)` (or finer) | `logs-12.json` | 2026-10-07 00:00 – 2026-10-21 02:40 UTC, hourly rows |
| `8d1f2c4e-5a7b-4c3d-9e1f-0a2b3c4d5e6f` | by revision, `bin(1d)` | `logs-18.json` | same window, daily rows |
| `8d1f2c4e-5a7b-4c3d-9e1f-0a2b3c4d5e6f` | by revision, no bin | `logs-17.json` | totals for the whole covered window; for a shorter window, sum `logs-12.json` |
| `2b7e9a10-3c4d-4e5f-8a9b-0c1d2e3f4a5b` | by error code, with a bin | `logs-13.json` | same window, daily rows |
| `2b7e9a10-3c4d-4e5f-8a9b-0c1d2e3f4a5b` | by error code, no bin | `logs-19.json` | totals for the whole covered window; for a shorter window, sum `logs-13.json` |
| `c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b` | raw lines | `logs-14.json` | lines with status 500 and above, 2026-10-19 01:50–02:30 and 2026-10-21 01:00–02:40 UTC; other windows return no rows |
| `f0e1d2c3-b4a5-4968-8776-655443322110` | any | `logs-15.json` | 2026-10-19 00:00 – 2026-10-21 02:40 UTC |
| `6e5d4c3b-2a19-4807-b6f5-e4d3c2b1a090` | any | `logs-16.json` | |

Statistics blocks in the result files describe the whole covered window.
