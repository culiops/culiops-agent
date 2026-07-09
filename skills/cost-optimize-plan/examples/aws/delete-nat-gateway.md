---
cloud: aws
action: delete
resource_type: nat-gateway
applies_when: action == "delete" AND resource matches "nat-*"
---

# Verify: Delete NAT Gateway

## Required IAM
- `ec2:DescribeNatGateways`
- `ec2:DescribeRouteTables`
- `ec2:DescribeVpcEndpoints`
- `cloudwatch:GetMetricStatistics`

## Queries

1. `aws ec2 describe-nat-gateways --nat-gateway-ids <nat-id>` — confirms `State=available` and captures `VpcId`, `SubnetId`, `NatGatewayAddresses`.
2. `aws ec2 describe-route-tables --filters Name=route.nat-gateway-id,Values=<nat-id> --query 'RouteTables[].[RouteTableId,Associations]'` — lists route tables routing `0.0.0.0/0` (or specific CIDR) to this NAT. Blast-radius input — count of dependent subnets.
3. `aws cloudwatch get-metric-statistics --namespace AWS/NATGateway --metric-name BytesOutToDestination --dimensions Name=NatGatewayId,Value=<nat-id> --start-time <now-90d> --end-time <now> --period 86400 --statistics Sum` — 90d egress bytes. **Activity signal, Principle 1.**
4. `aws cloudwatch get-metric-statistics --namespace AWS/NATGateway --metric-name BytesInFromDestination --dimensions Name=NatGatewayId,Value=<nat-id> --start-time <now-90d> --end-time <now> --period 86400 --statistics Sum` — 90d return-path bytes. Pairs with BytesOut to confirm idle.
5. (Optional, opt-in at GATE 2) `aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc-id> --query 'VpcEndpoints[].[ServiceName,State]'` — surfaces existing VPC endpoints. **Informational for ladder fallback** (see Principle 2 note in Rollback).

## Evidence thresholds

| Signal | 🟢 Threshold | 🚫 Trigger |
|--------|--------------|------------|
| `NatGateways[0].State` | `available` | `pending`, `deleting`, `failed` |
| 90d `BytesOutToDestination` (Sum) | `0` bytes | ≥ 1 MB — active egress |
| 90d `BytesInFromDestination` (Sum) | `0` bytes | ≥ 1 MB — active return traffic |
| Route tables routing through this NAT | `0` (orphaned) OR documented as part of teardown | ≥ 1 production route table without operator-confirmed cutover plan — bump tier 🔴 |

**Principle 1 reminder:** route-table attachment is **blast radius**, not evidence of use. A NAT can be routed-to by 5 subnets and still be idle if no instance behind those subnets is making egress. Score Dimension 3 on bytes, not on route-table count.

## Reversibility classification
- **Default:** 🔴 irreversible. NAT Gateways receive a new Elastic IP on recreation unless the operator explicitly allocates and assigns a pre-existing EIP. Allow-listed downstream firewalls (partner integrations, SaaS IP allowlists) break.
- **Mitigated:** if the NAT's `NatGatewayAddresses[].AllocationId` is a customer-owned EIP that will be released and re-assigned to the replacement → 🟡 (rebuild ~5 min, same public IP).

## Blast radius classification
- **Default:** 🟡 — at least one route table routes egress through this NAT. Bump to 🟢 only if Query 2 returns zero route-table associations (already orphaned). Bump to 🔴 if ≥ 2 production VPCs depend on it or if the NAT serves a shared-services VPC per catalog.

## Rollback note (informational, shown in plan)
"NAT Gateway recreation takes ~5 min and assigns a new Elastic IP unless a pre-existing EIP is supplied via `--allocation-id`. Any downstream firewall allow-listing the old NAT IP must be updated before recreation, or recreate with the original EIP. **Principle 2 ladder fallback:** if delete is blocked by blast radius (active egress on critical routes), check whether traffic is dominated by AWS-service destinations (S3, DynamoDB, ECR, Secrets Manager) — those can route through VPC Gateway / Interface Endpoints at a fraction of NAT data-processing cost ($0.045/GB) without removing the NAT. Compute the % of `BytesOutToDestination` going to AWS service IP ranges before proposing this fallback."
