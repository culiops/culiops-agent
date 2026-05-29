---
cloud: aws
action: delete
resource_type: lambda-function
applies_when: action == "delete" AND resource matches "arn:aws:lambda:*:function:*"
---

# Verify: Delete Lambda function

## Required IAM
- `lambda:GetFunction`
- `lambda:ListEventSourceMappings`
- `lambda:ListAliases`
- `lambda:ListVersionsByFunction`
- `lambda:GetProvisionedConcurrencyConfig`
- `cloudwatch:GetMetricStatistics`
- `logs:DescribeLogStreams` (optional, for last-execution timestamp beyond CloudWatch metric resolution)

## Queries

1. `aws lambda get-function --function-name <name>` — confirms exists, captures `Runtime`, `LastModified`, `CodeSha256`, `PackageType`.
2. `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations --dimensions Name=FunctionName,Value=<name> --start-time <now-30d> --end-time <now> --period 86400 --statistics Sum` — 30d invocation count. **Activity signal, Principle 1.** 30d (not 14d) because some scheduled functions run monthly.
3. `aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations --dimensions Name=FunctionName,Value=<name>,Name=Resource,Value=<name>:$LATEST --start-time <now-30d> --end-time <now> --period 86400 --statistics Sum` — invocations against `$LATEST` only, isolates the unaliased path.
4. `aws lambda list-event-source-mappings --function-name <name>` — lists SQS / Kinesis / DynamoDB Streams / Kafka event sources. **Attachment signal — Dimension 2/4 input, NOT Dimension 3.** A function with 3 active event source mappings and zero `Invocations` is still idle.
5. `aws lambda list-aliases --function-name <name>` and `aws lambda list-versions-by-function --function-name <name>` — surfaces any aliases or non-`$LATEST` versions that might be invoked by external consumers (API Gateway, CloudFront, alb integrations) not captured in event source mappings.
6. (Conditional) `aws lambda get-provisioned-concurrency-config --function-name <name> --qualifier <each-alias-or-version>` — if any alias has provisioned concurrency configured, the operator is paying for warm capacity. Surface this in the rollback note.
7. (Optional, opt-in at GATE 2) `aws logs describe-log-streams --log-group-name /aws/lambda/<name> --order-by LastEventTime --descending --max-items 1` — last log stream timestamp confirms last actual execution (catches functions invoked but logging failed, or functions with logging disabled).

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|------------|
| 30d `Invocations` (Sum) | `0` | ≥ 1 — function ran at least once |
| Last log stream `lastEventTimestamp` (if queried) | older than 30d OR no log streams | within 30d |
| Event source mappings | any state — **not a 🚫 trigger** (attachment ≠ activity) | n/a |
| Provisioned concurrency configured | none | configured — flag as keep-warm cost; do not score 🚫 on this alone |

**Principle 1 reminder:** event source mappings, aliases, and API Gateway integrations are **attachment**. They mean "something would break if deleted" — Dimension 2 (blast radius). They are NOT evidence of use. Score Dimension 3 on `Invocations`, full stop.

**Keep-alive noise to subtract:** if provisioned concurrency is configured, the function has CloudWatch `ProvisionedConcurrencyInvocations` ≥ 0 driven by AWS keep-warm pings, not real traffic. Subtract these from `Invocations` before judging activity. If `Invocations - ProvisionedConcurrencyInvocations == 0` over 30d, the function is idle even though it appears "warm".

## Reversibility classification
- **Default:** 🟡 if function code is committed to IaC (Terraform / CloudFormation / SAM / CDK) — redeploy restores. ~5–15 min RTO.
- **Mitigated to 🟢:** if a published version (not just `$LATEST`) exists and is preserved — full restore via `aws lambda update-function-code --s3-bucket <bucket> --s3-key <key>` from the version's stored package.
- **Bumped to 🔴:** if function code is in-console-only (no IaC source), event source mapping configurations are not in IaC, or any consumer (API Gateway / ALB / CloudFront) references the function ARN directly.

## Blast radius classification
- **Default:** 🟡 — function may be invoked by event source mappings, aliases, or external consumers. Bump to 🟢 if Query 4 returns zero mappings AND Query 5 confirms no aliases AND no IaC `data` block references the ARN. Bump to 🔴 if any consumer is API Gateway or ALB (deletion produces 5XX without coordinated cutover).

## Rollback note (informational, shown in plan)
"Redeploy via IaC (~5–15 min). If a published version is preserved, restore is faster. **Pre-delete: take a backup** — `aws lambda get-function --function-name <name>` returns a presigned URL to the deployment package; download it locally before delete. Event source mappings must be recreated separately if not in IaC. **Principle 2 ladder fallback:** if delete is blocked by blast radius, check whether memory allocation is over-provisioned (typical: 1024 MB default vs actual peak ≤ 256 MB per `max_memory_used` in CloudWatch Logs). Lambda cost is GB-seconds — halving memory halves cost per invocation, fully reversible by re-applying IaC. Compute potential savings before recommending downsize."
