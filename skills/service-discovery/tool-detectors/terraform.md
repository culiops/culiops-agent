---
name: terraform
url: https://www.terraform.io
deploys: Multi-cloud and on-prem infrastructure via providers
---

## File signatures
- `*.tf`
- `*.tf.json`
- `terraform.tfvars`, `*.auto.tfvars`, `*.tfvars.json`
- `.terraform.lock.hcl`
- `terragrunt.hcl` (Terragrunt wrapper — record as Terragrunt-on-Terraform)

## Stack boundary
A "stack" is one root module — a directory containing a `provider` block plus a `terraform { backend ... }` or `terraform { required_providers ... }` block at the top level, with no parent module calling it.

Multi-instance is expressed via:
- per-environment `*.tfvars` files (commonly `envs/<env>.tfvars` or `terraform.<env>.tfvars`) passed via `-var-file=...`
- Terraform workspaces (`terraform workspace`)
- Terragrunt environments (one directory per env, each with its own `terragrunt.hcl`)

## Parameter sources (highest to lowest priority)
- `-var key=value` flags on the CLI
- `*.tfvars` / `*.tfvars.json` files passed via `-var-file=...`
- `*.auto.tfvars` / `*.auto.tfvars.json` files (auto-loaded)
- `TF_VAR_*` environment variables
- Workspace-keyed values (e.g., `lookup(local.per_env, terraform.workspace, ...)`)
- `variable` block defaults
- `terraform_remote_state` lookups (record the remote state as a cross-stack dependency, do NOT chase it)

## Resource extraction
- Each `resource "<type>" "<name>"` block → one inventory entry; raw type is the literal type string (e.g., `aws_ecs_service`, `google_storage_bucket`, `azurerm_key_vault`)
- `module` blocks → record as a sub-stack reference; chase only if the module source is local within the same root module
- `data` blocks → cross-resource lookup; record as a dependency on the looked-up resource
- `terraform_remote_state` → cross-stack dependency

## Naming pattern hints
Terraform does not enforce a naming convention. Detect the recurring template across `name = ...` arguments (e.g., `${var.service}-${var.env}-${each.key}`) and present that as the inferred pattern.

## Typical cross-stack dependencies
- Other Terraform stacks via `terraform_remote_state`
- Cloud-provider resources via `data.<provider>_*` lookups
- HCP / Vault / external secret stores via provider data sources
