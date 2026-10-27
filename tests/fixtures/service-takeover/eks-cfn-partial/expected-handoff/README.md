---
handoff-package-schema: 1
service-takeover-version: 0.6.0
service: search-api
account: "123456789012"
region: eu-west-1
generated-at: 2026-05-12T16:00:00Z
outgoing-team: Search Team
incoming-team: Platform Team
---

# Service Takeover — search-api

> **Private repo only.** This package holds the account ID, IAM ARNs, escalation chains and incident detail. Record references (where a secret lives, who owns it), never values. No tokens/signed links in URLs. Prefer role/team aliases over personal phone numbers. Check the repo is private before committing.

## TL;DR

- **Handoff date:** 2026-06-22
- **From:** Search Team (Lena M. — lena@example.com, Omar T. — omar@example.com)
- **To:** Platform Team
- **Readiness verdict:** partial — nothing fails; 3 items are `?` (7, 8, 9: the in-cluster Deployment has no baseline, no deploy history and no audit-log query) and 10 are `◐`. 9 ✓ verified, 3 ✓ attested, 10 ◐, 0 ✗, 0 ✗ conflict, 3 ?, 0 N/A. Evidence as of 2026-05-12T13:35:00Z. Five AWS resources are CloudFormation-owned; EKS in-cluster workloads are not traced.
- **Open questions count:** 0 high / 6 medium / 1 low
- **Top 5 open questions:**
  1. The in-cluster Deployment has no evidence: no deploy history, baseline or audit-log query (items 7, 8, 9 `?`; items 16, 18 unverifiable) (MED-1)
  2. Alarm and alert-rule coverage is incomplete (item 10 `◐`) (MED-2)
  3. Deploy role and Kubernetes access are unverified (items 2, 15, 16) (MED-3)
  4. External API ownership has no record (item 21 `◐`) (MED-4)
  5. ALB clients are interview-stated only (item 19) (MED-5)

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
- [ ] Read MED-1: get `helm history` before relying on the deploy-frequency answer.
- [ ] Read LOW-1: the data layer is CloudFormation-owned; get the templates and the change-set process.
- [ ] Confirm your EKS access entry and RBAC (item 15) with `kubectl auth can-i`.
- [ ] Subscribe to the 4 alerts in Section 5; read the landmines in Section 7.
- [ ] Verify your team's IAM identities have console + CLI access to AWS account **123456789012** in region **eu-west-1** (and `kubectl` access to context **platform-eks**, namespace **search**).

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
