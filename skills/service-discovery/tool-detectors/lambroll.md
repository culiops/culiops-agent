---
name: lambroll
url: https://github.com/fujiwara/lambroll
deploys: AWS Lambda functions (one function per deploy unit)
---

Syntax below follows the lambroll README (https://github.com/fujiwara/lambroll, main branch, fetched 2026-10-26).

## File signatures
- `function.json` / `function.jsonnet` (the Lambda function definition; default for `--function`). Counts as lambroll ONLY with a top-level `FunctionName` AND at least one of `Handler`, `Role`, `Runtime` (avoids the Azure Functions `function.json` collision)
- `.lambdaignore` (default `--exclude-file` for the deploy package)
- UNVERIFIED: a `lambroll.yml` / `lambroll.yaml` global config. The README does not document one, so it is not a signature. Do not rely on it

## Stack boundary
One stack = one function definition file: exactly one Lambda function per deploy unit. The function's source (the `--src` directory, default `.`) lives beside it unless overridden.

Multi-instance is expressed via:
- separate definition files per environment passed with `--function <file>` (the README documents the flag, not a naming scheme)
- per-environment directories each holding their own `function.json`
- environment variables read via template functions inside the definition

## Secret-bearing files
- NEVER resolve `` {{ tfstate ... }} ``: it reads Terraform state (secrets). NEVER open `*.tfstate*`; a `--tfstate` / `--prefixed-tfstate` URL is recorded as a cross-stack reference only.
- `Environment.Variables`: record KEY names; withhold values (`<set in <file>:<line>>`) when the key contains (case-insensitive) any of: `password`, `passwd`, `secret`, `token`, `key`, `apikey`, `api_key`, `private`, `credential`, `dsn`, `conn`, `connection_string`, `auth`, `cert`.
- `--envfile` targets are **not opened** (env files are secret-bearing — SKILL.md Constraint 5); record the path as a parameter source.
- `secrets*.yaml`, `*.sops.*`, `*.enc.*` are not opened at all.

## Parameter sources (highest to lowest priority)
- `--envfile <path> ...` environment files, exported before rendering
- Template functions in the definition: `` {{ env `VAR` `default` }} `` and `` {{ must_env `VAR` }} `` (also `json_escape`). Record the variable NAME; unresolved unless the operator supplies the value
- `` {{ tfstate `addr` }} `` / `` {{ tfstatef ... }} `` enabled by `--tfstate URL`; `--prefixed-tfstate PREFIX=URL` yields `` {{ <prefix>tfstate ... }} ``. Record the reference as a CROSS-STACK dependency, do NOT resolve or chase it
- Jsonnet (`function.jsonnet`): `--ext-str` / `--ext-code` external variables read via `std.extVar`
- UNVERIFIED: `ssm` / `secretsmanager` template helpers. The README does not document them; treat as unknown syntax and ask rather than assume

## Resource extraction
- The function definition → one inventory entry equivalent to `aws_lambda_function`; raw type: `lambroll/function`
- `Role:` ARN → IAM role dependency
- `Environment.Variables:` → record keys (NOT values); flag any value that looks like a secret reference (e.g., contains `arn:aws:secretsmanager:`)
- `VpcConfig:` → subnet and security group dependencies
- `Layers:` → layer ARNs
- `DeadLetterConfig.TargetArn:` → SQS or SNS dependency
- `FileSystemConfigs:` → EFS dependency
- `TracingConfig.Mode:` → observability configuration
- `Tags:` → when present, lambroll sets/removes tags on deploy; record them (ownership signal)
- Function URL: UNVERIFIED file layout (the README fetched does not document one); if a Function URL is declared anywhere, record it as a public endpoint and ask

## Naming pattern hints
lambroll does not enforce a naming convention. Record `FunctionName:` as-is; if it uses a template (e.g. `` {{ must_env `ENV` }}-hello ``), record the template and the variable.

## Typical cross-stack dependencies
- Terraform state via `` {{ tfstate ... }} `` (function config consumes outputs of a stack that owns the role, VPC, layers)
- Secrets Manager / SSM via `Environment.Variables` references or function code
- IAM role (`Role:`), layers (`Layers:`), VPC subnets and security groups (`VpcConfig:`), EFS access points (`FileSystemConfigs:`)
- Event sources configured outside lambroll (EventBridge, S3 notifications, API Gateway, SQS mappings) — record as "triggers configured elsewhere"
