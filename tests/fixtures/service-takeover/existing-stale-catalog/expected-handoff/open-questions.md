---
open-questions-schema: 1
service: payments
generated-at: 2026-05-12T16:00:00Z
high-priority-count: 0
medium-priority-count: 2
low-priority-count: 0
---

# Open Questions — payments

**Generated:** 2026-05-12T16:00:00Z

## Summary

| Priority | Count |
|---|---|
| High | 0 |
| Medium | 2 |
| Low | 0 |

No high-priority blockers. Two medium-priority items should be resolved before or shortly after the handoff date of 2026-06-15.

---

## High Priority (blockers — must resolve before handoff)

*None.*

---

## Medium Priority (important — should resolve within 30 days of handoff)

### MED-1 — Training schedule not yet confirmed

- **Source:** General handoff planning
- **Detail:** The interview documents the deploy process, runbooks, landmines, and DR procedure thoroughly. However, no structured knowledge-transfer session between Pay Team and Platform Team has been scheduled. An informal walkthrough risks missing nuanced operational knowledge (e.g., cold-start behavior, Stripe webhook fragility, DLQ triage procedure).
- **Suggested action:** Schedule a 2-hour walkthrough session between Bob/Carol (outgoing) and the Platform Team before 2026-06-15. Cover: live deploy demo, runbook walkthrough, DR scenario tabletop.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08 (one week before handoff)

### MED-2 — DR test not yet scheduled for incoming team

- **Source:** filled-interview.md → Section 10 → DR drill last run 2025-11-01
- **Detail:** The last DR drill was 2025-11-01 (>6 months ago) and was conducted by the Pay Team. The Platform Team has not yet verified they can execute the DR runbook (https://docs.example.com/payments/dr-runbook). RTO of 30 min requires the on-call operator to be familiar with the failover steps.
- **Suggested action:** Schedule a DR tabletop or partial failover drill with the Platform Team before or within 30 days after handoff. Carol (outgoing) should walk through the DR runbook once with the Platform Team on-call representative.
- **Owner:** alice (Platform Team) + Carol P. (outgoing SRE)
- **Target date:** 2026-07-15 (within 30 days of handoff)

---

## Low Priority

*None.*

---

## Resolved items

*None at this time. Items resolved during scorecard review are tracked in expected-handoff/readiness-scorecard.md Manual override log.*
