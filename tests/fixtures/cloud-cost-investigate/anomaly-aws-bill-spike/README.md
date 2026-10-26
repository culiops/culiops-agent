# anomaly-aws-bill-spike - cloud-cost-investigate fixture

Anomaly-mode fixture with three overlapping causes of a bill increase, only one of which is a new resource that a "new resources" sweep can find. Usage is measured the way the skill now defines it: the three usage record types (`Usage`, `DiscountedUsage`, `SavingsPlanCoveredUsage`) at `AmortizedCost`.

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`, member account, single region us-east-1). Fixture "now" is 2026-05-08. The skill compares two equal 30-day windows of complete Cost Explorer days: previous 2026-03-05..2026-04-03 and current 2026-04-04..2026-05-03. Amortized usage moves from $66,190.18 to $81,243.50 (net +$15,053.32). Three things happened in the current window:

1. **ML compute fleet (the #1 usage driver).** Eight `p3.8xlarge` instances (bill-derived $12.24 per instance-hour, never covered by a commitment) appear on 2026-04-26..04-28, launched by the ML team via `ml-platform-bot` / `agarcia`. None has a `Service` or `Owner` tag. One of the eight (`i-00b4169a51c38d72e`) is not new: it ran 2026-03-12..03-20, was stopped, and was restarted on 2026-04-28, so its `LaunchTime` matches the window although CloudTrail has no `RunInstances` for it there.
2. **Savings Plan expiry (a driver with no resource change).** The EC2 Instance Savings Plan that covered most of the `r5` fleet ended on 2026-04-15. Until then r5 usage was `SavingsPlanCoveredUsage` at the plan's effective rate (amortized $360.00/day, $500.00/day at on-demand value) plus $40.00/day of on-demand overflow. From 2026-04-16 the same instances (same hours) are all on-demand `Usage` at $540.00/day. The economic change is $140.00/day for 18 days = $2,520.00. Because the covered line is in the usage set, the driver is NOT overstated by the recurring-fee drop: that fee is not "usage" and, under amortization, is only unused commitment (none for the m5 and r5 plans, which were fully used).
3. **All-upfront purchase (NOT a usage driver).** A SageMaker Savings Plan bought on 2026-04-21 is one `SavingsPlanUpfrontFee` of $9,000.00 in `UnblendedCost` on that single day. In `AmortizedCost` the upfront fee is $0.00 and the cost is spread at $24.66 per day ($9,000.00 / 365). No SageMaker usage appears in the account, so the amortized daily amount shows as unused commitment (`SavingsPlanRecurringFee`), $320.58 over the 13 days to 2026-05-03.

Smaller facts: an RDS dev instance deleted on 2026-04-10 gives a -$607.81 offset; the last two returned days (2026-05-04, 2026-05-05) are `Estimated` and partial. The m5 Savings Plan (active until 2027-02-14) covers a constant $100.80/day amortized ($140.00/day on-demand value) in both windows: it contributes $0.00 to the delta.

## The operator question

> "Our AWS bill spiked from $68K to $92K - find out why. We need to identify what changed and which team or workload is responsible so we can decide whether to keep it running or shut it down."

(See `operator-question.md`.) The operator's figures are the cash bill (Unblended, whole bill: $67,720.18 → $91,773.50), which includes the one-time $9,000.00 upfront purchase. The skill's primary view is amortized usage ($66,190.18 → $81,243.50, +$15,053.32); the reconciliation below shows how the two meet. "Last month" and "this month" are also not calendar months: calendar April alone is $73,838.42 and May has only 3 complete days ($13,773.54). The skill states explicit dates and does not compare a calendar month with month-to-date or forecast.

## What this fixture exercises

- **Mode detection from question phrasing:** "spiked / why" gives anomaly mode (suggested at GATE 1).
- **Scoping probe (GATE 1a):** identity, alias, `organizations describe-organization` (member account, so no `LINKED_ACCOUNT` filter), CE by `REGION` (us-east-1 only). `scoping-probe.json`.
- **Equal complete windows:** the query ends 2 days before "now" (End 2026-05-06 exclusive); the response flags 2026-05-04 and 2026-05-05 `Estimated: true` (partial values), the skill drops them, leaving 60 complete days = 2 x 30. No forecast, no month-to-date.
- **Usage = three record types at AmortizedCost:** filtering `Usage` alone would drop the covered m5 and r5 usage and turn the plan expiry into a $9,000.00 "new on-demand spend" (the recurring-fee drop then sits on the other side of the ledger). With covered usage included at its effective rate the r5 driver is $2,520.00.
- **Non-usage lines on their own, in both views:** `record-type-breakdown.json` has `AmortizedCost` and `UnblendedCost` for every record type. The SageMaker $9,000.00 upfront fee is a single-day Unblended item and an amortized $24.66/day unused-commitment line.
- **Commitment expiry:** `coverage.json` shows r5 coverage falling from 92.6% to 0.0% on 2026-04-16 with unchanged r5 hours, and `describe-savings-plans` shows the plan `expired`, end 2026-04-15. The new-resource sweep cannot explain this driver.
- **Native anomaly detection:** `cost-anomalies.json` flags only the p3 spend (a lead, not the whole story).
- **LaunchTime caveat:** 8 instances match `LaunchTime >= window start`; CloudTrail `RunInstances` corroborates 7; `i-00b4169a51c38d72e` is a restart (root volume `AttachTime` 2026-03-12, prior p3 usage of 200.00 hours in the previous window).
- **Driver decomposition:** drivers + offsets + unexplained remainder sum exactly to the net amortized usage delta ($15,053.32); the whole-bill check in `UnblendedCost` reconciles to +$24,053.32.
- **Remediation list:** two low-confidence rows with `Owner`, `Realizable`, `Rate` and `live:` evidence; tagging and purchase accounting go to Informational / Next steps, not the table. No delete recommendation.
- **Not exercised:** utilization metrics for the p3 fleet are not fetched (no GATE 3); the report lists that as a Gap.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | The freeform cost question to feed the skill |
| `scoping-probe.json` | Query 1-4: identity, alias, organization (member), CE by region (AmortizedCost, usage record types) |
| `cost-anomalies.json` | Query 5: native `ce get-anomalies` (one finding: the p3 fleet) |
| `billing-data.json` | Query 6: CE DAILY by SERVICE, the three usage record types, `AmortizedCost` + `UnblendedCost`, 62 days, last 2 days `Estimated` |
| `record-type-breakdown.json` | Query 7: CE DAILY by `RECORD_TYPE`, both metrics (usage record types, unused commitment, negation, upfront fee, Support) |
| `coverage.json` | Queries 8-9: Savings Plans coverage around the expiry, plan list (one expired, one all-upfront purchase), no RIs |
| `ec2-usage-type.json` | Query 10: CE DAILY by `USAGE_TYPE` x `RECORD_TYPE` for EC2 (amortized, unblended, hours) |
| `new-resources.json` | Query 11: `describe-instances`, 8 p3.8xlarge with `BlockDeviceMappings` (one restart) |
| `cloudtrail-run-instances.json` | Query 12: `RunInstances` events (7 of 8 instances; none for the restart) |
| `DRY-RUN-NOTES.md` | Expected skill behaviour at each step |

## Expected output

| View | Previous 30d | Current 30d | Delta |
|------|--------------|-------------|-------|
| **Usage record types, AmortizedCost (primary)** | $66,190.18 | $81,243.50 | **+$15,053.32** |
| Non-usage, AmortizedCost (unused commitment +$320.58, Support unchanged at $1,530.00) | $1,530.00 | $1,850.58 | +$320.58 |
| Whole bill, AmortizedCost | $67,720.18 | $83,094.08 | +$15,373.90 |
| Whole bill, **UnblendedCost** (cash view) | $67,720.18 | $91,773.50 | **+$24,053.32** |

Ranked usage drivers (absolute dollars, AmortizedCost):

| Rank | Driver | Delta |
|------|--------|-------|
| 1 | `BoxUsage:p3.8xlarge`: ML fleet (7 new + 1 restarted) | +$13,008.68 |
| 2 | `BoxUsage:r5.4xlarge`: Savings Plan expired 2026-04-15, same instances now on-demand (covered -$6,480.00, on-demand +$9,000.00) | +$2,520.00 |
| offset | RDS: dev instance deleted 2026-04-10 (cause not verified) | -$607.81 |
| unexplained | c5 / m6i / t3 EC2, S3, Lambda, CloudWatch drift (m5 plan: +$0.00) | +$132.45 |
| **Sum** | | **+$15,053.32** |

Whole-bill reconciliation in `UnblendedCost`: amortized usage +$15,053.32 + amortized non-usage +$320.58 = amortized whole bill +$15,373.90; plus the $9,000.00 upfront payment not yet amortized (+$8,679.42 = $9,000.00 - $320.58) = **+$24,053.32** Unblended.

The same bill read as Unblended (not the skill's primary view) scatters the r5 expiry across three lines: covered usage -$9,000.00, negation +$9,000.00, recurring fee -$6,480.00, on-demand usage +$9,000.00. Unblended usage (covered at on-demand value) is $71,566.18 to $84,099.50, +$12,533.32, with non-usage +$11,520.00; the total is the same +$24,053.32.

Remediation list: **empty** — anomaly drivers are not savings. The ML fleet (run rate $70,502.40/mo at the bill-derived $12.24/hr) and the r5 Savings Plan renewal (on-demand premium ≈ $4,200.00/mo) are listed under Informational as **owner decisions**, with no savings claimed. Total counted: $0.00 high, $0.00 medium, $0.00 low.
