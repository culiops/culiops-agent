---
open-questions-schema: 2
service: payments
generated-at: 2026-05-12T16:05:00Z
high-priority-count: 1
medium-priority-count: 10
low-priority-count: 1
---

# Open Questions — payments

**Generated:** 2026-05-12T16:05:00Z

## Summary

| Priority | Count |
|---|---|
| High | 1 |
| Medium | 10 |
| Low | 1 |

One High conflict; the drift between the stale and the fresh catalog is Medium.

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

### MED-7 — Drift since the 2026-04-28 catalog: 3 resources are new (`payments-capture-dlq`, 2 secrets)

- **Source:** state.md Drift table; service-catalog.2026-04-28.md vs service-catalog.md
- **Detail:** The 5 older rows are unchanged. The DLQ and both secrets were not in the prior catalog (it says secrets were untagged then). They are either newly created or newly tagged.
- **Suggested action:** Ask the Pay Team whether the DLQ and secrets were created after 2026-04-28 or only tagged; if created, note who changed what (CloudTrail has the events for the DLQ).
- **Owner:** Carol P. (Pay Team)
- **Target date:** 2026-06-01

### MED-8 — alice's console read access to Secrets Manager should be revoked after handoff

- **Source:** interview-questionnaire.md Sections 9 and 11
- **Detail:** alice has console read access to the payments secrets for debugging.
- **Suggested action:** Revoke after the 2026-06-15 handoff.
- **Owner:** alice and Pay Team
- **Target date:** 2026-06-16

### MED-9 — Is `payments-deploy-role` shared with other services?

- **Source:** runtime-profile.md Control-Plane Activity (open question)
- **Detail:** The role is the principal on every deploy event; its other uses are unknown.
- **Suggested action:** Ask the Pay Team; check the role trust policy with the incoming CI owners.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

### MED-10 — How is `payments-reconciler` triggered?

- **Source:** runtime-profile.md Wiring and Gaps
- **Detail:** No resource policy or event source mapping was found; EventBridge/Scheduler rules are not enumerated. The activity baseline shows one invocation a day.
- **Suggested action:** Ask the Pay Team for the schedule owner; look for an EventBridge rule in the console.
- **Owner:** Carol P. (Pay Team)
- **Target date:** 2026-06-08

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
