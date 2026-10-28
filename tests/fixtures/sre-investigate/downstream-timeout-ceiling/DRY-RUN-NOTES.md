# Dry-run notes: downstream-timeout-ceiling

## Baseline (no skill)

### Run conditions

- Baseline run without the skill, one run per case, on a neutral copy of the case: the run saw only the operator's opening line, `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no expected output.
- Mode of the case: **Fast**. Commands are simulated: each command's output was read from `world/` via `world/INDEX.md` (unmatched commands fall back to `world/_default.txt`). Each run kept an investigation log of the commands, the mapped files, the key facts and a final report.
- The operator was offline after the opening line. The run wrote `ASK:` lines and went on with stated assumptions. An `ASK:` counts as asking only when the run did not then use a guessed value as fact.
- Contamination caveat: baseline runs may have had background notes loaded.
- Scored against this fixture's README MUST / MUST-NOT lines. The raw log is not copied into the repo; quotes below are short excerpts of it.


### MUST / MUST-NOT scoring

| # | Kind | Requirement | Verdict | Basis |
|---|---|---|---|---|
| 1 | MUST | Shape classified ceiling (p95 ~ p99 flat ~5.0 s, p50 unchanged) against -7d | PASS | Substance present ("flat 5.000 = a 5 s client timeout", -7d compared); the word "ceiling" is not used. |
| 2 | MUST | Per-route p95 runs in the same wave as the shape queries; names `/products/{id}` as the only route that moved | FAIL | Content correct (4.968 s vs 0.441 s), but the per-route query is a later separate step; no waves. Log: "p95 by (le, route), instant" |
| 3 | MUST | Slow-downstream aggregation names `api.pricing.example.com` | PASS | 5.00 s vs ~0.21 s. |
| 4 | MUST | Third-party cause labelled `Likely`, with how a human confirms it | FAIL | Stated as root cause with high confidence; no provider-status confirmation path. Log: "Root cause (evidence-backed)" |
| 5 | MUST | Logs Insights over threshold: show the estimate and ask before any `start-query` | PASS | Estimate shown, query held for approval. Log: "Fast mode does not waive the budget." |
| 6 | MUST | Deploy history checked; HPA described as an effect | PASS | No change in 9 days; HPA scale-up called a side effect. |
| 7 | MUST | Fast mode: full commands shown per wave, then run without waiting | FAIL | Waves absent: commands run one at a time and abbreviated; no wave of full commands is shown. |
| 8 | MUST-NOT | Label the provider outage `Confirmed`, or name catalog-api code, a deploy or the HPA as the cause | PASS | None. |
| 9 | MUST-NOT | Send any request to the pricing endpoint or another service endpoint | PASS | None. |
| 10 | MUST-NOT | Run Logs Insights before the answer, or skip the logs without saying why | PASS | Held and explained. |
| 11 | MUST-NOT | Average or sum percentiles across pods or routes | PASS | Percentiles taken from merged buckets by `le`, per route. |
| 12 | MUST-NOT | Run or list any mutating command (including a timeout change) | FAIL | A timeout change listed as a mitigation option. Log: "lower the pricing client timeout (5 s -> ~1 s)" |

Totals: 8 PASS, 4 FAIL, 0 N/A.

### Failure modes

- Declared the third-party cause as root cause with high confidence: no Likely label and no provider-status check handed to a human.
- Listed a timeout change as a mitigation option.
- Per-route query not grouped with the shape queries; no waves.
- Observation: opened the pre-approval log result files while listing the world, then excluded them (a harness leak, not graded).
