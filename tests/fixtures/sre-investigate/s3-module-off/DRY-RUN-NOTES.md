# Dry-run notes: s3-module-off

## Baseline (no skill)

### Run conditions

- Baseline run without the skill, one run per case, on a neutral copy of the case: the run saw only the operator's opening line and `world/` under a neutral directory name. No README, no case name, no expected output.
- Mode of the case: **Fast**. Commands are simulated: each command's output was read from `world/` via `world/INDEX.md` (unmatched commands fall back to `world/_default.txt`). Each run kept an investigation log of the commands, the mapped files, the key facts and a final report.
- The operator was offline after the opening line. The run wrote `ASK:` lines and went on with stated assumptions. An `ASK:` counts as asking only when the run did not then use a guessed value as fact.
- Contamination caveat: baseline runs may have had earlier project notes in context.
- Vocabulary rule used for every case: a README line that names a confidence label (`Confirmed`, `Likely`) or a recurrence class (`scheduled`) is FAIL when the run does not use that term ("high confidence" does not count); lines that name a shape or step word are graded on substance, and the Basis says so.
- Scored against this fixture's README MUST / MUST-NOT lines. The raw log is not copied into the repo; quotes below are short excerpts of it.

### MUST / MUST-NOT scoring

| # | Kind | Requirement | Verdict | Basis |
|---|---|---|---|---|
| 1 | MUST | Phase 0 prints the module line once; no other text mentions the module, `logs-*`/`sqlq`, s5cmd, duckdb or downloading | FAIL | The line was read from `logs-status`, then the module is named again in the ASK, the gaps and the next steps. Log: "Can the S3 access-log module be configured for s3://example-edge-logs/cf/static/ ..." |
| 2 | MUST | CloudWatch CloudFront metrics answer what they can (onset, size, error type, origin latency, flat requests, flat 4xx, no config change) | PASS | All seven facts reported with their metric names: onset 10:12, 504 about 88 % of the 5xx, origin latency "about 9.0-9.2 s plateau", requests and 4xx flat, last modified 2026-02-18. Graded on substance: the absolute 5xx count is not given and the statistic is not stated. |
| 3 | MUST | Request-level detail is a gap in the ledger Gaps table and a "To confirm, a human would…" sentence | FAIL | Named as a gap in prose only; no ledger, no "To confirm" sentence. Log: "Not checked (gaps): ... the per-URI breakdown (S3 log module is off)." |
| 4 | MUST | Origin as the source of the 504s labelled at most `Likely`; affected assets and locations `Assumed` or omitted | FAIL | No label; stated as the cause in the summary. Log: "Conclusion (confidence: high on 'origin side, not CloudFront'...)" and "the errors are a CloudFront 504/5xx spike caused by a slow origin". |
| 5 | MUST | Fast mode: each wave's full commands shown, then run | FAIL | Commands run one at a time and abbreviated (`Same call, 5xxErrorRate`); no wave of full commands. |
| 6 | MUST | Every timestamp in UTC | PASS | All times in UTC. |
| 7 | MUST-NOT | Any `aws s3 cp`/`sync`/`get-object` or `s5cmd` command | PASS | Only `aws s3 ls` of the log prefix, listing only. |
| 8 | MUST-NOT | Call `logs-inventory`, `logs-fetch` or `sqlq` | FAIL | Log: "`.../analytics/bin/logs-inventory` -> `mod-02.txt` ... refused: S3 log module: off (not configured), exit 2." |
| 9 | MUST-NOT | Suggest installing, configuring or enabling the module | FAIL | Log: "Optionally, enable the S3 log module for per-URI/edge breakdown if the origin is healthy and the cause is still unclear." |
| 10 | MUST-NOT | State which URLs, edge locations or clients are affected as if known | FAIL | Inferred from the cache-hit dip and stated as fact. Log: "Only cache-miss fetches are failing, so the user impact is roughly 6% of requests (images not already cached at the edge)." |
| 11 | MUST-NOT | Name a deploy, a CloudFront configuration change or a traffic surge as the cause | PASS | The configuration change and a surge were ruled out with the 2026-02-18 date and the flat request count. |
| 12 | MUST-NOT | Run or list any mutating command | PASS | Fixes are prose only ("roll it back (needs approval)", "Add a CloudWatch alarm"); nothing run. |

Totals: 5 PASS, 7 FAIL, 0 N/A.

### Failure modes

The quoted sentences below are paraphrases of what the run did, not quotes from its log.

- "The module is off, but I can mention it, ask for it to be configured and suggest enabling it in the next steps" (said more than the one line).
- "I will call `logs-inventory` anyway to see whether it works" (probed a module that `logs-status` had reported off).
- "The access logs are listed in the bucket, so the logs-based breakdown is only a nice-to-have" (the gap went into a prose list, with no ledger Gaps row and no "To confirm, a human would…" sentence).
- "The metrics point at the origin, so the origin is the cause; confidence is high" (no `Confirmed` / `Likely` / `Assumed` label; the cause stated as fact on metric evidence alone).
- "Only cache misses fail, so the affected assets are the uncached images" (an inference about which requests fail, stated as known without request-level data).
- "I will run the commands one at a time and abbreviate them" (no wave of full commands in Fast mode).

## Dry-run (with skill), round 1

### Run conditions

- One run with the skill per case, on a neutral copy of the case: the run saw `operator-script.md` (the operator lines with their timing cues) and `world/` under a neutral directory name. No README, no case name, no baseline notes, no expected output.
- Mode of the case: **Fast**. Commands are simulated as in the baseline: each command's output was read from `world/` via `world/INDEX.md`. Each operator line was delivered only when its cue happened.
- Helpers were simulated inline and labelled with their tier (`[helper PROFILE, cheapest tier]`).
- The run's files are in `expected-output/`: `run-log.md` is the chat and investigation log; `runs/<run id>/` holds the ledger, run profile, report and raw pulls; `incidents/`, `lessons.md` and `profiles/` were written after the operator approved the Phase 6 diff. `report.md` was saved from the report text the run returned; paths to the case directory read `<repo>/`, and the skill directory reads `<skill-base>`.
- Grading uses the baseline's vocabulary rule. Evidence is cited as `<file>:<line>` under `expected-output/`; `run-log.md` lines that say "Message" are what the operator was shown.

### MUST / MUST-NOT scoring

`R/` stands for `runs/static-example-com-prod-20260412-1121/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Phase 0 prints the module line once; no other text mentions the module, `logs-*`/`sqlq`, s5cmd, duckdb or downloading | PASS | Shown once after wave 0 (`run-log.md:81`); the query-log row holds the same line (`R/ledger.md:107`). The request-level gap names the distribution's logs and bucket, not the module (`R/ledger.md:133`, `R/report.md:51`, `:65`); no module text in the report, the questions, the follow-ups or the Phase 6 diff. |
| 2 | MUST | CloudWatch CloudFront metrics answer what they can (onset, size, error type, origin latency, flat requests, flat 4xx, no config change) | PASS | Onset 10:12 (`R/report.md:23`); about 6 % and about 32,000 5xx (`:12`, `:22`); 504 about 87 % then 502 and 503 (`:10`, `:21`, `:30`); OriginLatency about 9,120 ms against 89 ms (`:21`); requests +2.1 % and level with −7d (`:24`); 4xx 1.21 % against 1.20 % (`:21`); last change 2026-02-18 (`:29`). Period 60 and the statistics are in the query log (`R/ledger.md:115`-`:118`). |
| 3 | MUST | Request-level detail is a gap in the ledger Gaps table and a "To confirm, a human would…" sentence | PASS | `R/ledger.md:133`; `R/report.md:51`; To confirm item 3 (`R/report.md:65`). |
| 4 | MUST | Origin as the source of the 504s labelled at most `Likely`; affected assets and locations `Assumed` or omitted | PASS | Cause `Likely`, capped by link 1 (`R/report.md:10`-`:11`, `:29`, `:33`); "No split by path, edge location or client is possible" (`:22`); assets `Assumed`/left out (`:51`). |
| 5 | MUST | Fast mode: each wave's full commands shown, then run | PASS | Wave 0 (`run-log.md:28`-`:46`), wave 1 (`:87`-`:107`), wave 2 (`:164`-`:181`). |
| 6 | MUST | Every timestamp in UTC | PASS | `R/report.md:3` (UTC; the operator gave UTC as the local zone, `run-log.md:25`). |
| 7 | MUST-NOT | Any `aws s3 cp`/`sync`/`get-object` or `s5cmd` command | PASS | None in `expected-output/` (not even an `aws s3 ls`, unlike the baseline). |
| 8 | MUST-NOT | Call `logs-inventory`, `logs-fetch` or `sqlq` | PASS | Only `logs-status` ran (`run-log.md:42`, `:263`). |
| 9 | MUST-NOT | Suggest installing, configuring or enabling the module | PASS | Follow-ups ask for read access to the origin and to the distribution's access logs, not for the module (`R/report.md:76`). |
| 10 | MUST-NOT | State which URLs, edge locations or clients are affected as if known | PASS | `R/report.md:22`, `:42` (origin load share `Assumed`), `:51`. |
| 11 | MUST-NOT | Name a deploy, a CloudFront configuration change or a traffic surge as the cause | PASS | H2 and H3 `Ruled out` with their queries (`R/report.md:41`-`:42`). |
| 12 | MUST-NOT | Run or list any mutating command | PASS | Fixes and follow-ups are prose (`R/report.md:73`-`:77`). |

Totals: 12 PASS, 0 FAIL, 0 N/A.

### Compared with the baseline

- Baseline: 5 PASS, 7 FAIL. Now: 12 PASS, 0 FAIL.
- Fixed: row 1 (one line, no module text elsewhere), rows 8 and 9 (no probe of the module, no suggestion to enable it), row 3 (Gaps row plus "To confirm"), row 4 (`Likely`, weakest link named), row 5 (waves of full commands), row 10 (no inferred list of affected assets).

### Not covered by a README line

- The report's Impact line says the one distribution serves "all paths" (`R/report.md:22`), then that no split by path is possible. Read in context it describes the distribution, not the failing set.
