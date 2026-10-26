# Dry-run notes — window-and-tier-check

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides the upstream report path and asks for Principle 3 + 🔵 handling. Skill loads `upstream-report.md`, extracts 2 items, reads `**Cloud:** aws`, `**Scope:** 123456789012 / acme-prod`, `**Date:** 2026-07-09 09:00`. Target = account 123456789012, region ap-southeast-1. **Freshness:** same-day → no warning. $5/mo floor: both pass. No catalog. Operator supplies the IaC repo (`~/acme-infra`, simulated). Approved.

2. **Step 2 (Plan verification batch)** — Playbooks: item #1 → `delete-s3-bucket.md`; item #2 → `delete-kinesis-stream.md`. Both upstream items were flagged on 14d and are deletes, so per **Principle 3** the skill re-verifies over the **90d delete band** (60-180d allowed), not the upstream 14d. The S3 activity source is chosen by availability: the batch includes the discovery calls (request-metrics configuration, bucket logging, event data stores) and the CloudTrail Lake query as the conditional last source, itemized as billed per GB scanned. The Kinesis playbook's optional write-throttle query is offered and the operator opts in (declining would not block Evidence 🟢; it would only be listed in Gaps). GATE 2 approved. Per Step 2, each item's playbook queries are listed as conditional on Query 0b; here no owner routes to ❔, so none is skipped.

3. **Step 3 (Execute)** — `0a` target check passes. `0b` for both items: owner terraform for each (neither routes to ❔). Item #1 activity: no request metrics (row 3), no access logging (row 4), event data store `org-data-events` exists and captures S3 data events (row 5) → Lake query (row 6): **214 GetObject across 13/13 weekly buckets, last 2026-07-08**. Item #2: 90d hourly `get-metric-data` (one call) → all zero; the optional write-throttle query, opted in at GATE 2, is also zero; consumers and mapping found (attachment).

4. **Step 4 (Triage)** — rules in order, first match wins:
   - **#1:** required activity row triggered by a recurring pattern → Evidence **🚫** → rule 1 → **🚫 Do not act**. The upstream 14d "no request charges" was a window-too-short proxy.
   - **#2:** Rev 🔴 (re-create yields a new ARN), Blast 🟡 (2 EFO + 1 mapping), Evidence **🟢** (all three required rows = 0 over 90d hourly, no burst, and the optional throttle row that ran = 0, so no run row is ⚪; attachment is NOT scored here, Principle 1), Dep 🟡 (`code:kinesis.tf:19`, `code:lambda.tf:55`; the second consumer is not in IaC). Rule 1 no. **Rule 2: Evidence 🟢 AND idle-ambiguous AND delete → 🔵.** Rule 2 precedes rule 3, so Reversibility 🔴 does not reroute it.
   - Dev-note emitted at `.culiops/cost-optimize-plan/dev-notes/orders-ingest.md`.

5. **GATE 3 (Plan review)** — Plan drafted with the 🔵 row between 🟡 and 🔴 in the summary. Operator approves. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260709-0912.md`, dev-note alongside, both uncommitted.

## What this fixture validates

- **Principle 3 window scaling flips a delete** — evidence from a window sized to the action, from a source that can actually observe it.
- **Evidence source honesty:** S3 object activity from CloudTrail Lake (existing store), never `lookup-events`; if no store existed the signal would be ⚪ and the item 🔴 (recorded in Gaps).
- **🔵 tier + dev-note** (rule 2, idle-ambiguous class, artifact template).
- **Attachment stays out of Evidence (Principle 1)**, yet is what makes the stream idle-ambiguous (a separate, explicit tier-routing input).
- **Temporal-distribution reasoning:** steady events = active; flat zero = idle.
- **Freshness gate no-op path.**

## Acceptance check

A reviewer confirms: (a) item #1 lands in 🚫 because the 90d Lake query (214 `GetObject`, steady) overrides the upstream 14d proxy, naming Principle 3 and citing `live:6`; (b) item #2 lands in 🔵 with Evidence scored 🟢 and the EFO / Lambda attachments scored into Blast and Dependency, and the dev-note is emitted with the single owner question and the reversible fallback; (c) the plan summary has the 🔵 row between 🟡 and 🔴; (d) no item claims actionable savings: $0/mo now, $180/mo pending confirmation; (e) no `lookup-events` mock exists for the bucket; (f) header has `Target` / `IaC repo(s)` and rows `0a`, `0b-1`, `0b-2`.
