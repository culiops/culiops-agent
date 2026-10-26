**Change comms for:** `shipping-api` / `live`
**Type:** `result`
**Platform:** `Google Chat`
**Sources:** `.culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md` (Date 2026-10-26 09:40), and operator-supplied

## Draft

```text
*❌ Failed: shipping-api p99 latency alarm (live), applied 09:25 CET*
State: applied with the wrong threshold (0.8, expected 800), alarm currently in ALARM, <TODO: rolled back or not>
Next: rolling forward tomorrow (2026-10-27 CET)
Ticket: SHIP-204
```

## Fact table

| Field | Value | Source |
|-------|-------|--------|
| Service | shipping-api | `record: .culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md#header` |
| Environment | live | `record: .culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md#header` |
| What (short name) | shipping-api p99 latency alarm | `record: .culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md#header` (Change line) |
| Execution path | Direct apply (no PR exists, so no PR line) | `record: .culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md#header` |
| Record Outcome | completed (not used as the outcome: Verification is not clean) | `record: .culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md#Outcome` |
| Apply outcome | Failed (applied, threshold wrong) | `operator-supplied` |
| Timezone | CET | `operator-supplied` |
| Apply time | 09:25 CET (today → 2026-10-26) | `operator-supplied` |
| Problem | threshold is 0.8 where 800 is expected; alarm state ALARM; re-plan still shows one change | `record: .culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md#Execution Log` (Phase 1, Verification line) and `operator-supplied` ("the alarm threshold is wrong") |
| Expected threshold | 800 | `record: .culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md#Change Plan` (Success criteria) |
| Rolled back or not | `<TODO: rolled back or not>` | `operator-supplied (not given)` |
| Next steps | rolling forward tomorrow (tomorrow → 2026-10-27 CET) | `operator-supplied` |
| Ticket key | SHIP-204 | `record: .culiops/iac-change-execution/shipping-api-add-p99-alarm-20261026-0940.md#Ticket Reference` |

## Redaction log

Redaction log: nothing masked

## Open TODOs
- `<TODO: rolled back or not>` (State line)

## Flags
none
