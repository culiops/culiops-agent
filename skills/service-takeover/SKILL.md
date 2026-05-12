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

### Step 2 — Diagram extraction (Gate 2)

If the execution plan included diagram extraction:

1. Skill prints the exact `service-discovery` invocation, including all flags and the expected scoping primitive.
2. Operator runs `service-discovery` in real-discovery mode against the supplied diagrams.
3. When complete, operator provides the catalog path back to `service-takeover`.
4. Skill validates the path exists and is a `service-discovery` catalog (checks for required frontmatter).
5. Skill copies the catalog into the takeover directory as a snapshot: `.culiops/service-takeover/<service>/service-catalog.md` (the snapshot is read-only afterwards).
6. State file updated.

If existing-artifact branch was selected at Step 1.5, this step verifies the artifact path and snapshots it (with optional thin re-scan if "verify" was chosen).

### Step 3 — Live resource discovery (Gate 3)

If the execution plan included live discovery (almost always true in takeover scenarios):

1. Skill prints the exact `service-discovery` invocation for the live-discovery pass (typically distinct from the diagram pass — different inputs, same tool).
2. Operator runs it.
3. Skill validates and snapshots the live-discovery catalog (may be merged with the diagram catalog by `service-discovery` itself; orchestrator does not merge).
4. State file updated.

Some takeover scenarios skip Step 2 (no diagrams supplied) and go straight to Step 3. Some skip Step 3 (offline catalog already exists). Both are valid paths through the orchestrator.

### Step 4 — Runtime profile (Gate 4)

1. Skill prints the exact `runtime-trace` invocation with the agreed scoping primitive, intent category (always `takeover` when invoked from this skill unless operator overrode at Step 1), and the `--redact` flag IF the operator indicated the handoff package may be shared externally.
2. Operator runs `runtime-trace` end-to-end (which has its own 6 gates).
3. When complete, operator provides the runtime-profile path back.
4. Skill snapshots `<service>-runtime-profile.md` into the takeover directory.
5. State file updated.

### Step 5 — Outgoing-team interview (Gate 5)

Doc-driven async interview. The skill emits a structured questionnaire markdown; the operator (and/or the outgoing team) fills it in offline; the skill ingests the filled version.

#### 5a — Emit questionnaire

Skill creates `.culiops/service-takeover/<service>/interview-questionnaire.md` from a v1 template covering eleven sections:

1. **Service overview** — name, business purpose, criticality tier, age, why it exists.
2. **People & ownership** — current owners, on-call schedule, escalation contacts, related teams.
3. **SLOs / SLIs** — defined? measured? error budget tracked? where are dashboards?
4. **Deploy process** — how does code/config reach prod? deploy frequency? rollback procedure? deploy permissions?
5. **Alerting & on-call** — what's monitored? who pages? known noisy alerts? **link to top runbooks if any exist.**
6. **Runbooks & incidents** — list of existing runbooks (paths/links), incidents in last 12 months, post-mortems if any.
7. **Known landmines** — fragile components, "do not touch on Friday" things, undocumented quirks.
8. **Dependencies** — upstream callers (with contacts), downstream services (with SLAs/contracts), external APIs and their owners.
9. **Secrets & credentials** — where are secrets stored, who owns rotation, what services have access (references only, never values).
10. **Compliance, data & disaster recovery** — PII handling, data retention policy, backup strategy and last test date, DR plan and RTO/RPO, regulatory constraints (SOC2 / HIPAA / GDPR if applicable).
11. **Roadmap & open work** — pending changes, in-flight projects, known tech debt, deprecation plans.

Each section has prefilled probing questions with empty answer slots and an explicit `_To be filled in: ___` marker. The questionnaire header includes the outgoing-team contact info, the handoff date, and a one-paragraph context explaining what the interview is for (so the outgoing team can fill it in async without a meeting).

#### 5b — Ingest filled questionnaire

When the operator has the filled-in questionnaire, they return to `service-takeover` and tell it "interview ready at `<path>`" (default path is the emit location, but operator can supply a different path if they renamed/moved it).

Skill ingests:

1. Parses the markdown by section headings.
2. For each section, classifies completion: `complete` (all probing questions have non-trivial answers), `partial` (some answers missing or marked `unknown`/`TBD`), `empty` (no answers).
3. Records completion status to `state.md`.
4. Surfaces partial/empty sections to the operator as a summary table. Operator decides per-section: accept-as-is (will surface in readiness scorecard as gaps) or return-to-outgoing-team (operator goes back to step 5a and re-emits with the current partial answers preserved).
5. Snapshots the filled questionnaire into the takeover directory (the file IS already in the takeover directory by convention, so this is effectively just a state marker).

The skill never asks for follow-up answers itself — the source of this knowledge is the outgoing team, not the operator typing in chat.

### Step 6 — Readiness scorecard (Gate 6)

Auto-mark from prior artifacts; operator overrides on gaps. The output is `.culiops/service-takeover/<service>/readiness-scorecard.md`.

#### Baseline checklist — 25 items across 8 categories

| Category | Items |
|---|---|
| **Access** | (1) operator has IAM read in target account; (2) deploy role identified; (3) console+CLI access verified |
| **Inventory** | (4) resources enumerated; (5) cross-region footprint known; (6) secrets/credentials references catalogued |
| **Runtime** | (7) activity baseline captured; (8) deploy events history captured; (9) principals touching service enumerated |
| **Alerting** | (10) critical metrics have alarms; (11) on-call rotation configured; (12) paging path verified |
| **Runbooks** | (13) top-5 symptom→action runbooks exist; (14) recent incidents documented |
| **Deploy & Rollback** | (15) CI/CD access; (16) deploy process documented; (17) rollback path documented; (18) deploy frequency known (DORA) |
| **Dependencies** | (19) upstream callers identified; (20) downstream services identified; (21) external API ownership known |
| **Compliance** | (22) PII handling known; (23) data retention policy known; (24) backup strategy verified; (25) DR plan exists |

#### Auto-marking rules

Each item is marked **✓** (pass), **✗** (fail), or **?** (unknown) with an evidence citation:

- **Items 1–3 (Access):** Auto-mark ✓ if Step 1.5's execution plan recorded successful AWS access; otherwise ?.
- **Items 4–6 (Inventory):** Auto-mark from `service-catalog.md`. Item 4 ✓ if catalog has ≥1 resource. Item 5 ✓ if catalog includes cross-region data from runtime-trace's Resource Explorer pass. Item 6 ✓ if catalog has a secrets-references section (per `service-discovery`'s spec — secrets are recorded as refs, never values).
- **Items 7–9 (Runtime):** Auto-mark from `runtime-profile.md`. Item 7 ✓ if runtime profile has the Activity Baselines section with at least one resource. Item 8 ✓ if Control-Plane Activity has at least one event. Item 9 ✓ if "principals touching this service" table has at least one row.
- **Items 10–25 (Alerting through Compliance):** Auto-mark from `interview-questionnaire.md` filled sections. Each item has a designated questionnaire section; if the section's answers contain affirmative responses to specific probing questions, auto-mark ✓. If section is partial or empty, mark `?` and prompt operator. If section explicitly states "no runbooks exist" / "no DR plan" / etc., auto-mark ✗.

Items that cannot be auto-marked from any artifact stay `?` and require operator manual mark with a one-line note (`[manual]` flag). Examples: "rollback path tested in last 90 days" — no artifact can prove this; operator must attest.

#### Output structure

```markdown
# Readiness Scorecard — <service>

## Verdict
- Overall: <ready / not-ready / partial> based on category-level pass rates.
- Critical gaps: <list of ✗ or ? items in high-criticality categories>.

## Per-category summary
| Category | Pass | Fail | Unknown | Verdict |
|---|---|---|---|---|

## Per-item detail
For each of 25 items:
| # | Item | Mark | Evidence | Operator note |
|---|---|---|---|---|

## Open questions (auto-extracted from ? items)
- (e.g., "Rollback path: not yet verified — operator to test before sign-off")

## Manual override log
- For each ? → ✓ or ✗ override by operator, record: timestamp, item #, note.
```

#### Optional extras

Operator may supply `.culiops/service-takeover/<service>/extra-checklist.md` with additional items, parsed and merged into the scorecard alongside the baseline. The baseline file is never modified by extras — they coexist as a separate section in the output ("Operator-supplied extras").

### Step 7 — Handoff package (Gate 7)

The final assembly step. Outputs:

```
.culiops/service-takeover/<service>/
├── README.md                       ← the handoff summary (TL;DR + index + open questions)
├── state.md                         ← workflow state (which steps ran, when, paths, gate sign-offs)
├── execution-plan.md                ← Step 1.5 output (the audit + plan + operator approval)
├── service-catalog.md               ← COPY (snapshot) of the service-discovery catalog
├── runtime-profile.md               ← COPY (snapshot) of the runtime-trace profile
├── interview-questionnaire.md       ← filled-in interview (Step 5)
├── readiness-scorecard.md           ← Step 6 output
└── open-questions.md                ← consolidated open questions across all artifacts
```

#### `README.md` — the handoff front door

Self-contained 1–2 page summary; the receiving team should be able to read just this file and know what to do next.

```markdown
# Service Takeover — <service>

## TL;DR
- Handoff date: <date>
- From: <outgoing team>
- To: <incoming team>
- Readiness verdict: <ready / not-ready / partial>
- Top 5 open questions:
  1. ...

## What this package contains
- service-catalog.md — what resources exist
- runtime-profile.md — what's actually running, billing, and being called
- interview-questionnaire.md — tribal knowledge from <outgoing team>
- readiness-scorecard.md — Production Readiness Review results
- open-questions.md — every unresolved item, prioritized

## First-day actions for <incoming team>
- Read readiness-scorecard.md verdict and gaps
- Schedule follow-up with <outgoing-team contact> on top 3 open questions
- Verify console + CLI access in account <id>
- Subscribe to existing alerts (see runbook section of catalog)

## Standards this package follows
- Production Readiness Review (PRR) — SRE book Ch. 32
- Four golden signals — SRE book Ch. 6
- ITIL 4 Service Transition framework
- AWS Well-Architected Operational Excellence pillar
```

#### `open-questions.md` — consolidated cross-artifact

Every "open question" callout across the catalog, runtime profile, interview, and scorecard, deduplicated and prioritized:

```markdown
# Open Questions — <service>

## High priority (blocks operational readiness)
- (from readiness scorecard) Rollback path not verified — operator to test.
- (from runtime profile) Deploy role `arn:...` is shared with which other services?
- (from interview, partial) DR plan section empty — needs outgoing-team follow-up.

## Medium priority (clarifies operational understanding)
- ...

## Low priority (nice to know)
- ...
```

#### `state.md` — workflow record

Maintained throughout the run, finalized at Gate 7:

```markdown
# Service Takeover State — <service>

## Run identity
- Service: <name>
- Account: <id>, region: <region>
- Operator: <IAM principal>
- Initiated: <timestamp>
- Last updated: <timestamp>

## Step status
| Step | Status | Started | Completed | Artifact | Gate approval |
|---|---|---|---|---|---|
| 1   | done | <ts> | <ts> | — | <operator>, <ts> |
| 1.5 | done | <ts> | <ts> | execution-plan.md | <operator>, <ts> |
| 2   | done | <ts> | <ts> | service-catalog.md (snapshot) | <operator>, <ts> |
...

## Audit trail
For each gate approval, each delegated-skill instruction issued, each CLI command emitted:
- Timestamp, action, operator confirmation.
```

#### Versioning

- `service-takeover-version: <x.y.z>` in `state.md` frontmatter.
- `handoff-package-schema: 1` at the top of `README.md` (bumped on breaking structural changes).
- Each snapshot retains the source artifact's schema version in its own frontmatter (we copy the file as-is, so the catalog snapshot keeps `service-discovery-schema: N`, the runtime profile snapshot keeps `runtime-profile-schema: 1`).

#### Reminder

After writing all files, the skill prints:

> Handoff package complete at `.culiops/service-takeover/<service>/`. To make this part of the receiving team's repo, commit the directory. The skill does NOT auto-commit. Recommended commit message: `service-takeover: handoff package for <service> from <outgoing-team>`.

## Resumability — operational model

Re-invoking `service-takeover` on an existing `<service>` (state file exists):

1. Skill reads `state.md` first.
2. Prints current state: which steps are `done`, `in_progress`, `pending`.
3. Asks operator: resume from current step, jump to a specific step, or restart entirely (restart preserves prior artifacts with timestamp suffixes — never deletes).
4. From the chosen step, runs the normal gate flow.

This means a takeover can span weeks. Day 1: intake, audit, run service-discovery. Day 4: come back, run runtime-trace. Day 10: emit interview questionnaire. Day 14: ingest filled interview, run readiness, assemble package.

The skill never silently picks up where it left off — operator always confirms the resume point.

## Skill Structure

```
skills/service-takeover/
├── SKILL.md                              ← main skill definition; References + workflow-to-standards mapping at top
├── templates/
│   ├── interview-questionnaire.md        ← v1 questionnaire template (9 sections)
│   ├── readiness-scorecard-baseline.md   ← 25-item baseline checklist with auto-mark rules
│   └── handoff-readme-template.md        ← README.md template for the handoff package
└── examples/
    ├── execution-plan-example.md         ← example Step 1.5 output
    └── auto-mark-rules.md                ← per-item auto-mark logic reference
```

No `examples/aws/` directory — `service-takeover` doesn't have per-resource definitions of its own. Resource type coverage is inherited from `service-discovery` (cloud-agnostic) and `runtime-trace` (per-AWS-resource).

Fixtures for testing live under `tests/fixtures/service-takeover/<scenario>/`. See Testing below.

## Testing

Three layers, ordered by build effort:

1. **Fixture-driven dry-runs.** Each scenario under `tests/fixtures/service-takeover/<name>/` includes:
   - `input.md` — intake values + available materials.
   - `mock-artifacts/` — simulated outputs from sibling skills (a fake `service-discovery` catalog, a fake `runtime-trace` profile).
   - `filled-interview.md` — a filled-in questionnaire.
   - `expected-handoff/` — expected contents of the final handoff package directory.
   - `DRY-RUN-NOTES.md` — gate-by-gate simulated execution trace.

2. **Live smoke test against a real personal-sandbox service.** Optional, manual, pre-release. Costs sibling skills' costs (under $0.10).

3. **Negative-case fixtures:**
   - `partial-interview` — operator chose to proceed despite empty SLO/DR sections; verify readiness scorecard correctly marks them as ✗ or ?.
   - `no-diagrams` — Step 2 skipped because no diagrams supplied; Step 3 still runs.
   - `existing-stale-catalog` — execution plan offers verify path; operator chooses re-run; old catalog preserved with timestamp.
   - `runtime-trace-skipped` — operator chose to skip runtime-trace (e.g., account doesn't allow it); scorecard's Runtime category goes to ?.
   - `interactive-resume` — Day 1 stops at Step 3; Day 7 re-invokes; state file resumes from Step 4.

## Versioning

- Skill version in this file's frontmatter (`service-takeover-version`).
- `state.md` carries the skill version at the top of its frontmatter, stamped at run start.
- Handoff package's `README.md` declares `handoff-package-schema: 1` at the top. Bumped only on breaking structural changes (e.g., renaming `readiness-scorecard.md` to a different filename, or restructuring the README sections such that downstream parsers break).
- Snapshots retain the source artifact's own schema version in their frontmatter — `service-catalog.md` keeps `service-discovery-schema: <N>`, `runtime-profile.md` keeps `runtime-profile-schema: 1`. The orchestrator never rewrites snapshot frontmatter.

## Out of Scope for v1

Documented explicitly so future maintainers don't extend the skill into these areas without a fresh design pass:

- **Programmatic sibling-skill invocation.** Skill orchestrates the operator, not other skills.
- **Cost recommendations.** Downstream `cloud-cost-investigate`, operator-invoked.
- **IaC generation / state import.**
- **Multi-cloud.** AWS-only for v1.
- **Multi-account.** Single account per run.
- **Auto-commit.** Operator decides.
- **Sign-off automation.** Skill produces evidence; the "done" judgment is the operator's.
- **Custom auto-mark rules.** v1 ships fixed rules. If a team needs different rules, they fork the template; the skill does not load arbitrary user-supplied rule files.
- **Real-time interview** (interactive chat-based Q&A with the operator typing answers). The interview is async by design — the source is the outgoing team, not the operator.
