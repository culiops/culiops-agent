# Dry-run of `service-discovery` against `repo-unknown-tool`

Simulated run of the 5-step skill against this fixture. Recorded on 2026-04-15.

## What the fixture exercised

| Principle | Exercised by |
|-----------|--------------|
| Detector loader correctly produces zero matches | No `tool-detectors/*.md` signature matches `mycli.yml` or `services/api.json`; no known tool detected |
| Escape hatch fires | `mycli.yml` (top-level keys: `service:`, `cluster:`, `deploy:`) and `services/api.json` (top-level keys: `service:`, `image:`) both match deploy-shape heuristic; skill STOPS at Step 1 with the three-option prompt |
| No silent skip | Without operator input, no resource inventory is produced for these files; Step 1 cannot advance |
| Assumptions caveat | "teach me" or "ignore" answers trigger the mandatory Assumptions section line per Step 5 §10 |

## Path A — operator answers "teach me"

**Simulated dialog:**

> "I see these files that look like deploy descriptors but I don't recognize the tool: `mycli.yml`, `services/api.json`. For each, please tell me one of: tool name / teach me / ignore."
>
> Operator: "`mycli.yml` — teach me. Stack boundary: one `mycli.yml` is one deploy unit; the `service_definition:` key points to `services/api.json` which is part of the same stack. Parameter sources: environment variables. Resource mapping: `service:` key → one container/service running on the cluster named by `cluster:`; `image:` in the service definition → the container image. No cross-stack dependencies declared."

After this answer, the skill proceeds with operator-supplied mappings:

- Stack = `mycli.yml` + `services/api.json`
- `services/api.json` is attributed to this stack (not a second unclassified file)
- Resource inventory: 1 row — `mycli/service` (operator-supplied raw type); service name = `api`; image = `registry.example.com/api:2026.04.1`; cluster = `my-cluster-prod`
- No `arn:`, `gs://`, or cloud-provider references detected → no cloud resource equivalents to record
- Naming fragment: `api` (no templating detected; static)
- Identifying dimensions: replicas=4, ports=[8080]
- Signal envelope: not declared
- Cross-stack dependencies: none declared

The produced catalog would include the mandatory Assumptions caveat (Step 5 §10):

> *"Tool `mycli` was not pre-known to the skill; the stack boundary, parameter resolution, and resource mapping for this tool came from operator input during this scan and are not encoded in any detector file. Recommend contributing `tool-detectors/mycli.md`."*

## Path B — operator answers "ignore"

**Simulated dialog:**

> Operator: "`mycli.yml` — ignore. `services/api.json` — ignore. These config files belong to an internal deploy tool not yet supported by the skill."

Outcome: no inventory rows from either file. Since this repo contains no other stacks (no other IaC files), the skill exits Step 1 with:

> "No in-scope stack found after excluding the files you marked `ignore`. If you want to catalog any of the skipped files, re-run and choose `teach me`."

If other stacks had existed in the repo alongside the unknown tool, the catalog for those other stacks would carry the mandatory Assumptions caveat:

> *"Files `mycli.yml` and `services/api.json` are present in the repo but were marked `ignore` at operator request. They may represent deployed resources not included in this catalog."*

## Findings and fixes applied

### Observation — deploy-shape heuristic is accurate for this fixture *(no fix required)*

`mycli.yml` has three deploy-shape keys (`service:`, `cluster:`, `deploy:`) and `services/api.json` has two (`service:`, `image:`). The heuristic fires correctly. No false negatives.

### Observation — `services/api.json` is caught as a referenced file, not a second independent stack *(no fix required)*

The escape hatch correctly lists both `mycli.yml` and `services/api.json` as unclassified because neither was attributed to any loaded detector. In Path A, the operator explains that `services/api.json` is referenced by `mycli.yml` (via `service_definition: services/api.json`) and belongs to the same stack — after which the skill treats the JSON as part of the single `mycli` stack, not as a second independent deploy unit. The current prompt wording handles this correctly: the operator can name both files together in one "teach me" answer.

### Observation — `DB_URL` in `services/api.json` contains a credentials-looking value *(no fix required)*

The value `postgres://api:redacted@db.example.internal:5432/api` is hard-coded in the JSON, not behind a secrets-exclusion path. It's a plaintext connection string (the `redacted` placeholder makes the fixture safe). The skill would read this file in Path A (after operator approval), record the `DB_URL` key name, and flag the value as a credentials-shaped string in the "Assumptions and Caveats" section ("env var `DB_URL` appears to contain database credentials inline — recommend moving to a secrets manager reference"). This is correct behavior under the Iron Law (read what's there; surface what's concerning).
