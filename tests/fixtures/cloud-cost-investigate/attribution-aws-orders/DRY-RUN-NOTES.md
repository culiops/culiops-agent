# Dry-run of `cloud-cost-investigate` against `attribution-aws-orders`

Expected skill behaviour at each step. Recorded for pre-dry-run reference; "Gaps surfaced" and "Fixes applied" are filled in during the actual dry-run.

Note: `get-rds-database-recommendations` and `get-idle-recommendations` are now in `examples/aws.md` (Step 2B, waste mode); they are not used in this attribution fixture.

## Step 1 - Detect & Scope

- Reads `operator-question.md`. Heuristic: "what does X cost / break it down by resource" gives **attribution mode** (suggested).
- Detects AWS from `AWS_PROFILE` / `~/.aws/` (simulated for the fixture).
- **Scoping probe (GATE 1a)**, 4 read-only calls, 1 Cost Explorer request, about $0.01:

  | # | API | Result in this fixture |
  |---|-----|------------------------|
  | 1 | `sts get-caller-identity` | account `123456789012` |
  | 2 | `iam list-account-aliases` | `acme-prod` |
  | 3 | `organizations describe-organization` | returns an organization whose `MasterAccountId` is `999988887777` (not the caller): **member account**, so Cost Explorer already returns only this account and no `LINKED_ACCOUNT` filter is needed. A payer variant would need that filter on every CE call (and on Q5/Q6 below). |
  | 4 | `ce get-cost-and-usage` MONTHLY, 2026-04, `Service=orders` tag, three usage record types, `AmortizedCost`, group by `REGION` | `us-east-1` $2,698.96 (100%) |

- Scope: single account `123456789012` (`acme-prod`). Regions covered: us-east-1 (100% of `Service=orders` spend). Time range: previous complete billing month 2026-04, plus 2026-03 for the comparison.
- Catalog lookup: finds `.culiops/service-discovery/orders.md`: "Found service catalog for `orders`: 8 resources across ECS, RDS, S3, SQS and Step Functions; tag convention `Service=orders`, `Component=<name>`."
- Scoping summary: mode=attribution, account=`123456789012` (`acme-prod`, member), service=orders, period=2026-04, catalog=orders.md (8 resources), IaC repo=none.

**GATE 1:** operator confirms.

## Step 2C - Attribution mode query plan

Resource-ID-level cost (`get-cost-and-usage-with-resources`) covers only the last 14 days and needs an opt-in, and the window here is a full month, so the skill states that per-resource numbers will come from the `Component` cost-allocation tag instead.

| # | API | Scope | Region(s) | Time | IAM | Est. cost | Why |
|---|-----|-------|-----------|------|-----|-----------|-----|
| 5 | `ce:GetCostAndUsage` | `Service=orders` AND `RECORD_TYPE` in {`Usage`, `DiscountedUsage`, `SavingsPlanCoveredUsage`}, MONTHLY, group `USAGE_TYPE`, metrics `AmortizedCost` + `UsageQuantity` | global | 2026-03-01 to 2026-05-01 | `ce:GetCostAndUsage` | $0.01 (1 page) | service-level totals for both months, by usage type |
| 6 | `ce:GetCostAndUsage` | same filter, group `TAG:Component` x `USAGE_TYPE` | global | 2026-03-01 to 2026-05-01 | `ce:GetCostAndUsage` | $0.01 (1 page) | per-resource cost via the cost-allocation tag |
| 7 | `ce:ListCostAllocationTags` (`--tag-keys Service Component`) | account | global | now | `ce:ListCostAllocationTags` | $0 | a tag-filtered figure or trend that spans a key's activation is `UNVERIFIED` |

The period comparison needs no extra query (both months are in the same window). The untraced check is analysis on Q6 against the catalog.

**Total estimated API cost:** $0.02 for the batch ($0.03 with the scoping probe); Q7 is free.
**IAM permissions needed:** `ce:GetCostAndUsage`, `ce:ListCostAllocationTags` (plus the probe's `sts:GetCallerIdentity`, `iam:ListAccountAliases`, `organizations:DescribeOrganization`).

**GATE 2:** operator approves.

## Step 3 - Execute

- Q5 returns `cost-by-usage-type.json`: 2 periods, 17 usage-type groups in March and 15 in April, status `ok`.
- Q6 returns `cost-by-tag.json`: 2 periods, 19 cells in March and 17 in April, status `ok`.
- Q7 returns `tag-activation.json`: `Service` and `Component` are both `Active`, `LastUpdatedDate` 2025-11-18, before the 2026-03-01 start of the comparison. No figure or trend spans an activation, so the tag-based numbers and the March-to-April comparison are not downgraded.
- Reconciliation done before analysis: Q5 April sum $2,698.96 = Q6 April sum $2,698.96; March $2,478.96 = $2,478.96. No `Component$` (untagged-within-service) group exists in either month.

## Step 4C - Attribution analysis

### Load catalog

```
orders-api            ECS Fargate service         (active)
orders-worker         ECS Fargate service         (active)
orders-prod-db        RDS PostgreSQL, Multi-AZ    (active)
orders-dev-db         RDS PostgreSQL              (active per catalog; to be verified)
orders-events         S3 bucket                   (active)
orders-archives       S3 bucket                   (active)
orders-events-queue   SQS queue                   (active)
orders-fulfillment    Step Functions (STANDARD)   (active)
```

### Cross-reference Q6 April groups against the catalog

| `Component` tag value | 2026-04 | Catalog match? |
|-----------------------|---------|----------------|
| `orders-prod-db` | $922.70 | yes |
| `orders-api` | $676.74 | yes |
| `orders-worker` | $355.47 | yes |
| `orders-events-queue` | $180.00 | yes |
| `orders-events` | $164.00 | yes |
| `orders-fulfillment` | $150.00 | yes |
| `orders-archives` | $134.40 | yes |
| `shared-nat` | $115.65 | **NO: context cost** |

Catalog resources with no April group: `orders-dev-db` (**untraced**).

### Service total

```
     922.70  (orders-prod-db)
     676.74  (orders-api)
     355.47  (orders-worker)
     180.00  (orders-events-queue)
     164.00  (orders-events)
     150.00  (orders-fulfillment)
     134.40  (orders-archives)
= 2,583.31
```

Sum of Q6 groups for the 7 traced catalog resources = **$2,583.31**. Cross-check against Q5: $2,698.96 (all `Service=orders` usage) minus $115.65 (the NAT usage types `USE1-NatGateway-Hours` and `USE1-NatGateway-Bytes`, which no catalog resource uses) = $2,583.31. The two derivations agree exactly, so there is no discrepancy to explain.

### Per-resource, per-usage-type (2026-04, from Q6)

| Resource | Usage type | Quantity | Cost |
|----------|-----------|----------|------|
| `orders-prod-db` | `USE1-Multi-AZUsage:db.r6g.xlarge` | 720 Hrs | $691.20 |
| `orders-prod-db` | `USE1-RDS:Multi-AZ-GP3-Storage` | 800 GB-Mo | $184.00 |
| `orders-prod-db` | `USE1-RDS:ChargedBackupUsage` | 500 GB-Mo | $47.50 |
| `orders-api` | `USE1-Fargate-vCPU-Hours:perCPU` | 11520 vCPU-Hours | $466.33 |
| `orders-api` | `USE1-Fargate-GB-Hours` | 23040 GB-Hours | $102.41 |
| `orders-api` | `USE1-DataTransfer-Out-Bytes` | 1200 GB | $108.00 |
| `orders-worker` | `USE1-Fargate-vCPU-Hours:perCPU` | 7200 vCPU-Hours | $291.46 |
| `orders-worker` | `USE1-Fargate-GB-Hours` | 14400 GB-Hours | $64.01 |
| `orders-events-queue` | `USE1-Requests-Tier1` | 450000000 Requests | $180.00 |
| `orders-events` | `TimedStorage-ByteHrs` | 4000 GB-Mo | $92.00 |
| `orders-events` | `Requests-Tier1` | 12000000 Requests | $60.00 |
| `orders-events` | `Requests-Tier2` | 30000000 Requests | $12.00 |
| `orders-fulfillment` | `USE1-StateTransitions` | 6000000 StateTransitions | $150.00 |
| `orders-archives` | `TimedStorage-GDA-ByteHrs` | 60000 GB-Mo | $59.40 |
| `orders-archives` | `Requests-GDA-Tier1` | 1500000 Requests | $75.00 |

Note: the two Fargate usage types are shared by `orders-api` and `orders-worker` in Q5 (combined $924.21); only the `Component` tag in Q6 separates them. This is why Q6 exists.

### Flags

**Untraced resource: `orders-dev-db`**
- In the catalog (RDS PostgreSQL, `env=dev`). No `Component$orders-dev-db` group in 2026-04.
- Q6 shows a 2026-03 group for it ($27.60: `USE1-InstanceUsage:db.t4g.medium` 312 Hrs, `USE1-RDS:GP3-Storage` 41.94 GB-Mo), which is about 13 days of a month: consistent with a mid-March deletion.
- Skill emits: `UNTRACED: orders-dev-db - in the service catalog but no cost under Service=orders / Component=orders-dev-db for 2026-04. Last cost seen 2026-03 (partial month). Possible causes: deleted, tag removed, or moved to another account; not verified. NOT counted as $0.`
- Offers an optional GATE 3 batch (2 free calls: `rds describe-db-instances --db-instance-identifier orders-dev-db`, CloudTrail `DeleteDBInstance` within 90 days). In this dry-run the operator declines, and the Gaps section records it.

**Context cost: `shared-nat`**
- Billed under `Service=orders` (a VPC module's `default_tags` stamps it) with `Component=shared-nat`, $115.65 in 2026-04. Not in the catalog.
- Skill emits: `CONTEXT COST: shared-nat (NAT gateway, $115.65) - billed under Service=orders but not a catalog resource of orders. EXCLUDED from the orders service total.`

### Period comparison (2026-03 to 2026-04, from Q6)

| Resource | 2026-03 | 2026-04 | Delta |
|----------|---------|---------|-------|
| `orders-api` | $611.44 | $676.74 | +$65.30 |
| `orders-worker` | $220.38 | $355.47 | +$135.09 |
| `orders-prod-db` | $939.24 | $922.70 | -$16.54 |
| `orders-dev-db` | $27.60 | $0.00 | -$27.60 |
| `orders-events` | $155.90 | $164.00 | +$8.10 |
| `orders-archives` | $127.42 | $134.40 | +$6.98 |
| `orders-events-queue` | $152.00 | $180.00 | +$28.00 |
| `orders-fulfillment` | $135.00 | $150.00 | +$15.00 |
| **Service total** | **$2,368.98** | **$2,583.31** | **+$214.33 (+9.0%)** |

- Like-for-like (excluding the deleted dev DB from March): $2,341.38 to $2,583.31, +10.3%.
- Top contributors: `orders-worker` +$135.09 (Fargate vCPU-hours 4464 to 7200, i.e. the fleet grew from about 3 to 5 tasks) and `orders-api` +$65.30. Offsets: `orders-dev-db` -$27.60 (deleted), `orders-prod-db` -$16.54 (720 Multi-AZ instance-hours in April vs 744 in March).
- Driver amounts add up to the net delta: 135.09 + 65.30 + 28.00 + 15.00 + 8.10 + 6.98 - 16.54 - 27.60 = 214.33.
- The NAT line is excluded from both months (context cost): $109.98 to $115.65.

## Step 5 - Compose report

Writes draft to `.culiops/cloud-cost-investigate/orders-attribution-<YYYYMMDD-HHmm>.md`.

Header:

```
**Cloud cost investigation**
**Mode:** attribution
**Cloud:** aws
**Scope:** 123456789012 (acme-prod) (single) - member
**Regions covered:** us-east-1 (100% of Service=orders spend in the window)
**Time range:** 2026-04-01 -> 2026-05-01 (comparison: 2026-03-01 -> 2026-04-01)
**Catalog used:** .culiops/service-discovery/orders.md
**IaC repo(s):** none
```

Queries run (extracted results only):

| # | API | Scope | Region(s) | Time | Status | Rows |
|---|-----|-------|-----------|------|--------|------|
| 1 | `sts get-caller-identity` | account | global | - | ok | 1 |
| 2 | `iam list-account-aliases` | account | global | - | ok | 1 |
| 3 | `organizations describe-organization` | account | global | - | ok | 1 |
| 4 | `ce get-cost-and-usage` (group REGION, tag Service=orders) | 123456789012 | global | 2026-04 | ok | 1 |
| 5 | `ce get-cost-and-usage` (group USAGE_TYPE) | Service=orders, usage record types | global | 2026-03..2026-04 | ok | 17 + 15 |
| 6 | `ce get-cost-and-usage` (group TAG Component x USAGE_TYPE) | Service=orders, usage record types | global | 2026-03..2026-04 | ok | 19 + 17 |
| 7 | `ce list-cost-allocation-tags` (Service, Component) | account | global | now | ok | 2 |

### Findings

> **Orders service - 2026-04**
> Total: **$2,583.31** (live:5, live:6; the two derivations agree exactly)
> Period comparison: $2,368.98 in 2026-03, **+9.0%** month over month (+10.3% like-for-like without the deleted dev DB)

Per-resource breakdown (from the `Component` cost-allocation tag, live:6; both tag keys active since 2025-11-18, live:7):

| # | Resource | Type | Cost (2026-04) | % of total |
|---|----------|------|----------------|------------|
| 1 | `orders-prod-db` | RDS PostgreSQL (Multi-AZ) | $922.70 | 35.7% |
| 2 | `orders-api` | ECS Fargate service | $676.74 | 26.2% |
| 3 | `orders-worker` | ECS Fargate service | $355.47 | 13.8% |
| 4 | `orders-events-queue` | SQS queue | $180.00 | 7.0% |
| 5 | `orders-events` | S3 bucket | $164.00 | 6.3% |
| 6 | `orders-fulfillment` | Step Functions state machine | $150.00 | 5.8% |
| 7 | `orders-archives` | S3 bucket | $134.40 | 5.2% |

### Remediation list (prioritized)

No remediation actions. Attribution mode makes no savings claim.

**Total estimated savings:** $0/mo. Untraced and context items are below, not in this table.

### Informational / excluded

None.

### Untraced / context

| Kind | Resource | Detail |
|------|----------|--------|
| Untraced | `orders-dev-db` (RDS) | In catalog, no 2026-04 cost under `Service=orders`. Last cost 2026-03 ($27.60, partial month). Not counted as $0. Deletion not verified (live:6 only). |
| Context cost | `shared-nat` (NAT gateway) | $115.65 in 2026-04, billed under `Service=orders` but not a catalog resource. Excluded from the service total. |

### Gaps

- `orders-dev-db` deletion not verified: operator declined the optional GATE 3 batch (`describe-db-instances`, CloudTrail `DeleteDBInstance`).
- Commitment coverage was not queried in attribution mode. The cost lookup already includes covered usage at its effective rate (`DiscountedUsage`, `SavingsPlanCoveredUsage`, `AmortizedCost`); none appears here because no commitment applies to these services. Unused commitment (`SavingsPlanRecurringFee` under amortization) is not part of any resource's cost and is not attributed.
- Per-resource numbers depend on the `Component` tag being complete. Both tag keys were activated on 2025-11-18, before the comparison window (live:7), so the March-to-April trend does not span an activation. The reconciliation (Q5 = Q6) shows no untagged remainder in this window, but a resource tagged with the wrong `Component` value would be misattributed.
- Resource-level cost (`get-cost-and-usage-with-resources`) not used: it covers only the last 14 days.

### Next steps (informational)

- Remove `orders-dev-db` from the catalog and from Terraform if it was intentionally deleted.
- Document a cost-split rule for the shared NAT gateway, and fix the VPC module's `default_tags` so it stops carrying `Service=orders`.
- Run `cost-optimize-plan` only if a waste or anomaly investigation produces remediation rows.

**GATE 4:** operator approves the report; skill commits only the report file (default-branch / public-remote warning applies).

## Gaps surfaced

(filled during actual dry-run)

## Fixes applied

(filled during actual dry-run)
