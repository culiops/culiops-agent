# Dry-run of `cloud-cost-investigate` against `anomaly-aws-bill-spike`

Expected skill behaviour at each step. Recorded for pre-dry-run reference; "Gaps surfaced" and "Fixes applied" are filled in during the actual dry-run.

Note: `get-rds-database-recommendations` and `get-idle-recommendations` are now in `examples/aws.md` (Step 2B, waste mode); they are not used in this anomaly fixture.

## Step 1 - Detect & Scope

- Reads `operator-question.md`. Heuristic: "spiked / why" gives anomaly mode (suggested).
- Detects AWS from `AWS_PROFILE` / `~/.aws/` (simulated).
- **Scoping probe (GATE 1a)**, 4 read-only calls, 1 CE request (~$0.01), `scoping-probe.json`: account `123456789012`, alias `acme-prod`; `describe-organization` returns `MasterAccountId` `999988887777` (not the caller): member account, no `LINKED_ACCOUNT` filter. CE by `REGION` (usage record types, AmortizedCost): us-east-1 is the only region with spend, so the sweep region is us-east-1 (100%).
- Time range (anomaly default, ends 2 days ago, equal lengths): current 2026-04-04..2026-05-03 vs previous 2026-03-05..2026-04-03, both 30 days. The query is issued with End 2026-05-06 (exclusive); the two newest returned days are expected to be estimated and are dropped (see Step 3).
- Operator figures: "$68K → $92K" is the cash bill (Unblended whole bill $67,720.18 → $91,773.50, including the one-time $9,000.00 upfront); the skill restates them as explicit dates and amortized usage, and does not compare a calendar month with month-to-date or forecast.
- Catalog: none (anomaly mode allows this). IaC repo: none.

**GATE 1:** operator confirms.

## Step 2A - Anomaly mode query plan (GATE 2 batch)

"Usage" = `RECORD_TYPE` in {`Usage`, `DiscountedUsage`, `SavingsPlanCoveredUsage`}, read at `AmortizedCost`.

| # | API | Scope | Region(s) | Time | IAM | Est. cost | Why |
|---|-----|-------|-----------|------|-----|-----------|-----|
| 5 | `ce:GetAnomalies` | account | global | 2026-04-04..2026-05-06 | `ce:GetAnomalies` | $0.01 | native root-cause lead |
| 6 | `ce:GetCostAndUsage` DAILY, 3 usage record types, group `SERVICE`, metrics `AmortizedCost` + `UnblendedCost` | account | global | 2026-03-05..2026-05-06 | `ce:GetCostAndUsage` | $0.02 (2 pages) | which service moved |
| 7 | `ce:GetCostAndUsage` DAILY, no record-type filter, group `RECORD_TYPE`, both metrics | account | global | 2026-03-05..2026-05-06 | `ce:GetCostAndUsage` | $0.02 (2 pages) | purchases / unused commitment / fees are not usage |
| 8 | `ce:GetSavingsPlansCoverage` + `ce:GetReservationCoverage` DAILY, EC2, group `INSTANCE_FAMILY` | account | global | same | `ce:GetSavingsPlansCoverage`, `ce:GetReservationCoverage` | $0.02 (2 requests) | an expiry raises on-demand cost with no resource change |
| 9 | `savingsplans:DescribeSavingsPlans` + `ec2:DescribeReservedInstances` | account | us-east-1 | now | `savingsplans:DescribeSavingsPlans`, `ec2:DescribeReservedInstances` | $0 | commitment end dates |
| 10 | `ce:GetCostAndUsage` DAILY, EC2 + 3 usage record types, group `USAGE_TYPE` x `RECORD_TYPE`, `AmortizedCost` + `UnblendedCost` + `UsageQuantity` | account | global | same | `ce:GetCostAndUsage` | $0.02 (2 pages) | dimension of the EC2 change; how each usage type is billed; bill-derived rate |
| 11 | `ec2:DescribeInstances` (LaunchTime >= 2026-04-04) | account | us-east-1 | now | `ec2:DescribeInstances` | $0 | candidate new resources |
| 12 | `cloudtrail:LookupEvents` (`RunInstances`) | account | us-east-1 | 2026-04-04..2026-05-06 (<= 90d) | `cloudtrail:LookupEvents` | $0 | corroborate creation (LaunchTime resets on restart) |

**Total estimated API cost:** $0.09 for the batch (plus $0.01 probe). **IAM:** consolidated list above plus the probe's `sts:GetCallerIdentity`, `iam:ListAccountAliases`, `organizations:DescribeOrganization`.

**GATE 2:** operator approves.

## Step 3 - Execute

- Q5 `cost-anomalies.json`: 1 anomaly (EC2, root cause `BoxUsage:p3.8xlarge`, start 2026-04-26, total impact $18,211.17 including the estimated days). The SP expiry is NOT flagged.
- Q6 `billing-data.json`: 62 daily periods x 5 services. **2026-05-04 and 2026-05-05 return `Estimated: true`** with partial values (amortized usage $4,278.37 and $2,844.21, against $4,594.53 on a full day such as 2026-05-03). They are excluded. Remaining: 60 complete days. Only the EC2 line differs between the two metrics.
- Q7 `record-type-breakdown.json`: 62 daily periods; record types `Usage`, `SavingsPlanCoveredUsage`, `SavingsPlanNegation`, `SavingsPlanRecurringFee`, `Support`, and `SavingsPlanUpfrontFee` on 2026-04-21 only.
- Q8-Q9 `coverage.json`; Q10 `ec2-usage-type.json`; Q11 `new-resources.json` (8 instances, 3 + 3 + 1 + 1 reservations); Q12 `cloudtrail-run-instances.json` (3 events, 7 instances).
- All queries `ok`. Raw output stays in the session.

## Step 4A - Anomaly analysis

### Windows and usage totals

| | Previous 2026-03-05..04-03 | Current 2026-04-04..05-03 | Delta |
|--|----------------------------|---------------------------|-------|
| Usage record types, **AmortizedCost** (sum of Q6) | $66,190.18 | $81,243.50 | **+$15,053.32** |
| Same lines, UnblendedCost (covered usage at on-demand value; reference only) | $71,566.18 | $84,099.50 | +$12,533.32 |

The two metrics differ only on commitment-covered EC2 usage (m5 and r5). Amortized is the one that tells the economic story.

### Non-usage delta, reported as its own line (Q7), both views

| Record type | AmortizedCost prev | cur | delta | UnblendedCost prev | cur | delta |
|-------------|-------------------|-----|-------|--------------------|-----|-------|
| `SavingsPlanRecurringFee` | $0.00 | $320.58 | +$320.58 | $13,824.00 | $7,344.00 | -$6,480.00 |
| `SavingsPlanNegation` | $0.00 | $0.00 | +$0.00 | -$19,200.00 | -$10,200.00 | +$9,000.00 |
| `SavingsPlanUpfrontFee` | $0.00 | $0.00 | +$0.00 | $0.00 | $9,000.00 | +$9,000.00 |
| `Support` | $1,530.00 | $1,530.00 | +$0.00 | $1,530.00 | $1,530.00 | +$0.00 |
| **Non-usage net** | | | **+$320.58** | | | **+$11,520.00** |

Reading the lines:
- `SavingsPlanRecurringFee` under Amortized is UNUSED commitment only: $320.58 = the SageMaker plan at $24.66/day x 13 days (2026-04-21..05-03), because no SageMaker usage appears in the account. The m5 and r5 plans were fully used (no unused amount). Under Unblended the same line is the full hourly fee of the m5 and r5 plans, and it falls -$6,480.00 when the r5 plan ends.
- `SavingsPlanUpfrontFee`: $9,000.00 on 2026-04-21 in Unblended; $0.00 in Amortized (spread as $24.66/day = $9,000.00 / 365). It is a purchase, not usage.
- `SavingsPlanNegation` exists only in Unblended (it cancels the on-demand value of covered usage); it is zero under Amortized.

### Whole-bill check

| View | Previous | Current | Delta |
|------|----------|---------|-------|
| AmortizedCost, all record types | $67,720.18 | $83,094.08 | +$15,373.90 |
| UnblendedCost, all record types | $67,720.18 | $91,773.50 | **+$24,053.32** |

Amortized usage +$15,053.32 + amortized non-usage +$320.58 = +$15,373.90. Unblended = amortized + the $9,000.00 upfront payment not yet amortized (+$8,679.42 = $9,000.00 - $320.58 already recognized) = +$24,053.32.

### Commitment check first (Q8, Q9)

- `describe-savings-plans`: r5 EC2 Instance plan, $15.00/hr ($360.00/day), state `expired`, end 2026-04-15T23:59:59Z. m5 plan active until 2027-02-14. SageMaker plan active from 2026-04-21 (SageMaker only). No RIs.
- Coverage: r5 92.6% (2026-04-14, 04-15) to 0.0% (2026-04-16 onward). Q10 shows why this is not new usage: r5 hours are identical in both windows (16071.30 h each); only the billing changed.

| r5.4xlarge (Q10) | Previous | Current | Delta |
|------------------|----------|---------|-------|
| `SavingsPlanCoveredUsage`, amortized | $10,800.00 | $4,320.00 | -$6,480.00 |
| `Usage` (on-demand) | $1,200.00 | $10,200.00 | +$9,000.00 |
| **r5 usage, amortized** | $12,000.00 | $14,520.00 | **+$2,520.00** |

Net $2,520.00 = 18 days x ($540.00 - $400.00). Had only `Usage` been queried, the r5 delta would have read +$9,000.00, with the offset hidden in the fee and covered/negation lines.

### Decompose by dimension (Q6 then Q10)

- By service: EC2 is the top mover. Other services: RDS -$607.81, S3 +$44.10, Lambda +$5.93, CloudWatch +$1.96.
- By usage type within EC2 (Q10, amortized): `BoxUsage:p3.8xlarge` +$13,008.68; `BoxUsage:r5.4xlarge` +$2,520.00; m5 +$0.00; c5 +$29.71; m6i +$29.97; t3 +$20.78.
- Bill-derived p3 rate (on-demand `Usage` rows): $15,456.68 / 1262.81 instance-hours = $12.24 per instance-hour (rounded to cents).

### Match new resources (Q11, Q12) - the LaunchTime caveat

| Instance | LaunchTime | RunInstances in window (Q12)? | Verdict |
|----------|------------|-------------------------------|---------|
| `i-0a3f7d92c84e61b05`, `i-0b4e8a03d95f72c16`, `i-0c5fa914e06b83d27` | 2026-04-26 14:32..14:38 | yes (ml-platform-bot, 14:31:58) | new |
| `i-0d60c25f17894e38a`, `i-0e71d3628050f49b2`, `i-0f82e4739116a50c3` | 2026-04-27 09:14..09:21 | yes (ml-platform-bot, 09:14:41) | new |
| `i-09a3f58140b27c61d` | 2026-04-28 16:44 | yes (agarcia, 16:44:05) | new |
| `i-00b4169a51c38d72e` | 2026-04-28 16:47 | **no** | **restart**: root volume AttachTime 2026-03-12; ran 2026-03-12..03-20 (200.00 h, $2,448.00) in the previous window |

All 8 are untagged for `Service` / `Owner` (3 + 1 + 1 carry only `Environment=staging`). Cost split of the p3 delta: the 7 new instances cost $13,899.70 in the current window; the restarted instance costs $1,556.98 now against $2,448.00 before, net -$891.02; total +$13,008.68. Treating the whole current-window p3 bill ($15,456.68) as new spend would overstate the delta by $2,448.00, which the fleet already cost in the previous window.

### Rank drivers (absolute dollars) and reconcile

| Rank | Driver | Delta | Dimensions | Candidate explanation | Evidence |
|------|--------|-------|------------|-----------------------|----------|
| 1 | p3.8xlarge ML fleet | +$13,008.68 | EC2, us-east-1, `BoxUsage:p3.8xlarge` | 7 new + 1 restarted instance, untagged | live:5, live:10, live:11, live:12 |
| 2 | r5 on-demand after plan expiry | +$2,520.00 | EC2, us-east-1, `BoxUsage:r5.4xlarge` | Savings Plan ended 2026-04-15; same hours, no resource change | live:8, live:9, live:10 |
| offset | RDS step-down | -$607.81 | RDS, from 2026-04-10 | consistent with a dev instance removed; cause not queried | live:6 |
| unexplained | c5/m6i/t3, S3, Lambda, CloudWatch drift | +$132.45 | several | small, spread across services; not chased | live:6, live:10 |

Check: +$13,008.68 + +$2,520.00 -$607.81 + +$132.45 = +$15,053.32 = net amortized usage delta. Unexplained is 0.9% of the net delta.

## Drill-down decision

No GATE 3 batch is proposed: the resource-state and CloudTrail queries already cover the question. The report records as a Gap that p3 and r5 utilization was not fetched (activity of the fleet is unknown), and the operator may ask for a follow-up batch.

## Step 5 - Compose report

Writes draft to `.culiops/cloud-cost-investigate/acme-prod-anomaly-<YYYYMMDD-HHmm>.md`. Header:

```
**Cloud cost investigation**
**Mode:** anomaly
**Cloud:** aws
**Scope:** 123456789012 (acme-prod) (single) - member
**Regions covered:** us-east-1 (100% of spend in the window)
**Time range:** 2026-04-04 -> 2026-05-03 vs 2026-03-05 -> 2026-04-03 (30 days each; 2026-05-04 and 05-05 excluded: estimated)
**Catalog used:** none
**IaC repo(s):** none
**Date:** 2026-05-08 10:00
```

Findings: net amortized usage delta +$15,053.32; ranked drivers and reconciliation as above; non-usage delta +$320.58 (amortized) as its own line; whole-bill delta +$24,053.32 Unblended / +$15,373.90 Amortized.

### Remediation list (prioritized)

No rows. Anomaly mode explains a change; it does not turn drivers into savings. Neither driver has waste evidence (utilization was not fetched), so both go to Informational as owner decisions. A savings claim needs a waste-mode run (or a GATE 3 utilization batch) on these resources.

**Total estimated savings:** $0.00/mo (high) + $0.00/mo (medium) + $0.00/mo (low).

### Informational / excluded

| Item | Amount | Reason | Evidence |
|------|--------|--------|----------|
| **Owner decision:** 8 untagged p3.8xlarge instances (ML fleet, driver #1) — still needed? | run rate $70,502.40/mo (8 × $12.24 × 720 h, bill-derived $15,456.68 / 1,262.81 h, live:10); 0% SP/RI coverage (live:8) | driver, not waste: `activity-unverified` (utilization not fetched); launched by `ml-platform-bot` / `agarcia` (live:12). No savings claimed | live:8, live:10, live:11, live:12 |
| **Owner decision:** renew the r5 EC2 Instance Savings Plan that expired 2026-04-15 (driver #2) | on-demand premium $140.00/day ≈ $4,200.00/mo while uncovered (live:10) | a new commitment is a purchase decision, outside this read-only skill; only worth it if the r5 fleet stays this size for the term (r5 utilization not fetched). No savings claimed | live:8, live:9, live:10 |
| `SavingsPlanUpfrontFee`, SageMaker plan bought 2026-04-21 (all upfront) | $9,000.00 one-time Unblended; $24.66/day Amortized | purchase, not usage; not a driver of the EC2 increase | live:7, live:9 |
| Unused commitment (`SavingsPlanRecurringFee`, Amortized): SageMaker plan with no SageMaker usage in the account | $320.58 in the window ($24.66/day) | sunk cost of the purchase; worth checking that SageMaker usage is planned (SageMaker usage not queried). No savings claimed | live:7, live:9 |
| p3 fleet spend with no `Service` / `Owner` tag | $15,456.68 in the current window | untagged; owner unknown. Visibility, not waste | live:10, live:11 |
| Estimated days 2026-05-04, 2026-05-05 | not compared | `Estimated: true`, partial values, excluded from both windows | live:6 |

### Gaps

- Utilization of the p3 fleet and the r5 fleet was not fetched (no GATE 3): "running" is not "used".
- The RDS offset (-$607.81) is attributed to a removed dev instance only by its timing (step on 2026-04-10); not verified with `describe-db-instances` or CloudTrail.
- Native Cost Anomaly Detection did not flag the Savings Plan expiry.
- `RunInstances` has no event for `i-00b4169a51c38d72e` in the queried window: the lookup starts at the window start (2026-04-04), so the original 2026-03-12 `RunInstances` (inside the 90-day Event history) was not looked up; the instance is classified a restart from AttachTime and prior p3 usage in Q10, not from its creation event.

### Next steps (informational)

- Ask the ML team (`ml-platform-bot`, `agarcia` per CloudTrail) about the 8 untagged instances, then tag them with `Service` and `Owner`.
- Decide on the r5 Savings Plan renewal after checking r5 utilization.
- Run `cost-optimize-plan` to triage the remediation list before any change.

**GATE 4:** operator approves the report; skill commits only the report file (default-branch / public-remote warning applies).

## Gaps surfaced

(filled during actual dry-run)

## Fixes applied

(filled during actual dry-run)
