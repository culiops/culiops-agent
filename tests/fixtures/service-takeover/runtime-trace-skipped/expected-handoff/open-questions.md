---
open-questions-schema: 1
service: payments
generated-at: 2026-05-12T15:45:00Z
high-priority-count: 1
medium-priority-count: 2
low-priority-count: 0
---

# Open Questions — payments

**Generated:** 2026-05-12T15:45:00Z

## Summary

| Priority | Count |
|---|---|
| High | 1 |
| Medium | 2 |
| Low | 0 |

One high-priority blocker: IAM gap prevents runtime baseline capture. Takeover verdict is not-ready until this is resolved. Two medium-priority items should be resolved before or shortly after the handoff date of 2026-06-15.

---

## High Priority (blockers — must resolve before handoff)

### HIGH-1 — Activity baseline unavailable — recommend escalating IAM for ce:* read and re-running

- **Source:** expected-handoff/state.md → Step 1.5: capability-probe-result: Cost Explorer DENIED
- **Detail:** Cost Explorer access (`ce:*`) is blocked by corporate IAM policy in account 123456789012. Step 4 (runtime-trace) was skipped at operator request. As a result, no `runtime-profile.md` was produced and scorecard items 7-9 (Runtime category) plus items 2 (deploy role) and 5 (cross-region footprint) are all unresolved (?). The takeover readiness verdict is not-ready.
- **Suggested action:** Request `ce:GetCostAndUsage` and `ce:GetCostForecast` read access on account 123456789012 from your IAM admin (reference: corporate policy exception process). Once granted, re-run `service-takeover` from Step 4. Alternatively, if deploy role and cross-region footprint can be confirmed manually (direct IAM lookup / AWS console), operator can manually mark items 2 and 5; items 7-9 still require runtime-trace.
- **Owner:** alice (Platform Team)
- **Target date:** Before 2026-06-15 handoff date

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
