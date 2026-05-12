*(Other sections same as basic-lambda-service except where noted.)*

## Overview

| Source | Status | Reason |
|---|---|---|
| Cost Explorer | ✓ ran | |
| CloudTrail LookupEvents | — skipped | No CloudTrail trail configured in this account; logging disabled |
| CloudWatch GetMetricData | ✓ ran | |
| Resource Explorer | ✓ ran | |

## Control-Plane Activity (CloudTrail)

**CloudTrail unavailable — control-plane history is blank.**

This account has no CloudTrail trail configured (response from `cloudtrail:DescribeTrails` returned an empty list). No principal, event, or change-history analysis possible for this run.

To enable: configure a CloudTrail trail with management events on in this account. See AWS documentation. **This is an out-of-scope action for the `runtime-trace` skill.**

## Gaps and Caveats

- **CloudTrail unavailable** — this is the most significant gap in this profile. No principals identified, no recent change events, no cross-account access visibility. Treat the "who is touching this service" question as **unanswered** until CloudTrail is enabled and the skill re-run.
- *(carry over other basic-lambda-service Gaps items)*
