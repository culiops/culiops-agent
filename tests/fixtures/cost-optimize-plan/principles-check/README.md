# principles-check — cost-optimize-plan fixture

Two-item report exercising the Guiding principles (activity ≠ attachment; verify cost-change direction; scale the window) end-to-end through `delete-lambda.md` and `rightsize-dynamodb.md`.

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`) in `ap-southeast-1`. The upstream waste audit (2026-05-29) found two candidates:

1. **`cron-backfill-2024` Lambda function** — $35/mo, all of it **provisioned concurrency (2 units) on the alias `live`** (PC cannot exist on `$LATEST`). Zero invocations. The resource-based policy shows **2 EventBridge rules** as invokers, plus the alias. Under naive triage this wiring means "in use" → 🚫. Per Principle 1 it is attachment (blast / dependency), not activity. `Invocations` over 90d hourly is empty, and an empty Lambda `Invocations` series counts as zero only because the Metrics-rule conditions hold (target check passed, `get-function` succeeded, dimensions taken from describe output). The playbook subtracts nothing from `Invocations` and gives no "published version" credit. Correct outcome: **🟡 Coordinated**.

2. **`orders-canonical` DynamoDB table** — 200 RCU / 100 WCU provisioned (+ GSI 50 / 25) at 73-76% p99 utilization. Compute Optimizer's preview suggested "switch to on-demand, $80/mo". The playbook converts units (hourly `Sum` ÷ 3600 vs provisioned CU/s), derives provisioned rates from the bill and on-demand rates from the Pricing API fallback, and finds on-demand would cost **~$372/mo MORE**. Correct outcome: **🚫 Do not act** with reason `cost-direction-inverted`.

**IaC repo: simulated** (`~/acme-infra`); `mock-responses/iac-grep-simulated.json` stands in for the grep and the `code:` refs are illustrative. All rates in the mocks are **fictional fixture values**, not AWS list prices.

## The operator question

> "Triage the cost report at .culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260529-1430.md and build me an execution plan. Use the Principle 1 (activity ≠ attachment) and Principle 2 (verify cost-change direction) guardrails when scoring evidence."

(See `operator-question.md`.)

## What this fixture exercises

- **Principle 1:** Evidence 🟢 from `Invocations` alone; EventBridge rules, alias, policy and PC go to Blast / Dependency. No keep-alive subtraction exists any more: provisioned-concurrency invocations are real invocations.
- **Empty ≠ zero (Constraint 12):** the empty `Invocations` series is accepted as zero only with all three Metrics-rule conditions satisfied, stated in the plan.
- **Window scaling (Principle 3):** the upstream 30d view is re-read over 90d hourly (one `get-metric-data` call; hourly 90d would exceed `get-metric-statistics`' 1,440 cap).
- **Optional evidence row:** last log stream (`describe-log-streams`), opted in and passing. Dimension 3: an optional row that ran must pass; one declined at GATE 2 would not block 🟢 and would be listed in Gaps. Only an optional row that ran and came back ⚪ (e.g. log group retention shorter than the window) would make Evidence 🟡, and a delete with Evidence not 🟢 then lands in 🔴 (tier rule 3).
- **Reversibility per `delete-lambda.md`:** 🟡 (terraform + retrievable artifact); never 🟢; unqualified delete removes all versions and aliases.
- **Principle 2 ladder:** remove the provisioned concurrency first (it is the entire $35/mo).
- **Principle 2 cost-direction math** with correct units, bill-derived rates, Pricing API fallback, `Realizable` ✗; resolves the upstream `direction-unverified` label. Tier rule 1 → 🚫 because the recommended lever is the one that loses.
- **Secrets rule:** `get-function` is a `--query` projection; `Environment` and `Code.Location` never appear.
- **No fabrication:** no capacity-reduction item is injected; the evidence in fact does not support one (73-76% utilization, per-minute peak 171/200).

## Files in this fixture

Row = the `#` in the plan's "Verification queries run" table.

| File | Row | Purpose |
|------|-----|---------|
| `operator-question.md` | — | freeform operator prompt |
| `upstream-report.md` | — | synthetic waste report; item #2 carries `direction-unverified` |
| `mock-responses/sts-get-caller-identity.json` | 0a | target check |
| `mock-responses/iac-grep-simulated.json` | 0b-1, 0b-2, Dim 4 | simulated IaC grep |
| `mock-responses/list-tags-cron-backfill-2024.json` | 0b-1 | Lambda tags |
| `mock-responses/list-tags-of-resource-orders-canonical.json` | 0b-2 | DynamoDB tags |
| `mock-responses/get-function-cron-backfill-2024.json` | 1 | `--query` projection only (no Environment / Code.Location) |
| `mock-responses/list-aliases-and-versions-cron-backfill-2024.json` | 2 | alias `live` → v7 |
| `mock-responses/get-metric-data-invocations-cron-backfill-2024-90d-hourly.json` | 3 | **empty** Invocations series (function + alias) |
| `mock-responses/list-provisioned-concurrency-configs-cron-backfill-2024.json` | 4 | PC 2 units on alias `live` |
| `mock-responses/list-event-source-mappings-cron-backfill-2024.json` | 5 | none |
| `mock-responses/get-policy-cron-backfill-2024.json` | 6 | 2 EventBridge invokers on the alias; no function URL |
| `mock-responses/describe-log-streams-cron-backfill-2024.json` | 7 | optional: last event before the window |
| `mock-responses/describe-table-orders-canonical.json` | 8 | PROVISIONED, 200/100 + GSI 50/25 |
| `mock-responses/get-metric-data-orders-canonical-30d-hourly.json` | 9 | consumed vs provisioned CU/s (units converted), throttles |
| `mock-responses/get-metric-data-orders-canonical-15d-per-minute.json` | 10 | burst view (steady) |
| `mock-responses/get-reservation-coverage-dynamodb.json` | 11 | 0% reserved |
| `mock-responses/bill-derived-rates-orders-canonical.json` | 12 | bill-derived provisioned rates (fictional) |
| `mock-responses/get-products-dynamodb-on-demand-ap-southeast-1.json` | 13 | Pricing API fallback for on-demand rates (fixture values) |
| `expected-output.md` | — | the plan at GATE 3 |
| `DRY-RUN-NOTES.md` | — | gate transitions and acceptance check |

## Expected tier outcomes

| # | Item | Upstream priority | Tier | Dominant dimension |
|---|------|-------------------|------|--------------------|
| 1 | Delete Lambda cron-backfill-2024 | 1 ($35/mo) | 🟡 Coordinated | Reversibility 🟡 / Blast 🟡 / Dependency 🟡; Principle 1 kept it out of 🚫 |
| 2 | Switch orders-canonical to on-demand | 2 ($80/mo claimed) | 🚫 Do not act | Principle 2: `cost-direction-inverted` (Realizable ✗), tier rule 1 |

## Why this fixture was added

Real-case use of cost-optimize-plan surfaced two failure modes: attachment treated as activity, and uncritical trust of mode-switch savings claims. The fixture has since been updated to the current playbooks: provisioned concurrency lives on an alias, no keep-alive subtraction, no "published version" mitigation, and the DynamoDB unit conversion and rate sourcing are done per `rightsize-dynamodb.md`.
