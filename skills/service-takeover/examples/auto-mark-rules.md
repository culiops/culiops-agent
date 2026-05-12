# Auto-Mark Rules — Reference

This document is a quick lookup for the readiness-scorecard auto-mark rules defined in `templates/readiness-scorecard-baseline.md`. It is not consumed at runtime; it's an implementer/maintainer reference.

For each of the 25 baseline items, the auto-mark rule is a function of:
- **Source artifact(s)** — which file(s) the skill reads.
- **Sentinel** — what the skill looks for (presence, count, specific string).
- **Mark output** — ✓ / ✗ / ? / N/A / `[manual]`.

The full rules are in `templates/readiness-scorecard-baseline.md`. This file summarizes the artifact dependencies:

## Artifact dependency map

| Item | Artifact(s) needed |
|---|---|
| 1 | state.md |
| 2 | runtime-profile.md (Control-Plane Activity) |
| 3 | [manual] |
| 4 | service-catalog.md |
| 5 | runtime-profile.md (Cross-Region Footprint) |
| 6 | service-catalog.md OR interview-questionnaire.md (Section 9) |
| 7 | runtime-profile.md (Activity Baselines) |
| 8 | runtime-profile.md (Control-Plane Activity / Notable change events) |
| 9 | runtime-profile.md (principals table) |
| 10 | interview-questionnaire.md (Section 5 — Alarms) |
| 11 | interview-questionnaire.md (Section 2 — On-call schedule) |
| 12 | [manual] |
| 13 | interview-questionnaire.md (Section 6 — Existing runbooks) |
| 14 | interview-questionnaire.md (Section 6 — Incidents) |
| 15 | interview-questionnaire.md (Section 4 — Deploy permissions) |
| 16 | interview-questionnaire.md (Section 4 — How code reaches prod) |
| 17 | interview-questionnaire.md (Section 4 — Rollback procedure) |
| 18 | interview-questionnaire.md (Section 4 — Deploy frequency) |
| 19 | interview-questionnaire.md (Section 8 — Upstream callers) |
| 20 | interview-questionnaire.md (Section 8 — Downstream services) |
| 21 | interview-questionnaire.md (Section 8 — External APIs) |
| 22 | interview-questionnaire.md (Section 10 — PII handling) |
| 23 | interview-questionnaire.md (Section 10 — Data retention) |
| 24 | interview-questionnaire.md (Section 10 — Backup strategy + Last backup-restore test) |
| 25 | interview-questionnaire.md (Section 10 — Disaster recovery plan) |

## Sentinels reference

Each item's full sentinel logic is documented inline in `templates/readiness-scorecard-baseline.md`. Common patterns:

- **Presence sentinel:** ✓ if section is non-empty and contains at least one non-trivial answer.
- **Count sentinel:** ✓ if count of entries ≥ threshold (e.g., ≥3 runbooks for item 13).
- **String sentinel:** ✓ if answer contains specific keyword (e.g., "deploy" in principal name for item 2).
- **Quantitative sentinel:** ✓ if answer contains a number/timeframe (e.g., "twice a week" for item 18).
- **Explicit-negative sentinel:** ✗ if answer explicitly states "no X" (e.g., "no DR plan" for item 25).
- **Empty sentinel:** ? if section is empty or contains only fill-in markers.

## Adding new items

If a future version adds items 26+, they go in `templates/readiness-scorecard-baseline.md` following the same format. This examples file should be updated to add the artifact-dependency row.

Operators who want skill-specific extras (not in the baseline) should put them in `.culiops/service-takeover/<service>/extra-checklist.md` — they are merged into the scorecard at Step 6 but do not modify this baseline file.
