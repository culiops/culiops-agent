---
handoff-package-schema: 1
service-takeover-version: 0.6.0
service: payments
account: "123456789012"
region: us-east-1
generated-at: 2026-05-12T10:05:00Z
outgoing-team: Pay Team
incoming-team: Platform Team
---

# Service Takeover — payments

> **Private repo only.** This package holds the account ID, IAM ARNs, escalation chains and incident detail. Record references (where a secret lives, who owns it), never values. No tokens/signed links in URLs. Prefer role/team aliases over personal phone numbers. Check the repo is private before committing.

## TL;DR

- **Handoff date:** 2026-06-15
- **From:** Pay Team (Bob L. — bob@example.com, Carol P. — carol@example.com)
- **To:** Platform Team
- **Readiness verdict:** partial — no item fails outright; items 10 (an alarm named in the interview does not exist) and 19 (unexplained queue sender) are conflicts outside the not-ready categories, and 6 items are operator-stated (`◐`). 14 ✓ verified, 3 ✓ attested, 6 ◐, 0 ✗, 2 ✗ conflict, 0 ?, 0 N/A.
- **Open questions count:** 2 high / 6 medium / 3 low
- **Top 5 open questions:**
  1. Alarm `payments-latency-p99` is named in the interview but not in the account (item 10 conflict) (HIGH-1)
  2. `legacy-orders-exec` may send to `payments-capture-queue` but is not a listed caller (item 19 conflict) (HIGH-2)
  3. Restore test is operator-stated, not attested (item 24) (MED-1)
  4. Runbook, postmortem and rollback links not yet opened (items 13, 14, 17) (MED-2)
  5. Stripe contract owner and PII scope need confirmation (items 21, 22) (MED-3)

## What this package contains

| File | What it is |
|---|---|
| `service-catalog.md` | Snapshot of the `service-discovery` catalog — what exists, owner and live check per row, secret references, dependency graph. |
| `runtime-profile.md` | Snapshot of the `runtime-trace` runtime profile (schema 2) — tag-attributed spend, who managed it (management events), what is wired to call it, activity baselines, cross-Region footprint. |
| `interview-questionnaire.md` | Filled-in outgoing-team interview — tribal knowledge that doesn't live in code. |
| `readiness-scorecard.md` | Production Readiness Review scorecard — 25 items, each ✓ verified / ✓ attested / ◐ operator-stated / ✗ / ✗ conflict / ? / N/A with a cited source. |
| `open-questions.md` | Consolidated unresolved questions across all artifacts, prioritized. |
| `execution-plan.md` | Record of how this package was assembled (Step 1.5 audit, actions, Step 6 batch). |
| `state.md` | Workflow state — steps, same-target checks, probe results, gate sign-offs. |

## First-day actions for Platform Team

- [ ] Read this README in full.
- [ ] Read HIGH-1 and HIGH-2 first (both are interview-vs-artifact conflicts).
- [ ] Open the runbook, postmortem and rollback links; subscribe to the 4 alarms that exist and ask where the p99 latency alarm went.
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
4. **Gate 4 — Runtime profile** — delegated to `runtime-trace` (its own 7 gates: 1, 1a, 2–6).
5. **Gate 5 — Interview** — emitted questionnaire, ingested filled version.
6. **Gate 6 — Readiness scorecard** — marked items from prior artifacts; ran an approved read-only verification batch and recorded derived facts only.
7. **Gate 7 — Handoff package** — assembled this directory.

The run was paused at Gate 4 on 2026-05-05 and resumed on 2026-05-12 (see `state.md`).

To reproduce this package, see `state.md` for the gate sign-offs and `execution-plan.md` for the actions taken.

## What this package does NOT contain

- **Cost optimization recommendations.** Use `cloud-cost-investigate` after takeover if needed.
- **Generated IaC.** Use `terraform import` blocks if you need to bring unmanaged resources under Terraform.
- **Real-time monitoring.** Subscribe to alerts and dashboards listed in the interview.
- **Trace data (X-Ray / OTel).** Out of scope for `runtime-trace`.

## Committing this package

The package is sensitive. Before committing, check the current branch and the remote's visibility (`git branch --show-current`, `git remote -v`, and the host's repo-visibility setting). Commit only to a private repo, never to a public one. If the package may be shared outside the incoming team, review every file; `--redact` on `runtime-trace` covers the runtime profile only.

## Questions about this package itself

- The skill source: `skills/service-takeover/SKILL.md` in the culiops-agent repo.
- The `state.md` file in this directory for the audit trail.
