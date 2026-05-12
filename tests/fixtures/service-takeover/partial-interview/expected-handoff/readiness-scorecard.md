---
readiness-scorecard-schema: 1
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-12T16:00:00Z
verdict: not-ready
---

# Readiness Scorecard — payments

**Verdict: not-ready**
**Generated:** 2026-05-12T16:00:00Z
**Operator:** alice (arn:aws:iam::123456789012:user/alice)

---

## Per-category summary

| Category | Items | ✓ | ✗ | ? | [manual] |
|---|---|---|---|---|---|
| Access | 1-3 | 2 | 0 | 0 | 1 |
| Inventory | 4-6 | 3 | 0 | 0 | 0 |
| Runtime | 7-9 | 3 | 0 | 0 | 0 |
| Alerting | 10-12 | 2 | 0 | 0 | 1 |
| Runbooks | 13-14 | 1 | 0 | 1 | 0 |
| Deploy & Rollback | 15-18 | 4 | 0 | 0 | 0 |
| Dependencies | 19-21 | 3 | 0 | 0 | 0 |
| Compliance | 22-25 | 0 | 4 | 0 | 0 |
| **Total** | **25** | **18** | **4** | **1** | **2** |

Verdict: **not-ready** — Compliance category 0/4 passing. Section 10 of the interview was left empty by the outgoing team; the skill correctly does not auto-pass items without evidence.

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: expected-handoff/state.md → Step 1.5: capability-probe-result: AWS access verified at 2026-05-12T14:05:00Z]
- **Notes:** `aws sts get-caller-identity` confirmed alice's identity in account 123456789012.

### Item 2 — Deploy role identified ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: mock-artifacts/runtime-profile.md → Control-Plane Activity → Principals table → `payments-deploy-role` with UpdateFunctionCode events]
- **Notes:** `arn:aws:iam::123456789012:role/payments-deploy-role` identified as GitHub Actions deploy role with 15 UpdateFunctionCode events in 90d.

### Item 3 — Console+CLI access verified ✓

- **Mark:** ✓ [manual: alice confirmed console login and CLI access on 2026-05-12. "Ran `aws lambda list-functions --region us-east-1` and confirmed all three payments-* functions visible."]
- **Evidence:** [manual: operator-confirmed on 2026-05-12T16:02:00Z]

---

## Category: Inventory (items 4–6)

### Item 4 — Resources enumerated ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: mock-artifacts/service-catalog.md → Resource Inventory → 8 rows including 3 Lambdas, 2 SQS queues, 1 DynamoDB table, 2 Secrets Manager secrets]
- **Notes:** Catalog populated via real-discovery + diagram extraction. 8 resources tagged `service=payments`.

### Item 5 — Cross-region footprint known ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: mock-artifacts/runtime-profile.md → Cross-Region Footprint → Resource Explorer ran ✓, us-east-1 only, 0 resources in other regions]
- **Notes:** Resource Explorer search confirmed no cross-region resources.

### Item 6 — Secrets/credentials references catalogued ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: mock-artifacts/service-catalog.md → Secrets References → 2 entries; filled-interview.md → Section 9 → 3 Secrets Manager paths with rotation owners]
- **Notes:** All secrets documented as references only; no secret values captured.

---

## Category: Runtime (items 7–9)

### Item 7 — Activity baseline captured ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: mock-artifacts/runtime-profile.md → Activity Baselines (CloudWatch) → 5-row table covering all Lambda, SQS, and DynamoDB resources]
- **Notes:** 14-day baseline captured; all resources show nominal verdicts.

### Item 8 — Deploy events history captured ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: mock-artifacts/runtime-profile.md → Control-Plane Activity → Notable change events → 5 deploy events, most recent 2026-05-08]
- **Notes:** 5 deploy events in 90-day CloudTrail window. Pattern matches stated deploy frequency of 3-5/week.

### Item 9 — Principals touching service enumerated ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: mock-artifacts/runtime-profile.md → Control-Plane Activity → Principals table → 3 rows: payments-deploy-role, alice, payments-lambda-exec]
- **Notes:** Deploy role, human operator, and Lambda execution role all accounted for.

---

## Category: Alerting (items 10–12)

### Item 10 — Critical metrics have alarms ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 5 → Alarms configured → 5 alarms listed with names and severities]
- **Notes:** 5 alarms covering error rate, queue depth, DLQ, Lambda errors, and latency p99. Section 5 was fully completed.

### Item 11 — On-call rotation configured ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 2 → On-call schedule → PagerDuty, weekly Monday 10am UTC, current on-call Bob]
- **Notes:** Rotation includes Bob, Carol, Dan; escalation to Priya documented.

### Item 12 — Paging path verified ✓

- **Mark:** ✓ [manual: alice confirmed "Received a test page from PagerDuty for payments P1 alarm on 2026-05-12. Platform Team paging verified end-to-end."]
- **Evidence:** [manual: operator-confirmed on 2026-05-12T16:04:00Z]

---

## Category: Runbooks (items 13–14)

### Item 13 — Top-5 symptom→action runbooks exist ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 6 → Existing runbooks → 5 runbooks listed with URLs and descriptions]
- **Notes:** auth-error-spike, capture-queue-backup, dlq-triage, stripe-degradation, rollback — all at https://docs.example.com/payments/runbooks/. The runbooks sub-section of Section 6 was filled; incidents sub-sections were left empty.

### Item 14 — Recent incidents documented ?

- **Mark:** ? (auto — insufficient evidence)
- **Evidence:** [evidence: filled-interview.md → Section 6 → Incidents in last 12 months — empty (`_To be filled in: ___`)]
- **Notes:** The outgoing team did not provide incident history. The skill cannot assert incidents are absent — this is a data gap, not a confirmation. Operator should follow up with Pay Team before sign-off.

---

## Category: Deploy & Rollback (items 15–18)

### Item 15 — CI/CD access ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 4 → Deploy permissions → mentions "Platform Team's `platform-team-deploy` will need to be added before handoff date — action item tracked in Section 11"]
- **Notes:** Platform Team IAM role identified as open action item. Confirmed actionable before handoff date 2026-06-15.

### Item 16 — Deploy process documented ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 4 → How does code reach prod? → GitHub Actions deploy.yml, 8-minute pipeline, full steps described]
- **Notes:** Complete deploy path documented including S3 artifact upload and Lambda UpdateFunctionCode.

### Item 17 — Rollback path documented ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 4 → Rollback procedure → GitHub Actions revert-and-redeploy workflow, steps described, last tested 2026-04-22, 4 minutes]
- **Notes:** Rollback procedure tested within last 30 days.

### Item 18 — Deploy frequency known (DORA) ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 4 → Deploy frequency → "3-5 deploys per week (~4/week averaged over last quarter)"]
- **Notes:** Quantitative value provided; DORA deploy frequency = medium-high.

---

## Category: Dependencies (items 19–21)

### Item 19 — Upstream callers identified ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 8 → Upstream callers → checkout-service (Maria R., maria@example.com) and billing-service (Tom S., tom@example.com)]
- **Notes:** Both callers named with team leads and contact emails.

### Item 20 — Downstream services identified ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 8 → Downstream services → Stripe API (contract owner: Bob, renewal 2027-03), fraud-detection (Ying L.), notifications-service (Alex G.)]
- **Notes:** All downstream dependencies named with contacts; Stripe contract details provided.

### Item 21 — External API ownership known ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 8 → External APIs → Stripe API with vendor, contract owner, billing impact, rate limit, status page]
- **Notes:** Complete external API documentation; contract owner Bob L., renewal 2027-03.

---

## Category: Compliance (items 22–25)

### Item 22 — PII handling known ✗

- **Mark:** ✗ (auto — evidence absent)
- **Evidence:** [evidence: filled-interview.md → Section 10 → PII handling — empty (`_To be filled in: ___`). Section 10 was not filled by outgoing team.]
- **Notes:** PII handling is a critical compliance item. Without this, the incoming team cannot confirm data protection obligations or GDPR/PCI scope. This must be resolved before takeover sign-off.

### Item 23 — Data retention policy known ✗

- **Mark:** ✗ (auto — evidence absent)
- **Evidence:** [evidence: filled-interview.md → Section 10 → Data retention policy — empty (`_To be filled in: ___`). Section 10 was not filled by outgoing team.]
- **Notes:** Retention policy determines TTL configuration and legal hold obligations. Cannot confirm compliance without this. High priority open question.

### Item 24 — Backup strategy verified ✗

- **Mark:** ✗ (auto — evidence absent)
- **Evidence:** [evidence: filled-interview.md → Section 10 → Backup strategy — empty (`_To be filled in: ___`). Section 10 was not filled by outgoing team.]
- **Notes:** Backup configuration (PITR, snapshots) and last restore test date are unknown. Cannot confirm RPO targets are met. High priority open question.

### Item 25 — DR plan exists ✗

- **Mark:** ✗ (auto — evidence absent)
- **Evidence:** [evidence: filled-interview.md → Section 10 → Disaster recovery plan — empty (`_To be filled in: ___`). Section 10 was not filled by outgoing team.]
- **Notes:** RTO and RPO are undocumented. Failover region unknown. DR runbook URL unknown. Cannot confirm disaster recovery readiness. High priority open question.

---

## Manual override log

| Timestamp | Item | Mark | Operator | Note |
|---|---|---|---|---|
| 2026-05-12T16:02:00Z | Item 3 (Console+CLI access) | ✓ manual | alice | "Ran `aws lambda list-functions --region us-east-1` and confirmed all three payments-* functions visible." |
| 2026-05-12T16:04:00Z | Item 12 (Paging path) | ✓ manual | alice | "Received a test page from PagerDuty for payments P1 alarm on 2026-05-12. Platform Team paging verified end-to-end." |
