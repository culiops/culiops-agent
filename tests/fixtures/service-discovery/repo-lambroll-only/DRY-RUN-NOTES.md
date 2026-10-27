# Dry-run of `service-discovery` against `repo-lambroll-only`

Simulated run of the IaC path against this fixture. First recorded 2026-04-15; re-run 2026-10-26 for secrets-by-projection; re-run 2026-10-27 for the deployed-ref, membership, parameter-provenance and edge-basis rules.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Detector loading | `tool-detectors/lambroll.md` matched `function.json` + `.lambdaignore` |
| Unclassified-deploy-artifacts escape hatch | Did NOT fire — `secrets/prod.enc.yaml` correctly excluded BEFORE the deploy-shape check (path matches `*.enc.*` secrets pattern; exclusion applied first) |
| SOPS regression | `secrets/prod.enc.yaml` noted as existing in the repo but never read; presence recorded in Assumptions and Caveats |
| Cross-stack dependency, not chased | `{{ tfstate ... }}` references in `function.json` for `Role`, `VpcConfig.SubnetIds`, `VpcConfig.SecurityGroupIds`, and `Layers` — all four recorded as upstream Terraform dependencies, none chased |
| Secret reference recording | `Environment.Variables.HMAC_KEY_ARN` (`function.json:13`) is a Secrets Manager ARN — the key name matches the secret-key list, but the value is a reference to a secret store, so the ARN is recorded as a reference; the secret value is never fetched |
| Unresolved template parameter | `` {{ env `LOG_LEVEL` }} `` (`function.json:14`) has no declared source: README says only `ENV` is passed and no env file ships. Listed as an unresolved parameter and an open question; the skill does not guess a value |
| Detector-prefixed raw type | Inventory shows `lambroll/function` |

## Findings and fixes applied

### F1 — SKILL.md did not make secrets-exclusion ordering explicit *(fixed)*

The "Detect unclassified deploy artifacts" sub-step in Step 1 scanned `*.yml`, `*.yaml`, `*.toml`, `*.json` files without first excluding secrets-shaped paths. `secrets/prod.enc.yaml` matches `*.enc.*` and should have been excluded before the deploy-shape heuristic was applied. Without the fix, the skill could have flagged `secrets/prod.enc.yaml` as an unclassified deploy artifact and prompted the operator about it — potentially causing the operator to look at or describe secret content.

Fixed in `SKILL.md` Step 1 "Detect unclassified deploy artifacts" paragraph to add: *"Apply the secrets-exclusion rule first (Constraint 5) — exclude any file whose path matches secrets-shaped patterns before evaluating deploy-shape."*

### Observation — no envfile in fixture *(no fix needed)*

The README states how the environment is chosen: the operator passes `ENV=prod` (or `staging`) inline when invoking `lambroll deploy` (`ENV=prod lambroll deploy`). No `--envfile` is used and no `envs/` directory exists, so there is no env file to read. `function.json` uses lambroll template functions (`` {{ env `ENV` }} ``): at catalog time the operator supplies `ENV=prod`. The lambroll detector's `## Parameter sources` covers this case (template-function variables are recorded by NAME; the value is unresolved unless the operator supplies it).

### Observation — `LOG_LEVEL` is an unresolved parameter *(no fix needed; expected behaviour)*

`function.json:14` reads `` {{ env `LOG_LEVEL` }} ``. Nothing in the repo or README says where `LOG_LEVEL` comes from. At Step 2 the skill lists it under "Unresolved (needs your input)"; the operator may answer with a value (recorded as given) or "skip with placeholder". The catalog then shows `LOG_LEVEL = <unresolved: env LOG_LEVEL, function.json:14>` and repeats it under Open Questions.

## Evidence rules (re-run 2026-10-27)

- **Deployed ref:** nothing in the repo shows it (`README.md` has only the inline `ENV=prod lambroll deploy`), so it is `UNVERIFIED`; the skill asks and records `operator-stated`. `git status --short` is shown at Gate 1.
- **Membership:** not asked. The stack declares one resource, the function `webhook-handler-{{ env `ENV` }}` (`function.json:2`), tagged `Service: webhook-handler` (`function.json:30`). Recorded `membership: single resource, code:function.json:2`; Unattributed: none.
- **Parameter provenance:** `ENV = prod` comes from the operator (inline at deploy time, `README.md:19`) and is recorded `operator-stated`, not as a default. `LOG_LEVEL` (`function.json:14`) has no source the repo can show: it stays unresolved and the operator is asked where the instance's values come from.
- **Edges:** the four `{{ tfstate }}` links (role, subnets, security group, layer) are `code:` for the link; whether each is on the invocation path is not shown, so each edge is `critical-path: unknown` until confirmed. The EventBridge trigger is configured elsewhere: `downstream: none found in this repo — consumers in other repos / stacks are not visible`.

## What a produced doc would look like

`.culiops/service-discovery/webhook-handler-prod.md` would contain:

- Header: commit SHA, date=2026-04-15, instance=prod, tools=lambroll, `Working tree: clean`, `Deployed ref: <answer> — operator-stated`.
- `## Overview` — fictional webhook handler Lambda in us-east-1, env=prod; Node.js 20 runtime, 512 MB memory, 30s timeout; VPC-attached; arm64 architecture.
- `## Prerequisites` — `aws` CLI v2, `lambroll` ≥ v1; AWS auth via SSO; least-privilege: Lambda read (`lambda:GetFunction`, `lambda:GetFunctionConfiguration`) + CloudWatch Logs read + Secrets Manager describe (NOT `GetSecretValue`); mutations listed (lambroll deploy — `MUTATION — requires explicit approval`, lambroll rollback — `MUTATION — requires explicit approval`).
- `## Resource Inventory` — 1 row:

  | Category | Type | Resolved Name | Naming Fragment | Conditional? | Identifying Dimensions | Signal Envelope | Source |
  |----------|------|---------------|-----------------|--------------|------------------------|-----------------|--------|
  | serverless | `lambroll/function` / `aws_lambda_function` | `webhook-handler-prod` | `webhook-handler-{env}` | No | env, runtime=nodejs20.x, arch=arm64, memory=512MB, timeout=30s, X-Ray tracing=Active | not declared | `function.json` |

- `## Naming Patterns` — `webhook-handler-{env}` (function name); `/aws/lambda/webhook-handler-{env}` (CloudWatch Log Group, default Lambda behavior).
- `## Identifying Dimensions` — env, region (us-east-1), Lambda version/alias, log stream.
- `## Dependency Graph` — upstream (`critical-path: unknown`, basis `code: function.json:4,19-25`): Terraform stack owning IAM role (`aws_iam_role.webhook_handler`) — cross-stack via `{{ tfstate }}`, not resolved at catalog time; VPC subnets (×2) and security group — cross-stack; Lambda layer `aws_lambda_layer_version.shared_observability` — cross-stack. Additional: Secrets Manager secret `webhook-handler/{env}/hmac-key` (referenced from `HMAC_KEY_ARN` env var — read-only, not at catalog time). Event source: EventBridge rule configured in a separate Terraform stack — not in-scope; recorded as "downstream event trigger, configured elsewhere."
- `## Signal Envelopes` — none declared in code; runbook anchor falls back to "no declared SLI — establish baseline."
- `## Investigation Runbooks` — at least one for "webhooks not being processed / dropped", with first branch checking upstream Terraform stack (IAM role reachable, VPC connectivity), second branch checking Lambda invocation errors / throttles in CloudWatch Metrics, third branch checking EventBridge rule state (configured elsewhere — requires cross-stack investigation).
- `## Stack-Specific Tooling` — `examples/aws.md`; 1-line note: "lambroll CLI (`lambroll status`, `lambroll log`) is the primary operator tool; see https://github.com/fujiwara/lambroll."
- `## Assumptions and Caveats` — drift note; `{{ tfstate ... }}` values (IAM role ARN, subnet IDs, security group ID, layer ARN) were NOT resolved at catalog time; `secrets/prod.enc.yaml` exists in the repo and was not read — its contents are unknown to this catalog; EventBridge event source mapping is configured in a separate Terraform stack and is out of scope; **Unattributed:** none (single resource); **Completeness:** the inventory lists what the code declares; resources created outside it (console, runtime, other stacks) are not listed.
- `## Open Questions` — the operator provided `ENV=prod` inline (no env file ships in the fixture); `LOG_LEVEL` (`function.json:14`) is unresolved: where is it set at deploy time?
