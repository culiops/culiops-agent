# Dry-run of `pre-flight` against `app-impact-env-rename`

Simulated runs on 2026-10-26: operator from `operator-script.md` (L3 declined), app on GitHub with `gh` results from `gh-responses.md` (Mode B).

## Baseline (skill before category 11), cues removed

| Runs | Verdict | Asked for the app source | Cited the app | Verdict driven by |
|---|---|---|---|---|
| 1 | RED | no | no. "Confirm in the app source" was handed to the operator as a mitigation | category 7 Red + Yellow/⚪ escalation |

The gate said RED for the wrong reason. If the operator adds alarms (category 7) and runs service-discovery (category 4), the verdict drops to YELLOW, the rename is applied, and every invoice upload fails behind a green `/healthz`. A run whose operator script still had the `Application source` section did ask, so it was discarded as cued.

## With category 11

| Principle | Exercised by |
|---|---|
| Trigger | Renamed env vars and a value-format change are app-contract changes, so Q8 is asked |
| Mode B approval | Choosing `gh` at Q8 approves the four `GET` read types. A first run, from before this rule, asked for a second approval, got none, and left category 11 ⚪ |
| Pinned version | `commits/v3.8.2` → `5f2c9a1`. Tree and contents were read at that SHA, not at `main` |
| No code search as evidence | `gh search code` was not used (default branch only) |
| Findings | `app:acme-billing/invoicesvc@5f2c9a1:internal/config/config.go:17` reads `INVOICE_BUCKET` only → empty bucket, every `PutObject` fails (`internal/store/s3.go:6-7`). `:18` reads `PDF_TIMEOUT` only → falls back to 5s. `20` without a unit would fail `time.ParseDuration` even under the new name |
| Silent breakage | `/healthz` returns 200 without touching S3 (`cmd/invoicesvc/main.go:17`), so ECS completes the rollout |
| Operator premise | "The values are the same" is `operator-stated`. The app reads names, and one value changed format |

## Scoring

| # | Category | Score | Signal |
|---|---|---|---|
| 1 | Blast radius | 🟡 | Task definition replaced, every task redeployed (`plan:12-21`) |
| 2 | Reversibility | 🟡 | Revert, then apply as a new revision. Failed uploads in the window are not undone |
| 3 | Change velocity | 🟢 | Fixture condition |
| 4 | Dependency impact | ⚪ | No catalog |
| 5 | Timing context | 🟢 | `operator` |
| 6 | Operator familiarity | 🟡 | First time with this service |
| 7 | Observability readiness | ⚪ | No monitoring in the visible IaC; repo is partial |
| 8 | Cost impact | 🟢 | No size change |
| 9 | Security posture | 🟢 | Names only |
| 10 | Resource health | ⚪ | L3 declined |
| 11 | Application compatibility | 🔴 | Old names still read (`config.go:17,18`), silent failure |

Record header: plan hash `sha256:fa5e225b0c3bafd87520f13957b436b2095f206c7c9e0ef6dca3cd9a5df66b07`, target `444455556666` / `ap-northeast-1`, App source `gh acme-billing/invoicesvc @ v3.8.2 (5f2c9a1)`.

**Verdict: RED — SOFT BLOCK, driven by category 11.**

## Mitigations the skill should recommend

- Expand–contract. Ship an app release that reads the new names and falls back to the old ones, and that parses both `20` and `20s`. Deploy it and verify a real invoice upload, then apply the rename. Alternatively, set both old and new names for one release.
- Check after apply with a real invoice, not `/healthz`. Make the health check, or an alarm on upload errors, cover the S3 write path.
