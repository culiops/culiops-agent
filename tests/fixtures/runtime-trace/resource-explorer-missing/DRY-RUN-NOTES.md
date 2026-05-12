# Dry-run notes — resource-explorer-missing

## What this fixture validates

- Skill correctly probes Resource Explorer at Gate 2 and detects absent index.
- Output doc explains the gap and gives the operator concrete options.
- Skill does NOT attempt to enable Resource Explorer (write action; out of scope).

## Gate transitions

Same as basic-lambda-service except Gate 4 runs three source blocks (CE, CT, CW); RE is skipped.

## Acceptance check

- Capability matrix shows RE as "— skipped."
- Cross-Region section explains the gap with three concrete options.
- Skill never proposes enabling RE.
