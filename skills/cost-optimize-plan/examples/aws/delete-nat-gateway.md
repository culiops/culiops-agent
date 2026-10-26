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
- `cloudwatch:GetMetricData`

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`). Apply the **Metrics rule** to every CloudWatch query below. `cloudformation` owner → ❔ `unsupported-owner`. `terraform`: record both the `aws_nat_gateway` and its `aws_eip` addresses (`code:<path:line>`). `unmanaged` → "re-apply old IaC" rollback is unavailable.
1. `aws ec2 describe-nat-gateways --nat-gateway-ids <nat-id>` — captures `State`, `VpcId`, `SubnetId`, `ConnectivityType` (`public` or `private`), `NatGatewayAddresses[].{AllocationId,PublicIp}`. **Precondition:** `State=available`. `pending` → re-check later; `deleting` / `deleted` / `failed` → resource is gone or broken, drop the item as stale. Success of this call is the "describe succeeded" precondition for treating empty metrics as zero.
2. `aws ec2 describe-route-tables --filters Name=route.nat-gateway-id,Values=<nat-id> --query 'RouteTables[].[RouteTableId,Associations[].[SubnetId,Main],Tags]'` — route tables sending traffic (`0.0.0.0/0` or specific CIDR) to this NAT. **Attachment.** A route table with `Main=true` covers every subnet in the VPC without an explicit association.
3. **Activity metrics (one call, 90d @ 3600s).** 90d × 24 = 2,160 datapoints per metric exceeds the 1,440 `get-metric-statistics` cap, so use `get-metric-data`; dimension `NatGatewayId` from Query 1:

   ```
   aws cloudwatch get-metric-data --start-time <now-90d> --end-time <now> --scan-by TimestampAscending --metric-data-queries '[
    {"Id":"out","MetricStat":{"Metric":{"Namespace":"AWS/NATGateway","MetricName":"BytesOutToDestination","Dimensions":[{"Name":"NatGatewayId","Value":"<nat-id>"}]},"Period":3600,"Stat":"Sum"}},
    {"Id":"in","MetricStat":{"Metric":{"Namespace":"AWS/NATGateway","MetricName":"BytesInFromDestination","Dimensions":[{"Name":"NatGatewayId","Value":"<nat-id>"}]},"Period":3600,"Stat":"Sum"}}]'
   ```

   `out` = egress bytes (**activity signal, Principle 1**); `in` = return-path bytes, pairs with `out` to confirm idle.
4. (Optional, opt-in at GATE 2) `aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=<vpc-id> --query 'VpcEndpoints[].[ServiceName,State]'` — surfaces existing VPC endpoints. **Informational for the ladder fallback** (see Rollback note).

> **Window (Principle 3):** delete reads 60–180d at hourly granularity (90d used here). Judge the temporal distribution: a single burst older than 30d with zero since is `historical-burst`, not active use.

## Evidence thresholds

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| 90d hourly `BytesOutToDestination` (Sum) | required | every hour < 1 MB (noise floor), or only a `historical-burst` | ≥ 1 MB in any hour of the last 30d, or a recurring pattern — active egress |
| 90d hourly `BytesInFromDestination` (Sum) | required | every hour < 1 MB, or only a `historical-burst` | ≥ 1 MB in any hour of the last 30d, or a recurring pattern — active return traffic |

A `required` row that is ⚪ (failed query, or empty with a failed Target check / describe) forces Evidence ⚪ → 🔴.

## Attachment (Dimension 2 / 4 input)

Route-table attachment is **blast radius**, not evidence of use (Principle 1). A NAT routed-to by 5 subnets is still idle if nothing behind them makes egress. These rows never produce 🚫.

| Signal | Query | Effect |
|--------|-------|--------|
| Route tables routing through this NAT | 2 | `0` (orphaned) → Blast 🟢; ≥ 1 non-production route table → Blast 🟡; **≥ 1 production route table** (or a `Main=true` association) without an operator-confirmed cutover plan → Blast 🔴 |
| Other NATs in the same VPC (AZ redundancy) | `describe-nat-gateways --filter Name=vpc-id,Values=<vpc-id>` | this is the last NAT in the VPC → Blast ≥ 🟡 |
| IaC references to the NAT / its route resources (Dim 4 grep) | `code:` | per Dimension 4 thresholds |

## Reversibility classification
- **Default:** 🔴 irreversible. Recreating a NAT gives a new ID, and a new Elastic IP unless the old allocation is reused. Allow-listed downstream firewalls (partner integrations, SaaS IP allowlists) break if the IP changes.
- **Mitigated → 🟡:** the NAT is `public`, its EIP allocation (`NatGatewayAddresses[].AllocationId`) stays allocated to the account (not released), and the NAT is recreated with `--allocation-id` (~5 min, same public IP). The retained EIP is billed as an idle public IPv4 (rate: bill-derived or Pricing API) — subtract it from the saving.

## Blast radius classification
- **Default:** 🟡 — at least one route table routes egress through this NAT. See the Attachment table for 🟢 / 🔴 bumps. Also 🔴 if ≥ 2 production VPCs depend on it or the NAT serves a shared-services VPC per catalog.

## Rollback note (informational, shown in plan)
"NAT Gateway recreation takes ~5 min. **Deleting a NAT gateway disassociates its Elastic IP but does not release it** — the EIP stays allocated (and billed as an idle public IPv4) until released separately, either manually or by IaC (a Terraform `aws_eip` outside the destroyed block is untouched; one removed together with the NAT is released and the IP is lost). To keep the IP for rollback, leave the EIP allocated and recreate with `--allocation-id`. If the EIP is released, recreation assigns a new IP and any downstream firewall allow-listing the old one must be updated first.

**Principle 2 ladder fallback:** if delete is blocked by blast radius (active egress on critical routes), check whether traffic is dominated by AWS-service destinations (S3, DynamoDB, ECR, Secrets Manager) — those can route through VPC Gateway / Interface Endpoints at a fraction of the NAT data-processing charge, without removing the NAT. Compute the % of `BytesOutToDestination` going to AWS service IP ranges (VPC flow logs, if enabled) before proposing this fallback; price the saving from the bill-derived NAT data-processing rate (Principle 4), not list price."
