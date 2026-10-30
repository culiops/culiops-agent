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
| `echo` … `${JIRA_API_TOKEN:+x}` | `env-01.txt` | |
| `aws sts get-caller-identity` | `sts-01.json` | |
| `aws iam get-role` … | `iam-01.json` | |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `aws cloudwatch describe-alarms` … | `cw-03.json` | |
| `aws cloudwatch describe-alarm-history` … | `cw-02.json` | |
| `aws cloudwatch get-metric-data` (or `get-metric-statistics`) … `HTTPCode_Target_5XX_Count` | `cw-01.json` | Sum, period 60. Covers 2026-10-26 08:40–14:40 UTC; minutes without 5xx have no datapoint. |
| `aws ecs describe-services` … `orders-api` | `ecs-01.json` | |
| `aws rds describe-events` … | `rds-01.json` | Covers the last 24 hours; filter by the requested source or category. |
| `aws rds describe-db-instances` … | `rds-02.json` | |
| `aws logs describe-log-groups` … | `logs-01.json` | |
| `aws logs start-query` … `/ecs/orders-api`, `stats count(*)` grouped by `error_code` (and/or `status`), window overlapping 14:00–14:10 UTC | `logs-02.json` | |
| `aws logs start-query` … `/ecs/orders-api`, `stats count(*)` grouped by `msg` or `@message`, window overlapping 14:00–14:10 UTC | `logs-04.json` | |
| `aws logs start-query` … `/ecs/orders-api`, no `stats`, window overlapping 14:00–14:10 UTC | `logs-03.json` | |
| `aws logs start-query` … | `logs-05.json` | Any other query or window. |
| `aws logs get-query-results` … `4c5d6e7f-8091-4a2b-b3c4-d5e6f7081920` | `logs-12.json` | Covers 14:00–14:10 UTC. |
| `aws logs get-query-results` … `a1b2c3d4-e5f6-4071-8293-a4b5c6d7e8f9` | `logs-13.json` | Covers 14:00–14:10 UTC. |
| `aws logs get-query-results` … `d1e2f3a4-b5c6-4d7e-8f90-a1b2c3d4e5f6` | `logs-14.json` | 8 lines, 14:02–14:05 UTC (all levels). |
| `aws logs get-query-results` … `b2c3d4e5-f6a7-4182-9304-b5c6d7e8f9a0` | `logs-15.json` | |
| `aws logs stop-query` … | `_default.txt` | |
| `curl` … `https://jira.example.com/rest/api/2/issue/SUP-1093` (or any read-only Jira client call for `SUP-1093`) | `jira-01.json` | |
