# Fixture: resource-explorer-missing

## Scenario

Same payments service as `basic-lambda-service` but Resource Explorer is not configured in this AWS account: `ListIndexes` returns an empty list. Skill must fall back to the Resource Groups Tagging API (`tag:GetResources`) to resolve the resource set at Step 2b, record that cross-Region is not verifiable, and recommend enabling Resource Explorer (without doing so itself).

## Scoping primitive

Tag-based: `service=payments`. (Note: `tag:GetResources` is **regional**, so the resolved set covers the primary Region only. Without Resource Explorer the skill cannot independently confirm cross-Region coverage. Operator should also supply an ARN list if cross-Region coverage matters.)

## Gate 1 operator inputs

Same as basic-lambda-service.

## Expected gate behavior

- **GATE 1a:** `ListIndexes` returns `{"Indexes": []}` (no `GetIndex`/`GetView` to run). Other probes as in basic-lambda-service.
- **Gate 2:** capability matrix shows Resource Explorer ✗ ("not configured; `ListIndexes` returned empty") and the **resolution fallback `untested`** (`tag:GetResources`, us-east-1, free; no probe, first used at Step 2b). Operator confirms.
- **Step 2b:** `tag:GetResources` with `TagFilters service=payments` in us-east-1 returns the 5 resources (`tg-001`). The list is shown to the operator. Downstream gates behave as in basic-lambda-service.
- **Gate 4:** four source blocks (CE, CloudTrail, Wiring, CloudWatch); there is no Resource Explorer block.
- **Output:** "Cross-Region Footprint" says cross-Region is **not verifiable** and explains why. "Gaps and Caveats" recommends enabling Resource Explorer and re-running.
