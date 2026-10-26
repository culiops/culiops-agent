---
readiness-scorecard-schema: 2
service: search-api
account: "123456789012"
region: eu-west-1
generated-at: 2026-05-12T15:55:00Z
verdict: partial
---

# Readiness Scorecard — search-api

**Verdict: partial** — 12 ✓ verified, 3 ✓ attested, 8 ◐ operator-stated, 0 ✗, 0 ✗ conflict, 1 ?, 1 N/A (25 items). 9 verification checks (listed per item) could move it toward `ready`.
**Why:** `◐` on items 2, 15, 16, 18, 19, 22, 24, 25; `?` on item 8.
**Generated:** 2026-05-12T15:55:00Z
**Operator:** alice (arn:aws:iam::123456789012:user/alice)

Rules applied: `readiness-scorecard-baseline.md` (template-version 2). One evidence class per item; a non-empty interview answer is at most `◐`; empty is `?`, never `✗`; arithmetic pass rates are shown per category but never decide the verdict. Citations are package-relative (`interview-questionnaire.md` is the snapshot of `filled-interview.md`).

---

## Per-category summary

| Category | Items | ✓ verified | ✓ attested | ◐ | ✗ | ✗ conflict | ? | N/A |
|---|---|---|---|---|---|---|---|---|
| Access | 1-3 | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| Inventory | 4-6 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Runtime | 7-9 | 2 | 0 | 0 | 0 | 0 | 1 | 0 |
| Alerting | 10-12 | 1 | 2 | 0 | 0 | 0 | 0 | 0 |
| Runbooks | 13-14 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Deploy & Rollback | 15-18 | 1 | 0 | 3 | 0 | 0 | 0 | 0 |
| Dependencies | 19-21 | 1 | 0 | 1 | 0 | 0 | 0 | 1 |
| Compliance | 22-25 | 1 | 0 | 3 | 0 | 0 | 0 | 0 |
| **Total** | **25** | **12** | **3** | **8** | **0** | **0** | **1** | **1** |

## What would move this toward `ready`

- **The one `?` (item 8):** `helm history search-api -n search` gives the Deployment's deploy history; it also settles 16 and 18 (operator action, not an AWS read).
- **The 8 `◐` items:** 2, 15, 16 (access entry and RBAC checks), 18, 19 (confirm with the Web and Mobile teams), 22 (security confirms PII scope), 24 (attested restore test), 25 (how data reaches eu-central-1).
- Nothing fails or conflicts, so the verdict is `partial`. CloudFormation ownership of 5 rows is recorded (item 4 note) and does not change a mark.

---

## Step 6 verification batch

Offered by default at Gate 6; alice approved it at 2026-05-12T15:33:00Z. Two read-only AWS commands, $0, `--profile prod-main --region eu-west-1`, after `aws sts get-caller-identity` re-confirmed account 123456789012. Only derived facts are recorded.

| # | Item | Check (read-only, projected; `--profile`/`--region` pinned) | Derived fact (raw output not recorded) | Timestamp |
|---|---|---|---|---|
| 1 | 10 | `aws cloudwatch describe-alarms --profile prod-main --region eu-west-1 --alarm-name-prefix search- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Actions:length(AlarmActions)}'` | 4 alarms returned; names match the interview; each has >= 1 action | 2026-05-12T15:35:10Z |
| 2 | 24 | `aws elasticache describe-replication-groups --profile prod-main --region eu-west-1 --replication-group-id search-cache --query 'ReplicationGroups[].SnapshotRetentionLimit'` | SnapshotRetentionLimit = 7 | 2026-05-12T15:35:40Z |
| 3 | 6 | (artifact comparison, no AWS call) | interview Section 9 lists 1 Secrets Manager secret and 1 Kubernetes Secret; catalog Secret References lists the same 2 | 2026-05-12T15:35:40Z |
| 4 | 20 | (artifact comparison, no AWS call) | interview downstream list (3) = catalog outbound dependencies (3) | 2026-05-12T15:35:40Z |

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: state.md:71]
- **Notes:** Caller account equals the intake account 123456789012; derived fact only.

### Item 2 — Deploy role identified — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:54]
- **Notes:** The interview names CI role `search-ci-deployer`. The profile's principals (CloudFormation service role, load-balancer controller, alice) show no deploy-style events: the Deployment is updated through the Kubernetes API, which CloudTrail Event history does not record.
- **Check that would verify it:** Operator confirms the role with the CI owner; `aws eks list-access-entries --cluster-name platform-eks` (read-only) shows whether its access entry exists.

### Item 3 — Console+CLI access verified — ✓ attested

- **Mark:** ✓ attested
- **Evidence:** [attested: alice, 2026-05-12T15:42:00Z: ran `aws sts get-caller-identity` and `aws eks describe-cluster --name platform-eks` successfully]
- **Notes:** Personal console/CLI login; no artifact can prove it.

## Category: Inventory (items 4–6)

### Item 4 — Resources enumerated — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: service-catalog.md:17; service-catalog.md:31-40]
- **Notes:** 10 attributed rows, live-backed (real-discovery over AWS and Kubernetes). Owner is mixed: 5 rows `cloudformation (<stack>)` (`search-data-stack`, `search-iam-stack`), 3 `helm search-api`, the ALB (controller-owned) and the log group (fluent-bit). Changes to the 5 CloudFormation rows must go through the stack, not the console.

### Item 5 — Cross-region footprint known — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:150]
- **Notes:** All four checks pass (aggregator view, 17 Regions, tags in view, complete): no tagged resources outside eu-west-1.

### Item 6 — Secrets/credentials references catalogued — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: service-catalog.md:50, service-catalog.md:51]; [stated: interview-questionnaire.md:99]
- **Notes:** One Secrets Manager reference and one Kubernetes Secret (key name only) in a live-backed catalog; the interview lists the same two.

## Category: Runtime (items 7–9)

### Item 7 — Activity baseline captured — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:131, runtime-profile.md:135]
- **Notes:** Two AWS rows with data (ALB, SQS). **Gap: EKS in-cluster workloads are not traced** ([evidence: runtime-profile.md:137]); the Deployment itself has no baseline here. Passes for the AWS resources only.

### Item 8 — Deploy events history captured — ?

- **Mark:** ?
- **Evidence:** [evidence: runtime-profile.md:114]
- **Notes:** 6 management events exist, all on data-layer or load-balancer resources (CloudFormation role, load-balancer controller, alice); none is a deploy to compute. Helm rollouts are Kubernetes API calls, not CloudTrail management events.
- **Check that would verify it:** `helm history search-api -n search` (operator; not an AWS read) would give the deploy history.

### Item 9 — Managing principals enumerated (management events) — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: runtime-profile.md:100, runtime-profile.md:101, runtime-profile.md:102]
- **Notes:** 3 managing principals (management events only). This does not say who calls the service.

## Category: Alerting (items 10–12)

### Item 10 — Critical metrics have alarms — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:68]; [query: aws cloudwatch describe-alarms --profile prod-main --region eu-west-1 --alarm-name-prefix search- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Actions:length(AlarmActions)}' @ 2026-05-12T15:35:10Z]
- **Notes:** All 4 alarms named in the interview exist, each with an action (ALB 5XX, ALB p95, queue age, cache CPU).

### Item 11 — On-call rotation configured — ✓ attested

- **Mark:** ✓ attested
- **Evidence:** [attested: alice, 2026-05-12T15:44:00Z: opened the PagerDuty schedule for search-api; weekly rotation, Omar on call]; [stated: interview-questionnaire.md:36]
- **Notes:** Third-party pager; not provable from AWS.

### Item 12 — Paging path verified — ✓ attested

- **Mark:** ✓ attested
- **Evidence:** [attested: alice, 2026-05-12T15:46:00Z: received a test page for a search-alb-5xx-rate test alert]
- **Notes:** Paging tool; not provable from AWS.

## Category: Runbooks (items 13–14)

### Item 13 — Top runbooks exist (>=3) — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:75]; [evidence: alice opened https://docs.example.com/search/runbooks/5xx-spike, .../reindex-stuck and .../rollback at 2026-05-12T15:38:00Z; each exists and matches its symptom]
- **Notes:** 3 runbooks, all opened by the operator.

### Item 14 — Recent incidents documented — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:76]; [evidence: alice opened https://docs.example.com/postmortems/2026-02-09 at 2026-05-12T15:38:00Z]
- **Notes:** 1 incident in 12 months with an opened postmortem.

## Category: Deploy & Rollback (items 15–18)

### Item 15 — CI/CD access (incoming team can deploy) — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:54, interview-questionnaire.md:55]
- **Notes:** The interview says an EKS access entry for `platform-team-eks` was created 2026-05-09 and mapped to `search-operators`. No deploy actions exist to simulate on the AWS side (item 2 has no deploy events); the in-cluster RBAC half is outside AWS.
- **Check that would verify it:** Operator runs `kubectl auth can-i update deployments -n search` as `platform-team-eks`, and `aws eks list-access-entries --cluster-name platform-eks` (read-only) shows the entry.

### Item 16 — Deploy process documented — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:49]
- **Notes:** GitHub Actions runs `helm upgrade --install` with `search-ci-deployer`. CloudTrail cannot corroborate a Kubernetes API deploy.
- **Check that would verify it:** `helm history search-api -n search` plus the access-entry check above.

### Item 17 — Rollback path documented — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:53]; [evidence: alice opened https://docs.example.com/search/runbooks/rollback at 2026-05-12T15:38:00Z]
- **Notes:** The rollback is documented (`helm rollback search-api <revision>`). That it works is operator-stated (last exercised 2026-03-30), not verified.

### Item 18 — Deploy frequency known (DORA) — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:51]
- **Notes:** "About weekly". No CloudTrail comparison is possible for in-cluster rollouts.
- **Check that would verify it:** `helm history search-api -n search` (operator) over 90 days.

## Category: Dependencies (items 19–21)

### Item 19 — Upstream callers identified — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:90]
- **Notes:** web-frontend and mobile-api via the ALB, with contacts. The Wiring section shows what the ALB forwards to, not who calls it.
- **Check that would verify it:** Operator confirms with the Web and Mobile teams (ALB access logs would show clients; not collected here).

### Item 20 — Downstream services identified — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:91]; [evidence: service-catalog.md:57]
- **Notes:** ElastiCache `search-cache`, SQS `search-reindex-queue` and the S3 bucket are exactly the catalog's outbound dependencies.

### Item 21 — External API ownership known — N/A

- **Mark:** N/A
- **Evidence:** [stated: interview-questionnaire.md:92] — "None"
- **Notes:** Explicit statement that no external APIs are used; the catalog's outbound list has none either.

## Category: Compliance (items 22–25)

### Item 22 — PII handling known — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:106]
- **Notes:** Free-text queries can contain personal data; query logs are the only place it lands. A PII answer is at most `◐`.
- **Check that would verify it:** Security contact confirms the scope and the 14-day log retention (operator action).

### Item 23 — Data retention policy known — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [stated: interview-questionnaire.md:107]; [evidence: service-catalog.md:36, service-catalog.md:37]
- **Notes:** Index snapshots 30 days and query logs 14 days; the catalog shows the S3 lifecycle (30 days) and the log-group retention (14 days) live, consistent with the interview.

### Item 24 — Backups configured and restore tested — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:108, interview-questionnaire.md:109]; [query: aws elasticache describe-replication-groups --profile prod-main --region eu-west-1 --replication-group-id search-cache --query 'ReplicationGroups[].SnapshotRetentionLimit' @ 2026-05-12T15:35:40Z]
- **Notes:** ElastiCache snapshot retention is 7 days (matches the interview) and the S3 bucket is versioned (catalog). The 2026-03-02 restore test was run by the Search Team and is operator-stated.
- **Check that would verify it:** Becomes `✓ verified` when the operator attests a restore test within 12 months.

### Item 25 — DR plan exists — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:110]; [evidence: runtime-profile.md:150]
- **Notes:** RTO 4 h, RPO 24 h and a runbook are stated. The footprint (nothing outside eu-west-1) is consistent with a rebuild-on-demand plan, but nothing shows where the snapshot data would come from if the Region were lost: the catalog shows no cross-Region copy of the ElastiCache snapshots or the S3 bucket.
- **Check that would verify it:** Outgoing team states how data reaches eu-central-1 (cross-Region snapshot copy or replication); then compare with the catalog.

---

## Manual override log

| Timestamp | Item | Old mark | New mark | Operator | Reason |
|---|---|---|---|---|---|
| 2026-05-12T15:38:00Z | 13 | ◐ | ✓ verified | alice | Opened the 3 runbook links; each exists and matches its symptom. |
| 2026-05-12T15:38:00Z | 14 | ◐ | ✓ verified | alice | Opened the postmortem link for INC-2026-02-09. |
| 2026-05-12T15:38:00Z | 17 | ◐ | ✓ verified | alice | Opened the rollback runbook (documented; not executed). |
| 2026-05-12T15:42:00Z | 3 | ? | ✓ attested | alice | Console/CLI login and `describe-cluster` run today. |
| 2026-05-12T15:44:00Z | 11 | ◐ | ✓ attested | alice | Opened the PagerDuty schedule; rotation visible. |
| 2026-05-12T15:46:00Z | 12 | ? | ✓ attested | alice | Received a test page. |
