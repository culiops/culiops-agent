# Fixture: multi-region-drift

## Scenario

Same payments service as `basic-lambda-service` but with one Lambda (`payments-archive`) deployed in us-west-2 that nobody on the receiving team knew about. Resource Explorer is the only source that surfaces it.

## Scoping primitive

Tag-based: `service=payments`.

## Gate 1 operator inputs

(Same as basic-lambda-service except intent context: "Drift check before takeover — pre-flight sanity check.")

- Intent category: `drift-check`

## Expected gate behavior

Same as basic-lambda-service. Resource Explorer surfaces 6 resources instead of 5; the 6th is in us-west-2. The output's Cross-Region section highlights this; the Gaps section adds an "open question: is `payments-archive` in us-west-2 in scope for the takeover?" item.

## Notable findings

- Resource Explorer surfaces 1 resource outside us-east-1 (Lambda `payments-archive` in us-west-2).
- CloudTrail does not include events for the us-west-2 Lambda (the trail is regional, configured for us-east-1 only). This becomes a Gap entry: "CloudTrail does not cover us-west-2 events in this account configuration."
- CloudWatch metrics fetch fails for the us-west-2 Lambda (regional API mismatch). Recorded as: "us-west-2 resources not included in CloudWatch metric pass — re-run with `--region us-west-2` to cover them, or expand the scoping primitive."
