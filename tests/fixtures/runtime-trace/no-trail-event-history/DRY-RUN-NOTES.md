# Dry-run notes — no-trail-event-history

(Renamed from `cloudtrail-disabled`. The old scenario skipped CloudTrail when `DescribeTrails` was empty and reported "who is touching this service" as unanswered. That was wrong: Event history is always on and separate from trails.)

## What this fixture validates

- The CloudTrail capability test is a **1-page `LookupEvents` probe**, not `DescribeTrails`.
- An empty `trailList` changes only a Gap (">90 days and data events unavailable"), never the source status.
- CloudTrail is **not skipped**: the plan keeps the 5 `LookupEvents` series, the output has real principals and change events, and takeover items that depend on them are not forced to `?`.
- The skill does NOT propose creating a trail (write action; out of scope).

## Gate transitions

1. Gate 1 — operator inputs accepted.
2. GATE 1a — `DescribeTrails` returns `{"trailList": []}`; `LookupEvents` (1 page) succeeds; the remaining probes as in basic-lambda-service.
3. Gate 2 — capability matrix: CloudTrail ✓ ("Event history only; no trail configured"). No "proceed without CloudTrail?" question.
4. Step 2b / Gate 3 — as basic-lambda-service; plan includes the CloudTrail rows.
5. Gate 4 — four source blocks: CE, CloudTrail, Wiring, CloudWatch.
6. Gate 5 / Gate 6 — as basic-lambda-service.

## Acceptance check

- The Overview CloudTrail row reads **✓ ran** with the note about Event history, **not** "— skipped".
- The Gate 3 plan contains the CloudTrail `LookupEvents` rows (assert CloudTrail was NOT skipped).
- "Control-Plane Activity (CloudTrail)" contains events and principals; it does not contain "CloudTrail unavailable" or "unanswered".
- "Gaps and Caveats" contains (case-insensitive) the sentence "no trail configured: history older than 90 days and data events are not available".
- The skill never proposes creating or enabling a trail (that would need five-field approval per the Iron Law).
