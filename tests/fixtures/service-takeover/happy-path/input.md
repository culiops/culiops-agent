# Fixture: happy-path

## Scenario

A payments service tagged `service=payments` in AWS account `123456789012`, region `us-east-1`. Three Lambdas, SQS, DynamoDB. Two diagram PNGs are available. The Pay Team is handing off to the Platform Team. Outgoing team fills in the full interview; all categories of the readiness scorecard get evidence-based marks.

## Operator inputs at Gate 1

- Service name: `payments`
- Account: 123456789012
- Region: us-east-1
- Intent category: `takeover`
- Intent context: "Service takeover from Pay Team, scheduled for 2026-06-15."
- Available materials: 2 diagram PNGs (~/handoff/payments-arch.png, ~/handoff/payments-flows.png); no IaC; no existing catalog; no existing runtime profile.
- Outgoing team: Pay Team (primary contact: Bob, bob@example.com)
- Incoming team: Platform Team

## Expected gate transitions

- Gate 1 → accept inputs
- Gate 1.5 → emit execution plan; operator approves
- Gate 2 → instruct operator to run service-discovery (real-discovery, image mode); operator returns catalog path
- Gate 3 → instruct operator to run service-discovery (real-discovery, AWS CLI mode); operator returns catalog path (merged with diagram catalog)
- Gate 4 → instruct operator to run runtime-trace; operator returns profile path
- Gate 5 → emit questionnaire; operator returns filled version (mock-artifacts/filled-interview.md)
- Gate 6 → auto-mark scorecard; operator confirms manual items
- Gate 7 → assemble handoff package

## Notable findings

- All 25 readiness items get either ✓ or [manual] with positive operator notes.
- Verdict: ready.
- 0 high-priority open questions, 2 medium-priority (training schedule, DR test scheduling).
