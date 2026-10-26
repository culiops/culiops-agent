# Fixture: basic-lambda-service

## Scenario

A small payments service tagged `service=payments` in AWS account `123456789012`, region `us-east-1`. Three Lambda functions, an SQS queue used for retries, a DynamoDB table for idempotency tokens. The team taking over wants a runtime profile before the official handoff next month.

All sources are available (Event history on and one multi-Region trail, Resource Explorer aggregator index in `us-east-1`, principal has the read-only policy attached, Cost Explorer enabled, `service` activated as a cost-allocation tag). The account is a **member** account of an AWS Organization (not the payer).

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

- **Gate 1 (Scoping):** all inputs accepted.
- **GATE 1a (Scoping probe):** one approved mini-batch, 10 read-only calls, only the CE probe is billed ($0.01): `sts:GetCallerIdentity` (account must equal the operator-typed ID), `iam:ListAccountAliases`, `organizations:DescribeOrganization` (member account here; `AWSOrganizationsNotInUseException` = standalone is equally fine), Resource Explorer `ListIndexes` / `GetIndex` / `ListViews` / `GetView` in `us-east-1`, `cloudtrail:DescribeTrails`, `cloudtrail:LookupEvents` (1 page, `MaxResults=1`), `ce:GetCostAndUsage` (1 day, tag-filtered).
- **Gate 2 (Capability matrix):** built from the probe results; all sources ✓. Operator confirms.
- **Step 2b (Resolve resource set, free):** Resource Explorer `Search` `tag:service=payments` in the aggregator Region returns 5 resources; the list is shown to the operator.
- **Gate 3 (Plan):** priced against the resolved set (5 resources, 23 metrics). Plan estimate $0.0202, plus $0.01 already spent in GATE 1a = projected $0.0302. Below the soft warning ($0.25). Operator approves.
- **Gate 4 (Execution), order: Cost Explorer -> CloudTrail -> Wiring -> CloudWatch.** Each source is shown and approved separately. Resource Explorer does not get a Gate 4 block (it ran at Step 2b).
- **Gate 5 (Synthesis):** operator approves with no revisions.
- **Gate 6 (Write):** writes `.culiops/runtime-trace/payments-runtime-profile.md` and projected-field JSON sidecars under `.culiops/runtime-trace/payments-audit/`. No redacted export (flag not set). Sidecars are not committed by the skill.

## Notable findings (driven by mock data)

- Every Cost Explorer call carries `Filter: Tags service=payments`; spend is DAILY over the closed window 2026-04-11 -> 2026-05-11 (End exclusive), summed. Tagged spend = $23.02 (Lambda 80.0%, DynamoDB 18.2%, SQS 1.8%).
- Shared NAT / data-transfer cost is **not** attributable by tag and is **absent** from the spend table. It is stated as a Gap, not as a finding.
- There is no "services billing but absent from diagram" callout: this run has no catalog primitive to compare against.
- DynamoDB table `payments-idempotency` is a resolved resource of a type with no `examples/aws/` file -> Gap "metrics not collected".
- Management-event principals: `PaymentsDeployRole` (CI) and `alice`. These are managers of the resources, not callers. Configured callers come from the Wiring block (API Gateway -> `payments-charge`; `payments-retry-queue` -> `payments-refund`).
- `payments-cleanup`: empty CloudWatch result, `ListMetrics` shows the metric exists -> verdict `no-activity-14d`, never an action word.
- All resources are in `us-east-1`; cross-Region claim is allowed because the view is in the aggregator Region, the indexed Regions are recorded, the view includes tags, and `Count.Complete=true`.
