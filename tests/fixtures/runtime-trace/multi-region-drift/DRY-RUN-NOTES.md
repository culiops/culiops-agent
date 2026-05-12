# Dry-run notes — multi-region-drift

## What this fixture validates

- Resource Explorer cross-region pass catches a forgotten resource outside the primary region.
- The skill correctly notes the **limitation** that this run's CloudTrail / CloudWatch queries did not cover the out-of-region resource.
- The Gaps section guides the operator to a clear next action (re-run with the other region).
- The "open question" callout flows into a future `service-takeover` interview step.

## Gate transitions

Identical to basic-lambda-service. Resource Explorer is the only source whose response differs.

## Acceptance check

- Cross-Region table shows both regions.
- "Resources outside assumed primary region" table is populated.
- Gaps and Caveats includes the cross-region limitation note + the open question.
