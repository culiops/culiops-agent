# Dry-run notes — verification-fail

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides the path to the upstream report. Skill loads `upstream-report.md`, extracts the 1-item Remediation list, reads `**Cloud:** aws` and `**Scope:** 123456789012 / acme-prod`; target = account 123456789012, region ap-southeast-1. Report is fresh. $5/mo floor: the item passes ($400). No catalog. Operator supplies the IaC repo path (`~/acme-infra`, simulated). Approved.

2. **GATE 2 (Verification batch)** — Playbook `examples/aws/delete-s3-bucket.md`. Batch: Query 0 (`0a` target check, `0b` ownership probe) then the playbook queries: location, versioning + lifecycle, the activity-source discovery (request-metrics configuration, then bucket logging with the access-log read, CloudTrail Lake only if neither covers the window), size/object metrics, policy, replication, log-target sweep, DNS sweep. The optional IAM principal sweep is offered and declined. Itemized cost: the access-log read (about 90 LIST + 3,800 GET) at per-request S3 pricing; no CloudTrail Lake scan is planned because it is conditional on the earlier sources. Operator approves. Per Step 2, each item's playbook queries are listed as conditional on Query 0b; here no owner routes to ❔, so none is skipped.

3. **Step 3 (Execute)** — `0a` first: account = `Scope`. Then all queries succeed (mocks). Activity: no request-metrics configuration (row 3) → source 3b: the bucket has server access logging into a readable log bucket → the access-log summary shows 3,694 GETs in 90d, 1,247 in the last 30d, daily 31-52, last 2026-05-27 14:32 UTC, all `lambda-export-fn`. `lookup-events` is never used for S3 object activity.

4. **Step 4 (Triage)** — Required activity row triggered (recurring, recent) → Evidence **🚫**. Tier rule 1 fires first → **🚫 Do not act**. Other dimensions are not scored.

5. **GATE 3 (Plan review)** — Operator agrees with the 🚫 placement; approves. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260528-1022.md`, uncommitted.

## What this fixture validates

- **A real data-event source for S3 activity.** Server access logs (source 3b), not `lookup-events`. The earlier version of this fixture mocked `GetObject` events from LookupEvents, which can never happen. Same verdict, now on a signal that exists.
- **Source fall-through order:** request metrics (none) → access logs (available) → CloudTrail Lake (not needed, not run, not billed).
- **Skill resists the upstream recommendation** when evidence contradicts a `high`-confidence delete; the item is NOT silently dropped.
- **Temporal distribution read:** steady daily reads for 90d are active use, not one burst (Principle 3).
- **Attachment kept out of Evidence** (Principle 1): the IAM role read policy in IaC is noted as corroboration only.
- **Zero-actionable plan renders** with every actionable tier "No items in this tier." and `$0/mo` total.
- **Secrets / privacy rule:** log rows, requester IPs and object keys are summarized, never recorded.

## Acceptance check

A reviewer walks the mocks and confirms: (a) `access-log-summary-bucket-logs-active.json` is the only source of S3 object activity and no `lookup-events` mock exists for the bucket; (b) the item lands in 🚫 with the counts, last-GET timestamp and principal quoted and `live:4` cited; (c) all other actionable tiers are empty and the 🚫 count is 1; (d) the item is neither absent nor in any other tier; (e) header has `Target` and `IaC repo(s)`, and rows `0a` / `0b` exist.

> **Mock convention:** `access-log-summary-*.json` holds a summarized result of reading ~3,800 log objects (counts, distribution, requester) — a fixture convention, since reproducing thousands of log rows adds nothing and the Secrets rule forbids recording them.
