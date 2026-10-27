---
name: service-takeover
description: Use when the user wants to take over an AWS service from another team — especially when there's no documentation, no infrastructure-as-code, and only diagram images. Triggers include "service takeover", "handoff service X", "we're taking over service from team Y", "I need to onboard onto service X". Orchestrator skill that guides the operator through eight gates: intake, information audit, discovery (delegates to service-discovery), catalog verification, runtime profile (delegates to runtime-trace), outgoing-team interview (doc-driven async), readiness scorecard (Production Readiness Review style, strict evidence classes), handoff package assembly. Produces a self-contained directory at .culiops/service-takeover/<service>/ that the receiving team can read to be operational on day one. Resumable across multi-day takeover sessions. AWS services; workloads on any Kubernetes cluster (EKS or not) are checked with kubectl and helm, but runtime-trace covers AWS resources only.
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
EVERY READINESS CLAIM MUST CITE EVIDENCE (artifact + line, or a live read-only query).
AN INTERVIEW ANSWER ON A CHECKABLE FACT IS ◐ OPERATOR-STATED, NEVER A PASS.
"READY" ONLY WHEN EVERY ITEM IS VERIFIED, ATTESTED (ITEMS 3/11/12) OR N/A.
EVERY DELEGATED STEP CHECKS FOR EXISTING ARTIFACTS FIRST (use / verify / re-run).

OUT-OF-SCOPE ACTIONS REQUIRE FIVE-FIELD APPROVAL: WHAT / WHY / COST /
BLAST RADIUS / ALTERNATIVES. Verbal "yes" without seeing the five fields is
not approval. (Same pattern as runtime-trace and service-discovery.)
```

- Law 1 (no writes): inherited; transitive across delegated steps. If a sibling skill would require a write API to satisfy a step, that step is out of scope.
- Law 2 (no programmatic invocation): the orchestrator prints the exact sibling-skill invocation as instruction text for the operator. The operator runs the sibling skill, the operator confirms the artifact path, the orchestrator resumes. There is no "auto" path.
- Law 3 (evidence-backed, strict): the readiness scorecard's value is the evidence trail. Marks use the evidence classes in `templates/readiness-scorecard-baseline.md`: `✓ verified` (cited artifact line or live read-only query), `✓ attested` (only for facts no artifact can prove — items 3, 11, 12), `◐ operator-stated` (an interview answer on a checkable fact), `✗`, `✗ conflict` (interview vs artifact disagree), `?`, `N/A`. Any `◐` or `?` caps the verdict at `partial`; any `✗` or `✗ conflict` makes it `not-ready`.
- Law 4 (resumability): the orchestrator always reads `state.md` before proposing actions. It never re-runs completed steps without operator confirmation.

## Constraints (Non-Negotiable)

1. **Artifacts and live evidence are the source of truth; the interview is testimony.** Every readiness item, every handoff-package claim, every action in the audit trail must trace to either: (a) a prior-step artifact (catalog, runtime profile), (b) a cited read-only query result, (c) an interview answer — recorded as `◐ operator-stated` when the fact is checkable, (d) an operator attestation for facts no artifact can prove, or (e) an out-of-scope acknowledgement. Where testimony and evidence disagree, the item is `✗ conflict`, never silently resolved.
2. **No assumptions.** When an artifact is missing, the relevant readiness items are marked `?` (unknown), not auto-passed.
3. **Strict scope per run — one verified target.** One service, one AWS account, one primary region — plus, when workloads run in a cluster, one Kubernetes context and namespace. Every snapshotted artifact is checked against intake (account, region, service) and for age before it is used (Gate 3, Step 4). A mismatch stops the run. Multi-account is out of scope (sibling skills handle their own per-run scope).
4. **No secrets, ever.** Inherited from `service-discovery` and `runtime-trace` — secret-shaped values are never read from any source. The interview questionnaire records *references* to secrets (where they live, who owns them), never values; tokens never appear in URLs. Targeted CLI commands are projected (`--query`) and only the derived fact is recorded — never pasted raw output. Ingest (Step 5b) scans the filled questionnaire for secret-shaped strings and asks before keeping any.
5. **Read-only access only.** The sibling skills list the permissions they need. The Step 1.5 probes and the Step 6 verification batch need their own; they are listed in the baseline ("Permissions for the probes and the batch") and shown to the operator before the batch runs. The skill never asks for write perms.
6. **Operator confirmation at every gate.** Eight gates. None are optional. Optional *batches* (Step 6 verification) are offered at a gate, never skipped silently.
7. **Sibling skill artifacts are consumed read-only.** `service-takeover` never modifies, renames or deletes the catalog or runtime profile — it reads them, snapshots them into the handoff package, and cites them. Earlier snapshots are kept inside the takeover directory as `<name>.<YYYY-MM-DD>.md`.
8. **Out-of-scope actions require five-field approval.** Same pattern as `runtime-trace`.
9. **Evidence citations in the readiness scorecard.** Every mark carries `[evidence: <path>:<line>]` (or `<path>#<heading>` where no line exists), `[query: <command> @ <timestamp>]`, `[docs: <URL> @ <date read>]` (official AWS / Kubernetes documentation read in this session, for what a setting or metric means), or `[attested: <note>]`. No bare mark without provenance. Recalled behaviour is not evidence. **Source order.** Prefer what the installed tool reports for this target (`plan:` / `live:`: `terraform plan`, `terraform providers schema -json`, `kubectl explain`, the CLI's own help), because it matches the versions in use. Next is official documentation for the version in use (provider lock file, chart version, cluster version), read in this session and cited as `docs: <URL>` with the date and the sentence relied on. Recall comes last: it may say where to look, but it is `UNVERIFIED` and never decides a mark or the verdict. Look things up only for claims that drive a decision; keep the URL, date and quote, not the page.

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
| "I'll generate a runbook section from the runtime profile's no-activity callout" | STOP — `service-takeover` does not generate runbooks or recommendations. Runbook items go in the interview as questions; if no runbook exists, the readiness scorecard flags the gap. |
| "The interview says alarms/backups/deploy access exist, so the item passes" | STOP — that's `◐ operator-stated`. Offer the Step 6 verification check; only its result can make it `✓ verified`. |
| "The interview and the runtime profile disagree, I'll go with the interview — they know the service" | STOP — mark `✗ conflict`, cite both, raise it as a High open question. |
| "The interview says there are no external APIs / no PII / no incidents, so the item is N/A" | STOP — that is testimony. `N/A` needs a cited artifact or record; an interview statement alone is `◐`. |
| "CloudTrail shows no deploys, so the stated deploy frequency is wrong" | STOP — CI and GitOps deploys may not appear as API calls by a person's role. Use the evidence source that matches the delivery model; a source that cannot see the deploys gives `?`, never `✗ conflict`. |
| "Most items pass, so the verdict is ready" | STOP — the verdict is strict: any `✗` or `✗ conflict` in any category → `not-ready`; otherwise any `◐` or `?` → `partial`. |
| "The catalog and the runtime profile are both for 'payments', good enough" | STOP — compare account, region and service from each artifact's stamp/frontmatter with intake. Different environment = stop. |
| "The handoff package is large, I'll symlink the catalog instead of copying" | STOP — package must be self-contained. Copy, never symlink. |

## Workflow & Gates

Eight gates, none optional, each requires explicit operator confirmation.

```
Gate 1:   Intake                 → scoping primitives, intent, audience, available materials
Gate 1.5: Information audit      → identity probe, inventory have/need, propose action per gap, approve plan
Gate 2:   Discovery              → one delegation to service-discovery (IaC path + Step 2V, or real-discovery)
Gate 3:   Catalog verification   → same-target + freshness check, live-verification status, snapshot
Gate 4:   Runtime profile        → delegate to runtime-trace; same-target check; snapshot
Gate 5:   Interview              → emit questionnaire; operator fills async; skill ingests (secret scan)
Gate 6:   Readiness scorecard    → evidence classes, conflict check, optional verification batch, strict verdict
Gate 7:   Handoff package        → assemble README + snapshots + interview + scorecard
                                    (the final write step; package is committed-or-not by operator)
```

### Step 1 — Intake (Gate 1)

Skill prompts for and the operator supplies:

- **Service name** (free text, used in output directory).
- **AWS account ID** + **primary region**.
- **Kubernetes** (only if workloads run in a cluster): cluster, context name, namespace(s).
- **Delivery model** — how changes reach production: applied by a person (IAM role or kubeconfig), a CI/CD pipeline (on merge or on trigger), or a GitOps controller in the cluster. Free text; the interview (Section 4) and the IaC or controller files confirm it. It decides which evidence the Deploy & Rollback items use.
- **Intent category** (structured): `takeover` is the default and primary use case. Other categories (`drift-check`, `post-incident`, `pre-cost-opt`) are valid invocation triggers but produce a leaner output (no full interview). All 25 items are still marked: the items the missing interview would have answered are `?`, so a lean run's verdict is at most `partial`.
- **Intent context** (free text, mandatory): why this run, when the handoff is scheduled, who it's for.
- **Available materials**: which inputs the operator already has:
  - Diagram images (paths)
  - IaC repo (path, if any — usually none in takeover scenarios)
  - Existing `service-discovery` catalog (path, if any)
  - Existing `runtime-trace` runtime profile (path, if any)
  - Outgoing team contact info (free text, for the interview header)
- **Outgoing team** (free text): which team is handing off, primary contact person. If there is no outgoing team or nobody can answer (orphaned or vendor-run service), say so: Gate 5 records no respondent, its sections stay empty and the items that depend on them are `?`. The skill does not fill them in.
- **Incoming team** (free text): who the receiver is — appears in the handoff README.

If the operator is re-invoking on an existing `<service>` (state file exists at `.culiops/service-takeover/<service>/state.md`), the skill reads the state file first and resumes from the current step. Re-invocation skips intake fields that were captured in the initial run unless the operator explicitly resets them.

### Step 1.5 — Information audit + execution plan (Gate 1.5)

The new gate, sitting between intake and the first delegated step. Without this gate, the orchestrator would blindly run sibling skills even when their artifacts already exist or when targeted CLI commands would suffice.

Skill produces `.culiops/service-takeover/<service>/execution-plan.md` with a table:

| Need | What we have | Gap | Proposed action | Cost | Approval |
|---|---|---|---|---|---|
| Architecture understanding | 2 diagram PNGs at `<path>` | — | input to Step 2 (real-discovery reads them) | $0 | auto |
| Resource enumeration from IaC | none | full | none — IaC unavailable; Step 2 uses real-discovery | $0 | auto |
| Live resource enumeration | none | full | run `service-discovery` real-discovery mode | priced at its own cost gate | needed |
| Cross-region inventory | none | full | covered by runtime-trace (Resource Explorer) | $0 | covered |
| Activity baseline | none | full | run `runtime-trace` | priced at its own cost gate | needed |
| Target identity | intake says `123456789012` / `us-east-1` | unverified | run `aws sts get-caller-identity --profile <p> --query Account` and `aws configure get region --profile <p>` | $0 | needed |
| Target identity (Kubernetes) | intake says context `<ctx>` / namespace `<ns>` | unverified | run `kubectl config current-context` and `kubectl get namespace <ns> -o name`; if the catalog names a cluster, confirm the context points at it | not priced (cluster API read) | needed |
| CloudTrail Event history | unknown | unknown | run `aws cloudtrail lookup-events --max-results 1 --profile <p> --region us-east-1 --query 'Events[0].EventTime'` (Event history needs no trail) | $0 | needed |
| Tag scoping | tag `service=payments` supplied | — | proceed | $0 | auto |
| Existing service-discovery catalog | none | full | covered above | — | — |
| Existing runtime-trace profile | none | full | covered above | — | — |

**Cost column.** A sibling-skill row is priced at that skill's own cost gate. A targeted command shows `$0` only when official documentation read in this session says the call is free (`docs: <URL>`); otherwise write `unknown`. Read-only does not mean free — the Cost Explorer API, for one, bills per request.

**Action types the orchestrator may propose:**

1. **Run a sibling skill** — full invocation, operator runs the sibling, brings the artifact path back. Skill prints the exact invocation string.
2. **Run a targeted CLI command** — specific read-only AWS CLI calls when the gap is small enough that a full sibling run is overkill (e.g., one capability probe). Skill emits the exact `aws` command, always with `--profile`/`--region` and a `--query` projection that returns only the fact needed; operator runs it and pastes the output back; skill records **only the derived fact** (e.g., "Event history readable: yes, latest event 2026-05-12T09:14Z") with the command and timestamp. Raw pasted output is never written to any file.
3. **Manual operator input** — for tribal-knowledge gaps no CLI can fill (e.g., "who owns this service today?"). Captured in the interview questionnaire.
4. **Accept the gap** — explicitly mark unavailable; the readiness scorecard flags it.
5. **Use existing artifact** — sub-options: use as-is / use with thin-verify re-scan / fresh re-run. The audit shows the artifact's age and target (account/region/service). On re-run, the earlier snapshot is kept in the takeover directory as `<name>.<YYYY-MM-DD>.md` and diffed against the new one (resources added/removed → open questions); the sibling skill's own file is never renamed or deleted.

The operator approves the plan as a whole. Once approved, the plan becomes the authoritative source for what will happen at Steps 2–4. Operator can return to this gate later (re-invocation re-prints the plan) if priorities change.

**Auto-approval rule:** rows tagged `auto` proceed without explicit confirmation because they represent "we already have this; no action." Rows tagged `needed` require approval. Rows tagged `covered` are auto-approved as a side effect of approving their covering row.

### Step 2 — Discovery (Gate 2)

One delegation to `service-discovery`, routed by what intake found:

- **IaC repo supplied** → service-discovery's IaC path, with **Step 2V (live cross-check) accepted**, so the catalog is live-backed.
- **No IaC (diagrams/docs only)** → service-discovery's real-discovery path (documents → live read-only queries in one flow, with its own gates).
- **Only CloudFormation / SAM / Serverless / CDK** → service-discovery recognises them as unsupported and offers real-discovery; accept it. Resources are recorded with `Owner: cloudformation (<stack>)`.

1. Skill prints the exact `service-discovery` invocation (path, service name, instance, the intake account/region/profile and, when workloads run in a cluster, the kube context).
2. Operator runs `service-discovery` end-to-end and returns the catalog path.

If the existing-artifact branch was selected at Step 1.5, skip to Gate 3 with that artifact.

### Step 3 — Catalog verification (Gate 3)

1. **Same target.** Compare the catalog stamp (account, region / kube context, target instance) with intake. Any mismatch → stop and report; never snapshot a catalog of a different environment.
2. **Freshness.** Show the catalog date against the handoff date. Older than 30 days, or this is a resumed run → offer use-as-is / verify / re-run (recorded in `state.md`).
3. **Live status.** Show `Live verification: performed | not performed` (or real-discovery), the count of `not found` / `drift` rows, and the Unattributed list. These feed items 4 and 6.
4. Snapshot to `.culiops/service-takeover/<service>/service-catalog.md` (read-only afterwards). A previous snapshot is kept as `service-catalog.<YYYY-MM-DD>.md` and diffed. State file updated.

### Step 4 — Runtime profile (Gate 4)

1. Skill prints the exact `runtime-trace` invocation with the agreed scoping primitive (a cost-allocation tag where one exists — the only way spend can be attributed), intent category (always `takeover` when invoked from this skill unless operator overrode at Step 1), and the `--redact` flag IF the operator indicated the handoff package may be shared externally.
2. Operator runs `runtime-trace` end-to-end (which has its own 7 gates).
3. When complete, operator provides the runtime-profile path back.
4. **Same target + schema.** Compare the profile frontmatter (`account`, `region`, `service`) with intake; mismatch → stop. Read `runtime-profile-schema`; a schema-1 profile is accepted with a "re-run recommended — older format lacks Wiring and cross-Region verification" open question, and items 5 and 19 are `?`. In-cluster workloads are a recorded gap in the profile ("not traced"): items 7–9 and 19 for them need the Kubernetes checks in the baseline, else `?`.
5. Skill snapshots `<service>-runtime-profile.md` into the takeover directory (earlier snapshot kept dated, as in Step 3). State file updated.

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
5. **Secret scan.** Before snapshotting, scan the filled questionnaire for secret-shaped strings (keys, tokens, passwords, connection strings, signed URLs). Show any hits and ask the operator to replace them with references; never keep a value.
6. Snapshots the filled questionnaire into the takeover directory (the file IS already in the takeover directory by convention, so this is effectively just a state marker).

The skill never asks for follow-up answers itself — the source of this knowledge is the outgoing team, not the operator typing in chat.

### Step 6 — Readiness scorecard (Gate 6)

Mark every item from evidence using the classes, rules and verification checks in [`templates/readiness-scorecard-baseline.md`](templates/readiness-scorecard-baseline.md) — that file is authoritative. The output is `.culiops/service-takeover/<service>/readiness-scorecard.md`.

#### Baseline checklist — 25 items across 8 categories

| Category | Items |
|---|---|
| **Access** | (1) operator has IAM read in target account; (2) deploy role identified; (3) console+CLI access verified |
| **Inventory** | (4) resources enumerated; (5) cross-region footprint known; (6) secrets/credentials references catalogued |
| **Runtime** | (7) activity baseline captured; (8) deploy events history captured; (9) managing principals enumerated (management events) |
| **Alerting** | (10) critical metrics have alarms; (11) on-call rotation configured; (12) paging path verified |
| **Runbooks** | (13) top runbooks exist (≥3); (14) recent incidents documented |
| **Deploy & Rollback** | (15) CI/CD access; (16) deploy process documented; (17) rollback path documented; (18) deploy frequency known (DORA) |
| **Dependencies** | (19) upstream callers identified; (20) downstream services identified; (21) external API ownership known |
| **Compliance** | (22) PII handling known; (23) data retention policy known; (24) backups configured and restore tested; (25) DR plan exists |

#### Marking rules (summary — the baseline is authoritative)

1. **Evidence classes.** `✓ verified` (cited artifact line or live read-only query) · `✓ attested` (items 3, 11, 12 only) · `◐ operator-stated` (interview answer on a checkable fact) · `✗` · `✗ conflict` · `?` · `N/A`. A non-empty interview answer is at most `◐`; empty is `?`, never `✗`. `N/A` needs a cited artifact or record that says the item does not apply; an interview statement alone is `◐`.
2. **Artifact items (1, 4–9)** come from `state.md`, the catalog and the runtime profile, read with their current schemas: item 1 needs a permission-requiring read to have succeeded, not only the identity probe; items 4 and 7 need coverage of every compute and data-store resource, not one row; item 4/6 count only attributed rows and need a live-backed catalog for `✓ verified`; item 5 needs the runtime profile's cross-Region verification to have passed ("not verifiable" → `?`); item 9 is management principals only. Workloads in a cluster use the Kubernetes checks in the baseline.
3. **Conflict check.** Every interview answer with an artifact counterpart is compared (deploy frequency vs change events, upstream callers vs Wiring, downstream vs dependency graph, DR regions vs Cross-Region Footprint, secrets vs catalog references, backups vs catalog config). Disagreement → `✗ conflict`, both sources cited, High open question.
4. **Step 6 verification batch (optional, offered by default).** For each `◐` item with a verification check (10, 15, 18–20, 23–25), the skill proposes the read-only projected command (`--profile`/`--region` pinned, identity re-checked). On approval the results are recorded as `[query: … @ …]` and move items to `✓ verified`, `✗` or `✗ conflict`. Skipped → items stay `◐`. The baseline gives the Kubernetes equivalent where one exists and lists the read-only permissions the batch needs.
5. **Verdict (strict).** `ready` only if every item (and every operator-supplied extra) is `✓ verified`, `✓ attested` or `N/A`. Any `✗` or `✗ conflict` in any category → `not-ready`. Otherwise → `partial`. Pass rates are shown per category but never decide the verdict.
6. **Priority and order.** Open questions rank High = every `✗` and `✗ conflict`; Medium = every `?` and `◐`; Low = notes on `✓` items. Within a level, the cheapest resolution first (a Step 6 check, then a document to open, then an outgoing-team follow-up). Each entry names its item number and mark. The README's top 5 is the first five.
7. **Evidence as of.** The verdict states the oldest timestamp behind any `✓`. At Gate 7, if the handoff date is more than the team's freshness window (default 7 days) after that, offer to re-run the Step 6 checks before assembling the package.

#### Output structure

```markdown
# Readiness Scorecard — <service>

## Verdict
- Overall: <ready / not-ready / partial> — strict rule (any ✗ or ✗ conflict → not-ready; otherwise any ◐ or ? → partial). Evidence as of <oldest timestamp behind any ✓>.
- Counts: <n> verified · <n> attested · <n> operator-stated · <n> ✗ · <n> conflict · <n> unknown · <n> N/A.
- Blocking items: <every ✗ / ✗ conflict first, then every ? and ◐, in the priority order of rule 6>.
- To reach ready: <n> verification checks available (listed under each ◐ item).

## Per-category summary
| Category | Verified | Attested | Stated | Fail | Conflict | Unknown | N/A |
|---|---|---|---|---|---|---|---|

## Per-item detail
For each of 25 items:
| # | Item | Mark | Evidence | Verification check (if ◐) | Operator note |
|---|---|---|---|---|---|

## Open questions (auto-extracted from ? items)
- (e.g., "Rollback path: not yet verified — operator to test before sign-off")

## Verification batch
- Each command run, its timestamp, the derived fact, and the item(s) it moved.

## Manual override log
- For each override: timestamp, item #, old mark → new mark, reason. An override that clears a `✗`, `✗ conflict` or `◐` needs the artifact or query that resolves it, not a reason alone.
```

#### Optional extras

Operator may supply `.culiops/service-takeover/<service>/extra-checklist.md` with additional items, parsed and merged into the scorecard alongside the baseline. Extras use the same evidence classes and coexist as a separate section ("Operator-supplied extras"), and the same verdict rule counts them: an extra that is `✗` makes the verdict `not-ready`, one that is `◐` or `?` keeps it `partial`. This is how a team adds its own requirements.

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
- Readiness verdict: <ready / not-ready / partial> (strict; see scorecard for blocking items and the checks that would reach ready), evidence as of <timestamp>
- Top 5 open questions:
  1. ...

## What this package contains
- service-catalog.md — what resources exist
- runtime-profile.md — what it costs (attributed only if tag-scoped), who managed it, what is wired to call it, activity baselines, cross-region footprint
- interview-questionnaire.md — tribal knowledge from <outgoing team>
- readiness-scorecard.md — Production Readiness Review results
- open-questions.md — every unresolved item, prioritized

## First-day actions for <incoming team>
- Read readiness-scorecard.md verdict and gaps
- Schedule follow-up with <outgoing-team contact> on top 3 open questions
- Verify console + CLI access in account <id> (and cluster access to <context>/<namespace> if workloads run in a cluster)
- Run the pending verification checks listed in readiness-scorecard.md
- Subscribe to existing alerts (see interview Section 5)

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
- Each snapshot retains the source artifact's schema version in its own frontmatter (copied as-is). The orchestrator reads `runtime-profile-schema` (current: 2) and the catalog stamp to decide which rules apply.

#### Reminder

After writing all files, the skill prints:

> Handoff package complete at `.culiops/service-takeover/<service>/`. It contains account IDs, IAM ARNs, people/team contacts, incident and compliance detail — **commit it only to a private repo.** The skill does NOT auto-commit. Recommended commit message: `service-takeover: handoff package for <service> from <outgoing-team>`.

Before printing, the skill shows the current branch (warns if it is the default branch) and the output of `git remote -v`, and warns if the remote is or may be public. If the package must be shared outside the team, all artifacts need redaction — not only the runtime profile's `--redact` export.

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
│   ├── interview-questionnaire.md        ← v1 questionnaire template (11 sections)
│   ├── readiness-scorecard-baseline.md   ← 25-item baseline checklist with auto-mark rules
│   └── handoff-readme-template.md        ← README.md template for the handoff package
└── examples/
    ├── execution-plan-example.md         ← example Step 1.5 output
    └── auto-mark-rules.md                ← per-item auto-mark logic reference
```

No `examples/aws/` directory — `service-takeover` doesn't have per-resource definitions of its own. Resource type coverage is inherited from `service-discovery` (AWS + Kubernetes) and `runtime-trace` (per-AWS-resource; in-cluster workloads, on EKS or any other cluster, are a recorded gap).

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
   - `happy-path` — full run; the Step 6 verification batch finds the incoming deploy role missing (item 15 `✗`) and the interview's DR and deploy-frequency claims conflict with artifacts → `not-ready`.
   - `partial-interview` — operator chose to proceed despite empty SLO/DR sections; verify readiness scorecard correctly marks them as `?`; its one `✗ conflict` still makes the verdict `not-ready`.
   - `existing-stale-catalog` — execution plan offers verify path; operator chooses re-run; old snapshot kept as `service-catalog.<date>.md` and diffed.
   - `runtime-trace-skipped` — operator chose to skip runtime-trace; scorecard's Runtime category goes to `?`.
   - `interactive-resume` — Day 1 stops at Gate 3; Day 7 re-invokes; the catalog's age is shown and the operator chooses use-as-is; state file resumes from Step 4.
   - `eks-cfn-partial` — EKS service with CloudFormation-owned resources and unattributable spend; the in-cluster workloads give three `?` and several `◐`, nothing fails → exactly `partial`.

## Versioning

- Skill version in this file's frontmatter (`service-takeover-version`).
- `state.md` carries the skill version at the top of its frontmatter, stamped at run start.
- Handoff package's `README.md` declares `handoff-package-schema: 1` at the top. Bumped only on breaking structural changes (e.g., renaming `readiness-scorecard.md` to a different filename, or restructuring the README sections such that downstream parsers break).
- Snapshots retain the source artifact's own schema version in their frontmatter — `service-catalog.md` keeps `service-discovery-schema: <N>`, `runtime-profile.md` keeps its `runtime-profile-schema: <N>`. The orchestrator never rewrites snapshot frontmatter.

## Out of Scope for v1

Documented explicitly so future maintainers don't extend the skill into these areas without a fresh design pass:

- **Programmatic sibling-skill invocation.** Skill orchestrates the operator, not other skills.
- **Cost recommendations.** Downstream `cloud-cost-investigate`, operator-invoked.
- **IaC generation / state import.**
- **Other clouds.** Not supported (multi-cloud content archived at tag `archive/multi-cloud-v0.10.0`).
- **Multi-account.** Single account per run.
- **Auto-commit.** Operator decides.
- **Sign-off automation.** Skill produces evidence; the "done" judgment is the operator's.
- **Custom auto-mark rules.** v1 ships fixed rules. If a team needs different rules, they fork the template; the skill does not load arbitrary user-supplied rule files.
- **Real-time interview** (interactive chat-based Q&A with the operator typing answers). The interview is async by design — the source is the outgoing team, not the operator.
