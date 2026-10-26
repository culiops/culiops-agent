# DRY-RUN-NOTES — query-failure fixture

## Gate transitions

### GATE 1 - Scope confirmation
- Report: `acme-prod-waste-mixed-20260528-1200.md`; 3 items, $240/mo total.
- Items (prioritized by savings): bucket-logs-2019 ($180), vol-0cccc1 ($35), prod-old-lb ($25).
- Target: account 123456789012, region ap-southeast-1. No catalog. **No IaC repo supplied** ("none - ownership from tags only"), so every owner will resolve to `unknown`.
- **Operator approves.**

### GATE 2 - Verification batch approval
- Query 0: `0a` target check, `0b-1..3` ownership probes (S3 tagging, `describe-volumes`, ELB `describe-tags`).
- Item #1 (`delete-s3-bucket.md`): location, versioning + lifecycle, request-metrics configuration, bucket logging, event data stores, **CloudTrail Lake `StartQuery` / `GetQueryResults` (conditional: used only if neither request metrics nor access logs cover the window; billed per GB scanned, itemized)**, size metrics, policy, replication, log-target sweep, DNS sweep.
- Item #2 (`delete-unattached-ebs.md`): describe-snapshots, attach/detach history (`lookup-events`, management events), Recycle Bin rules.
- Item #3 (`delete-unused-load-balancer.md`): describe, listeners, targets, ALB metrics, Route53 / CloudFront / Global Accelerator sweeps.
- IAM list shown includes `cloudtrail:StartQuery`, `cloudtrail:GetQueryResults`. **Operator approves WITHOUT pre-checking their own IAM** - a realistic flow; the skill lists permissions but does not simulate them.

### Step 3 - Execute verification (FAILS here)
- `0a` ok: account = `Scope`. `0b-1..3` ok.
- Rows 1-5 for item #1 ok: bucket location; no versioning, no lifecycle; no request-metrics configuration (3a unavailable); no server access logging (3b unavailable); event data store `org-data-events` exists and captures S3 data events (3c is the only source left).
- Row 6: `cloudtrail:StartQuery` -> **`AccessDeniedException`. SKILL STOPS.**

### Steps 4, 5 and GATE 3 - NEVER REACHED
- No triage, no plan file, no GATE 3.

---

## What this fixture validates

- **Constraint 8 (stop on query failure):** the batch stops, the failure is surfaced with reason, required permission and remedies. No partial plan.
- **A denial on a query the playbooks really use:** `cloudtrail:StartQuery` is the one billed, non-Get/Describe/List read allowed by Law 1. (An earlier version denied `cloudtrail:LookupEvents` for an S3 bucket, a query that no longer exists in the S3 playbook.)
- **Law 3 / Constraint 4:** a failed query does not become an unobserved signal and no item is promoted to a tier on partial evidence; items #2 and #3 are not tiered just because their ownership probes succeeded.
- **Actionable operator guidance:** three concrete paths (grant permission, trim the item, investigate SCP / boundary).
- **Mock completeness:** `mock-responses/` holds exactly the queries that ran, with the failure last; none for the unreached playbook queries.

---

## Acceptance check

A reviewer confirms:

- **(a)** `expected-output.md` is an error message (not a plan) that names the failing query (#6), the affected item (#1), the required permission and the AWS error string.
- **(b)** No `.culiops/cost-optimize-plan/` plan file would be written in a real run.
- **(c)** The successful rows (0a, 0b-1..3, 1-5) are NOT incorporated into a partial plan; they are discarded on abort.
- **(d)** The suggested-next-actions list gives three remediation paths.
- **(e)** `mock-responses/` contains exactly: `sts-get-caller-identity`, the three ownership-probe mocks (`get-bucket-tagging-…`, `describe-volumes-…`, `describe-tags-…`), rows 1-5 for the bucket, and `start-query-bucket-logs-2019-denied.json` (the error). Nothing for unreached queries.
