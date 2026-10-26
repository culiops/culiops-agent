# Dry-run notes — principles-check

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides the upstream report path and asks for the Principle 1 + 2 guardrails. Skill loads `upstream-report.md`, extracts 2 items, reads `**Cloud:** aws`, `**Scope:** 123456789012 / acme-prod`; target = account 123456789012, region ap-southeast-1. $5/mo floor: both pass. No catalog. Operator supplies `~/acme-infra` (simulated). Approved.

2. **Step 2 (Plan verification batch)** — Item #1 → `delete-lambda.md`; item #2 → `rightsize-dynamodb.md`. Query 0 first (`0a`, `0b-1`, `0b-2`). The upstream Lambda window is 30d, a delete needs 60-180d, so the batch reads 90d hourly (one `get-metric-data` call). The alias query runs before the metrics query because the per-alias series needs the alias name. The Lambda playbook's optional last-log-stream query is opted in (declining it would not block Evidence 🟢; it would be listed in Gaps). The DynamoDB optional autoscaling query is not selected (static capacity in IaC). Rates: provisioned from the bill (`ce:GetCostAndUsage`), on-demand from the Pricing API fallback; commitment coverage via `ce:GetReservationCoverage`. Operator approves 13 numbered queries plus Query 0. Per Step 2, each item's playbook queries are listed as conditional on Query 0b; here no owner routes to ❔, so none is skipped.

3. **Step 3 (Execute)** — `0a` passes. `0b`: both owners terraform (no ❔ routing). All queries succeed. The `Invocations` series is empty; Constraint 12 is applied explicitly: target check ✓, `get-function` ✓ same account/region, dimension values from describe / list-aliases ✓ → counted as zero. Secrets rule: `get-function` is projected, nothing sensitive is recorded.

4. **Step 4 (Triage)** — rules in order:
   - **#1:** Rev 🟡 (terraform + retrievable artifact; no 🟢 for Lambda), Blast 🟡 (default; PC, alias, policy present), Evidence 🟢 (`Invocations` empty-as-zero over 90d, last log event before the window; attachment NOT scored here), Dep 🟡 (2 IaC rule consumers, alias, policy). Rule 1 no, rule 2 no (not idle-ambiguous: nothing fires on the schedules), rule 3 no (no 🔴; Evidence is 🟢 so "delete AND Evidence not 🟢" does not fire), rule 4 yes → **🟡**.
   - **#2:** Principle 2 math (units: Sum ÷ 3600 vs provisioned CU/s; 30d totals for on-demand request units): provisioned $92.61 vs on-demand $465.00, +$372.39 → `Realizable` ✗. Tier rule 1, second clause → **🚫**. Reason `cost-direction-inverted`.
   - Plan notes the Principle 2 ladder for #1 (remove PC first) but does not add a plan item.

5. **GATE 3 (Plan review)** — Operator approves. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260529-1438.md`, uncommitted.

## What this fixture validates

- **Principle 1:** Evidence 🟢 from activity; the attachment (EventBridge rules via the resource policy, alias, PC) lands in Dimensions 2 / 4. Plan shows an explicit callout.
- **Constraint 12 (empty ≠ zero)** stated with its three conditions; **Constraint 14** (no env values / presigned URL).
- **delete-lambda.md as written:** PC on an alias; no keep-alive subtraction; no published-version → 🟢; reversibility capped at 🟡.
- **Principle 2** with correct DynamoDB units, bill-derived vs Pricing-API rates labelled, commitment coverage in `Realizable`, GSI included; resolves `direction-unverified`.
- **Cost result ≠ activity signal:** Evidence is not 🚫 for #2; the 🚫 comes from tier rule 1's cost clause and the upstream recommended the losing lever, so the item is 🚫 (not merely dropped into Gaps).
- **Optional rows:** the last-log query ran and passed. Declining it would not change #1 (listed in Gaps); an optional row that ran and returned ⚪ would make Evidence 🟡 and send the delete to 🔴.
- **No fabrication:** no capacity-reduction item is injected, and the Gaps say why none is supported.

## Acceptance check

A reviewer confirms: (a) #1 lands in 🟡 with Evidence 🟢 and Blast / Dependency 🟡, NOT Evidence 🚫, and the plan states why the empty `Invocations` series counts as zero; (b) #1 Reversibility is 🟡 (never 🟢) and nothing in the plan subtracts provisioned-concurrency invocations or credits a published version; (c) #2 lands in 🚫 with the cost-direction table visible, units converted, rate sources labelled, and reason `cost-direction-inverted`; (d) Next steps names the PC-removal first rung for #1 and does not inject a capacity-reduction item for #2; (e) the $80/mo upstream claim appears only as "Savings claimed" with explicit rejection; (f) header has `Target` / `IaC repo(s)`; rows `0a`, `0b-1`, `0b-2` present; Drift section present.
