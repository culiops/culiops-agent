# Dry-run of `iac-change-execution` against `helm-config-update`

Expected skill behaviour at each step. Recorded for pre-dry-run reference; "Gaps surfaced" and "Fixes applied" are filled in during the actual dry-run.

## Step 1 — Research

**Input:** operator request — "Increase replica count from 2 to 4 for notifyapi in prod."

**Expected behaviour:**

| Check | Expected outcome |
|-------|-----------------|
| Catalog lookup | Finds `.culiops/service-discovery/notifyapi-prod.md` — reads dependency graph and naming pattern |
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

## Step 4 — Execute

### GATE 2: Code review

- Skill surfaces the diff (single line change) for operator review
- Operator approves

### 4a: Generate plan output

- Skill presents: `helm diff upgrade notifyapi . -f values.yaml -f values-prod.yaml -n notifyapi-prod`
- Expected diff: Deployment replica count changes from 2 to 4

### 4b: Pre-flight gate

- Skill checks `.culiops/pre-flight/` for a reusable record
- Finds `.culiops/pre-flight/notifyapi-config-update-20260424-1030.md`
- Match rule check: (a) same service `notifyapi` + action type (replica scaling) ✓, (b) resources (Deployment) are a subset of assessed resources ✓, (c) no commits since `d4e5f6g` touch `values-prod.yaml` or `Chart.yaml` ✓
- **REUSE** — does NOT re-invoke pre-flight
- Shows: "Using existing pre-flight record from `.culiops/pre-flight/notifyapi-config-update-20260424-1030.md` (verdict: GREEN)"
- GATE 3: Green → proceed

### 4c: Execute (PR path)

- Skill presents PR action and waits for GATE 4 approval
- Creates branch `iac-change/notifyapi-scale-replicas`, commits, opens PR
- PR description references the reused pre-flight record
- Reports PR URL to operator
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

## Step 5 — Verify & Record

- PR path: "PR created. Pipeline will handle apply and verification."
- Writes execution record to `.culiops/iac-change-execution/notifyapi-scale-replicas-<timestamp>.md`
- Record notes: pre-flight reused (not re-invoked)
- GATE 5: offers to commit the record

## Key tests

| Test | What it verifies |
|------|-----------------|
| Helm detection | Skill identifies Chart.yaml → Helm (not Terraform) |
| Catalog read | Skill uses dependency graph from `.culiops/service-discovery/notifyapi-prod.md` |
| Pre-flight reuse | Skill finds existing Green record, checks match rule, reuses without re-invoking |
| Values file targeting | `values-prod.yaml` is modified, not `values.yaml` |
| Minimal diff | Only `replicaCount` line is changed |
| PR path | No direct apply; skill produces PR workflow |

## Gaps surfaced

_(to be filled during actual dry-run)_

## Fixes applied

_(to be filled during actual dry-run)_
