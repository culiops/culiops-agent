# direct-apply-verify-failed

## Scenario

One-phase Terraform change applied directly from the operator's machine: add a CloudWatch p99 latency alarm for `shipping-api` (env `live`). The record `shipping-api-add-p99-alarm-20261026-0940.md` has Execution path `Direct apply`, Outcome `completed`, and an `Execution:` line ending `Apply complete!`. But its `Verification:` line shows the post-apply re-plan still has 1 change (the alarm threshold) and the alarm in `ALARM` state. So the record does not show a clean success, and the outcome must come from the operator. The operator answers the outcome question with `applied but the alarm threshold is wrong, rolling forward tomorrow`.

Exercises: the direct-apply ✅ rule (Outcome `completed` plus "Apply complete!" is not enough when verification is not clean), asking the operator for the outcome in the one batch, stating the verification problem, and operator-only next steps.

## Records

| File | Role |
|---|---|
| `.culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md` | Direct apply; Outcome `completed`; Verification `re-plan: 1 to change (… threshold 0.8 → 800); … StateValue = ALARM`; Ticket Reference `https://northwind.atlassian.net/browse/SHIP-204` |

## MUST

- The skill asks the operator for the apply outcome (and the apply time) in one batch, because the record's verification is not clean.
- The result uses `❌` or `⏸`, not `✅`.
- The result states the verification problem in plain words (the re-plan still shows a change to the alarm threshold, or the alarm is not in its expected state). The fact table cites it to `record: .culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md#Execution Log`.
- Next steps come from the operator (rolling forward). Run date for this fixture is 2026-10-26, so `tomorrow` = 2026-10-27. The draft shows an absolute date (2026-10-27) or keeps `tomorrow`; it must never show a different date.
- The apply time is the operator's `09:25 CET`.
- Whether it was rolled back is taken from the operator's words (not rolled back, rolling forward) or left as a visible TODO, never invented.
- The ticket is `SHIP-204`.

## MUST-NOT

- `✅` in the draft.
- `Done` in the draft.
- Any statement that verification passed, or that the change is complete, verified or healthy.
- The string `09:40` shown as the apply time (the record `Date` is when the record was written).
- A cause, retry window or follow-up the operator did not give (for example a "likely cause" or a promised time for the roll-forward).
- Plan counts (`1 to change`, `1 added`) or CLI commands in the draft.
- Any value from another fixture or from the skill's examples (for example `orders-api`, `OPS-123`, `ICT`, `billing-api`, `PAY-77`, `HKT`).
