# Dry-run of `service-discovery` against `repo-sops-only`

Simulated run of the 5-step skill against this fixture. Recorded on 2026-04-15.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Secrets exclusion takes precedence over the escape hatch | `secrets/prod.enc.yaml` and `secrets/staging.enc.json` both match `*.enc.*` — excluded BEFORE the deploy-shape scan even runs on them |
| SOPS files never read | `secrets/prod.enc.yaml` and `secrets/staging.enc.json` are excluded by path pattern; `.sops.yaml` may be read (it's a config file, not a secrets file) but contains only KMS key references, no secret values |
| Empty-stack handling | After detector pass and secrets exclusion, no IaC files remain; skill exits Step 1 with "no in-scope stack found" rather than looping or erroring |

## Findings and fixes applied

### F1 — SKILL.md did not make secrets-exclusion ordering explicit *(fixed, same commit as Task 15)*

Without the fix, `secrets/staging.enc.json` could have triggered the escape hatch. Its top-level keys are `db_password`, `api_key`, and `sops` — none of which appear on the deploy-shape key list (`service:`, `cluster:`, `function:`, etc.), so in practice this particular file would NOT have been flagged as deploy-shaped even without the ordering fix. However, `secrets/prod.enc.yaml` has top-level keys `db_password`, `api_key`, `sops` as well — same situation.

The real risk addressed by the fix is not this specific fixture but the general case: a SOPS-encrypted file could happen to have a deploy-shape key at its top level (e.g., a secrets file with a `service:` key grouping). The ordering fix ensures secrets-shaped paths are excluded unconditionally and entirely, regardless of their content.

The fix was applied in `SKILL.md` Step 1 "Detect unclassified deploy artifacts" before the Task 15 dry-run commit. No additional fix needed here.

### Observation — `.sops.yaml` correctly not excluded *(no fix required)*

`.sops.yaml` does not match any secrets-exclusion pattern (`*.enc.*`, `*.secret.*`, `secrets/`, `.env*`, `*.pem`, `*.key`, `id_rsa*`, `vault/`). It is a SOPS configuration file, not an encrypted secrets file. The skill may read it — it contains only a `creation_rules` block with a KMS key ARN. Reading it reveals the encryption scheme in use and confirms SOPS is in the repo, but discloses no secret values. Correct behavior.

### Observation — empty-stack outcome is handled by implication *(no fix required)*

SKILL.md does not have an explicit "no stacks found" exit path. However, Step 1's "Present and STOP" template shows the operator what was detected before asking for confirmation; if `IaC tool(s) detected: none` and `In-scope stack(s): none`, the operator would reject and the skill would naturally halt. An explicit "no in-scope stack found" message would be a usability improvement but is not a correctness gap — the Iron Law ("no assumptions, ask the human") already prevents the skill from inventing a catalog.

## What a produced doc would look like

No catalog is produced for this fixture. The skill exits Step 1 with:

> "Service: `<name>`
> Repo: `<path>`
> IaC tool(s) detected: none
> In-scope stack(s): none
> Note: The only files in this repo are SOPS-encrypted secrets (`secrets/prod.enc.yaml`, `secrets/staging.enc.json`), which were excluded under Constraint 5. No IaC stack was found.
>
> Is this correct?"

If the operator confirms, the session ends. No `.culiops/service-discovery/` file is written. If the operator says "incorrect — there should be more files here", the skill asks the operator to point at the IaC files before proceeding.
