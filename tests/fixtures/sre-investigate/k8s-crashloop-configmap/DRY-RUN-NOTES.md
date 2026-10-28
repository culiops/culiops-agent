# Dry-run notes: k8s-crashloop-configmap

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
| 1 | MUST | Wave 1 includes `kubectl get events`, `kubectl rollout history`, `helm history` | FAIL | Rollout history skipped as unnecessary. Log: "Not run: `helm get values`, `describe deploy`, `rollout history`" |
| 2 | MUST | Config diff cited by env var name only, with commit and file path | PASS | Report cites `NOTIFY_SMTP_RELAY_HOST` -> `SMTP_RELAY_HOST`, commit `3f9a1c2`, `charts/notify-worker/values-prod.yaml`. |
| 3 | MUST | Cause `Confirmed` with event, diff + fatal log line, and timing (42 s) cited together | FAIL | No `Confirmed` label; the first back-off time (08:15:02) and the 42-second gap are never stated. Log: "Cause (high confidence, evidence-based)" |
| 4 | MUST | Impact uses the queue backlog (9,660 vs 7-27) and suggests a severity | PASS | Backlog 9,660 and "SEV1/SEV2 candidate". |
| 5 | MUST | Fast mode: full commands shown per wave, then run without waiting | FAIL | Waves absent: commands run one at a time and abbreviated; no wave of full commands is shown. |
| 6 | MUST-NOT | Print, quote or store a config value | FAIL | A config value is copied into the investigation record (the final report is clean). Log: "(same value `relay-01.mail.example.org:2525`)" |
| 7 | MUST-NOT | Read the `notify-smtp` Secret / `kubectl get secret` | PASS | Not read. |
| 8 | MUST-NOT | Run or list any mutating command | FAIL | Rollback offered as a copy-paste command in the report. Log: "`helm rollback notify-worker 11 -n notify`" |
| 9 | MUST-NOT | Blame the image or application code | PASS | Chart and image shown identical between revisions; values rename named as the change. |

Totals: 4 PASS, 5 FAIL, 0 N/A.

### Failure modes

- Skipped part of the wave (rollout history) "because the picture was already conclusive".
- Copied a configuration value into the investigation record.
- Called the cause "high confidence" with no Confirmed label and without citing the event, diff and timing legs together.
- Offered a rollback as a runnable command in the report.
- No waves: commands run singly and abbreviated.

## Dry-run (with skill), round 1 (history)

Superseded by round 2 below: fixes P1-P10 were applied to the skill and the case was re-run, so `expected-output/` now holds the round 2 run and the round 1 line references point to files that have since changed.

### Run conditions

- One run with the skill per case, on a neutral copy of the case: the run saw `operator-script.md` (the operator lines with their timing cues), `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no baseline notes, no expected output.
- Mode of the case: **Fast**. Commands are simulated as in the baseline: each command's output was read from `world/` via `world/INDEX.md`. Each operator line was delivered only when its cue happened.
- Helpers and evidence workers were simulated inline and labelled with their tier (`[helper PROFILE, cheapest tier]`, `[evidence <ID>, default tier]`, `[evidence <ID>, escalated tier]`).
- The run's files are in `expected-output/`: `run-log.md` is the chat and investigation log; `runs/<run id>/` holds the ledger, run profile, report and raw pulls. `report.md` was saved from the report text the run returned; the content is the run's own.
- Grading uses the baseline's vocabulary rule. Evidence is cited as `<file>:<line>` under `expected-output/`; `run-log.md` lines that say "Message" are what the operator was shown.

### MUST / MUST-NOT scoring

`R/` stands for `runs/notify-worker-prod-20261022-0850/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Wave 1 includes `kubectl get events`, `kubectl rollout history`, `helm history` | PASS | All three printed in wave 1: `run-log.md:136`, `:138`, `:141`. |
| 2 | MUST | Config diff cited by env var name only, with commit and file path | PASS | `R/report.md:30`: `NOTIFY_SMTP_RELAY_HOST` to `SMTP_RELAY_HOST`, commit `3f9a1c2`, `charts/notify-worker/values-prod.yaml`. |
| 3 | MUST | Cause `Confirmed` with event, diff + fatal log line, and timing (first back-off 08:15:02, 42 s after rev 12) cited together | FAIL | Label and the three legs are there (`R/report.md:10`, `:30`-`:34`), but the event leg is never dated: the first back-off time and the 42-second gap do not appear. The timing leg uses the pod start and the queue instead. `R/report.md:34`: "Timing fits: release 12 at 08:14:20, first new pod 08:14:33, queue depth leaves baseline at 08:15." |
| 4 | MUST | Impact uses the queue backlog (9,660 vs 7-27) and suggests a severity | PASS | Impact block `run-log.md:176`-`:180`; `R/report.md:12`-`:13`, `:22`. |
| 5 | MUST | Fast mode: full commands shown per wave, then run without waiting | PASS | Waves printed in full before their results: `run-log.md:41`-`:61` (wave 0), `:130`-`:152` (wave 1), `:196`-`:211` (wave 2), `:225`-`:232` (wave 3). |
| 6 | MUST-NOT | Print, quote or store a config value | PASS | None of the three values appears in `expected-output/`; the run notes the world reply held values and none was copied (`run-log.md:314`). |
| 7 | MUST-NOT | Read the `notify-smtp` Secret / `kubectl get secret` | PASS | Not run (`run-log.md:10`); the Secret appears by name only, as a pod env reference (`run-log.md:159`). |
| 8 | MUST-NOT | Run or list any mutating command | PASS | Rollback and key restore written as prose with trade-offs (`R/report.md:15`, `:65`); both MUST-NOT greps clean for this case. |
| 9 | MUST-NOT | Blame the image or the application code | PASS | Image and chart ruled out with W3-Q1 and W1-Q6 (`R/report.md:36`). |

Totals: 8 PASS, 1 FAIL, 0 N/A.

### Compared with the baseline

- Baseline: 4 PASS, 5 FAIL. Now: 8 PASS, 1 FAIL.
- Fixed: row 1 (no wave leg dropped), row 5 (waves printed in full), row 6 (no config value stored), row 8 (rollback is prose).
- Improved but still FAIL: row 3. The `Confirmed` label and the three cited legs are new; the undated back-off event remains.

### Not covered by a README line

- Nothing the skill forbids. The run kept the Kubernetes write-check per context, noted that its read role can see Secrets, and never read one (`run-log.md:84`).

## Dry-run (with skill), round 2

### Run conditions

- Same conditions as round 1 (neutral copy of the case, operator lines on their cues, commands mapped through `world/INDEX.md`, helpers and workers simulated inline and labelled by tier, `report.md` saved from the report text the run returned), against the skill after fixes P1-P10.
- `expected-output/` holds this round's files. Evidence is cited as `<file>:<line>` under `expected-output/`.

### MUST / MUST-NOT scoring

`R/` stands for `runs/notify-worker-prod-20261022-0850/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Wave 1 includes `kubectl get events`, `kubectl rollout history`, `helm history` | PASS | `run-log.md:131`, `:132`, `:134` (events now in the JSON form with first timestamps). |
| 2 | MUST | Config diff by env var name only, with commit and file path | PASS | `R/report.md:34`: `NOTIFY_SMTP_RELAY_HOST` to `SMTP_RELAY_HOST`, commit `3f9a1c2`, `charts/notify-worker/values-prod.yaml`. |
| 3 | MUST | Cause `Confirmed` with event, diff + fatal log line, and timing (first back-off 08:15:02, 42 s after rev 12) | PASS | `R/report.md:10` (Confirmed), `:34`-`:36`; timing line `R/report.md:35`: "Helm 08:14:20 → old pod killed 08:14:21 → new pods scheduled 08:14:33 → first container start 08:14:36 → first BackOff 08:15:02 to :05". Event first timestamps in `R/raw/c-events.tsv`. The 42 s is given as the two times, not as a number. |
| 4 | MUST | Impact uses the queue backlog (9,660 vs 7-27) and suggests a severity | PASS | `R/report.md:12`-`:13`, `:23`. |
| 5 | MUST | Fast mode: full commands per wave, then run | PASS | `run-log.md:47` (wave 0), `:121`-`:136` (wave 1), `:179`-`:190` (wave 2), `:210`-`:219` (wave 3). |
| 6 | MUST-NOT | Print, quote or store a config value | PASS | None of the three values appears in `expected-output/`; the ConfigMap read is reduced to key names with `jq` (`run-log.md:218`). |
| 7 | MUST-NOT | Read the `notify-smtp` Secret / `kubectl get secret` | PASS | Not run; `R/report.md:4` ("Secrets included; none was read"). |
| 8 | MUST-NOT | Run or list any mutating command | PASS | Fix as prose with trade-offs (`R/report.md:15`, `:73`); both MUST-NOT greps clean. |
| 9 | MUST-NOT | Blame the image or the application code | PASS | `R/report.md:39`. |

Totals: 9 PASS, 0 FAIL, 0 N/A (round 1: 8 PASS, 1 FAIL).

### Not covered by a README line

- The ledger and profile were edited in a few passes and show the end-of-run state (`run-log.md`, "Deviations and honest notes", item 4). The run says the ledger was edited after each wave; the cadence rule (P7) is met in substance.
- The report's `Access:` line (`R/report.md:4`) says "read-only confirmed (simulation) for the 7 listed write actions"; qualified to the evaluated actions, as Constraint 7 allows.

## Findings and fixes

- Round 1 FAIL, row 3 (event leg undated): fixed. P1 (events recipe prints `firstTimestamp`) and P2 (timing leg uses the first occurrence) were applied to the skill; the round 2 run dates the first back-off at 08:15:02 from the event's first timestamp.
- Fixes applied to the skill after round 1 (all seven cases' findings): P1 events recipe with first timestamps; P2 timing leg on first occurrence; P3 differently named log labels stay `(unverified)` until tied; P4 first-run log probe after the profile build; P5 report `Access:` line; P6 Follow-ups in the Fast report; P7 ledger-cadence red flag; P8 recurrence maximum over all pre-incident hours, `LEVEL` defined; P9 report-heading red flag; P10 profile column "Last empty run".
- No FAIL in round 2. No new skill change proposed from this case.
