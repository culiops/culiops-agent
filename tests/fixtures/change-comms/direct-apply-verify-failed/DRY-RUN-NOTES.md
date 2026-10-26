# Dry-run notes: change-comms against direct-apply-verify-failed

New fixture added in the final-review fix wave. It proves that a direct-apply record with Outcome `completed` but a failing Verification line is not reported as `✅ Done`. First simulated run is round 6 below; run transcript not committed.

## Round 6 (final skill 656ac5b)

Simulated run against the final skill (656ac5b). The record shows Outcome `completed` and `Apply complete!`, but its Verification line still shows one change and the alarm in `ALARM`. The run refused `✅ Done`, asked the operator for the apply time and outcome in one batch, then asked once whether it was rolled back (no scripted answer, so it is a TODO). The result is `❌ Failed` and states the verification problem.

Drafts as produced:

result (Google Chat), `expected-output/shipping-api-add-p99-alarm-20261026-1500-result.md`:

```text
*❌ Failed: shipping-api p99 latency alarm (live), applied 09:25 CET*
State: applied with the wrong threshold (0.8, expected 800), alarm currently in ALARM, <TODO: rolled back or not>
Next: rolling forward tomorrow (2026-10-27 CET)
Ticket: SHIP-204
```

### Findings (round 6)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: asks for apply outcome and apply time in one batch | pass | `direct-apply-verify-failed-r6.md` l.47-50; the rolled-back follow-up is a dependent item (l.66) |
| MUST: result uses `❌` or `⏸`, not `✅` | pass | result.md l.9 (`❌ Failed`) |
| MUST: verification problem stated, cited to `#Execution Log` | pass | result.md l.10, l.27 |
| MUST: next steps from the operator, absolute date 2026-10-27 or `tomorrow` | pass | result.md l.11, l.30 |
| MUST: apply time `09:25 CET` | pass | result.md l.9, l.26 |
| MUST: rolled back or not from the operator's words, or a visible TODO | pass | result.md l.10, l.29, l.38 (`<TODO: rolled back or not>`) |
| MUST: ticket `SHIP-204` | pass | result.md l.12, l.31 |
| MUST-NOT: `✅` in the draft | pass | `grep -nE '✅|Done' direct-apply-verify-failed/expected-output/*` returns nothing |
| MUST-NOT: `Done` in the draft | pass | same grep returns nothing |
| MUST-NOT: verification passed / complete / verified / healthy claim | pass | result.md l.9-12 say failed, wrong threshold, ALARM |
| MUST-NOT: `09:40` as the apply time | pass | `09:40` appears only in the Sources date (l.4) and record paths; the apply time is `09:25 CET` (l.9) |
| MUST-NOT: cause, retry window or follow-up the operator did not give | pass | result.md l.11 repeats only the operator's `rolling forward tomorrow` |
| MUST-NOT: plan counts or CLI commands in the draft | pass | `grep -nE '1 to change|1 added|terraform|aws ' direct-apply-verify-failed/expected-output/*` returns nothing |
| MUST-NOT: values from other fixtures or the examples | pass | `grep -nwE 'orders-api|OPS-123|ICT|billing-api|PAY-77|HKT'` over expected-output returns nothing |
| Final-fix I1: `✅ Done` refused because verification is not clean | pass | `direct-apply-verify-failed-r6.md` l.40 |

Round 6: 15 pass, 0 FAIL (README lines plus final-fix checks). No skill change.
