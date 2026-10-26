# Dry-run notes — cost-cap-exceeded

## What this fixture validates

- The $1.00 hard cap is a true tripwire, not a suggestion, and the test now actually exceeds it. (The previous fixture's plan summed to $0.16, not the stated $1.21.)
- The estimate counts **Cost Explorer pagination** (every page is a $0.01 request) and the **GATE 1a probe** already spent.
- Skill produces a *plan-refused* report instead of a runtime profile when the cap is exceeded.
- Operator is given three explicit options (reduce scope / raise cap with justification / abort).
- No billable calls beyond the GATE 1a probe are made when the plan is refused; the free Step 2b resolution has already run (it is what Gate 3 prices against).
- Cap-raise requires *documented* justification (written to the audit trail).

## Arithmetic (checkable)

| Item | Calculation | Cost |
|---|---|---|
| CE DAILY, 365 days, SERVICE + USAGE_TYPE | ~110 pages x $0.01 | $1.10 |
| CloudWatch, 12,000 metrics | 12,000 / 1,000 x $0.01 | $0.12 |
| Plan estimate | $1.10 + $0.12 | $1.22 |
| GATE 1a CE probe (spent) | 1 x $0.01 | $0.01 |
| Cumulative | $1.22 + $0.01 | $1.23 |

## Gate transitions

1. Gate 1 — operator inputs accepted; metric-cap override (12,000) and the 12-month CE window recorded.
2. GATE 1a — 10 read-only probes; CE probe billed $0.01.
3. Gate 2 — all sources available. Operator confirms.
4. Step 2b — free RE `Search` resolves 612 resources.
5. Gate 3 — plan $1.22, cumulative $1.23. **Skill refuses.** Prints plan, arithmetic, cap, three options. Operator chooses abort (option 3).
6. Gates 4-6 — never executed.

## Acceptance check

- No runtime-profile.md emitted.
- A plan-refused report IS emitted at `.culiops/runtime-trace/platform-core-plan-refused.md`.
- The report's plan rows sum to the stated estimate (1.10 + 0.12 = 1.22) and the cumulative figure includes the probe (1.23).
- Audit trail shows the GATE 1a probes and `re-001` only, not the planned-but-refused queries.
- Skill never silently proceeds even by $0.01 over.

## Flags for the reviewer

- **UNVERIFIED planning assumption:** the "~2,000 rows/page" figure used to get ~110 pages is not an AWS-documented page size. The fixture only needs the plan to exceed the cap; the real skill should state its page estimate as an assumption and re-check actual cost after the first page (the existing ">2x estimate" pause covers this).
- DAILY granularity over 12 months is assumed to be within Cost Explorer's daily lookback; if a real account rejects it, the skill's own error handling applies and this fixture is unaffected.

## Out-of-scope reminder

If a future change wanted to allow auto-raising the cap when "obviously" needed, that change requires a fresh design pass — the cap is currently a hard tripwire by design, calibrated against realistic blast radii in the spec at `docs/superpowers/specs/2026-05-12-runtime-trace-design.md`.
