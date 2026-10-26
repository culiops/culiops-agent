# Fixture: no-trail-event-history

(Replaces `cloudtrail-disabled`. That fixture encoded a wrong rule: "no trail -> skip CloudTrail". CloudTrail **Event history is on by default and is separate from trails** (CloudTrail user guide, "Working with CloudTrail event history"), so `LookupEvents` keeps working with no trail configured.)

## Scenario

Same payments service as `basic-lambda-service`, but the AWS account has **no CloudTrail trail at all**: `cloudtrail:DescribeTrails` returns an empty `trailList`. Event history (last 90 days of management events) is still available, and the GATE 1a 1-page `LookupEvents` probe succeeds. The skill must run the CloudTrail source and record what a missing trail costs: no history older than 90 days, no data events.

## Scoping primitive

Tag-based: `service=payments`.

## Gate 1 operator inputs

Same as basic-lambda-service.

## Expected gate behavior

- **GATE 1a:** `DescribeTrails` -> `{"trailList": []}` (free, informs the Gap only). `LookupEvents` with `MaxResults=1` returns an event (this is the capability test). Everything else as in basic-lambda-service.
- **Gate 2:** capability matrix shows CloudTrail ✓ with the note "Event history only; no trail configured". The operator is NOT asked whether to proceed without CloudTrail.
- **Step 2b / Gate 3:** unchanged from basic-lambda-service; the plan keeps the 5 CloudTrail `LookupEvents` series (free). Plan estimate and projected total are the same as basic ($0.0202 / $0.0302).
- **Gate 4:** four source blocks (CE, CloudTrail, Wiring, CloudWatch). CloudTrail returns the same events as basic-lambda-service.
- **Output:** "Control-Plane Activity (CloudTrail)" is populated normally. "Gaps and Caveats" carries: "no trail configured: history older than 90 days and data events are not available".
- The skill never proposes creating a trail (a write action; out of scope).
