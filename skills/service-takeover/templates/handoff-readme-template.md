---
handoff-package-schema: 1
service-takeover-version: <skill-version>
service: <service-name>
account: <aws-account-id>
region: <primary-region>
generated-at: <ISO-8601-UTC>
outgoing-team: <team-name>
incoming-team: <team-name>
---

# Service Takeover — <service-name>

## TL;DR

- **Handoff date:** <date>
- **From:** <outgoing team>
- **To:** <incoming team>
- **Readiness verdict:** <ready / not-ready / partial>
- **Open questions count:** <high>/<medium>/<low>
- **Top 5 open questions:**
  1. <question>
  2. <question>
  3. <question>
  4. <question>
  5. <question>

## What this package contains

| File | What it is |
|---|---|
| `service-catalog.md` | Snapshot of the `service-discovery` catalog at handoff time — what resources exist, naming patterns, dependency map. |
| `runtime-profile.md` | Snapshot of the `runtime-trace` runtime profile at handoff time — what's billing, who's calling, activity baselines, cross-region inventory. |
| `interview-questionnaire.md` | Filled-in outgoing-team interview — tribal knowledge that doesn't live in code. |
| `readiness-scorecard.md` | Production Readiness Review scorecard — 25 items across 8 categories, evidence-backed. |
| `open-questions.md` | Consolidated unresolved questions across all artifacts, prioritized. |
| `execution-plan.md` | Record of how this package was assembled (Step 1.5 audit + actions taken). |
| `state.md` | Workflow state — which steps ran, when, gate sign-offs. |

## First-day actions for <incoming team>

- [ ] Read this README in full.
- [ ] Skim `readiness-scorecard.md` and note any **✗** or **?** items in your team's tracker.
- [ ] Schedule a 30-minute follow-up with **<outgoing-team primary contact>** to cover the top-3 open questions above.
- [ ] Verify your team's IAM identities have console + CLI access to AWS account **<account-id>** in region **<region>**.
- [ ] Subscribe to the alerts listed in `interview-questionnaire.md` Section 5 on your team's paging tool.
- [ ] Read the top-3 runbooks referenced in `interview-questionnaire.md` Section 6.
- [ ] Note the landmines in Section 7 of the interview — surface them in your next team standup before any change.
- [ ] Read `interview-questionnaire.md` Section 10 (compliance/DR) and confirm your team can meet the stated RTO/RPO.

## Standards this package follows

This handoff package was assembled following these recognized industry patterns:

- **Production Readiness Review (PRR)** — Google SRE book, Ch. 32 ("The Evolving SRE Engagement Model"). Source of the 8-category scorecard structure.
- **Four golden signals** — Google SRE book, Ch. 6 ("Monitoring Distributed Systems"). Underlies the runtime-profile activity baselines.
- **ITIL 4 Service Transition** — formal-handoff framework. Source of the package's "knowledge transfer + configuration item" structure.
- **AWS Well-Architected Framework — Operational Excellence pillar (OPS-3 to OPS-7)** — source of the operational-readiness questions.
- **DORA metrics** (Accelerate, by Forsgren et al.) — deploy frequency, lead time, MTTR, change failure rate — captured in interview Sections 4 and 6.

## How this package was generated

This package was assembled by the `service-takeover` skill (culiops plugin, version <skill-version>). The skill orchestrated an operator through eight gates:

1. **Intake** — gathered scoping primitives.
2. **Information audit** — surveyed available materials, proposed cheapest action per gap.
3. **Diagram extraction** — delegated to `service-discovery` (real-discovery mode).
4. **Live discovery** — delegated to `service-discovery` (real-discovery mode, AWS CLI).
5. **Runtime profile** — delegated to `runtime-trace`.
6. **Interview** — emitted questionnaire, ingested filled version.
7. **Readiness scorecard** — auto-marked items from prior artifacts; operator marked the rest.
8. **Handoff package** — assembled this directory.

To reproduce this package, see `state.md` for the gate sign-offs and `execution-plan.md` for the actions taken.

## What this package does NOT contain

- **Cost optimization recommendations.** Use `cloud-cost-investigate` after takeover if needed.
- **Generated IaC.** Use a separate IaC-import tool (e.g., Terraformer).
- **Real-time monitoring.** Subscribe to alerts and dashboards listed in the interview.
- **Trace data (X-Ray / OTel).** Out of scope for `runtime-trace` v1.

## Questions about this package itself

If something in this package looks wrong, refer to:

- The design spec: `docs/superpowers/specs/2026-05-12-service-takeover-design.md` in the culiops-agent repo.
- The skill source: `skills/service-takeover/SKILL.md` in the culiops-agent repo.
- The `state.md` file in this directory for the audit trail.
