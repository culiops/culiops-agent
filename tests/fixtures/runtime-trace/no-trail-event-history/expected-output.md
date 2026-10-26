*(Other sections same as basic-lambda-service except where noted.)*

## Overview

| Source | Status | Reason |
|---|---|---|
| Scoping probe (GATE 1a) | ✓ ran | |
| Resource Explorer (resolve + cross-Region) | ✓ ran | |
| Cost Explorer | ✓ ran | |
| CloudTrail LookupEvents | ✓ ran | Event history only: no trail configured (`DescribeTrails` returned an empty list); history limited to 90 days of management events |
| Wiring (Lambda / SQS reads) | ✓ ran | |
| CloudWatch GetMetricData | ✓ ran | |

## Control-Plane Activity (CloudTrail)

*Source: CloudTrail Event history (90 days, management events). No trail is configured in this account; Event history is on by default and does not depend on one.*

**Requests:** `cloudtrail:LookupEvents`, one call series per resource name, 5 series (`ct-001`..`ct-005`), region us-east-1, last 90d, page cap 20 per resource, <= 2 requests/s.

Top API actions:

| API action | Event count |
|---|---|
| UpdateFunctionCode | 2 |
| UpdateFunctionConfiguration | 1 |
| GetFunction | 1 |
| DescribeTable | 1 |

*Management events only — principals that managed these resources; data-plane callers are in Wiring.*

Principals touching this service:

| Principal | Type | Last seen | Event count |
|---|---|---|---|
| arn:aws:iam::123456789012:role/PaymentsDeployRole | AssumedRole | 2026-05-09T14:22:25Z | 3 |
| arn:aws:iam::123456789012:user/alice | IAMUser | 2026-05-10T09:15:11Z | 2 |

Notable change events:

| Time (UTC) | Event | Principal | Resource | EventId |
|---|---|---|---|---|
| 2026-05-09T14:21:40Z | UpdateFunctionCode | PaymentsDeployRole | payments-refund | 4d5e6f70-... |
| 2026-05-09T14:22:18Z | UpdateFunctionCode | PaymentsDeployRole | payments-charge | 1a2b3c4d-... |
| 2026-05-09T14:22:25Z | UpdateFunctionConfiguration | PaymentsDeployRole | payments-charge | 2b3c4d5e-... |

## Gaps and Caveats

- **No trail configured: history older than 90 days and data events are not available.** Control-plane history in this profile is limited to CloudTrail Event history (last 90 days, management events, per Region).
- *(carry over other basic-lambda-service Gaps items, except the `mgmt-trail` S3 archive sentence, which does not apply here)*
