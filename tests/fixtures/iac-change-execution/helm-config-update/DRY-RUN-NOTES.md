# Dry-run of `iac-change-execution` against `helm-config-update`

Expected skill behaviour at each step. Recorded for pre-dry-run reference; "Gaps surfaced" and "Fixes applied" are filled in during the actual dry-run.

## Step 1 — Research

**Input:** operator request — "Increase replica count from 2 to 4 for notifyapi in prod."

**Expected behaviour:**

| Check | Expected outcome |
|-------|-----------------|
| Catalog lookup | Finds `.culiops/service-discovery/notifyapi-prod.md` — reads dependency graph and naming pattern |
| Pre-flight lookup | Finds `.culiops/pre-flight/notifyapi-config-update-20260424-1030.md` — reads verdict (Green), reuse window (expires 2026-04-27T10:30Z), and conditions |
| Pre-flight reuse check | Today is 2026-04-24; record is within reuse window. Skill checks: change matches description ✓, no intervening commits to `values-prod.yaml`/`Chart.yaml` ✓, no active incidents ✓ → REUSE (do not re-invoke `pre-flight`) |
| Tool detection | Finds `Chart.yaml` → identifies Helm. Notes `values.yaml` (base) and `values-prod.yaml` (prod overrides) |
| Values file targeting | `replicaCount: 2` is in `values-prod.yaml` (overrides base default of 1). Skill identifies `values-prod.yaml` as the file to modify |
| Naming pattern | Reads catalog: `{{ .Chart.Name }}` — Kubernetes resources use chart name directly |

## Step 2 — Plan

**Expected output:**

```
Phase 1 (of 1):
  Modify: values-prod.yaml — replicaCount: 2 → 4
  Add:    (none)
  Destroy:(none)

Execution path: PR (default)
Pre-flight: REUSED — .culiops/pre-flight/notifyapi-config-update-20260424-1030.md (Green, expires 2026-04-27T10:30Z)
```

## Step 3 — Implement

**Expected behaviour:**

- Modifies `values-prod.yaml`: changes `replicaCount: 2` to `replicaCount: 4`
- Does NOT touch `values.yaml` (base defaults are not env-specific overrides)
- Does NOT modify any template files
- Change is minimal — only the one line

**Expected diff:**
```diff
--- a/values-prod.yaml
+++ b/values-prod.yaml
@@ -1,7 +1,7 @@
 # Prod overrides — applied on top of values.yaml
 # To change: helm upgrade notifyapi . -f values.yaml -f values-prod.yaml

-replicaCount: 2
+replicaCount: 4
```

## Step 4 — Code review gate

**Expected behaviour:**

- Skill surfaces the diff (single line change) for operator review
- Operator approves

## Step 5 — Pre-flight

**Expected behaviour:**

- Skill reads existing record `.culiops/pre-flight/notifyapi-config-update-20260424-1030.md`
- Confirms reuse conditions are still met (within window, no intervening changes, no incidents)
- Records "pre-flight reused" — does NOT call the `pre-flight` skill
- Logs: "Reusing pre-flight record from 2026-04-24T10:30Z (Green, valid until 2026-04-27T10:30Z)"

## Step 6 — Execute (PR path)

**Expected behaviour:**

- Skill opens a GitHub PR (or prints the git commands to do so)
- PR title: something like `feat(notifyapi): scale replicas 2→4 in prod`
- PR description references the reused pre-flight record
- Skill does NOT run `helm upgrade` directly

**Helm upgrade command for PR description (for operator reference):**
```
helm upgrade notifyapi . \
  -f values.yaml \
  -f values-prod.yaml \
  --namespace notifyapi-prod \
  --atomic \
  --timeout 5m
```

## Key tests

| Test | What it verifies |
|------|-----------------|
| Helm detection | Skill identifies Chart.yaml → Helm (not Terraform) |
| Catalog read | Skill uses dependency graph from `.culiops/service-discovery/notifyapi-prod.md` |
| Pre-flight reuse | Skill finds existing Green record and reuses it without re-invoking pre-flight |
| Values file targeting | `values-prod.yaml` is modified, not `values.yaml` |
| Minimal diff | Only `replicaCount` line is changed |
| PR path | No direct apply; skill produces PR workflow |

## Gaps surfaced

_(to be filled during actual dry-run)_

## Fixes applied

_(to be filled during actual dry-run)_
