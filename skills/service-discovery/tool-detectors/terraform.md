---
name: terraform
url: https://www.terraform.io
deploys: Infrastructure via providers (AWS in this skill's supported stack); covers OpenTofu and Terragrunt
---

## File signatures
- `*.tf`, `*.tf.json`
- `*.tofu`, `*.tofu.json` (OpenTofu)
- `terraform.tfvars`, `*.auto.tfvars`, `*.tfvars.json`, `*.tfbackend`
- `.terraform.lock.hcl`
- `terragrunt.hcl`, `root.hcl`, `terragrunt.stack.hcl` (Terragrunt wrapper — record as Terragrunt-on-Terraform)
- Exclude `.terraform/**` (downloaded third-party modules; matches `*.tf` but is not this repo's code) and `node_modules/**`

## Stack boundary
A "stack" is one root module: a directory with `*.tf` files that is NOT the target of any local `module "x" { source = "./…" }` in the repo AND satisfies at least one of:
- it has a `terraform { backend ... }` block,
- it has a `terragrunt.hcl` beside it (or a Terragrunt unit points at it),
- the operator names it as the apply directory.

`required_providers` alone does not make a root module (child modules declare it too). A root without an explicit `provider` block is still a root.

Multi-instance is expressed via:
- per-environment `*.tfvars` files (commonly `envs/<env>.tfvars` or `terraform.<env>.tfvars`) passed via `-var-file=...`
- Terraform workspaces (`terraform.workspace` references in the code; the active workspace is unknown from files alone — ask)
- Terragrunt environments (one directory per env, each with its own `terragrunt.hcl`)

## Secret-bearing files
- NEVER read `*.tfstate*`. NEVER run `terraform state …`, `terraform output`, `terraform plan`, or `terraform init` (state reads and provider downloads can expose secrets and mutate the working directory).
- From `*.tfvars` / `*.auto.tfvars` / `*.tfvars.json` read variable NAMES and non-secret values only. A value is withheld, recorded as `<set in <file>:<line>>`, when the variable is declared `sensitive = true` OR the key contains (case-insensitive) any of: `password`, `passwd`, `secret`, `token`, `key`, `apikey`, `api_key`, `private`, `credential`, `dsn`, `conn`, `connection_string`, `auth`, `cert`.
- `secrets*.yaml`, `*.sops.*`, `*.enc.*` are not opened at all; never run `sops -d`.

## Parameter sources (highest to lowest priority)
- `-var key=value` and `-var-file=...` on the CLI. They are applied in command-line order, later wins (UNVERIFIED against current Terraform docs; confirm before relying on the order)
- `*.auto.tfvars` / `*.auto.tfvars.json` (auto-loaded, alphabetical order)
- `terraform.tfvars` / `terraform.tfvars.json` (auto-loaded)
- `TF_VAR_*` environment variables
- Workspace-keyed values (e.g., `lookup(local.per_env, terraform.workspace, ...)`)
- `variable` block defaults
- `terraform_remote_state` lookups (record the remote state as a cross-stack dependency, do NOT chase it)

Apply the Secret-bearing files rule to every source above.

## Resource extraction
- Each `resource "<type>" "<name>"` block → one inventory entry; raw type is the literal type string (e.g., `aws_ecs_service`, `aws_s3_bucket`)
- `module` blocks → record as a sub-stack reference; chase only if the module source is local within the same root module. Remote modules (registry, git, S3): record `source` + `version`; read only if vendored in the repo; do not fetch
- `data` blocks → cross-resource lookup; record as a dependency on the looked-up resource
- `terraform_remote_state` → cross-stack dependency

## Naming pattern hints
Terraform does not enforce a naming convention. Detect the recurring template across `name = ...` arguments (e.g., `${var.service}-${var.env}-${each.key}`) and present that as the inferred pattern.

## Typical cross-stack dependencies
- Other Terraform stacks via `terraform_remote_state`
- AWS resources via `data.aws_*` lookups
- HCP / Vault / external secret stores via provider data sources
