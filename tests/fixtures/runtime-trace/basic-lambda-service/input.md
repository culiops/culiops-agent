# Fixture: basic-lambda-service

## Scenario

A small payments service tagged `service=payments` in AWS account `123456789012`, region `us-east-1`. Three Lambda functions, an SQS queue used for retries, a DynamoDB table for idempotency tokens. The team taking over wants a runtime profile before the official handoff next month.

All four sources are available (CloudTrail logging on, Resource Explorer configured, principal has the read-only policy attached, Cost Explorer enabled).

## Scoping primitive

Tag-based: `service=payments`.

## Gate 1 operator inputs

- Service name: `payments`
- AWS account: `123456789012`
- Primary region: `us-east-1`
- Scoping primitive: tag `service=payments`
- Intent category: `takeover`
- Intent context: "Service takeover from the Pay Team, scheduled for 2026-06-15. We have no documentation and want a runtime baseline before the handoff meeting."
- Intended audience: "Incoming on-call rotation for the payments service (the Platform Team)."
- Redact flag: not set.

## Expected gate behavior

- Gate 1: all inputs accepted. Skill proceeds.
- Gate 2: capability matrix shows all four sources available. Operator confirms.
- Gate 3: plan emits 5 rows (2× CE, 1× CloudTrail, 1× CloudWatch, 1× RE). Estimated cost $0.022. Below soft warning. Operator approves.
- Gate 4: source-by-source. Each source returns data matching the mock JSON. Operator approves each source.
- Gate 5: skill assembles draft. Operator approves with no revisions.
- Gate 6: writes `.culiops/runtime-trace/payments-runtime-profile.md` and JSON sidecars. No redacted export (flag not set).

## Notable findings (driven by mock data)

- DynamoDB **not** mentioned by the team but appears in Cost Explorer at $4.18/mo → flagged in "services billing but absent from diagram" callout.
- One Lambda (`payments-cleanup`) is idle (0 invocations in 14d) → flagged in "idle suspects" callout.
- Deploy role `arn:aws:iam::123456789012:role/PaymentsDeployRole` and engineer `arn:aws:iam::123456789012:user/alice` are the only principals touching the service → captured in "principals touching this service" table.
- All resources confirmed in us-east-1; no cross-region drift.
