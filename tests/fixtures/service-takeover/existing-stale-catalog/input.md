# Fixture: existing-stale-catalog

## Scenario

The operator previously ran service-discovery against the payments service 14 days ago. The catalog still exists at `.culiops/service-discovery/payments-catalog.md`. Today they're starting a takeover and want fresh discovery data.

## Operator inputs

Same as happy-path, plus:
- Available materials note: "Pre-existing service-discovery catalog at `.culiops/service-discovery/payments-catalog.md` (14 days old)."

## Expected gate behavior

- Gate 1.5: execution plan identifies the pre-existing catalog. Proposes 3 options for Step 2 row: use as-is / verify with thin re-scan / re-run from scratch.
- Operator selects re-run.
- At Step 2: skill renames the old catalog to `.culiops/service-discovery/payments-catalog.20260428-stale.md` (timestamp suffix from old catalog's frontmatter `generated-at`), then prints fresh `service-discovery` invocation.
- Rest of run proceeds as happy-path.

## Notable findings

- Old catalog preserved (never deleted).
- New catalog snapshot in handoff directory is from today, not from 14 days ago.
- state.md records the rename action in audit trail.
