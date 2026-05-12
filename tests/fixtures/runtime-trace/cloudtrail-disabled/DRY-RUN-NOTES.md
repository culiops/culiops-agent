# Dry-run notes — cloudtrail-disabled

## What this fixture validates

- Skill correctly probes CloudTrail at Gate 2 and detects disabled state.
- Operator is given a clear capability matrix showing CT ✗.
- Skill does NOT attempt to enable CloudTrail (would be a write action; out of scope).
- Output doc's CT section degrades gracefully: explains what's missing, why, and how to fix.
- "Gaps and Caveats" emphasizes the blind spot.

## Gate transitions

1. Gate 1 — operator inputs accepted.
2. Gate 2 — `cloudtrail:DescribeTrails` returns `{"trailList": []}`. Capability matrix: CT ✗. Operator confirms "proceed without CT."
3. Gate 3 — plan emits 4 rows (no CT). Operator approves.
4. Gate 4 — three source blocks (CE, CW, RE). Operator approves each.
5. Gate 5 — draft includes a "Control-Plane Activity" section with the unavailability notice.
6. Gate 6 — output written.

## Acceptance check

- Capability matrix in the output Overview correctly shows CT as "— skipped."
- "Control-Plane Activity" section explains the gap; does not produce false data.
- "Gaps and Caveats" calls this out as the top blind spot.
- Skill never proposes enabling CloudTrail (that would require five-field approval per Iron Law).
