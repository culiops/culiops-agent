# happy-path — cost-optimize-plan fixture

Positive-path fixture exercising a 3-item `cloud-cost-investigate` waste report with all playbooks present, every verification query succeeding, and the full 🟢 / 🟡 / 🔴 tier mix: one Fast win (lifecycle to Standard-IA), one Coordinated (EC2 rightsize), one Risky (EBS delete).

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`) in `ap-southeast-1`. The upstream waste audit found 3 candidates totalling $428/mo: an EC2 rightsize from Compute Optimizer ($280/mo), a missing S3 lifecycle rule on a 4.2 TiB bucket ($100/mo), and an unattached 200 GB gp3 volume ($48/mo).

**IaC repo: simulated.** The operator supplies `~/acme-infra` at GATE 1, but no real IaC tree exists in this fixture. `mock-responses/iac-grep-simulated.json` stands in for the grep results; the `code:<path:line>` refs in `expected-output.md` are illustrative.

## The operator question

> "Triage the cost report at .culiops/cloud-cost-investigate/acme-prod-waste-20260528-0915.md and build me an execution plan."

(See `operator-question.md`.)

## What this fixture exercises

- **Target check + ownership probe (Query 0).** `0a` verifies account = report `Scope`; `0b-<item>` resolves owners: EC2 and S3 → `terraform` (code refs), EBS volume → `unmanaged` (no IaC match, no controller tag).
- **Required vs optional evidence rows.** The EC2 memory row is **required** because the target class has less RAM (32 vs 64 GiB); the CloudWatch agent is installed (mock supplied), so Evidence stays 🟢. Without a CWAgent mock this item would go 🔴 (`verification-incomplete`).
- **Hourly 30d metrics via `get-metric-data`.** Mock JSON is summarized (`_summary`) rather than 720 points per series.
- **`Realizable` column.** EC2: commitment coverage queried (0% SP/RI, on-demand). Lifecycle: cost-direction computed (net +$97/mo vs upstream $100/mo; bill-derived Standard rate, fixture Standard-IA rates).
- **Lifecycle to an instantly readable class is 🟢 Fast win.** `lifecycle-s3.md`: a `Transition` to Standard-IA is Reversibility 🟢 (reads keep working; only Glacier Flexible / Deep Archive is 🟡, `Expiration` 🔴). The access-pattern row is `optional` for IA (no restore problem; retrieval fees are in the cost-direction row). It is run anyway via Storage Class Analysis (115 days of history, 0 GETs on objects aged >= 90d) and passes, which Dimension 3 requires of any optional row that ran. Object-size distribution from S3 Inventory (nothing under the 128 KiB IA minimum).
- **EBS snapshot validity.** The only snapshot predates the detach and is older than the 90d CloudTrail window, so it is not provably valid; Reversibility 🔴 and the item is 🔴 Risky. Evidence is 🟢, so tier rule 3's "delete AND Evidence not 🟢" clause is not what fires.
- **Drift section** (code = live for the two IaC-owned items) and **evidence refs** (`live:<n>`, `code:<path:line>`).
- **Ordering hint:** fresh final snapshot before the delete (#3).
- **All queries succeed:** Gaps has no blocking entries.

## Files in this fixture

Row = the `#` in the plan's "Verification queries run" table.

| File | Row | Purpose |
|------|-----|---------|
| `operator-question.md` | — | The freeform operator request |
| `upstream-report.md` | — | Synthetic `cloud-cost-investigate` waste report (skill input) |
| `mock-responses/sts-get-caller-identity.json` | 0a | Target check: account 123456789012 |
| `mock-responses/iac-grep-simulated.json` | 0b-1, 0b-2, 0b-3, Dim 4 | Simulated IaC grep (illustrative `code:` refs) |
| `mock-responses/describe-instances-i-0a1b2c3d4e5f67890.json` | 0b-1 | EC2 metadata + tags (no ASG / k8s tags) |
| `mock-responses/get-bucket-tagging-logs-bucket-app.json` | 0b-2 | Bucket tags |
| `mock-responses/describe-volumes-vol-0xxxxxxxxxxxxxxx1.json` | 0b-3 | Volume state + tags (available, no k8s tags) |
| `mock-responses/describe-instance-types-m5-4xlarge-m5-2xlarge.json` | 1 | Current vs target class (RAM halves) |
| `mock-responses/get-metric-data-i-0a1b2c3d4e5f67890-30d-hourly.json` | 2 | CPU / network, 30d hourly (summarized) |
| `mock-responses/list-metrics-cwagent-mem-i-0a1b2c3d4e5f67890.json` | 3 | CWAgent dimension discovery |
| `mock-responses/get-metric-data-cwagent-mem-i-0a1b2c3d4e5f67890-30d-hourly.json` | 3 | `mem_used_percent`, 30d hourly (summarized) |
| `mock-responses/co-rec-i-0a1b2c3d4e5f67890.json` | 4 | Compute Optimizer recommendation (14d lookback) |
| `mock-responses/describe-target-groups-vpc-0abc123def456789a.json` | 5 | Target groups in the instance's VPC |
| `mock-responses/describe-target-health-prod-api-tg.json` | 5 | 2 healthy targets |
| `mock-responses/describe-alarms-state-alarm-i-0a1b2c3d4e5f67890.json` | 6 | No alarms in ALARM |
| `mock-responses/get-savings-plans-coverage-i-0a1b2c3d4e5f67890.json` | 7 | 0% SP coverage |
| `mock-responses/get-reservation-coverage-i-0a1b2c3d4e5f67890.json` | 7 | 0 reserved hours |
| `mock-responses/get-bucket-lifecycle-config-logs-bucket-app.json` | 8 | `NoSuchLifecycleConfiguration` |
| `mock-responses/get-bucket-versioning-logs-bucket-app.json` | 9 | Versioning never enabled |
| `mock-responses/list-bucket-intelligent-tiering-logs-bucket-app.json` | 10 | No Intelligent-Tiering |
| `mock-responses/get-metric-data-bucket-size-logs-bucket-app-90d.json` | 11 | Size / object count (daily metrics) |
| `mock-responses/list-bucket-analytics-configurations-logs-bucket-app.json` | 12 | Storage Class Analysis config |
| `mock-responses/storage-class-analysis-export-logs-bucket-app.json` | 12 | SCA export summary: 0 GETs on aged objects (optional row for IA) |
| `mock-responses/s3-inventory-size-distribution-logs-bucket-app.json` | 13 | Object-size distribution |
| `mock-responses/bill-derived-rates-logs-bucket-app.json` | 14 | Bill-derived Standard rate + fixture Standard-IA rates (fictional) |
| `mock-responses/describe-snapshots-vol-0xxxxxxxxxxxxxxx1.json` | 15 | One snapshot, predates the detach |
| `mock-responses/lookup-events-ebs-90d.json` | 16 | Attach/Detach (management events): none in 90d |
| `mock-responses/rbin-list-rules-ebs-snapshot.json` | 17 | No Recycle Bin rule |
| `expected-output.md` | — | The plan the skill produces at GATE 3 |
| `DRY-RUN-NOTES.md` | — | Gate transitions and acceptance check |

## Expected tier outcomes

| # | Item | Upstream priority | Tier | Dominant dimension |
|---|------|-------------------|------|--------------------|
| 1 | Rightsize prod-api m5.4xlarge → m5.2xlarge | 1 ($280) | 🟡 Coordinated | Blast 🟡 (ALB target, no catalog) + Dependency 🟡 (1 IaC consumer) |
| 2 | Add lifecycle rule Standard → Standard-IA at 90d on logs-bucket-app | 2 ($100) | 🟢 Fast win | All four 🟢 (transition to an instantly readable class, terraform owner with code found)
| 3 | Delete vol-0xxxxxxxxxxxxxxx1 unattached EBS | 3 ($48) | 🔴 Risky | Reversibility 🔴 (no provably valid snapshot) |
