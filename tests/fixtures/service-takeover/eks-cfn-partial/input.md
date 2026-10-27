# Fixture: eks-cfn-partial

## Scenario

An EKS-hosted service, `search-api` (Deployment in namespace `search` on cluster `platform-eks`, account 123456789012, region eu-west-1). The data layer is owned by CloudFormation (`search-data-stack`, `search-iam-stack`); the app is deployed with Helm. No cost-allocation tag exists, so runtime-trace scopes by the catalog's resource set and spend is "account context". The Search Team hands off to the Platform Team on 2026-06-22.

## Operator inputs

- Service `search-api`; account 123456789012; region eu-west-1; Kubernetes context `platform-eks`, namespace `search`; delivery model: a GitHub Actions pipeline runs `helm upgrade --install`; intent `takeover`; handoff 2026-06-22
- Materials: 1 architecture PNG; no IaC repo supplied (Helm chart and CFN templates exist in git); kube context `platform-eks` read-only
- Outgoing: Search Team (Lena M., lena@example.com); incoming: Platform Team

## Expected behavior

- One discovery delegation (real-discovery: diagram + AWS + Kubernetes). The catalog records **Owner** per row: 5 rows `cloudformation (<stack>)`, 3 `helm search-api`, 2 controller/agent-owned. CloudFormation ownership is recognised and recorded; the takeover proceeds.
- runtime-trace: no tag, so the Spend section says **"Account context — NOT attributable to this service"**; **"EKS in-cluster workloads not traced"** appears in the Activity Baselines section and Gaps.
- Interview Section 4b (IaC & ownership) is answered: Helm repo, CFN stacks, RBAC, IRSA role.
- Scorecard: no `✗` or `✗ conflict`; three `?` (items 7, 8, 9: the in-cluster Deployment has no baseline, no deploy history and no audit-log query, because Helm rollouts are not CloudTrail events and `runtime-trace` does not trace in-cluster workloads); 10 `◐` (item 21 is `◐`, not `N/A`: no vendor register is cited); verdict **partial** (9 ✓ verified, 3 ✓ attested, 10 ◐, 0 ✗, 0 ✗ conflict, 3 ?, 0 N/A).
