---
name: cost-optimize-plan
description: Use when the operator wants to turn a cloud-cost-investigate report into an actionable, tiered execution plan. Triggers include phrases like "triage the cost report", "which of these cost recommendations are safe to act on", "plan the rollout for these savings", "build an action plan from the waste audit". Read-only; produces a four-tier plan (fast-win / coordinated / risky / do-not-act) with per-action safety verification evidence and rollback notes. Sits between cloud-cost-investigate (input) and iac-change-execution (downstream). v1 supports AWS only — GCP / Azure / Kubernetes playbooks deferred to v1.1+.
---

# Cost Optimize Plan

Given a `cloud-cost-investigate` report, run a read-only per-action verification pass, triage each remediation across four dimensions (reversibility, blast radius, evidence of no-use, dependency footprint), and produce a tiered execution plan. Strict read-only Iron Law; per-batch operator approval for verification queries; no handoff to execution — operator drives `iac-change-execution` manually with the plan.

## The Iron Law

```
NO MUTATIONS. EVER.
NO VERIFICATION QUERIES WITHOUT OPERATOR APPROVAL.
NO TIER ASSIGNMENT WITHOUT EVIDENCE.
NO HANDOFF TO EXECUTION — OPERATOR DRIVES.
```

- **Law 1: Read-only.** Cost APIs, resource-state APIs, metrics APIs, access-log queries only. No `delete` / `terminate` / `update` / `tag` — not even "harmless" ones.
- **Law 2: Per-batch verification approval.** All verification queries for the report are planned together, itemized with IAM perms + per-query API cost, and approved as one batch before any run.
- **Law 3: Every tier assignment carries evidence.** No item lands in 🟢 or 🚫 without a labelled signal — the verification result row points at the specific query and its output. Same discipline as `cloud-cost-investigate`'s source-labelled savings.
- **Law 4: Skill stops at the plan.** Even when an item is 🟢 Fast win and the operator says "just run it" — the skill refuses. Operator opens `iac-change-execution` separately. Avoids skipping the per-change `pre-flight` gate.

## Constraints (Non-Negotiable)

1. **Read-only.** No mutations of any kind.
2. **Per-batch query approval.** All verification queries pass GATE 2 as a single batch with IAM + cost itemization. No silent extensions.
3. **No playbook → manual review.** Items whose `(cloud, action-type, resource-type)` has no `examples/<cloud>/<action>.md` playbook are marked `manual-review-required` and parked in a dedicated section of the plan. Skill never invents a verification strategy on the fly.
4. **Evidence required for every tier.** No 🟢 / 🚫 without a verification signal. If a query failed, the item stays in 🔴 with `verification-incomplete` evidence — never silently promoted.
5. **Single report per run.** Skill runs against one `cloud-cost-investigate` report at a time. Combining reports across accounts / time ranges is out of scope.
6. **Catalog re-use, not re-fetch.** Service-discovery catalog is consulted (if present) for dependency lookup — never re-discovered.
7. **Output: `.culiops/cost-optimize-plan/<scope-slug>-<YYYYMMDD-HHmm>.md`.** Scope-slug matches the upstream report's slug, so plan files line up next to the investigation they triage.
8. **Stop on query failure.** Auth errors, rate limits, throttling halt the run and surface to operator. The skill does not silently skip and produce a partial plan disguised as complete.
9. **No re-evaluation of savings.** Upstream report's savings/source/confidence are copied verbatim into the plan. This skill adds safety/triage columns alongside.
10. **No handoff automation.** Plan ends at GATE 3 commit. Even a single fast-win item does not trigger `iac-change-execution` automatically.

## Rationalization Prevention

| Thought | Reality |
|---------|---------|
| "Item is obviously safe, I'll skip its verification query" | STOP — every actionable item gets verification. |
| "No playbook, but I know what to check for this type" | STOP — mark `manual-review-required`. Codify the playbook first, then ship. |
| "Verification failed for that one query, but the others passed — call it 🟢" | STOP — incomplete evidence = 🔴, not 🟢. |
| "Operator wants to chain straight into iac-change-execution" | STOP — plan terminus is the gate. |
| "Upstream report's savings number looks wrong, I'll recompute" | STOP — that's `cloud-cost-investigate`'s job. Flag and stop. |
| "Operator says they know that S3 bucket is dead, skip the CloudTrail check" | STOP — operator certainty is not evidence. Run the query or park as manual-review-required. |
| "Catalog is missing for this account — score Dependency dimension as 🟢 (no consumers found = no consumers exist)" | STOP — missing catalog ≠ no dependencies. Score as ⚪ and bump tier conservatively. |

## Red Flags — STOP and Follow Process

| Red Flag | What to Do |
|----------|------------|
| About to call any non-`Get`/`Describe`/`List`/`Lookup`/`Simulate` API | STOP — read-only. The skill never calls write APIs. |
| Upstream report has no `Remediation list` table | STOP — abort at GATE 1 with `report-format-invalid`. |
| An item's `(cloud, action, resource_type)` has no matching playbook in `examples/<cloud>/` | Park in `❔ Manual review required` section. Do NOT invent verification queries. |
| Verification query returns rate-limited / throttled | STOP the batch; surface to operator. No partial plan. |
| Operator says "skip verification on item #N — I know it's safe" | STOP — verification is per-batch and applies to all actionable items. Operator can drop the item from scope, not skip its verification. |
| 🚫 Tier triggered (evidence of use found) | Item stays in plan but in `🚫 Do not act` section. Do NOT silently drop. |
| Upstream report's savings number looks wrong | STOP — out of scope. Flag in `Gaps` section and continue. |
| Operator asks to chain directly into `iac-change-execution` | STOP — plan terminus is GATE 3. Operator opens execution skill manually. |
| Multi-cloud upstream report (multiple `**Cloud:**` headers) | STOP — abort at GATE 1 with `multi-cloud-report-unsupported`. |

## Workflow

Fixed pipeline with three operator gates. Mirrors `cloud-cost-investigate`'s shape (scope → batch → review) with one fewer gate — no drill-down loop because verification is a single batch by design.

```dot
digraph cost_optimize_plan {
    rankdir=TB;
    node [shape=box, style=rounded];

    input    [label="Input: path to\ncloud-cost-investigate report"];
    load     [label="Step 1: Load & Parse\n(extract remediation table,\ndetect cloud, apply floor)"];
    gate1    [label="GATE 1: Operator\nconfirms scope + floor", shape=diamond];
    plan_q   [label="Step 2: Plan Verification\nBatch (per-item playbook lookup,\ndedupe, IAM + cost itemized)"];
    gate2    [label="GATE 2: Operator\napproves verification batch", shape=diamond];
    exec     [label="Step 3: Execute Verification\n(read-only queries,\nstop on any failure)"];
    triage   [label="Step 4: Triage\n(score 4 dimensions, assign tier,\ndetect ordering hints)"];
    compose  [label="Step 5: Compose Plan\n(tier groups, evidence,\nrollback, gaps)"];
    gate3    [label="GATE 3: Operator\napproves plan\n(commit / revise)", shape=diamond];
    done     [label="Done", shape=doublecircle];

    input -> load;
    load -> gate1;
    gate1 -> plan_q    [label="approved"];
    gate1 -> load      [label="corrections"];
    plan_q -> gate2;
    gate2 -> exec      [label="approved"];
    gate2 -> plan_q    [label="trim / change floor"];
    exec -> triage;
    triage -> compose;
    compose -> gate3;
    gate3 -> compose   [label="revise"];
    gate3 -> done      [label="approved"];
}
```

### Step 1 — Load & Parse (shared)

Read the upstream report and establish scope.

1. Read upstream report file (operator provides path).
2. Parse the `## Remediation list (prioritized)` table → list of items.
3. Read header for `**Cloud:**` (single-cloud required), `**Scope:**`, time-range, mode.
4. Look up catalog: `.culiops/service-discovery/` directory (optional). If present, parse for dependency lookup later.
5. Apply optional savings floor (default $5/mo, matching upstream). Items below the floor go to a "filtered (below floor)" appendix in the plan.
6. Present scoping summary to operator (see GATE 1 below).

### GATE 1 — Scope

Operator confirms or corrects.

> **Cost optimization plan scoping summary:**
>
> **Upstream report:** `<path>`
> **Mode:** waste | anomaly | attribution (from upstream)
> **Cloud:** aws (single — mixed-cloud upstream reports are unsupported and abort with `multi-cloud-report-unsupported`)
> **Scope:** `<account/subscription/project/cluster>`
> **Time range:** `<from> → <to>`
> **Catalog:** `<.culiops/service-discovery/ path or 'none — Dimension 4 conservative scoring'>`
> **Items considered:** N (above $X/mo floor) / M filtered (below floor)
>
> **Confirm to proceed to verification planning.**

### Step 2 — Plan Verification Batch

For each item, look up playbook by `(cloud, action, resource_type)`. Derive `action` from the upstream remediation's verb (e.g., "Delete unattached EBS volume" → action=delete) and `resource_type` from resource ID format (e.g., `vol-*` → ebs-volume).

Items with no matching playbook go to `manual-review-required` queue (skipped from the batch, surfaced in final plan).

For items with a matching playbook: collect required queries, dedupe across items (e.g., shared route53 sweep), aggregate IAM perms list, sum estimated API costs.

Present batch as:

| # | Item | API | Scope | IAM | Est. cost | Why |
|---|------|-----|-------|-----|-----------|-----|
| 1 | Delete vol-xxxxx | ec2:DescribeVolumes | vol-xxxxx | ec2:Describe* | $0 | confirm state=available, age |
| 2 | Delete logs-2019 | cloudtrail:LookupEvents | logs-2019, 90d | cloudtrail:LookupEvents | $1.20 | confirm no GetObject/PutObject |
| ... | ... | ... | ... | ... | ... | ... |

Plus footer with total API cost, consolidated IAM perms list, manual-review count.

### GATE 2 — Verification batch

Operator approves, trims (drops specific queries or items), or changes the savings floor (loops back to Step 1).

If batch is empty (e.g., all items routed to manual-review), skill skips Step 3 and goes straight to compose-plan with a manual-review-only output. Note: this case is non-zero — fixture `no-playbook` exercises it.

### Step 3 — Execute Verification (shared mechanics)

Run the approved batch. Each query's raw output captured for the plan's `## Verification queries run` section. If a query fails (auth, rate limit, service unavailable), skill stops and reports — does NOT silently skip and does NOT auto-retry. Surfaces to operator with the failure reason and a suggested fix (e.g., "grant `cloudtrail:LookupEvents` and re-run, or trim item #N from batch").

### Step 4 — Triage

For each item, score the 4 dimensions per the rules in `## Triage Model` (Section to be added in Task 8 — at this point, the reader will see a forward reference; acceptable). Tier assignment is deterministic (no LLM judgment in the rule).

Detect ordering hints mechanically:
- **Snapshot-before-delete:** if an item is a delete-EBS or delete-EC2 and playbook recommends snapshotting first, emit a hint.
- **Same-resource conflict:** if two items target the same resource, emit "do #X before #Y".
- **Catalog dependency edges:** if item N deletes resource R, and another item M operates on a resource depending on R per catalog, emit "do #M before #N".

### Step 5 — Compose Plan

Render the markdown using the output template (Section "Output Format" to be added in Task 8). Write to `.culiops/cost-optimize-plan/<scope-slug>-<YYYYMMDD-HHmm>.md` only AFTER GATE 3 approval.

### GATE 3 — Plan review

Operator reviews drafted plan, approves to commit, or requests revisions (e.g., "bump item #5 from 🟡 to 🔴 — that EIP is allowlisted in our partner's firewall, recreating loses the IP"). On approve, skill commits the plan file (only the plan — no other changes).

## Triage Model

Four dimensions per item. Each scores 🟢 / 🟡 / 🔴 / ⚪ (unknown). Tier assignment is a deterministic rule over the four scores — no LLM judgment in the rule, only in interpreting evidence against thresholds.

### Dimension 1 — Reversibility *(from playbook + IaC context)*

| Score | Condition |
|-------|-----------|
| 🟢 | Reversible config change (resize down, lifecycle policy add, tag add). Undone by re-applying old IaC. |
| 🟡 | Recoverable within retention window (snapshotted delete, versioned bucket delete with versioning history). |
| 🔴 | Irreversible (un-versioned delete, NAT GW destroy, schema drop, key rotation). |

Source: playbook's `Reversibility classification` section. Hardcoded in the playbook, not LLM-inferred.

### Dimension 2 — Blast radius *(from IaC + catalog if present)*

| Score | Condition |
|-------|-----------|
| 🟢 | Single resource, no shared-namespace impact. |
| 🟡 | Touches a shared name (S3 bucket name, DNS, IAM role), or referenced by ≤1 other resource. |
| 🔴 | Referenced by ≥2 other resources, or touches load balancer / VPC / shared DB / DNS zone. |
| ⚪ | No catalog and resource type unclear — score as if 🟡 (conservative). |

Source: playbook's `Blast radius classification` default, optionally widened by catalog lookup.

### Dimension 3 — Evidence of no-use *(from verification queries — the heart of this skill)*

| Score | Condition |
|-------|-----------|
| 🟢 | All `🟢 Threshold` rows from the playbook's evidence table pass. |
| 🟡 | Some thresholds pass, some return ⚪ unknown (query rate-limited, IAM denied, data missing). No 🚫 triggers. |
| 🚫 | Any `🚫 Trigger` row matched — evidence of active use found. |
| ⚪ | Verification queries failed entirely (auth error, throttling). |

Only dimension that can independently force 🚫.

### Dimension 4 — Dependency footprint *(from catalog if present, IaC otherwise)*

| Score | Condition |
|-------|-----------|
| 🟢 | No catalog references; not referenced by IaC `data` blocks elsewhere. |
| 🟡 | Referenced by 1–2 IaC consumers or 1 catalog entry. |
| 🔴 | Referenced by ≥3 IaC consumers or marked critical-path in catalog. |
| ⚪ | No catalog and no IaC scan possible. |

Source: `grep` over IaC tree for resource name/ARN/ID; catalog lookup if `.culiops/service-discovery/` exists.

### Tier assignment rules

Apply in order — first match wins:

1. **🚫 Do not act** ← Evidence is 🚫.
2. **🔴 Risky** ← Reversibility is 🔴 OR Blast radius is 🔴 OR Dependency is 🔴 OR Evidence is ⚪. (Note: ⚪ on Reversibility / Blast / Dependency is treated as 🟡-equivalent — does not force 🔴. Only ⚪ on Evidence triggers 🔴.)
3. **🟡 Coordinated** ← any dimension is 🟡 (including ⚪ on Dimensions 1, 2, or 4), no 🔴 / 🚫 / Evidence-⚪ anywhere.
4. **🟢 Fast win** ← all four dimensions 🟢.

### Worked examples

| Item | Reversibility | Blast | Evidence | Dependency | → Tier |
|------|---------------|-------|----------|------------|--------|
| Delete vol-xxx unattached EBS, $48/mo | 🔴 irreversible | 🟢 | 🟢 detached 90d | 🟢 | **🔴 Risky** (irreversible) |
| Add lifecycle policy on logs-bucket, $200/mo | 🟢 reversible | 🟢 | 🟢 (policy-only) | 🟢 | **🟢 Fast win** |
| Delete S3 bucket logs-2019, $400/mo | 🔴 | 🟡 namespace | 🟢 0 events 90d | 🟢 | **🔴 Risky** |
| Same, but CloudTrail shows 1247 GetObject in 30d | 🔴 | 🟡 | 🚫 | 🟢 | **🚫 Do not act** |
| Rightsize prod-api m5.4xl → m5.2xl, $280/mo | 🟢 | 🟡 ALB target | 🟢 CPU 4% 14d | 🟡 1 consumer | **🟡 Coordinated** |

### Ordering hints

Detected mechanically, not LLM-inferred:

- **Snapshot-before-delete:** If item N is `delete <resource>` and playbook recommends snapshotting → emit "do snapshot step before #N" as callout. Not a hard sequence.
- **Same-resource-conflict:** If two items target the same resource → emit "do #X before #Y" to avoid second invalidating first.
- **Catalog-dependency edges:** If item N deletes resource R, and item M operates on a resource that depends on R per catalog → "do #M before #N".

Within a tier, sort by savings $ descending.

## Output Format

Plan file: `.culiops/cost-optimize-plan/<scope-slug>-<YYYYMMDD-HHmm>.md`. Scope-slug matches the upstream report's slug, so investigation and plan sit next to each other in different `.culiops/` subdirs.

`````markdown
````markdown
**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/<...>.md
**Mode of upstream:** waste | anomaly | attribution
**Scope:** <account/subscription/project/cluster>
**Catalog used:** <path or 'none'>
**Date:** <YYYY-MM-DD HH:mm>
**Items considered:** <N>   **Savings floor:** $<X>/mo
**Cloud:** <aws|gcp|azure|kubernetes>

## Scoping decisions
<what was confirmed at GATE 1>

## Verification queries run
| # | Item | API | IAM | Status | Evidence captured |
|---|------|-----|-----|--------|-------------------|
| 1 | Delete vol-xxxxx | ec2:DescribeVolumes | ec2:Describe* | ok | state=available since 2026-02-14 |
| 2 | Delete logs-2019 | cloudtrail:LookupEvents | cloudtrail:LookupEvents | ok | 0 GetObject in 90d |

## Plan summary
| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 3 | $312/mo |
| 🟡 Coordinated | 5 | $1,840/mo |
| 🔴 Risky | 2 | $448/mo |
| 🚫 Do not act | 1 | ($400/mo — evidence of use) |
| ❔ Manual review | 4 | $260/mo |

## 🟢 Fast wins
| # | Action | Resource | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|---------|---------------|-------|----------|------------|--------|----------|
| 1 | Add lifecycle policy 90→Glacier | logs-bucket-app | $200/mo | 🟢 | 🟢 | 🟢 | 🟢 | gcp-recommender (high) | Remove policy via IaC revert |

> Ordering hint: none — items independent.

## 🟡 Coordinated
| # | Action | Resource | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|---------|---------------|-------|----------|------------|--------|----------|
| 4 | Rightsize prod-api m5.4xl→m5.2xl | i-yyyyy | $280/mo | 🟢 | 🟡 ALB target | 🟢 CPU 4% 14d | 🟡 1 consumer | compute-optimizer (medium) | Re-apply old IaC |

> Ordering hint: do #4 outside peak hours (catalog: peak = 14:00–16:00 UTC).

## 🔴 Risky
| # | Action | Resource | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|---------|---------------|-------|----------|------------|--------|----------|
| 9 | Delete vol-xxxxx unattached EBS | vol-xxxxx | $48/mo | 🔴 | 🟢 | 🟢 detached 90d | 🟢 | line-item (high) | Snapshot first; restore from snapshot |
| 10 | Delete bucket logs-2019 | logs-2019 | $400/mo | 🔴 | 🟡 namespace | 🟢 0 events 90d | 🟢 | line-item (high) | None — versioning not enabled |

> Ordering hint: take snapshot before #9.

## 🚫 Do not act
| # | Action | Resource | Savings claimed | Disqualifying evidence |
|---|--------|----------|-----------------|------------------------|
| 11 | Delete bucket logs-active | logs-active | $400/mo | cloudtrail:LookupEvents → 1,247 GetObject in last 30d (last: 2026-05-27 14:32 UTC) |

## ❔ Manual review required (no playbook in v1)
| # | Action | Resource | Savings | Source | Confidence | Reason |
|---|--------|----------|---------|--------|------------|--------|
| 14 | Delete Lambda fn idle-worker | idle-worker | $35/mo | gcp-recommender | medium | No `delete-lambda` playbook in v1 |

## Gaps
- Verification query #7 failed (IAM denied iam:SimulatePrincipalPolicy for logs-2019). Dimension 4 scored ⚪. Operator may grant the perm and re-run.

## Next steps (informational)
- Operator picks an item, opens `iac-change-execution`, references this plan path + item #.
- iac-change-execution will write the IaC, then call pre-flight for full risk clearance before apply.
- Manual review items: triage by hand or wait for v1.1 playbooks.
````
`````
