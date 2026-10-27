---
open-questions-schema: 2
service: payments
generated-at: 2026-05-12T15:35:00Z
high-priority-count: 0
medium-priority-count: 7
low-priority-count: 1
---

# Open Questions — payments

**Generated:** 2026-05-12T15:35:00Z

## Summary

| Priority | Count |
|---|---|
| High | 0 |
| Medium | 7 |
| Low | 1 |

Runtime-trace was skipped by the operator (time constraint), not because anything was denied. No item is `✗` or `✗ conflict`, so there is no High item.

Priority follows the scorecard rule: every `✗` and `✗ conflict` is High; every `?` and `◐` is Medium; notes on `✓` items are Low. Within a level the cheapest resolution comes first (a Step 6 check, then a document to open, then an outgoing-team follow-up). Each entry names its item and mark.

---

## High Priority (blockers — resolve before sign-off)

*None: no item is `✗` or `✗ conflict`.*

---

## Medium Priority (should resolve within 30 days of handoff)

### MED-1 — No runtime profile: items 5, 7, 8, 9 are `?`; items 4, 2, 16, 18, 19, 25 cannot be cross-checked (`?`, `◐`)

- **Source:** state.md Step 4 (skipped); readiness-scorecard.md items 2, 4, 5, 7, 8, 9, 16, 18, 19, 25
- **Detail:** The operator skipped runtime-trace for time. The cross-Region footprint, activity baseline, deploy-event history, managing principals and configured callers (Wiring) are all unknown, the catalog cannot be compared with the profile's resource list, and the interview claims on deploy frequency, callers and DR cannot be checked.
- **Suggested action:** Run runtime-trace (about 30 minutes of gate approvals; its Cost Explorer calls are billed per request and are not required for the other sections) and resume at Step 4; re-score.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-01

### MED-2 — Alarm coverage is incomplete (item 10, `◐`)

- **Source:** readiness-scorecard.md item 10; interview-questionnaire.md Section 5
- **Detail:** The 5 named alarms exist, are enabled and have actions, but there is none on `payments-ledger` and no throttle or concurrency alarm on the Lambdas.
- **Suggested action:** Pay Team adds the missing alarms or records why a resource needs none; re-run `describe-alarms` (Step 6 check).
- **Owner:** Carol P. (Pay Team) and alice
- **Target date:** 2026-06-08

### MED-3 — Retention period is not a configured period (item 23, `◐`)

- **Source:** readiness-scorecard.md item 23; interview Section 10; catalog `payments-ledger` row
- **Detail:** The interview says 7 years plus a 90-day grace. TTL on `expires_at` is enabled, but each record's expiry is data, so no configuration shows the period.
- **Suggested action:** Open the retention policy, or the code that sets `expires_at`, and cite it.
- **Owner:** alice (Platform Team) and Bob L.
- **Target date:** 2026-06-15

### MED-4 — Runbook, postmortem and rollback links not yet opened (items 13, 14, 17, `◐`)

- **Source:** readiness-scorecard.md items 13, 14, 17
- **Detail:** 5 runbooks, 2 postmortems and the rollback runbook are listed under docs.example.com; none has been opened by the incoming team.
- **Suggested action:** Open each link and confirm it matches its symptom; cite the paths in the scorecard.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08

### MED-5 — Restore test has no record (item 24, `◐`)

- **Source:** readiness-scorecard.md item 24; interview Section 10; catalog PITR row
- **Detail:** Backups are in place on `payments-ledger` (PITR). The 2026-02-15 restore test is a date the Pay Team stated; the incoming team has no ticket or run log for it.
- **Suggested action:** Open the Pay Team's ticket or runbook run log for that test and cite it, or witness a PITR restore into a scratch table (Carol repeats it) and record the run.
- **Owner:** alice (Platform Team) and Carol P.
- **Target date:** 2026-07-15

### MED-6 — Stripe contract owner and PII scope need confirmation (items 21, 22, `◐`)

- **Source:** readiness-scorecard.md items 21, 22; interview Sections 8 and 10
- **Detail:** Contract ownership (Bob L., renewal 2027-03) and the PII scope are policy statements AWS cannot confirm.
- **Suggested action:** Confirm the contract owner with procurement and the PII scope with the security contact.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

### MED-7 — alice's console read access to Secrets Manager should be revoked after handoff

- **Source:** interview-questionnaire.md Sections 9 and 11
- **Detail:** alice has console read access to the payments secrets for debugging.
- **Suggested action:** Revoke after the 2026-06-15 handoff.
- **Owner:** alice and Pay Team
- **Target date:** 2026-06-16

---

## Low Priority

### LOW-1 — API Gateway `abc123def456` ownership and spend; SNS `payments-events` unattributed

- **Source:** service-catalog.md Unattributed list; runtime-profile.md Spend (account context)
- **Detail:** Neither carries the `service` tag; the gateway also fronts other services.
- **Suggested action:** Decide whether to tag them or keep them as dependencies.
- **Owner:** alice (Platform Team)

---

## Resolved items

*None at this time.*
