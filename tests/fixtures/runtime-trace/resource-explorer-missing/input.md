# Fixture: resource-explorer-missing

## Scenario

Same payments service as `basic-lambda-service` but Resource Explorer is not configured in this AWS account. `ListIndexes` returns an empty list. Skill must skip RE gracefully, record the gap, and recommend enabling RE (without doing so itself).

## Scoping primitive

Tag-based: `service=payments`. (Note: without RE, the skill cannot independently confirm cross-region coverage. Operator should also supply ARN list if cross-region coverage matters.)

## Gate 1 operator inputs

Same as basic-lambda-service.

## Expected gate behavior

- Gate 2 capability matrix shows Resource Explorer ✗ ("not configured in this account; ListIndexes returned empty").
- Output doc's "Cross-Region Footprint" section is replaced with a gap notice.
- "Gaps and Caveats" recommends enabling Resource Explorer and re-running for cross-region completeness.
