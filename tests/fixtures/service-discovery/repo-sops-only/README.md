# repo-sops-only — SOPS-only fixture

A repository whose only "configuration" is SOPS-encrypted secrets. There is no IaC, no deploy tool, no manifests. The fixture exists as a **regression case** to confirm:

1. SOPS files are NEVER read by the skill.
2. SOPS files do NOT trigger the unclassified-deploy-artifacts escape hatch (the secrets-exclusion rule must be checked BEFORE the deploy-shape heuristic).
3. The skill stops at Step 1 with "no in-scope stacks after secrets exclusion" (an explicit exit, not an implied one) rather than looping or producing a misleading catalog.

## What this fixture exercises in the skill

- **Secrets exclusion takes precedence over the escape hatch.**
- **Empty-stack handling:** the skill produces a useful "nothing to catalog" outcome rather than a fatal error.
