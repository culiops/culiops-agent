*(Other sections same as basic-lambda-service except where noted.)*

## Overview

| Source | Status | Reason |
|---|---|---|
| Cost Explorer | ✓ ran | |
| CloudTrail LookupEvents | ✓ ran | |
| CloudWatch GetMetricData | ✓ ran | |
| Resource Explorer | — skipped | Not configured in this account; `ListIndexes` returned empty |

## Cross-Region Footprint (Resource Explorer)

**Resource Explorer unavailable — cross-region inventory not collected.**

This account has no Resource Explorer index (`resource-explorer-2:ListIndexes` returned an empty list). The skill cannot independently verify whether resources tagged `service=payments` exist outside the assumed primary region (us-east-1).

**Recommended:** Enable Resource Explorer in this account (free; see AWS docs) and re-run `runtime-trace`. Enabling Resource Explorer is **out-of-scope** for this skill — operator action.

## Gaps and Caveats

- **Resource Explorer unavailable** — cross-region drift cannot be detected by this run. If the takeover scope might include other regions, do one of:
  - Enable Resource Explorer (free) and re-run this skill.
  - Re-run with an explicit ARN list scoping primitive including resources from other regions.
  - Accept this gap and document the assumption that the service is single-region.
- *(carry over other basic-lambda-service Gaps items)*
