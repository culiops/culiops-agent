# Dry-run notes — basic-lambda-service

## Gate transitions

1. **Gate 1 (Scoping)** — operator provides all required inputs from `input.md`. Skill accepts and proceeds.
2. **GATE 1a (Scoping probe)** — skill shows the 10-call read-only batch (see `mock-api-responses/probe-responses.json`), the operator approves it, and it runs. Checks: `sts:GetCallerIdentity` account equals the typed account; `organizations:DescribeOrganization` says member account (payer check; a standalone account would return `AWSOrganizationsNotInUseException`, also fine); Resource Explorer aggregator index in `us-east-1`, view includes `tags`; Event history reachable (1-page `LookupEvents`); CE probe (tag-filtered, 1 day) returns a non-zero amount, which also proves the cost-allocation tag is active. Only the CE probe is billed ($0.01).
3. **Gate 2 (Capability matrix)** — built from the GATE 1a results, not from fresh calls. Resource Explorer, CloudTrail, Cost Explorer ✓ probed; Wiring reads and `GetMetricData` `untested` (no probe; p7 tests `ListMetrics` only) until their first Gate 4 call. Operator confirms.
4. **Step 2b (Resolve resource set)** — free `resource-explorer-2:Search` `tag:service=payments` returns 5 resources (`re-001`). The list is shown to the operator.
5. **Gate 3 (Plan)** — 6 rows priced against the resolved set: CE x2 ($0.02), CloudTrail 5 series (free), Wiring 8 reads (~$0.00, within free tiers), CloudWatch 23 metrics ($0.00023), conditional `ListMetrics` (free tier). Plan estimate $0.0202; $0.01 already spent in GATE 1a; projected $0.0302. Below the soft warning ($0.25). Operator approves the plan.
6. **Gate 4 (Execution)** — order is Cost Explorer -> CloudTrail -> Wiring -> CloudWatch. Four source blocks, each approved separately. Resource Explorer has no Gate 4 block (it ran at Step 2b).
7. **Gate 5 (Synthesis)** — skill assembles the draft matching `expected-output.md`. Operator approves with no revisions.
8. **Gate 6 (Write)** — writes `.culiops/runtime-trace/payments-runtime-profile.md` and projected-field sidecars to `.culiops/runtime-trace/payments-audit/`. The skill does not commit them. Sample: `sample-sidecar-ct-001.json`.

## What this fixture validates

- Happy path with all sources available, in the new gate order.
- **C1:** every CE request carries the tag Filter; the spend table is the tagged service's, not the account's. Shared NAT / data transfer is NOT in the table and appears only as an account-context note and a Gap.
- **M2:** CE is DAILY over a closed window (End exclusive), summed; `Estimated` days excluded; `AmortizedCost`; record types limited to Usage / DiscountedUsage / SavingsPlanCoveredUsage.
- **M3:** no "services billing but absent from diagram" callout (no catalog primitive in this run).
- **H4:** the resource set is resolved and shown before the plan is priced; CloudTrail names and the 23-metric count come from it.
- **H3:** CloudTrail is 5 call series (one lookup attribute per call), page cap 20 per resource, <= 2 req/s.
- **H2:** the principals table keeps its heading and columns, with a "management events only" note above it; the new Wiring block carries configured callers.
- **H5:** sparse metric. `payments-cleanup` returns an EMPTY `Values` array, a `ListMetrics` existence check follows, and the verdict is `no-activity-14d`. The TL;DR may only say "no activity observed in 14d; window too short to judge periodic jobs — ask the service owner or previous owners what payments-cleanup does". No "idle", no "candidate for sunset", no action word anywhere.
- **M5:** verdict thresholds are labelled `heuristic:` with raw numbers shown next to them.
- **H6:** the Cross-Region section records the aggregator Region, indexed Regions and view properties before it says "none outside primary Region".
- **C2:** sidecars are projected; the raw mock contains `requestParameters` (with a fake `DB_CONN` secret), IPs, user agents and a session name, none of which reach the sidecar sample.
- **M6:** numbers are internally consistent (TL;DR percentages = table percentages; usage types sum to the service totals; the audit total includes the probe).
- DynamoDB is a resolved resource of a type with no `examples/aws/` file -> Gap "metrics not collected".

## Acceptance check

A reviewer steps through `input.md` and each `mock-api-responses/*.json` and confirms the skill would produce `expected-output.md` with **representative** results (allowing for run-specific timestamps). Explicit assertions:

1. Every `ce:GetCostAndUsage` request in the output contains the tag Filter and `Granularity: DAILY`; the probe request does too.
2. `ce-001` and `ce-002` totals are equal (23.02) and the Share column sums to 100.0%.
3. The audit total is $0.0302 and includes `probe-010`.
4. The string "absent from diagram" does not appear; neither do "idle" nor "sunset".
5. The headings "Control-Plane Activity (CloudTrail)", "Notable change events:" and "Principals touching this service:" appear verbatim (downstream `service-takeover` reads them), and the principals table is preceded by the "management events only" line.
6. A "## Wiring (configured callers)" section follows Control-Plane Activity.
7. "Notable change events:" carries a count line ("3 shown of 5 fetched") and lists every `ReadOnly=false` event.
8. `payments-retry-queue` is described as not a DLQ because `sqs:ListDeadLetterSourceQueues` (`wr-008`) returned an empty list; the Gaps section says DLQ status covers same-account sources only.
9. Empty CloudTrail series read "none found by this lookup", never "untouched".
10. No `requestParameters`, `responseElements`, `sourceIPAddress`, `userAgent` or session name (`ci-runner-44`) appears in the profile or in a sidecar.

Mock notes: `cloudwatch-metric-data.json` shows 4 of the 23 queries and only the newest 5 points of each hourly series; the CE mocks show 3 of 30 daily rows plus a `_sum_of_all_30_days` block. Strict byte-for-byte mapping is out of scope.

## Flags for the reviewer

- `lambda:GetPolicy` returns `ResourceNotFoundException` for functions without a resource policy (`wr-002`, `wr-003`). The skill must treat that as "none", not as a failure that triggers stop-on-error.
- **UNVERIFIED / semantic risk:** per the AWS `ListMetrics` API reference, metrics with no datapoints in the past two weeks are not returned. So the `cw-002` HIT is only consistent with a datapoint at the very edge of the horizon, and a MISS cannot distinguish "wrong dimension/Region" from "no datapoints for more than 2 weeks". The fixture models a hit (the case the review asks for). The skill should word a miss as `no-data (metric not listed: wrong dimension/Region, or no datapoints for > 2 weeks)` rather than a flat `metric-not-found`.
- `ListIndexes` is added to the GATE 1a Resource Explorer probes because `GetIndex` alone cannot list the indexed Regions the cross-Region claim needs. `DescribeTrails` is also in the probe batch (free); it only informs the ">90 days / data events" Gap.
- CloudWatch is simplified to the 14d hourly pass only (23 queries). The previous fixture also claimed a "24h at 5min" pass that was never in the 18-query count.
