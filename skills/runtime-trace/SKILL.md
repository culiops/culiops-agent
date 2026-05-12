---
name: runtime-trace
description: Use when the user wants to build a runtime profile of an AWS service — what's actually billing, who's actually calling it, what its activity baseline looks like, and where it actually lives across regions. Triggers include "runtime profile <service>", "trace runtime for <service>", "what's actually running for <service>". Useful for service takeovers (no docs, no IaC), drift checks after a previous discovery, post-incident retrospectives, and pre-cost-optimization baselining. Read-only; queries Cost Explorer, CloudTrail LookupEvents, CloudWatch GetMetricData, and Resource Explorer. AWS only in v1.
---

# Runtime Trace

Produce a self-contained runtime profile of an AWS service by querying four cheap, read-only data sources — **Cost Explorer** (the spend oracle), **CloudTrail LookupEvents** (the control-plane log), **CloudWatch GetMetricData** (activity baselines, targeted), and **Resource Explorer** (cross-region inventory) — and writing the result to `.culiops/runtime-trace/<service>-runtime-profile.md` in the target repo. Six gates, hard cost cap of $1.00 per run, every claim traceable to an API call.

This skill answers four questions that infrastructure-as-code discovery cannot:

1. **What's actually billing?** (Cost Explorer reveals services and usage types diagrams omit.)
2. **Who's actually calling it?** (CloudTrail surfaces IAM principals, deploy events, cross-account access — last 90 days.)
3. **What does its activity look like?** (CloudWatch baselines for the four golden signals — traffic, latency, errors, saturation — over 14 days.)
4. **Where does it actually live?** (Resource Explorer finds tagged resources outside the assumed primary region.)

`runtime-trace` is a sibling to `service-discovery` (which catalogs resources from IaC or from live cloud APIs in real-discovery mode). It is **not** a cost-investigation tool (that's `cloud-cost-investigate`) and **not** an orchestrator — a future `service-takeover` skill will compose `service-discovery` + `runtime-trace` + interview/readiness steps into an end-to-end takeover workflow.

## References

The design draws on the following intellectual foundations. They are cited here so a future maintainer (or you, six months from now) understands the *why* behind the workflow.

| Reference | What it informs |
|---|---|
| **Observability Engineering** (Majors, Fong-Jones, Miranda) — Ch. 1–5, 8 | The "high-cardinality / slice-retroactively" framing. Justifies querying Cost Explorer and CloudTrail (queryable after-the-fact) instead of pre-built dashboards. |
| **Site Reliability Engineering** (Google) — Ch. 32 "The Evolving SRE Engagement Model" | Source of the service-takeover / Production Readiness Review pattern. Justifies the gate-driven workflow and the capability-detection-before-query step. |
| **Site Reliability Engineering** — Ch. 6 "Monitoring Distributed Systems" | Source of the four-golden-signals framing (traffic, latency, errors, saturation). Justifies the CloudWatch metric set per resource type. |
| **Working Effectively with Legacy Code** (Feathers) | "Characterization, not assumption" — prove what the system does before assuming what it should do. Justifies the "every claim cites its API call" discipline. |
| **The Pragmatic Programmer** (Hunt, Thomas) — "Tracer Bullets" chapter | Source-by-source gate model: thin end-to-end probe per source before fanning out. Justifies per-source approval at Gate 4. |
| **AWS Well-Architected Framework** — Operational Excellence pillar | Source of the readiness-question framing that downstream `service-takeover` will use. |

## The Iron Law

```
NO WRITE API CALLS. EVER.
ALL CLOUD QUERIES ARE READ-ONLY. NO EXCEPTIONS.
NO ASSUMPTIONS. IF UNCLEAR, ASK THE HUMAN.
EVERY QUERY APPROVED BEFORE EXECUTION (plan-approve-execute).

HARD COST CAP: $1.00 per run. Skill aborts before any query whose cumulative
cost estimate would exceed $1.00. Raising the cap requires documented operator
justification at Gate 3.

SOFT WARNING: $0.25 per run. When the running actual-cost total crosses $0.25,
skill pauses and asks the operator to confirm continuation. Normal runs (under
$0.05) never trigger this; legitimate larger runs proceed with one extra
confirmation.

COST ESTIMATE BEFORE EVERY API CALL — even free ones. Estimates appear in
the Gate 3 plan table; the running actual-cost total is updated between
Gate 4 source blocks. If actuals exceed estimate by >2x on any source,
skill pauses and asks the operator before continuing.

OUT-OF-SCOPE ACTIONS REQUIRE FIVE-FIELD APPROVAL. Any need that falls outside
the declared scope (enabling CloudTrail, broadening an IAM policy, running an
Athena scan, modifying any resource, invoking another skill) requires explicit
operator approval with WHAT / WHY / COST / BLAST RADIUS / ALTERNATIVES.
Verbal "yes" without seeing the five fields is not approval.
```

- Law 1 (no writes): every API call enumerated in this skill is read-only. If a feature would require a write API, that feature is out of scope.
- Law 2 (no assumptions): if a metric is missing, a CloudTrail event ambiguous, or a Cost Explorer line item unattributable, the output records "unknown" with the reason — never a guess.
- Law 3 (cost cap): $1.00 is calibrated against realistic worst-case (~$0.16 across all four sources). The cap catches bug/misconfig blast immediately while giving legitimate larger runs (e.g., 500 CloudWatch metrics) room to complete.
- Law 4 (out-of-scope approval): "five-field approval" means the operator sees a structured proposal with WHAT (the exact API call or human action), WHY (what gap motivates it), COST (estimated $ and time), BLAST RADIUS (read-only? account-wide? cross-account? reversible?), ALTERNATIVES (what we could do instead, including "skip and document the gap"). Verbal "yes" without seeing the five fields is not approval.

## Constraints (Non-Negotiable)

1. **The cloud APIs are the source of truth.** Every claim in the runtime profile must cite a specific API call, its parameters, and its timestamp. No outside-knowledge inference (e.g., "Lambda usually has X" without an actual `GetMetricData` response).
2. **No assumptions.** If a metric is missing, a CloudTrail event is ambiguous, or a Cost Explorer line item is unattributable, the doc records "unknown" with the reason — never a guess.
3. **Strict scope.** Resource Explorer is queried for the supplied scoping primitive only; CloudTrail is filtered by ResourceName or EventSource derived from the scoping primitive; CloudWatch is targeted at resources surfaced by Cost Explorer or supplied directly. No fan-out across the account.
4. **No secrets, ever.** The skill never reads secret-shaped values from any API response. CloudTrail events that include request parameters with secret-shaped fields (passwords, keys, tokens) have those fields redacted before being written to the audit trail.
5. **Read-only IAM only.** The reference policy ships in `examples/iam-policy-readonly.json` and contains zero write actions. If a feature would require a write action, that feature is out of scope.
6. **Resolve to a single, named scope.** A run targets one AWS account + one primary region + one scoping primitive. Multi-account or multi-region-primary runs require separate invocations.
7. **Operator confirmation at every gate.** Six workflow gates exist (Section "Workflow & Gates"). None are optional. No gate may be auto-confirmed.
8. **Out-of-scope actions require five-field approval.** See Iron Law.

## Rationalization Prevention

| Thought | Reality |
|---|---|
| "Cost Explorer queries are basically free, I don't need to estimate" | STOP — every API call is estimated, every estimate shown to the operator. |
| "I'll just enable Resource Explorer for them, it'll only take a moment" | STOP — enabling a service is a write action and out-of-scope. Five-field approval required. |
| "The operator already approved the plan, I can skip the per-source gate" | STOP — Gate 4 (per-source) is separate from Gate 3 (plan). Both required. |
| "This Athena scan would only cost a few dollars" | STOP — Tier 2 sources are out-of-scope. Five-field approval required even if cheap. |
| "I'll just retry the failed call, maybe it was transient" | STOP — failures stop the skill. No silent retries. Operator decides. |
| "The diagram says the service is in us-east-1, I'll only query that region" | STOP — Resource Explorer's cross-region pass exists precisely to catch this assumption. Run it. |
| "This CloudTrail event has a password in `requestParameters`, I'll include it" | STOP — redact secret-shaped fields before writing to the audit trail. |
| "The cost cap is $1.00, I'm at $0.95, the next call is only $0.05" | STOP — the cap is a hard tripwire. Abort and ask the operator to raise the cap with justification. |
| "We crossed $0.25 but nothing looks wrong, I'll skip the soft-warning pause" | STOP — soft warnings are confirmations, not optional. The operator's "continue" is the safety check. |
| "I'll infer this resource type's metrics from defaults" | STOP — only metrics declared in `examples/aws/<resource-type>.md` are queried. If a resource type isn't covered, record it as a gap. |
| "The plan said 60 metrics, but we found 12 more resources, I'll just add them" | STOP — adding queries beyond the approved plan requires a new Gate 3. Re-plan or skip. |

## Cost Guardrails

- **Hard cap: $1.00 per run.** Calibrated against the realistic worst case across all four sources (~$0.16). Catches bug/misconfig explosions immediately; gives legitimate larger runs (e.g., 500 CloudWatch metrics) room to complete.
- **Soft warning: $0.25 per run.** When the running actual-cost total crosses $0.25, skill pauses and asks the operator to confirm. Normal runs (under $0.05) never trigger.
- **Estimate before every API call.** Even free ones. The Gate 3 plan table shows estimated cost per row.
- **Tier 2 sources (Athena log scans on VPC Flow Logs, ALB access logs, CloudFront / WAF logs) are explicitly OUT OF SCOPE.** If demand emerges, build a separate `log-trace` skill — do not extend this skill.
- **"One API call" = one row in the cost table.** Pagination retries count separately.
- **Read-only does not mean free.** Cost Explorer charges $0.01 per API call. Operator approves the plan and acknowledges the dollar amount at Gate 3.

### Cost ceilings per source (theoretical worst case)

| Source | Per-call cost | Skill cap | Worst-case total |
|---|---|---|---|
| Cost Explorer | $0.01 | ≤10 calls/run (16 with optional dimensions) | $0.10–$0.16 |
| CloudTrail LookupEvents | free (management events) | — | $0.00 |
| CloudWatch GetMetricData | $0.01 / 1,000 metrics | 200 metrics/run | $0.002 |
| Resource Explorer | free | — | $0.00 |
| **Total worst case** | | | **~$0.16** |

## The Four Data Sources

### a. Cost Explorer — the spend oracle

- **APIs:** `ce:GetCostAndUsage` (primary), `ce:GetDimensionValues` (for value discovery), `ce:GetTags` (when tag scoping is supplied).
- **Query shape:** `GROUP BY DIMENSION=SERVICE` and `GROUP BY DIMENSION=USAGE_TYPE`, time range last 30 days, monthly granularity. Optional second pass with `GROUP BY TAG=<key>` when a tag scoping primitive is supplied.
- **Why:** Bills don't lie. Surfaces services that diagrams and tags omit. Catches stealth dependencies (NAT Gateway data transfer, KMS, Secrets Manager, Route 53 health checks, CloudWatch Logs ingest).
- **Cost:** $0.01 per API call. Skill budgets ≤10 calls per run → under $0.10 typical.
- **Output contribution:** "Spend share by service" table; "services billing but absent from diagram/catalog" callout.
- **Edge case:** Cost Explorer must be enabled in the account (free, but opt-in for new accounts). If disabled, skill stops at Gate 2 with a clear message.

### b. CloudTrail LookupEvents — the control-plane log

- **APIs:** `cloudtrail:LookupEvents` (primary), `cloudtrail:GetTrailStatus` and `cloudtrail:DescribeTrails` (for capability detection).
- **Query shape:** `LookupAttributes` filtered by `ResourceName` (when an ARN list is the scoping primitive) or `EventSource` (when service inventory is derived from source a). Time window: last 90 days (LookupEvents AWS-imposed max).
- **Why:** Reveals who actually touches this service — IAM principals (roles, users, federated identities), deploy events, cross-account access, recent config drift. Catches "the deploy goes through this CI role nobody mentioned."
- **Cost:** Free for management events, last 90 days. `LookupEvents` returns management events only — data events (e.g., S3 object-level reads, Lambda invokes) are not queryable via this API and are out of scope for v1.
- **Output contribution:** "Top API actions by event count" table; "principals touching this service" table (ARN, principal type, last-seen, event count); "notable change events" timeline; "principals not in any known runbook" callout.
- **Edge cases:**
  - CloudTrail logging disabled → source skipped, gap recorded in output.
  - 90-day cap is documented as an explicit limitation in the output doc. Anything older requires Athena over CloudTrail's S3 archive, which is out-of-scope (Tier 2).

### c. CloudWatch GetMetricData — the activity baseline (targeted)

- **APIs:** `cloudwatch:GetMetricData` (primary), `cloudwatch:ListMetrics` (for capability detection).
- **Query shape:** **targeted only** — runs only against resources surfaced by source (a) or supplied as scoping primitives. Per-resource metric sets defined in `examples/aws/<resource-type>.md` files. Time range: last 14 days hourly for headline charts, last 24 hours at 5-minute granularity for "current shape." Skill caps total metrics per run at 200.
- **Per-resource metric sets (v1 coverage; extensible):** see `examples/aws/lambda.md`, `examples/aws/ecs-service.md`, `examples/aws/alb.md`, `examples/aws/rds-instance.md`, `examples/aws/sqs-queue.md`, `examples/aws/apigw-rest.md`.
- **Why:** Four-golden-signals visibility per resource. Identifies idle suspects (near-zero activity) and peak hours.
- **Cost:** $0.01 per 1,000 metrics. With the 200-metric cap, max $0.002 per run.
- **Output contribution:** Per-resource four-golden-signals table; peak-hour callout; idle-suspect callout.
- **Uncovered resource types:** If a resource surfaces that has no `examples/aws/<resource-type>.md` file, record "metrics not collected — resource type not yet supported" as a gap in the output doc. Do not infer defaults.

### i. Resource Explorer — the cross-region inventory

- **APIs:** `resource-explorer-2:Search` (primary), `resource-explorer-2:ListIndexes` and `resource-explorer-2:ListViews` (for capability detection).
- **Query shape:** `Search` with a filter expression derived from the scoping primitive (tag, service name, region). Aggregated view across all regions where Resource Explorer is indexed.
- **Why:** Catches resources tagged for the service but living outside the assumed primary region. The classic "we forgot we have a Lambda in us-west-2."
- **Cost:** Free.
- **Output contribution:** "Resources by region" table; "resources outside the assumed primary region" callout.
- **Edge case:** If Resource Explorer is not configured in the account, source is skipped with a "known gap — recommend enabling Resource Explorer (free, see AWS docs) and re-running" note. Enabling Resource Explorer is **not** something the skill does — that's an out-of-scope write action.

### Cross-cutting rules for all four sources

1. **Every query shown and approved before execution.** Gate 3 prints the full plan. Gate 4 prints per-source results before moving on.
2. **All outputs traceable.** Every claim cites which API call + timestamp produced it.
3. **Read-only IAM.** Reference policy in `examples/iam-policy-readonly.json`. No write actions. CE and Resource Explorer APIs don't support resource-level ARN restrictions, so `Resource: "*"` is the AWS-imposed minimum — documented explicitly so the operator is not surprised.
4. **Time windows are explicit.** Cost = 30d; CloudTrail = 90d; CloudWatch = 14d hourly + 24h at 5min; Resource Explorer = point-in-time. The output doc states these prominently.

## Workflow & Gates

Six gates, none optional, each requires explicit operator confirmation.

```
Gate 1: Scoping        → confirm service name, scoping primitive, account, region, intent
Gate 2: Capability     → detect which sources are available; operator confirms capability matrix
Gate 3: Query plan     → show every API call with params, time window, estimated cost; approve plan
Gate 4: Source-by-source execution → per source: run → show raw results → operator OK → next source
Gate 5: Synthesis      → present runtime-profile draft; operator reviews, iterates, approves
Gate 6: Write          → save .culiops/runtime-trace/<service>-runtime-profile.md + audit sidecars
```

### Step 1 — Scoping (Gate 1)

Skill prompts for, and the operator supplies:

- **Service name** (free text, used in output filename).
- **AWS account ID** and **primary region**.
- **Scoping primitive** — at least one of:
  - tag key/value (e.g., `service=payments`)
  - list of resource ARNs
  - "the resource set from this service-discovery catalog at `<path>`"
- **Intent category** (structured choice): one of `takeover` / `drift-check` / `post-incident` / `pre-cost-opt` / `other`. Used by future tooling to filter/aggregate runtime-profile docs.
- **Intent context** (free text, mandatory): "Why are you running this?" — e.g., "Service takeover from Team Foo, scheduled for 2026-06-15." Appears verbatim in the output doc's "How to read this document" block.
- **Intended audience** (free text): who will read the output — e.g., "Incoming on-call rotation for the payments service."
- **Optional:** override default time windows; pass `--redact` flag (consumed at Gate 6).

**Hard stop** if no scoping primitive is supplied. The skill refuses to run "find me everything in the account" mode — it has no way to attribute cost or events to a specific service.

### Step 2 — Capability detection (Gate 2)

Read-only probes:

- `cloudtrail:DescribeTrails` + `cloudtrail:GetTrailStatus` — is logging on? in which regions?
- `resource-explorer-2:ListIndexes` — is Resource Explorer configured? where's the aggregator index?
- `ce:GetCostAndUsage` with a tiny test query (one day, one dimension) — does the principal have Cost Explorer perms? is Cost Explorer enabled?
- `cloudwatch:ListMetrics` with `MaxResults=1` — does the principal have CloudWatch read perms?

Output: a capability matrix shown to the operator:

| Source | Available? | Action |
|---|---|---|
| Cost Explorer | ✓ / ✗ | will run / will skip / will fail without IAM change |
| CloudTrail | ✓ / ✗ | will run / will skip with gap recorded |
| CloudWatch | ✓ / ✗ | will run / will skip / will fail without IAM change |
| Resource Explorer | ✓ / ✗ | will run / will skip with gap recorded |

Operator confirms the matrix. If a critical source is unavailable, operator can abort and fix the prerequisite (enable CloudTrail logging, configure Resource Explorer, attach broader IAM perms) before re-running. **The skill does not perform these fixes.**

### Step 3 — Query plan (Gate 3)

Skill prints the full execution plan as a markdown table. Example:

| # | Source | API call | Params (summary) | Time window | Est. cost | IAM perm |
|---|---|---|---|---|---|---|
| 1 | Cost Explorer | `ce:GetCostAndUsage` | GROUP BY SERVICE | 30d | $0.01 | `ce:GetCostAndUsage` |
| 2 | Cost Explorer | `ce:GetCostAndUsage` | GROUP BY USAGE_TYPE | 30d | $0.01 | `ce:GetCostAndUsage` |
| 3 | CloudTrail | `cloudtrail:LookupEvents` | filter=ResourceName, 5 ARNs | 90d | free | `cloudtrail:LookupEvents` |
| 4 | CloudWatch | `cloudwatch:GetMetricData` | 12 resources × 5 metrics = 60 metrics, hourly | 14d | $0.0006 | `cloudwatch:GetMetricData` |
| 5 | Resource Explorer | `resource-explorer-2:Search` | filter=tag:owner=team-x | n/a | free | `resource-explorer-2:Search` |

**Total estimated cost:** $X.XX (must be ≤ $1.00 hard cap).

Operator approves the entire plan (or edits and re-confirms). If the estimate exceeds $1.00, the skill **refuses** to proceed — operator must reduce scope or explicitly raise the cap with documented justification (recorded in the audit trail).

### Step 4 — Source-by-source execution (Gate 4)

Each source runs as a discrete block. After each block:

1. Skill prints the raw API response (truncated to relevant fields, with full payload cached to the audit sidecar at `.culiops/runtime-trace/<service>-audit/<call-id>.json`).
2. Skill prints its derived rows for the output doc.
3. Skill updates the running cost total and compares to the estimate.
4. Operator responds: "looks right, continue" / "this is wrong, here's why" / "stop here."

Gate 4 is **per-source**, not per-API-call. Approving "run all Cost Explorer queries" is one approval; approving "run the 60 CloudWatch metrics" is one approval. More granular control adds friction without proportionate safety gain.

**Triggers that pause execution mid-Gate-4:**

- Running actual cost crosses $0.25 → soft-warning pause (Iron Law).
- Running actual cost would exceed $1.00 on the next call → abort (Iron Law).
- Actuals exceed estimate by >2× on any source → pause and ask before continuing.
- Any API failure (AccessDenied, throttling, unexpected error) → stop and report. **No silent retries.** Operator decides: fix and re-run, skip the source, or abort.
