# waste-aws-account — cloud-cost-investigate fixture

Waste-mode fixture exercising a full account audit including Compute Optimizer rightsizing, unattached EBS volumes, orphaned snapshots, and untagged spend.

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`) with ~$12K/mo of identifiable waste and $8K/mo of spend with no `Service` tag. Compute Optimizer has been running for 14+ days and has surfaced 3 EC2 rightsizing recommendations and 1 EBS volume rightsizing recommendation.

## The operator question

> "Run a waste audit on our AWS prod account. What can we delete or rightsize?"

(See `operator-question.md`.)

## What this fixture exercises

- **Mode detection from question phrasing:** "waste audit / delete or rightsize" → waste mode (suggested at GATE 1).
- **Compute Optimizer + resource-state sweeps in one batch:** CO EC2, CO EBS, `describe-volumes`, `describe-snapshots`, and CE untagged-spend all run in a single GATE 2 batch.
- **Deduplication:** `vol-0xxxx1234abcd5678` appears in both `compute-optimizer.json` (as an EBS rightsizing candidate) and `unattached-volumes.json` (as an unattached volume). The skill must dedup and emit one row labelled `compute-optimizer` (preferred source per spec) rather than two rows.
- **Dollar-threshold filtering:** candidates below $5/mo are dropped from the remediation list.
- **Source/confidence labelling:** each remediation item carries a `source` (`compute-optimizer` | `line-item-computation`) and `confidence` (`high` | `medium` | `low`) label.
- **Untagged spend flagged separately:** the CE untagged-spend finding is reported as an informational flag (`untagged-spend-flag`), not as a waste item. No savings figure is claimed.
- **Drill-down at GATE 3:** utilization metrics for the 3 CO-flagged EC2 instances are fetched in a separate batch to confirm the rightsizing signal. All 3 show <5% avg CPU over 14d — recommendations are confirmed.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | The freeform cost question to feed the skill |
| `compute-optimizer.json` | Synthetic CO EC2 + EBS recommendations |
| `unattached-volumes.json` | Synthetic `aws ec2 describe-volumes` output (12 unattached gp3 volumes) |
| `orphaned-snapshots.json` | Synthetic `aws ec2 describe-snapshots` output (47 snapshots >30d old) |
| `untagged-spend.json` | Synthetic `aws ce get-cost-and-usage` output (by tag absence) |
| `utilization-metrics.json` | Synthetic CloudWatch CPU metrics for 3 CO-flagged instances |
| `DRY-RUN-NOTES.md` | Expected skill behaviour at each step |

## Savings summary (expected output)

| Finding | Source | Confidence | Est. savings |
|---------|--------|------------|-------------|
| Delete 11 unattached EBS volumes | line-item-computation | high | ~$420/mo |
| Rightsize 3 EC2 instances | compute-optimizer | medium | ~$490/mo |
| Resize 1 EBS volume (oversized) | compute-optimizer | medium | ~$48/mo |
| Delete 47 orphaned snapshots | line-item-computation | high | ~$320/mo |
| Tag $8K/mo of untagged spend | untagged-spend-flag | informational | n/a |

**Total:** ~$740/mo high-confidence, ~$538/mo medium-confidence.
