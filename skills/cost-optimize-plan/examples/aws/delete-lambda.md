---
cloud: aws
action: delete
resource_type: lambda-function
applies_when: action == "delete" AND resource matches "arn:aws:lambda:*:function:*"
---

# Verify: Delete Lambda function

## Required IAM
- `lambda:GetFunction` (its raw output carries `Environment` and a presigned `Code.Location` — always project with `--query`, see Secrets rule)
- `lambda:ListTags`
- `lambda:ListEventSourceMappings`
- `lambda:ListAliases`
- `lambda:ListVersionsByFunction`
- `lambda:GetPolicy`
- `lambda:ListFunctionUrlConfigs`
- `lambda:ListProvisionedConcurrencyConfigs`
- `cloudwatch:GetMetricData`
- `logs:DescribeLogStreams` (optional)

## Queries

0. **Target check + ownership probe** (`examples/aws.md`). Tags: `aws lambda list-tags --resource <function-arn>`. Grep the IaC repo for the function name / ARN: `lambroll` → `function.json`, `terraform` → `aws_lambda_function` block (cite `code:<path:line>`). `aws:cloudformation:stack-name` (CFN / Serverless / SAM / CDK) → `unsupported-owner`, stop on this item.
1. `aws lambda get-function --function-name <name> --query 'Configuration.{Runtime:Runtime,LastModified:LastModified,CodeSha256:CodeSha256,PackageType:PackageType}'` — confirms existence in this account/region and gives the describe baseline for the Metrics rule. **Never** record `Environment` or `Code.Location` (Secrets rule). Compare `LastModified` / `CodeSha256` with the IaC for drift.
2. **Invocation activity** — `aws cloudwatch get-metric-data`, namespace `AWS/Lambda`, metric `Invocations`, stat `Sum`, **hourly**, window 90d (delete band, Principle 3; also catches monthly schedules). Unqualified invocations are published only under the `FunctionName` dimension (`Name=FunctionName,Value=<name>`). Invocations through an alias or version are also published with the `Resource` dimension as `<name>:<alias|version>` (`Name=FunctionName,Value=<name>` + `Name=Resource,Value=<name>:<alias>`): run that series too for every alias/version from Query 5 and take the larger count per hour (do not add — avoid double counting; verify the aggregate behaviour once per account). `Resource=<name>:$LATEST` is not a published value — do not query it. Read the temporal distribution, not just the total. **Activity signal, Principle 1.**
   - **Provisioned concurrency is real traffic.** `ProvisionedConcurrencyInvocations` counts invocations served by warm capacity; AWS does not ping functions. Never subtract it. A function whose traffic is served entirely by provisioned concurrency is active.
   - **Lambda@Edge:** edge functions run in replica regions and report there, so `Invocations` in the function's home region proves nothing. If `get-policy` shows `replicator.lambda.amazonaws.com` (verify) or a CloudFront `LambdaFunctionAssociations` references the ARN → signal ⚪ `edge-function`.
3. `aws lambda list-provisioned-concurrency-configs --function-name <name>` — warm capacity is billed whether or not traffic arrives. Configured PC with **zero** traffic is the cheapest-reversible lever (Principle 2): note removal as the first rung of the ladder; configured PC **with** traffic = active.
4. `aws lambda list-event-source-mappings --function-name <name>` — SQS / Kinesis / DynamoDB Streams / Kafka sources. **Attachment (Dimension 2/4), not activity.** A function with active mappings and zero `Invocations` is still idle by Dimension 3.
5. `aws lambda list-aliases --function-name <name> --query 'Aliases[].{name:Name,version:FunctionVersion}'` and `aws lambda list-versions-by-function --function-name <name> --query 'Versions[].{v:Version,modified:LastModified}'` — aliases and versions that external consumers may target. (`delete-function` without `--qualifier` removes **all** versions and aliases, so these are not a restore path.)
6. **Resource-based policy** — `aws lambda get-policy --function-name <name>` (`ResourceNotFoundException` = no policy); repeat with `--qualifier <alias>` for each alias. Record the `Principal` / `SourceArn` pairs as a summary: which services/accounts can invoke (API Gateway, S3, EventBridge, SNS, ALB, CloudFront, Cognito, …). Also `aws lambda list-function-url-configs --function-name <name>` — function URLs.

7. (Optional, opt-in at GATE 2) `aws logs describe-log-streams --log-group-name /aws/lambda/<name> --order-by LastEventTime --descending --max-items 1 --query 'logStreams[].lastEventTimestamp'` — last execution timestamp. Valid only if the log group exists, uses the default name (a custom `LoggingConfig` log group → ⚪), and retention covers the window; a missing/expired log group is not evidence of idleness.

## Evidence thresholds

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| `Invocations` (Sum, hourly, 90d; `FunctionName` and per-alias `Resource` series) | required | `0` across the window, Metrics rule satisfied | ≥ 1 on a recurring or recent pattern (Principle 3: one old burst is not steady use) |
| Last log stream timestamp (Query 7) | optional | older than the window, log group present with sufficient retention | within the window |

⚪: Target check failed, Query 1 failed, `edge-function`, or Metrics-rule conditions not met → Evidence ⚪ (→ 🔴).

**Principle 1 reminder:** mappings, aliases, resource-policy invokers, function URLs and provisioned concurrency are **attachment** — they mean "something would break", not "something is used". Score Dimension 3 on `Invocations`, full stop.

## Attachment (Dimension 2 / 4 input)

| Signal | Query | Effect |
|--------|-------|--------|
| Policy principal API Gateway / ALB (`elasticloadbalancing.amazonaws.com`) / CloudFront | 6 | any → Blast 🔴 (deletion produces 5XX without a coordinated cutover) |
| Function URL configured | 6 | any → Blast 🔴 |
| Policy principal S3 / EventBridge / SNS / other service | 6 | any → Dependency 🟡 |
| Event source mappings | 4 | any → Dependency 🟡; not in IaC → Reversibility 🔴 |
| Aliases / non-`$LATEST` versions | 5 | any → Dependency 🟡 |
| Provisioned concurrency configured | 3 | any → flag keep-warm cost; Principle 2 first rung |
| IaC references to the ARN / name (`code:`) | 0 | 1–2 → Dependency 🟡; ≥ 3 → Dependency 🔴 |

## Reversibility classification
- **Default:** 🟡 if the owner is `terraform` or `lambroll` AND the deployable artifact is retrievable (code in the repo, or the S3 package / ECR image the config points at still exists) — redeploy restores, ~5–15 min RTO.
- **Otherwise 🔴:** owner `unmanaged` / `unknown` (code only in the console), artifact not retrievable, or event source mappings / resource policies not in IaC.
- **No 🟢, no "published version" mitigation.** `aws lambda delete-function` without `--qualifier` deletes all versions and aliases, so previously published versions are gone with the function.

## Blast radius classification
- **Default:** 🟡 — function may be invoked by mappings, aliases, policy-granted services or external consumers.
- **Bump to 🟢** only if Queries 3–6 are all empty (no mappings, aliases, policy, function URL) AND no IaC reference.
- **Bump to 🔴** per the Attachment table.

## Rollback note (informational, shown in plan)
"Redeploy via IaC (~5–15 min) — only if the deployable artifact is still retrievable. Deleting without a qualifier removes every version and alias, so there is no published-version fallback. Pre-delete backup is an operator step: `get-function` returns a presigned URL to the deployment package; downloading it is done by the operator and the URL is not recorded in the plan. Event source mappings, resource-policy permissions and function URLs must be recreated separately if not in IaC. **Principle 2 ladder fallback:** first remove idle provisioned concurrency; then, if delete is blocked by blast radius, check whether memory is over-provisioned (e.g. 1024 MB configured vs a much lower peak `max_memory_used` in the function's logs). Lambda cost is GB-seconds — halving memory halves cost per invocation and is reversible by re-applying IaC. Compute the saving before recommending a downsize."
