---
name: service-takeover
description: Use when the user wants to take over an AWS service from another team — especially when there's no documentation, no infrastructure-as-code, and only diagram images. Triggers include "service takeover", "handoff service X", "we're taking over service from team Y", "I need to onboard onto service X". Orchestrator skill that guides the operator through eight gates: intake, information audit, diagram extraction (delegates to service-discovery), live resource discovery (delegates to service-discovery), runtime profile (delegates to runtime-trace), outgoing-team interview (doc-driven async), readiness scorecard (Production Readiness Review style, evidence-backed), handoff package assembly. Produces a self-contained directory at .culiops/service-takeover/<service>/ that the receiving team can read to be operational on day one. Resumable across multi-day takeover sessions. AWS only in v1.
---

# Service Takeover

Guide an operator through the structured handoff of an AWS service from another team. Built for the worst-case takeover: **no documentation, no IaC, only diagram images, and a deadline.**

This skill **orchestrates the operator, not other skills.** When a step delegates to `service-discovery` or `runtime-trace`, the orchestrator prints the exact invocation the operator should run. The operator runs the sibling skill themselves (which preserves the sibling's own Iron Law, gate model, and IAM scope), then returns the artifact path to `service-takeover`, which snapshots it into the handoff package and continues.

The skill produces a **self-contained handoff package** at `.culiops/service-takeover/<service>/`:

- `README.md` — handoff summary the receiving team reads first.
- `state.md` — workflow state (which steps ran, when, gate sign-offs).
- `execution-plan.md` — the Step 1.5 audit + plan + approval record.
- `service-catalog.md` — snapshot of the `service-discovery` catalog.
- `runtime-profile.md` — snapshot of the `runtime-trace` runtime profile.
- `interview-questionnaire.md` — filled-in outgoing-team interview.
- `readiness-scorecard.md` — evidence-backed Production Readiness Review scorecard.
- `open-questions.md` — consolidated open questions across all artifacts.

The receiving team gets one directory they can read to be operational on day one.

## References

| Reference | What it informs |
|---|---|
| **Site Reliability Engineering** (Google) — Ch. 32 "The Evolving SRE Engagement Model" | The Production Readiness Review (PRR) pattern. Direct basis for Step 6 (readiness scorecard) and the 8-category structure (access, inventory, runtime, alerting, runbooks, deploy & rollback, dependencies, compliance). |
| **Site Reliability Engineering** — Ch. 6 "Monitoring Distributed Systems" | The four golden signals (traffic, latency, errors, saturation). Cross-referenced when consuming runtime-trace's activity baselines into the readiness scorecard. |
| **Working Effectively with Legacy Code** (Feathers) | "Characterization, not assumption." Justifies the "every readiness claim cites evidence" discipline. The skill never guesses at facts; it cites the artifact or marks the item unknown. |
| **Seeking SRE** (Blank-Edelman, ed.) — chapters on inheriting opaque systems | Patterns for the outgoing-team interview (Step 5) — structured, async-friendly, knowledge-transfer-oriented. |
| **The DevOps Handbook** (Kim, Humble, Debois, Willis) — Part IV "The Technical Practices of Feedback" | Operational ownership and the formal-handoff pattern. Justifies the readiness items around deploy paths, rollback procedures, and incident response. |
| **Accelerate** (Forsgren, Humble, Kim) | The four DORA metrics (deploy frequency, lead time for changes, mean time to restore, change failure rate). Frames the readiness "Deploy & Rollback" category. |
| **AWS Well-Architected Framework** — Operational Excellence pillar (OPS-3 through OPS-7) | The structured questions "How do you understand the health of your workload?" and "How do you mitigate deployment risks?" — direct sources for readiness items. |
| **ITIL 4 — Service Transition practices** | The formal-handoff framework: knowledge management, configuration management, change enablement. Justifies the handoff-package structure (catalog + profile + interview + scorecard + open questions). |
| **The Pragmatic Programmer** (Hunt, Thomas) — "Tracer Bullets" chapter | The thin-probe-first pattern. Justifies the information-audit gate (Step 1.5) — probe what we have, fire a thin action per gap, before committing to a full sibling-skill run. |
| **Observability Engineering** (Majors, Fong-Jones, Miranda) | The high-cardinality / slice-retroactively framing. Carries through from `runtime-trace`. |

## Workflow-to-Standards Mapping

| Step | Industry pattern | Authority |
|---|---|---|
| 1. Intake | ITIL Service Transition — Knowledge Management input | ITIL 4 |
| 1.5. Information audit | "Tracer Bullets" — thin-probe-first | Pragmatic Programmer |
| 2–3. Discovery | Characterization (applied to infrastructure) | Feathers (adapted) |
| 4. Runtime profile | Four golden signals + control-plane characterization | SRE book Ch. 6; Observability Engineering |
| 5. Interview | Async structured knowledge transfer | Seeking SRE; ITIL knowledge transfer |
| 6. Readiness | Production Readiness Review (PRR) | SRE book Ch. 32 |
| 7. Handoff package | ITIL Service Transition — configuration item handover | ITIL 4 |

## The Iron Law

```
NO WRITE API CALLS. EVER.
ALL CLOUD QUERIES READ-ONLY (delegated to sibling skills' own Iron Laws).
NEVER INVOKE SIBLING SKILLS PROGRAMMATICALLY. THE OPERATOR RUNS THEM.
NO COMMAND, NO QUERY, NO INTERVIEW INGESTION WITHOUT OPERATOR APPROVAL.
EVERY READINESS CLAIM MUST CITE EVIDENCE (artifact + line) OR BE MARKED MANUAL.
EVERY DELEGATED STEP CHECKS FOR EXISTING ARTIFACTS FIRST (use / verify / re-run).

OUT-OF-SCOPE ACTIONS REQUIRE FIVE-FIELD APPROVAL: WHAT / WHY / COST /
BLAST RADIUS / ALTERNATIVES. Verbal "yes" without seeing the five fields is
not approval. (Same pattern as runtime-trace and service-discovery.)
```

- Law 1 (no writes): inherited; transitive across delegated steps. If a sibling skill would require a write API to satisfy a step, that step is out of scope.
- Law 2 (no programmatic invocation): the orchestrator prints the exact sibling-skill invocation as instruction text for the operator. The operator runs the sibling skill, the operator confirms the artifact path, the orchestrator resumes. There is no "auto" path.
- Law 3 (evidence-backed): the readiness scorecard's value is the evidence trail. Every ✓ / ✗ either auto-marks from a cited artifact line, auto-marks from a cited interview-questionnaire answer, or carries an explicit `[manual]` flag with a one-line operator note.
- Law 4 (resumability): the orchestrator always reads `state.md` before proposing actions. It never re-runs completed steps without operator confirmation.

## Constraints (Non-Negotiable)

1. **Artifacts are the source of truth.** Every readiness item, every handoff-package claim, every action in the audit trail must trace to either: (a) a prior-step artifact (catalog, runtime profile, interview), (b) an operator's explicit manual mark, or (c) an out-of-scope acknowledgement.
2. **No assumptions.** When an artifact is missing, the relevant readiness items are marked `?` (unknown), not auto-passed.
3. **Strict scope per run.** One service, one AWS account, one primary region. Multi-account is out-of-scope for the v1 orchestrator (sibling skills handle their own per-run scope).
4. **No secrets, ever.** Inherited from `service-discovery` and `runtime-trace` — secret-shaped values are never read from any source. The interview questionnaire records *references* to secrets (where they live, who owns them), never values.
5. **Read-only IAM only.** No IAM policy is required by `service-takeover` itself beyond what sibling skills require. The skill never asks for write perms.
6. **Operator confirmation at every gate.** Eight gates (matching the eight steps). None are optional.
7. **Sibling skill artifacts are consumed read-only.** `service-takeover` never modifies the catalog or runtime profile — it reads them, snapshots them into the handoff package, and cites them.
8. **Out-of-scope actions require five-field approval.** Same pattern as `runtime-trace`.
9. **Evidence citations in the readiness scorecard.** Every auto-marked item carries a `[evidence: <path>:<line>]` citation. No bare ✓ or ✗ without provenance.

## Rationalization Prevention

| Thought | Reality |
|---|---|
| "service-discovery already ran in this repo, I'll just use the catalog without asking" | STOP — Step 1.5 checks the catalog's timestamp and presents the operator with use/verify/re-run. Auto-consumption without explicit confirmation is forbidden. |
| "I'll just invoke runtime-trace directly from this skill, it'll be faster" | STOP — programmatic sibling invocation is forbidden by the Iron Law. Print the invocation, wait for the operator. |
| "The interview section on SLOs is empty, I'll mark it 'no SLOs defined'" | STOP — empty means unknown, not negative. Mark `?` and surface as an open question. |
| "This readiness item is obviously true; I'll auto-pass it without citation" | STOP — every auto-mark requires an evidence citation. If no citation exists, the item is `[manual]`. |
| "The catalog says no alerting; the runtime profile doesn't disagree; I'll auto-fail the alerting items" | STOP — absence of evidence is not evidence. Mark `?` and ask the operator. |
| "The operator said 'continue' earlier; I'll skip the next gate" | STOP — each gate is its own confirmation. Earlier "yes" never carries forward. |
| "This out-of-region resource isn't in scope, I'll filter it out" | STOP — every Resource Explorer finding makes it into the handoff. Filtering creates blind spots. |
| "The operator approved the execution plan at Step 1.5; I'll run all delegated steps without re-confirming" | STOP — the plan approval authorizes *what* will be proposed at each step, not the steps themselves. Each delegated step still re-prints the exact invocation and gets approval. |
| "I'll generate a runbook section from the runtime profile's idle-suspect callout" | STOP — `service-takeover` does not generate runbooks. Runbook items go in the interview as questions; if no runbook exists, the readiness scorecard flags the gap. |
| "The handoff package is large, I'll symlink the catalog instead of copying" | STOP — package must be self-contained. Copy, never symlink. |

## Workflow & Gates

Eight gates, none optional, each requires explicit operator confirmation.

```
Gate 1:   Intake                 → scoping primitives, intent, audience, available materials
Gate 1.5: Information audit      → inventory have/need, propose action per gap, approve plan
Gate 2:   Diagram extraction     → delegate to service-discovery (real-discovery mode, images)
Gate 3:   Live discovery         → delegate to service-discovery (real-discovery mode, AWS CLI)
Gate 4:   Runtime profile        → delegate to runtime-trace
Gate 5:   Interview              → emit questionnaire; operator fills async; skill ingests
Gate 6:   Readiness scorecard    → auto-mark from artifacts + operator overrides on gaps
Gate 7:   Handoff package        → assemble README + snapshots + interview + scorecard
                                    (the final write step; package is committed-or-not by operator)
```

### Step 1 — Intake (Gate 1)

Skill prompts for and the operator supplies:

- **Service name** (free text, used in output directory).
- **AWS account ID** + **primary region**.
- **Intent category** (structured): `takeover` is the default and primary use case. Other categories (`drift-check`, `post-incident`, `pre-cost-opt`) are valid invocation triggers but produce a leaner output (smaller scorecard, no full interview).
- **Intent context** (free text, mandatory): why this run, when the handoff is scheduled, who it's for.
- **Available materials**: which inputs the operator already has:
  - Diagram images (paths)
  - IaC repo (path, if any — usually none in takeover scenarios)
  - Existing `service-discovery` catalog (path, if any)
  - Existing `runtime-trace` runtime profile (path, if any)
  - Outgoing team contact info (free text, for the interview header)
- **Outgoing team** (free text): which team is handing off, primary contact person.
- **Incoming team** (free text): who the receiver is — appears in the handoff README.

If the operator is re-invoking on an existing `<service>` (state file exists at `.culiops/service-takeover/<service>/state.md`), the skill reads the state file first and resumes from the current step. Re-invocation skips intake fields that were captured in the initial run unless the operator explicitly resets them.

### Step 1.5 — Information audit + execution plan (Gate 1.5)

The new gate, sitting between intake and the first delegated step. Without this gate, the orchestrator would blindly run sibling skills even when their artifacts already exist or when targeted CLI commands would suffice.

Skill produces `.culiops/service-takeover/<service>/execution-plan.md` with a table:

| Need | What we have | Gap | Proposed action | Cost | Approval |
|---|---|---|---|---|---|
| Architecture understanding | 2 diagram PNGs at `<path>` | — | none — proceed to Step 2 | $0 | auto |
| Resource enumeration from IaC | none | full | none — IaC unavailable; will use real-discovery in Step 3 | $0 | auto |
| Live resource enumeration | none | full | run `service-discovery` real-discovery mode | $0 (read-only) | needed |
| Cross-region inventory | none | full | covered by runtime-trace (Resource Explorer) | $0 | covered |
| Activity baseline | none | full | run `runtime-trace` | ~$0.05 | needed |
| CloudTrail availability | unknown | unknown | run `aws cloudtrail describe-trails --region us-east-1` to probe | $0 | needed |
| Tag scoping | tag `service=payments` supplied | — | proceed | $0 | auto |
| Existing service-discovery catalog | none | full | covered above | — | — |
| Existing runtime-trace profile | none | full | covered above | — | — |

**Action types the orchestrator may propose:**

1. **Run a sibling skill** — full invocation, operator runs the sibling, brings the artifact path back. Skill prints the exact invocation string.
2. **Run a targeted CLI command** — specific read-only AWS CLI calls when the gap is small enough that a full sibling run is overkill (e.g., one capability probe). Skill emits the exact `aws` command; operator pastes the output back; skill ingests.
3. **Manual operator input** — for tribal-knowledge gaps no CLI can fill (e.g., "who owns this service today?"). Captured in the interview questionnaire.
4. **Accept the gap** — explicitly mark unavailable; the readiness scorecard flags it.
5. **Use existing artifact** — sub-options: use as-is / use with thin-verify re-scan / fresh re-run. Old artifact renamed with timestamp suffix on re-run (never deleted).

The operator approves the plan as a whole. Once approved, the plan becomes the authoritative source for what will happen at Steps 2–4. Operator can return to this gate later (re-invocation re-prints the plan) if priorities change.

**Auto-approval rule:** rows tagged `auto` proceed without explicit confirmation because they represent "we already have this; no action." Rows tagged `needed` require approval. Rows tagged `covered` are auto-approved as a side effect of approving their covering row.
