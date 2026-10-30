# World index

## Matching rules

1. A pattern names the command words and the arguments that pick the row. Any other flags and arguments may come anywhere, in any order; `…` marks where they usually sit, and `*` inside a value matches any text.
2. `--profile`, `--region`, `--output`, `--query`, `--no-cli-pager`, `--color`, and kubectl's `-o`/`--sort-by`/`--field-selector` do not change which row matches, unless the row says so. A profile may be given as `--profile p`, `--profile=p` or `AWS_PROFILE=p`. Where a row needs an output format (`-o json`), it says so.
3. kubectl: the namespace may be given as `-n ns` or `--namespace ns`, before or after the verb. Resource kinds match their short, singular and plural names (`po`/`pod`/`pods`, `rs`/`replicaset`/`replicasets`, `deploy`/`deployment`).
4. Time windows: a row whose Notes give a covered window matches any request whose window overlaps it. Return only the points or rows inside the requested window (and sum them when the request asks for a coarser period or no time bin). A request whose window overlaps no row's window gets the default for its kind.
5. Query text (PromQL, LogQL, TraceQL, Logs Insights): a query matches when it asks for the same metric or fields with the same selectors, whatever the spelling (`0.5` = `0.50`, label order, whitespace, `sum by (le) (…)` = `sum(…) by (le)`), whether it is sent with `curl`, a CLI or an MCP tool.
6. The first matching row wins.
7. Defaults: an unmatched JSON API call returns `_default.txt` (`{}`); an unmatched text command (`kubectl`, `helm`, `git`, `grep`, `command -v`, `echo`) returns `_empty.txt` (no output, exit status 0 unless a row says otherwise). `cat` or `ls` of a path that no row names prints `No such file or directory` with exit status 1.
8. Plugin commands: `…/analytics/bin/<name>` stands for the plugin's `skills/sre-investigate/analytics/bin/<name>`, called by any path (relative or absolute). Each row gives the combined stdout and stderr of the command in the order the tool wrote them, and its exit status. A `~` in an output stands for the operator's home directory.
9. State. The module rows are written for this order, the way the tool behaves: `logs-inventory` before `logs-fetch` (a fetch needs a manifest that covers the slice's day and the day after it; otherwise the refusal row applies); `logs-fetch … --yes --run <id>` before `sqlq … --run <id>`. Wherever an output shows the run id `shop-web-prod-20260412-0915`, show the id the command used instead. A real fetch appends its charge to the ledger, so a second real fetch in the same investigation shows the first one's MB added to its `24h` figure and, for the same run id, to its `run` figure (plain addition; the caps lines then change from `OK` to `OVER` if the sum passes the cap).
10. The fixture's clock is 2026-04-12 09:15:30 UTC. WAF samples reach back three hours from it.

## Rows

| Command pattern | File | Notes |
|---|---|---|
| `cat .culiops/sre-investigate/environment.md` | `environment.md` | |
| `ls` … `.culiops/sre-investigate` | `ls-01.txt` | |
| `command -v agentbox-env` | `_empty.txt` | Exit status 1. |
| `command -v s5cmd` | `tool-01.txt` | The tools are installed on this host. |
| `command -v duckdb` | `tool-02.txt` | |
| `s5cmd version` | `ver-01.txt` | |
| `duckdb --version` | `ver-02.txt` | |
| `date` … | `date-01.txt` | Apply a `+FORMAT` and `-u` to this time (`date -u +%Y%m%d-%H%M` prints `20260412-0915`). |
| `…/analytics/bin/logs-status` | `mod-01.txt` | Exit status 0. |
| `cat ~/.config/culiops/sre-investigate/logs.env` | `logs-env.txt` | |
| `ls` … `~/.config/culiops/sre-investigate` | `ls-02.txt` | No `over-cap.allow` file. `ls`, `cat` or `test -e` of that file: no such file, exit status 1. |
| `cat ~/.local/share/culiops/sre-investigate/budgets/ledger.jsonl` | table P0 | |
| `ls` … `~/.local/share/culiops/sre-investigate/data/<run-id>` or `…/<run-id>/shop-waf` | table P0 | Only after a real fetch for that run id. |
| `aws sts get-caller-identity` | `sts-01.json` | |
| `aws iam get-role` … | `iam-01.json` | |
| `aws iam simulate-principal-policy` … | `iam-02.json` | Evaluation results. |
| `aws wafv2 list-web-acls` … | `waf-01.json` | `--scope REGIONAL`, region `us-east-1`. Any other scope or region returns `{"WebACLs": []}`. |
| `aws wafv2 get-web-acl` … `example-shop-acl` | `waf-02.json` | |
| `aws wafv2 get-logging-configuration` … | `waf-03.json` | |
| `aws wafv2 list-resources-for-web-acl` … | `waf-04.json` | |
| `aws wafv2 get-sampled-requests` … | table P1 | |
| `aws cloudwatch list-metrics` … `AWS/WAFV2` | `cw-01.json` | |
| `aws cloudwatch describe-alarms` … | `cw-02.json` | No alarm exists for this ACL. |
| `aws cloudwatch get-metric-data` or `get-metric-statistics` … `AWS/WAFV2` … | table P2 | Region `us-east-1`; dimensions `WebACL=example-shop-acl`, `Region=us-east-1`, `Rule=<name or ALL>`. |
| `…/analytics/bin/logs-inventory shop-waf <from> <to>` | table P3 | |
| `…/analytics/bin/logs-fetch shop-waf <day> [slice] [--every N]` (no `--yes`) | table P4 | A dry run. |
| `…/analytics/bin/logs-fetch shop-waf <day> [slice] [--every N] --yes --run <id>` [`--force`] | table P5 | |
| `…/analytics/bin/sqlq shop-waf --run <id> …` | table P6 | |
| any `…/analytics/bin/<tool>` with a dataset other than `shop-waf` | `dry-23.txt` | `refused: unknown dataset '<name>' (configured: shop-waf)`, exit status 2. |

Slices of unlisted shape (another hour, hour range, minute range or `--every N`) in P4: print the same lines as the nearest listed row with the numbers recomputed from `hours-01.txt`: `files` is the files of the slice plus the widen file, divided by N and rounded up for `--every N`; `MB` is the sum from the table, scaled by the sampled share; `est_cost` is MB ÷ 1024 × $0.11 + files ÷ 1000 × $0.0005, to four decimals; the `24h` figure is the MB plus 1,945.6 (plus any MB already fetched in this investigation); the verdict is `OVER (24h)` when it passes 2048, `OVER (fetch)` when the MB passes 200. A real run (P5) of a slice that is not listed there is not modelled: return `_default.txt`.

**P0 — ledger and data directory**

| State | Ledger file | Data directory listing |
|---|---|---|
| before any real fetch | `ledger-00.txt` | the path does not exist (no such file or directory, exit status 1) |
| after the real fetch of set a | `ledger-a.txt` | `data-ls-a.txt` (replace `RUNID` with the run id) |
| after set b | `ledger-b.txt` | `data-ls-b.txt` |
| after set c | `ledger-c.txt` | `data-ls-c.txt` |
| after set d | `ledger-d.txt` | `data-ls-d.txt` |
| after set e | `ledger-e.txt` | `data-ls-e.txt` |
| after set f | `ledger-f.txt` | `data-ls-f.txt` |

**P1 — `get-sampled-requests`**

| Window | File |
|---|---|
| inside 06:15 – 09:15 UTC on 2026-04-12, rule metric `Default_Action` (or no rule given) | `waf-06.json` |
| inside that window, any other rule metric | `waf-07.json` |
| any window that starts before 06:15 UTC on 2026-04-12 | `waf-05.txt` (exit status 254) |

**P2 — `get-metric-data` / `get-metric-statistics` on `AWS/WAFV2`**

Statistic `Sum`. A period of 60 to 299 returns the 60-second file points inside the window; 300 to 3599 the 300-second file; 3600 or more the 3600-second file, and a period over 3600 combines those points by summing. A series without a point for a period has no data for it (the rule never fired); the point is simply absent. A request with several queries returns one `MetricDataResults` entry per query. The 60-second files cover two windows only: 2026-04-04 10:00 – 20:00 and 2026-04-11 10:00 – 20:00 UTC.

| Metric | `Rule` | Period | File | Covers (UTC) |
|---|---|---|---|---|
| `AllowedRequests` | `ALL` | 3600 or more | `cw-11.json` | 2026-04-04 00:00 – 2026-04-12 09:15 |
| `AllowedRequests` | `ALL` | 300 to 3599 | `cw-12.json` | same |
| `AllowedRequests` | `ALL` | 60 to 299 | `cw-13.json` | the two windows above |
| `BlockedRequests` | `ALL` | 3600 or more | `cw-14.json` | 2026-04-04 00:00 – 2026-04-12 09:15 |
| `BlockedRequests` | `ALL` | 300 to 3599 | `cw-15.json` | same |
| `BlockedRequests` | `ALL` | 60 to 299 | `cw-16.json` | the two windows above |
| `BlockedRequests` | `AWS-AWSManagedRulesAmazonIpReputationList` | 3600 or more | `cw-17.json` | 2026-04-04 00:00 – 2026-04-12 09:15 |
| `BlockedRequests` | `AWS-AWSManagedRulesAmazonIpReputationList` | 300 to 3599 | `cw-18.json` | same |
| `BlockedRequests` | `AWS-AWSManagedRulesAmazonIpReputationList` | 60 to 299 | `cw-19.json` | the two windows above |
| `BlockedRequests` | `geo-block-embargo` | 3600 or more | `cw-20.json` | 2026-04-04 00:00 – 2026-04-12 09:15 |
| `BlockedRequests` | `geo-block-embargo` | 300 to 3599 | `cw-21.json` | same |
| `BlockedRequests` | `geo-block-embargo` | 60 to 299 | `cw-22.json` | the two windows above |
| `BlockedRequests` | `rate-limit-coupon` | 3600 or more | `cw-23.json` | 2026-04-04 00:00 – 2026-04-12 09:15 |
| `BlockedRequests` | `rate-limit-coupon` | 300 to 3599 | `cw-24.json` | same |
| `BlockedRequests` | `rate-limit-coupon` | 60 to 299 | `cw-25.json` | the two windows above |
| `CountedRequests` (rule `count-new-bot-signals`), `AllowedRequests` for a rule other than `ALL`, `CaptchaRequests`, `ChallengeRequests` | | any | `_default.txt` | not modelled |

**P3 — `logs-inventory shop-waf <from> <to>`**

| From – to | File | Notes |
|---|---|---|
| 2026-04-11 – 2026-04-11 | `inv-01.txt` | |
| 2026-04-11 – 2026-04-12 | `inv-02.txt` | |
| 2026-04-10 – 2026-04-11 | `inv-03.txt` | 2026-04-10 has no log objects: the gap line. |
| 2026-04-10 – 2026-04-12 | `inv-04.txt` | |
| 2026-04-10 – 2026-04-10 | `inv-05.txt` | |
| 2026-04-12 – 2026-04-12 | `inv-06.txt` | |
| any other range inside 2026-04-10 – 2026-04-12 | assemble | One row per day from the rows above (2026-04-10: 0 files, `0.00`, `$0.0000`, and its gap line; 2026-04-11: 288 files, `1843.20` MB, `$0.1981`; 2026-04-12: 111 files, `156.97` MB, `$0.0169`), a `total` row, and a `manifest:` line with the requested range in the file name. |
| a range with a day before 2026-04-04 or after 2026-04-12, or longer than 92 days | assemble | Days with no objects print `0 files` rows and the gap line. A range over 92 days prints `refused: range of <n> days is over the 92-day limit; split it` (exit status 2). |

All inventories exit with status 0 except a refusal.

**P4 — `logs-fetch shop-waf <day> …` dry run**

Needs an inventory that covers the day and the day after it, otherwise `dry-22.txt` (`refused: no manifest covers <day>; run logs-inventory …`, exit status 2; show the first uncovered day and the matching inventory command). Exit status 0 when the verdict line says `OK`; 2 when it says `OVER`.

| Day | Slice (after the day, before any option) | File | Verdict |
|---|---|---|---|
| 2026-04-11 | none (whole day) | `dry-01.txt` | OVER (fetch, run, 24h) |
| 2026-04-11 | none, `--every 12` | `dry-02.txt` | OVER (24h) |
| 2026-04-11 | none, `--every 20` | `dry-03.txt` | OK |
| 2026-04-11 | `12-16` | `dry-04.txt` | OVER (fetch, 24h) |
| 2026-04-11 | `13` | `dry-05.txt` | OK |
| 2026-04-11 | `14` | `dry-06.txt` | OK |
| 2026-04-11 | `15` | `dry-07.txt` | OK |
| 2026-04-11 | `13-14` | `dry-08.txt` | OK |
| 2026-04-11 | `14-15` | `dry-09.txt` | OK |
| 2026-04-11 | `13-15` | `dry-10.txt` | OVER (24h) |
| 2026-04-11 | `13-15 --every 2` | `dry-11.txt` | OK |
| 2026-04-11 | `13-15 --every 3` | `dry-12.txt` | OK |
| 2026-04-11 | `13-15 --every 4` | `dry-13.txt` | OK |
| 2026-04-11 | `13 --every 2` | `dry-14.txt` | OK |
| 2026-04-11 | `13-14 --every 2` | `dry-15.txt` | OK |
| 2026-04-11 | `13:35-14:05` | `dry-16.txt` | OK |
| 2026-04-11 | `13:40-15:15` | `dry-17.txt` | OK |
| 2026-04-10 | none | `dry-18.txt` | OK (needs an inventory that covers 2026-04-11; the two files it lists belong to 2026-04-11) |

**P5 — `logs-fetch … --yes --run <id>` (real run)**

The run id must be `<service>-<env>-<YYYYMMDD>-<HHMM>`, lowercase (the id `shop-web-prod-20260412-0915` has that form); anything else prints `refused: invalid run id '<id>' (expected <service>-<env>-<YYYYMMDD>-<HHMM>, lowercase)` (exit status 2). Each output below is for a ledger that already holds the two earlier charges (`ledger-00.txt`).

| Day | Slice | `--force` | File | Exit | Set |
|---|---|---|---|---|---|
| 2026-04-11 | `13` | no | `run-a.txt` | 0 | a |
| 2026-04-11 | `13-14` | no | `run-b.txt` | 0 | b |
| 2026-04-11 | `13-15 --every 2` | no | `run-c.txt` | 0 | c |
| 2026-04-11 | none, `--every 20` | no | `run-d.txt` | 0 | d |
| 2026-04-11 | `13:40-15:15` | no | `run-e.txt` | 0 | e |
| 2026-04-11 | `13-15 --every 3` | no | `run-f.txt` | 0 | f |
| 2026-04-11 | `13-15` | no | `dry-19.txt` | 2 | nothing is downloaded or charged |
| 2026-04-11 | `13-15` | yes | `dry-20.txt` | 2 | no marker file exists, so the override is refused; nothing is downloaded or charged |
| 2026-04-11 | none | no | `dry-21.txt` | 2 | nothing is downloaded or charged |
| 2026-04-11 | none | yes | `dry-20.txt` | 2 | same refusal |
| the same slice, `--every` and run id as a fetch already done | | no | `run-b-again.txt` | 0 | `fetched 0 files … skipped <N> present`, N = the files of that fetch, `converted: rows 0` |
| the same run id and dataset with a different `--every` | | no | `run-b-sample.txt` | 2 | show the earlier and the requested factor |
| any other slice | | no | `_default.txt` | | not modelled (see above) |

An override with a marker file the operator has created is not modelled; the operator script never creates one.

**P6 — `sqlq shop-waf --run <id> …`**

`<set>` is the set of the real fetch that used `<id>`: files `q<set>-<name>.txt`. A run id with no real fetch prints `q-wrongrun.txt` (exit status 2; show the id used). Exit status 0 unless a row says otherwise. Notice lines start with `-- ` and come first, as the tool prints them.

| Command | File |
|---|---|
| `--list` | `q<set>-list.txt` |
| `<name>` for each of `asns by_day by_minute client_keys clients concentration count_rules countries fingerprints header_shape labels matched_data rules_by_minute summary top_rules uris user_agents` | `q<set>-<name>.txt` |
| `by_minute --param action=BLOCK` | `q<set>-by_minute_block.txt` |
| `compare_days --param a=2026-04-10 --param b=2026-04-11` | `q<set>-compare_days.txt` |
| `--sql` selecting blocked requests by `/24` network (set b only) | `qb-adhoc-net.txt` |
| `--sql` selecting blocked requests by `user_agent` (set b only) | `qb-adhoc-ua.txt` |
| `--sql` calling a file or network function (`read_csv(…)`, `read_parquet(…)`, `glob(…)`), `COPY`, `ATTACH`, a dot-command, or more than one statement | `qb-adhoc-refused.txt` (exit status 2; show the function or keyword the statement used) |
| any other `--sql` | the CSV of the nearest named query of the same set if its columns hold the answer; otherwise the header row of the statement's columns and no data rows |
| a named query not listed, or a missing required `--param` | `_default.txt` |
| `run:<dir>` instead of a dataset | `_default.txt` (not modelled) |

Sets and what they hold (the dry-run and real-run lines above show the sample factor):

| Set | Fetch | Rows converted | Sample factor |
|---|---|---|---|
| a | `13` | 49,107 | 1 |
| b | `13-14` | 104,714 | 1 |
| c | `13-15 --every 2` | 74,584 | 2 |
| d | whole day `--every 20` | 42,769 | 20 |
| e | `13:40-15:15` | 88,363 | 1 |
| f | `13-15 --every 3` | 51,352 | 3 |

In sets c, d and f the first lines of every query output are the tool's `-- sampled 1/N: …` notice; the counts that follow are the sample's counts, not scaled.
