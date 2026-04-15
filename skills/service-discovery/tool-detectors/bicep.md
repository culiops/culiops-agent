---
name: bicep
url: https://learn.microsoft.com/azure/azure-resource-manager/bicep/
deploys: Azure resources via the Bicep DSL (compiles to ARM)
---

## File signatures
- `*.bicep`
- `bicepconfig.json`
- `*.parameters.<env>.json` (ARM parameter files)
- `*.bicepparam` (Bicep parameter files)

## Stack boundary
One stack = one top-level `*.bicep` file deployed at a defined scope (resource group, subscription, management group, or tenant).

Multi-instance is expressed via:
- per-environment `*.parameters.<env>.json` (ARM parameter files) passed via `az deployment <scope> create -p`
- `*.bicepparam` files passed the same way
- inline `az deployment <scope> create -p key=value` overrides

## Parameter sources (highest to lowest priority)
- inline `-p key=value` on the `az deployment` CLI
- `*.bicepparam` file passed via `-p`
- `*.parameters.<env>.json` (ARM parameter file) passed via `-p`
- `param` declarations with default values in the Bicep file
- Key Vault references via `@Microsoft.KeyVault(SecretUri=...)` (record reference, NEVER read)

## Resource extraction
- Each `resource <symbolic-name> '<type>@<api-version>' = { ... }` → one inventory entry; raw type is `<type>@<api-version>` (e.g., `Microsoft.Web/sites@2022-09-01`)
- `module <symbolic-name> '<path-or-registry-ref>' = { ... }` → if `<path-or-registry-ref>` is a local `*.bicep`, chase only if it's part of the same deploy unit; otherwise record as a sub-module reference
- `resource <symbolic-name> '<type>@<api>' existing = { ... }` → cross-resource (or cross-scope) reference to an already-deployed resource; record as a dependency, do NOT chase

## Naming pattern hints
Bicep does not enforce a naming convention. Detect recurring templates across resource `name:` properties (e.g., `name: '${prefix}-${env}-${location}'`).

## Typical cross-stack dependencies
- Resources in other resource groups / subscriptions via `existing` declarations with explicit `scope:`
- Key Vault secret URIs (`@Microsoft.KeyVault(...)`)
- Role assignments referencing `principalId` of identities deployed elsewhere
