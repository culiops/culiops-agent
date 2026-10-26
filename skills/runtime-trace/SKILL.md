---
name: runtime-trace
description: Use when the user wants to build a runtime profile of an AWS service — what it actually costs, who manages it and what is wired to call it, what its activity baseline looks like, and where it actually lives across regions. Triggers include "runtime profile <service>", "trace runtime for <service>", "what's actually running for <service>". Useful for service takeovers (no docs, no IaC), drift checks after a previous discovery, post-incident retrospectives, and pre-cost-optimization baselining. Read-only; queries Cost Explorer, CloudTrail LookupEvents (Event history), CloudWatch GetMetricData, Resource Explorer, and free resource-policy reads. AWS APIs only; in-cluster Kubernetes workloads are recorded as a gap.
---

# Runtime Trace

Produce a self-contained runtime profile of an AWS service by querying cheap, read-only data sources — **Cost Explorer** (the spend oracle, tag-filtered), **CloudTrail LookupEvents** (Event history: who managed it), **wiring reads** (resource policies and event-source mappings: what is configured to call it), **CloudWatch GetMetricData** (activity baselines, targeted), and **Resource Explorer** (cross-region inventory) — and writing the result to `.culiops/runtime-trace/<service>-runtime-profile.md` in the target repo. Seven gates, hard cost cap of $1.00 per run, every claim traceable to an API call.

This skill answers four questions that infrastructure-as-code discovery cannot:

1. **What does it actually cost?** (Cost Explorer, filtered to the service's cost-allocation tag. Without a tag, spend is account context only — see "Spend attribution".)
2. **Who manages it, and what is wired to call it?** (CloudTrail Event history surfaces the IAM principals behind management events — deploys, config changes, cross-account access — last 90 days. Data-plane callers never appear there; resource policies and event-source mappings show what is *configured* to call it.)
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
- Law 2 (no assumptions): if a metric is missing, a CloudTrail event ambiguous, or a Cost Explorer line item unattributable, the output records "unknown" with the reason — never a guess. **Empty is not zero:** an empty CloudWatch series, an empty Resource Explorer result, or an empty CloudTrail page is "no data" until a check proves the query could have returned data (see each source's rules).
- Law 3 (cost cap): $1.00 is calibrated against realistic worst-case (~$0.16 across all sources). The cap catches bug/misconfig blast immediately while giving legitimate larger runs (e.g., 500 CloudWatch metrics) room to complete.
- Law 4 (out-of-scope approval): "five-field approval" means the operator sees a structured proposal with WHAT (the exact API call or human action), WHY (what gap motivates it), COST (estimated $ and time), BLAST RADIUS (read-only? account-wide? cross-account? reversible?), ALTERNATIVES (what we could do instead, including "skip and document the gap"). Verbal "yes" without seeing the five fields is not approval.

## Constraints (Non-Negotiable)

1. **The cloud APIs are the source of truth.** Every claim in the runtime profile must cite a specific API call, its parameters, and its timestamp. No outside-knowledge inference (e.g., "Lambda usually has X" without an actual `GetMetricData` response). A claim is only as wide as the query behind it: account-wide spend is never presented as the service's spend, a regional query is never presented as account-wide, and management events are never presented as "all callers".
2. **No assumptions.** If a metric is missing, a CloudTrail event is ambiguous, or a Cost Explorer line item is unattributable, the doc records "unknown" with the reason — never a guess.
3. **Strict scope.** The resource set is resolved from the scoping primitive first (Step 2b) and shown to the operator; CloudTrail, wiring reads and CloudWatch then target exactly that set. Cost Explorer is filtered by the scoping tag. No fan-out across the account (no unfiltered CE as "service spend", no `EventSource` lookups by default).
4. **No secrets, ever — by projection, not by regex.** Pattern-based redaction cannot recognise a secret stored under an innocent key (`DB_CONN`, `CONFIG`). So nothing unprojected is ever written: audit sidecars and the profile carry only the fields listed in "Audit sidecar projection" (Gate 6). CloudTrail `requestParameters`, `responseElements`, `sourceIPAddress`, `userAgent` and role session names (often an email) are never written to any file. Raw responses stay in the session.
5. **Read-only IAM only.** The reference policy ships in `examples/iam-policy-readonly.json` and contains zero write actions. If a feature would require a write action, that feature is out of scope.
6. **Resolve to a single, named, verified scope.** A run targets one AWS account + one primary region + one scoping primitive. Multi-account or multi-region-primary runs require separate invocations. The account is **verified, not trusted**: GATE 1a's `sts get-caller-identity` must match the operator-typed account ID, and the active CLI region (`AWS_REGION` / `AWS_DEFAULT_REGION` / profile) must match the primary region, or every regional call carries `--region` explicitly. In an Organizations management (payer) account, every CE call adds a `LINKED_ACCOUNT` filter for the target account.
7. **Operator confirmation at every gate.** Seven workflow gates exist (Section "Workflow & Gates"). None are optional. No gate may be auto-confirmed.
8. **Out-of-scope actions require five-field approval.** See Iron Law.
9. **Describe, never prescribe.** Verdicts carry no action words ("sunset", "delete", "remove", "rightsize", "candidate for …"). A 14-day window cannot judge a periodic job, and cost-skill Principle 3 requires 60–180 days of evidence before any delete. Any downstream skill that reads this profile treats its activity data as context, never as delete evidence.

## Rationalization Prevention

| Thought | Reality |
|---|---|
| "Cost Explorer queries are basically free, I don't need to estimate" | STOP — every API call is estimated, every estimate shown to the operator. |
| "I'll just enable Resource Explorer for them, it'll only take a moment" | STOP — enabling a service is a write action and out-of-scope. Five-field approval required. |
| "The operator already approved the plan, I can skip the per-source gate" | STOP — Gate 4 (per-source) is separate from Gate 3 (plan). Both required. |
| "This Athena scan would only cost a few dollars" | STOP — Tier 2 sources are out-of-scope. Five-field approval required even if cheap. |
| "I'll just retry the failed call, maybe it was transient" | STOP — failures stop the skill. No silent retries. Operator decides. |
| "The operator says the service is in us-east-1, I'll only query that region" | STOP — Resource Explorer's cross-region pass exists precisely to catch this assumption. Run it. |
| "This CloudTrail event has a password in `requestParameters`, I'll include it" | STOP — redact secret-shaped fields before writing to the audit trail. |
| "The cost cap is $1.00, I'm at $0.95, the next call is only $0.05" | STOP — the cap is a hard tripwire. Abort and ask the operator to raise the cap with justification. |
| "We crossed $0.25 but nothing looks wrong, I'll skip the soft-warning pause" | STOP — soft warnings are confirmations, not optional. The operator's "continue" is the safety check. |
| "I'll infer this resource type's metrics from defaults" | STOP — only metrics declared in `examples/aws/<resource-type>.md` are queried. If a resource type isn't covered, record it as a gap. |
| "The plan said 60 metrics, but we found 12 more resources, I'll just add them" | STOP — adding queries beyond the approved plan requires a new Gate 3. Re-plan or skip. |
| "DescribeTrails is empty, so CloudTrail is off — skip the source" | STOP — `LookupEvents` reads Event history, which is on by default and separate from trails. Probe with one `LookupEvents` page; a missing trail only limits history to 90 days and excludes data events. |
| "The unfiltered GROUP BY SERVICE result is close enough to the service's spend" | STOP — unfiltered CE is the whole account (or the whole org in a payer). Filter by the scoping tag, or label the section "account context — not attributable". |
| "The metric came back empty, so it's zero" | STOP — CloudWatch publishes no datapoint for an absent event, and a wrong dimension/region also returns `[]`. Run the `ListMetrics` existence check, then record `no-data` or `metric-not-found`. |
| "Zero invocations in 14 days — I'll flag it as a sunset candidate" | STOP — Constraint 9. Record `no-activity-14d` and an open question for the outgoing team. |
| "Resource Explorer found nothing outside the primary region, so there is no cross-region drift" | STOP — only a view in the aggregator Region searches across Regions, and un-indexed Regions are invisible. Check the index type and view first. |
| "I'll put the full CloudTrail event in the sidecar for reproducibility" | STOP — Constraint 4. Projected fields only. Re-run the query to reproduce. |

## Cost Guardrails

- **Hard cap: $1.00 per run.** Calibrated against the realistic worst case across all sources (~$0.16). Catches bug/misconfig explosions immediately; gives legitimate larger runs (e.g., 500 CloudWatch metrics) room to complete.
- **Soft warning: $0.25 per run.** When the running actual-cost total crosses $0.25, skill pauses and asks the operator to confirm. Normal runs (under $0.05) never trigger.
- **Estimate before every API call.** Even free ones. The GATE 1a probe table and the Gate 3 plan table show estimated cost per row.
- **Tier 2 sources (Athena log scans on VPC Flow Logs, ALB access logs, CloudFront / WAF logs) are explicitly OUT OF SCOPE.** If demand emerges, build a separate `log-trace` skill — do not extend this skill.
- **Every page is a request.** One plan row = one call series; its estimate is `pages × per-request price`. Cost Explorer `GetCostAndUsage`, `GetDimensionValues` and `GetTags` each charge per request **including every paginated page**, with no free tier — check the current price on the AWS Cost Explorer pricing page; the skill uses $0.01/request for estimates.
- **Read-only does not mean free.** Operator approves the plan and acknowledges the dollar amount at Gate 3.

### Cost ceilings per source (theoretical worst case)

| Source | Per-request cost | Skill cap | Worst-case total |
|---|---|---|---|
| Cost Explorer | $0.01 per request (each page counts) | ≤10 requests/run incl. pages (16 with optional dimensions) | $0.10–$0.16 |
| CloudTrail LookupEvents | free (Event history) | 20 pages per resource name (default), ≤2 req/s | $0.00 |
| Wiring reads (resource policies, event-source mappings, target groups) | free | one call per resolved resource | $0.00 |
| CloudWatch GetMetricData / ListMetrics | $0.01 / 1,000 metrics requested; ListMetrics free | 200 metrics/run | $0.002 |
| Resource Explorer / Tagging API | free | — | $0.00 |
| **Total worst case** | | | **~$0.16** |

## The Data Sources

### a. Cost Explorer — the spend oracle

- **APIs:** `ce:GetCostAndUsage` (primary), `ce:GetDimensionValues` (for value discovery), `ce:GetTags` (when tag scoping is supplied).
- **Spend attribution (decided at GATE 1a, printed in the profile):**
  - **Tag primitive** → every CE call carries `Filter: {Tags: {Key: <key>, Values: [<value>]}}` (AND `LINKED_ACCOUNT=<target>` in a payer account). This is the only case where the section is titled "Spend attributed to <service>".
  - **ARN-list or catalog primitive without a tag** → CE cannot attribute spend to resources (the resource-level `GetCostAndUsageWithResources` covers 14 days only and is opt-in in Cost Explorer settings). The section becomes **"Account context — not attributable to this service"**: account totals by service, clearly labelled, never in the TL;DR as the service's cost. If the operator confirms resource-level data is enabled, a 14-day `RESOURCE_ID` query is offered as an optional plan row.
  - **Shared cost** (NAT Gateway, data transfer, shared load balancers, KMS) is usually untagged and therefore invisible to a tag filter. The profile says so in Gaps instead of guessing a share.
- **Query shape:** `GROUP BY DIMENSION=SERVICE` and `GROUP BY DIMENSION=USAGE_TYPE`, granularity **DAILY** summed over a closed 30-day window (`End` is exclusive). Days whose result carries `Estimated: true` are excluded and the window is stated as actually used. Metric **`AmortizedCost`** with `RECORD_TYPE ∈ {Usage, DiscountedUsage, SavingsPlanCoveredUsage}` so RI/SP-covered usage is counted at its effective rate and one-off purchases, credits, refunds and tax don't masquerade as service spend; other record types, if present, are listed in a one-line footnote.
- **Why:** Bills don't lie — once they are scoped. A tag-filtered bill catches tagged dependencies the team forgot (an idempotency table, a log group, a Secrets Manager secret).
- **Cost:** $0.01 per request, each page counts. Budget ≤10 requests per run.
- **Output contribution:** "Spend by service" and "usage types" tables, with the attribution mode printed above them; "services billing but absent from the catalog" callout **only when the scoping primitive is a `service-discovery` catalog** (the comparison baseline is that catalog's resource types — without a catalog there is nothing to compare against, and the callout is omitted).
- **Tag-allocation heuristic:** If a tag-filtered query returns $0.00 but the Step 2b resolution found resources carrying the tag, surface a TL;DR alert: *"likely cost-allocation tag not activated in Billing — recommend activating `<tag-key>` as a cost-allocation tag and re-running."* Tags only flow into Cost Explorer after Billing-console activation, and only from activation onward.
- **Edge case:** Cost Explorer must be enabled in the account (free, but opt-in for new accounts). If the GATE 1a probe fails with "not enabled", the source is skipped with a gap.

### b. CloudTrail LookupEvents — the management-event log

- **APIs:** `cloudtrail:LookupEvents` (primary and capability probe), `cloudtrail:DescribeTrails` (informational only).
- **Event history is always on.** `LookupEvents` reads CloudTrail **Event history**: 90 days of management events per Region, enabled by default and separate from any trail. An empty `DescribeTrails` does **not** disable this source — it only means nothing older than 90 days and no data events exist anywhere, which becomes a Gap. The capability probe is one `LookupEvents` page in the primary Region.
- **Query shape:** one call series **per resolved resource name** — `LookupAttributes` accepts exactly one attribute per call. Time window: last 90 days. Pages are at most 50 events; the skill caps each series at **20 pages (1,000 events) by default**, shown per row in the Gate 3 plan, and records "truncated at N events" when the cap is hit.
- **Rate limit:** 2 requests/s per account per Region. The skill paces calls client-side to stay under it. A `ThrottlingException` gets **one** retry after a 2-second back-off — this is pacing, not a silent retry; a second failure stops the source and reports, per Gate 4.
- **ResourceName filter format:** Use the **simple resource name** — the trailing element of the resource ARN (e.g., `paymentservice`), **not** a cluster-prefixed or composite identifier (e.g., NOT `culishop-lab-paymentservice`). CloudTrail records the resource name as the AWS service emitted it; ECS services record only their `ServiceName`. If a filter returns zero events when the resource is known to exist, retry with the trailing-element form before recording "no events" — and record which form was used.
- **`EventSource` lookups are off by default.** `EventSource=lambda.amazonaws.com` returns every Lambda event in the account, not this service's. It runs only if the operator explicitly chooses it at Gate 3, and its results are labelled "account-wide, unscoped" and kept out of the principals table.
- **Global-service events** (IAM, STS, Organizations) are recorded in `us-east-1`. When the primary Region is elsewhere and the principals table names roles, the plan offers an optional `us-east-1` series per role name (`ResourceName=<role-name>`) to catch role/policy changes.
- **What it shows — and what it doesn't:** principals behind **management** events (create/update/delete, deploys, config changes, console and CLI reads that are management events). Data-plane activity — Lambda invokes, SQS sends/receives, DynamoDB item reads, S3 object access, HTTP requests through a load balancer — is never in Event history. The principals table is therefore "who *managed* this service", never "who calls it"; configured callers come from source c.
- **Output contribution:** "Top API actions by event count"; "Principals touching this service" table (ARN, principal type, last-seen, event count) under the note *management events only*; "notable change events" timeline; cross-account principals callout; "principals not in any known runbook" open question.
- **Edge cases:**
  - Probe fails with AccessDenied → source skipped, gap recorded, IAM fix named.
  - The 90-day limit is documented in the output. Anything older requires Athena over a trail's S3 archive, which is out of scope (Tier 2).

### c. Wiring reads — configured callers (free, read-only)

- **Why:** Event history can't see who invokes a function or sends to a queue. Resource policies and event-source mappings show who is **configured** to.
- **APIs (per resolved resource type):**
  - Lambda: `lambda:GetPolicy` (resource policy principals and source ARNs), `lambda:ListEventSourceMappings --function-name` (queues/streams that trigger it). Project out `Policy` statements' `Principal`, `Action`, `Condition.ArnLike/SourceArn` and the mappings' `EventSourceArn`, `State` — never `GetFunction` / `GetFunctionConfiguration` (they return environment variables).
  - SQS: `sqs:GetQueueAttributes --attribute-names Policy RedrivePolicy RedriveAllowPolicy` (who may send; whether this queue is a DLQ or has one).
  - ALB / NLB: `elasticloadbalancing:DescribeTargetGroups --load-balancer-arn` and `DescribeListeners` (what it forwards to).
  - Other types: not read; recorded as "wiring not collected for <type>".
- **Cost:** free. One call per resolved resource; listed in the Gate 3 plan.
- **Output contribution:** "Wiring (configured callers)" table: resource, caller (principal / source ARN / event source), mechanism (resource policy / event-source mapping / listener), citation.

### d. CloudWatch GetMetricData — the activity baseline (targeted)

- **APIs:** `cloudwatch:GetMetricData` (primary), `cloudwatch:ListMetrics` (capability probe and empty-result check).
- **Query shape:** **targeted only** — runs only against the resource set resolved in Step 2b. Per-resource metric sets defined in `examples/aws/<resource-type>.md`. Time range: last 14 days at hourly granularity. Skill caps total metrics per run at 200. Regional: resources outside the primary Region are excluded from this pass and listed in Gaps.
- **Per-resource metric sets (coverage; extensible):** see `examples/aws/lambda.md`, `examples/aws/ecs-service.md`, `examples/aws/alb.md`, `examples/aws/rds-instance.md`, `examples/aws/sqs-queue.md`, `examples/aws/apigw-rest.md`.
- **Why:** Four-golden-signals visibility per resource. Identifies resources with no observed activity and peak hours.
- **Cost:** $0.01 per 1,000 metrics requested. With the 200-metric cap, max $0.002 per run.
- **Empty is not zero.** CloudWatch publishes no datapoint for a period in which nothing happened, and a wrong dimension, namespace or Region also returns an empty series. For every empty series the skill runs `ListMetrics` with the same namespace, metric name and dimensions (free; metrics stay listed for about two weeks after their last datapoint): listed → `no-data (metric exists)`; not listed → `metric-not-found` (wrong dimension, never emitted, or older than the listing window). Neither is ever written as `0`.
- **Coverage heuristic:** If a metric returns fewer than 50% of expected datapoints (e.g., fewer than 168 over a 14-day hourly window), surface as a Gap: *"metric coverage <N>% — either intermittent activity or partial Container Insights / metric publisher configuration."* Operator decides which interpretation applies.
- **Verdicts** are defined per resource type in the examples files. They are descriptions, never actions (Constraint 9). Thresholds are labelled `heuristic:` and the raw numbers are always shown next to the verdict.
- **Uncovered resource types:** If a resource has no `examples/aws/<resource-type>.md` file, record "metrics not collected — resource type not yet supported" as a gap. Do not infer defaults.

### e. Resource Explorer — the cross-region inventory

- **APIs:** `resource-explorer-2:Search` (primary), `resource-explorer-2:GetIndex`, `ListIndexes`, `ListViews`, `GetView` (capability probe); fallback `tag:GetResources` (Resource Groups Tagging API, regional) for Step 2b resolution when Resource Explorer isn't set up.
- **Query shape:** `Search` with a filter expression derived from the scoping primitive (tag, service name), against a view in the **aggregator** Region.
- **Cross-Region claims need three checks**, recorded in the profile:
  1. **Index type.** Only a view in the aggregator Region searches across Regions. A local index searches its own Region only.
  2. **Indexed Regions.** Regions without a local index are invisible even to the aggregator (`ListIndexes`).
  3. **View properties.** The view must include the `tags` property for a `tag:` filter to be meaningful (`GetView` → `IncludedProperties`); `UNVERIFIED` against current AWS docs as of 2026-10-26 — the skill checks it rather than assuming either way.
  Plus: `Search` returns `Count.Complete`; `false` means results were capped — record a Gap. Resource Explorer does not index every resource type.
  Only when all checks pass may the profile say "no resources outside the primary Region". Otherwise: **"cross-Region: not verifiable — <reason>"**.
- **Why:** Catches resources tagged for the service but living outside the assumed primary region. The classic "we forgot we have a Lambda in us-west-2."
- **Cost:** Free.
- **Owner hint:** when the results carry tags, read `aws:cloudformation:stack-name` into an `Owner hint` column (CloudFormation, Serverless, SAM and CDK all deploy through stacks). Descriptive only — no extra queries, nothing stops.
- **Output contribution:** "Resources by region" table; "resources outside the assumed primary region" callout; verification status of the three checks.
- **Edge case:** If Resource Explorer is not configured, the source is skipped with a "known gap — recommend creating an aggregator index (free) and re-running" note. Creating indexes or views is **not** something the skill does — that's an out-of-scope write action.

### Cross-cutting rules for all sources

1. **Every query shown and approved before execution.** GATE 1a shows the probe batch; Gate 3 prints the full plan. Gate 4 prints per-source results before moving on.
2. **All outputs traceable.** Every claim cites which API call + timestamp produced it.
3. **Read-only IAM.** Reference policy in `examples/iam-policy-readonly.json`. No write actions. CE and Resource Explorer APIs don't support resource-level ARN restrictions, so `Resource: "*"` is the AWS-imposed minimum — documented explicitly so the operator is not surprised.
4. **Time windows are explicit.** Cost = closed 30d minus estimated days; CloudTrail = 90d; CloudWatch = 14d hourly; wiring and Resource Explorer = point-in-time. The output doc states these prominently.
5. **Raw output stays in the session.** Gate 4 shows responses on screen; only projected fields reach files (Constraint 4).

## Workflow & Gates

Seven gates, none optional, each requires explicit operator confirmation.

```
Gate 1:  Scoping         → confirm service name, scoping primitive, account, region, intent
Gate 1a: Scoping probe   → approve and run a small read-only probe batch (identity, payer, RE index, CT, CE, CW)
Gate 2:  Capability      → operator confirms the capability matrix + spend-attribution mode
         Step 2b         → resolve the resource set (free) and show it
Gate 3:  Query plan      → every API call with params, pages, time window, estimated cost; approve plan
Gate 4:  Source-by-source execution → CE → CloudTrail → Wiring → CloudWatch; per source: run → show results → operator OK → next
Gate 5:  Synthesis       → present runtime-profile draft; operator reviews, iterates, approves
Gate 6:  Write           → save .culiops/runtime-trace/<service>-runtime-profile.md + projected audit sidecars
```

### Step 1 — Scoping (Gate 1)

Skill prompts for, and the operator supplies:

- **Service name** (free text, used in output filename).
- **AWS account ID** and **primary region**.
- **Scoping primitive** — at least one of:
  - tag key/value (e.g., `service=payments`) — the only primitive that lets spend be attributed
  - list of resource ARNs
  - "the resource set from this service-discovery catalog at `<path>`"
- **Intent category** (structured choice): one of `takeover` / `drift-check` / `post-incident` / `pre-cost-opt` / `other`. Used by future tooling to filter/aggregate runtime-profile docs.
- **Intent context** (free text, mandatory): "Why are you running this?" — e.g., "Service takeover from Team Foo, scheduled for 2026-06-15." Appears verbatim in the output doc's "How to read this document" block.
- **Intended audience** (free text): who will read the output — e.g., "Incoming on-call rotation for the payments service."
- **Optional:** override default time windows or the CloudTrail page cap; pass `--redact` flag (consumed at Gate 6).

**Hard stop** if no scoping primitive is supplied. The skill refuses to run "find me everything in the account" mode — it has no way to attribute cost or events to a specific service.

### Step 1a — Scoping probe (Gate 1a)

Show this batch as a table (call, region, est. cost) and run it only on approval:

| # | Call | Est. cost | Answers |
|---|---|---|---|
| p1 | `sts get-caller-identity` | free | Does the identity's account match the operator-typed account? (Mismatch → hard stop.) |
| p2 | `iam list-account-aliases` | free | Account alias for the Overview. |
| p3 | `organizations describe-organization` | free | Payer or member? `AWSOrganizationsNotInUseException` = standalone; `AccessDenied` in a member account is normal. Master account ID = caller account → payer → `LINKED_ACCOUNT` filter on every CE call. |
| p4 | `resource-explorer-2 get-index` + `list-indexes` + `list-views` + `get-view` (primary Region) | free | Index type (local/aggregator), aggregator Region, indexed Regions, default view properties. |
| p5 | `cloudtrail lookup-events --max-results 1` (primary Region) + `describe-trails` | free | Event history readable? Any trail (for the >90d / data-events Gap)? |
| p6 | `ce get-cost-and-usage` — 1 day, 1 dimension (+ tag filter if tag primitive) | $0.01 | CE enabled and permitted? Does the tag filter return anything? |
| p7 | `cloudwatch list-metrics` (1 page, primary Region) | free | CloudWatch read permitted? |

Every probe is read-only and counts toward the run's cost total.

### Step 2 — Capability matrix (Gate 2)

Built from the GATE 1a results, shown to the operator:

| Source | Available? | Action |
|---|---|---|
| Cost Explorer | ✓ / ✗ | will run (attribution: tag / account context) / will skip / will fail without IAM change |
| CloudTrail Event history | ✓ / ✗ | will run (trail: yes/no — affects only the >90d/data-events Gap) / will fail without IAM change |
| Wiring reads | ✓ / ✗ | will run / will skip (no IAM) |
| CloudWatch | ✓ / ✗ | will run / will skip / will fail without IAM change |
| Resource Explorer | ✓ aggregator / ~ local only / ✗ | will run (cross-Region verifiable) / will run (single Region only) / will skip with gap |

Operator confirms the matrix and the spend-attribution mode. If a critical source is unavailable, operator can abort and fix the prerequisite (attach IAM perms, create an aggregator index, activate a cost-allocation tag) before re-running. **The skill does not perform these fixes.**

### Step 2b — Resolve the resource set

Free and read-only; runs right after Gate 2:

- **Tag primitive** → Resource Explorer `Search` (aggregator view if available), else `tag:GetResources` in the primary Region.
- **ARN list** → used as given; each ARN's Region and type are parsed.
- **Catalog** → the resources the `service-discovery` catalog lists, with their citations.

Show the resolved set (ARN, type, Region, owner hint, metric file available?). Resources outside the primary Region are listed and marked "excluded from CloudTrail/CloudWatch pass — re-run with that Region". EKS clusters are marked "in-cluster workloads not traced". The operator confirms the set before Gate 3 is priced. This list is what CloudTrail, wiring and CloudWatch target — nothing else.

### Step 3 — Query plan (Gate 3)

Skill prints the full execution plan as a markdown table, priced against the resolved set. Example:

| # | Source | API call | Params (summary) | Pages | Time window | Est. cost | IAM perm |
|---|---|---|---|---|---|---|---|
| 1 | Cost Explorer | `ce:GetCostAndUsage` | GROUP BY SERVICE, Filter tag service=payments, DAILY, AmortizedCost | 1 | closed 30d | $0.01 | `ce:GetCostAndUsage` |
| 2 | Cost Explorer | `ce:GetCostAndUsage` | GROUP BY USAGE_TYPE, same filter | 1–2 | closed 30d | $0.02 | `ce:GetCostAndUsage` |
| 3–7 | CloudTrail | `cloudtrail:LookupEvents` | ResourceName=<name>, one series per resource (5) | ≤20 each | 90d | free | `cloudtrail:LookupEvents` |
| 8–11 | Wiring | `lambda:GetPolicy`, `lambda:ListEventSourceMappings`, `sqs:GetQueueAttributes` | per resolved resource | 1 each | point-in-time | free | see IAM policy |
| 12 | CloudWatch | `cloudwatch:GetMetricData` | 3 functions × 6 + 1 queue × 5 = 23 metrics, hourly | 1 | 14d | $0.0002 | `cloudwatch:GetMetricData` |

**Total estimated cost:** $X.XX including the GATE 1a probes (must be ≤ $1.00 hard cap).

Operator approves the entire plan (or edits and re-confirms). If the estimate exceeds $1.00, the skill **refuses** to proceed — operator must reduce scope or explicitly raise the cap with documented justification (recorded in the audit trail).

### Step 4 — Source-by-source execution (Gate 4)

Sources run in this order: **Cost Explorer → CloudTrail → Wiring → CloudWatch.** (Resource Explorer already ran in Step 2b.) After each source:

1. Skill prints the response on screen, truncated to relevant fields. Raw responses are kept in the session only.
2. Skill prints its derived rows for the output doc.
3. Skill updates the running cost total and compares to the estimate.
4. Operator responds: "looks right, continue" / "this is wrong, here's why" / "stop here."

Gate 4 is **per-source**, not per-API-call. Approving "run all Cost Explorer queries" is one approval; approving "run the 23 CloudWatch metrics" is one approval. More granular control adds friction without proportionate safety gain.

**Triggers that pause execution mid-Gate-4:**

- Running actual cost crosses $0.25 → soft-warning pause (Iron Law).
- Running actual cost would exceed $1.00 on the next call → abort (Iron Law).
- Actuals exceed estimate by >2× on any source → pause and ask before continuing.
- Any API failure (AccessDenied, unexpected error, or a throttle that survives the one paced retry) → stop and report. **No silent retries.** Operator decides: fix and re-run, skip the source, or abort.

### Step 5 — Synthesis (Gate 5)

Skill assembles the runtime-profile draft (structure in "Output Document Structure" below) and shows it inline to the operator. Operator iterates: ask for revisions, request additional callouts, remove sections, correct mis-derived rows. **No single-shot — explicit iteration loop here.** Before showing the draft, the skill self-checks it: no action words in verdicts or TL;DR (Constraint 9); every spend number carries its attribution mode; no empty series written as 0; cross-Region claim matches the three RE checks. Skill does not proceed until operator says "approved."

### Step 6 — Write (Gate 6)

On approval, the skill writes:

- `.culiops/runtime-trace/<service>-runtime-profile.md` — the human-readable profile (always emitted).
- `.culiops/runtime-trace/<service>-audit/<call-id>.json` — one sidecar per call series, holding the **projection** below. Always emitted unless the operator opts out at Gate 6.
- `.culiops/runtime-trace/<service>-runtime-profile.redacted.md` — emitted **only** if the operator passed `--redact` at Gate 1. Account IDs → `<ACCOUNT>`. Principal ARNs and resource ARNs → `arn:aws:<service>:<region>:<ACCOUNT>:<handle>`, where `<handle>` is the first 8 hex chars of HMAC-SHA256(per-run random salt, ARN), so the same resource keeps the same handle within the doc but the handle can't be reversed by hashing guessed ARNs. The salt is never written to any file. Sidecars are **not** redacted — they stay internal.

**Audit sidecar projection** (the only fields written):

- Every sidecar: call ID, timestamp (UTC), source, API name, request parameters (these are the skill's own filters — no secrets), page count, response size, cost, gate-of-approval reference.
- Cost Explorer: the `ResultsByTime` groups (keys + amounts + `Estimated`).
- CloudTrail: per event `EventId, EventTime, EventName, EventSource, ReadOnly, principal ARN` (the `sessionIssuer` role ARN for assumed roles, never the session name), `principal type, recipientAccountId, Resources[]`. **Never** `requestParameters`, `responseElements`, `sourceIPAddress`, `userAgent`, or the raw `CloudTrailEvent` string.
- Wiring: the projected fields named in source c.
- CloudWatch: `Id, Label, Timestamps, Values, StatusCode`.
- Resource Explorer: `Arn, Region, ResourceType`, owner hint, `Count`.

**Committing.** The skill does not commit. Committing the profile is the operator's call: the skill prints the paths, says whether the current branch is the default branch, and warns if the repo's remote is public (`git remote -v` + the host's visibility, if determinable). Principal ARNs, account IDs and spend are business-sensitive even after projection. Sidecars are internal: the skill recommends adding `.culiops/runtime-trace/*-audit/` to `.gitignore` and never stages them.

## Output Document Structure

`.culiops/runtime-trace/<service>-runtime-profile.md`. Self-contained by design — a reader six months from now, with no chat context and no operator memory, must be able to understand what it is, verify the claims, and reproduce the run.

```markdown
---
runtime-profile-schema: 2
runtime-trace-version: <plugin version from .claude-plugin/plugin.json>
generated-at: <ISO 8601 UTC>
service: <name>
account: <id>
region: <primary>
intent-category: <takeover | drift-check | post-incident | pre-cost-opt | other>
---

# Runtime Profile — <service-name>

## How to read this document
- What this is: runtime profile generated by runtime-trace v<x>
- Why it was generated: <operator's intent context from Gate 1, verbatim>
- Intent category: <category from Gate 1>
- Who should read this: <operator's audience statement from Gate 1, verbatim>
- What it covers: spend (closed 30d; attribution mode stated), management events (90d), configured callers (point-in-time), activity baselines (14d), cross-region resources (point-in-time)
- What it does NOT cover: data-plane callers (invokes, queue sends, HTTP requests), application logs, traces, in-cluster Kubernetes workloads, IaC, runbooks, on-call procedures, secret ownership (see "Gaps and Caveats")
- How fresh is this: generated <timestamp>; AWS state may have changed since. Re-run instructions at the bottom.

## Overview
- Service (operator-supplied), account (+ alias), verified by `sts get-caller-identity` at <timestamp>; payer / member / standalone; primary region
- Scoping primitive used (verbatim, every value listed)
- Discovery source: runtime-trace v<x.y.z>
- Run timestamp (UTC), operator (IAM principal)
- Sources status table (✓ ran / — skipped with reason / ✗ failed with reason)
- Time windows used per source (explicit)
- Total cost of this run: $X.XX (cap was $1.00)

## TL;DR
*Auto-generated from sections below. Verify against tables before consuming.*
- (≤5 bullets, headline findings)

## Spend Profile (Cost Explorer)
- Attribution mode, first line: "Spend attributed to <service> (tag <k>=<v>)" OR "Account context — NOT attributable to this service"
- Full request JSON above each table (filter, window actually used, metric, record types)
- Spend by service, closed 30d (estimated days excluded)
- Usage-type breakdown for top 5 services
- Callout (catalog primitive only): services billing but absent from the catalog
- Note: shared/untagged cost (NAT, data transfer, shared LBs) not attributable by tag
- Every row cites API call ID + timestamp

## Control-Plane Activity (CloudTrail)
- Source: Event history (trail present: yes/no). Lookup form used per resource; "truncated at N events" where the page cap hit
- Top API actions by event count, last 90d
- Principals touching this service (ARN, type, last-seen, event count) — preceded by: *management events only; these principals managed the resources. Data-plane callers are not visible here — see Wiring.*
- Notable change events timeline (with EventId for console lookup)
- Callout: cross-account principals
- Callout: principals not in any known runbook (open question for takeover)

## Wiring (configured callers)
- Resource | Caller (principal / source ARN / event source) | Mechanism (resource policy / event-source mapping / listener) | Citation
- "Wiring not collected for <type>" rows for types without a wiring read

## Activity Baselines (CloudWatch)
- Per-resource four-golden-signals table, raw numbers always shown
  | Resource | Traffic | Latency p50/p99 | Errors | Saturation | Verdict |
- Verdict vocabulary: `no-activity-14d`, `no-data (metric exists)`, `metric-not-found`, and the per-type heuristic verdicts from `examples/aws/` — never an action word
- Peak-hour callout
- No-activity callout: resources with zero observed activity in the window, each with an open question for the outgoing team ("is this a periodic job?"), never a recommendation
- Each cell carries MetricDataQuery ID + Namespace/MetricName/Dimensions triple

## Cross-Region Footprint (Resource Explorer)
- Verification: index type (aggregator in <region> / local only), indexed Regions, view includes tags (yes/no), `Count.Complete`
- Resources by region, by service, with owner hint
- Callout: resources outside assumed primary region — or "cross-Region: not verifiable — <reason>" when any check fails
- Callout: "Resource Explorer not configured" if applicable
- Search filter expression printed verbatim, with View ARN

## Gaps and Caveats (mandatory; never empty on a real run)
- Sources that couldn't run, and what's missing because of it
- Time-window edges (e.g., "CloudTrail LookupEvents max 90d — older history invisible")
- Unverifiable claims (anything inferred rather than directly observed)
- Resource types not covered (e.g., "DynamoDB metrics not collected — resource type not yet supported in examples/aws/")
- Data-plane callers not visible to Event history; no trail → nothing older than 90d, no data events
- Resources outside the primary Region excluded from CloudTrail/CloudWatch; EKS in-cluster workloads not traced
- Open questions for the outgoing team (feeds future service-takeover interview step)

## Glossary
*Auto-generated; only terms that appear in this doc.*
- NAT Gateway data transfer: <one-line>
- Four golden signals: <one-line, cites SRE book ch. 6>
- CloudTrail LookupEvents 90d cap: <one-line, AWS limit>
- (etc.)

## How to re-run this analysis
- Skill invocation: `runtime-trace --service <name> --account <id> --region <region> --scoping-primitive <verbatim>`
- Required IAM perms: <verbatim from examples/iam-policy-readonly.json>
- Required setup: <"Resource Explorer view in <region>" / "CloudTrail enabled with ManagementEvents=on" / etc. — only items that aren't AWS defaults>
- Expected cost: ~$<estimated based on this run's actuals>
- What may have drifted since this run: <date> ago — AWS state, IAM principals, spend, cross-region footprint can all change. Re-run before consuming this doc for any operational decision.

## Audit Trail
For each API call:
- Timestamp (UTC)
- Source (e.g., "Cost Explorer")
- API: `<service>:<Action>`
- Request parameters (the skill's own filters)
- Response size (bytes) + truncation policy applied
- Cost ($)
- Gate that approved it (Gate 3 plan-line #N, Gate 4 source approval timestamp)

Projected responses at `.culiops/runtime-trace/<service>-audit/<call-id>.json` (internal; not committed by the skill).

Total cost: $X.XX (≤ $1.00 cap).

Gate sign-offs: operator name + approval timestamps per gate.
```

### Output design rules

- **TL;DR is auto-generated** and labelled as such. If it conflicts with the tables below, the tables are authoritative — TL;DR is a convenience, not a contract.
- **"How to read this document"** uses operator-supplied intent and audience text verbatim. Skill never paraphrases or interprets.
- **Every claim is traceable.** No row in any table without a citation. Same discipline as `service-discovery`.
- **"Gaps and Caveats" is mandatory, never optional.** Even a clean run lists time-window edges and inferred-vs-observed distinctions. An empty Gaps section means the skill is lying.
- **Projected JSON sidecars emitted by default.** They record what each derived row came from. Reproducibility comes from re-running the logged request, not from storing raw responses (Constraint 4).
- **No charts, no images.** Markdown tables only. Doc is grep-able, PR-diffable, committable.
- **No recommendations.** The skill describes what is, not what should change (Constraint 9). Recommendations belong to humans or to downstream skills (`cloud-cost-investigate`, `service-takeover`), which must gather their own evidence for any change.
- **Strictly internal by default.** No automatic redaction in the primary doc. Operator who needs to share externally passes `--redact` at Gate 1, which causes Gate 6 to also emit a `<service>-runtime-profile.redacted.md` with rules described under Gate 6.

## Skill Structure

```
skills/runtime-trace/
├── SKILL.md                    ← this file
├── examples/
│   ├── aws/
│   │   ├── lambda.md           ← per-resource CloudWatch metric set
│   │   ├── ecs-service.md
│   │   ├── alb.md
│   │   ├── rds-instance.md
│   │   ├── sqs-queue.md
│   │   └── apigw-rest.md
│   └── iam-policy-readonly.json
```

Extending support to a new resource type = add one markdown file under `examples/aws/`. No code change needed.

Fixtures for testing live under `tests/fixtures/runtime-trace/<scenario>/`. Each fixture exercises one scenario end-to-end. See "Testing" below.

## Testing

Three layers, ordered by build effort:

1. **Fixture-driven dry-runs.** Each scenario under `tests/fixtures/runtime-trace/<name>/` includes:
   - `input.md` — scoping primitive, intent category, intent context, expected gate transitions.
   - `mock-api-responses/` — canned JSON responses for each API call the skill would make.
   - `expected-output.md` — the runtime-profile doc the skill should produce.
   - `DRY-RUN-NOTES.md` — simulated execution: which gates fire, which sources run, where the operator approves vs. aborts.

   A reviewer or implementing agent can step through the fixture inputs and validate the skill produces `expected-output.md`. Diff-based golden testing.

2. **Live smoke test in a sandbox account.** Optional, run manually before each release. Against a small known service in a personal AWS sandbox, run the skill end-to-end. Verify the doc reads correctly and total cost is under $0.10. Not in CI (costs money + requires creds). **Note:** the v0.7.0 smoke test was driven manually by a human operator; automated JSON sidecar emission (Gate 6) is verified by fixture but has not yet been exercised in a fully-automated live skill invocation — verify on the next end-to-end agent-driven run.

3. **Negative-case fixtures.** Explicitly covered:
   - `no-trail-event-history` — no trail configured; Event history is still traced, gap = >90d and data events.
   - `resource-explorer-missing` — Resource Explorer not configured; resource set resolved via the Tagging API, cross-Region not verifiable.
   - `multi-region-drift` — out-of-Region resource found (variant A) and local-index-only (variant B, cross-Region not verifiable).
   - `cost-cap-exceeded` — Gate 3 plan exceeds $1.00 (arithmetic shown); skill refuses to proceed.

## Versioning

- Skill version = the culiops plugin version in `.claude-plugin/plugin.json`, written to each profile as `runtime-trace-version`.
- Output doc schema version (`runtime-profile-schema: 2` — v2 added Wiring, attribution mode, verification fields and the verdict vocabulary) at the top of every emitted profile. Bumped only on breaking changes to the markdown structure. Enables future tools (or a future `service-takeover` skill) to parse runtime-profile docs deterministically.

## Out of Scope for v1

Documented explicitly so a future maintainer doesn't accidentally extend the skill into these areas without a fresh design pass:

- **Cost investigation** (anomaly hunting, waste analysis, savings recommendations) — that's `cloud-cost-investigate`.
- **Log scans** — VPC Flow Logs, ALB access logs, CloudFront / WAF logs. Athena scans are pay-per-TB. If demand emerges, build a separate `log-trace` skill.
- **X-Ray / OpenTelemetry traces** — useful when instrumented but rarely available in takeover scenarios.
- **AWS Config history** — overlaps with CloudTrail Event history for our purposes.
- **Other clouds** — not supported (multi-cloud content archived at tag `archive/multi-cloud-v0.10.0`).
- **In-cluster Kubernetes tracing** — EKS workloads are recorded as a gap; a Kubernetes source (events, OpenCost allocation, Prometheus) needs its own design pass.
- **IaC generation / state import** — even when the runtime profile reveals untracked resources, this skill does not generate Terraform/CDK.
- **Service-takeover orchestration** — the broader takeover workflow (interview, readiness checklist, handoff package) is a separate skill built on top of `runtime-trace` later.
- **Compute Optimizer / Trusted Advisor** — they provide optimization recommendations, which crosses into `cloud-cost-investigate` territory.
