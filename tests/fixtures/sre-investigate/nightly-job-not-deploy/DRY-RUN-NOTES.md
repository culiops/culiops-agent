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
