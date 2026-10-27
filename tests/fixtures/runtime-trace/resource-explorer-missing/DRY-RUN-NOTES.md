# Dry-run notes — resource-explorer-missing

## What this fixture validates

- GATE 1a detects the absent Resource Explorer index (`ListIndexes` empty) and the capability matrix shows RE ✗.
- Step 2b still resolves the resource set, via the **Resource Groups Tagging API** (`tag:GetResources`, regional, free), so the plan is priced against a real list and CloudTrail / Wiring / CloudWatch have names to target.
- Cross-Region is reported as **not verifiable**, never as "none outside primary Region": the fallback only sees us-east-1.
- Output explains the gap and gives the operator concrete options.
- Skill does NOT attempt to enable Resource Explorer (write action; out of scope).

## Gate transitions

Same as basic-lambda-service except:

1. GATE 1a — `ListIndexes` returns `{"Indexes": []}`; no `GetIndex` / `ListViews` / `GetView` follow-ups.
2. Gate 2 — RE ✗, resolution fallback `untested` (no probe).
3. Step 2b — `tag:GetResources` (`tg-001`) instead of `resource-explorer-2:Search` (`re-001`).
4. Gate 4 — four source blocks (CE, CloudTrail, Wiring, CloudWatch).

## Acceptance check

- Capability matrix shows RE as "— skipped" and the tagging-API fallback as `untested` (never ✓ without a probe).
- The resolved resource set is present and sourced from `tg-001`.
- Cross-Region section says "not verifiable" and offers the three options; the phrases "none outside primary Region" and "no cross-region drift" do not appear.
- Skill never proposes enabling RE as something it will do itself.
- Needs `tag:GetResources` in the read-only IAM policy (review finding M4).
