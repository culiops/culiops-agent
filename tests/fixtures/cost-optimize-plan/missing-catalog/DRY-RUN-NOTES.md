# Dry-run notes - missing-catalog

## Gate transitions

1. **GATE 1 (Scope)** - Operator provides the upstream report path. Skill loads `upstream-report.md`, extracts 2 items, reads `**Cloud:** aws`, `**Scope:** 987654321098 / acme-staging`; target = account 987654321098, region us-east-1. $5/mo floor: both pass ($52, $180). Checks `.culiops/service-discovery/`: **does not exist**. Asks for the IaC repo path: **operator has none to give** ("none - ownership from tags only"). Scoping summary shows `Catalog: none - Dimension 4 conservative scoring` and `IaC repo(s): none`. Skill notes owners will be `unknown` and Dimension 4 ⚪ (🟡-equivalent for the lifecycle change; a delete is held in 🔴). Operator confirms. Approved.

2. **GATE 2 (Verification batch)** - Query 0 (`0a`, `0b-1`, `0b-2`), then item #1 -> `delete-unattached-ebs.md` (snapshots, attach/detach history, Recycle Bin rules) and item #2 -> `lifecycle-s3.md` (lifecycle config, versioning, Intelligent-Tiering, size metrics, Storage Class Analysis, inventory size distribution, bill-derived rates). Both playbooks present; no manual-review items. One documentation row (`d1`, S3 RestoreObject page) is added for the Glacier Flexible behaviour claim (Constraint 16). IAM list and per-query cost itemized (free describe/list, LookupEvents free, one Cost Explorer request, a few S3 GETs). Operator approves. Per Step 2, each item's playbook queries are listed as conditional on Query 0b; here no owner routes to ❔, so none is skipped.

3. **Step 3 (Execute)** - `0a`: account = `Scope`. Ownership probes: no controller tags, no IaC to grep -> both owners `unknown`. All 10 queries succeed.

4. **Step 4 (Triage)** - rules in order:
   - **#1 (delete vol-0bbbb1):** Rev 🟡 (valid snapshot, taken after the last detach and inside the window), Blast 🟢, Evidence 🟢 (no events in 90d), Dep ⚪. Rule 1 no; rule 2 no (EBS is not idle-ambiguous); rule 3 yes: the action is a delete and Dimension 4 is ⚪ (Evidence is 🟢, so the "delete AND Evidence not 🟢" clause does not fire; the last clause does) -> **🔴 `dependency-unknown`**.
   - **#2 (lifecycle):** Rev 🟡 (Transition to Glacier Flexible, confirmed by docs row `d1`; owner unknown), Blast 🟢, Evidence 🟢 (0 GETs on aged objects over 98d; net +$180.3/mo; size within 20%), Dep ⚪. Rule 4 -> **🟡**.
   - Ordering hint: fresh final snapshot before deleting #1, once the dependency question is answered.

5. **GATE 3 (Plan review)** - Operator reviews: dependency-⚪ note per item and in Gaps; #1 is held in 🔴 until the IaC repo or a catalog is supplied. Approves. Plan written to `.culiops/cost-optimize-plan/acme-staging-20260528-1136.md`, uncommitted.

## What this fixture validates

- **A missing catalog / IaC repo does not block the plan, and it does not make a delete look safe.** Dimension 4 ⚪ takes the 🟡-equivalent path (rule 4) for a non-delete, but a delete with Dimension 4 or Blast ⚪ is 🔴 `dependency-unknown` (rule 3). Evidence ⚪ still forces 🔴 as before.
- **The plan is still produced** and conservative; the absence of a catalog is a scoping gap, not a verification failure (all queries succeed, Evidence 🟢).
- **Owner `unknown` is handled:** no `code:` refs are fabricated, Reversibility gets no "re-apply old IaC" basis, the header says `IaC repo(s): none`.
- **Plan summary shows 🟢 = 0, 🟡 = 1, 🔴 = 1.**
- **The lesson is stated accurately:** neither item would be a Fast win with a catalog (Reversibility 🟡), so the plan does not promise one.
- **Snapshot-before-delete** ordering hint emitted for #1.
- **Behaviour claims and prices are sourced:** Glacier restore behaviour from a documentation read; fallback prices from a named Pricing API query with region and date.

## Acceptance check

A reviewer confirms: (a) the skill does not error on a missing catalog / IaC repo and proceeds conservatively; (b) the lifecycle item lands in 🟡 and the delete lands in 🔴 `dependency-unknown`; (c) each item states Dimension 4 ⚪ and why, with owner `unknown`; (d) summary is 🟢=0, 🟡=1, 🔴=1; (e) Gaps mention the missing catalog and IaC repo with `service-discovery` / supplying the repo as the remedy, and do not claim a Fast win; (f) header has `Target` and `IaC repo(s)`; `Drift` says no comparison was possible.
