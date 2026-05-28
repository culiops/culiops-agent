# happy-path — cost-optimize-plan fixture

Positive-path fixture exercising a 3-item `cloud-cost-investigate` waste report with all playbooks present, all verification queries succeeding, and the full 🟢 / 🟡 / 🔴 tier mix produced.

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`) in `ap-southeast-1`. The upstream `cloud-cost-investigate` waste audit found 3 remediation candidates totalling $528/mo: an unattached gp3 EBS volume ($48/mo), an EC2 rightsize recommendation from Compute Optimizer ($280/mo), and a missing S3 lifecycle policy on a 4.2 TB storage bucket ($200/mo). All three items have matching v1 playbooks. All 11 verification queries succeed. The skill produces a plan with one item in each of the three actionable tiers — 🟢 Fast win (lifecycle), 🟡 Coordinated (rightsize), 🔴 Risky (delete EBS) — with no 🚫 or ❔ sections needed.

## The operator question

> "Triage the cost report at .culiops/cloud-cost-investigate/acme-prod-waste-20260528-0915.md and build me an execution plan."

(See `operator-question.md`.)

## What this fixture exercises

- **Load + parse of `cloud-cost-investigate` waste-mode report:** reads `upstream-report.md`, extracts 3-item Remediation list, detects `**Cloud:** aws`, applies $5/mo floor (all 3 items pass).
- **Single-batch verification (~11 queries total across 3 items, dedupe applied):** EBS (describe-volumes, describe-snapshots, cloudtrail-lookup), EC2 (describe-instances, cloudwatch-cpu, cloudwatch-network, compute-optimizer-rec, describe-target-health), S3 (get-lifecycle, list-intelligent-tiering, cloudwatch-bucket-size).
- **Four-dimension scoring producing 🟢 / 🟡 / 🔴 tier mix:** lifecycle policy lands 🟢 (all four 🟢), rightsize lands 🟡 (blast 🟡 + dependency 🟡), EBS delete lands 🔴 (reversibility 🔴 dominates).
- **Ordering hint: snapshot-before-delete on item #3** (EBS playbook recommends snapshot first; emitted as a callout in 🔴 section).
- **All queries succeed (positive path):** Gaps section says "None."

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | The freeform operator request to feed the skill |
| `upstream-report.md` | Synthetic `cloud-cost-investigate` waste report — skill input |
| `mock-responses/describe-volumes-vol-0xxxxxxxxxxxxxxx1.json` | EBS volume state (available, 200 GB gp3) |
| `mock-responses/describe-snapshots-vol-0xxxxxxxxxxxxxxx1.json` | Most-recent snapshot exists (weekly-backup, 2026-05-13) |
| `mock-responses/lookup-events-ebs-90d.json` | CloudTrail: 0 attach/detach events in 90d |
| `mock-responses/describe-instances-i-0a1b2c3d4e5f67890.json` | EC2 instance metadata (m5.4xlarge, running) |
| `mock-responses/cpu-stats-i-0a1b2c3d4e5f67890.json` | CloudWatch: 14d CPU avg ~4%, max ~12% |
| `mock-responses/network-stats-i-0a1b2c3d4e5f67890.json` | CloudWatch: 14d NetworkIn sum <100 MB/day |
| `mock-responses/co-rec-i-0a1b2c3d4e5f67890.json` | Compute Optimizer: m5.4xlarge → m5.2xlarge recommendation |
| `mock-responses/describe-target-health-prod-api-tg.json` | ALB target group: 2 healthy targets (redundancy present) |
| `mock-responses/get-bucket-lifecycle-config-logs-bucket-app.json` | S3: NoSuchLifecycleConfiguration (no existing policy) |
| `mock-responses/list-bucket-intelligent-tiering-logs-bucket-app.json` | S3: no Intelligent-Tiering configs present |
| `mock-responses/bucket-size-bytes-logs-bucket-app.json` | CloudWatch: StandardStorage ~4.2 TB |
| `expected-output.md` | The plan markdown the skill produces at GATE 3 |
| `DRY-RUN-NOTES.md` | Gate transitions and acceptance check |

## Expected tier outcomes

| # | Item | Upstream priority | cost-optimize-plan tier | Dominant dimension |
|---|------|-------------------|------------------------|--------------------|
| 1 | Rightsize prod-api m5.4xlarge → m5.2xlarge | 1 (highest savings) | 🟡 Coordinated | Blast 🟡 (ALB target) + Dependency 🟡 (1 consumer) |
| 2 | Add lifecycle policy on logs-bucket-app (90d→Glacier) | 2 | 🟢 Fast win | All four 🟢 |
| 3 | Delete vol-0xxxxxxxxxxxxxxx1 unattached EBS | 3 | 🔴 Risky | Reversibility 🔴 (irreversible delete) |
