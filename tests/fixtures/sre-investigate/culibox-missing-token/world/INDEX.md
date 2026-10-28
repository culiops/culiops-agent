# World index

## Matching rules

1. A pattern names the command words and the arguments that pick the row. Any other flags and arguments may come anywhere, in any order; `…` marks where they usually sit, and `*` inside a value matches any text.
2. `--profile`, `--region`, `--output`, `--query`, `--no-cli-pager`, `--color`, and kubectl's `-o`/`--sort-by`/`--field-selector` do not change which row matches, unless the row says so. A profile may be given as `--profile p`, `--profile=p` or `AWS_PROFILE=p`. Where a row needs an output format (`-o json`), it says so.
3. kubectl: the namespace may be given as `-n ns` or `--namespace ns`, before or after the verb. Resource kinds match their short, singular and plural names (`po`/`pod`/`pods`, `rs`/`replicaset`/`replicasets`, `deploy`/`deployment`).
4. Time windows: a row whose Notes give a covered window matches any request whose window overlaps it. Return only the points or rows inside the requested window (and sum them when the request asks for a coarser period or no time bin). A request whose window overlaps no row's window gets the default for its kind.
5. Query text (PromQL, LogQL, TraceQL, Logs Insights): a query matches when it asks for the same metric or fields with the same selectors, whatever the spelling (`0.5` = `0.50`, label order, whitespace, `sum by (le) (…)` = `sum(…) by (le)`), whether it is sent with `curl`, a CLI or an MCP tool.
6. The first matching row wins.
7. Defaults: an unmatched JSON API call returns `_default.txt` (`{}`); an unmatched text command (`kubectl`, `helm`, `git`, `grep`, `command -v`, `echo`) returns `_empty.txt` (no output, exit status 0 unless a row says otherwise). `cat` or `ls` of a path that no row names prints `No such file or directory` with exit status 1.

Profile exception to rule 2: every `aws` command run with profile `prod-read` (as `--profile prod-read`, `--profile=prod-read` or `AWS_PROFILE=prod-read`, before or after the subcommand) matches the first row below, whatever the subcommand.

## Rows

| Command pattern | File | Notes |
|---|---|---|
| `aws` … profile `prod-read` | `aws-err-01.txt` | Exit status 255. |
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls` … `.culiops/sre-investigate` | `ls-01.txt` | |
| `command -v agentbox-env` | `cmd-01.txt` | Exit status 0. |
| `agentbox-env` … | `_empty.txt` | |
| `echo` … `${SENTRY_AUTH_TOKEN:+x}` | `_empty.txt` | |
| `aws sts get-caller-identity` (profile `staging-read`) | `sts-01.json` | |
| `aws iam get-role` … | `iam-01.json` | |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `aws ecs list-clusters` | `ecs-02.json` | |
| `aws ecs list-services` … `staging` | `ecs-03.json` | |
| `aws ecs describe-services` … `payments-worker` | `ecs-01.json` | |
| `aws sqs list-queues` … | `sqs-01.json` | |
| `aws cloudwatch get-metric-data` (or `get-metric-statistics`) … `AWS/SQS` … `ApproximateNumberOfMessagesVisible` … `payments-worker-dlq` | `cw-01.json` | Period 300. Covers 2026-10-25 05:30–07:10 UTC. |
| `aws logs describe-log-groups` … | `logs-01.json` | |
| `aws logs start-query` … `/ecs/payments-worker`, `stats` grouped by any of `task_def_revision`, `error`, `@message`, window overlapping 03:00–07:15 UTC | `logs-02.json` | |
| `aws logs start-query` … `/ecs/payments-worker`, no `stats`, window overlapping 03:00–07:15 UTC | `logs-04.json` | |
| `aws logs start-query` … | `logs-03.json` | Any other query or window. |
| `aws logs get-query-results` … `9a0b1c2d-3e4f-4a5b-8c6d-7e8f9a0b1c2d` | `logs-12.json` | Covers 03:00–07:15 UTC. |
| `aws logs get-query-results` … `3a4b5c6d-7e8f-4091-a2b3-c4d5e6f70812` | `logs-14.json` | Sample of matching lines, 06:24–07:15 UTC. |
| `aws logs get-query-results` … `7f8e9d0c-1b2a-4394-8576-a4b3c2d1e0f9` | `logs-13.json` | |
| `gh api repos/example-org/payments-worker/compare/*`, `gh release view` … or `gh pr list` … `example-org/payments-worker` | `gh-01.txt` | |
| `curl` … `sentry.io/api/0/` … or `sentry-cli` … | `sentry-01.json` | HTTP 401 / exit status 1. |
