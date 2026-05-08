# Dry-run of `cloud-cost-investigate` against `anomaly-aws-bill-spike`

Expected skill behaviour at each step. Recorded for pre-dry-run reference; "Gaps surfaced" and "Fixes applied" are filled in during the actual dry-run.

## Step 1 — Detect & Scope

- Reads `operator-question.md`. Heuristic: "spiked / why" → anomaly mode (suggested).
- Detects AWS via `~/.aws/` (simulated for fixture).
- Scope: single account `123456789012`. Time range: last 30d vs. previous 30d.
- Catalog lookup: none found.
- Presents scoping summary and asks for confirmation.

**GATE 1:** operator confirms.

## Step 2A — Anomaly mode query plan

Skill proposes 4 queries:
1. `ce:GetCostAndUsage` — daily by service for last 30d. ($0.01)
2. `ce:GetCostAndUsage` — drill-by `USAGE_TYPE` filtered to top-delta service from query 1. ($0.01)
3. `ce:GetCostAndUsage` — same as 2 but for the previous 30d window. ($0.01)
4. `ec2:DescribeInstances` — filtered to launches within last 30d. ($0)

Total estimated API cost: $0.03.
IAM: `ce:GetCostAndUsage`, `ec2:DescribeInstances`.

**GATE 2:** operator approves.

## Step 3 — Execute

- Queries 1-3 return the synthetic billing data (`billing-data.json`).
- Query 4 returns the synthetic instance list (`new-resources.json`).

## Step 4 — Anomaly analysis

- Period delta: $74K - $52K = +$22K.
- By-service delta: EC2 +$22K (99% of delta), all other services flat.
- Drill: `BoxUsage:p3.8xlarge` is +$20K of the +$22K within EC2.
- New resources: 8 `p3.8xlarge` instances launched 12 days ago, all in `us-east-1`, all untagged.
- Ranked driver: 1 entry — "8 untagged p3.8xlarge instances in us-east-1 launched 2026-04-26", absolute delta ~$20K, evidence: instance IDs.

## Drill-down decision

- No additional queries needed; the new-resource query already covered it.
- Skill skips GATE 3 and proceeds to report.

## Step 5 — Compose report

- Writes draft to `.culiops/cloud-cost-investigate/123456789012-anomaly-2026-05-08-1432.md`.
- Findings section names the driver with full evidence.
- Remediation list (anomaly mode produces informational items, not deletes):
  | # | Action | Resource(s) | Est. savings | Source | Confidence | Evidence |
  |---|--------|-------------|--------------|--------|------------|----------|
  | 1 | Tag 8 untagged p3.8xlarge instances with `Service` and `Owner` | `i-aaa, i-bbb, ...` | n/a (visibility only) | line-item-computation | high | tag absence in describe-instances output |
  | 2 | Confirm with ML team that 8 instances are still needed | same | up to $20K/mo if shut down | line-item-computation | low (depends on team need) | running 24/7 since 2026-04-26 |
- Total estimated savings: $0/mo high-confidence; up to $20K/mo low-confidence pending team confirmation.
- Gaps: utilization metrics not fetched (operator declined drill-down — none was offered, all queries already covered the question).

**GATE 4:** operator approves the report; skill commits to `.culiops/cloud-cost-investigate/`.

## Gaps surfaced

(filled during actual dry-run)

## Fixes applied

(filled during actual dry-run)
