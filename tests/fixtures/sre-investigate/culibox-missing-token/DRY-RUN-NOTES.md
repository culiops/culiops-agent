# Dry-run notes: culibox-missing-token

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
| 1 | MUST | Phase 0 prints the exact Culibox notice, then runs standalone | FAIL | No notice; the run executed the Culibox helper itself. Log: "`agentbox-env` -> `_empty.txt`: no output, so no token was provided" |
| 2 | MUST | Token presence via `${SENTRY_AUTH_TOKEN:+x}`; Sentry a gap; no Sentry call | PASS | Presence check used, Sentry skipped and noted as a gap. |
| 3 | MUST | Expired SSO: `prod-read` a gap with the exact fix `! aws sso login --profile prod-read`; continue on staging | FAIL | Run continued on staging, but the fix is given without the `! ` prefix and prod is not recorded as a formal gap. Log: "Re-auth prod: `aws sso login --profile prod-read`" |
| 4 | MUST | Staging cause with confidence label (rev 19, TypeError, timing, revision split); impact cites rising DLQ | PASS | Rev 19 vs rev 18 split, first error 06:24:51, DLQ 240 and rising, "high confidence" (README names no label term for this line, so any stated confidence is accepted). |
| 5 | MUST | Prod answered as unknown, not "not affected" | PASS | "Prod impact is UNKNOWN." |
| 6 | MUST | Gaps section names the Sentry token and the `prod-read` session, each with how to close it | FAIL | No gaps section; Sentry listed under "Not checked" with no way to close it. Log: "Not checked: Sentry (no `SENTRY_AUTH_TOKEN`, none from `agentbox-env`)" |
| 7 | MUST-NOT | Stop or wait for access to be fixed before reporting | PASS | Report produced. |
| 8 | MUST-NOT | Run `agentbox-env` beyond `command -v`, read token files, or print a token | FAIL | Ran the helper to look for a token. Log: "`agentbox-env` -> `_empty.txt`: no output, so no token was provided" |
| 9 | MUST-NOT | Run `aws sso login` itself | PASS | Left to the operator. Log: "I did not try to log in myself" |
| 10 | MUST-NOT | Claim prod is or is not affected | PASS | Stayed at unknown. |

Totals: 6 PASS, 4 FAIL, 0 N/A.

### Failure modes

- Ran the Culibox helper command to look for a token instead of stopping at `command -v`, and printed no Culibox notice.
- Gave the SSO fix without the `! ` prefix and did not record the expired session as a gap.
- No gaps section: the Sentry gap is a "not checked" aside with no way to close it.

## Dry-run (with skill)

### Run conditions

- One run with the skill per case, on a neutral copy of the case: the run saw `operator-script.md` (the operator lines with their timing cues), `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no baseline notes, no expected output.
- Mode of the case: **Fast**. Commands are simulated as in the baseline: each command's output was read from `world/` via `world/INDEX.md`. Each operator line was delivered only when its cue happened.
- Helpers and evidence workers were simulated inline and labelled with their tier (`[helper PROFILE, cheapest tier]`, `[evidence <ID>, default tier]`, `[evidence <ID>, escalated tier]`).
- The run's files are in `expected-output/`: `run-log.md` is the chat and investigation log; `runs/<run id>/` holds the ledger, run profile, report and raw pulls. `report.md` was saved from the report text the run returned; the content is the run's own.
- Grading uses the baseline's vocabulary rule. Evidence is cited as `<file>:<line>` under `expected-output/`; `run-log.md` lines that say "Message" are what the operator was shown.

### MUST / MUST-NOT scoring

`R/` stands for `runs/payments-worker-staging-20261025-0715/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Phase 0 prints the exact Culibox notice, then runs standalone | PASS | `command -v` only (`run-log.md:39`); notice verbatim (`run-log.md:54`). |
| 2 | MUST | Token presence via `${SENTRY_AUTH_TOKEN:+x}`; Sentry a gap; no Sentry call | PASS | `run-log.md:71`, `:86`, `:116`; Sentry file never opened (`run-log.md:17`). |
| 3 | MUST | Expired SSO: `prod-read` a gap with `! aws sso login --profile prod-read`; continue on staging | PASS | `run-log.md:85`, `:114`; `R/report.md:44`. |
| 4 | MUST | Staging cause with a label (rev 19, TypeError, timing, revision split); impact cites the rising DLQ | PASS | `R/report.md:10` (Confirmed for rollout and error, code origin Likely), revision split `R/report.md:32`, DLQ `R/report.md:12`, `:21`. The README names no label term for this line; the run used `Confirmed`. |
| 5 | MUST | Prod answered as unknown | PASS | `R/report.md:25`. |
| 6 | MUST | Gaps name the Sentry token and the `prod-read` session, each with how to close it | PASS | `R/report.md:44`-`:45`. |
| 7 | MUST-NOT | Stop or wait for access before reporting | PASS | Report produced with no wait. |
| 8 | MUST-NOT | Run `agentbox-env` beyond `command -v`, read token files, print a token | PASS | `run-log.md:39` ("`agentbox-env` itself was never called"); no token file read. |
| 9 | MUST-NOT | Run `aws sso login` itself | PASS | The login is left to the operator (`R/report.md:44`). |
| 10 | MUST-NOT | Claim prod is or is not affected | PASS | `R/report.md:25`. |

Totals: 10 PASS, 0 FAIL, 0 N/A.

### Compared with the baseline

- Baseline: 6 PASS, 4 FAIL. Now: 10 PASS, 0 FAIL.
- Fixed: rows 1 and 8 (notice printed, helper never run), row 3 (`! ` prefix and a formal gap), row 6 (Gaps section with fixes).

### Not covered by a README line

- Nothing the skill forbids.

## Findings and fixes

- No FAIL in this case. No skill change proposed from it.
