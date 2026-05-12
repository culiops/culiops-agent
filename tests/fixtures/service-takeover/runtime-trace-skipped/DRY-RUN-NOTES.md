# DRY-RUN-NOTES — runtime-trace-skipped fixture

## What this fixture validates

Scenario: operator lacks `ce:*` IAM permissions in the target account (corporate policy blocks Cost Explorer for engineering accounts). The skill's Gate 1.5 capability probe detects the denial before any sibling skill is invoked. The operator chooses to proceed without runtime data. Step 4 is skipped cleanly.

## Validation points

### 1. Capability probe detects IAM gap at Gate 1.5 (before any sibling invocation)

Probe phase runs four checks: AWS access, CloudTrail, Resource Explorer, Cost Explorer. The Cost Explorer check (`ce:GetCostAndUsage`) returns ACCESS DENIED. The skill surfaces this as a gap with three operator-decidable options — not a hard failure that aborts the run.

Expected behavior verified:
- Probe result recorded in state.md capability-probe table: `DENIED — ce:* blocked by corporate IAM policy`.
- Three options presented to operator: escalate IAM, proceed without runtime data, abort.
- Operator selects "proceed without runtime data" — selection recorded with timestamp in state.md audit trail and execution-plan.md IAM gap decision block.
- No `runtime-trace` invocation occurs.
- No CLI commands for `ce:*` are emitted after the denial.

### 2. Step 4 marked `skipped` in state.md with reason

Step 4 row in state.md:

```
| 4 | Runtime profile — runtime-trace | skipped | — | — | IAM gap — operator choice (accepted at Gate 1.5; no runtime-profile.md produced) |
```

Audit trail entry:

```
2026-05-12T14:35:00Z  Step 4 skipped — IAM gap accepted at Gate 1.5 (operator choice); no runtime-trace invoked; no runtime-profile.md produced
```

Neither a `done` nor `failed` — explicitly `skipped` with reason traceable to the Gate 1.5 decision.

### 3. runtime-profile.md absent from handoff directory; placeholder present

`mock-artifacts/runtime-profile.md` does NOT exist. `mock-artifacts/.runtime-trace-not-run` exists with one-line explanation. The skill does not synthesize a fake runtime profile or leave a partial file.

### 4. Scorecard Runtime category (items 7-9) all degrade to `?`

Items 7, 8, 9 all show:
- **Mark:** ? (auto-degraded)
- **Evidence:** `no runtime-profile.md (Step 4 skipped per operator at Gate 1.5)`

No false ✓ (would assert data we don't have) and no ✗ (would imply the service is broken). The `?` mark represents "evidence source unavailable, cannot assert either way."

### 5. Items 2 and 5 also degrade to `?`

Item 2 (deploy role) relied on `runtime-profile.md → Control-Plane Activity → Principals table`. Item 5 (cross-region footprint) relied on `runtime-profile.md → Cross-Region Footprint → Resource Explorer query`. Both degrade to `?` for the same reason. The degradation propagates correctly to all items that depend on the missing artifact.

### 6. Verdict: not-ready

With 7 items at `?` (5 from runtime-profile dependency, 2 manual not confirmed), the scorecard verdict is `not-ready`. The skill does not silently declare `ready` or omit the verdict.

### 7. open-questions.md surfaces HIGH-1 blocker

`HIGH-1` in open-questions.md states: "Activity baseline unavailable — recommend escalating IAM for ce:* read and re-running." It is listed under High Priority (blockers — must resolve before handoff), not Medium or Low. It includes concrete suggested action (request specific permissions, re-run from Step 4).

### 8. Handoff README first-day actions include IAM follow-up

README first-day actions include:
> **Address IAM gap before signing off on takeover.** Request `ce:GetCostAndUsage` and `ce:GetCostForecast` access on account 123456789012 from IAM admin. Then re-run `service-takeover` from Step 4...

The README verdict is `not-ready` and the IAM gap action is the first substantive item in first-day actions.

### 9. Steps 2, 3, 5, 6, 7 proceed normally

Gates 2 and 3 (service-discovery) do not require Cost Explorer and run normally. Step 5 (interview) and Steps 6-7 (scorecard + package) also proceed. The skip is surgical — only Step 4 is affected.

### 10. Execution plan records the decision

`execution-plan.md` contains an "IAM gap — operator decision" section capturing: the gap description, impact, three options presented, operator selection, and timestamp. This is the audit trail for why Step 4 is absent.

## How to re-run after IAM is resolved

1. Operator requests `ce:GetCostAndUsage` and `ce:GetCostForecast` on account 123456789012.
2. IAM admin grants access.
3. Operator re-invokes `service-takeover` for service `payments`.
4. Skill reads `state.md`, sees Step 4 as `skipped`, offers to resume from Step 4.
5. Capability probe re-runs — Cost Explorer now passes.
6. Step 4 executes: `runtime-trace` invoked, `runtime-profile.md` produced.
7. Scorecard re-runs with new artifact — items 7-9, 2, 5 auto-marked from runtime-profile.md.
8. Verdict updates to `ready` (assuming all other items remain ✓).
