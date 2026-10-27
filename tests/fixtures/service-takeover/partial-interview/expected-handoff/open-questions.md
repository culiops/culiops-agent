---
open-questions-schema: 2
service: payments
generated-at: 2026-05-12T16:00:00Z
high-priority-count: 1
medium-priority-count: 9
low-priority-count: 1
---

# Open Questions — payments

**Generated:** 2026-05-12T16:00:00Z

## Summary

| Priority | Count |
|---|---|
| High | 1 |
| Medium | 9 |
| Low | 1 |

The one High item is the conflict; the outgoing-team follow-ups are Medium (`?`). The skill never asks the operator to fill in the missing answers.

Priority follows the scorecard rule: every `✗` and `✗ conflict` is High; every `?` and `◐` is Medium; notes on `✓` items are Low. Within a level the cheapest resolution comes first (a Step 6 check, then a document to open, then an outgoing-team follow-up). Each entry names its item and mark.

---

## High Priority (blockers — resolve before sign-off)

### HIGH-1 — `legacy-orders-exec` may send to `payments-capture-queue` but is not a listed caller (item 19 conflict)

- **Source:** runtime-profile.md Wiring (`wr-007`); interview-questionnaire.md Section 8
- **Detail:** The queue policy lets role `arn:aws:iam::123456789012:role/legacy-orders-exec` send messages. The interview lists only checkout-service and billing-service (via API Gateway) as upstream callers.
- **Suggested action:** Ask the Pay Team which service assumes the role and whether it is still in use; add it to Section 8 with a contact.
- **Owner:** Bob L. (Pay Team)
- **Target date:** 2026-06-01

---

## Medium Priority (should resolve within 30 days of handoff)

### MED-1 — DynamoDB `payments-ledger` has no activity baseline (item 7, `?`)

- **Source:** readiness-scorecard.md item 7; runtime-profile.md Gaps and Caveats
- **Detail:** 3 of 4 compute and data-store resources have a baseline row; `runtime-trace` does not collect `dynamodb:table` metrics. Until the table has one, item 7 is `?`.
- **Suggested action:** Query the table's CloudWatch metrics over a stated window and record the query (check, then add to the scorecard).
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08

### MED-2 — Verification batch declined: items 10 and 15 are unverified (`◐`)

- **Source:** readiness-scorecard.md Step 6; execution-plan.md addendum
- **Detail:** `describe-alarms` (alarms named in the interview), `simulate-principal-policy` and `get-context-keys-for-principal-policy` for `platform-team-deploy` were not run.
- **Suggested action:** Run the three read-only commands (a few minutes) and record the derived facts.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08

### MED-3 — Runbook and rollback links not yet opened (items 13, 17, `◐`)

- **Source:** readiness-scorecard.md items 13, 17
- **Detail:** 5 runbooks and the rollback runbook are listed under docs.example.com; none has been opened by the incoming team.
- **Suggested action:** Open each link and confirm it matches its symptom; cite the paths in the scorecard.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08

### MED-4 — Stripe contract owner needs confirmation (item 21, `◐`)

- **Source:** readiness-scorecard.md item 21; interview Section 8
- **Detail:** Contract ownership (Bob L., renewal 2027-03) is not verifiable from AWS.
- **Suggested action:** Confirm the contract owner with procurement.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

### MED-5 — Section 10 is empty: PII, retention, backups, restore test and DR are unknown (items 22-25, `?`)

- **Source:** interview-questionnaire.md Section 10 (empty); service-catalog.md PITR/TTL row
- **Detail:** Items 22-25 are `?`. The catalog shows PITR and TTL (`expires_at`) on `payments-ledger`, so backups and an expiry mechanism exist, but the policy, restore test and DR plan are unstated. An empty section is never `✗`.
- **Suggested action:** Return Section 10 to the outgoing team (Bob L.) for completion; do not fill it in on their behalf.
- **Owner:** Bob L. (Pay Team)
- **Target date:** 2026-06-01

### MED-6 — Incident history, recurring issues, MTTR and change failure rate are empty (item 14, `?`)

- **Source:** interview-questionnaire.md Section 6 (partial)
- **Detail:** Only the runbooks sub-section was filled. Absence of data is not absence of incidents.
- **Suggested action:** Return Section 6 to the outgoing team.
- **Owner:** Bob L. (Pay Team)
- **Target date:** 2026-06-08

### MED-7 — Section 3 is empty: SLOs, SLIs, error budget and dashboards not provided

- **Source:** interview-questionnaire.md Section 3 (empty)
- **Detail:** No scored item depends on Section 3, but alert thresholds and the on-call target cannot be judged without it.
- **Suggested action:** Return Section 3 to the outgoing team for completion.
- **Owner:** Bob L. (Pay Team)
- **Target date:** 2026-06-01

### MED-8 — Section 11 open issues are empty

- **Source:** interview-questionnaire.md Section 11 (partial)
- **Detail:** Pending changes, deprecations and the outlook were filled; the open-issues list was not.
- **Suggested action:** Return Section 11 to the outgoing team.
- **Owner:** Bob L. (Pay Team)
- **Target date:** 2026-06-08

### MED-9 — Is `payments-deploy-role` shared with other services?

- **Source:** runtime-profile.md Control-Plane Activity (open question)
- **Detail:** The role is the principal on every deploy event; its other uses are unknown.
- **Suggested action:** Ask the Pay Team; check the role trust policy with the incoming CI owners.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

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
