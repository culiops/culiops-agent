# Dry-run of `service-discovery` against `repo-lambroll-only`

Simulated run of the 5-step skill against this fixture. Recorded on 2026-04-15.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Detector loading | `tool-detectors/lambroll.md` matched `function.json` + `.lambdaignore` |
| Unclassified-deploy-artifacts escape hatch | Did NOT fire — `secrets/prod.enc.yaml` correctly excluded BEFORE the deploy-shape check (path matches `*.enc.*` secrets pattern; exclusion applied first) |
| SOPS regression | `secrets/prod.enc.yaml` noted as existing in the repo but never read; presence recorded in Assumptions and Caveats |
| Cross-stack dependency, not chased | `{{ tfstate ... }}` references in `function.json` for `Role`, `VpcConfig.SubnetIds`, `VpcConfig.SecurityGroupIds`, and `Layers` — all four recorded as upstream Terraform dependencies, none chased |
| Secret reference recording | `Environment.Variables.HMAC_KEY_ARN` value is a Secrets Manager ARN — recorded as a reference, value never resolved |
| Detector-prefixed raw type | Inventory shows `lambroll/function` |

## Findings and fixes applied

### F1 — SKILL.md did not make secrets-exclusion ordering explicit *(fixed)*

The "Detect unclassified deploy artifacts" sub-step in Step 1 scanned `*.yml`, `*.yaml`, `*.toml`, `*.json` files without first excluding secrets-shaped paths. `secrets/prod.enc.yaml` matches `*.enc.*` and should have been excluded before the deploy-shape heuristic was applied. Without the fix, the skill could have flagged `secrets/prod.enc.yaml` as an unclassified deploy artifact and prompted the operator about it — potentially causing the operator to look at or describe secret content.

Fixed in `SKILL.md` Step 1 "Detect unclassified deploy artifacts" paragraph to add: *"Apply the secrets-exclusion rule first (Constraint 5) — exclude any file whose path matches secrets-shaped patterns before evaluating deploy-shape."* Committed ahead of this note as `service-discovery: enforce secrets exclusion before deploy-shape scan`.

### Additional observation — no envfile in fixture *(no fix needed)*

The README mentions `lambroll deploy --envfile envs/<env>.env` but no `envs/` directory exists in the fixture. The `function.json` uses Go-template `{{ env "ENV" }}` syntax — at catalog time, the operator provides the env value (e.g., `ENV=prod`). The lambroll detector's `## Parameter sources` already handles this case: env-var interpolation from `--envfile` is listed as highest priority, and constants from JSON itself as lowest. No gap in the detector.

## What a produced doc would look like

`.culiops/service-discovery/webhook-handler-prod.md` would contain:

- Header: commit SHA, date=2026-04-15, instance=prod, tools=lambroll.
- `## Overview` — fictional webhook handler Lambda in us-east-1, env=prod; Node.js 20 runtime, 512 MB memory, 30s timeout; VPC-attached; arm64 architecture.
- `## Prerequisites` — `aws` CLI v2, `lambroll` ≥ v1; AWS auth via SSO; least-privilege: Lambda read (`lambda:GetFunction`, `lambda:GetFunctionConfiguration`) + CloudWatch Logs read + Secrets Manager describe (NOT `GetSecretValue`); mutations listed (lambroll deploy — `MUTATION — requires explicit approval`, lambroll rollback — `MUTATION — requires explicit approval`).
- `## Resource Inventory` — 1 row:

  | Category | Type | Resolved Name | Naming Fragment | Conditional? | Identifying Dimensions | Signal Envelope | Source |
  |----------|------|---------------|-----------------|--------------|------------------------|-----------------|--------|
  | serverless | `lambroll/function` / `aws_lambda_function` | `webhook-handler-prod` | `webhook-handler-{env}` | No | env, runtime=nodejs20.x, arch=arm64, memory=512MB, timeout=30s, X-Ray tracing=Active | not declared | `function.json` |

- `## Naming Patterns` — `webhook-handler-{env}` (function name); `/aws/lambda/webhook-handler-{env}` (CloudWatch Log Group, default Lambda behavior).
- `## Identifying Dimensions` — env, region (us-east-1), Lambda version/alias, log stream.
- `## Dependency Graph` — upstream (critical-path): Terraform stack owning IAM role (`aws_iam_role.webhook_handler`) — cross-stack via `{{ tfstate }}`, not resolved at catalog time; VPC subnets (×2) and security group — cross-stack; Lambda layer `aws_lambda_layer_version.shared_observability` — cross-stack. Additional: Secrets Manager secret `webhook-handler/{env}/hmac-key` (referenced from `HMAC_KEY_ARN` env var — read-only, not at catalog time). Event source: EventBridge rule configured in a separate Terraform stack — not in-scope; recorded as "downstream event trigger, configured elsewhere."
- `## Signal Envelopes` — none declared in code; runbook anchor falls back to "no declared SLI — establish baseline."
- `## Investigation Runbooks` — at least one for "webhooks not being processed / dropped", with first branch checking upstream Terraform stack (IAM role reachable, VPC connectivity), second branch checking Lambda invocation errors / throttles in CloudWatch Metrics, third branch checking EventBridge rule state (configured elsewhere — requires cross-stack investigation).
- `## Stack-Specific Tooling` — `examples/aws.md`; 1-line note: "lambroll CLI (`lambroll status`, `lambroll log`) is the primary operator tool; see https://github.com/fujiwara/lambroll."
- `## Assumptions and Caveats` — drift note; `{{ tfstate ... }}` values (IAM role ARN, subnet IDs, security group ID, layer ARN) were NOT resolved at catalog time; `secrets/prod.enc.yaml` exists in the repo and was not read — its contents are unknown to this catalog; EventBridge event source mapping is configured in a separate Terraform stack and is out of scope.
- `## Open Questions` — no `envs/` directory present in the fixture at catalog time; operator provided `ENV=prod` as context.
