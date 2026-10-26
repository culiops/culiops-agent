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
Jsonnet is NOT a deploy tool by itself. In this skill's supported stack it appears as the format of ecspresso configs and service/task definitions, and of lambroll `function.jsonnet`. ecspresso (v2.0+ for the config file) and lambroll both render Jsonnet themselves, so no separate `jsonnet` binary is involved.

When jsonnet is detected, ALSO determine the consuming tool and load that detector (`ecspresso.md` or `lambroll.md`). If the consuming tool is unclear, STOP and ask the human. Do not assume Terraform consumes Jsonnet; there is no such integration in the supported stack.

## Secret-bearing files
- Apply the consuming tool's Secret-bearing files section.
- `std.native('must_env')`, `std.native('env')`, `std.native('tfstate')`, `std.native('ssm')` and `std.native('secretsmanager_arn')` are references: record the variable name / address / path, never the resolved value, and never resolve `tfstate`.
- `--ext-str` / `--ext-code` values from the CLI or scripts: names only; withhold values whose key matches the secret-key list (`password`, `secret`, `token`, `key`, `credential`, `dsn`, `conn`, `auth`, `cert`, …).

## Parameter sources (highest to lowest priority)
- External variables (extVar): `--ext-str` / `--ext-code` as used by ecspresso and lambroll (read via `std.extVar`)
- Native functions provided by the consuming tool (`std.native('must_env')` etc.; ecspresso v2.4+ documents them; lambroll's README documents `std.extVar` only, native functions UNVERIFIED)
- Imports of `.libsonnet` files (resolved via the jsonnet path)
- jsonnet-bundler vendored libraries under `vendor/`

## Resource extraction
None directly — extraction happens against the rendered output, using the consuming tool's detector.

## Naming pattern hints
Detect templating helpers (commonly named `name(...)`, `fullname(...)`, or `prefix + ...`) and present the resulting string template.

## Typical cross-stack dependencies
None directly — see the consuming tool's detector.
