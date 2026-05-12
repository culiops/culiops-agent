# Fixture: cost-cap-exceeded

## Scenario

A platform service tagged `service=platform-core` with 600+ resources across many AWS service types. Cost Explorer's GROUP BY plan needs additional dimension passes (linked-account, tag, usage-type, service) and CloudWatch fan-out across hundreds of resources would push the metric count to 12,000+ (60× the 200 cap; operator wants to override).

Gate 3 estimates total at $1.21 — over the $1.00 hard cap.

## Scoping primitive

Tag-based: `service=platform-core`.

## Gate 1 operator inputs

- Service name: `platform-core`
- Intent category: `takeover`
- Intent context: "Large platform takeover, expecting wide scope."
- Operator chose to override the 200-metric CloudWatch cap (sets it to 12,000) at Gate 1 advanced options.

## Expected gate behavior

- Gate 1: accepted with the metric-cap override recorded.
- Gate 2: all four sources available.
- Gate 3: plan estimate = $1.21. Skill **REFUSES to proceed.** Prints:
  - the plan
  - the cap ($1.00)
  - "Cannot proceed: estimated cost $1.21 exceeds the hard cap of $1.00."
  - three options: (a) reduce scope, (b) raise the cap with documented justification (operator must explicitly state the justification, which is recorded in the audit trail), (c) abort.
- If operator chooses (b), the cap-raise event is logged with the justification and re-runs Gate 3 with the new cap. If operator chooses (a) or (c), no API calls are made.

This fixture covers only the "refuse and present options" branch. A separate run could cover the "operator raised the cap" branch.

## Notable findings

- No runtime profile written. Skill produces a "plan-refused" report at `.culiops/runtime-trace/platform-core-plan-refused.md` documenting the plan, the cap, and the three options offered to the operator.
