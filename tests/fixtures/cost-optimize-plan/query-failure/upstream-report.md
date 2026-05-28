# Cloud Cost Investigation Report

**Generated:** 2026-05-28T12:00:00Z
**Skill:** cloud-cost-investigate v0.8
**Cloud:** aws
**Mode:** waste
**Scope:** 123456789012 (acme-prod)
**Region:** ap-southeast-1
**Report ID:** acme-prod-waste-mixed-20260528-1200

---

## Summary

| Metric | Value |
|--------|-------|
| Items found | 3 |
| Estimated monthly waste | $240 |
| High-confidence items | 2 |
| Medium-confidence items | 1 |

---

## Remediation List

| # | Action | Resource(s) | Est. savings | Source | Confidence | Evidence |
|---|--------|-------------|-------------|--------|------------|---------|
| 1 | Delete unattached EBS volume | vol-0cccc1 | $35/mo | line-item-computation | high | volume.state=available since 2026-03-10 |
| 2 | Delete S3 bucket bucket-logs-2019 | bucket-logs-2019 | $180/mo | line-item-computation | high | $180/mo unchanged 60+ days |
| 3 | Delete unused load balancer prod-old-lb | prod-old-lb | $25/mo | line-item-computation | medium | 0 RequestCount in 30d |

**Total estimated savings: $240/mo**

---

## Item Details

### Item 1 — Delete unattached EBS volume vol-0cccc1

- **Resource type:** EBS volume
- **Resource ID:** vol-0cccc1
- **Region:** ap-southeast-1a
- **Size:** 40 GiB (gp3)
- **State:** available (no attachments)
- **Detached since:** 2026-03-10
- **Monthly cost:** ~$35
- **Confidence:** high
- **Evidence:** volume.state=available; Attachments=[]; no instance association in billing for 79 days

### Item 2 — Delete S3 bucket bucket-logs-2019

- **Resource type:** S3 bucket
- **Resource ID:** bucket-logs-2019
- **Region:** ap-southeast-1
- **Bucket size:** ~1.8 TB (standard storage)
- **Monthly cost:** ~$180
- **Confidence:** high
- **Evidence:** cost line item flat at $180/mo for 60+ days; bucket name suggests 2019-era log archive; no versioning, no lifecycle rules observed

### Item 3 — Delete unused load balancer prod-old-lb

- **Resource type:** Application Load Balancer
- **Resource ID:** prod-old-lb
- **Region:** ap-southeast-1
- **Monthly cost:** ~$25
- **Confidence:** medium
- **Evidence:** CloudWatch RequestCount metric = 0 for past 30 days; no active target group health checks passing
