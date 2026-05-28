---
cloud: aws
action: delete
resource_type: elastic-ip
applies_when: action == "delete" AND resource matches "eipalloc-*"
---

# Verify: Delete idle Elastic IP

## Required IAM
- `ec2:DescribeAddresses`
- `elasticloadbalancing:DescribeLoadBalancers`
- `route53:ListHostedZones`
- `route53:ListResourceRecordSets`

## Queries

1. `aws ec2 describe-addresses --public-ips <ip>` — confirms `AssociationId` is null/absent (unassociated).
2. `aws elbv2 describe-load-balancers --query 'LoadBalancers[?contains(AvailabilityZones[].LoadBalancerAddresses[].IpAddress, `<ip>`)]'` — sweeps NLBs for a static IP reference.
3. `aws route53 list-hosted-zones --query 'HostedZones[].Id'` — retrieves all hosted zone IDs for the DNS sweep.
4. Per zone: `aws route53 list-resource-record-sets --hosted-zone-id <zone-id> --query 'ResourceRecordSets[?Type==`A` && contains(ResourceRecords[].Value, `<ip>`)]'` — checks for DNS A records pointing at the IP.

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|------------|
| `Addresses[0].AssociationId` | absent | present |
| Route53 A records pointing at IP | 0 across all zones | ≥ 1 |
| NLB static IP references | none | any |
| `Addresses[0].NetworkInterfaceId` | absent | present (ENI association) |

## Reversibility classification
- **Default:** 🟡 partially reversible. Releasing the IP frees it back to the AWS pool; re-allocation returns a **different** IP. External allowlists and hardcoded DNS entries referencing the original IP would require updating.

## Blast radius classification
- **Default:** 🟡 — the IP is a shared namespace resource. Partner firewall allowlists, external DNS records, or application configs that hardcode the IP will break on release.

## Rollback note (informational, shown in plan)
"Releasing an Elastic IP is irreversible in identity — re-allocation produces a new IP. If any external system (partner firewall, DNS, allowlist) referenced the released IP, those references must be updated to point at the newly-allocated IP. Confirm zero DNS A records and zero NLB references before proceeding."
