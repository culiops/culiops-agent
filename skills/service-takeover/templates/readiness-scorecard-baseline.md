---
template-version: 1
emitted-by: service-takeover
purpose: Baseline checklist for Step 6 readiness scorecard. Defines 25 items
  across 8 categories with per-item auto-mark rules. See examples/auto-mark-rules.md
  for the rule lookup format.
---

# Readiness Scorecard — Baseline Checklist

This file defines the 25-item Production Readiness Review (PRR) checklist used in Step 6 of `service-takeover`. Each item has:

- An **ID** (1–25), stable across runs and schema versions.
- An **item** (the question being asked).
- An **auto-mark rule** (how the skill assigns ✓ / ✗ / ?).
- An **evidence pointer** (which prior artifact, which section, optionally which line pattern).
- An **operator-prompt** template (what the skill asks the operator if the item must be marked manually).

Categories follow the SRE book Ch. 32 PRR structure plus DevOps Handbook / AWS Well-Architected adaptations.

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account

- **Auto-mark rule:** ✓ if `state.md` records "Step 1.5 capability probe: AWS access verified". ? otherwise.
- **Evidence:** `state.md` → "Step 1.5: capability-probe-result".
- **Operator prompt (if manual):** "Have you successfully run `aws sts get-caller-identity` against the target account today?"

### Item 2 — Deploy role identified

- **Auto-mark rule:** ✓ if the runtime profile's Control-Plane Activity section lists at least one principal whose name contains `deploy` (case-insensitive) or whose recorded EventName history includes deploy-style actions (`UpdateFunction*`, `UpdateService`, `CreateDeployment`). ? otherwise.
- **Evidence:** `runtime-profile.md` → "Control-Plane Activity (CloudTrail)" section → "Principals touching this service" table.
- **Operator prompt (if manual):** "Looking at runtime-profile.md's principals table, which is the deploy role? Paste the ARN."

### Item 3 — Console+CLI access verified

- **Auto-mark rule:** Always `[manual]` — no artifact can prove the operator has personally logged in and run a CLI command. Operator confirms with one-line note.
- **Operator prompt:** "Have you personally logged in to the AWS console for this account AND run `aws <service> describe-*` successfully today? (yes/no/explain)"

---

## Category: Inventory (items 4–6)

### Item 4 — Resources enumerated

- **Auto-mark rule:** ✓ if `service-catalog.md` exists in the handoff directory AND has at least one resource row in its inventory table. ✗ if catalog exists but is empty. ? if no catalog.
- **Evidence:** `service-catalog.md` → resource inventory section.

### Item 5 — Cross-region footprint known

- **Auto-mark rule:** ✓ if `runtime-profile.md` has a "Cross-Region Footprint (Resource Explorer)" section that ran (not skipped). ✗ if RE was skipped and operator did not supply a cross-region manual inventory. ? if no runtime profile.
- **Evidence:** `runtime-profile.md` → "Cross-Region Footprint" section status.

### Item 6 — Secrets/credentials references catalogued

- **Auto-mark rule:** ✓ if `service-catalog.md` has a secrets-references section (per `service-discovery`'s schema — secrets are recorded as refs, never values) with ≥1 entry, OR if interview Section 9 has non-empty answers under "Secret stores in use". ✗ if both are empty/absent. ? otherwise.
- **Evidence:** `service-catalog.md` → secrets-references; `interview-questionnaire.md` → Section 9.

---

## Category: Runtime (items 7–9)

### Item 7 — Activity baseline captured

- **Auto-mark rule:** ✓ if `runtime-profile.md` has the "Activity Baselines (CloudWatch)" section with at least one resource row. ✗ if section is empty (e.g., CloudWatch was skipped). ? if no runtime profile.
- **Evidence:** `runtime-profile.md` → "Activity Baselines" section.

### Item 8 — Deploy events history captured

- **Auto-mark rule:** ✓ if `runtime-profile.md`'s "Control-Plane Activity" section has at least one event in the "Notable change events" timeline. ✗ if section is empty or CloudTrail was unavailable. ? if no runtime profile.
- **Evidence:** `runtime-profile.md` → "Control-Plane Activity" → "Notable change events".

### Item 9 — Principals touching service enumerated

- **Auto-mark rule:** ✓ if `runtime-profile.md`'s "principals touching this service" table has ≥1 row. ✗ if CloudTrail was unavailable. ? if no runtime profile.
- **Evidence:** `runtime-profile.md` → principals table.

---

## Category: Alerting (items 10–12)

### Item 10 — Critical metrics have alarms

- **Auto-mark rule:** ✓ if interview Section 5 ("Alerting & on-call") has a non-empty "Alarms configured" answer mentioning at least one alarm by name. ✗ if section explicitly says "no alarms". ? if section is empty.
- **Evidence:** `interview-questionnaire.md` → Section 5 → "Alarms configured".

### Item 11 — On-call rotation configured

- **Auto-mark rule:** ✓ if interview Section 2 ("People & ownership") has non-empty "On-call schedule" answer naming a rotation tool AND a current on-call. ? otherwise.
- **Evidence:** `interview-questionnaire.md` → Section 2 → "On-call schedule".

### Item 12 — Paging path verified

- **Auto-mark rule:** Always `[manual]` — no artifact can prove the operator has personally received a test page on their phone. Operator confirms with one-line note.
- **Operator prompt:** "Have you personally received a test page from the on-call paging tool for this service in the last 7 days? (yes/no/scheduled-for-date)"

---

## Category: Runbooks (items 13–14)

### Item 13 — Top-5 symptom→action runbooks exist

- **Auto-mark rule:** ✓ if interview Section 6 ("Runbooks & incidents") lists ≥3 runbooks under "Existing runbooks". ✗ if section explicitly says "no runbooks". ? if section is empty.
- **Evidence:** `interview-questionnaire.md` → Section 6 → "Existing runbooks".

### Item 14 — Recent incidents documented

- **Auto-mark rule:** ✓ if interview Section 6 has ≥1 entry under "Incidents in last 12 months" with a postmortem link. ? if entries exist but no postmortem links. ✗ if section is empty AND interview also lacks Section 7 landmines.
- **Evidence:** `interview-questionnaire.md` → Section 6 → "Incidents in last 12 months".

---

## Category: Deploy & Rollback (items 15–18)

### Item 15 — CI/CD access

- **Auto-mark rule:** ✓ if interview Section 4 has non-empty "Deploy permissions" answer naming the operator's incoming-team identity (matched by string presence in the answer). ? otherwise.
- **Evidence:** `interview-questionnaire.md` → Section 4 → "Deploy permissions".
- **Operator prompt:** "Does the incoming team's IAM role appear in the deploy-permissions list? If you don't see it, this item is ✗ until added."

### Item 16 — Deploy process documented

- **Auto-mark rule:** ✓ if interview Section 4 has non-empty "How does code reach prod?" answer with ≥1 sentence. ? if empty.
- **Evidence:** `interview-questionnaire.md` → Section 4.

### Item 17 — Rollback path documented

- **Auto-mark rule:** ✓ if interview Section 4 has non-empty "Rollback procedure" answer mentioning explicit steps. ✗ if explicitly "no rollback procedure". ? if empty.
- **Evidence:** `interview-questionnaire.md` → Section 4 → "Rollback procedure".

### Item 18 — Deploy frequency known (DORA)

- **Auto-mark rule:** ✓ if interview Section 4 has non-empty "Deploy frequency" answer with a quantitative value (e.g., "twice a week", "5/day"). ? if qualitative only or empty.
- **Evidence:** `interview-questionnaire.md` → Section 4 → "Deploy frequency".

---

## Category: Dependencies (items 19–21)

### Item 19 — Upstream callers identified

- **Auto-mark rule:** ✓ if interview Section 8 has non-empty "Upstream callers" answer with ≥1 named service AND contact info. ? if listed without contacts. ✗ if explicitly "none / unknown".
- **Evidence:** `interview-questionnaire.md` → Section 8 → "Upstream callers".

### Item 20 — Downstream services identified

- **Auto-mark rule:** ✓ if interview Section 8 has non-empty "Downstream services" answer with ≥1 named service AND contract/SLA reference. ? if listed without contracts.
- **Evidence:** `interview-questionnaire.md` → Section 8 → "Downstream services".

### Item 21 — External API ownership known

- **Auto-mark rule:** ✓ if interview Section 8 has non-empty "External APIs" answer with vendor + contract-owner for each entry. ? if listed without owners. N/A if interview explicitly says "no external APIs".
- **Evidence:** `interview-questionnaire.md` → Section 8 → "External APIs".

---

## Category: Compliance (items 22–25)

### Item 22 — PII handling known

- **Auto-mark rule:** ✓ if interview Section 10 has non-empty "PII handling" answer. ? if empty. N/A if interview explicitly says "no PII handled".
- **Evidence:** `interview-questionnaire.md` → Section 10 → "PII handling".

### Item 23 — Data retention policy known

- **Auto-mark rule:** ✓ if interview Section 10 has non-empty "Data retention policy" answer with a specific timeframe. ? if empty or qualitative ("a while").
- **Evidence:** `interview-questionnaire.md` → Section 10 → "Data retention policy".

### Item 24 — Backup strategy verified

- **Auto-mark rule:** ✓ if interview Section 10 has non-empty "Backup strategy" AND "Last backup-restore test" answers, with test date within last 12 months. ? if backup strategy exists but restore not tested recently. ✗ if no backup strategy.
- **Evidence:** `interview-questionnaire.md` → Section 10 → "Backup strategy" + "Last backup-restore test".

### Item 25 — DR plan exists

- **Auto-mark rule:** ✓ if interview Section 10 has non-empty "Disaster recovery plan" answer with RTO + RPO values + DR runbook path. ? if partial. ✗ if "no DR plan".
- **Evidence:** `interview-questionnaire.md` → Section 10 → "Disaster recovery plan".

---

## Notes for the skill at runtime

1. **Evidence citations are mandatory.** Every auto-marked item in the generated `readiness-scorecard.md` must include `[evidence: <relative-path>:<section-heading>]`. Manual items carry `[manual: <one-line operator note>]`.
2. **Unknown is the default.** If the rule's evidence is missing or ambiguous, the item is `?`, not auto-✓. The operator decides whether to override.
3. **Operator override log.** Every manual mark or auto-mark override is appended to the "Manual override log" section of the generated scorecard with timestamp.
4. **Optional extras.** If `extra-checklist.md` exists alongside this template (in the run's handoff directory, not in the skill repo), the skill parses it as additional items and merges them into the scorecard's "Operator-supplied extras" section.
