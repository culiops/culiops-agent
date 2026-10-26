*(Other sections same as basic-lambda-service except where noted.)*

## Overview

| Source | Status | Reason |
|---|---|---|
| Scoping probe (GATE 1a) | ✓ ran | |
| Resource Explorer | — skipped | Not configured in this account; `ListIndexes` returned empty |
| Resource-set resolution | ✓ ran | Fallback: `resourcegroupstaggingapi:GetResources` (`tg-001`), us-east-1 only |
| Cost Explorer | ✓ ran | |
| CloudTrail LookupEvents | ✓ ran | |
| Wiring (Lambda / SQS reads) | ✓ ran | |
| CloudWatch GetMetricData | ✓ ran | |

### Resolved resource set (Step 2b, `tg-001`)

Resolved by `tag:GetResources` `service=payments` in us-east-1 (free; the API is regional). Same 5 resources and Owner hint as basic-lambda-service. Shown to the operator at Gate 3. **This set covers us-east-1 only.**

## Cross-Region Footprint (Resource Explorer)

**cross-Region: not verifiable — Resource Explorer is not configured.**

This account has no Resource Explorer index (`resource-explorer-2:ListIndexes` returned an empty list). The resource set was resolved with the Resource Groups Tagging API, which is regional and was queried in us-east-1 only. The skill therefore cannot say whether resources tagged `service=payments` exist outside the primary Region (us-east-1). No "none outside primary Region" claim is made.

**Recommended:** Enable Resource Explorer in this account (free; see AWS docs), ideally with an aggregator index, and re-run `runtime-trace`. Enabling Resource Explorer is **out-of-scope** for this skill — operator action.

## Gaps and Caveats

- **Resource Explorer unavailable — cross-Region footprint not verifiable.** The resource set was resolved with `tag:GetResources` in us-east-1 only. If the takeover scope might include other Regions, do one of:
  - Enable Resource Explorer (free) with an aggregator index and re-run this skill.
  - Re-run with an explicit ARN list scoping primitive including resources from other Regions.
  - Accept this gap and document the assumption that the service is single-Region.
- **Downstream note:** `service-takeover` readiness item 5 (cross-Region footprint) is marked `?` for this profile.
- *(carry over other basic-lambda-service Gaps items)*
