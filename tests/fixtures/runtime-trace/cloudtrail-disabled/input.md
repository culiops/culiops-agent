# Fixture: cloudtrail-disabled

## Scenario

Same payments service as `basic-lambda-service` but the AWS account has no CloudTrail enabled (or no trail in the primary region with management events on). Skill must skip the CloudTrail source gracefully and record the gap.

## Scoping primitive

Tag-based: `service=payments`.

## Gate 1 operator inputs

Same as basic-lambda-service.

## Expected gate behavior

- Gate 2 capability matrix shows CloudTrail ✗ ("logging disabled in this account"). Operator confirms they want to proceed without CloudTrail data.
- Gate 3 plan omits the CloudTrail row entirely. Total estimated cost drops to $0.022 − $0.00 = $0.022 (CT was free anyway).
- Gate 4 runs only 3 source blocks (CE, CW, RE).
- Output doc's "Control-Plane Activity" section is replaced with: "CloudTrail unavailable — control-plane history is blank. No principal/event analysis possible. To enable: configure a CloudTrail trail with management events on in this account (see AWS docs). This is an out-of-scope action for the skill."
- "Gaps and Caveats" emphasizes this is the biggest blind spot in this profile.
