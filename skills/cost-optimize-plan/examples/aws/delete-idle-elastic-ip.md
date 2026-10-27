---
cloud: aws
action: delete
resource_type: elastic-ip
applies_when: action == "delete" AND resource matches "eipalloc-*"
---

# Verify: Delete idle Elastic IP

An Elastic IP has **no activity metric**: nothing measures traffic "through" an EIP. There is no Dimension 3 activity signal. Idleness here is a *state* (unassociated, for how long); association, ENI, NLB, NAT and DNS are **attachment**. An unassociated EIP with no references is an idle-ambiguous delete: only the owner can confirm no external party has the address allowlisted, so it lands in 🔵. An associated EIP is not idle — it is billed as an in-use public IPv4 and is out of this playbook.

## Required IAM
- `ec2:DescribeAddresses`
- `ec2:DescribeNatGateways`
- `elasticloadbalancing:DescribeLoadBalancers`
- `route53:ListHostedZones`
- `route53:ListResourceRecordSets`
- `cloudtrail:LookupEvents` (optional, idle duration)

## Queries

0. **Target check + ownership probe** (`examples/aws.md`). Tags come from Query 1. Grep the IaC repo for the allocation ID, the public IP and `aws_eip` blocks (cite `code:<path:line>`). Controller or ASG tags per the ownership table → ❔ `owned-by-<owner>`.
1. `aws ec2 describe-addresses --allocation-ids <eipalloc-id>` — match key is the `eipalloc-*` ID, not the IP. Record `PublicIp`, `Domain`, `PublicIpv4Pool` (anything other than `amazon` = BYOIP / customer-owned pool → ❔, verify semantics), `Tags`, and whether `AssociationId`, `InstanceId`, `NetworkInterfaceId` are present.
   - Any of them present → **associated → not idle**: ❔ `not-idle`, stop on this item.
2. NLB static-IP references: `aws elbv2 describe-load-balancers --query 'LoadBalancers[?AvailabilityZones[?LoadBalancerAddresses[?AllocationId==`<eipalloc-id>`]]].LoadBalancerArn'` (per region). NAT Gateway use: `aws ec2 describe-nat-gateways --filter Name=nat-gateway-address.allocation-id,Values=<eipalloc-id>` (verify filter name).
3. `aws route53 list-hosted-zones` (public and private), then per zone list ALL records (paginate: `aws route53 list-resource-record-sets --hosted-zone-id <zone-id>`) and match client-side `Type == A` records whose `ResourceRecords[].Value` equals the `PublicIp`. No server-side contains filter exists.
4. (Optional) idle duration: `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<eipalloc-id> --start-time <now-90d>` — last `DisassociateAddress` / first `AllocateAddress` (free, management events, 90 days max; verify that these events record the allocation ID as a resource, otherwise ⚪). No events in 90d while currently unassociated ⇒ unassociated for the whole 90d.
5. External DNS and third-party allowlists (partner firewalls, SaaS IP allowlists, hardcoded configs) **cannot be swept by this skill.** Record a Gap; ask the owner. An `operator-stated` "no external allowlist" is recorded, citing who said so, but it does not clear the idle-ambiguous route: only the owner's answer to the dev-note does (Law 3).

## Evidence thresholds

| Signal | Req | 🟢 Threshold | 🚫 Trigger |
|--------|-----|--------------|------------|
| Unassociated: no `AssociationId`, `InstanceId`, `NetworkInterfaceId` (Query 1) | required | all absent | — (associated = not idle → ❔ `not-idle`, not a 🚫) |
| Unassociated for ≥ 60d (Query 4) | optional | no association event in the window | — |

There is no 🚫 trigger: no activity signal exists to observe.

## Attachment (Dimension 2 / 4 input)

| Signal | Query | Effect |
|--------|-------|--------|
| Route53 A record to the IP | 3 | ≥ 1 → Blast 🔴 (a record to an unassociated IP is already broken or stale — owner decides) |
| NLB static-IP / NAT Gateway reference | 2 | any → ❔ `not-idle` (association missed by Query 1) |
| IaC reference (`code:`) | 0 | 1–2 → Dependency 🟡; ≥ 3 → Dependency 🔴 |
| External allowlist / external DNS (unswept) | 5 | idle-ambiguous (an operator-stated "none" does not clear it) |

**Tier:** a delete of an unassociated EIP with Evidence 🟢 routes to **🔵 Requires owner confirmation** — public-IP release is irreversible in identity, and external allowlists cannot be enumerated (matches pre-flight's hard block on releasing a public IP with an unconfirmed external allowlist). Reversibility and Blast are still recorded.

## Reversibility classification
- **Default:** 🟡 — releasing returns the address to the AWS pool. `aws ec2 allocate-address --address <ip>` can attempt recovery, but only if no other account has taken it since (not guaranteed); otherwise re-allocation yields a **different** IP and every external reference must change.
- **🔴** if the owner states the IP is allowlisted externally or hardcoded in a system you cannot update.

## Blast radius classification
- **Default:** 🟡 — the IP is a shared-namespace resource: partner allowlists, external DNS, hardcoded configs.
- **Raised to 🔴:** per the Attachment table.

## Rollback note (informational, shown in plan)
"Releasing an Elastic IP is irreversible in identity. Recovery by address (`allocate-address --address`) works only while no one else has been allocated it; otherwise a new IP is issued and any external system that referenced the old one (partner firewall, DNS, allowlist) must be updated. Confirm zero DNS A records, zero NLB/NAT references and, with the owner, zero external allowlists before proceeding."
