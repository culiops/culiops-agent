---
name: pulumi
url: https://www.pulumi.com
deploys: Multi-cloud infrastructure via general-purpose programming languages
---

## File signatures
- `Pulumi.yaml` (project file)
- `Pulumi.<stack>.yaml` (per-stack config files)
- `__main__.py` plus a `pulumi` Python import (Python projects)
- `index.ts` / `index.js` plus a `@pulumi/*` import (Node projects)
- `Program.cs` plus a `Pulumi` C# using directive (.NET projects)
- `main.go` plus a `pulumi-go` import (Go projects)

## Stack boundary
One *project* = one `Pulumi.yaml`. One *instance* = one `Pulumi.<stack>.yaml` (a "stack" in Pulumi terminology).

The catalog targets one stack instance — confirm with the human which `Pulumi.<stack>.yaml` to use.

## Parameter sources (highest to lowest priority)
- `--config key=value` on the CLI
- `Pulumi.<stack>.yaml` `config:` block
- ESC environments referenced from `Pulumi.<stack>.yaml` (`environment:`)
- The configured secrets provider (Pulumi Cloud, AWS KMS, Azure Key Vault, etc.) — record references, NEVER read values
- `pulumi.Config()` defaults declared in code

## Resource extraction
- Each `new <pulumi/cloud>.Resource(...)` (or equivalent in the project's language) → one inventory entry; raw type is the Pulumi resource type
- `pulumi.StackReference` → cross-stack dependency
- Component resources (custom classes extending `pulumi.ComponentResource`) → record as a logical grouping; expand into the contained resources

## Naming pattern hints
Pulumi auto-suffixes physical names by default unless `name:` is set explicitly. Detect explicit name templates from constructor `name` arguments.

## Typical cross-stack dependencies
- Other Pulumi stacks via `StackReference`
- ESC environments and the configured secrets store
- Cloud-provider data sources (`getXxx` functions in the SDK)
