---
open-questions-schema: 1
service: payments
generated-at: 2026-05-12T16:00:00Z
high-priority-count: 5
medium-priority-count: 3
low-priority-count: 0
---

# Open Questions — payments

**Generated:** 2026-05-12T16:00:00Z

## Summary

| Priority | Count |
|---|---|
| High | 5 |
| Medium | 3 |
| Low | 0 |

Five high-priority blockers must be resolved before takeover sign-off. These all stem from Section 10 (Compliance/DR) and Section 3 (SLOs) being left empty by the outgoing team. The operator chose to accept the interview as-is at Gate 5; these items now represent the critical knowledge gaps the incoming team must close.

---

## High Priority (blockers — must resolve before handoff)

### HIGH-1 — SLOs not defined

- **Source:** filled-interview.md → Section 3 — all fields empty
- **Detail:** No SLOs are documented for the payments service. Without defined SLOs, the incoming team has no quantitative targets for availability and latency, no error budget to track, and no objective measure of whether the service is meeting its obligations to upstream callers (checkout-service, billing-service). The service is Tier 0 / revenue-critical.
- **Suggested action:** Work with Pay Team (Bob L.) to define and document SLOs before handoff date. Minimum needed: availability SLO, latency SLO, dashboard URLs.
- **Owner:** alice (Platform Team) + Bob L. (Pay Team)
- **Target date:** 2026-06-01 (2 weeks before handoff)

### HIGH-2 — Backup strategy unknown

- **Source:** filled-interview.md → Section 10 → Backup strategy — empty
- **Detail:** Backup configuration for the payments-ledger DynamoDB table is unknown. It is unknown whether PITR is enabled, whether cross-region backups exist, what the restore window is, and when a restore was last tested. The payments-ledger holds financial transaction data with a likely 7-year retention obligation.
- **Suggested action:** Verify with infrastructure/Pay Team: confirm PITR status via AWS console (`dynamodb describe-continuous-backups`); confirm last restore test date; confirm whether cross-region backup is enabled.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08 (1 week before handoff)

### HIGH-3 — DR plan unknown — RTO/RPO unverified

- **Source:** filled-interview.md → Section 10 → Disaster recovery plan — empty
- **Detail:** RTO and RPO for the payments service are undocumented. Failover region is unknown. DR runbook location is unknown. The incoming team cannot sign off on operational readiness without knowing the disaster recovery posture for a Tier 0 service.
- **Suggested action:** Obtain DR runbook from Pay Team (Carol P. likely owns). Assess whether active-passive failover exists, what the RTO target is, and when the last DR drill occurred. Schedule a DR tabletop or partial failover drill for the incoming team before or within 30 days after handoff.
- **Owner:** alice (Platform Team) + Carol P. (outgoing SRE)
- **Target date:** 2026-06-08 (1 week before handoff)

### HIGH-4 — PII handling unknown

- **Source:** filled-interview.md → Section 10 → PII handling — empty
- **Detail:** It is unknown whether the payments service handles PII, what categories of personal data are stored, how they are protected (encryption, masking, access controls), and what the data subject rights obligations are (GDPR right-to-erasure, PCI DSS cardholder data scope). For a payments service, PCI DSS and GDPR applicability are highly likely.
- **Suggested action:** Confirm with Pay Team and/or legal/compliance before takeover sign-off: PII categories in scope, protection mechanisms (encryption at rest, field masking), data subject deletion procedure, PCI DSS SAQ type.
- **Owner:** alice (Platform Team) + Bob L. (Pay Team) + legal/compliance
- **Target date:** 2026-06-08 (1 week before handoff)

### HIGH-5 — Data retention policy unknown

- **Source:** filled-interview.md → Section 10 → Data retention policy — empty
- **Detail:** The retention policy for transaction records in payments-ledger is undocumented. For a financial service, regulatory retention periods (typically 7 years) are likely. It is unknown whether TTL is configured on the table, whether records are auto-purged or must be manually deleted, and whether legal hold obligations override standard TTL.
- **Suggested action:** Clarify with Pay Team (Bob) and legal: retention duration, regulatory basis, TTL configuration on payments-ledger, and any legal hold records.
- **Owner:** alice (Platform Team) + Bob L. (Pay Team)
- **Target date:** 2026-06-08 (1 week before handoff)

---

## Medium Priority (important — should resolve within 30 days of handoff)

### MED-1 — Incident history not documented

- **Source:** filled-interview.md → Section 6 → Incidents in last 12 months — empty
- **Detail:** The outgoing team did not provide incident history, recurring issues, MTTR, or change failure rate. This limits the incoming team's ability to understand operational patterns, prepare for recurring problems (e.g., known cold-start behavior, end-of-month Stripe rate limiting), and calibrate on-call response times.
- **Suggested action:** Ask Bob/Carol to fill in incident history asynchronously. Minimum needed: 2-3 major incidents from last 12 months with postmortem links, and any known recurring issues.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15 (handoff date)

### MED-2 — Training session not yet scheduled

- **Source:** General handoff planning
- **Detail:** No structured knowledge-transfer session has been scheduled. The empty sections (SLOs, Compliance/DR) mean the incoming team has less context than in a full handoff, making a live walkthrough even more critical.
- **Suggested action:** Schedule a 2-hour walkthrough session with Bob/Carol before 2026-06-15. Prioritize: compliance/DR gaps, SLO discussion, runbook walkthrough.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08 (1 week before handoff)

### MED-3 — Open issues at handoff not documented

- **Source:** filled-interview.md → Section 11 → Open issues at handoff — empty
- **Detail:** The outgoing team left the open-issues sub-section of Section 11 blank. Pending changes are documented (IaC migration, provisioned concurrency, SQS batch-size tuning), but any bugs, P0s, or action items carrying over from the Pay Team are unknown.
- **Suggested action:** Request the open-issues list from Bob before handoff date. Review against known tech debt in Section 7 to confirm alignment.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15 (handoff date)

---

## Low Priority

*None.*

---

## Resolved items

*None at this time. Items resolved during scorecard review are tracked in expected-handoff/readiness-scorecard.md Manual override log.*
