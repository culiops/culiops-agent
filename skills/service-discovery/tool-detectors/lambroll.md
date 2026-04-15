---
name: lambroll
url: https://github.com/fujiwara/lambroll
deploys: AWS Lambda functions (one function per deploy unit)
---

## File signatures
- `function.json` / `function.jsonnet` (the Lambda function definition — required)
- `.lambdaignore` (lambroll's analog of `.gitignore` for the deploy package)
- `lambroll.yml` / `lambroll.yaml` (optional global config in some setups)

## Stack boundary
One stack = one `function.json` (or `function.jsonnet`) — exactly one Lambda function per deploy unit. The function's source code (the deploy package) lives in the same directory tree as `function.json` unless overridden.

Multi-instance is expressed via:
- separate `function-<env>.json` files passed to `lambroll deploy --function function-<env>.json`
- per-environment directories each containing their own `function.json`
- env-var interpolation (`{{ env "VAR_NAME" }}` Go template syntax) within `function.json`

## Parameter sources (highest to lowest priority)
- `--envfile <path>` flag (file of `KEY=VALUE` pairs sourced into the environment)
- Environment variables referenced via Go template `{{ env "VAR_NAME" }}` syntax in `function.json`
- `{{ tfstate "<output-name>" }}` template helpers (lambroll reads Terraform state when configured) — record the upstream Terraform stack as a CROSS-STACK dependency, do NOT chase it
- `{{ ssm "<parameter-path>" }}` template helpers (SSM Parameter Store) — record the parameter path as a runtime reference
- `{{ secretsmanager "<secret-id>" }}` template helpers — record reference, NEVER read secret values
- Jsonnet TLA / external variables when `function.jsonnet` is used

## Resource extraction
- The function definition → one inventory entry equivalent to `aws_lambda_function` / `AWS::Lambda::Function`; raw type: `lambroll/function`
- `Role:` ARN → IAM role dependency
- `Environment.Variables:` → record env var keys (NOT values); flag any value that looks like a secret marker (e.g., contains `arn:aws:secretsmanager:`)
- `VpcConfig:` → VPC subnet and security group dependencies
- `Layers:` → Lambda layer dependencies (record ARNs)
- `DeadLetterConfig.TargetArn:` → SQS or SNS dependency
- `FileSystemConfigs:` → EFS dependency
- `TracingConfig.Mode:` → record observability configuration
- Function URL configuration (if `function_url.json` is present alongside) → record as an additional public endpoint

## Naming pattern hints
lambroll does not enforce a naming convention. Record `FunctionName:` as-is. If it uses template interpolation, record the resolved value for the target instance.

## Typical cross-stack dependencies
- Terraform state via `{{ tfstate ... }}` (very common — function config consumes outputs of a TF stack that owns the IAM role, VPC, layers, etc.)
- Secrets Manager via `{{ secretsmanager ... }}` (referenced from `Environment.Variables` or task code)
- SSM Parameter Store via `{{ ssm ... }}`
- IAM role (referenced by `Role:`)
- Lambda layers (referenced by `Layers:`)
- VPC subnets and security groups (referenced by `VpcConfig:`)
- EFS access points (referenced by `FileSystemConfigs:`)
- Event sources configured outside lambroll (EventBridge rules, S3 notifications, API Gateway integrations, SQS event source mappings) — record as "downstream/upstream event triggers, configured elsewhere"
