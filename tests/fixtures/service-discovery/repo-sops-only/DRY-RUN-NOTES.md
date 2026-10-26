# Dry-run of `service-discovery` against `repo-sops-only`

Simulated run of the IaC path against this fixture. First recorded 2026-04-15; re-run 2026-10-26 for secrets-by-projection.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Secrets exclusion takes precedence over the escape hatch | `secrets/prod.enc.yaml` and `secrets/staging.enc.json` both match `*.enc.*` — excluded BEFORE the deploy-shape scan even runs on them |
| SOPS files never read | `secrets/prod.enc.yaml` and `secrets/staging.enc.json` are excluded by path pattern; `.sops.yaml` matches `*.sops.*` and is not opened either (it holds only KMS key references and nothing in it is needed) |
| Empty-stack handling | After detector pass and secrets exclusion, no IaC files remain; the skill reports **"no in-scope stacks after secrets exclusion"** and stops rather than looping or erroring (explicit expected behaviour, see below) |

## Findings and fixes applied

### F1 — Secrets-exclusion ordering must be explicit *(fixed)*

Without the ordering rule, `secrets/staging.enc.json` could have triggered the escape hatch. Its top-level keys are `db_password`, `api_key` and `sops` — none on the deploy-shape key list (`service:`, `cluster:`, `function:`, etc.), so in practice this particular file would NOT have been flagged even without the fix; `secrets/prod.enc.yaml` has the same top-level keys.

The real risk is the general case: a SOPS-encrypted file could happen to have a deploy-shape key at its top level (e.g., a secrets file with a `service:` key grouping). `SKILL.md` Step 1 "Detect unclassified deploy artifacts" therefore applies the secrets-exclusion rule first, so secrets-shaped paths are excluded unconditionally and entirely, regardless of content. No additional change needed for this fixture.

### Observation — `.sops.yaml` is excluded too *(changed from the 2026-04-15 run)*

`.sops.yaml` is a SOPS configuration file (only a `creation_rules` block with a KMS key ARN, no secret values). The 2026-04-15 run read it. The current Constraint 5 list includes `*.sops.*`, which `.sops.yaml` matches (empty prefix), and nothing in it is needed for a catalog, so the conservative behaviour is: do not open it. Presence can be noted from the file listing ("SOPS is in use") without reading it.

### Expected behaviour — empty-stack exit is explicit *(stated here, not left to implication)*

When the detector pass and the secrets exclusion leave nothing, the skill does not fall through to the "Present and STOP" template and wait for the operator to reject it. It reports:

> "No in-scope stacks after secrets exclusion. The only candidate files (`secrets/prod.enc.yaml`, `secrets/staging.enc.json`, `.sops.yaml`) are SOPS secrets or SOPS config that Constraint 5 forbids opening. Nothing to catalog."

and stops. It then asks only whether the operator meant a different path. This is a clean stop: no catalog, no commit, no `.culiops/service-discovery/` file.

## What a produced doc would look like

No catalog is produced for this fixture. The skill stops at Step 1 with the message above. If the operator replies "there should be more files here", the skill asks the operator to point at the IaC paths before it does anything else. Acceptance checks:

- Neither `*.enc.*` file is opened (no read of `secrets/prod.enc.yaml` or `secrets/staging.enc.json`; `sops -d` is never run).
- `.sops.yaml` is not opened (it matches `*.sops.*`); SOPS use is noted from the file listing only.
- The deploy-shape scan and the escape-hatch prompt do not fire for the encrypted files.
- No `.culiops/service-discovery/` file is written.
