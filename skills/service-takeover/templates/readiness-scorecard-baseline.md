---
template-version: 2
emitted-by: service-takeover
purpose: Baseline checklist for Step 6 readiness scorecard. Defines 25 items
  across 8 categories, the evidence classes, the strict verdict rule, and the
  per-item auto-mark rules and verification checks. See examples/auto-mark-rules.md
  for the lookup summary.
---

# Readiness Scorecard — Baseline Checklist

This file defines the 25-item Production Readiness Review (PRR) checklist used in Step 6 of `service-takeover`. Each item has:

- An **ID** (1–25), stable across runs and schema versions.
- An **item** (the question being asked).
- An **auto-mark rule** (how the skill assigns a mark from the artifacts).
- An **evidence pointer** (which prior artifact, which section).
- A **verification check** (the read-only query that turns `◐ operator-stated` into `✓ verified` or `✗ conflict`), where one exists.
- An **operator prompt** for items that need a human answer.

Categories follow the SRE book Ch. 32 PRR structure plus DevOps Handbook / AWS Well-Architected adaptations.

---

## Evidence classes (one mark per item)

| Mark | Meaning | Allowed when |
|---|---|---|
| `✓ verified` | Backed by a cited artifact line or a cited live read-only query | Catalog row with `Live ✓` or real-discovery result; runtime-profile section; Step 1.5 / Step 6 projected query result |
| `✓ attested` | Operator attestation with a one-line note | **Only** items 3, 11 and 12 — facts no artifact or query can prove (personal console login, a rotation in a third-party pager, a test page received) |
| `◐ operator-stated` | An interview or operator answer on a **checkable** fact, not yet verified | The interview answers the question but no artifact or query confirms it |
| `✗` | Evidence shows the item fails | Cited artifact, query, or an explicit interview "no X" |
| `✗ conflict` | Interview and artifact disagree | Both sources cited; always a High open question |
| `?` | Unknown | Evidence missing, empty, ambiguous, or upstream says "not verifiable" |
| `N/A` | Does not apply | Explicit interview statement (e.g. "no external APIs"), cited |

**Presence is not proof.** A non-empty interview answer yields at most `◐`. Empty means `?`, never `✗`.

**Document-backed items** (13, 14, 17, 21, 22, 25): an answer that points to a document becomes `✓ verified` when the operator opens the cited document and it actually answers the item. The citation is the document path or URL (never one carrying a token). Every item therefore has a path to `✓ verified`, `✓ attested` or `N/A` — `ready` is reachable, but only with evidence.

**Conflict check.** Before finalising, compare every interview answer that has an artifact counterpart (deploy frequency vs CloudTrail deploy events; upstream callers vs Wiring; downstream services vs the catalog dependency graph; regions in DR answers vs the Cross-Region Footprint; secrets listed vs catalog secret references; backup claims vs catalog backup config). Disagreement → `✗ conflict`.

## Verdict (strict)

- **`ready`** — every item is `✓ verified`, `✓ attested` or `N/A`.
- **`not-ready`** — any `✗` or `✗ conflict` in Access, Runtime, Deploy & Rollback, or Compliance.
- **`partial`** — everything else, i.e. any `◐` or `?`, or an `✗` / `✗ conflict` only in Inventory, Alerting, Runbooks or Dependencies.

The verdict line always states the counts and, for `partial`, the number of verification checks that could move it toward `ready`. Arithmetic pass rates are reported per category but never decide the verdict.

## Step 6 verification batch (optional, offered by default)

For each `◐` item that has a verification check, the skill proposes the check as a read-only, projected command (with `--profile` / `--region` pinned to the intake account, confirmed by `aws sts get-caller-identity`). The operator approves the batch, runs it (or lets the skill run it, per the Step 1.5 rule for targeted commands), and the skill records only the derived fact with the command and timestamp as evidence. Skipping the batch leaves those items `◐` and the verdict `partial`.

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account

- **Auto-mark rule:** `✓ verified` if `state.md` records the Step 1.5 identity probe (`aws sts get-caller-identity --query Account`) **and** the account equals the intake account. Mismatch → `✗`. No probe → `?`.
- **Evidence:** `state.md` → "Step 1.5: identity-probe-result".

### Item 2 — Deploy role identified

- **Auto-mark rule:** The runtime profile's principals table (management events) is a **hint**: a principal whose name contains `deploy`, or whose events include deploy-style actions (`UpdateFunctionCode`, `UpdateService`, `RegisterTaskDefinition`, `CreateDeployment`). The operator confirms the role → `✓ verified` (profile row + confirmation). Interview names a role not in the profile → `◐`. Interview and profile name different roles with no overlap → `✗ conflict`. Neither → `?`.
- **Evidence:** `runtime-profile.md` → "Control-Plane Activity (CloudTrail)" → "Principals touching this service"; `interview-questionnaire.md` → Section 4.
- **Operator prompt:** "Which of these principals is the deploy role? Paste the ARN."

### Item 3 — Console+CLI access verified

- **Auto-mark rule:** Always `✓ attested` / `✗` from the operator — no artifact can prove a personal login.
- **Operator prompt:** "Have you personally logged in to the AWS console for this account AND run a read-only CLI command successfully today? (yes/no/explain)"

---

## Category: Inventory (items 4–6)

### Item 4 — Resources enumerated

- **Auto-mark rule:** Count only **attributed** inventory rows (not the "Unattributed — operator assigns" list). `✓ verified` if ≥1 row and the catalog is live-backed: `**Live verification:** performed` (IaC path, Step 2V) or `Discovery source: real-discovery`. Rows marked `not found` are listed as open questions. Code-only catalog (`Live verification: not performed`) → `◐`. Catalog exists with no attributed rows → `✗`. No catalog → `?`.
- **Evidence:** `service-catalog.md` → stamp + Resource Inventory.

### Item 5 — Cross-region footprint known

- **Auto-mark rule:** `✓ verified` only if `runtime-profile.md` → "Cross-Region Footprint" states the verification passed (aggregator-Region view, indexed Regions, complete results). "cross-Region: not verifiable — …" or Resource Explorer skipped → `?` (unless the operator supplies a cross-region inventory, which is `◐`). No runtime profile → `?`.
- **Evidence:** `runtime-profile.md` → "Cross-Region Footprint (Resource Explorer)" verification line.

### Item 6 — Secrets/credentials references catalogued

- **Auto-mark rule:** `✓ verified` if the catalog records ≥1 secret **reference** (name/ARN/key names) and the catalog is live-backed (as item 4). Code-only catalog with references → `◐`. Only the interview (Section 9) lists secret stores → `◐`. Interview lists secrets the catalog doesn't (or vice versa) → `✗ conflict` for the difference. Both empty → `?`.
- **Evidence:** `service-catalog.md` → secret references; `interview-questionnaire.md` → Section 9.

---

## Category: Runtime (items 7–9)

### Item 7 — Activity baseline captured

- **Auto-mark rule:** `✓ verified` if "Activity Baselines (CloudWatch)" has ≥1 resource row with data (verdicts `no-data` / `metric-not-found` don't count as captured). CloudWatch skipped, or only no-data rows → `?`. EKS in-cluster workloads recorded as a gap → note it; the item can still pass for the AWS resources. No runtime profile → `?`.
- **Evidence:** `runtime-profile.md` → "Activity Baselines (CloudWatch)".

### Item 8 — Deploy events history captured

- **Auto-mark rule:** `✓ verified` if "Notable change events" covers the 90-day window (source: Event history) and includes deploy-style events for the service's compute resources. Events present but none deploy-style → `?` with note. Source unavailable (AccessDenied) → `?`. No runtime profile → `?`.
- **Evidence:** `runtime-profile.md` → "Control-Plane Activity" → "Notable change events".

### Item 9 — Managing principals enumerated (management events)

- **Auto-mark rule:** `✓ verified` if the principals table has ≥1 row. This item does **not** mean callers are known — that is item 19. Source unavailable → `?`. No runtime profile → `?`.
- **Evidence:** `runtime-profile.md` → principals table.

---

## Category: Alerting (items 10–12)

### Item 10 — Critical metrics have alarms

- **Auto-mark rule:** Interview Section 5 names alarms → `◐`. Explicit "no alarms" → `✗`. Empty → `?`.
- **Verification check:** `aws cloudwatch describe-alarms --profile {p} --region {r} --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Dims:Dimensions,Actions:AlarmActions}'` → `✓ verified` if alarms exist on the critical-path resources' error/latency/saturation metrics **and** have actions; alarms named in the interview but absent → `✗ conflict`; none → `✗`.
- **Evidence:** `interview-questionnaire.md` → Section 5; verification result.

### Item 11 — On-call rotation configured

- **Auto-mark rule:** Third-party pager — not provable from AWS. Interview names a rotation tool and current on-call, and the operator confirms they can see the rotation → `✓ attested`. Interview only → `◐`. Empty → `?`.
- **Evidence:** `interview-questionnaire.md` → Section 2.

### Item 12 — Paging path verified

- **Auto-mark rule:** Always `✓ attested` / `✗` from the operator.
- **Operator prompt:** "Have you personally received a test page from the on-call paging tool for this service in the last 7 days? (yes/no/scheduled-for-date)"

---

## Category: Runbooks (items 13–14)

### Item 13 — Top runbooks exist (≥3)

- **Auto-mark rule:** Interview Section 6 lists ≥3 runbooks → `◐`. The operator opens each link/path and confirms it exists and matches a symptom → `✓ verified` (cite the paths). Explicit "no runbooks" → `✗`. Empty → `?`.
- **Evidence:** `interview-questionnaire.md` → Section 6 → "Existing runbooks".

### Item 14 — Recent incidents documented

- **Auto-mark rule:** ≥1 incident in the last 12 months with a postmortem link the operator has opened → `✓ verified`; entries without links → `◐`; explicit "no incidents in 12 months" → `N/A` (cited); empty → `?`.
- **Evidence:** `interview-questionnaire.md` → Section 6 → "Incidents in last 12 months".

---

## Category: Deploy & Rollback (items 15–18)

### Item 15 — CI/CD access (incoming team can deploy)

- **Auto-mark rule:** Interview Section 4 says the incoming team's role has deploy permission → `◐`. Says it "will be added" / not yet → `✗`. Empty → `?`.
- **Verification check (AWS-side permission):** `aws iam simulate-principal-policy --policy-source-arn {incoming-role-arn} --action-names <the deploy actions from item 2's events> --resource-arns <service resource ARNs> --profile {p} --query 'EvaluationResults[].{Action:EvalActionName,Decision:EvalDecision}'` → all `allowed` → `✓ verified`; any `implicitDeny` / `explicitDeny` → `✗` (or `✗ conflict` if the interview said yes). The CI system's own access (e.g. pipeline project permissions) is not visible from AWS → operator attestation noted alongside.
- **Evidence:** `interview-questionnaire.md` → Section 4 → "Deploy permissions"; verification result.

### Item 16 — Deploy process documented

- **Auto-mark rule:** Interview describes how code reaches prod → `◐`. The described path matches the deploy principal and events in the runtime profile (e.g. "CI role X deploys" and X appears with deploy events) → `✓ verified`. Mismatch → `✗ conflict`. Empty → `?`.
- **Evidence:** `interview-questionnaire.md` → Section 4; `runtime-profile.md` principals + change events.

### Item 17 — Rollback path documented

- **Auto-mark rule:** Interview gives explicit rollback steps → `◐`. A rollback runbook path the operator has opened → `✓ verified` for "documented" (whether it works stays an open question unless a test date is cited). Explicit "no rollback procedure" → `✗`. Empty → `?`.
- **Evidence:** `interview-questionnaire.md` → Section 4 → "Rollback procedure".

### Item 18 — Deploy frequency known (DORA)

- **Auto-mark rule:** Interview gives a quantitative frequency → `◐`. Qualitative or empty → `?`.
- **Verification check:** count deploy-style events in `runtime-profile.md` → "Notable change events" over its window and compare. Within a factor of 2 → `✓ verified` (cite both); otherwise `✗ conflict`.
- **Evidence:** interview Section 4 → "Deploy frequency"; runtime profile change events.

---

## Category: Dependencies (items 19–21)

### Item 19 — Upstream callers identified

- **Auto-mark rule:** `runtime-profile.md` → "Wiring (configured callers)" rows are artifact evidence. Interview names callers with contacts and they match Wiring → `✓ verified`. Interview only → `◐`. Wiring shows a caller the interview omits (or the reverse) → `✗ conflict` for the difference. Explicit "none / unknown" with empty Wiring → `?`.
- **Evidence:** `runtime-profile.md` → Wiring; interview Section 8 → "Upstream callers".

### Item 20 — Downstream services identified

- **Auto-mark rule:** Interview lists downstream services with contract/SLA references → `◐`. They match the catalog Dependency Graph → `✓ verified`. Mismatch → `✗ conflict`. Empty → `?`.
- **Evidence:** interview Section 8; `service-catalog.md` → Dependency Graph.

### Item 21 — External API ownership known

- **Auto-mark rule:** Vendor + contract owner per entry → `◐`. The operator opens the cited contract/vendor record (procurement entry, vendor-management page) and it names the owner → `✓ verified` (cite the path/URL, no tokens). Listed without owners → `?`. Explicit "no external APIs" → `N/A`.
- **Evidence:** interview Section 8 → "External APIs".

---

## Category: Compliance (items 22–25)

### Item 22 — PII handling known

- **Auto-mark rule:** Non-empty answer → `◐`. The operator opens the cited data-classification / data-handling document for this service and it covers the PII fields the catalog's data stores hold → `✓ verified` (cite the path/URL). Explicit "no PII handled" → `N/A` (cited) — but if catalog resources are named or tagged as holding customer/payment data, that is `✗ conflict`. Empty → `?`.
- **Evidence:** interview Section 10 → "PII handling".

### Item 23 — Data retention policy known

- **Auto-mark rule:** Specific timeframe → `◐`. If the catalog shows the mechanism (S3 lifecycle rule, DynamoDB TTL, log-group retention) consistent with it → `✓ verified`; inconsistent → `✗ conflict`. Qualitative or empty → `?`.
- **Evidence:** interview Section 10; catalog configuration rows.

### Item 24 — Backups configured and restore tested

- **Auto-mark rule:** Interview describes backups and a restore-test date → `◐`. Explicit "no backups" → `✗`. Empty → `?`.
- **Verification check:** backup configuration for the stateful resources in the catalog — RDS `describe-db-instances --query 'DBInstances[].{Id:DBInstanceIdentifier,Retention:BackupRetentionPeriod,LatestRestorable:LatestRestorableTime}'`, DynamoDB `describe-continuous-backups --table-name {t} --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus'`, AWS Backup `list-recovery-points-by-resource --resource-arn {arn} --query 'RecoveryPoints[].{Created:CreationDate,Status:Status}'`. Backups on every stateful resource **and** a restore-test date within 12 months the operator attests to → `✓ verified`. Backups confirmed but restore untested/unattested → stays `◐` with note. A stateful resource without backups → `✗` (or `✗ conflict` if the interview claimed it).
- **Evidence:** interview Section 10; verification result.

### Item 25 — DR plan exists

- **Auto-mark rule:** RTO + RPO + DR runbook path → `◐`. The plan's regions/mechanisms are consistent with the Cross-Region Footprint and backup configuration (e.g. "active-passive to us-west-2" needs resources or replicated backups in us-west-2) → `✓ verified`; inconsistent → `✗ conflict`. Explicit "no DR plan" → `✗`. Partial → `?`.
- **Evidence:** interview Section 10; runtime-profile Cross-Region Footprint; item 24 result.

---

## Notes for the skill at runtime

1. **Evidence citations are mandatory.** Every mark in `readiness-scorecard.md` carries `[evidence: <path>:<line>]` where a line exists, else `[evidence: <path>#<heading>]`, or `[query: <command> @ <timestamp>]` for verification results. Attested items carry `[attested: <one-line operator note>]`.
2. **Unknown is the default.** Missing or ambiguous evidence → `?`. Presence of an answer → at most `◐`.
3. **Operator override log.** Every manual mark or override is appended to the "Manual override log" with timestamp, old mark, new mark and reason. An override can never turn `◐` into `✓ verified` without a cited artifact or query.
4. **Optional extras.** If `extra-checklist.md` exists in the run's handoff directory, its items are merged into an "Operator-supplied extras" section and use the same evidence classes. Extras never change the baseline verdict rule.
