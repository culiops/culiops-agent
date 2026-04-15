---
name: jsonnet
url: https://jsonnet.org
deploys: Nothing directly — preprocessor that renders to JSON or YAML consumed by another tool
---

## File signatures
- `*.jsonnet`
- `*.libsonnet`
- `jsonnetfile.json` / `jsonnetfile.lock.json` (jsonnet-bundler)

## Stack boundary
Jsonnet is NOT a deploy tool by itself. It is a preprocessor whose output is consumed by another tool (Terraform via `terraform_remote_state` providers, Kubernetes via `kubectl apply`, ECS via ecspresso, Lambda via lambroll, CloudFormation via custom pipelines, etc.).

When jsonnet is detected, ALSO determine the consuming tool and load that detector. If the consuming tool is unclear, STOP and ask the human.

## Parameter sources (highest to lowest priority)
- Top-level arguments (TLA): `jsonnet --tla-str env=prod ...`
- External variables (extVar): `jsonnet --ext-str region=eu-west-1 ...`
- Imports of `.libsonnet` files (resolved via `--jpath` / `JSONNET_PATH`)
- jsonnet-bundler vendored libraries under `vendor/`

## Resource extraction
None directly — extraction happens against the rendered output, using the consuming tool's detector.

## Naming pattern hints
Detect templating helpers (commonly named `name(...)`, `fullname(...)`, or `prefix + ...`) and present the resulting string template.

## Typical cross-stack dependencies
None directly — see the consuming tool's detector.
