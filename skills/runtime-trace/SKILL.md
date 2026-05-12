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
