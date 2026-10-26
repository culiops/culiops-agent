---
open-questions-schema: 2
service: payments
generated-at: 2026-05-12T15:35:00Z
high-priority-count: 1
medium-priority-count: 4
low-priority-count: 1
---

# Open Questions — payments

**Generated:** 2026-05-12T15:35:00Z

## Summary

| Priority | Count |
|---|---|
| High | 1 |
| Medium | 4 |
| Low | 1 |

Runtime-trace was skipped by the operator (time constraint), not because anything was denied.

Every `✗ conflict` in the scorecard is High by rule. `◐` and `?` items are listed in the scorecard with the check that would settle each; only the ones that need someone else's action appear here.

---

## High Priority (blockers — resolve before sign-off)

### HIGH-1 — No runtime profile: items 5, 7, 8, 9 are `?`; items 2, 16, 18, 19, 25 cannot be cross-checked

- **Source:** state.md Step 4 (skipped); readiness-scorecard.md items 2, 5, 7, 8, 9, 16, 18, 19, 25
- **Detail:** The operator skipped runtime-trace for time. The cross-Region footprint, activity baseline, deploy-event history, managing principals and configured callers (Wiring) are all unknown, and the interview claims on deploy frequency, callers and DR cannot be checked.
- **Suggested action:** Run runtime-trace (about 30 minutes of gate approvals, about $0.03; Cost Explorer is not required for the other sections) and resume at Step 4; re-score.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-01

---

## Medium Priority (should resolve within 30 days of handoff)

### MED-1 — Restore test is operator-stated, not attested (item 24)

- **Source:** readiness-scorecard.md item 24; interview Section 10; catalog PITR row
- **Detail:** Backups are in place on `payments-ledger` (PITR). The 2026-02-15 restore test was run by the Pay Team; nobody on the incoming team has witnessed one.
- **Suggested action:** Witness a PITR restore into a scratch table (Carol repeats it), then attest the date.
- **Owner:** alice (Platform Team) and Carol P.
- **Target date:** 2026-07-15

### MED-2 — Runbook, postmortem and rollback links not yet opened (items 13, 14, 17)

- **Source:** readiness-scorecard.md items 13, 14, 17
- **Detail:** 5 runbooks, 2 postmortems and the rollback runbook are listed under docs.example.com; none has been opened by the incoming team.
- **Suggested action:** Open each link and confirm it matches its symptom; cite the paths in the scorecard.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08

### MED-3 — Stripe contract owner and PII scope need confirmation (items 21, 22)

- **Source:** readiness-scorecard.md items 21, 22; interview Sections 8 and 10
- **Detail:** Contract ownership (Bob L., renewal 2027-03) and the PII scope are policy statements AWS cannot confirm.
- **Suggested action:** Confirm the contract owner with procurement and the PII scope with the security contact.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

### MED-4 — alice's console read access to Secrets Manager should be revoked after handoff

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
