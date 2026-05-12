# Dry-run notes — cost-cap-exceeded

## What this fixture validates

- The $1.00 hard cap is a true tripwire, not a suggestion.
- Skill produces a *plan-refused* report instead of a runtime profile when the cap is exceeded.
- Operator is given three explicit options (reduce scope / raise cap with justification / abort).
- No API calls beyond capability probes are made when the plan is refused.
- Cap-raise requires *documented* justification (written to the audit trail).

## Gate transitions

1. Gate 1 — operator inputs accepted; metric-cap override (12,000) recorded.
2. Gate 2 — all sources available. Operator confirms.
3. Gate 3 — plan estimate $1.21. **Skill refuses.** Prints plan, cap, three options. Operator chooses abort (option 3).
4. Gates 4-6 — never executed.

## Acceptance check

- No runtime-profile.md emitted.
- A plan-refused report IS emitted at `.culiops/runtime-trace/platform-core-plan-refused.md`.
- Audit trail shows only the capability probe call, not the planned-but-refused queries.
- Skill never silently proceeds even by $0.01 over.

## Out-of-scope reminder

If a future change wanted to allow auto-raising the cap when "obviously" needed, that change requires a fresh design pass — the cap is currently a hard tripwire by design, calibrated against realistic blast radii in the spec at `docs/superpowers/specs/2026-05-12-runtime-trace-design.md`.
