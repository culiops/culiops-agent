# principles-check — cost-optimize-plan fixture

Two-item report exercising the v0.9 Guiding principles (activity ≠ attachment; verify cost-change direction) end-to-end through the new `delete-lambda.md` and `rightsize-dynamodb.md` playbooks.

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`) in `ap-southeast-1`. The upstream `cloud-cost-investigate` waste audit, run on 2026-05-29, found two candidates that the v0.9 principle guardrails should treat carefully:

1. **`cron-backfill-2024` Lambda function** — $35/mo from provisioned-concurrency. 0 invocations in 30d. **Attached to 2 EventBridge rules**. Under naive triage this attachment would suggest "in use" → 🚫 Do not act. Per Principle 1, attachment is blast radius (Dimension 2), not activity (Dimension 3); the function's Invocations metric is the activity dimension and it's zero. Correct outcome: 🟡 Coordinated (delete possible, but EventBridge rules must be coordinated).

2. **`orders-canonical` DynamoDB table** — 200 RCU / 100 WCU PROVISIONED, sustained ~70% utilization. Compute Optimizer DynamoDB preview suggested "switch to on-demand for $80/mo savings". Per Principle 2, this is a `direction-unverified` claim until cost-direction math is computed. The new `rightsize-dynamodb.md` playbook computes the delta and finds that at the observed steady throughput, on-demand mode would cost ~$366/mo MORE, not save $80/mo. Correct outcome: 🚫 Do not act with reason `cost-direction-inverted`; "Next steps" surfaces the actual savings lever (reduce provisioned capacity ~20%).

## The operator question

> "Triage the cost report at .culiops/cloud-cost-investigate/acme-prod-waste-mixed-20260529-1430.md and build me an execution plan. Use the Principle 1 (activity ≠ attachment) and Principle 2 (verify cost-change direction) guardrails when scoring evidence."

(See `operator-question.md`.)

## What this fixture exercises

- **Principle 1 in cost-optimize-plan triage.** Item #1's Evidence dimension is scored 🟢 (Invocations=0) regardless of the 2 attached EventBridge rules. The attachment lands in Dimension 2 (blast radius), bumping the tier from 🟢 to 🟡 — not bumping it to 🚫 as naive triage would.
- **Principle 2 cost-direction math in `rightsize-dynamodb.md`.** Item #2's mode-switch claim is recomputed from observed throughput × live regional pricing. The math shows the direction is inverted; item lands in 🚫 with the computation visible in the plan as evidence.
- **`direction-unverified` upstream label is resolved downstream.** The upstream report tagged item #2 `confidence: low (direction-unverified)` per the v0.9 cloud-cost-investigate Principle 2 addition. cost-optimize-plan's playbook is responsible for resolving that label — the fixture validates that resolution path.
- **Two v0.9 playbooks (`delete-lambda.md`, `rightsize-dynamodb.md`) end-to-end.** Both new playbooks' query batches, evidence thresholds, reversibility / blast-radius defaults, and rollback notes get exercised.
- **Plan-level Principle 1 / Principle 2 callouts.** The plan output includes inline callouts explaining the discipline applied so the operator can audit.
- **No fabrication of items not in upstream report.** "Next steps" names the correct rightsize lever for orders-canonical (reduce provisioned capacity) but does not inject it as a plan item.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | freeform operator prompt |
| `upstream-report.md` | synthetic cloud-cost-investigate waste report with 2 items + `direction-unverified` label on item #2 |
| `mock-responses/get-function-cron-backfill-2024.json` | Lambda metadata (IaC-managed) |
| `mock-responses/invocations-cron-backfill-2024.json` | 30d Invocations all zero |
| `mock-responses/event-source-mappings-cron-backfill-2024.json` | empty (event sources are EventBridge rules, not mappings) |
| `mock-responses/list-rule-names-by-target-cron-backfill-2024.json` | 2 EventBridge rules attached — the Principle 1 attachment signal |
| `mock-responses/get-provisioned-concurrency-config-cron-backfill-2024.json` | 2 units allocated (source of the $35/mo cost) |
| `mock-responses/describe-table-orders-canonical.json` | PROVISIONED, 200/100 + GSI 50/25 |
| `mock-responses/consumed-rcu-orders-canonical.json` | 14d hourly RCU, p99/avg 1.6 (steady) |
| `mock-responses/consumed-wcu-orders-canonical.json` | 14d hourly WCU, p99/avg 1.07 (steady) |
| `mock-responses/throttle-events-orders-canonical.json` | zero throttles (not under-provisioned) |
| `mock-responses/pricing-dynamodb-ap-southeast-1.json` | live regional pricing for both modes |
| `expected-output.md` | the plan markdown the skill produces at GATE 3 |
| `DRY-RUN-NOTES.md` | gate transitions and acceptance check |

## Expected tier outcomes

| # | Item | Upstream priority | cost-optimize-plan tier | Dominant dimension |
|---|------|-------------------|------------------------|--------------------|
| 1 | Delete Lambda cron-backfill-2024 | 1 ($35/mo) | 🟡 Coordinated | Blast 🟡 (EventBridge attachment) — **Principle 1 prevented this from being a 🚫** |
| 2 | Switch orders-canonical to on-demand | 2 ($80/mo claimed) | 🚫 Do not act | **Principle 2 cost-direction-inverted** — recomputation shows on-demand would cost more |

## Why this fixture was added (v0.9)

Real-case use of cost-optimize-plan after v0.8 surfaced two failure modes the original 5 fixtures did not exercise: naive treatment of attachment as activity, and uncritical trust of mode-switch savings claims. This fixture validates the v0.9 principle additions (`## Guiding principles` section + new playbooks' embedded Principle 1 / Principle 2 thresholds) under realistic inputs.
