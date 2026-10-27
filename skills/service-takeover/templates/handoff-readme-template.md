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

> **Private repo only.** This package holds the account ID, IAM ARNs, escalation chains and incident detail. Record references (where a secret lives, who owns it), never values. No tokens/signed links in URLs. Prefer role/team aliases over personal phone numbers. Check the repo is private before committing.

## TL;DR

- **Handoff date:** <date>
- **From:** <outgoing team>
- **To:** <incoming team>
- **Readiness verdict:** <ready / not-ready / partial> — `ready` only if every item is ✓ verified / ✓ attested / N/A; any ✗ or ✗ conflict → not-ready; otherwise any ◐ or ? → partial. Evidence as of <oldest timestamp behind any ✓>. To reach ready: <n> checks (listed in `readiness-scorecard.md`).
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
| `runtime-profile.md` | Snapshot of the `runtime-trace` runtime profile at handoff time — spend (attributed only if tag-scoped), who managed it (management events), what is wired to call it, activity baselines, cross-region footprint. |
| `interview-questionnaire.md` | Filled-in outgoing-team interview — tribal knowledge that doesn't live in code. |
| `readiness-scorecard.md` | Production Readiness Review scorecard — 25 items across 8 categories. Each mark is ✓ verified, ✓ attested, ◐ operator-stated, ✗, ✗ conflict, ? or N/A, with a cited source. |
| `open-questions.md` | Consolidated unresolved questions across all artifacts, prioritized. |
| `execution-plan.md` | Record of how this package was assembled (Step 1.5 audit + actions taken). |
| `state.md` | Workflow state — which steps ran, when, gate sign-offs. |

## First-day actions for <incoming team>

- [ ] Read this README in full.
- [ ] Skim `readiness-scorecard.md` and note any **✗**, **◐** or **?** items in your team's tracker. Treat **✗ conflict** as high priority: the interview and the artifacts disagree.
- [ ] Schedule a 30-minute follow-up with **<outgoing-team primary contact>** to cover the top-3 open questions above.
- [ ] Verify your team's IAM identities have console + CLI access to AWS account **<account-id>** in region **<region>** (and, if workloads run in a cluster, `kubectl` access to context **<context>**, namespace **<namespace>**).
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

This package was assembled by the `service-takeover` skill (culiops plugin, version <skill-version>). The skill orchestrated an operator through these gates:

1. **Gate 1 — Intake** — gathered scoping primitives.
2. **Gate 1.5 — Information audit** — surveyed available materials, proposed the cheapest action per gap.
3. **Gates 2–3 — Discovery** — one delegation to `service-discovery` (IaC path with live cross-check if IaC was supplied; otherwise real-discovery from docs and live APIs).
4. **Gate 4 — Runtime profile** — delegated to `runtime-trace`.
5. **Gate 5 — Interview** — emitted questionnaire, ingested filled version.
6. **Gate 6 — Readiness scorecard** — marked items from prior artifacts, with an optional read-only verification batch for operator-stated items.
7. **Gate 7 — Handoff package** — assembled this directory.

To reproduce this package, see `state.md` for the gate sign-offs and `execution-plan.md` for the actions taken.

## What this package does NOT contain

- **Cost optimization recommendations.** Use `cloud-cost-investigate` after takeover if needed.
- **Generated IaC.** Use `terraform import` blocks if you need to bring unmanaged resources under Terraform.
- **Real-time monitoring.** Subscribe to alerts and dashboards listed in the interview.
- **Trace data (X-Ray / OTel).** Out of scope for `runtime-trace`.

## Committing this package

The package is sensitive. Before committing, check the current branch and the remote's visibility (`git branch --show-current`, `git remote -v`, and the host's repo-visibility setting). Commit only to a private repo, never to a public one. If the package may be shared outside the incoming team, review every file; `--redact` on `runtime-trace` covers the runtime profile only.

## Questions about this package itself

If something in this package looks wrong, refer to:

- The skill source: `skills/service-takeover/SKILL.md` in the culiops-skills repo.
- The `state.md` file in this directory for the audit trail.
