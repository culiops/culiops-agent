# missing-catalog — cost-optimize-plan fixture

Two-item upstream report against an account with no service-discovery catalog. Both items would normally be 🟢 Fast wins, but Dimension 4 (Dependency footprint) scores ⚪ because no catalog AND no IaC tree — items conservatively downgrade to 🟡 Coordinated per the tier rules' ⚪ disambiguation.

## What's modelled

A fictional AWS account `987654321098` (`acme-staging`) in `us-east-1`. The upstream `cloud-cost-investigate` waste audit found 2 remediation candidates totalling $232/mo: an unattached gp3 EBS volume `vol-0bbbb1` ($52/mo) and a missing S3 lifecycle policy on `logs-archive-bucket` ($180/mo). The operator's account has **no `.culiops/service-discovery/` directory** — the service-discovery skill has never been run. No IaC tree is accessible in the working directory either. As a result, Dimension 4 (Dependency footprint) scores ⚪ for both items.

## What this fixture exercises

- **All verification queries succeed (6 queries across 2 items).** Evidence dimension scores 🟢 for both items — the queries themselves return good data.
- **Dimension 4 detects no catalog at the scoping step → scores ⚪ for both items.** No `.culiops/service-discovery/` directory exists and no IaC tree is present to grep.
- **Tier rules apply: ⚪ on Dim 4 → treated as 🟡-equivalent → items go to 🟡 Coordinated, NOT 🔴 Risky.** This is the ⚪ disambiguation: only Evidence-⚪ forces 🔴; Dependency-⚪ treats as 🟡.
- **Plan shows both items in 🟡 with explicit dependency-unknown note in the Evidence/Dependency column.** Each item's dimension detail explains the ⚪ status and suggests running `service-discovery` first.
- **0 items in 🟢 Fast wins.** The absence of a catalog is enough to prevent 🟢 — you need all four dimensions to be 🟢 for a Fast win, and Dependency-⚪ is treated as 🟡.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | The freeform operator request to feed the skill |
| `upstream-report.md` | Synthetic `cloud-cost-investigate` waste report — skill input |
| `mock-responses/describe-volumes-vol-0bbbb1.json` | EBS volume state (available, 200 GB gp3, no attachments) |
| `mock-responses/describe-snapshots-vol-0bbbb1.json` | 1 snapshot from 2026-05-08 (20 days old — reversibility mitigated) |
| `mock-responses/lookup-events-ebs-vol-0bbbb1.json` | CloudTrail: 0 attach/detach events in 90d |
| `mock-responses/get-bucket-lifecycle-config-logs-archive-bucket.json` | S3: NoSuchLifecycleConfiguration |
| `mock-responses/list-bucket-intelligent-tiering-logs-archive-bucket.json` | S3: no Intelligent-Tiering configs present |
| `mock-responses/bucket-size-bytes-logs-archive-bucket.json` | CloudWatch: 3.6 TB StandardStorage (matches upstream claim) |
| `expected-output.md` | The plan markdown the skill produces at GATE 3 |
| `DRY-RUN-NOTES.md` | Gate transitions and acceptance check |

## Expected tier outcomes

| # | Item | Upstream priority | cost-optimize-plan tier | Dominant dimension |
|---|------|-------------------|------------------------|--------------------|
| 1 | Delete unattached EBS volume vol-0bbbb1 | 1 | 🟡 Coordinated | Dependency ⚪ (no catalog, no IaC tree) → 🟡-equivalent |
| 2 | Add lifecycle policy 90d→Glacier on logs-archive-bucket | 2 | 🟡 Coordinated | Dependency ⚪ (no catalog, no IaC tree) → 🟡-equivalent |
