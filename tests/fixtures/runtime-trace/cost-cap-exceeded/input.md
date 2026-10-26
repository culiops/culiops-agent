# Fixture: cost-cap-exceeded

## Scenario

A platform service tagged `service=platform-core` with ~600 resources across many AWS service types. The operator wants a year of daily spend broken down by service **and** usage type, and CloudWatch fan-out across all resources, overriding the 200-metric default to 12,000. Cost Explorer pagination is what makes the plan expensive: every page of `GetCostAndUsage` is a separate $0.01 request.

The plan (priced against the resolved resource set) comes to $1.22, plus the $0.01 GATE 1a probe already spent = $1.23 — over the $1.00 hard cap.

## Scoping primitive

Tag-based: `service=platform-core`.

## Gate 1 operator inputs

- Service name: `platform-core`
- Intent category: `takeover`
- Intent context: "Large platform takeover, expecting wide scope."
- Operator chose to override the 200-metric CloudWatch cap (sets it to 12,000) at Gate 1 advanced options.
- Operator chose a 12-month CE window (2025-05-11 -> 2026-05-11, 365 days, DAILY) grouped by SERVICE and USAGE_TYPE.

## Expected gate behavior

- Gate 1: accepted with the metric-cap override and the CE window recorded.
- GATE 1a: 10 read-only probes; only the CE probe is billed ($0.01).
- Gate 2: all sources available.
- Step 2b: free Resource Explorer `Search` `tag:service=platform-core` resolves **612** resources (`Count.Complete=true`).
- Gate 3: plan priced against the 612 resources:
  - CE: ~110 pages x $0.01 = **$1.10**
  - CloudWatch: 12,000 metrics / 1,000 x $0.01 = **$0.12**
  - CloudTrail, Wiring, Resource Explorer: free
  - Plan estimate **$1.22**; already spent in GATE 1a **$0.01**; cumulative **$1.23** > $1.00.
  Skill **REFUSES to proceed.** Prints the plan with arithmetic, the cap, "Cannot proceed: estimated cumulative cost $1.23 exceeds the hard cap of $1.00." and three options: (a) reduce scope, (b) raise the cap with documented justification (recorded in the audit trail), (c) abort.
- If the operator chooses (b), the cap-raise event is logged with the justification and Gate 3 is re-run with the new cap. If (a) or (c), no further billable calls are made.

This fixture covers only the "refuse and present options" branch (operator picks abort).

## Notable findings

- No runtime profile written. Skill produces a "plan-refused" report at `.culiops/runtime-trace/platform-core-plan-refused.md` documenting the plan, the arithmetic, the cap and the options.
- The arithmetic is checkable: 110 x 0.01 + 12,000/1,000 x 0.01 + 0.01 = 1.10 + 0.12 + 0.01 = 1.23.
