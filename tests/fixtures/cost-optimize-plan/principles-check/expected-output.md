**Cost optimization plan**
**Upstream report:** .culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260529-1430.md
**Mode of upstream:** waste
**Scope:** 123456789012 / acme-prod (single)
**Catalog used:** none
**Date:** 2026-05-29 14:38
**Items considered:** 2   **Savings floor:** $5/mo
**Cloud:** aws

## Scoping decisions

Confirmed at GATE 1:
- Upstream report: `.culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260529-1430.md` (waste mode, single-cloud aws).
- 2 items above $5/mo floor; 0 filtered below floor.
- Catalog: none — Dimension 4 (Dependency) will score ⚪ where IaC grep cannot resolve; treated as 🟡-equivalent per tier rules.
- Region: ap-southeast-1.
- **Principles applied this run:** Principle 1 (activity ≠ attachment) is invoked for item #1 (Lambda + EventBridge attachment); Principle 2 (cost-direction check) is invoked for item #2 (mode-switch claim labeled `direction-unverified` upstream).
- Operator approved scope and savings floor. Proceeding to verification planning.

## Verification queries run

| # | Item | API | IAM | Status | Evidence captured |
|---|------|-----|-----|--------|-------------------|
| 1 | Delete cron-backfill-2024 | lambda:GetFunction | lambda:GetFunction | ok | Runtime=python3.11, IaC-managed (terraform/lambda/cron-backfill-2024) |
| 2 | Delete cron-backfill-2024 | cloudwatch:GetMetricStatistics (Lambda.Invocations 30d) | cloudwatch:GetMetricStatistics | ok | Sum=0 across all 30 daily datapoints — **Principle 1 activity check: idle** |
| 3 | Delete cron-backfill-2024 | lambda:ListEventSourceMappings | lambda:ListEventSourceMappings | ok | `EventSourceMappings: []` (function is invoked by EventBridge rules, not event source mappings) |
| 4 | Delete cron-backfill-2024 | events:ListRuleNamesByTarget | events:ListRuleNamesByTarget | ok | 2 EventBridge rules target the function: `legacy-backfill-daily-cron`, `legacy-backfill-weekly-cleanup` — **attachment signals, scored into Dimension 2 (blast radius), NOT Dimension 3** |
| 5 | Delete cron-backfill-2024 | lambda:GetProvisionedConcurrencyConfig | lambda:GetProvisionedConcurrencyConfig | ok | 2 units allocated — source of the $35/mo charge; no keep-warm noise to subtract (Invocations=0 not >0) |
| 6 | Switch orders-canonical to on-demand | dynamodb:DescribeTable | dynamodb:DescribeTable | ok | PROVISIONED, 200 RCU + 100 WCU base, GSI customer-id-index 50 RCU + 25 WCU |
| 7 | Switch orders-canonical to on-demand | cloudwatch:GetMetricStatistics (ConsumedReadCapacityUnits 14d hourly) | cloudwatch:GetMetricStatistics | ok | p99/avg ratio ≈ 1.6 — **steady workload shape** per Principle 2 cost-direction table |
| 8 | Switch orders-canonical to on-demand | cloudwatch:GetMetricStatistics (ConsumedWriteCapacityUnits 14d hourly) | cloudwatch:GetMetricStatistics | ok | p99/avg ratio ≈ 1.07 — even steadier than reads |
| 9 | Switch orders-canonical to on-demand | cloudwatch:GetMetricStatistics (Read+WriteThrottleEvents 14d) | cloudwatch:GetMetricStatistics | ok | Sum=0 each — not under-provisioned |
| 10 | Switch orders-canonical to on-demand | pricing:GetProducts | pricing:GetProducts | ok | Provisioned: $0.000147/RCU-hr, $0.000735/WCU-hr; On-demand: $0.297/M-RRU, $1.4847/M-WRU (ap-southeast-1) |

**Total estimated API cost:** $0.10 (10 GetMetricStatistics + 1 pricing call within free tier).

### Principle 2 cost-direction computation (item #2)

Per `rightsize-dynamodb.md` playbook, mode-switch savings claims require explicit math against observed throughput × real pricing. Computing:

| Component | Provisioned (current) | On-demand (proposed) |
|---|---|---|
| Base RCU (200 × $0.000147/hr × 730 hr) | $21.46/mo | — |
| Base WCU (100 × $0.000735/hr × 730 hr) | $53.66/mo | — |
| GSI RCU (50 × $0.000147/hr × 730 hr) | $5.37/mo | — |
| GSI WCU (25 × $0.000735/hr × 730 hr) | $13.41/mo | — |
| Base read requests (138 RRU/s avg × 86400 × 30 × $0.297/M) | — | $106.20/mo |
| Base write requests (68 WRU/s avg × 86400 × 30 × $1.4847/M) | — | $261.61/mo |
| GSI read requests (≈ 35 RRU/s avg × 86400 × 30 × $0.297/M) | — | $26.95/mo |
| GSI write requests (≈ 17 WRU/s avg × 86400 × 30 × $1.4847/M) | — | $65.38/mo |
| **Total compute cost** | **$93.90/mo** | **$460.14/mo** |

**Result:** on-demand mode at observed throughput would cost ~$366/mo MORE than current provisioned. The upstream $80/mo savings claim is **direction-wrong** — the per-request premium on on-demand exceeds the per-shard reservation cost at this steady ~70% utilization.

**Principle 2 verdict for item #2:** reject the mode-switch action. Flag as 🚫 Do not act with reason `cost-direction-inverted`. Note in plan: a sibling rightsize action (reduce provisioned 200/100 → 160/80, ~20% reduction matching 1.6× p99/avg headroom) is the correct lever and would save ~$15-19/mo — but that's a separate item not in the upstream report; flagged in Next steps for the operator to add to a follow-up audit.

## Plan summary

| Tier | Count | Total est. savings |
|------|-------|--------------------|
| 🟢 Fast wins | 0 | — |
| 🟡 Coordinated | 1 | $35/mo |
| 🔴 Risky | 0 | — |
| 🚫 Do not act | 1 | ($80/mo claim direction-inverted; no savings to capture from this action) |
| ❔ Manual review | 0 | — |

**Total plan savings:** $35/mo actionable.

## 🟢 Fast wins

No items in this tier.

## 🟡 Coordinated

| # | Action | Resource | Savings | Reversibility | Blast | Evidence | Dependency | Source | Rollback |
|---|--------|----------|---------|---------------|-------|----------|------------|--------|----------|
| 1 | Delete Lambda function cron-backfill-2024 | arn:aws:lambda:ap-southeast-1:123456789012:function:cron-backfill-2024 | $35/mo | 🟡 IaC-managed (redeploy ~5-15 min) | 🟡 2 EventBridge rules attached | 🟢 0 Invocations / 30d (Principle 1: attachment scored separately) | ⚪ → 🟡-equivalent (no catalog) | line-item-computation (medium) | Re-apply terraform/lambda/cron-backfill-2024 module; pre-delete take backup via `aws lambda get-function` presigned URL; coordinate EventBridge rule cleanup or deactivation before delete |

> **Ordering hint for item #1:** disable the 2 EventBridge rules (`legacy-backfill-daily-cron`, `legacy-backfill-weekly-cleanup`) before deleting the function. Disabling is fully reversible via `aws events enable-rule`; deletion is not.

> **Principle 1 callout:** the 2 EventBridge rules attached to this function would, under naive triage, suggest the function is "in use" and warrant a 🚫 verdict. Activity-based evidence (Invocations = 0 across 30d) confirms the function is idle. The rules are blast-radius input — they tell us what coordination is needed before deletion, not whether the deletion is warranted.

## 🔴 Risky

No items in this tier.

## 🚫 Do not act

| # | Action | Resource | Original Savings Claim | Reason |
|---|--------|----------|------------------------|--------|
| 2 | Switch DynamoDB orders-canonical to on-demand mode | arn:aws:dynamodb:ap-southeast-1:123456789012:table/orders-canonical | $80/mo (compute-optimizer-preview, low confidence, direction-unverified) | **Principle 2 cost-direction check failed.** At observed steady ~70% utilization (p99/avg ratio 1.6 for reads, 1.07 for writes), provisioned mode costs ~$94/mo; on-demand at the same throughput would cost ~$460/mo. The mode switch would INCREASE cost by ~$366/mo. Upstream Compute Optimizer DynamoDB preview lacked workload-shape input. Reject this action. See "Next steps" for the correct rightsize lever. |

## ❔ Manual review required

No items in this tier — all 2 items had matching playbooks in v1.

## Gaps

- Item #1: EventBridge rule cleanup is a downstream IaC change, not part of this plan's verification. The operator must include rule deletion or deactivation as a coordinated step in the `iac-change-execution` invocation.
- Item #2: no actionable item produced; the correct savings lever (provisioned capacity reduction) requires a fresh `cloud-cost-investigate` query batch the operator did not authorize this run.

## Next steps (informational)

- **Item #1:** open `iac-change-execution` with the cron-backfill-2024 module path and a 2-step plan: (a) disable 2 EventBridge rules; (b) delete the Lambda function and provisioned concurrency config.
- **Item #2:** if savings on `orders-canonical` are still desired, run a fresh `cloud-cost-investigate` waste query targeting "over-provisioned DynamoDB" — the candidate action is reducing provisioned 200/100 RCU/WCU → ~160/80 (~20% reduction matching the observed 1.6× p99/avg headroom). Expected savings ~$15-19/mo, fully reversible. Apply via `cost-optimize-plan` → `iac-change-execution` once that new report exists. **Do NOT** apply the mode-switch suggested in this run's upstream report — the direction is wrong at the current workload shape.
