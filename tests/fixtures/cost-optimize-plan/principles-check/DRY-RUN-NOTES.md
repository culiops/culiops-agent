# Dry-run notes — principles-check

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides path to upstream report (`operator-question.md`) and explicit instruction to apply Principle 1 + Principle 2 guardrails. Skill loads `upstream-report.md`, extracts 2-item Remediation list, reads `**Cloud:** aws`, `**Scope:** 123456789012 / acme-prod`. Applies $5/mo floor — both items pass. No catalog at `.culiops/service-discovery/` — Dimension 4 will score ⚪ (treated as 🟡-equivalent). Operator approves scope. Approved.

2. **Step 2 (Plan verification batch)** — Skill matches both items to playbooks:
   - Item #1 → `examples/aws/delete-lambda.md` (added v0.9)
   - Item #2 → `examples/aws/rightsize-dynamodb.md` (added v0.9, includes mandatory Principle 2 cost-direction math)

   Batch consolidates 10 queries (5 per item) with deduplication. Total estimated API cost ~$0.10 (10 GetMetricStatistics within free tier + 1 pricing call free). IAM consolidated: `lambda:GetFunction`, `lambda:ListEventSourceMappings`, `lambda:GetProvisionedConcurrencyConfig`, `events:ListRuleNamesByTarget`, `dynamodb:DescribeTable`, `cloudwatch:GetMetricStatistics`, `pricing:GetProducts`. GATE 2 approved.

3. **Step 3 (Execute queries)** — All 10 queries succeed. Evidence buffered:
   - `get-function-cron-backfill-2024.json` → IaC-managed, terraform module path
   - `invocations-cron-backfill-2024.json` → Sum=0 across 30d, all datapoints
   - `event-source-mappings-cron-backfill-2024.json` → empty array
   - `list-rule-names-by-target-cron-backfill-2024.json` → 2 EventBridge rules (attachment)
   - `get-provisioned-concurrency-config-cron-backfill-2024.json` → 2 units (no keep-warm noise to subtract since Invocations=0)
   - `describe-table-orders-canonical.json` → PROVISIONED, 200/100 RCU/WCU + GSI 50/25
   - `consumed-rcu-orders-canonical.json` → p99/avg ratio 1.6 (steady)
   - `consumed-wcu-orders-canonical.json` → p99/avg ratio 1.07 (steady)
   - `throttle-events-orders-canonical.json` → zero throttles (not under-provisioned)
   - `pricing-dynamodb-ap-southeast-1.json` → live regional pricing for both modes

4. **Step 4 (Triage)** — Per-item scoring:

   **Item #1 (Delete cron-backfill-2024):**
   - Dimension 1 Reversibility: 🟡 (IaC-managed, ~5-15 min RTO; default per delete-lambda.md)
   - Dimension 2 Blast radius: 🟡 (2 EventBridge rules attached; default 🟡 bumped via list-rule-names-by-target result)
   - Dimension 3 Evidence of no-use: **🟢** (Invocations Sum=0 across 30d — *Principle 1 check: EventBridge rule attachment is NOT this dimension's input*)
   - Dimension 4 Dependency footprint: ⚪ no catalog (treated as 🟡-equivalent)
   - Tier rule: any 🟡 → 🟡 Coordinated. Final: **🟡 Coordinated**.

   **Item #2 (Switch orders-canonical to on-demand):**
   - Per `rightsize-dynamodb.md`, mode-switch claims must include cost-direction math. Skill computes:
     - Current provisioned cost ≈ $94/mo (RCU + WCU + GSI)
     - Proposed on-demand cost at observed throughput ≈ $460/mo
     - Delta: **+$366/mo (cost INCREASES)** — direction inverted from upstream claim
   - Per playbook's Principle 2 threshold table: "computed cost delta < 20% savings OR computed cost INCREASES" → 🚫 trigger for the mode-switch action specifically.
   - Tier rule: 🚫 dimension → **🚫 Do not act** with reason `cost-direction-inverted`.

5. **GATE 3 (Plan review)** — Plan drafted. Operator reviews:
   - Item #1 in 🟡 with Principle 1 callout explaining why EventBridge attachment did NOT bump Evidence to 🚫.
   - Item #2 in 🚫 with full cost-direction math table embedded as evidence.
   - "Next steps" section names the correct lever for orders-canonical (provisioned capacity reduction ~20% = ~$15-19/mo) but does NOT inject it as a plan item (the savings claim doesn't exist in the upstream report; skill cannot fabricate one).

   Operator approves. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260529-1438.md`.

## What this fixture validates

- **Principle 1 (activity ≠ attachment) in cost-optimize-plan triage.** The skill correctly scores Dimension 3 = 🟢 based on `Invocations=0`, despite the function being attached to 2 EventBridge rules. The attachment is routed into Dimension 2 (blast radius) where it belongs, NOT Dimension 3. The plan explicitly calls this out so the operator sees the discipline at work.

- **Principle 2 (cost-direction verification) in rightsize-dynamodb playbook.** The skill computes the per-mode cost delta from observed throughput × real (fetched) pricing, finds the upstream "switch to on-demand" claim would actually INCREASE cost, and lands the action in 🚫 with the math shown. No silent rejection; the operator sees both the upstream claim and the recomputation.

- **`direction-unverified` upstream label honored.** The upstream report's item #2 carried `confidence: low (direction-unverified)` per the v0.9 cloud-cost-investigate Principle 2 rule. cost-optimize-plan's playbook recomputed and resolved the label — either to 🟢 actionable (would have been if math confirmed savings) or 🚫 (direction-inverted, as here). No item with `direction-unverified` lands in a 🟢 / 🟡 / 🔴 actionable tier without the math being run.

- **New v0.9 playbooks (`delete-lambda.md`, `rightsize-dynamodb.md`) used end-to-end.** Both playbooks' query batches, evidence threshold tables, reversibility / blast-radius defaults, and rollback notes are exercised. Verifies the playbooks parse correctly and produce coherent triage.

- **Plan never fabricates items not in upstream report.** The "correct" rightsize lever for orders-canonical (reduce provisioned capacity) is named in Next steps but not injected as a plan item — that would require a new cloud-cost-investigate query batch with its own evidence + savings number.

- **Multi-item batch dedup mechanics still work.** The 10-query batch has no cross-item dedup opportunities in this fixture (Lambda + DynamoDB use disjoint APIs), but the consolidation + IAM-list aggregation path is exercised.

## Acceptance check

A reviewer confirms: (a) item #1 lands in 🟡 Coordinated with Evidence scored 🟢 and Blast scored 🟡 — NOT Evidence 🚫 / Blast 🟢 (which would indicate Principle 1 was misapplied); (b) item #2 lands in 🚫 Do not act with the full cost-direction math table visible in the plan, and the reason is `cost-direction-inverted`; (c) Next steps names the provisioned-capacity-reduction lever for orders-canonical without inserting it as a plan item; (d) the plan never claims actionable savings from item #2 (the $80/mo upstream claim is shown as "Original Savings Claim" only, with explicit rejection); (e) Principle 1 / Principle 2 are named explicitly in the plan's reasoning so the operator can audit the discipline.

## Why this fixture was added (v0.9)

After v0.8 shipped, real-case use of cost-optimize-plan surfaced two failure modes that the original 5 fixtures did not exercise:

1. Items with strong attachment signals (EventBridge rules, event source mappings, IAM trust policies) being incorrectly assumed "in use" without checking activity metrics — the Principle 1 failure mode.
2. Mode-switch savings claims from upstream recommenders (Compute Optimizer DynamoDB preview, Cost Optimization Hub) being trusted at the wrong workload shape — the Principle 2 cost-direction failure mode.

This fixture exercises both modes in a single 2-item batch, validating that the v0.9 principle additions to SKILL.md and the new delete-lambda / rightsize-dynamodb playbooks produce the right behavior under realistic inputs.
