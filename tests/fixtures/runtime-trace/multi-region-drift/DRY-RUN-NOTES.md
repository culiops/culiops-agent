# Dry-run notes — multi-region-drift

## What this fixture validates

**Variant A (aggregator index):**

- Resource Explorer's aggregator view catches a forgotten resource outside the primary Region.
- The cross-Region claim is backed by recorded checks: aggregator Region, indexed Regions, view properties, `Count.Complete`.
- The skill notes the **limitation** that CloudTrail / Wiring / CloudWatch ran in the primary Region only, so `payments-archive` is listed (resolved set) but not traced, and the Gap says so.
- The "open question" callout flows into a future `service-takeover` interview step.

**Variant B (local index only):**

- A local-only index is never reported as "no drift". The Cross-Region section says "cross-Region: not verifiable — local index only" and lists no Regions.
- The Gap recommends creating an aggregator index (operator action, out of scope).
- Downstream: `service-takeover` item 5 auto-marks `?` (its auto-mark sentinel reads the Cross-Region Footprint section; the heading is unchanged, the content now says "not verifiable").

## Gate transitions

Identical to basic-lambda-service (Gate 1 -> GATE 1a -> Gate 2 -> Step 2b -> Gate 3 -> Gate 4 (CE, CloudTrail, Wiring, CloudWatch) -> Gate 5 -> Gate 6). Only the Resource Explorer probe results and the Step 2b `Search` response differ:

- Variant A: `GetIndex` = `AGGREGATOR`; `Search` through the us-east-1 aggregator view returns 6 resources.
- Variant B: `GetIndex` = `LOCAL`; `ListIndexes` returns one index; `Search` returns 5 resources.

## Acceptance check

- Variant A: Cross-Region section shows the four checks and both Regions; the "outside primary Region" table is populated; Gaps include the cross-Region limitation note and the open question; `payments-archive` is marked as excluded from the traced passes.
- Variant B: the string "none outside primary Region" / "no cross-region drift" does NOT appear anywhere; the Cross-Region section contains "not verifiable — local index only"; Gaps recommend an aggregator index and state it is out of scope; `service-takeover` item 5 would be `?`.
