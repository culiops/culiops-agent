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
