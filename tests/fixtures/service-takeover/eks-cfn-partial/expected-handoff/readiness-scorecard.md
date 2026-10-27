---
readiness-scorecard-schema: 2
service: search-api
account: "123456789012"
region: eu-west-1
generated-at: 2026-05-12T15:55:00Z
verdict: partial
---

# Readiness Scorecard — search-api

**Verdict: partial** — 9 ✓ verified, 3 ✓ attested, 10 ◐ operator-stated, 0 ✗, 0 ✗ conflict, 3 ?, 0 N/A (25 items). 13 verification checks (listed per item) could move it toward `ready`. Evidence as of 2026-05-12T13:35:00Z.
**Why:** `◐` on items 2, 10, 15, 16, 18, 19, 21, 22, 24, 25; `?` on items 7, 8, 9 (the in-cluster workloads have no evidence).
**Generated:** 2026-05-12T15:55:00Z
**Operator:** alice (arn:aws:iam::123456789012:user/alice)

Rules applied: `readiness-scorecard-baseline.md` (template-version 3). One evidence class per item; a non-empty interview answer is at most `◐`; empty is `?`, never `✗`; arithmetic pass rates are shown per category but never decide the verdict. Citations are package-relative (`interview-questionnaire.md` is the snapshot of `filled-interview.md`).

---

## Per-category summary

| Category | Items | ✓ verified | ✓ attested | ◐ | ✗ | ✗ conflict | ? | N/A |
|---|---|---|---|---|---|---|---|---|
| Access | 1-3 | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| Inventory | 4-6 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| Runtime | 7-9 | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| Alerting | 10-12 | 0 | 2 | 1 | 0 | 0 | 0 | 0 |
| Runbooks | 13-14 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Deploy & Rollback | 15-18 | 1 | 0 | 3 | 0 | 0 | 0 | 0 |
| Dependencies | 19-21 | 1 | 0 | 2 | 0 | 0 | 0 | 0 |
| Compliance | 22-25 | 1 | 0 | 3 | 0 | 0 | 0 | 0 |
| **Total** | **25** | **9** | **3** | **10** | **0** | **0** | **3** | **0** |

## What would move this toward `ready`

- **The 3 `?` items (7, 8, 9 — the in-cluster Deployment has no evidence):** `helm history search-api -n search` gives the deploy history (8) and also settles 16 and 18; a query against the cluster's metrics backend over a stated window gives the activity baseline (7); the control-plane audit log, if enabled, says who changed cluster objects (9). These are operator actions, not AWS reads.
- **The 10 `◐` items:** 10 (alarm coverage; `kubectl get prometheusrules -n search` for the in-cluster alert rules), 2, 15, 16 (access entry and RBAC checks), 21 (a vendor or contract register entry), 18, 19 (confirm with the Web and Mobile teams), 22 (security confirms PII scope), 24 (a restore-test record), 25 (how data reaches eu-central-1).
- Nothing fails or conflicts, so the verdict is `partial`. CloudFormation ownership of 5 rows is recorded (item 4 note) and does not change a mark.

---

## Step 6 verification batch

Offered by default at Gate 6; alice approved it at 2026-05-12T15:33:00Z. Two read-only AWS commands, cost `unknown` (no pricing source read), `--profile prod-main --region eu-west-1`, after `aws sts get-caller-identity` re-confirmed account 123456789012. Only derived facts are recorded.

| # | Item | Check (read-only, projected; `--profile`/`--region` pinned) | Derived fact (raw output not recorded) | Timestamp |
|---|---|---|---|---|
| 1 | 10 | `aws cloudwatch describe-alarms --profile prod-main --region eu-west-1 --alarm-name-prefix search- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Dims:Dimensions,Actions:AlarmActions,Enabled:ActionsEnabled,State:StateValue}'` | 4 alarms returned; names match the interview; each has >= 1 action, `ActionsEnabled: true`, state `OK`. Metrics: ALB 5XX, ALB target response p95, queue oldest-message age, cache CPU. None for the S3 bucket, none for cache errors or latency, none for the in-cluster Deployment | 2026-05-12T15:35:10Z |
| 2 | 24 | `aws elasticache describe-replication-groups --profile prod-main --region eu-west-1 --replication-group-id search-cache --query 'ReplicationGroups[].SnapshotRetentionLimit'` (docs: https://docs.aws.amazon.com/cli/latest/reference/elasticache/describe-replication-groups.html @ 2026-05-12) | SnapshotRetentionLimit = 7 (days automatic snapshots are kept; 0 would mean backups off) | 2026-05-12T15:35:40Z |
| 3 | 6 | (artifact comparison, no AWS call) | interview Section 9 lists 1 Secrets Manager secret and 1 Kubernetes Secret; catalog Secret References lists the same 2 | 2026-05-12T15:35:40Z |
| 4 | 20 | (artifact comparison, no AWS call) | interview downstream list (3) = catalog outbound dependencies (3) | 2026-05-12T15:35:40Z |

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account — ✓ verified

- **Mark:** ✓ verified
- **Evidence:** [evidence: state.md:71]; [evidence: state.md:72]; [evidence: state.md:74]; [evidence: state.md:75]
- **Notes:** Caller account equals the intake account 123456789012. That call needs no permission, so the CloudTrail Event-history read (which does) is the proof of AWS read access. For the cluster: `kubectl config current-context` equals the intake context `platform-eks` and `kubectl auth can-i --list -n search` shows get/list on the workload objects. Derived facts only.

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

### Item 7 — Activity baseline captured — ?

- **Mark:** ?
- **Evidence:** [evidence: runtime-profile.md:131, runtime-profile.md:135]
- **Notes:** 0 of 3 compute and data-store resources covered: the Deployment (**gap: EKS in-cluster workloads are not traced**, [evidence: runtime-profile.md:137]), the ElastiCache group and the S3 bucket have no baseline row. The two rows that exist (ALB, SQS) are not those types. A point-in-time `kubectl get deploy` would not be a baseline.
- **Check that would verify it:** A query against the cluster's metrics backend for the Deployment over a stated window, recorded as `[query: … @ …]`; the cache and bucket metrics are not collected by `runtime-trace` either (operator action).

### Item 8 — Deploy events history captured — ?

- **Mark:** ?
- **Evidence:** [evidence: runtime-profile.md:114]
- **Notes:** 6 management events exist, all on data-layer or load-balancer resources (CloudFormation role, load-balancer controller, alice); none is a deploy to compute. Helm rollouts are Kubernetes API calls, not CloudTrail management events.
- **Check that would verify it:** `helm history search-api -n search` (operator; not an AWS read) would give the deploy history.

### Item 9 — Managing principals enumerated (management events) — ?

- **Mark:** ?
- **Evidence:** [evidence: runtime-profile.md:100, runtime-profile.md:101, runtime-profile.md:102]
- **Notes:** 3 managing principals for the AWS resources (management events only). Who changed the Deployment and other cluster objects is not in CloudTrail Event history; no control-plane audit-log query was recorded, so the in-cluster half is unknown. This does not say who calls the service.
- **Check that would verify it:** If the cluster's audit log is enabled (on EKS it goes to CloudWatch Logs), query it for changes to objects in namespace `search` over a stated window and cite the query (operator action).

## Category: Alerting (items 10–12)

### Item 10 — Critical metrics have alarms — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:68]; [query: aws cloudwatch describe-alarms --profile prod-main --region eu-west-1 --alarm-name-prefix search- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Dims:Dimensions,Actions:AlarmActions,Enabled:ActionsEnabled,State:StateValue}' @ 2026-05-12T15:35:10Z]
- **Notes:** All 4 alarms named in the interview exist, each enabled with an action and in state `OK` (ALB 5XX, ALB p95, queue age, cache CPU). They do not cover every compute and data-store resource: nothing alarms on the S3 bucket, the cache's errors or latency, or the in-cluster Deployment, and no alert-rule or notification-route check was made for the cluster.
- **Check that would verify it:** `kubectl get prometheusrules -n search` (where the Prometheus Operator CRD is installed, otherwise the monitoring backend's rules listing) plus the notification route to a receiver; add or justify the missing alarms and re-run `describe-alarms`.

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

### Item 21 — External API ownership known — ◐ operator-stated

- **Mark:** ◐ operator-stated
- **Evidence:** [stated: interview-questionnaire.md:92] — "None"
- **Notes:** The interview says none, and the catalog's outbound list has none. That is testimony plus an absence in discovery, not a record: no vendor or contract register is cited.
- **Check that would verify it:** Cite a vendor or contract register entry that lists no external API for this service (then `N/A`).

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
- **Evidence:** [stated: interview-questionnaire.md:108, interview-questionnaire.md:109]; [query: aws elasticache describe-replication-groups --profile prod-main --region eu-west-1 --replication-group-id search-cache --query 'ReplicationGroups[].SnapshotRetentionLimit' @ 2026-05-12T15:35:40Z]; [docs: https://docs.aws.amazon.com/cli/latest/reference/elasticache/describe-replication-groups.html @ 2026-05-12]
- **Notes:** ElastiCache snapshot retention is 7 days (matches the interview). The S3 bucket is versioned (catalog), but no backup check is listed for S3, so it is unchecked (`?`) for backups and is not counted as backed up. The 2026-03-02 restore test was run by the Search Team and is operator-stated: no ticket or run log is cited.
- **Check that would verify it:** Becomes `✓ verified` when a record of a restore test within 12 months exists (a ticket or runbook run log the operator opens and cites), and the bucket's backup is checked against its documentation.

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
