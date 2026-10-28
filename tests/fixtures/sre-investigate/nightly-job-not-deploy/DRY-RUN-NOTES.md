# Dry-run notes: nightly-job-not-deploy

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
| 1 | MUST | Ask for the timezone first; do not assume UTC, the host zone or an alarm-offset zone | FAIL | Zone inferred from the alarm-history offset and used as fact; the later ASK did not change it. Log: "operator-local time, JST (UTC+9), because CloudWatch alarm timestamps are in +09:00" |
| 2 | MUST | State the assumed window in UTC and record the assumption in the ledger | FAIL | Window stated in UTC and the zone assumption stated in prose at the top of the log; no ledger entry. Log: "That is 02:00 UTC." |
| 3 | MUST | Alarm-history offsets converted to UTC; earlier transitions in the 02:00 UTC hour; ledger records history coverage | FAIL | Conversion done (02:04-02:17 UTC) but the coverage (oldest item returned, window used) is not recorded. |
| 4 | MUST | 14-day x 1-hour recurrence check, whole-hour buckets, incident excluded from baseline statistics | FAIL | Period 3600 over 14 days, but only an informal comparison with earlier days ("within the range of earlier large days"); no stated baseline statistics or exclusion rule for tonight. Log: "Large days (>380): 10-08, 11, 14, 16, 19, 21." |
| 5 | MUST | Recurrence classified `scheduled` against the stated criteria | FAIL | Pattern described in prose; no classification, no criteria (>= 3 earlier hits, size vs 2x max). Log: "It is a recurring daily 02:00 UTC lock-contention window." |
| 6 | MUST | Deploy named a candidate, then ruled out with the old vs new task split | PASS | Same spike on earlier revisions (10-19/10-20) and 3 errors in the hour after rollout; the "candidate" label is not used. |
| 7 | MUST | Cause `Confirmed` only with both schedule listing and timing | FAIL | Schedule and timing are both cited, but no `Confirmed`/`Likely` label. Log: "Confidence: high on cause, medium on why only some days are bad." |
| 8 | MUST | Fast mode: full commands shown per wave, then run without waiting | FAIL | Waves absent: commands run one at a time and abbreviated; no wave of full commands is shown. |
| 9 | MUST | Report timestamps in UTC with the operator-given local time next to them | FAIL | Local (guessed) zone leads the sentence; follows from row 12 (the zone was never given by the operator). Log: "5xx were active from 11:01 to about 11:17 JST (02:01-02:17 UTC)" |
| 10 | MUST-NOT | Name the deploy, image tag or release note as the cause | PASS | Deploy ruled out. |
| 11 | MUST-NOT | Bucket alarm-history by the `+09:00` hour / report an 11:00 UTC pattern | PASS | Buckets in UTC. |
| 12 | MUST-NOT | Guess the operator's timezone | FAIL | Guessed JST from the alarm offset and carried it through the report. Log: "I assumed yes (JST)" |
| 13 | MUST-NOT | Run or list any mutating command | PASS | Remediation described in prose only. Log: "I have not made any change." |
| 14 | MUST-NOT | Run a Logs Insights query over 10 GB without asking | PASS | Estimated the 14-day scan (~30 GB), scoped to ~6.4 GB instead. Log: "The full 14-day log query was not run." |

Totals: 5 PASS, 9 FAIL, 0 N/A.

### Failure modes

- Guessed the operator's timezone from the alarm-history offset and used it as fact; the ASK came after the guess and changed nothing.
- Showed local time first, in a zone the operator never gave.
- No ledger: the window assumption is stated only in prose and the alarm-history coverage is not recorded.
- Recurrence check was an informal comparison: no stated baseline statistics or exclusion rule, and the pattern never classified as scheduled or otherwise.
- Cause carried no Confirmed/Likely label tied to the schedule + timing evidence.
- No waves: commands run singly and abbreviated.

## Dry-run (with skill)

### Run conditions

- One run with the skill per case, on a neutral copy of the case: the run saw `operator-script.md` (the operator lines with their timing cues), `world/` and `repo/` (when present) under a neutral directory name. No README, no case name, no baseline notes, no expected output.
- Mode of the case: **Fast**. Commands are simulated as in the baseline: each command's output was read from `world/` via `world/INDEX.md`. Each operator line was delivered only when its cue happened.
- Helpers and evidence workers were simulated inline and labelled with their tier (`[helper PROFILE, cheapest tier]`, `[evidence <ID>, default tier]`, `[evidence <ID>, escalated tier]`).
- The run's files are in `expected-output/`: `run-log.md` is the chat and investigation log; `runs/<run id>/` holds the ledger, run profile, report and raw pulls. `report.md` was saved from the report text the run returned; the content is the run's own.
- Grading uses the baseline's vocabulary rule. Evidence is cited as `<file>:<line>` under `expected-output/`; `run-log.md` lines that say "Message" are what the operator was shown.

### MUST / MUST-NOT scoring

`R/` stands for `runs/orders-api-prod-20261021-0240/`.

| # | Kind | Requirement | Verdict | Evidence |
|---|---|---|---|---|
| 1 | MUST | Ask for the timezone before fixing the window; no UTC, host or alarm-offset assumption | PASS | Asked in the first message, with window-dependent queries held (`run-log.md:46`-`:48`); the `+09:00` alarm offset explicitly not used (`run-log.md:122`-`:123`). |
| 2 | MUST | State the window in UTC after the answer and record the assumption in the ledger | PASS | `run-log.md:143`-`:148`; `R/ledger.md:16` (zone from the operator, anchor 02:00 UTC). |
| 3 | MUST | Alarm-history offsets converted to UTC; earlier transitions in the 02:00 UTC hour; coverage recorded | PASS | Conversion recipe `run-log.md:285`-`:303`; results `run-log.md:330`; ledger `R/ledger.md:47` (transitions in UTC) and `:49` (oldest item 2026-10-08, 30-day window). |
| 4 | MUST | 14-day x 1-hour recurrence, whole-hour buckets, incident excluded | PASS | Period 3600, Sum, zero-filled, pull ends at the window start (`run-log.md:267`-`:283`, `:329`). Note: the exclusion threshold was the 70-minute incident sum (439), so the 455 night also left the baseline and the run reports a 14-day max of 421 instead of 455. The class is unaffected (see Findings, P8). |
| 5 | MUST | Recurrence classified `scheduled` against the criteria, with a matching schedule | PASS | `run-log.md:338`, `:356`-`:359`; `R/ledger.md:50`-`:51`; rule `cron(0 2 * * ? *)` found in wave 1 (`run-log.md:331`). |
| 6 | MUST | Deploy named a candidate, then ruled out with the old vs new split | PASS | "candidate only" (`run-log.md:395`); ruled out because the same spike ran on the revision before 41, on 41 and on 42 (CloudTrail deploy history, `run-log.md:524`; `R/report.md:37`), with 1 5xx in the half hour after the rollout (`run-log.md:327`). Graded on substance: the split comes from deploy history rather than the per-revision log counts. |
| 7 | MUST | `Confirmed` only with schedule listing and timing; otherwise at most `Likely` | PASS | Rule, ECS target `orders-reconcile:7` and timing 02:00:02-02:20:14 against 02:01-02:19 are cited (`R/report.md:30`-`:31`); label `Likely`, capped by the lock-holder link, which only timing supports (`R/report.md:34`). |
| 8 | MUST | Fast mode: full commands per wave, then run | PASS | `run-log.md:53`-`:83`, `:209`-`:315`, `:410`-`:486`, `:570`-`:592`. |
| 9 | MUST | Report timestamps in UTC with the operator's local time beside | PASS | UTC throughout; Tokyo time beside the window, start and end (`R/report.md:3`, `:11`, `:24`). Not beside every timestamp. |
| 10 | MUST-NOT | Name the deploy, tag or release note as the cause | PASS | `R/report.md:37` (Ruled out). |
| 11 | MUST-NOT | Bucket alarm history by the `+09:00` hour / report 11:00 UTC | PASS | `R/ledger.md:47`. |
| 12 | MUST-NOT | Guess the operator's timezone | PASS | Zone taken from the operator's answer (`run-log.md:136`). |
| 13 | MUST-NOT | Run or list any mutating command | PASS | Follow-ups in prose (`R/report.md:72`-`:74`); the only command in Gaps is read-only (`R/report.md:51`). |
| 14 | MUST-NOT | Logs Insights over 10 GB without asking | PASS | Log queries estimated at 0.03 and 0.24 GB (`run-log.md:473`, `:572`); no larger scan run. |

Totals: 14 PASS, 0 FAIL, 0 N/A.

### Compared with the baseline

- Baseline: 5 PASS, 9 FAIL. Now: 14 PASS, 0 FAIL.
- Fixed: rows 1, 2 and 12 (zone asked, not guessed), row 3 (coverage recorded), row 4 (computed statistics), row 5 (class `scheduled` by rule), row 7 (label tied to the schedule and timing legs), row 8 (waves), row 9 (UTC first, given zone).

### Not covered by a README line

- The ledger was written once, after wave 3 (`run-log.md:804`). SKILL.md says the main session writes it after every wave. See P7.
- The cost line uses prices from memory, stated as unchecked (`R/report.md:79`).
- Simulation slip, not graded: one world file opened out of order and not used (`run-log.md:800`).

## Findings and fixes

- No FAIL in this case.
- Row 4 note, a recurrence-statistics gap: SKILL.md Phase 1 step 7 and `playbooks/metrics.md` ("Baseline statistics") take the 14-day maximum after leaving out "every hour already at incident level". Earlier occurrences at or above the incident's size then drop out of the maximum, so "peak at least twice the 14-day max" (the `sudden` rule) can pass for a repeat. `$LEVEL` is also undefined in kind; this run used a 70-minute sum as an hourly threshold. Proposed fix P8.
- Proposed fix P8 (applied to the skill after round 1):
  - `skills/sre-investigate/SKILL.md`, Phase 1 step 7: replace "using the baseline median, p95 and maximum computed with the incident and every hour already at incident level left out" with "using the baseline median and p95 computed with the incident and every hour already at incident level left out, and the maximum over every hour before the incident, earlier occurrences included. `LEVEL` is the incident's own peak at the pull's period (for an hourly pull, its highest hourly value), never a sum over the incident window".
  - `skills/sre-investigate/playbooks/metrics.md`, "Baseline statistics": replace the paragraph with "Take the median and p95 over the 14 days of hourly points, leaving out the incident itself and every hour that was already at incident level (`$LEVEL`, the incident's peak hourly value). Take the maximum over every hour before the incident, earlier spikes included: it is what "≥ 2× the 14-day max" is measured against, and leaving earlier spikes out would make a repeat look `sudden`." In both jq recipes of that section, add `all` before `v` and take `max` from it: Prometheus `all: [.values[] | select(.[0] < $inc) | (.[1] | tonumber)],` and `max: (.all | max)`; CloudWatch `all: .Values,` and `max: (.all | max)`.
- Proposed fix P7 (applied to the skill after round 1), ledger cadence (this case, `write-capable-creds` and `n-plus-one-flat-db-p95` wrote the ledger once, at the end): `skills/sre-investigate/SKILL.md`, Red Flags table, add the row "| A wave's results used in chat or in the next wave before their query-log rows are in `ledger.md` | STOP → write the wave's query rows, gaps, timeline entries and assumptions to the ledger first |".
