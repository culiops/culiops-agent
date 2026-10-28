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

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls` … `.culiops/sre-investigate` | `ls-01.txt` | |
| `command -v agentbox-env` | `_empty.txt` | Exit status 1. |
| `aws sts get-caller-identity` | `sts-01.json` | |
| `aws iam get-role` … `AWSReservedSSO_ReadOnly_0a1b2c3d4e5f6a7b` | `iam-01.json` | |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `aws cloudwatch describe-alarms` … | `cw-01.json` | Any name, prefix or state filter that includes this alarm; no filter returns the same. |
| `aws cloudwatch describe-alarm-history` … | `cw-02.json` | All history items the API returns for the account's alarms. |
| `aws cloudwatch list-metrics` … `AWS/ApplicationELB` | `cw-05.json` | |
| `aws cloudwatch get-metric-data` or `get-metric-statistics` … `HTTPCode_Target_5XX_Count`, period 3600 or more | `cw-03.json` | Sum, period 3600. Covers 2026-10-07 00:00 – 2026-10-21 02:40 UTC. `get-metric-statistics` returns the same numbers in its own shape. |
| `aws cloudwatch get-metric-data` or `get-metric-statistics` … `HTTPCode_Target_5XX_Count`, period under 3600 | `cw-04.json` | Sum, period 60. Covers 2026-10-07 00:00 – 2026-10-21 02:40 UTC. |
| `aws ecs list-clusters` | `ecs-11.json` | |
| `aws ecs list-services` … `prod` | `ecs-09.json` | |
| `aws ecs describe-services` … `orders-api` | `ecs-01.json` | |
| `aws ecs list-task-definition-families` | `ecs-10.json` | |
| `aws ecs list-task-definitions` … | `ecs-12.json` | Any family filter: return the matching ARNs. |
| `aws ecs describe-task-definition` … `orders-api:41` | `ecs-02.json` | |
| `aws ecs describe-task-definition` … `orders-api:42` (or `orders-api` with no revision) | `ecs-03.json` | |
| `aws ecs describe-task-definition` … `orders-reconcile:7` (or `orders-reconcile`) | `ecs-13.json` | |
| `aws ecs list-tasks` … `--desired-status STOPPED` … `--service-name orders-api` | `ecs-08.json` | |
| `aws ecs list-tasks` … `--desired-status STOPPED` | `ecs-05.json` | Any other filter (cluster, family, started-by) that includes this task. |
| `aws ecs list-tasks` … `--family orders-reconcile` or `--started-by *` | `ecs-08.json` | Running tasks only (the default desired status). |
| `aws ecs list-tasks` … | `ecs-04.json` | Running tasks. |
| `aws ecs describe-tasks` … `7e4b1c90d2a84f61b3c5a6d7e8f90123` | `ecs-06.json` | |
| `aws ecs describe-tasks` … (any of the task IDs in `ecs-04.json`) | `ecs-07.json` | Return the tasks requested. |
| `aws events list-rules` | `events-01.json` | |
| `aws events describe-rule` … `orders-reconcile-nightly` | `events-02.json` | |
| `aws events list-targets-by-rule` … `orders-reconcile-nightly` | `events-03.json` | |
| `aws events list-targets-by-rule` … `catalog-sitemap-weekly` | `events-04.json` | |
| `aws events list-targets-by-rule` … `orders-api-ecs-task-state` | `events-05.json` | |
| `aws scheduler list-schedules` | `scheduler-01.json` | |
| `aws cloudtrail lookup-events` … | `cloudtrail-01.json` | ECS management events. Covers 2026-10-07 00:00 – 2026-10-21 02:40 UTC. Return only events matching the lookup attributes; an attribute no event matches returns `{"Events": []}`. |
| `gh release list` … `example-org/orders-api` | `gh-02.txt` | |
| `gh release view` … `example-org/orders-api` | `gh-01.txt` | Latest release, or tag `2026.10.21-1`. |
| `aws logs describe-log-groups` … | `logs-01.json` | |
| `aws logs start-query` … `/ecs/orders-api`, `stats count(*)` grouped by `ecs_task_revision` (with or without a time bin) | `logs-02.json` | |
| `aws logs start-query` … `/ecs/orders-api`, `stats count(*)` grouped by `error_code` (with or without a time bin) | `logs-03.json` | |
| `aws logs start-query` … `/ecs/orders-api`, no `stats` (fields, filter, sort, limit) | `logs-04.json` | |
| `aws logs start-query` … `/ecs/orders-reconcile` | `logs-05.json` | |
| `aws logs start-query` … | `logs-06.json` | Any other query. |
| `aws logs get-query-results` … `8d1f2c4e-5a7b-4c3d-9e1f-0a2b3c4d5e6f` | `logs-12.json` | Hourly rows by revision. Covers 2026-10-07 00:00 – 2026-10-21 02:40 UTC. Statistics describe the whole covered window. |
| `aws logs get-query-results` … `2b7e9a10-3c4d-4e5f-8a9b-0c1d2e3f4a5b` | `logs-13.json` | Rows per UTC day and error code. Covers 2026-10-07 00:00 – 2026-10-21 02:40 UTC. Statistics describe the whole covered window. |
| `aws logs get-query-results` … `c3d4e5f6-0718-4293-a4b5-c6d7e8f90a1b` | `logs-14.json` | Lines with status 500 and above. Covers 2026-10-19 01:50–02:30 and 2026-10-21 01:00–02:40 UTC; other windows return no rows. |
| `aws logs get-query-results` … `f0e1d2c3-b4a5-4968-8776-655443322110` | `logs-15.json` | Covers 2026-10-19 00:00 – 2026-10-21 02:40 UTC. |
| `aws logs get-query-results` … `6e5d4c3b-2a19-4807-b6f5-e4d3c2b1a090` | `logs-16.json` | |
| `aws logs stop-query` … | `_default.txt` | |
