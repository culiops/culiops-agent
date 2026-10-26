# Fixture: multi-region-drift

Two variants share one scenario. Variant A (aggregator index) is the original case. Variant B (local index only) is new and tests the false-negative guard: a local-only index must never be reported as "no drift".

## Scenario

Same payments service as `basic-lambda-service` but with one Lambda (`payments-archive`) deployed in us-west-2 that nobody on the receiving team knew about.

## Scoping primitive

Tag-based: `service=payments`.

## Gate 1 operator inputs

(Same as basic-lambda-service except intent context: "Drift check before takeover — pre-flight sanity check.")

- Intent category: `drift-check`

## Variant A — aggregator index (original case)

Resource Explorer has an `AGGREGATOR` index in us-east-1 and a `LOCAL` index in us-west-2; the default view lives in us-east-1 and includes `tags`.

### Expected gate behavior

Same as basic-lambda-service. GATE 1a records the aggregator Region, the indexed Regions and the view's included properties. Step 2b (`Search` through the aggregator view) resolves **6** resources; the 6th is in us-west-2. It is listed in the resolved set but **excluded from the CloudTrail / Wiring / CloudWatch passes** (those run in the primary Region only), and that exclusion is stated as a Gap.

### Notable findings

- Resource Explorer surfaces 1 resource outside us-east-1 (Lambda `payments-archive` in us-west-2). It is the only source that sees it.
- CloudTrail Event history is per Region: this run queried us-east-1 only, so there are no events for `payments-archive`. Gap: "CloudTrail Event history was queried in us-east-1 only; events for us-west-2 resources are not covered."
- CloudWatch and Wiring were not run for `payments-archive` (regional APIs, primary-Region pass only). Gap: "us-west-2 resources not included in CloudWatch metric or Wiring pass — re-run with `--region us-west-2` to cover them, or expand the scoping primitive."
- Cost Explorer is unaffected: it is account-wide and the tag filter already includes the us-west-2 Lambda's tagged cost.

## Variant B — local index only (new)

Resource Explorer has only a **`LOCAL`** index in us-east-1; there is no aggregator index. The default view in us-east-1 includes `tags`. The `payments-archive` Lambda in us-west-2 exists exactly as in variant A, but Resource Explorer cannot see it: Regions without an index in the search path are invisible, and cross-Region search works only from a view in the aggregator Region (Resource Explorer user guide, "aggregator index").

### Expected gate behavior

Same as basic-lambda-service up to Step 2b. GATE 1a: `GetIndex` -> `Type: LOCAL`; `ListIndexes` returns one index (us-east-1). Step 2b `Search` returns **5** resources, all in us-east-1, `Count.Complete=true`. Everything downstream runs as in basic-lambda-service.

### Notable findings

- The Cross-Region section does NOT say "none outside the primary Region". It says "cross-Region: not verifiable — local index only" and lists no Regions.
- A Gap recommends creating an aggregator index (operator action; out of scope for the skill) or supplying an ARN list that includes other Regions.
- Downstream: `service-takeover` readiness item 5 (cross-Region footprint) therefore auto-marks `?`, not ✓.
