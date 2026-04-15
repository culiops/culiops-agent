# repo-lambroll-only — lambroll fixture

A synthetic lambroll-managed Lambda function. Nothing is runnable.

## What's modelled

`webhook-handler` — a fictional Node.js Lambda that processes inbound webhooks, in `us-east-1`.

- One Lambda function (`webhook-handler-${ENV}`) — Node.js 20, 512MB memory, 30s timeout.
- VPC-attached (subnets and security group come from `{{ tfstate ... }}`).
- Reads one secret from Secrets Manager (HMAC verification key) — referenced from `Environment.Variables`.
- Logs to CloudWatch Log Group `/aws/lambda/webhook-handler-${ENV}` (default Lambda behavior).
- Triggered by an EventBridge rule configured in a separate Terraform stack — recorded as a downstream-config-elsewhere note.

A SOPS-encrypted file (`secrets/prod.enc.yaml`) sits in the repo as a regression case — the skill MUST skip it under the secrets-exclusion rule.

## Environments

Two environments via `function.json` env interpolation; `lambroll deploy --envfile envs/<env>.env`.

## Stack layout

```
repo-lambroll-only/
├── function.json
├── .lambdaignore
├── src/
│   └── index.js       # placeholder — represents the deploy package
└── secrets/
    └── prod.enc.yaml  # SOPS-encrypted; skill MUST skip
```

## What this fixture exercises in the skill

- **Detector loading:** `lambroll.md` matches `function.json`.
- **Cross-stack dependency, not chased:** `{{ tfstate ... }}` references for Role, VPC, layers — recorded as upstream Terraform deps.
- **Secret reference recording:** `Environment.Variables` value referencing a Secrets Manager ARN is recorded; the secret is never read.
- **SOPS regression:** `secrets/*.enc.yaml` matches the secrets exclusion pattern — skill must NEVER read it; should NOT classify as a deploy artifact and trigger the escape hatch.
- **Event source noted as out-of-scope:** the EventBridge rule that triggers the function lives in a different stack — recorded as "configured elsewhere".
