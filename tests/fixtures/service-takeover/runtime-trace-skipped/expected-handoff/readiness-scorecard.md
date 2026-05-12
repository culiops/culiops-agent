---
readiness-scorecard-schema: 1
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-12T15:45:00Z
verdict: not-ready
---

# Readiness Scorecard — payments

**Verdict: not-ready**
**Generated:** 2026-05-12T15:45:00Z
**Operator:** alice (arn:aws:iam::123456789012:user/alice)

---

## Per-category summary

| Category | Items | ✓ | ✗ | ? | [manual] |
|---|---|---|---|---|---|
| Access | 1-3 | 1 | 0 | 1 | 1 |
| Inventory | 4-6 | 2 | 0 | 1 | 0 |
| Runtime | 7-9 | 0 | 0 | 3 | 0 |
| Alerting | 10-12 | 2 | 0 | 0 | 1 |
| Runbooks | 13-14 | 2 | 0 | 0 | 0 |
| Deploy & Rollback | 15-18 | 4 | 0 | 0 | 0 |
| Dependencies | 19-21 | 3 | 0 | 0 | 0 |
| Compliance | 22-25 | 4 | 0 | 0 | 0 |
| **Total** | **25** | **18** | **0** | **7** | **2** |

7 items unresolved (?). Runtime category entirely unresolved — no runtime-profile.md available (Step 4 skipped per operator at Gate 1.5). Items 2 and 5 degraded to ? for the same reason. Verdict: not-ready.

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: expected-handoff/state.md → Step 1.5: capability-probe-result: AWS access verified at 2026-05-12T14:05:00Z]
- **Notes:** `aws sts get-caller-identity` confirmed alice's identity in account 123456789012.

### Item 2 — Deploy role identified ?

- **Mark:** ? (auto-degraded)
- **Evidence:** no runtime-profile.md (Step 4 skipped per operator at Gate 1.5)
- **Notes:** Deploy role identification required runtime-profile.md Control-Plane Activity → Principals table. Step 4 was skipped due to IAM gap (ce:* denied). Operator can resolve manually if deploy role is known via other means (e.g., interview or direct IAM lookup) — operator left as ? in this fixture.

### Item 3 — Console+CLI access verified ✓

- **Mark:** ✓ [manual: alice confirmed console login and CLI access on 2026-05-12. "Ran `aws lambda list-functions --region us-east-1` and confirmed all three payments-* functions visible."]
- **Evidence:** [manual: operator-confirmed on 2026-05-12T15:20:00Z]

---

## Category: Inventory (items 4–6)

### Item 4 — Resources enumerated ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: mock-artifacts/service-catalog.md → Resource Inventory → 8 rows including 3 Lambdas, 2 SQS queues, 1 DynamoDB table, 2 Secrets Manager secrets]
- **Notes:** Catalog populated via real-discovery + diagram extraction. 8 resources tagged `service=payments`.

### Item 5 — Cross-region footprint known ?

- **Mark:** ? (auto-degraded)
- **Evidence:** no runtime-profile.md (Step 4 skipped per operator at Gate 1.5)
- **Notes:** Cross-region footprint confirmation required runtime-profile.md Cross-Region Footprint section (Resource Explorer query). Step 4 was skipped due to IAM gap. Operator can resolve manually by running `aws resource-explorer-2 search` directly, or by confirming via interview that service is single-region.

### Item 6 — Secrets/credentials references catalogued ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: mock-artifacts/service-catalog.md → Secrets References → 2 entries; filled-interview.md → Section 9 → 3 Secrets Manager paths with rotation owners]
- **Notes:** All secrets documented as references only; no secret values captured.

---

## Category: Runtime (items 7–9)

### Item 7 — Activity baseline captured ?

- **Mark:** ? (auto-degraded)
- **Evidence:** no runtime-profile.md (Step 4 skipped per operator at Gate 1.5)
- **Notes:** Activity baseline requires runtime-profile.md → Activity Baselines (CloudWatch). Step 4 was skipped due to IAM gap (ce:* denied in account 123456789012 by corporate policy). To resolve: escalate IAM for `ce:GetCostAndUsage` and `ce:GetCostForecast`, then re-run service-takeover from Step 4.

### Item 8 — Deploy events history captured ?

- **Mark:** ? (auto-degraded)
- **Evidence:** no runtime-profile.md (Step 4 skipped per operator at Gate 1.5)
- **Notes:** Deploy event history requires runtime-profile.md → Control-Plane Activity → Notable change events. Step 4 was skipped due to IAM gap. Operator has partial visibility via filled-interview.md Section 4 (deploy frequency stated as 3-5/week) but no CloudTrail-backed evidence. To resolve: re-run Step 4 after IAM is granted.

### Item 9 — Principals touching service enumerated ?

- **Mark:** ? (auto-degraded)
- **Evidence:** no runtime-profile.md (Step 4 skipped per operator at Gate 1.5)
- **Notes:** Principal enumeration requires runtime-profile.md → Control-Plane Activity → Principals table. Step 4 was skipped due to IAM gap. Operator can resolve manually via CloudTrail direct query if CloudTrail access is available without Cost Explorer. Left as ? in this fixture.

---

## Category: Alerting (items 10–12)

### Item 10 — Critical metrics have alarms ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 5 → Alarms configured → 5 alarms listed with names and severities]
- **Notes:** 5 alarms covering error rate, queue depth, DLQ, Lambda errors, and latency p99.

### Item 11 — On-call rotation configured ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 2 → On-call schedule → PagerDuty, weekly Monday 10am UTC, current on-call Bob]
- **Notes:** Rotation includes Bob, Carol, Dan; escalation to Priya documented.

### Item 12 — Paging path verified ✓

- **Mark:** ✓ [manual: alice confirmed "Received a test page from PagerDuty for payments P1 alarm on 2026-05-12. Platform Team paging verified end-to-end."]
- **Evidence:** [manual: operator-confirmed on 2026-05-12T15:30:00Z]

---

## Category: Runbooks (items 13–14)

### Item 13 — Top-5 symptom→action runbooks exist ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 6 → Existing runbooks → 5 runbooks listed with URLs and descriptions]
- **Notes:** auth-error-spike, capture-queue-backup, dlq-triage, stripe-degradation, rollback — all at https://docs.example.com/payments/runbooks/.

### Item 14 — Recent incidents documented ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 6 → Incidents in last 12 months → 2 incidents with postmortem links]
- **Notes:** INC-2026-03-12 (sev-2) and INC-2025-11-28 (sev-3) both have postmortem links.

---

## Category: Deploy & Rollback (items 15–18)

### Item 15 — CI/CD access ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 4 → Deploy permissions → mentions "Platform Team's `platform-team-deploy` will need to be added before handoff date — action item tracked in Section 11"]
- **Notes:** Platform Team IAM role identified as open action item; tracked in Section 11. Confirmed actionable before handoff date 2026-06-15.

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

### Item 22 — PII handling known ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 10 → PII handling → customer_id, masked card last-4, amounts, timestamps; KMS encryption; 7-year retention; Stripe tokenizes card numbers]
- **Notes:** PII scope clearly bounded; protection mechanism (KMS CMK) and retention policy documented.

### Item 23 — Data retention policy known ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 10 → Data retention policy → "7 years per financial regulation; TTL expires_at auto-purge after 7 years + 90 day grace"]
- **Notes:** Specific timeframe with regulatory basis provided.

### Item 24 — Backup strategy verified ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 10 → Backup strategy: DynamoDB PITR enabled, 35-day restore window; Last backup-restore test: 2026-02-15 (within 12 months), 18 minutes for ~3M records]
- **Notes:** Both backup strategy and recent restore test present. Restore tested 2026-02-15 (~87 days ago, well within 12-month window).

### Item 25 — DR plan exists ✓

- **Mark:** ✓ (auto)
- **Evidence:** [evidence: filled-interview.md → Section 10 → Disaster recovery plan: active-passive us-west-2 failover, RTO 30 min, RPO 5 min, DR runbook at https://docs.example.com/payments/dr-runbook, last drill 2025-11-01]
- **Notes:** RTO and RPO both specified; runbook URL provided; last drill date within 12 months.

---

## Manual override log

| Timestamp | Item | Mark | Operator | Note |
|---|---|---|---|---|
| 2026-05-12T15:20:00Z | Item 3 (Console+CLI access) | ✓ manual | alice | "Ran `aws lambda list-functions --region us-east-1` and confirmed all three payments-* functions visible." |
| 2026-05-12T15:30:00Z | Item 12 (Paging path) | ✓ manual | alice | "Received a test page from PagerDuty for payments P1 alarm on 2026-05-12. Platform Team paging verified end-to-end." |
