# anomaly-aws-bill-spike — cloud-cost-investigate fixture

Anomaly-mode fixture exercising a bill spike caused by an undocumented compute fleet.

## What's modelled

A fictional AWS account `123456789012` (`acme-prod`) where last-month spend was ~$52K and this-month-to-date is tracking to ~$74K. The cause modeled: 8 `p3.8xlarge` instances launched 12 days ago in `us-east-1` by an ML team, untagged.

## The operator question

> "Our AWS bill spiked from $52K last month to $74K this month — find out why."

(See `operator-question.md`.)

## What this fixture exercises

- **Mode detection from question phrasing:** "spiked / why" → anomaly mode (suggested at GATE 1).
- **Single-account default scope:** investigation runs against `123456789012` only — no org-wide escalation.
- **Time-range default for anomaly mode:** last 30d vs. previous 30d.
- **No catalog available:** `.culiops/service-discovery/` is empty; skill proceeds without a catalog (anomaly mode allows this).
- **Cost-by-service decomposition:** synthetic billing data shows EC2 as the top-delta service (+$22K).
- **Drill-down to usage type:** within EC2, `BoxUsage:p3.8xlarge` accounts for ~$20K of the +$22K.
- **New-resource discovery:** synthetic `describe-instances` output surfaces 8 `p3.8xlarge` instances launched 12 days ago, all untagged.
- **Driver attribution with evidence:** report names the driver (ML compute fleet) with evidence (instance IDs, launch times, untagged).
- **Cost Explorer per-call charge surfacing:** query plan shows estimated $0.04 (4 calls × $0.01).
- **Remediation list:** suggests "tag the 8 untagged p3.8xlarge instances with Service / Owner" (informational, not waste — these may be needed); does NOT recommend deletion.

## Files in this fixture

| File | Purpose |
|------|---------|
| `operator-question.md` | The freeform cost question to feed the skill |
| `billing-data.json` | Synthetic `aws ce get-cost-and-usage` output for last 30d daily-by-service |
| `new-resources.json` | Synthetic `aws ec2 describe-instances` output filtered to the anomalous window |
| `DRY-RUN-NOTES.md` | Expected skill behaviour at each step |
