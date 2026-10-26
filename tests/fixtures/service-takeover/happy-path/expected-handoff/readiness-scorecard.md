---
readiness-scorecard-schema: 2
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-12T16:05:00Z
verdict: not-ready
---

# Readiness Scorecard — payments

**Verdict: not-ready** — 12 ✓ verified, 3 ✓ attested, 6 ◐ operator-stated, 1 ✗, 3 ✗ conflict, 0 ?, 0 N/A (25 items).
**Why:** `✗` / `✗ conflict` in Deploy & Rollback (15, 18); Compliance (25).
**Generated:** 2026-05-12T16:05:00Z
**Operator:** alice (arn:aws:iam::123456789012:user/alice)

Rules applied: `readiness-scorecard-baseline.md` (template-version 2). One evidence class per item; a non-empty interview answer is at most `◐`; empty is `?`, never `✗`; arithmetic pass rates are shown per category but never decide the verdict. Citations are package-relative (`interview-questionnaire.md` is the snapshot of `filled-interview.md`).

---

## Per-category summary

| Category | Items | ✓ verified | ✓ attested | ◐ | ✗ | ✗ conflict | ? | N/A |
|---|---|---|---|---|---|---|---|---|
| Access | 1-3 | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| Inventory | 4-6 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Runtime | 7-9 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Alerting | 10-12 | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| Runbooks | 13-14 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| Deploy & Rollback | 15-18 | 1 | 0 | 1 | 1 | 1 | 0 | 0 |
| Dependencies | 19-21 | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| Compliance | 22-25 | 1 | 0 | 2 | 0 | 1 | 0 | 0 |
| **Total** | **25** | **12** | **3** | **6** | **1** | **3** | **0** | **0** |

## What would move this toward `ready`

- **Blocking (clear first):** item 15 (deploy permission for `platform-team-deploy`; one re-run of the simulation), item 25 (show or retract the us-west-2 standby), item 18 (explain 3-5/week vs 5 observed runs), item 19 (identify `legacy-orders-exec`). Until these clear, the verdict stays `not-ready`.
- **Then the 6 `◐` items:** 13, 14, 17 (operator opens the runbook, postmortem and rollback links), 21 (contract owner with procurement), 22 (PII scope with security), 24 (attested restore test).
- No item is `?`.

---

## Step 6 verification batch

Offered by default at Gate 6; alice approved it at 2026-05-12T15:50:00Z. Three read-only AWS commands, $0, `--profile prod-main --region us-east-1`, after `aws sts get-caller-identity` re-confirmed account 123456789012. The skill ran them; only the derived facts below are recorded. The comparisons below need no AWS call and were made from the artifacts.

| # | Item | Check (read-only, projected; `--profile`/`--region` pinned) | Derived fact (raw output not recorded) | Timestamp |
|---|---|---|---|---|
| 1 | 10 | `aws cloudwatch describe-alarms --profile prod-main --region us-east-1 --alarm-name-prefix payments- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Actions:length(AlarmActions)}'` | 5 alarms returned; names match the interview; each has >= 1 action | 2026-05-12T15:52:10Z |
| 2 | 24 | `aws dynamodb describe-continuous-backups --profile prod-main --region us-east-1 --table-name payments-ledger --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus'` | `ENABLED` on `payments-ledger` | 2026-05-12T15:52:40Z |
| 3 | 15 | `aws iam simulate-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --action-names lambda:UpdateFunctionCode lambda:UpdateFunctionConfiguration --resource-arns <payments-authorizer ARN> <payments-capture ARN> <payments-reconciler ARN> --query 'EvaluationResults[].{Action:EvalActionName,Resource:EvalResourceName,Decision:EvalDecision}'` | 6 of 6 results `implicitDeny` | 2026-05-12T15:53:20Z |
| 4 | 6 | (artifact comparison, no AWS call) | interview Section 9 lists 2 Secrets Manager secrets; catalog Secret References lists the same 2 | 2026-05-12T15:53:20Z |
| 5 | 18 | (artifact comparison, no AWS call) | stated 3-5/week vs 15 `UpdateFunctionCode` events = 5 runs in 90 d: conflict | 2026-05-12T15:53:20Z |
| 6 | 19 | (artifact comparison, no AWS call) | Wiring has `legacy-orders-exec` as an SQS sender; the interview omits it: conflict | 2026-05-12T15:53:20Z |
| 7 | 20 | (artifact comparison, no AWS call) | interview downstream list = catalog outbound dependencies (3 of 3) | 2026-05-12T15:53:20Z |

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: state.md:71]
- **Notes:** `aws sts get-caller-identity --query Account` returned the intake account 123456789012; only the derived fact is recorded.

### Item 2 — Deploy role identified — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:128]; [stated: interview-questionnaire.md:98]
- **Notes:** Hint from the profile: name contains `deploy` and 15 `UpdateFunctionCode` events. The interview names the same role. alice confirmed it at 2026-05-12T15:46:00Z (override log).

### Item 3 — Console+CLI access verified — ✓ attested

- **Mark:** ✓ attested
- **Evidence:** [attested: alice, 2026-05-12T15:58:00Z: ran `aws lambda list-functions --region us-east-1` and saw all three payments-* functions]
- **Notes:** Personal console/CLI login; no artifact can prove it.

## Category: Inventory (items 4–6)

### Item 4 — Resources enumerated — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: service-catalog.md:17; service-catalog.md:34-41]
- **Notes:** 8 attributed rows from real-discovery (live by construction), none `not found`. The 2 Unattributed items (API Gateway `abc123def456`, SNS `payments-events`) are not counted.

### Item 5 — Cross-region footprint known — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:204]
- **Notes:** All four checks pass (aggregator Region view, 17 indexed Regions, view includes tags, `Count.Complete=true`): no tagged resources outside us-east-1.

### Item 6 — Secrets/credentials references catalogued — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: service-catalog.md:54, service-catalog.md:55]; [stated: interview-questionnaire.md:209]
- **Notes:** Two secret references in a live-backed catalog. The interview (Section 9) lists the same two; the PagerDuty key is stored outside AWS, so there is no difference.

## Category: Runtime (items 7–9)

### Item 7 — Activity baseline captured — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:168, runtime-profile.md:176]
- **Notes:** 5 rows with data (3 Lambda, 2 SQS), none `no-data`. DynamoDB `payments-ledger` metrics are not collected (gap in the profile).

### Item 8 — Deploy events history captured — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:135, runtime-profile.md:143]
- **Notes:** 90-day Event history window; 15 deploy-style events on the compute resources.

### Item 9 — Managing principals enumerated (management events) — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:128, runtime-profile.md:129]
- **Notes:** 2 managing principals (management events only). This does not say who calls the service; see item 19.

## Category: Alerting (items 10–12)

### Item 10 — Critical metrics have alarms — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:119]; [query: aws cloudwatch describe-alarms --profile prod-main --region us-east-1 --alarm-name-prefix payments- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Actions:length(AlarmActions)}' @ 2026-05-12T15:52:10Z]
- **Notes:** All 5 alarms named in the interview exist, each with at least one action, on the error, queue-depth, DLQ and latency metrics of the critical path.

### Item 11 — On-call rotation configured — ✓ attested

- **Mark:** ✓ attested
- **Evidence:** [attested: alice, 2026-05-12T16:00:00Z: opened the PagerDuty schedule for payments; weekly rotation Bob / Carol / Dan, Bob on call]; [stated: interview-questionnaire.md:48]
- **Notes:** Third-party pager; not provable from AWS.

### Item 12 — Paging path verified — ✓ attested

- **Mark:** ✓ attested
- **Evidence:** [attested: alice, 2026-05-12T16:02:00Z: received a test page for a payments P1 alarm]
- **Notes:** Paging tool; not provable from AWS.

## Category: Runbooks (items 13–14)

### Item 13 — Top runbooks exist (>=3) — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:143]
- **Notes:** 5 runbooks listed with links (docs.example.com).
- **Check that would verify it:** Open each link and confirm it matches a symptom (operator action; cite the paths).

### Item 14 — Recent incidents documented — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:150]
- **Notes:** 2 incidents listed with postmortem links.
- **Check that would verify it:** Open the 2 postmortem links (operator action).

## Category: Deploy & Rollback (items 15–18)

### Item 15 — CI/CD access (incoming team can deploy) — ✗

- **Mark:** ✗
- **Evidence:** [stated: interview-questionnaire.md:98, interview-questionnaire.md:101]; [query: aws iam simulate-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --action-names lambda:UpdateFunctionCode lambda:UpdateFunctionConfiguration --resource-arns <payments-authorizer ARN> <payments-capture ARN> <payments-reconciler ARN> --query 'EvaluationResults[].{Action:EvalActionName,Resource:EvalResourceName,Decision:EvalDecision}' @ 2026-05-12T15:53:20Z]
- **Notes:** The interview says `platform-team-deploy` "will need to be added" to the deploy permissions. The simulation agrees: `implicitDeny` for `lambda:UpdateFunctionCode` and `lambda:UpdateFunctionConfiguration` on all 3 functions (6 of 6 results). The CI system's own access is not visible from AWS.

### Item 16 — Deploy process documented — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:83]; [evidence: runtime-profile.md:135]
- **Notes:** The interview says GitHub Actions deploys through `payments-deploy-role`; that role is the principal on every `UpdateFunctionCode` event in the window.

### Item 17 — Rollback path documented — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:95]
- **Notes:** `revert-and-redeploy` workflow described; drill on 2026-04-22 is operator-stated.
- **Check that would verify it:** Open the rollback runbook (https://docs.example.com/payments/runbooks/rollback); the drill itself stays operator-stated unless attested.

### Item 18 — Deploy frequency known (DORA) — ✗ conflict

- **Mark:** ✗ conflict
- **Evidence:** [stated: interview-questionnaire.md:89]; [evidence: runtime-profile.md:117, runtime-profile.md:143]
- **Notes:** Interview: 3-5 deploys per week (about 39-65 in 90 days). CloudTrail Event history: 15 `UpdateFunctionCode` events = 5 runs of three functions (about 0.4/week); even counting each function update as its own deploy it is about 1.2/week, more than 2x below the stated rate. Deploys through another account/Region would not appear here; that is the open question.

## Category: Dependencies (items 19–21)

### Item 19 — Upstream callers identified — ✗ conflict

- **Mark:** ✗ conflict
- **Evidence:** [stated: interview-questionnaire.md:188]; [evidence: runtime-profile.md:156]
- **Notes:** Interview: upstream callers are checkout-service and billing-service (via API Gateway). Wiring: queue policy on `payments-capture-queue` also lets role `legacy-orders-exec` send; it is not in the interview. The API Gateway rows match.

### Item 20 — Downstream services identified — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:192]; [evidence: service-catalog.md:74, service-catalog.md:75, service-catalog.md:76]
- **Notes:** The 3 downstream services in the interview (Stripe API, fraud-detection, notifications-service) are exactly the catalog's outbound dependencies.

### Item 21 — External API ownership known — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:197]
- **Notes:** Stripe: vendor and contract owner (Bob L., renewal 2027-03) named. Contract ownership is not verifiable from AWS.
- **Check that would verify it:** alice confirms the contract owner with procurement and notes it (would be an attested note).

## Category: Compliance (items 22–25)

### Item 22 — PII handling known — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:233]
- **Notes:** customer_id (UUID), masked card last-4, amounts, timestamps; KMS encryption; Stripe tokenizes card numbers. A PII answer is at most `◐`: it is a policy statement, not something AWS can confirm.
- **Check that would verify it:** Security/compliance contact confirms the PII scope (operator action).

### Item 23 — Data retention policy known — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:236]; [evidence: service-catalog.md:39]
- **Notes:** 7 years plus a 90-day grace via TTL on `expires_at`. The catalog confirms TTL is enabled on that attribute (live); the per-record expiry values are data and were not read.

### Item 24 — Backups configured and restore tested — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:239, interview-questionnaire.md:242]; [query: aws dynamodb describe-continuous-backups --profile prod-main --region us-east-1 --table-name payments-ledger --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus' @ 2026-05-12T15:52:40Z]
- **Notes:** PITR is `ENABLED` on the only stateful resource, so the backup half is confirmed. The restore test (2026-02-15, 18 minutes) was run by the Pay Team and is operator-stated.
- **Check that would verify it:** Becomes `✓ verified` when the operator attests a restore test within 12 months (witness one, or have Carol repeat it).

### Item 25 — DR plan exists — ✗ conflict

- **Mark:** ✗ conflict
- **Evidence:** [stated: interview-questionnaire.md:245, interview-questionnaire.md:239]; [evidence: runtime-profile.md:204]
- **Notes:** Interview: active-passive failover to us-west-2 (RTO 30 min, RPO 5 min, drill 2025-11-01). Resource Explorer (complete, tag-visible) finds nothing outside us-east-1, and the same interview says cross-region backup is not enabled. An untagged standby is possible; no source shows one.

---

## Manual override log

| Timestamp | Item | Old mark | New mark | Operator | Reason |
|---|---|---|---|---|---|
| 2026-05-12T15:46:00Z | 2 | ◐ | ✓ verified | alice | Confirmed `payments-deploy-role` is the deploy role (profile row + confirmation). |
| 2026-05-12T15:58:00Z | 3 | ? | ✓ attested | alice | Console login and `list-functions` run today. |
| 2026-05-12T16:00:00Z | 11 | ◐ | ✓ attested | alice | Opened the PagerDuty schedule; rotation visible. |
| 2026-05-12T16:02:00Z | 12 | ? | ✓ attested | alice | Received a test page for a payments P1 alarm. |
