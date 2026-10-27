# Fixture: happy-path

## Scenario

A payments service tagged `service=payments` in AWS account `123456789012`, region `us-east-1`: 3 Lambdas, 2 SQS queues, 1 DynamoDB table, 2 Secrets Manager secrets. Two diagram PNGs are available. The Pay Team is handing off to the Platform Team and fills in the full interview. The point of the fixture is that a fully filled interview does **not** produce `ready`: the Step 6 verification batch and the conflict check find a failing item and three interview-vs-artifact conflicts.

## Operator inputs at Gate 1

- Service name: `payments`
- Account: 123456789012 (alias `prod-main`); region: us-east-1
- Delivery model: a CI/CD pipeline deploys on merge to `main` (GitHub Actions)
- Intent category: `takeover`
- Intent context: "Service takeover from Pay Team, scheduled for 2026-06-15."
- Available materials: 2 diagram PNGs (`~/handoff/payments-arch.png`, `~/handoff/payments-flows.png`); no IaC; no existing catalog; no existing runtime profile.
- Outgoing team: Pay Team (primary contact: Bob L., bob@example.com)
- Incoming team: Platform Team

## Expected gate transitions

- Gate 1: accept inputs.
- Gate 1.5: probes (identity, CloudTrail Event history via `lookup-events --max-results 1`, Resource Explorer index); emit the execution plan; operator approves.
- Gates 2-3: ONE `service-discovery` delegation (real-discovery over the diagrams plus live APIs); snapshot validated with a same-target check.
- Gate 4: `runtime-trace` (it has its own 7 gates); snapshot with a same-target check.
- Gate 5: questionnaire emitted; filled version ingested (11 complete).
- Gate 6: auto-mark; Step 6 verification batch (3 read-only commands) approved and run; operator attests items 3, 11, 12 and confirms the deploy role (item 2).
- Gate 7: the evidence is older than the freshness window against the handoff date, so the skill offers a re-run of the Step 6 checks; the operator declines; assemble the package (8 files).

## Notable findings

- Verdict: **not-ready** (9 ✓ verified, 3 ✓ attested, 8 ◐, 1 ✗, 3 ✗ conflict, 1 ?, 0 N/A).
- Item 15 `✗`: `iam simulate-principal-policy` returns `implicitDeny` for the incoming role.
- Item 18 `✗ conflict` (3-5 deploys/week stated; 5 runs in 90 days in CloudTrail), item 19 `✗ conflict` (an unlisted queue sender), item 25 `✗ conflict` (DR to us-west-2 vs nothing outside us-east-1).
- Item 7 `?` (no baseline for the DynamoDB table); items 10 and 23 `◐` (partial alarm coverage; TTL is not a retention period).
- 4 High, 9 Medium, 1 Low open questions.
