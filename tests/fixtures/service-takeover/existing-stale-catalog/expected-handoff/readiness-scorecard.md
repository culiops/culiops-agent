---
readiness-scorecard-schema: 2
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-12T16:05:00Z
verdict: not-ready
---

# Readiness Scorecard — payments

**Verdict: not-ready** — 12 ✓ verified, 3 ✓ attested, 8 ◐ operator-stated, 0 ✗, 1 ✗ conflict, 1 ?, 0 N/A (25 items). Evidence as of 2026-05-12T14:05:00Z.
**Why:** `✗ conflict` in Dependencies (19).
**Generated:** 2026-05-12T16:05:00Z
**Operator:** alice (arn:aws:iam::123456789012:user/alice)

Rules applied: `readiness-scorecard-baseline.md` (template-version 3). One evidence class per item; a non-empty interview answer is at most `◐`; empty is `?`, never `✗`; arithmetic pass rates are shown per category but never decide the verdict. Citations are package-relative (`interview-questionnaire.md` is the snapshot of `filled-interview.md`).

---

## Per-category summary

| Category | Items | ✓ verified | ✓ attested | ◐ | ✗ | ✗ conflict | ? | N/A |
|---|---|---|---|---|---|---|---|---|
| Access | 1-3 | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| Inventory | 4-6 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Runtime | 7-9 | 2 | 0 | 0 | 0 | 0 | 1 | 0 |
| Alerting | 10-12 | 0 | 2 | 1 | 0 | 0 | 0 | 0 |
| Runbooks | 13-14 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| Deploy & Rollback | 15-18 | 3 | 0 | 1 | 0 | 0 | 0 | 0 |
| Dependencies | 19-21 | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| Compliance | 22-25 | 1 | 0 | 3 | 0 | 0 | 0 | 0 |
| **Total** | **25** | **12** | **3** | **8** | **0** | **1** | **1** | **0** |

## What would move this toward `ready`

- **Conflict (item 19):** identify `legacy-orders-exec`. Any `✗ conflict` makes the verdict `not-ready`, so this is the one blocker; clearing it moves the verdict to `partial`.
- **Then the `?` item:** 7 (a query for the DynamoDB `payments-ledger` metrics, which `runtime-trace` did not collect).
- **Then the 8 `◐` items:** 10 (re-run `describe-alarms` once the missing alarms exist), 23 (retention period for `payments-ledger`), 13, 14, 17 (operator opens the runbook, postmortem and rollback links), 24 (a restore-test record), 21 (contract owner with procurement), 22 (PII scope with security).
- The stale catalog did not lower any mark: the re-run catalog is live-backed (`Live verification: performed 2026-05-12`).

---

## Step 6 verification batch

Offered by default at Gate 6; alice approved it at 2026-05-12T15:50:00Z. Four read-only AWS commands, cost `unknown` (no pricing source read), `--profile prod-main --region us-east-1`, after `aws sts get-caller-identity` re-confirmed account 123456789012. The skill ran them; only the derived facts below are recorded. The comparisons below need no AWS call and were made from the artifacts.

| # | Item | Check (read-only, projected; `--profile`/`--region` pinned) | Derived fact (raw output not recorded) | Timestamp |
|---|---|---|---|---|
| 1 | 10 | `aws cloudwatch describe-alarms --profile prod-main --region us-east-1 --alarm-name-prefix payments- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Dims:Dimensions,Actions:AlarmActions,Enabled:ActionsEnabled,State:StateValue}'` | 5 alarms returned; names match the interview; each has >= 1 action, `ActionsEnabled: true`, state `OK`. Metrics: authorization success rate (custom), queue depth, DLQ depth, Lambda `Errors` (all payments-* functions), Lambda `Duration` p99. None on DynamoDB `payments-ledger`; no throttle or concurrency alarm on any Lambda | 2026-05-12T15:52:10Z |
| 2 | 24 | `aws dynamodb describe-continuous-backups --profile prod-main --region us-east-1 --table-name payments-ledger --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus'` | `ENABLED` on `payments-ledger` | 2026-05-12T15:52:40Z |
| 3 | 15 | `aws iam simulate-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --action-names lambda:UpdateFunctionCode lambda:UpdateFunctionConfiguration --resource-arns <payments-authorizer ARN> <payments-capture ARN> <payments-reconciler ARN> --query 'EvaluationResults[].{Action:EvalActionName,Resource:EvalResourceName,Decision:EvalDecision}'` | 6 of 6 results `allowed` | 2026-05-12T15:53:20Z |
| 4 | 15 | `aws iam get-context-keys-for-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --query 'ContextKeyNames'` | empty list: no condition key in the role's policies needs a value | 2026-05-12T15:53:40Z |
| 5 | 6 | (artifact comparison, no AWS call) | interview Section 9 lists 2 Secrets Manager secrets; catalog Secret References lists the same 2 | 2026-05-12T15:53:20Z |
| 6 | 18 | (artifact comparison, no AWS call) | stated 5 deploys/quarter vs 5 runs of three events in 90 d: within a factor of 2 | 2026-05-12T15:53:20Z |
| 7 | 19 | (artifact comparison, no AWS call) | Wiring has `legacy-orders-exec` as an SQS sender; the interview omits it: conflict | 2026-05-12T15:53:20Z |
| 8 | 20 | (artifact comparison, no AWS call) | interview downstream list = catalog outbound dependencies (3 of 3) | 2026-05-12T15:53:20Z |

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: state.md:73]; [evidence: state.md:74]
- **Notes:** `aws sts get-caller-identity --query Account` returned the intake account 123456789012. That call needs no permission, so the CloudTrail Event-history read (`lookup-events`, which does) is the proof of read access: it succeeded in the same account. Only derived facts are recorded.

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
- **Evidence:** [evidence: service-catalog.md:17; service-catalog.md:34-41; service-catalog.md:45-46]; [evidence: runtime-profile.md:202]
- **Notes:** 8 attributed rows from real-discovery (live by construction), none `not found`. The 2 Unattributed items (API Gateway `abc123def456`, SNS `payments-events`) are each dispositioned in the catalog (recorded by the operator as dependencies, not inventory). All 8 resources the profile lists under Resources by region (3 Lambdas, 2 queues, 1 table, 2 secrets) appear in the catalog.

### Item 5 — Cross-region footprint known — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:204]
- **Notes:** All four checks pass (aggregator Region view, 17 indexed Regions, view includes tags, `Count.Complete=true`): no tagged resources outside us-east-1.

### Item 6 — Secrets/credentials references catalogued — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: service-catalog.md:54, service-catalog.md:55]; [stated: interview-questionnaire.md:209]
- **Notes:** Two secret references in a live-backed catalog. The interview (Section 9) lists the same two; the PagerDuty key is stored outside AWS, so there is no difference.

## Category: Runtime (items 7–9)

### Item 7 — Activity baseline captured — ?

- **Mark:** ?
- **Evidence:** [evidence: runtime-profile.md:168, runtime-profile.md:176]; [evidence: runtime-profile.md:212]
- **Notes:** 3 of 4 compute and data-store resources covered: the 3 Lambdas have rows with data (so do the 2 SQS queues), none `no-data`. DynamoDB `payments-ledger` has no row: the profile lists its metrics as not collected. One resource without a baseline row makes the item `?` (n of m covered), not `✓ verified`.
- **Check that would verify it:** A CloudWatch query for the table's metrics over a stated window, recorded as `[query: … @ …]` (operator action; `runtime-trace` does not cover `dynamodb:table`).

### Item 8 — Deploy events history captured — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:135, runtime-profile.md:143]
- **Notes:** 90-day Event history window; 15 deploy-style events on the compute resources.

### Item 9 — Managing principals enumerated (management events) — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:128, runtime-profile.md:129]
- **Notes:** 2 managing principals (management events only). This does not say who calls the service; see item 19.

## Category: Alerting (items 10–12)

### Item 10 — Critical metrics have alarms — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:119]; [query: aws cloudwatch describe-alarms --profile prod-main --region us-east-1 --alarm-name-prefix payments- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Dims:Dimensions,Actions:AlarmActions,Enabled:ActionsEnabled,State:StateValue}' @ 2026-05-12T15:52:10Z]
- **Notes:** All 5 alarms named in the interview exist, each enabled with at least one action and in state `OK`. They do not cover every compute and data-store resource: the DynamoDB table `payments-ledger` has no alarm, and none of the Lambdas has a throttle or concurrency (saturation) alarm. Alarms existing is not the same as the service being covered.
- **Check that would verify it:** Add the missing alarms (or record why a resource needs none), then re-run `describe-alarms` (Step 6 check).

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

### Item 15 — CI/CD access (incoming team can deploy) — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:98, interview-questionnaire.md:101]; [query: aws iam simulate-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --action-names lambda:UpdateFunctionCode lambda:UpdateFunctionConfiguration --resource-arns <payments-authorizer ARN> <payments-capture ARN> <payments-reconciler ARN> --query 'EvaluationResults[].{Action:EvalActionName,Resource:EvalResourceName,Decision:EvalDecision}' @ 2026-05-12T15:53:20Z]; [query: aws iam get-context-keys-for-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --query 'ContextKeyNames' @ 2026-05-12T15:53:40Z]
- **Notes:** The simulation returns `allowed` for both actions on all 3 functions (6 of 6). `get-context-keys-for-principal-policy` returns an empty list, so no condition key was left without a value and the simulation is a full result. The incoming team deploys with its own role (interview Section 4), so the AWS side is the check that applies; it does not depend on the pipeline's repository permissions.

### Item 16 — Deploy process documented — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:83]; [evidence: runtime-profile.md:135]
- **Notes:** The interview says GitHub Actions deploys through `payments-deploy-role`; that role is the principal on every `UpdateFunctionCode` event in the window.

### Item 17 — Rollback path documented — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:95]
- **Notes:** `revert-and-redeploy` workflow described; drill on 2026-04-22 is operator-stated.
- **Check that would verify it:** Open the rollback runbook (https://docs.example.com/payments/runbooks/rollback); the drill itself stays operator-stated unless attested.

### Item 18 — Deploy frequency known (DORA) — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:89]; [evidence: runtime-profile.md:117, runtime-profile.md:143]
- **Notes:** Interview: 5 production deploys in the last quarter. CloudTrail: 5 runs of three `UpdateFunctionCode` events (2026-02-18, 03-04, 03-22, 04-15, 05-08). Within a factor of 2.

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

### Item 23 — Data retention policy known — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:236]; [evidence: service-catalog.md:39]
- **Notes:** 7 years plus a 90-day grace via TTL on `expires_at`. The catalog confirms TTL is enabled on that attribute (live), but a TTL setting names only the attribute: each record's expiry time is data, so no configured period equals the stated one.
- **Check that would verify it:** Open the retention policy or the writer code that sets `expires_at` (document the operator opens and cites), or read the stored expiry of a sample record.

### Item 24 — Backups configured and restore tested — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:239, interview-questionnaire.md:242]; [query: aws dynamodb describe-continuous-backups --profile prod-main --region us-east-1 --table-name payments-ledger --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus' @ 2026-05-12T15:52:40Z]
- **Notes:** PITR is `ENABLED` on the only stateful resource, so the backup half is confirmed. The restore test (2026-02-15, 18 minutes) was run by the Pay Team and is operator-stated.
- **Check that would verify it:** Becomes `✓ verified` when there is a record of a restore test within 12 months: a ticket or runbook run log the operator opens and cites (the Pay Team's 2026-02-15 run, or one witnessed by the incoming team). The stated date alone stays `◐`.

### Item 25 — DR plan exists — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:245]; [evidence: runtime-profile.md:204, service-catalog.md:39]
- **Notes:** Single-region recovery from PITR (RTO 4 h, RPO 5 min, runbook link). That matches the footprint (nothing outside us-east-1) and the catalog (PITR enabled); no cross-region mechanism is claimed.

---

## Manual override log

| Timestamp | Item | Old mark | New mark | Operator | Reason |
|---|---|---|---|---|---|
| 2026-05-12T15:46:00Z | 2 | ◐ | ✓ verified | alice | Confirmed `payments-deploy-role` is the deploy role (profile row + confirmation). |
| 2026-05-12T15:58:00Z | 3 | ? | ✓ attested | alice | Console login and `list-functions` run today. |
| 2026-05-12T16:00:00Z | 11 | ◐ | ✓ attested | alice | Opened the PagerDuty schedule; rotation visible. |
| 2026-05-12T16:02:00Z | 12 | ? | ✓ attested | alice | Received a test page for a payments P1 alarm. |
