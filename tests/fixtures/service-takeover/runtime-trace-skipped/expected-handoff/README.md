---
handoff-package-schema: 1
service-takeover-version: 0.6.0
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-12T15:40:00Z
outgoing-team: Pay Team
incoming-team: Platform Team
---

# Service Takeover — payments

> **Private repo only.** This package holds the account ID, IAM ARNs, escalation chains and incident detail. Record references (where a secret lives, who owns it), never values. No tokens/signed links in URLs. Prefer role/team aliases over personal phone numbers. Check the repo is private before committing.

## TL;DR

- **Handoff date:** 2026-06-15
- **From:** Pay Team (Bob L. — bob@example.com, Carol P. — carol@example.com)
- **To:** Platform Team
- **Readiness verdict:** partial — 4 items are `?` (5, 7, 8, 9: no runtime profile) and 11 are `◐`; nothing fails. 7 ✓ verified, 3 ✓ attested, 11 ◐, 0 ✗, 0 ✗ conflict, 4 ?, 0 N/A. Reaching `ready` needs the runtime profile first.
- **Open questions count:** 1 high / 4 medium / 1 low
- **Top 5 open questions:**
  1. No runtime profile: items 5, 7, 8, 9 are `?`; items 2, 16, 18, 19, 25 cannot be cross-checked (HIGH-1)
  2. Restore test is operator-stated, not attested (item 24) (MED-1)
  3. Runbook, postmortem and rollback links not yet opened (items 13, 14, 17) (MED-2)
  4. Stripe contract owner and PII scope need confirmation (items 21, 22) (MED-3)
  5. alice's console read access to Secrets Manager should be revoked after handoff (MED-4)

## What this package contains

| File | What it is |
|---|---|
| `service-catalog.md` | Snapshot of the `service-discovery` catalog — what exists, owner and live check per row, secret references, dependency graph. |
| `interview-questionnaire.md` | Filled-in outgoing-team interview — tribal knowledge that doesn't live in code. |
| `readiness-scorecard.md` | Production Readiness Review scorecard — 25 items, each ✓ verified / ✓ attested / ◐ operator-stated / ✗ / ✗ conflict / ? / N/A with a cited source. |
| `open-questions.md` | Consolidated unresolved questions across all artifacts, prioritized. |
| `execution-plan.md` | Record of how this package was assembled (Step 1.5 audit, actions, Step 6 batch). |
| `state.md` | Workflow state — steps, same-target checks, probe results, gate sign-offs. |

## First-day actions for Platform Team

- [ ] Read this README in full.
- [ ] Read HIGH-1: run runtime-trace and resume at Step 4 before relying on this scorecard.
- [ ] Open the runbook, postmortem and rollback links; subscribe to the 5 alerts in Section 5.
- [ ] Request that alice's console Secrets Manager read access be revoked after handoff.
- [ ] Verify your team's IAM identities have console + CLI access to AWS account **123456789012** in region **us-east-1**.

## Standards this package follows

- **Production Readiness Review (PRR)** — Google SRE book, Ch. 32. Source of the 8-category scorecard structure.
- **Four golden signals** — Google SRE book, Ch. 6. Underlies the runtime-profile activity baselines.
- **ITIL 4 Service Transition** — formal-handoff framework.
- **AWS Well-Architected Framework — Operational Excellence pillar (OPS-3 to OPS-7).**
- **DORA metrics** (Accelerate) — deploy frequency, lead time, MTTR, change failure rate; interview Sections 4 and 6.

## How this package was generated

This package was assembled by the `service-takeover` skill (culiops plugin, version 0.6.0). The skill orchestrated an operator through these gates:

1. **Gate 1 — Intake** — gathered scoping primitives.
2. **Gate 1.5 — Information audit** — surveyed available materials, probed identity, proposed the cheapest action per gap.
3. **Gates 2–3 — Discovery** — one delegation to `service-discovery` (real-discovery from the diagrams and live APIs); snapshot validated with a same-target check.
4. **Gate 4 — Runtime profile** — skipped by operator choice at Gate 1.5 (time constraint); no `runtime-profile.md` in this package.
5. **Gate 5 — Interview** — emitted questionnaire, ingested filled version.
6. **Gate 6 — Readiness scorecard** — marked items from prior artifacts; ran an approved read-only verification batch and recorded derived facts only.
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

- The skill source: `skills/service-takeover/SKILL.md` in the culiops-skills repo.
- The `state.md` file in this directory for the audit trail.
