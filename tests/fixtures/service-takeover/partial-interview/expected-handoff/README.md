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
- **From:** Pay Team (Bob L. — bob@example.com)
- **To:** Platform Team
- **Readiness verdict:** not-ready
- **Open questions count:** 5 high / 3 medium / 0 low
- **Top 5 open questions:**
  1. SLOs not defined — work with Pay Team to define before handoff (HIGH-1).
  2. Backup strategy unknown — verify PITR status and last restore test (HIGH-2).
  3. DR plan unknown — RTO/RPO unverified, runbook location unknown (HIGH-3).
  4. PII handling unknown — PCI/GDPR scope unconfirmed (HIGH-4).
  5. Data retention policy unknown — retention duration and TTL configuration unconfirmed (HIGH-5).

**Important:** The outgoing team filled in only 6 of 11 interview sections. Section 10 (Compliance/DR) and Section 3 (SLOs) were left entirely empty. The operator accepted the interview as-is at Gate 5. The 5 high-priority open questions above must be resolved before takeover sign-off. Do not mark the handoff complete until these are addressed.

## What this package contains

| File | What it is |
|---|---|
| `service-catalog.md` | Snapshot of the `service-discovery` catalog at handoff time — what resources exist, naming patterns, dependency map. |
| `runtime-profile.md` | Snapshot of the `runtime-trace` runtime profile at handoff time — what's billing, who's calling, activity baselines, cross-region inventory. |
| `interview-questionnaire.md` | Filled-in outgoing-team interview — tribal knowledge that doesn't live in code. **Note: Sections 3, 6 (partial), 10, and 11 (partial) were not completed by the outgoing team.** |
| `readiness-scorecard.md` | Production Readiness Review scorecard — 25 items across 8 categories, evidence-backed. Verdict: not-ready (Compliance category 0/4). |
| `open-questions.md` | Consolidated unresolved questions across all artifacts, prioritized. 5 high-priority blockers from empty compliance and SLO sections. |
| `execution-plan.md` | Record of how this package was assembled (Step 1.5 audit + actions taken). |
| `state.md` | Workflow state — which steps ran, when, gate sign-offs, and the "accept as-is" decision at Gate 5. |

## First-day actions for Platform Team

**Before proceeding with any production changes, resolve the 5 high-priority open questions:**

- [ ] **[HIGH-1]** Contact Bob L. (bob@example.com) to define SLOs (availability, latency targets, error budget). Do not operate the service without quantitative targets.
- [ ] **[HIGH-2]** Verify backup strategy: run `aws dynamodb describe-continuous-backups --table-name payments-ledger` to confirm PITR status. Obtain last restore test date from Carol P. (carol@example.com).
- [ ] **[HIGH-3]** Obtain DR runbook from Carol P. Confirm RTO/RPO targets and failover region. Schedule a DR tabletop with the Platform Team before or within 30 days of handoff.
- [ ] **[HIGH-4]** Confirm PII scope with Bob L. and legal/compliance. Verify PCI DSS SAQ type and GDPR data subject deletion procedure before taking on-call.
- [ ] **[HIGH-5]** Confirm data retention policy and TTL configuration on payments-ledger. Verify with legal that retention duration meets regulatory requirements.

**After resolving high-priority items:**

- [ ] Read this README in full.
- [ ] Schedule a 2-hour walkthrough session with Bob L. and Carol P. before 2026-06-15 (see open-questions MED-2). Prioritize compliance/DR gaps in that session.
- [ ] Verify your team's IAM identities have console + CLI access to AWS account **123456789012** in region **us-east-1**. Confirm `platform-team-deploy` role is added to deploy permissions.
- [ ] Subscribe to the 5 alerts listed in `interview-questionnaire.md` Section 5 on your team's PagerDuty rotation.
- [ ] Read the top-3 runbooks referenced in `interview-questionnaire.md` Section 6 (auth-error-spike, capture-queue-backup, dlq-triage).
- [ ] Note the landmines in Section 7 of the interview — surface in your next team standup before any change: (1) Stripe webhook signature verification fragility; (2) DynamoDB schema changes only during Friday 22:00 UTC maintenance window.
- [ ] Request incident history from Pay Team before or by handoff date (see open-questions MED-1).
- [ ] Request the open-issues list from Bob before handoff date (see open-questions MED-3).

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
6. **Interview** — emitted questionnaire, ingested partial version from Pay Team. Operator selected "accept as-is" at Gate 5 rather than returning to outgoing team for completion.
7. **Readiness scorecard** — auto-marked 18 items from prior artifacts; operator manually confirmed 2 items; 5 items marked `?` (4 Compliance items from empty Section 10 + 1 incidents item from empty Section 6 sub-fields). Per Iron Law, absence of evidence is `?` not `✗`.
8. **Handoff package** — assembled this directory.

To reproduce this package, see `state.md` for the gate sign-offs and `execution-plan.md` for the actions taken.

## What this package does NOT contain

- **Cost optimization recommendations.** Use `cloud-cost-investigate` after takeover if needed.
- **Generated IaC.** Use a separate IaC-import tool (e.g., Terraformer). Note: IaC migration is on the roadmap for Q3 2026.
- **Real-time monitoring.** Subscribe to alerts and dashboards listed in the interview.
- **Trace data (X-Ray / OTel).** Out of scope for `runtime-trace` v1.
- **Compliance/DR answers.** Section 10 was not filled by the outgoing team. See open-questions.md HIGH-2 through HIGH-5 for follow-up actions.

## Questions about this package itself

If something in this package looks wrong, refer to:

- The design spec: `docs/superpowers/specs/2026-05-12-service-takeover-design.md` in the culiops-agent repo.
- The skill source: `skills/service-takeover/SKILL.md` in the culiops-agent repo.
- The `state.md` file in this directory for the audit trail.
