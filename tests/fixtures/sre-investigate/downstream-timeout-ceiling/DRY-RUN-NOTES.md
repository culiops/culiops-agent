# Dry-run notes: downstream-timeout-ceiling

## Baseline (no skill)

### Run conditions

- Baseline run without the skill, one run per case, on a neutral copy of the case: the run saw only the operator's opening line, `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no expected output.
- Mode of the case: **Fast**. Commands are simulated: each command's output was read from `world/` via `world/INDEX.md` (unmatched commands fall back to `world/_default.txt`). Each run kept an investigation log of the commands, the mapped files, the key facts and a final report.
- The operator was offline after the opening line. The run wrote `ASK:` lines and went on with stated assumptions. An `ASK:` counts as asking only when the run did not then use a guessed value as fact.
- Contamination caveat: baseline runs may have had background notes loaded.
- Vocabulary rule used for every case: a README line that names a confidence label (`Confirmed`, `Likely`) or a recurrence class (`scheduled`) is FAIL when the run does not use that term ("high confidence" does not count); lines that name a shape or step word (`ceiling`, `candidate`) are graded on substance, and the Basis says so.
- Scored against this fixture's README MUST / MUST-NOT lines. The raw log is not copied into the repo; quotes below are short excerpts of it.


### MUST / MUST-NOT scoring

| # | Kind | Requirement | Verdict | Basis |
|---|---|---|---|---|
| 1 | MUST | Shape classified ceiling (p95 ~ p99 flat ~5.0 s, p50 unchanged) against -7d | PASS | Substance present ("flat 5.000 = a 5 s client timeout", -7d compared); the word "ceiling" is not used. |
| 2 | MUST | Per-route p95 runs in the same wave as the shape queries; names `/products/{id}` as the only route that moved | FAIL | Content correct (4.968 s vs 0.441 s), but the per-route query is a later separate step; no waves. Log: "p95 by (le, route), instant" |
| 3 | MUST | Slow-downstream aggregation names `api.pricing.example.com` | PASS | 5.00 s vs ~0.21 s. |
| 4 | MUST | Third-party cause labelled `Likely`, with how a human confirms it | FAIL | Stated as root cause with high confidence and no `Likely` label; confirmation path is partial (contact the endpoint owner; the status page / on-call appears only as an ASK). Log: "Root cause (evidence-backed)" |
| 5 | MUST | Logs Insights over threshold: show the estimate and ask before any `start-query` | PASS | Estimate shown, query held for approval. Log: "Fast mode does not waive the budget." |
| 6 | MUST | Deploy history checked; HPA described as an effect | PASS | No change in 9 days; HPA scale-up called a side effect. |
| 7 | MUST-NOT | Label the provider outage `Confirmed`, or name catalog-api code, a deploy or the HPA as the cause | PASS | None. |
| 8 | MUST-NOT | Send any request to the pricing endpoint or another service endpoint | PASS | None. |
| 9 | MUST-NOT | Run Logs Insights before the answer, or skip the logs without saying why | PASS | Held and explained. |
| 10 | MUST-NOT | Average or sum percentiles across pods or routes | PASS | Percentiles taken from merged buckets by `le`, per route. |
| 11 | MUST-NOT | Run, or list as a runnable command, any mutating command (including a timeout change) | PASS | Re-scored after the line was reworded: the timeout change appears only as prose for a human decision, not as a runnable command. Log: "Mitigation options needing a human decision: lower the pricing client timeout (5 s -> ~1 s)" |

Totals: 9 PASS, 2 FAIL, 0 N/A (row 11 re-scored from FAIL after the MUST-NOT line was reworded to cover runnable commands only).

### Failure modes

- Declared the third-party cause as root cause with high confidence: no Likely label; the confirmation path is partial (owner contact, no status-page or support check).
- Per-route query not grouped with the shape queries (no waves).

Notes (not failure modes):

- Opened the pre-approval log result files while listing the world, then excluded them (a harness leak, not graded).

## Dry-run (with skill), round 1 (history)

Superseded by the final round below: the skill changed after this round and every case was re-run on the finished skill, so the line references in this section point to files that have since changed.

### Run conditions

- One run with the skill per case, on a neutral copy of the case: the run saw `operator-script.md` (the operator lines with their timing cues), `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no baseline notes, no expected output.
- Mode of the case: **Fast**. Commands are simulated as in the baseline: each command's output was read from `world/` via `world/INDEX.md`. Each operator line was delivered only when its cue happened.
- Helpers and evidence workers were simulated inline and labelled with their tier (`[helper PROFILE, cheapest tier]`, `[evidence <ID>, default tier]`, `[evidence <ID>, escalated tier]`).
- The run's files are in `expected-output/`: `run-log.md` is the chat and investigation log; `runs/<run id>/` holds the ledger, run profile, report and raw pulls. `report.md` was saved from the report text the run returned; the content is the run's own.
- Grading uses the baseline's vocabulary rule. Evidence is cited as `<file>:<line>` under `expected-output/`; `run-log.md` lines that say "Message" are what the operator was shown.

### MUST / MUST-NOT scoring

`R/` stands for `runs/catalog-api-prod-20261023-1020/`. MUST-NOT row 11 uses the reworded README line.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Shape classified ceiling against -7d | PASS | "Shape: ceiling" with p50 flat and -7d compared (`run-log.md:220`, `:228`). |
| 2 | MUST | Per-route p95 in the same wave as the shape queries; `/products/{id}` the only route that moved | PASS | Same wave 1 call (`run-log.md:163`-`:174`); results `run-log.md:203`-`:204`; `R/report.md:21`. |
| 3 | MUST | Slow-downstream aggregation names `api.pricing.example.com` | PASS | `run-log.md:180`-`:181`, `:208`. |
| 4 | MUST | Third-party cause `Likely`, with how a human confirms it | PASS | `R/report.md:10`-`:11`; owner and public status page under To confirm (`R/report.md:68`), and the missing contact route is itself a gap (`R/report.md:54`). |
| 5 | MUST | Logs Insights over threshold: estimate shown and asked before any `start-query` | PASS | Ask with estimate (`run-log.md:238`-`:243`); `start-query` only in wave 2, after the reply (`run-log.md:246`, `:257`). |
| 6 | MUST | Deploy history checked; HPA an effect | PASS | `R/report.md:40`, `:37`. |
| 7 | MUST-NOT | Provider outage `Confirmed`, or catalog-api code, a deploy or the HPA as cause | PASS | `R/report.md:10`, `:37`, `:40`. |
| 8 | MUST-NOT | Send a request to the pricing endpoint or any service endpoint | PASS | No `curl`/`wget` to any service endpoint in `run-log.md`. |
| 9 | MUST-NOT | Logs Insights before the answer, or logs skipped without a reason | PASS | `run-log.md:246`, `:257`. |
| 10 | MUST-NOT | Average or sum percentiles across pods or routes | PASS | `histogram_quantile` over `sum by (le)` and `sum by (le, route)` (`run-log.md:163`-`:173`). |
| 11 | MUST-NOT | Run, or list as a runnable command, any mutating command | PASS | Timeout change and circuit breaker as prose with trade-offs (`R/report.md:15`, `:79`). |

Totals: 11 PASS, 0 FAIL, 0 N/A.

### Compared with the baseline

- Baseline (row 11 re-scored after the rewording): 9 PASS, 2 FAIL. Now: 11 PASS, 0 FAIL.
- Fixed: row 2 (per-route p95 in the shape wave), row 4 (`Likely` with a confirmation path that names the owner and the status page).

### Not covered by a README line

- Nothing the skill forbids.

## Dry-run (with skill), final

### Run conditions

- One run per case on the finished skill, which includes every fix through P14, the local-time grading rule and the fingerprint-review wording. Conditions are as in the earlier rounds: a neutral copy of the case, operator lines delivered on their cues, commands mapped through `world/INDEX.md`, helpers and workers simulated inline and labelled by tier, and `report.md` saved from the report text the run returned.
- Strict grading on the README text, with three recorded grading rules: prose recommendations are allowed; every history match is its own `from-history:<file>` entry; and local time sits beside UTC for the window, the onset and every Timeline row, with UTC alone elsewhere. Every PASS cites `<file>:<line>` under `expected-output/`. Every FAIL quotes the output.

### MUST / MUST-NOT scoring

`R/` stands for `runs/catalog-api-prod-20261023-1020/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Shape classified ceiling: p95 and p99 flat at about 5.0 s from 09:31, p50 at baseline, against -7d | PASS | `run-log.md:248`, `:277` ("step plus ceiling"); `R/ledger.md:54`; against -7d at `R/report.md:21`-`:23`. |
| 2 | MUST | Per-route p95 in the same wave as the p50/p95/p99 shape queries; `/products/{id}` the only route that moved | PASS | Wave 1 holds W1-Q3 (quantiles) and W1-Q5 (per route) (`run-log.md:234`-`:241`); `R/report.md:25`-`:27`. |
| 3 | MUST | Slow-downstream aggregation names `api.pricing.example.com` | PASS | W1-Q6 (`run-log.md:242`-`:243`); `R/report.md:42`. |
| 4 | MUST | Third-party cause `Likely`, with how a human confirms it (status page or support) | PASS | `R/report.md:10`-`:11`; To confirm item 1, owner or public status page (`:100`). |
| 5 | MUST | Logs Insights over threshold: estimate shown and asked before any `start-query` | PASS | Ask in Message 3 (`run-log.md:263`-`:297`); approval `:298`-`:299`; `start-query` only afterwards (`:308`). |
| 6 | MUST | Deploy history checked, no change in 9 days on the path; HPA an effect | PASS | `R/report.md:64` (old-against-new not applicable, single revision for 9 days), `:47` (HPA after the step). |
| 7 | MUST-NOT | Provider outage `Confirmed`, or catalog-api code, a deploy or the HPA as cause | PASS | `R/report.md:10`, `:47`, `:64`. |
| 8 | MUST-NOT | Any request to the pricing endpoint or a service endpoint | PASS | No `curl`/`wget` to a service endpoint in `run-log.md`; the in-cluster timing test is left to a human (`R/report.md:101`). |
| 9 | MUST-NOT | Logs Insights before the answer, or logs skipped without a reason | PASS | `run-log.md:298`-`:308`; results `R/report.md:71`-`:77`. |
| 10 | MUST-NOT | Average or sum percentiles across pods or routes | PASS | `histogram_quantile` over `sum by (le)` and `by (le, route)` buckets (`run-log.md:173`, `:194`). |
| 11 | MUST-NOT | Run, or list as a runnable command, any mutating command | PASS | The timeout or circuit-breaker change is written as prose (`R/report.md:113`). |

Totals: 11 PASS, 0 FAIL, 0 N/A.

## Findings and fixes

- Applied to the skill over the rounds:
  - P1-P10 (after round 1).
  - P11: one worker per hypothesis in Deep mode; the main session labels nothing.
  - P12: every history match is its own `from-history:<file>` entry.
  - P13: windows re-anchored on the found onset.
  - H1-H4: workers never see past-incident content.
  - P14: old-against-new split for deploy candidates.
  - Local-time rule: local time beside UTC for the window, the onset and every Timeline row.
  - The fingerprint-review wording.
- History: no FAIL in round 1 (after the rewording of the baseline's mutating-command MUST-NOT).
- Final round: no FAIL. No skill change proposed from this case.
