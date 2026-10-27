---
readiness-scorecard-schema: 2
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-12T16:00:00Z
verdict: not-ready
---

# Readiness Scorecard — payments

**Verdict: not-ready** — 10 ✓ verified, 3 ✓ attested, 5 ◐ operator-stated, 0 ✗, 1 ✗ conflict, 6 ?, 0 N/A (25 items). Evidence as of 2026-05-12T14:05:00Z.
**Why:** `✗ conflict` in Dependencies (19).
**Generated:** 2026-05-12T16:00:00Z
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
| Runbooks | 13-14 | 0 | 0 | 1 | 0 | 0 | 1 | 0 |
| Deploy & Rollback | 15-18 | 2 | 0 | 2 | 0 | 0 | 0 | 0 |
| Dependencies | 19-21 | 1 | 0 | 1 | 0 | 1 | 0 | 0 |
| Compliance | 22-25 | 0 | 0 | 0 | 0 | 0 | 4 | 0 |
| **Total** | **25** | **10** | **3** | **5** | **0** | **1** | **6** | **0** |

## What would move this toward `ready`

- **Conflict (item 19, High):** identify `legacy-orders-exec`. Any `✗ conflict` makes the verdict `not-ready`; clearing it moves the verdict to `partial`.
- **Checks (cheapest first):** a CloudWatch query for the DynamoDB `payments-ledger` metrics (7, `?`); `describe-alarms` (10) and `simulate-principal-policy` with `get-context-keys-for-principal-policy` for `platform-team-deploy` (15), which were not run because the batch was declined.
- **Documents to open:** the runbook and rollback links (13, 17); the Stripe contract owner with procurement (21).
- **Outgoing-team follow-ups (5 `?`):** Section 10 (items 22-25), the incident history (14). Empty is `?`, never `✗`.

---

## Step 6 verification batch

Offered by default at Gate 6; alice declined it at 2026-05-12T15:49:00Z (time). No command was run, so items 10 and 15 stay `◐` and the verdict is capped at `partial`. The comparisons below need no AWS call and were made from the artifacts.

| # | Item | Check (read-only, projected; `--profile`/`--region` pinned) | Derived fact (raw output not recorded) | Timestamp |
|---|---|---|---|---|
| 1 | 6 | (artifact comparison, no AWS call) | interview Section 9 lists 2 Secrets Manager secrets; catalog Secret References lists the same 2 | 2026-05-12T15:53:20Z |
| 2 | 18 | (artifact comparison, no AWS call) | stated 5 deploys/quarter vs 5 runs of three events in 90 d: within a factor of 2 | 2026-05-12T15:53:20Z |
| 3 | 19 | (artifact comparison, no AWS call) | Wiring has `legacy-orders-exec` as an SQS sender; the interview omits it: conflict | 2026-05-12T15:53:20Z |
| 4 | 20 | (artifact comparison, no AWS call) | interview downstream list = catalog outbound dependencies (3 of 3) | 2026-05-12T15:53:20Z |

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: state.md:71]; [evidence: state.md:72]
- **Notes:** `aws sts get-caller-identity --query Account` returned the intake account 123456789012. That call needs no permission, so the CloudTrail Event-history read (`lookup-events`, which does) is the proof of read access: it succeeded in the same account. Only derived facts are recorded.

### Item 2 — Deploy role identified — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:128]; [stated: interview-questionnaire.md:92]
- **Notes:** Hint from the profile: name contains `deploy` and 15 `UpdateFunctionCode` events. The interview names the same role. alice confirmed it at 2026-05-12T15:46:00Z (override log).

### Item 3 — Console+CLI access verified — ✓ attested

- **Mark:** ✓ attested
- **Evidence:** [attested: alice, 2026-05-12T15:52:00Z: ran `aws lambda list-functions --region us-east-1` and saw all three payments-* functions]
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
- **Evidence:** [evidence: service-catalog.md:54, service-catalog.md:55]; [stated: interview-questionnaire.md:201]
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
- **Evidence:** [stated: interview-questionnaire.md:113]
- **Notes:** 5 alarms named in the interview.
- **Check that would verify it:** `aws cloudwatch describe-alarms --profile prod-main --region us-east-1 --alarm-name-prefix payments- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Dims:Dimensions,Actions:AlarmActions,Enabled:ActionsEnabled,State:StateValue}'` (batch declined). `✓ verified` needs every compute and data-store resource covered by error, latency and saturation alarms, each enabled with an action and not in `INSUFFICIENT_DATA`; the DynamoDB table and Lambda saturation are the likely gaps.

### Item 11 — On-call rotation configured — ✓ attested

- **Mark:** ✓ attested
- **Evidence:** [attested: alice, 2026-05-12T15:54:00Z: opened the PagerDuty schedule for payments; weekly rotation Bob / Carol / Dan, Bob on call]; [stated: interview-questionnaire.md:48]
- **Notes:** Third-party pager; not provable from AWS.

### Item 12 — Paging path verified — ✓ attested

- **Mark:** ✓ attested
- **Evidence:** [attested: alice, 2026-05-12T15:56:00Z: received a test page for a payments P1 alarm]
- **Notes:** Paging tool; not provable from AWS.

## Category: Runbooks (items 13–14)

### Item 13 — Top runbooks exist (>=3) — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:137]
- **Notes:** 5 runbooks listed with links (docs.example.com).
- **Check that would verify it:** Open each link and confirm it matches a symptom (operator action; cite the paths).

### Item 14 — Recent incidents documented — ?

- **Mark:** ?
- **Evidence:** [stated: interview-questionnaire.md:144] is empty (`_To be filled in: ___`)
- **Notes:** Absence of data is not absence of incidents.
- **Check that would verify it:** Outgoing team to fill the incident history; then the operator opens the postmortem links.

## Category: Deploy & Rollback (items 15–18)

### Item 15 — CI/CD access (incoming team can deploy) — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:92, interview-questionnaire.md:95]
- **Notes:** The interview says the role was granted deploy permissions on 2026-05-08.
- **Check that would verify it:** `aws iam simulate-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --action-names lambda:UpdateFunctionCode lambda:UpdateFunctionConfiguration --resource-arns <payments-authorizer ARN> <payments-capture ARN> <payments-reconciler ARN> --query 'EvaluationResults[].{Action:EvalActionName,Resource:EvalResourceName,Decision:EvalDecision}'`, then `aws iam get-context-keys-for-principal-policy --profile prod-main --policy-source-arn arn:aws:iam::123456789012:role/platform-team-deploy --query 'ContextKeyNames'` to show no condition key was left without a value (batch declined).

### Item 16 — Deploy process documented — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:77]; [evidence: runtime-profile.md:135]
- **Notes:** The interview says GitHub Actions deploys through `payments-deploy-role`; that role is the principal on every `UpdateFunctionCode` event in the window.

### Item 17 — Rollback path documented — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:89]
- **Notes:** `revert-and-redeploy` workflow described; drill on 2026-04-22 is operator-stated.
- **Check that would verify it:** Open the rollback runbook (https://docs.example.com/payments/runbooks/rollback); the drill itself stays operator-stated unless attested.

### Item 18 — Deploy frequency known (DORA) — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:83]; [evidence: runtime-profile.md:117, runtime-profile.md:143]
- **Notes:** Interview: 5 production deploys in the last quarter. CloudTrail: 5 runs of three `UpdateFunctionCode` events (2026-02-18, 03-04, 03-22, 04-15, 05-08). Within a factor of 2.

## Category: Dependencies (items 19–21)

### Item 19 — Upstream callers identified — ✗ conflict

- **Mark:** ✗ conflict
- **Evidence:** [stated: interview-questionnaire.md:180]; [evidence: runtime-profile.md:156]
- **Notes:** Interview: upstream callers are checkout-service and billing-service (via API Gateway). Wiring: queue policy on `payments-capture-queue` also lets role `legacy-orders-exec` send; it is not in the interview. The API Gateway rows match.

### Item 20 — Downstream services identified — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:184]; [evidence: service-catalog.md:74, service-catalog.md:75, service-catalog.md:76]
- **Notes:** The 3 downstream services in the interview (Stripe API, fraud-detection, notifications-service) are exactly the catalog's outbound dependencies.

### Item 21 — External API ownership known — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:189]
- **Notes:** Stripe: vendor and contract owner (Bob L., renewal 2027-03) named. Contract ownership is not verifiable from AWS.
- **Check that would verify it:** alice confirms the contract owner with procurement and notes it (would be an attested note).

## Category: Compliance (items 22–25)

### Item 22 — PII handling known — ?

- **Mark:** ?
- **Evidence:** [stated: interview-questionnaire.md:225] is empty (`_To be filled in: ___`)
- **Notes:** Section 10 was not filled by the outgoing team.
- **Check that would verify it:** Outgoing team to answer; empty is never `✗`.

### Item 23 — Data retention policy known — ?

- **Mark:** ?
- **Evidence:** [stated: interview-questionnaire.md:228] is empty (`_To be filled in: ___`)
- **Notes:** No policy stated, so there is nothing to compare with the mechanism the catalog shows (service-catalog.md:39: TTL enabled on `expires_at`).
- **Check that would verify it:** Outgoing team to state the policy; the catalog TTL row then makes it checkable.

### Item 24 — Backups configured and restore tested — ?

- **Mark:** ?
- **Evidence:** [stated: interview-questionnaire.md:231] is empty (`_To be filled in: ___`)
- **Notes:** The catalog shows PITR enabled on `payments-ledger` (service-catalog.md:39), so backups exist; whether a restore was ever tested is unknown.
- **Check that would verify it:** Outgoing team to state the backup strategy and last restore test.

### Item 25 — DR plan exists — ?

- **Mark:** ?
- **Evidence:** [stated: interview-questionnaire.md:237] is empty (`_To be filled in: ___`)
- **Notes:** RTO, RPO, DR runbook and region are all unknown.
- **Check that would verify it:** Outgoing team to answer.

---

## Manual override log

| Timestamp | Item | Old mark | New mark | Operator | Reason |
|---|---|---|---|---|---|
| 2026-05-12T15:46:00Z | 2 | ◐ | ✓ verified | alice | Confirmed `payments-deploy-role` is the deploy role (profile row + confirmation). |
| 2026-05-12T15:52:00Z | 3 | ? | ✓ attested | alice | Console login and `list-functions` run today. |
| 2026-05-12T15:54:00Z | 11 | ◐ | ✓ attested | alice | Opened the PagerDuty schedule; rotation visible. |
| 2026-05-12T15:56:00Z | 12 | ? | ✓ attested | alice | Received a test page for a payments P1 alarm. |
