---
handoff-package-schema: 1
service-takeover-version: 0.6.0
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-12T16:05:00Z
outgoing-team: Pay Team
incoming-team: Platform Team
---

# Service Takeover — payments

## TL;DR

- **Handoff date:** 2026-06-15
- **From:** Pay Team (Bob L. — bob@example.com, Carol P. — carol@example.com)
- **To:** Platform Team
- **Readiness verdict:** ready
- **Open questions count:** 0 high / 2 medium / 0 low
- **Top 5 open questions:**
  1. Training session between Pay Team and Platform Team not yet scheduled (MED-1).
  2. DR drill not yet scheduled for incoming Platform Team (MED-2).
  3. Platform Team IAM deploy role (`platform-team-deploy`) needs to be added to deploy permissions before 2026-06-15.
  4. Alice's console Secrets Manager read access should be revoked post-handoff.
  5. *(No further open items — service is ready for takeover.)*

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

## First-day actions for Platform Team

- [ ] Read this README in full.
- [ ] Skim `readiness-scorecard.md` and note the 2 medium-priority open questions in your team's tracker.
- [ ] Schedule a 2-hour walkthrough session with **Bob L. (bob@example.com)** and **Carol P. (carol@example.com)** before 2026-06-15 (see open-questions MED-1).
- [ ] Verify your team's IAM identities have console + CLI access to AWS account **123456789012** in region **us-east-1**. Confirm `platform-team-deploy` role is added to deploy permissions.
- [ ] Subscribe to the 5 alerts listed in `interview-questionnaire.md` Section 5 on your team's PagerDuty rotation.
- [ ] Read the top-3 runbooks referenced in `interview-questionnaire.md` Section 6 (auth-error-spike, capture-queue-backup, dlq-triage).
- [ ] Note the landmines in Section 7 of the interview — surface in your next team standup before any change: (1) Stripe webhook signature verification fragility; (2) DynamoDB schema changes only during Friday 22:00 UTC maintenance window.
- [ ] Read `interview-questionnaire.md` Section 10 (compliance/DR) and confirm your team can meet RTO 30 min / RPO 5 min. Schedule a DR drill before 2026-07-15 (see open-questions MED-2).
- [ ] Request that alice's console Secrets Manager read access (`arn:aws:iam::123456789012:user/alice`) be revoked post-handoff.

## Standards this package follows

This handoff package was assembled following these recognized industry patterns:

- **Production Readiness Review (PRR)** — Google SRE book, Ch. 32 ("The Evolving SRE Engagement Model"). Source of the 8-category scorecard structure.
- **Four golden signals** — Google SRE book, Ch. 6 ("Monitoring Distributed Systems"). Underlies the runtime-profile activity baselines.
- **ITIL 4 Service Transition** — formal-handoff framework. Source of the package's "knowledge transfer + configuration item" structure.
- **AWS Well-Architected Framework — Operational Excellence pillar (OPS-3 to OPS-7)** — source of the operational-readiness questions.
- **DORA metrics** (Accelerate, by Forsgren et al.) — deploy frequency, lead time, MTTR, change failure rate — captured in interview Sections 4 and 6.

## How this package was generated

This package was assembled by the `service-takeover` skill (culiops plugin, version 0.6.0). The skill orchestrated an operator through eight gates:

1. **Intake** — gathered scoping primitives.
2. **Information audit** — surveyed available materials, proposed cheapest action per gap.
3. **Diagram extraction** — delegated to `service-discovery` (real-discovery, image mode).
4. **Live discovery** — delegated to `service-discovery` (real-discovery, AWS CLI).
5. **Runtime profile** — delegated to `runtime-trace`.
6. **Interview** — emitted questionnaire, ingested filled version from Pay Team.
7. **Readiness scorecard** — auto-marked 23 items from prior artifacts; operator manually confirmed 2 items.
8. **Handoff package** — assembled this directory.

To reproduce this package, see `state.md` for the gate sign-offs and `execution-plan.md` for the actions taken.

## What this package does NOT contain

- **Cost optimization recommendations.** Use `cloud-cost-investigate` after takeover if needed.
- **Generated IaC.** Use a separate IaC-import tool (e.g., Terraformer). Note: IaC migration is on the roadmap for Q3 2026.
- **Real-time monitoring.** Subscribe to alerts and dashboards listed in the interview.
- **Trace data (X-Ray / OTel).** Out of scope for `runtime-trace` v1.

## Questions about this package itself

If something in this package looks wrong, refer to:

- The design spec: `docs/superpowers/specs/2026-05-12-service-takeover-design.md` in the culiops-agent repo.
- The skill source: `skills/service-takeover/SKILL.md` in the culiops-agent repo.
- The `state.md` file in this directory for the audit trail.
