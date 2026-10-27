# missing-catalog - cost-optimize-plan fixture

Two-item upstream report against an account with no service-discovery catalog AND no IaC repo supplied. Dimension 4 (Dependency footprint) scores ⚪ and owners resolve to `unknown`. The lifecycle change lands in 🟡 Coordinated (⚪ on Dimension 4 is 🟡-equivalent for a non-delete). The delete lands in 🔴 Risky as `dependency-unknown`: a delete with unknown dependencies or blast radius is never 🟡.

## What's modelled

A fictional AWS account `987654321098` (`acme-staging`) in `us-east-1`. The upstream waste audit found 2 candidates totalling $232/mo: an unattached gp3 EBS volume `vol-0bbbb1` ($52/mo) and a missing S3 lifecycle rule on `logs-archive-bucket` ($180/mo). There is no `.culiops/service-discovery/` directory, and at GATE 1 the operator supplies **no IaC repo** ("none - ownership from tags only"). So the ownership grep cannot run (owner `unknown`) and Dimension 4 has nothing to scan (⚪).

## What this fixture exercises

- **No catalog + no IaC repo.** Header shows `IaC repo(s): none - ownership from tags only`; owner `unknown` per item; Dimension 4 ⚪.
- **Tier rules: ⚪ on Dim 4 splits by action.** Non-delete (lifecycle) → 🟡-equivalent → 🟡 Coordinated. Delete (EBS volume) → tier rule 3 last clause → 🔴 `dependency-unknown`. The plan is produced, conservatively placed.
- **All 10 verification queries succeed**, Evidence 🟢 for both items from real signals: attach/detach history (management events, valid for EBS) and Storage Class Analysis (0 GETs on aged objects) with the lifecycle cost-direction row.
- **Snapshot-validity rule:** the snapshot (2026-05-08) is completed and taken after the volume's last detach, so Reversibility is 🟡. It is DLM-managed, which the plan flags as a retention caveat.
- **Evidence-gated delete:** Evidence is 🟢, so tier rule 3's "delete AND Evidence not 🟢" clause does not fire; the 🔴 comes from the `dependency-unknown` clause.
- **Docs row:** the Glacier Flexible Reversibility claim (reads fail until restore) is confirmed by a documentation read (row `d1`) before Reversibility 🟡 relies on it (Constraint 16). Pricing-API fallback rates name the query, region and date.
- **Honest scope of the lesson:** neither item would be 🟢 even with a catalog, because Reversibility is 🟡 for both (a Glacier Flexible `Transition` and an `unknown` owner; a delete with a snapshot). With a catalog or IaC repo the delete could move from 🔴 to 🟡. The Gaps and Next steps say so, instead of promising a Fast win.

## Files in this fixture

Row = the `#` in the plan's "Verification queries run" table.

| File | Row | Purpose |
|------|-----|---------|
| `operator-question.md` | - | freeform operator request |
| `upstream-report.md` | - | synthetic waste report (skill input) |
| `mock-responses/sts-get-caller-identity.json` | 0a | target check (account 987654321098) |
| `mock-responses/describe-volumes-vol-0bbbb1.json` | 0b-1 | volume state + tags (owner unknown) |
| `mock-responses/get-bucket-tagging-logs-archive-bucket.json` | 0b-2 | bucket tags (owner unknown) |
| `mock-responses/describe-snapshots-vol-0bbbb1.json` | 1 | one valid, DLM-managed snapshot |
| `mock-responses/lookup-events-ebs-vol-0bbbb1.json` | 2 | no attach/detach in 90d (management events) |
| `mock-responses/rbin-list-rules-ebs-snapshot.json` | 3 | no Recycle Bin rule for EBS snapshots (volume rules not queried) |
| `mock-responses/get-bucket-lifecycle-config-logs-archive-bucket.json` | 4 | `NoSuchLifecycleConfiguration` |
| `mock-responses/get-bucket-versioning-logs-archive-bucket.json` | 5 | never versioned |
| `mock-responses/list-bucket-intelligent-tiering-logs-archive-bucket.json` | 6 | none |
| `mock-responses/get-metric-data-bucket-size-logs-archive-bucket-90d.json` | 7 | 3.61 TiB, 661,000 objects |
| `mock-responses/storage-class-analysis-logs-archive-bucket.json` | 8 | SCA: 0 GETs on aged objects |
| `mock-responses/s3-inventory-size-distribution-logs-archive-bucket.json` | 9 | object-size distribution |
| `mock-responses/bill-derived-rates-logs-archive-bucket.json` | 10 | bill-derived / fallback rates (fictional) |
| `expected-output.md` | - | the plan the skill produces at GATE 3 |
| `DRY-RUN-NOTES.md` | - | gate transitions and acceptance check |

## Expected tier outcomes

| # | Item | Upstream priority | Tier | Dominant dimension |
|---|------|-------------------|------|--------------------|
| 1 | Delete unattached EBS volume vol-0bbbb1 | 1 ($52) | 🔴 Risky (`dependency-unknown`) | Dependency ⚪ on a delete (Reversibility 🟡 valid snapshot does not offset it) |
| 2 | Add lifecycle rule 90d → Glacier Flexible on logs-archive-bucket | 2 ($180) | 🟡 Coordinated | Reversibility 🟡 (Glacier Flexible `Transition`, owner unknown) + Dependency ⚪ → 🟡-equivalent (non-delete) |
