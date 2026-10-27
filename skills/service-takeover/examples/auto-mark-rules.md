# Auto-Mark Rules — Reference

This document is a quick lookup for the readiness-scorecard auto-mark rules defined in `templates/readiness-scorecard-baseline.md`. It is not consumed at runtime; it's an implementer/maintainer reference. If it disagrees with the baseline, the baseline wins.

For each of the 25 baseline items, the auto-mark rule is a function of:
- **Source artifact(s)** — which file(s) the skill reads.
- **Evidence class** — a cited artifact line, a live read-only query, or an interview/operator answer.
- **Mark output** — one of the marks below.

## Marks

| Mark | Meaning | Allowed evidence |
|---|---|---|
| `✓ verified` | Proven | A cited artifact line, or a live read-only query (catalog `Live ✓`, runtime profile, projected CLI result from Step 1.5 / Step 6). |
| `✓ attested` | Not provable by any artifact | **Items 3, 11, 12 only.** Operator's one-line note. |
| `◐ operator-stated` | Interview/operator answer on a checkable fact, unverified | Interview answer. Never a pass on its own. |
| `✗` | Fails | Explicit negative in an artifact or answer ("no DR plan"), or a verified absence. |
| `✗ conflict` | Interview and artifact disagree | Both sources cited. Always a High open question. |
| `?` | Unknown | Missing, empty, ambiguous, or "not verifiable". |
| `N/A` | Does not apply | A cited artifact or record says so. An interview statement alone is `◐`. |

Presence of an interview answer yields `◐`, never `✓`. There is no "non-empty ⇒ pass" rule.

## Verdict rule

- `ready` only if every item is `✓ verified`, `✓ attested` or `N/A`.
- Otherwise, any `◐` or `?` → `partial`.
- Any `✗` or `✗ conflict`, in any category → `not-ready`.

For every `◐` item the scorecard lists the read-only check that would verify it. The optional **Step 6 verification batch** (offered by default, projected and approved like Step 1.5 commands) runs them and turns `◐` into `✓ verified` or `✗ conflict`. Skipping it leaves the items `◐` and the verdict `partial`.

## Citation format

Every `✓ verified` and `✗ conflict` carries `[evidence: <path>:<line>]` where a line exists, else `[evidence: <path>#<heading>]`. A `✗ conflict` cites both sources. `✓ attested` carries `[attested: <one-line operator note>]`. A `◐` carries `[stated: <path>#<heading>]`.

## Artifact dependency map

| Item | Artifact(s) needed | Step 6 verification batch |
|---|---|---|
| 1 | state.md (Step 1.5 probe; `sts get-caller-identity` account must equal intake, plus one permission-requiring read that succeeded) | — |
| 2 | runtime-profile.md (Control-Plane Activity) — a hint only; operator confirms | — |
| 3 | [attested] | — |
| 4 | service-catalog.md (attributed rows only) | — |
| 5 | runtime-profile.md (Cross-Region Footprint) | — |
| 6 | service-catalog.md (attributed rows only) OR interview-questionnaire.md (Section 9, ◐) | — |
| 7 | runtime-profile.md (Activity Baselines) | — |
| 8 | runtime-profile.md (Control-Plane Activity / Notable change events) | — |
| 9 | runtime-profile.md (managing principals, management events) | — |
| 10 | interview-questionnaire.md (Section 5 — Alarms) | **Yes** — `describe-alarms` |
| 11 | interview Section 2 → ◐; ✓ attested once the operator confirms they can see the rotation in the pager tool | — |
| 12 | [attested] | — |
| 13 | interview-questionnaire.md (Section 6 — Existing runbooks) | — |
| 14 | interview-questionnaire.md (Section 6 — Incidents) | — |
| 15 | interview-questionnaire.md (Section 4 — Deploy permissions, incoming role ARN) | **Yes** — `iam simulate-principal-policy` |
| 16 | interview-questionnaire.md (Section 4 — How code reaches prod) | — |
| 17 | interview-questionnaire.md (Section 4 — Rollback procedure) | — |
| 18 | interview-questionnaire.md (Section 4 — Deploy frequency) | **Yes** — compare with deploy-event count in runtime-profile Notable change events |
| 19 | interview-questionnaire.md (Section 8 — Upstream callers) + runtime-profile.md (Wiring) | **Yes** — stated callers vs Wiring rows |
| 20 | interview-questionnaire.md (Section 8 — Downstream services) + service-catalog.md (Dependency Graph) | **Yes** — compare with catalog Dependency Graph |
| 21 | interview-questionnaire.md (Section 8 — External APIs) | — |
| 22 | interview-questionnaire.md (Section 10 — PII handling) | — |
| 23 | interview-questionnaire.md (Section 10 — Data retention) | — |
| 24 | interview-questionnaire.md (Section 10 — Backup strategy + Last backup-restore test) | **Yes** — RDS / DynamoDB / AWS Backup (restore test itself stays ◐ or attested) |
| 25 | interview-questionnaire.md (Section 10 — Disaster recovery plan) | — |

Items 2, 8, 15, 16 and 18 depend on the delivery model; items 1, 7–10, 15, 19 and 24 have `Kubernetes:` lines in the baseline (item 18 uses item 8's history). Item 9 is "Managing principals enumerated (management events)" — those are who changed the service, not who calls it. Callers come from runtime-profile Wiring (item 19). Item 13 is "Top runbooks exist (≥3)".

## Rule patterns

Each item's full logic is in `templates/readiness-scorecard-baseline.md`. Common patterns:

- **Artifact-count rule:** `✓ verified` if the cited artifact has ≥ threshold *attributed* rows (items 4, 6). Rows that are `Live: not found` / `not checked` or on the Unattributed list don't count. `✓ verified` also needs `**Live verification:** performed` in the catalog (or real-discovery, which is live by construction); otherwise `◐`.
- **Explicit-statement rule:** `✓ verified` only on an explicit verified statement (item 5: a verified cross-Region statement; "cross-Region: not verifiable" → `?`).
- **Interview rule:** a non-empty, specific answer → `◐`. Quantitative or named answers (e.g. "twice a week" for item 18) are still `◐` until the Step 6 batch checks them.
- **Explicit-negative rule:** `✗` if the answer states "no X" (e.g. "no DR plan" for item 25).
- **Conflict rule:** interview and artifact disagree → `✗ conflict`, both cited, High open question.
- **Empty rule:** `?` if the section is empty or holds only fill-in markers. An empty section is never `✗`.

## Adding new items

If a future version adds items 26+, they go in `templates/readiness-scorecard-baseline.md` following the same format. This file should be updated to add the dependency row.

Operators who want skill-specific extras (not in the baseline) should put them in `.culiops/service-takeover/<service>/extra-checklist.md` — they are merged into the scorecard at Step 6 but do not modify the baseline file.
