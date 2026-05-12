# Dry-run notes — partial-interview

## What this fixture validates

This fixture demonstrates the skill's **graceful degradation** path: an outgoing team that fills in only 6 of 11 interview sections. Key behaviors validated:

1. **Section classification at Gate 5.** The skill classifies sections as `complete`, `partial`, or `empty` based on the presence of `_To be filled in: ___` markers. It does not assume empty sections contain valid data.
2. **"Accept as-is" gate decision.** The operator can choose to proceed without returning the questionnaire to the outgoing team. This choice is recorded explicitly in state.md.
3. **Evidence-based scorecard degradation.** Items auto-mark `?` (not ✓) when their source section is empty — per Iron Law, absence of evidence is unknown, not negative. The skill marks `✗` only when an interview answer explicitly states the negative (e.g., "no DR plan exists"). It does not infer or forward-fill answers.
4. **Iron Law compliance.** The skill never asks the operator to fill in Section 10 answers. The operator is not the source of compliance/DR knowledge — the outgoing team is. Missing knowledge surfaces as open questions, not as operator prompts.
5. **Not-ready verdict from Compliance category.** Four Compliance items unresolved (22–25 all `?`) is sufficient to produce a `not-ready` verdict regardless of the other 21 items.
6. **Open questions populated from empty sections.** The 5 high-priority open questions map directly to Section 10 (PII, retention, backup, DR) and Section 3 (SLOs). The 3 medium-priority items map to Section 6 (incidents) and Section 11 (open issues) being empty.

---

## Gate transitions

**Gate 1 → Step 1 complete**
Same as happy-path. Operator provides: service=payments, account 123456789012, region us-east-1, takeover intent, 2 diagram PNGs, no IaC, outgoing=Pay Team, incoming=Platform Team.

**Gate 1.5 → Step 1.5 complete (execution plan approved)**
Same as happy-path. All 4 capability probes pass. Execution plan identical to happy-path. Operator approves.

**Gate 2 → Step 2 complete (diagram extraction)**
Same as happy-path. Catalog snapshot at mock-artifacts/service-catalog.md.

**Gate 3 → Step 3 complete (live discovery)**
Same as happy-path. Catalog merged; 8 resources confirmed.

**Gate 4 → Step 4 complete (runtime profile)**
Same as happy-path. All 4 runtime-trace sources ran; profile snapshot at mock-artifacts/runtime-profile.md.

**Gate 5 → Step 5 complete (interview ingested — partial)**
Skill emits questionnaire. Bob L. fills in Sections 1, 2, 4, 5, 7, 8, 9 fully. Section 3 left entirely empty. Section 6: runbooks filled, incidents/recurring/MTTR/change-failure-rate empty. Section 10 entirely empty. Section 11: pending changes + deprecations + outlook filled, open issues empty.

Skill classifies: 6 complete, 3 partial, 2 empty. Presents classification summary to operator with 3 options: (a) return to outgoing team for completion, (b) accept as-is, (c) abort.

Operator selects "accept as-is". Skill records decision in state.md Gate 5 row and audit trail. Skill does NOT ask the operator to fill in any missing answers.

**Gate 6 → Step 6 complete (scorecard — not-ready)**
Skill auto-marks from artifacts:
- Items 1-9: ✓ from service-catalog.md and runtime-profile.md (unchanged from happy-path).
- Items 10-12: ✓ from Section 5 and Section 2 (fully completed sections).
- Item 13: ✓ from Section 6 → runbooks sub-section (5 runbooks present).
- Item 14: ? — Section 6 → incidents sub-section empty. Skill marks ? not ✓ (absence of data ≠ absence of incidents).
- Items 15-18: ✓ from Section 4 (fully completed).
- Items 19-21: ✓ from Section 8 (fully completed).
- Items 22-25: `?` — Section 10 entirely empty. Per Iron Law, absence of evidence is unknown, not negative. Skill auto-marks `?` (not `✗` not `✓`). Evidence citation: "filled-interview.md → Section 10 — empty (`_To be filled in: ___`)". `✗` is reserved for explicit negative answers.

Operator manually confirms Item 3 (console+CLI) and Item 12 (paging path) as ✓.

Verdict: not-ready. 4 unresolved `?` items in Compliance category (0 of 4 passing) is sufficient. Skill does not attempt to override or soften the verdict.

**Gate 7 → Step 7 complete (handoff package assembled)**
Package assembled with same file list as happy-path. README TL;DR prominently flags `not-ready` verdict and the 5 high-priority open questions. First-day actions lead with the 5 blockers before any routine steps.

---

## Key differences from happy-path

| Dimension | happy-path | partial-interview |
|---|---|---|
| Interview sections filled | 11/11 | 6 full + 3 partial + 2 empty |
| Gate 5 decision | accept (full) | accept as-is (partial) |
| Scorecard ✓ count | 23 | 18 |
| Scorecard ✗ count | 0 | 0 |
| Scorecard ? count | 0 | 5 |
| Compliance category | 4/4 | 0/4 |
| Verdict | ready | not-ready |
| High-priority open questions | 0 | 5 |
| Medium-priority open questions | 2 | 3 |

---

## Acceptance check

A reviewer steps through `input.md`, `mock-artifacts/`, and `filled-interview.md`, then confirms the skill would produce the contents of `expected-handoff/` with **representative** results (allowing for run-specific timestamps and operator usernames).

Specifically:
- `expected-handoff/readiness-scorecard.md` verdict would be `not-ready` for any run with this input set, because Section 10 is empty and the skill correctly does not auto-pass evidence-absent compliance items.
- `expected-handoff/open-questions.md` would have 5 high-priority items for any run where Section 10 and Section 3 are empty.
- `expected-handoff/state.md` Gate 5 row would always record "accept as-is" decision for this fixture.
- Items 22-25 would always be `?` (not `✗`) because empty sections are absence of evidence, not explicit negative answers. The skill reserves `✗` for explicit denials (e.g., "no DR plan exists").
