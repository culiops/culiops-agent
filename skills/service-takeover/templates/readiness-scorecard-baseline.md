---
template-version: 3
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
| `✓ attested` | Operator attestation with a one-line note | **Only** items 3, 11 and 12 — facts no artifact or query can prove (personal console login, a rotation in a third-party pager, a test page received). The note names what was observed and when (e.g. "test page received 14:02 today") |
| `◐ operator-stated` | An interview or operator answer on a **checkable** fact, not yet verified | The interview answers the question but no artifact or query confirms it |
| `✗` | Evidence shows the item fails | Cited artifact, query, or an explicit interview "no X" |
| `✗ conflict` | Interview and artifact disagree | Both sources cited; always a High open question |
| `?` | Unknown | Evidence missing, empty, ambiguous, or upstream says "not verifiable" |
| `N/A` | Does not apply | A cited artifact or record says so (e.g. the vendor-contract register lists none). An interview statement alone is `◐`, never `N/A` |

**Presence is not proof.** A non-empty interview answer yields at most `◐`. Empty means `?`, never `✗`.

**Document-backed items** (13, 14, 17, 21, 22, 25): an answer that points to a document becomes `✓ verified` when the operator opens the cited document and it actually answers the item. The citation is the document path or URL (never one carrying a token). Every item therefore has a path to `✓ verified`, `✓ attested` or `N/A` — `ready` is reachable, but only with evidence.

**Conflict check.** Before finalising, compare every interview answer that has an artifact counterpart (deploy frequency vs CloudTrail deploy events; upstream callers vs Wiring; downstream services vs the catalog dependency graph; regions in DR answers vs the Cross-Region Footprint; secrets listed vs catalog secret references; backup claims vs catalog backup config). Disagreement → `✗ conflict`.

## Verdict (strict)

- **`ready`** — every item, and every operator-supplied extra, is `✓ verified`, `✓ attested` or `N/A`.
- **`not-ready`** — any `✗` or `✗ conflict`, in any category. No category is exempt: an interview that claims alarms the account does not have (item 10) is as serious as a missing deploy role.
- **`partial`** — everything else, i.e. any `◐` or `?`.

The verdict line always states the counts and, for `partial`, the number of verification checks that could move it toward `ready`. Arithmetic pass rates are reported per category but never decide the verdict. The verdict also states the oldest timestamp behind any `✓` ("evidence as of").

**Open-question priority.** High = every `✗` and `✗ conflict`; Medium = every `?` and `◐`; Low = notes on `✓` items. Within a level, the cheapest resolution first: a verification check, then a document to open, then an outgoing-team follow-up. Each entry names its item number and mark; the README's top 5 is the first five.

## Step 6 verification batch (optional, offered by default)

For each `◐` item that has a verification check, the skill proposes the check as a read-only, projected command (with `--profile` / `--region` pinned to the intake account, confirmed by `aws sts get-caller-identity`). The operator approves the batch, runs it (or lets the skill run it, per the Step 1.5 rule for targeted commands), and the skill records only the derived fact with the command and timestamp as evidence. Skipping the batch leaves those items `◐` and the verdict `partial`.

**Permissions for the probes and the batch** (read-only; shown to the operator before the batch). AWS: `cloudtrail:LookupEvents`, `cloudwatch:DescribeAlarms`, `iam:SimulatePrincipalPolicy`, `iam:GetContextKeysForPrincipalPolicy`, `rds:DescribeDBInstances` / `DescribeDBClusters`, `dynamodb:DescribeContinuousBackups`, `backup:ListRecoveryPointsByResource`, `backup:ListRestoreJobsByProtectedResource` (`sts:GetCallerIdentity` needs none). Kubernetes: `get` / `list` on the workload, rollout and monitoring objects in the namespace. `kubectl auth can-i` as the operator's own identity needs nothing extra; `--as=<subject>` needs the `impersonate` verb (docs: https://kubernetes.io/docs/reference/access-authn-authz/user-impersonation/), so prefer having the incoming-team member run it as themselves.

**Delivery model and Kubernetes.** Items 2, 8, 15, 16 and 18 depend on how changes reach production (intake field). CloudTrail shows deploys that are AWS API calls made by a role. A CI/CD pipeline's calls show under the pipeline's role; a GitOps controller's changes to cluster objects do not show in CloudTrail at all. Each of those items says what to use for the other models. Where a check has a Kubernetes equivalent it is on the line starting `Kubernetes:`. The runtime profile does not trace in-cluster workloads (a recorded gap), so for them items 7–9 and 19 are `?` unless a Kubernetes check supplies the evidence.

---

## Category: Access (items 1–3)

### Item 1 — Operator has IAM read in target account

- **Auto-mark rule:** `✓ verified` if `state.md` records the Step 1.5 identity probe (`aws sts get-caller-identity --query Account`), the account equals the intake account, **and** at least one read that needs a permission succeeded in that account (the CloudTrail Event-history probe, or a sibling-skill read recorded in `state.md`). `GetCallerIdentity` needs no permissions, so alone it proves who and where, not read access (docs: https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html) — probe only → `◐`. Mismatch → `✗`. No probe → `?`.
- **Kubernetes:** also `kubectl config current-context` equals the intake context and `kubectl auth can-i --list -n <ns>` (as the operator, no `--as`) shows get/list on the workload objects; otherwise `?`.
- **Evidence:** `state.md` → "Step 1.5: identity-probe-result".

### Item 2 — Deploy role identified

- **Auto-mark rule:** The runtime profile's principals table (management events) is a **hint**: a principal whose name contains `deploy`, or whose events include deploy-style actions (`UpdateFunctionCode`, `UpdateService`, `RegisterTaskDefinition`, `CreateDeployment`). The operator confirms the role → `✓ verified` (profile row + confirmation). Interview names a role not in the profile → `◐`. Interview and profile name different roles with no overlap → `✗ conflict`. Neither → `?`.
- **Evidence:** `runtime-profile.md` → "Control-Plane Activity (CloudTrail)" → "Principals touching this service"; `interview-questionnaire.md` → Section 4.
- **Pipeline / GitOps:** the deployer is the pipeline's role or the controller's ServiceAccount, not a person. Cite the pipeline definition or the controller object (e.g. an Argo CD `Application`, whose `spec.source` names the repo, or a Flux `Kustomization`, whose `spec.sourceRef` names the source) as the evidence, with the same operator confirmation.
- **Operator prompt:** "Which of these principals is the deploy role? Paste the ARN."

### Item 3 — Console+CLI access verified

- **Auto-mark rule:** Always `✓ attested` / `✗` from the operator — no artifact can prove a personal login.
- **Operator prompt:** "Have you personally logged in to the AWS console for this account AND run a read-only CLI command successfully today? (yes/no/explain)"

---

## Category: Inventory (items 4–6)

### Item 4 — Resources enumerated

- **Auto-mark rule:** Count only **attributed** inventory rows (not the "Unattributed — operator assigns" list). `✓ verified` if ≥1 row and the catalog is live-backed: `**Live verification:** performed` (IaC path, Step 2V) or `Discovery source: real-discovery`. Rows marked `not found` are listed as open questions. `✓ verified` also needs the Unattributed list to be empty or every row dispositioned by the operator (in scope, or out of scope with a reason), and every compute and data-store resource in the runtime profile's "Cross-Region Footprint → Resources by region" to appear in the catalog; differences → `◐`, listed as open questions. Code-only catalog (`Live verification: not performed`) → `◐`. Catalog exists with no attributed rows → `✗`. No catalog → `?`.
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

- **Auto-mark rule:** `✓ verified` if "Activity Baselines (CloudWatch)" has a row with data for **every** compute and data-store resource in the catalog (verdicts `no-data` / `metric-not-found` don't count as captured). Any resource without one, or listed under "Resource types not covered" in Gaps and Caveats → `?`, with "n of m covered" and the missing resources as open questions. CloudWatch skipped → `?`. In-cluster workloads (a recorded gap) count as missing until the Kubernetes line below supplies evidence. No runtime profile → `?`.
- **Kubernetes:** a point-in-time read (`kubectl get deploy,sts,ds -n <ns>` desired vs ready, restarts) is not a baseline; a baseline is a query against the cluster's metrics backend over a stated window, recorded as `[query: … @ …]`. Without one → `?`.
- **Evidence:** `runtime-profile.md` → "Activity Baselines (CloudWatch)".

### Item 8 — Deploy events history captured

- **Auto-mark rule:** `✓ verified` if "Notable change events" covers the 90-day window (source: Event history) and includes deploy-style events for the service's compute resources. Events present but none deploy-style → `?` with note (under CI or GitOps delivery, no deploy-style events in Event history is not evidence of no deploys). Source unavailable (AccessDenied) → `?`. No runtime profile → `?`. Event history covers 90 days of management events per Region (docs: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html).
- **Kubernetes:** `kubectl rollout history <kind>/<name> -n <ns>`, `helm history <release> -n <ns>`, or the GitOps controller's own history (`argocd app history <app>`; a Flux `Kustomization` keeps only its last 5 reconciliations in `.status.history`) → `✓ verified` with the window stated. A Deployment keeps only `revisionHistoryLimit` old ReplicaSets (default 10), so the window may be short (docs: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/; https://fluxcd.io/flux/components/kustomize/kustomizations/; https://argo-cd.readthedocs.io/en/latest/user-guide/commands/argocd_app_history/).
- **Evidence:** `runtime-profile.md` → "Control-Plane Activity" → "Notable change events".

### Item 9 — Managing principals enumerated (management events)

- **Auto-mark rule:** `✓ verified` if the principals table has ≥1 row. This item does **not** mean callers are known — that is item 19. Source unavailable → `?`. No runtime profile → `?`.
- **Kubernetes:** who changed cluster objects is in the control-plane audit log, only if it is enabled (on EKS it is delivered to CloudWatch Logs, docs: https://aws.amazon.com/eks/features/; elsewhere it goes wherever the cluster ships it). Log enabled and queried → `✓ verified` (cite the query); otherwise `?`.
- **Evidence:** `runtime-profile.md` → principals table.

---

## Category: Alerting (items 10–12)

### Item 10 — Critical metrics have alarms

- **Auto-mark rule:** Interview Section 5 names alarms → `◐`. Explicit "no alarms" → `✗`. Empty → `?`.
- **Verification check:** `aws cloudwatch describe-alarms --profile {p} --region {r} --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Dims:Dimensions,Actions:AlarmActions,Enabled:ActionsEnabled,State:StateValue}'` → `✓ verified` if every compute and data-store resource in the catalog has alarms on its error, latency and saturation metrics, each with `ActionsEnabled: true` and at least one action. The metrics are the ones in the runtime profile's Activity Baselines row for that resource, or, where there is none, named from documentation read in this session (`docs: <URL>`) and confirmed by the operator. An alarm in `INSUFFICIENT_DATA`, or with actions disabled, does not count → `◐` with a note. Alarms named in the interview but absent → `✗ conflict`; none → `✗`.
- **Kubernetes:** alert rules for the namespace's workloads — `kubectl get prometheusrules -n <ns>` where the Prometheus Operator CRD is installed, otherwise the monitoring backend's rules listing — plus a notification route to a receiver. Same coverage rule; rule names and the route cited.
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

- **Auto-mark rule:** ≥1 incident in the last 12 months with a postmortem link the operator has opened → `✓ verified`; entries without links → `◐`; "no incidents in 12 months" → `◐`, and `N/A` only when the operator cites a query of the incident tracker or on-call log that shows none; empty → `?`.
- **Evidence:** `interview-questionnaire.md` → Section 6 → "Incidents in last 12 months".

---

## Category: Deploy & Rollback (items 15–18)

### Item 15 — CI/CD access (incoming team can deploy)

- **Auto-mark rule:** Interview Section 4 says the incoming team can deploy → `◐`. Says it "will be added" / not yet → `✗`. Empty → `?`. What "can deploy" means depends on the delivery model, and `✓ verified` needs every side that applies:
  - *Deploys with its own IAM role:* the AWS-side check below.
  - *Deploys through a pipeline or GitOps repo:* the ability to merge or trigger is a Git-host or CI permission, not visible from AWS or the cluster. Evidence is a cited record — the permission list the operator opens, or a pipeline run / sync triggered by an incoming-team member (a no-op redeploy is run by the team outside this skill). The statement alone stays `◐`. The role the pipeline uses is item 2.
- **Verification check (AWS-side permission):** `aws iam simulate-principal-policy --policy-source-arn {incoming-role-arn} --action-names <the deploy actions from item 2's events> --resource-arns <service resource ARNs> --profile {p} --query 'EvaluationResults[].{Action:EvalActionName,Decision:EvalDecision}'` → all `allowed` **and** `aws iam get-context-keys-for-principal-policy` lists no condition key the simulation had no value for → `✓ verified`. Unresolved condition keys → `◐ (simulated)`: the simulator's results can differ from live (docs: https://docs.aws.amazon.com/IAM/latest/APIReference/API_SimulatePrincipalPolicy.html). Any `implicitDeny` / `explicitDeny` → `✗` (or `✗ conflict` if the interview said yes).
- **Kubernetes:** `kubectl auth can-i <verb> <resource> -n <ns>` for the verbs the rollout uses (and `--list`), run by an incoming-team member as themselves; `--as=<subject>` only if the operator holds `impersonate`. `yes` for all → `✓ verified`; any `no` → `✗`.
- **Evidence:** `interview-questionnaire.md` → Section 4 → "Deploy permissions"; verification result.

### Item 16 — Deploy process documented

- **Auto-mark rule:** Interview describes how code reaches prod → `◐`. The described path matches the deploy principal and events in the runtime profile (e.g. "CI role X deploys" and X appears with deploy events; under GitOps, the controller object from item 2 and its sync history) → `✓ verified`. Mismatch → `✗ conflict`. Empty → `?`.
- **Evidence:** `interview-questionnaire.md` → Section 4; `runtime-profile.md` principals + change events.

### Item 17 — Rollback path documented

- **Auto-mark rule:** Interview gives explicit rollback steps → `◐`. A rollback runbook path the operator has opened → `✓ verified` for "documented" (whether it works stays an open question unless a test date is cited). Explicit "no rollback procedure" → `✗`. Empty → `?`.
- **Evidence:** `interview-questionnaire.md` → Section 4 → "Rollback procedure".

### Item 18 — Deploy frequency known (DORA)

- **Auto-mark rule:** Interview gives a quantitative frequency → `◐`. Qualitative or empty → `?`.
- **Verification check:** count deploys over a stated window from the source that sees this service's delivery model — `runtime-profile.md` → "Notable change events" for deploys made as AWS API calls; for Kubernetes or GitOps, the rollout / Helm / controller history from item 8 — and compare with the stated figure. Show both. Within a factor of 2 (a convention, not a standard) → `✓ verified`; otherwise `✗ conflict`. A source that cannot see the delivery model's deploys gives `?`, never `✗ conflict`.
- **Evidence:** interview Section 4 → "Deploy frequency"; runtime profile change events.

---

## Category: Dependencies (items 19–21)

### Item 19 — Upstream callers identified

- **Auto-mark rule:** `runtime-profile.md` → "Wiring (configured callers)" rows are artifact evidence. Interview names callers with contacts and they match Wiring → `✓ verified`. Interview only → `◐`. Wiring shows a caller the interview omits (or the reverse) → `✗ conflict` for the difference. Explicit "none / unknown" with empty Wiring → `?`.
- **Kubernetes:** `kubectl get ingress,svc,networkpolicy -n <ns>` shows what is configured to reach the workload (not observed traffic); cite the query. Wiring is not collected for in-cluster workloads, so without it the callers are `◐` at best.
- **Evidence:** `runtime-profile.md` → Wiring; interview Section 8 → "Upstream callers".

### Item 20 — Downstream services identified

- **Auto-mark rule:** Interview lists downstream services with contract/SLA references → `◐`. They match the catalog Dependency Graph → `✓ verified`. Mismatch → `✗ conflict`. Empty → `?`.
- **Evidence:** interview Section 8; `service-catalog.md` → Dependency Graph.

### Item 21 — External API ownership known

- **Auto-mark rule:** Vendor + contract owner per entry → `◐`. The operator opens the cited contract/vendor record (procurement entry, vendor-management page) and it names the owner → `✓ verified` (cite the path/URL, no tokens). Listed without owners → `?`. "No external APIs" → `◐`, and `N/A` only with a cited record (vendor or contract register) that lists none.
- **Evidence:** interview Section 8 → "External APIs".

---

## Category: Compliance (items 22–25)

### Item 22 — PII handling known

- **Auto-mark rule:** Non-empty answer → `◐`. The operator opens the cited data-classification / data-handling document for this service and it covers the PII fields the catalog's data stores hold → `✓ verified` (cite the path/URL). "No PII handled" → `◐`, and `N/A` only with a cited data-classification record that says so — and if catalog resources are named or tagged as holding customer/payment data, that is `✗ conflict`. Empty → `?`.
- **Evidence:** interview Section 10 → "PII handling".

### Item 23 — Data retention policy known

- **Auto-mark rule:** Specific timeframe → `◐`. If the catalog shows a mechanism whose configured period equals it (S3 lifecycle expiration days, log-group retention days) → `✓ verified`; a mechanism with no period in the configuration (DynamoDB TTL is on, but the expiry is per-item data) → `◐`; a different period → `✗ conflict`. Qualitative or empty → `?`.
- **Evidence:** interview Section 10; catalog configuration rows.

### Item 24 — Backups configured and restore tested

- **Auto-mark rule:** Interview describes backups and a restore-test date → `◐`. Explicit "no backups" → `✗`. Empty → `?`.
- **Verification check:** backup configuration for the stateful resources in the catalog — RDS `describe-db-instances --query 'DBInstances[].{Id:DBInstanceIdentifier,Retention:BackupRetentionPeriod,LatestRestorable:LatestRestorableTime}'`, DynamoDB `describe-continuous-backups --table-name {t} --query 'ContinuousBackupsDescription.PointInTimeRecoveryDescription.PointInTimeRecoveryStatus'`, AWS Backup `list-recovery-points-by-resource --resource-arn {arn} --query 'RecoveryPoints[].{Created:CreationDate,Status:Status}'`. Backups on every stateful resource **and** a record of a restore test within 12 months → `✓ verified`. The record is an AWS Backup restore job with status `COMPLETED` (`aws backup list-restore-jobs-by-protected-resource --resource-arn {arn} --query 'RestoreJobs[].{Status:Status,Created:CreationDate}'`; docs: https://docs.aws.amazon.com/aws-backup/latest/APIReference/API_ListRestoreJobsByProtectedResource.html), or a ticket / runbook run log the operator opens and cites. A restore-test date the operator only states stays `◐` (attestation is not allowed for this item). Backups confirmed but restore untested → `◐` with note. A stateful resource without backups → `✗` (or `✗ conflict` if the interview claimed it). A stateful resource type with no check listed here (S3, EFS, EBS, ElastiCache, …) is `?` for that resource, never counted as backed up; find its API in the documentation (`docs: <URL>`).
- **Kubernetes:** data on PersistentVolumes — the backing volume's backup by the AWS checks above, or the cluster's snapshot or backup objects (e.g. `VolumeSnapshot`, which exists only where the CSI snapshot CRDs and controller are installed, or the backup tool's schedule and backup objects), cited as queries. Same restore-record rule.
- **Evidence:** interview Section 10; verification result.

### Item 25 — DR plan exists

- **Auto-mark rule:** RTO + RPO + DR runbook path → `◐`. The plan's regions/mechanisms are consistent with the Cross-Region Footprint and backup configuration (e.g. "active-passive to us-west-2" needs resources or replicated backups in us-west-2) → `✓ verified`; inconsistent → `✗ conflict`. Explicit "no DR plan" → `✗`. Partial → `?`.
- **Evidence:** interview Section 10; runtime-profile Cross-Region Footprint; item 24 result.

---

## Notes for the skill at runtime

1. **Evidence citations are mandatory.** Every mark in `readiness-scorecard.md` carries `[evidence: <path>:<line>]` where a line exists, else `[evidence: <path>#<heading>]`, or `[query: <command> @ <timestamp>]` for verification results, and `[docs: <URL> @ <date read>]` where the mark rests on what a metric or setting means. Attested items carry `[attested: <one-line operator note>]`.
2. **Unknown is the default.** Missing or ambiguous evidence → `?`. Presence of an answer → at most `◐`.
3. **Operator override log.** Every manual mark or override is appended to the "Manual override log" with timestamp, old mark, new mark and reason. An override that clears a `✗`, `✗ conflict` or `◐` needs the cited artifact or query that resolves it; a reason alone never does.
4. **Optional extras.** If `extra-checklist.md` exists in the run's handoff directory, its items are merged into an "Operator-supplied extras" section and use the same evidence classes. Extras are counted by the same verdict rule.
