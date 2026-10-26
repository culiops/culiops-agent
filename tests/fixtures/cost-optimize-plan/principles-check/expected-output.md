**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260529-1430.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Target:** account 123456789012 (sts verified, live:0a), region(s) ap-southeast-1
**IaC repo(s):** ~/acme-infra (simulated for this fixture; code refs illustrative)
**Catalog used:** none
**Date:** 2026-05-29 14:38
**Items considered:** 2   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260529-1430.md` (waste mode, single-cloud aws).
- 2 items above $5/mo floor; 0 filtered below floor.
- Target: account `123456789012`, region `ap-southeast-1`. Catalog: none. IaC repo supplied: `~/acme-infra`.
- **Principles applied this run:** Principle 1 (activity ≠ attachment) for item #1 (Lambda + EventBridge / alias / policy wiring); Principle 2 (cost-direction check) for item #2 (mode-switch claim labelled `direction-unverified` upstream); Principle 3 (the upstream 30d window is short for a delete, so item #1 is re-read over 90d hourly).
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

All queries executed 2026-05-29 14:32-14:36 UTC. Row numbering: `0a` target check, `0b-<item>` ownership probe, then `1..N`. Evidence is summarized; no `Environment`, `Code.Location` or raw output recorded (Constraint 14).

| # | Item | API | IAM | Status | Evidence captured (summary) |
|---|------|-----|-----|--------|-----------------------------|
| 0a | all | sts:GetCallerIdentity | sts:GetCallerIdentity | ok | account 123456789012 = `Scope`; region ap-southeast-1 (2026-05-29T14:32Z) |
| 0b-1 | Delete cron-backfill-2024 | lambda:ListTags + IaC grep | lambda:ListTags | ok | no `aws:cloudformation:*` tag; `terraform/lambda/cron-backfill-2024/main.tf:1` → owner **terraform**; artifact retrievable from the repo |
| 0b-2 | Switch orders-canonical to on-demand | dynamodb:ListTagsOfResource + IaC grep | dynamodb:ListTagsOfResource | ok | no CloudFormation tag; `terraform/dynamodb/orders.tf:8` → owner **terraform**; no `ignore_changes` on capacity |
| 1 | Delete cron-backfill-2024 | lambda:GetFunction (`--query` projection: Runtime, LastModified, CodeSha256, PackageType) | lambda:GetFunction | ok | python3.11, last modified 2026-02-14; exists in this account/region (Metrics-rule describe baseline); matches IaC, no drift |
| 2 | Delete cron-backfill-2024 | lambda:ListAliases + ListVersionsByFunction | lambda:ListAliases, ListVersionsByFunction | ok | alias `live` → v7; versions $LATEST, 5, 6, 7 (not a restore path: unqualified delete removes all) |
| 3 | Delete cron-backfill-2024 | cloudwatch:GetMetricData (`Invocations` Sum; `FunctionName` and `Resource=…:live` series; **90d @ 3600s**) | cloudwatch:GetMetricData | ok | **both series empty over 90d: counted as zero** because the target check passed (0a), get-function succeeded in the same account/region (1) and the dimension values came from get-function / list-aliases (1, 2). No `$LATEST` series queried |
| 4 | Delete cron-backfill-2024 | lambda:ListProvisionedConcurrencyConfigs | lambda:ListProvisionedConcurrencyConfigs | ok | provisioned concurrency 2 units on **alias `live`**, READY: the source of the $35/mo; no traffic to subtract (nothing is subtracted in any case) |
| 5 | Delete cron-backfill-2024 | lambda:ListEventSourceMappings | lambda:ListEventSourceMappings | ok | none |
| 6 | Delete cron-backfill-2024 | lambda:GetPolicy (unqualified and `--qualifier live`) + ListFunctionUrlConfigs | lambda:GetPolicy, ListFunctionUrlConfigs | ok | unqualified: no policy; alias `live`: 2 statements, principal `events.amazonaws.com`, SourceArn rules `legacy-backfill-daily-cron`, `legacy-backfill-weekly-cleanup`; no function URL |
| 7 | Delete cron-backfill-2024 | logs:DescribeLogStreams (optional, opted in at GATE 2) | logs:DescribeLogStreams | ok | default log group present, retention 365d (covers the window); last execution event 2026-02-12, older than the window |
| 8 | Switch orders-canonical to on-demand | dynamodb:DescribeTable | dynamodb:DescribeTable | ok | PROVISIONED (no BillingModeSummary: always provisioned): 200 RCU / 100 WCU; GSI `customer-id-index` 50 / 25 |
| 9 | Switch orders-canonical to on-demand | cloudwatch:GetMetricData (Consumed R/W CU, Provisioned R/W CU, throttles; table + GSI; 30d @ 3600s) | cloudwatch:GetMetricData | ok | units converted (Sum ÷ 3600): table read avg 138 / p99 150 CU/s vs 200 provisioned (75%); write avg 68 / p99 73 vs 100 (73%); GSI p99 76% / 76%; p99/avg 1.09 / 1.07; 0 throttles anywhere |
| 10 | Switch orders-canonical to on-demand | cloudwatch:GetMetricData (Consumed R/W CU, 15d @ 60s) | cloudwatch:GetMetricData | ok | per-minute peak read 171 / write 80 CU/s (peak/avg 1.24 / 1.18): steady, not spiky |
| 11 | Switch orders-canonical to on-demand | ce:GetReservationCoverage (DynamoDB, 30d) | ce:Get* | ok | 0% reserved: no commitment absorbs a change |
| 12 | Switch orders-canonical to on-demand | ce:GetCostAndUsage (DynamoDB provisioned line items, 30d) | ce:GetCostAndUsage | ok | bill-derived provisioned rates (fictional account): 180,000 RCU-hours $26.46, 90,000 WCU-hours $66.15 |
| 13 | Switch orders-canonical to on-demand | pricing:GetProducts (AmazonDynamoDB, ap-southeast-1) | pricing:GetProducts | ok | on-demand request-unit rates (fixture values; fallback because the bill has no on-demand usage for this table) |

Optional query declined at GATE 2: `application-autoscaling:DescribeScalingPolicies` (the IaC sets static capacity; no autoscaling) - listed in Gaps.

**Total estimated API cost:** 2 Cost Explorer requests (billed per request) plus free describe/list/Pricing calls and a few GetMetricData calls: well under $0.25.

### Principle 2 cost-direction computation (item #2)

`rightsize-dynamodb.md`: mode-switch claims need explicit math against observed throughput x real rates. Provisioned rates are **bill-derived** (row 12); on-demand rates come from the Pricing API fallback (row 13); both are fixture values, not AWS list prices. Consumed units are the 30d totals from row 9 (in on-demand billing the same quantity is the request units billed). Table and GSI on both sides; 30 days = 720 hours.

| Component | Provisioned (current) | On-demand (proposed) |
|---|---|---|
| Table read: 200 RCU x 720 h x 0.000147 | $21.17 | — |
| Table write: 100 WCU x 720 h x 0.000735 | $52.92 | — |
| GSI read: 50 RCU x 720 h x 0.000147 | $5.29 | — |
| GSI write: 25 WCU x 720 h x 0.000735 | $13.23 | — |
| Table reads: 357.696 M x 0.30 per M | — | $107.31 |
| Table writes: 176.256 M x 1.50 per M | — | $264.38 |
| GSI reads: 90.720 M x 0.30 per M | — | $27.22 |
| GSI writes: 44.064 M x 1.50 per M | — | $66.10 |
| **Total** | **$92.61/mo** | **$465.00/mo** |

Result: `$92.61/mo current → $465.00/mo proposed (+402%, i.e. +$372.39/mo)`. The workload is steady (p99/avg 1.09 reads, 1.07 writes; per-minute peak/avg 1.24) and well utilized (73-76% of provisioned at p99), the shape for which provisioned beats on-demand. The upstream $80/mo saving is direction-wrong. This is a **cost result, not an activity signal**: Evidence is not 🚫; `Realizable` = ✗ cost increase, which tier rule 1 treats as 🚫 because the lever the upstream report recommends is the one that loses.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 1 | $35/mo |
| 🔵 Requires owner confirmation | 0 | — |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 1 | ($80/mo claim direction-inverted; no saving to capture from this action) |
| ❔ Manual review | 0 | — |

**Total plan savings:** $35/mo actionable.

## 🟢 Fast wins

No items in this tier.

## 🟡 Coordinated

| # | Action | Resource | Owner | Savings | Realizable | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|-------|---------|------------|---------------|-------|----------|------------|--------|----------|
| 1 | Delete Lambda function cron-backfill-2024 | arn:aws:lambda:ap-southeast-1:123456789012:function:cron-backfill-2024 | terraform `code:terraform/lambda/cron-backfill-2024/main.tf:1` | $35/mo | ✓ provisioned concurrency billed on-demand, no commitment (upstream line item) | 🟡 terraform + artifact in repo | 🟡 default (wired, see below) | 🟢 live:3,7 | 🟡 code:rules.tf:3,14; live:2,6 | line-item-computation (medium) | Redeploy via IaC (~5-15 min) while the artifact is retrievable; event rules, resource-policy permissions and alias must be recreated from IaC |

**Dimension detail:**
- **Reversibility 🟡** — `delete-lambda.md`: 🟡 when the owner is terraform/lambroll AND the artifact is retrievable (it is: source in the repo, `code:main.tf:1`). There is no 🟢, and no "published version" mitigation: an unqualified `delete-function` removes versions 5-7 and the `live` alias too.
- **Blast 🟡** — playbook default; not bumped to 🟢 because queries 4-6 are not all empty (alias, policy, provisioned concurrency). Not 🔴: no API Gateway / ALB / CloudFront principal and no function URL.
- **Evidence 🟢** — **Principle 1 applied:** the score rests on `Invocations` only. 0 over 90d at hourly granularity on the function and the `live` alias series (live:3; empty counted as zero only because the three Metrics-rule conditions hold), and the optional last-log row passes (last execution 2026-02-12, before the window; live:7). The 2 EventBridge rules in the resource policy, the alias and the provisioned concurrency are attachment and went to Blast / Dependency. Nothing was subtracted from `Invocations` (provisioned-concurrency invocations are real invocations; there are none).
- **Dependency 🟡** — 2 IaC consumers outside the function block (the two rules, `code:rules.tf:3,14`), plus alias and policy (live:2,6).
- **Not idle-ambiguous:** nothing fires on the schedules (0 invocations over 90d, including the weekly rule), so there is no "paused vs decommissioned" ambiguity left for an owner to resolve beyond the Gaps below.

> **Principle 1 callout:** the 2 attached rules would, under naive triage, read as "in use" and push this to 🚫. Activity (`Invocations` = 0 over 90d) says the function is idle; the rules say what must be coordinated before deleting.
>
> **Principle 2 ladder (preferred first step): remove the provisioned concurrency.** The entire $35/mo is the 2 warm units on alias `live` (`code:main.tf:30`). Removing it is reversible, keeps the function and its wiring intact and captures the full saving; the delete can follow later once the rules are cleaned up. Ordering: remove/disable the 2 rules in the same IaC change as the delete.

## 🔵 Requires owner confirmation

No items in this tier.

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

| # | Action | Resource | Savings claimed | Disqualifying evidence |
|---|--------|----------|-----------------|------------------------|
| 2 | Switch DynamoDB orders-canonical to on-demand mode | arn:aws:dynamodb:ap-southeast-1:123456789012:table/orders-canonical | $80/mo (compute-optimizer-preview, low confidence, direction-unverified) | **`cost-direction-inverted` (Principle 2).** At the observed steady throughput (live:9,10) provisioned costs $92.61/mo (bill-derived, live:12) and on-demand would cost $465.00/mo (live:12,13): **+$372.39/mo (+402%)**. Upstream preview lacked workload-shape input. No commitment is involved (live:11). Reject this action. |

**Dimension detail (#2):** Owner terraform (`code:terraform/dynamodb/orders.tf:8`). **Tier rule 1, second clause: the change raises cost (`Realizable` ✗).** This is not evidence of use and Evidence is not scored 🚫. The utilization rows of `rightsize-dynamodb.md` belong to the capacity-reduction lever (at 73-76% they would be ⚪ `marginal`); they are not the basis for this tier. Rule 1 fires first, so the other dimensions are recorded for information only. The upstream recommended exactly the lever that loses, so the item goes to 🚫 rather than being dropped into Gaps.

## ❔ Manual review required

No items in this tier — both items had matching playbooks.

## Drift

| # | Resource | Code (`code:`) | Live (`live:`) | Note |
|---|----------|----------------|----------------|------|
| 1 | cron-backfill-2024 | `runtime = "python3.11"` (`main.tf:1`), PC 2 on alias `live` (`main.tf:30`) | python3.11 (live:1), PC 2 on `live` (live:4) | none — matches |
| 2 | orders-canonical | `PROVISIONED`, 200 / 100, GSI 50 / 25 (`orders.tf:8`) | same (live:8) | none — matches |

## Gaps

- Item #1: EventBridge rule state (enabled / disabled) is not part of the playbook's queries; 0 invocations over 90d shows no schedule has fired. The 2 rules must be removed together with the function (same IaC change).
- Item #2: no cheaper reversible lever is supported by the evidence. The capacity-reduction lever (dropped, not proposed) needs a required utilization row <= 40%; between 40% and 80% the row is ⚪ `marginal` (`rightsize-dynamodb.md`), and this table runs at 73-76% p99 with a per-minute read peak of 171 CU/s (85% of 200). Measured headroom: about 24-27% at p99. Result: the table is correctly sized; no saving is claimed.
- Item #2: the `direction-unverified` label from the upstream report is resolved here as ✗ (cost increases).
- Optional `application-autoscaling:DescribeScalingPolicies` query declined at GATE 2 (static capacity in IaC); it does not affect any tier.
- Window: upstream used 30d for the Lambda; this plan re-read it over 90d (Principle 3).

## Next steps (informational)

- **Item #1:** open `iac-change-execution` with module `terraform/lambda/cron-backfill-2024`. Suggested sequence (Principle 2 ladder): (a) remove the provisioned concurrency (`main.tf:30`) — captures the full $35/mo, reversible; (b) later, remove the 2 rules (`rules.tf:3,14`) and delete the function, alias and versions in one change. `pre-flight` clearance is still mandatory.
- **Item #2:** do NOT switch to on-demand. Leave the table as is. If you want to look for savings on it, re-run `cloud-cost-investigate` for a real lever; none is indicated by this plan.
