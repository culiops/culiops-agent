# Dry-run notes — basic-lambda-service

## Gate transitions

1. **Gate 1 (Scoping)** — operator provides all required inputs from `input.md`. Skill accepts and proceeds.
2. **Gate 2 (Capability)** — probes return: CloudTrail ON, Resource Explorer configured with view in us-east-1, CE accessible, CW accessible. Capability matrix shows all four sources ✓. Operator confirms.
3. **Gate 3 (Plan)** — skill emits 5-row plan with estimated total $0.022. Below soft warning ($0.25). Operator approves entire plan.
4. **Gate 4 (Execution)** — runs in order: Cost Explorer (2 calls), CloudTrail (1), CloudWatch (18 metric queries), Resource Explorer (1). After each source, skill shows raw response (from `mock-api-responses/`) and derived rows. Operator says "continue" for each.
5. **Gate 5 (Synthesis)** — skill assembles draft matching `expected-output.md`. Operator approves with no revisions.
6. **Gate 6 (Write)** — outputs `.culiops/runtime-trace/payments-runtime-profile.md` + audit sidecars. Skill prints final paths.

## What this fixture validates

- Happy path with all sources available.
- Cost Explorer surfaces a stealth dependency (NAT data transfer) and an undocumented service (DynamoDB).
- CloudTrail surfaces both a CI deploy role and a human user.
- CloudWatch identifies an idle Lambda (`payments-cleanup`).
- Resource Explorer confirms no cross-region drift.
- Total cost under $0.05 (no soft warning trigger).
- "Open questions for outgoing team" callout populated.
- DynamoDB recorded as an uncovered resource type in Gaps (no `examples/aws/dynamodb.md` shipped in v1).

## Acceptance check

A reviewer steps through `input.md` + each `mock-api-responses/*.json` and confirms the skill would produce `expected-output.md` byte-for-byte (allowing for run-specific timestamps).
