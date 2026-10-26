---
cloud: aws
action: rightsize
resource_type: eks-nodegroup
applies_when: action == "rightsize" AND resource matches "arn:aws:eks:*:nodegroup/*"
---

# Verify: Rightsize EKS managed nodegroup

Covers three rightsizing levers, which compose: (a) reduce `desiredSize` / `minSize` (scale down), (b) change `instanceTypes` (smaller class or AMD/Graviton swap), and (c) capacity-type swap `ON_DEMAND` → `SPOT` (reliability tradeoff, see Caveats). This playbook handles managed nodegroups itself; it is the one playbook where the nodegroup, not the instance, is the owner (EC2 playbooks send nodegroup members here via `owned-by-eks-nodegroup`).

## Required IAM
- `eks:DescribeNodegroup`
- `eks:ListNodegroups`
- `autoscaling:DescribeAutoScalingGroups`
- `ec2:DescribeInstances`
- `cloudwatch:GetMetricData`
- `cloudwatch:ListMetrics` (Container Insights / CWAgent dimension discovery)
- Cluster-side (Kubernetes RBAC; `kubectl` / API, read-only). A dedicated read-only ClusterRole is needed — `system:node-reader` is **not** a built-in ClusterRole, and the built-in `view` is namespaced and does not cover nodes. Required rules:
  - core API: `get`, `list` on `nodes`; `list` on `pods` **cluster-wide** (all namespaces); `list` on `poddisruptionbudgets` (policy API) and `horizontalpodautoscalers` (autoscaling API)
  - `metrics.k8s.io`: `get`, `list` on `nodes` and `pods` (for `kubectl top`; requires metrics-server)
  - `events` `list` (optional, for `FailedScheduling`)

## Queries

0. Run the shared **Target check** and **Ownership probe** (`../aws.md`) against the nodegroup. Apply the **Metrics rule** to every CloudWatch query below. Ownership of the nodegroup: `terraform` (cite `code:<path:line>` of the `aws_eks_node_group` / module) → proceed; `cloudformation` (including **eksctl**-created nodegroups, which are CFN stacks: `aws:cloudformation:stack-name` tag) → ❔ `unsupported-owner`; `unmanaged` → "re-apply old IaC" rollback unavailable. `karpenter`-managed capacity is not a managed nodegroup → ❔ `owned-by-karpenter`.
1. `aws eks describe-nodegroup --cluster-name <cluster> --nodegroup-name <ng>` — captures `instanceTypes[]`, `scalingConfig.{min,desired,max}Size`, `capacityType`, `amiType`, `launchTemplate`, `nodegroupArn`, `resources.autoScalingGroups[]`, `tags`.
2. `aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names <asg-name>` — current instances (for utilization queries) **and `Tags`**.
3. **Who owns `desiredSize`?** Two checks; either one means `desiredSize` is not a stable lever:
   - **Cluster Autoscaler:** ASG tags `k8s.io/cluster-autoscaler/enabled` and `k8s.io/cluster-autoscaler/<cluster>` (Query 2), and `kubectl -n kube-system get deploy cluster-autoscaler` (name/namespace vary). CA overrides `desiredSize`, so lever (a) must change `minSize` / `maxSize`, not `desiredSize`.
   - **Karpenter:** `kubectl get nodepools.karpenter.sh` (and nodes labelled `karpenter.sh/nodepool`). Karpenter provisions its own nodes outside managed nodegroups; a managed nodegroup commonly only hosts the Karpenter controller itself and should not be shrunk below what it needs.
   - **Terraform `ignore_changes`:** grep the nodegroup's resource block for `ignore_changes = [scaling_config[0].desired_size]` (cite `code:<path:line>`). If present, a `desired_size` edit in IaC is ignored; use min/max or `update-nodegroup-config`.
4. For each instance in Query 2: utilization via `get-metric-data` (30d @ 3600s = 720 points per query), `AWS/EC2` `CPUUtilization` with `Stat` `Average`, `Maximum`, **`p95`**; plus `NetworkIn` / `NetworkOut` (`Sum`). Percentiles require `Stat: "p95"` here (or `--extended-statistics` on `get-metric-statistics`, which cannot be combined with `--statistics`). Node-side activity signal. Caveat: only *current* members are queried, so nodes replaced during the 30d window are missing — prefer the Container Insights aggregate (Query 5) when available.
5. Memory (**required when reducing capacity**): CloudWatch agent `CWAgent` `mem_used_percent` per instance (discover exact dimensions first with `aws cloudwatch list-metrics --namespace CWAgent --metric-name mem_used_percent --dimensions Name=InstanceId,Value=<id>`; a query must match the dimension set exactly), OR Container Insights `node_memory_utilization`. Container Insights node metrics are published per cluster / node (dimensions such as `ClusterName`, `NodeName`, `InstanceId` — verify with `aws cloudwatch list-metrics --namespace ContainerInsights --metric-name node_cpu_utilization --dimensions Name=ClusterName,Value=<cluster>`); there is **no nodegroup dimension**, so aggregate over the nodegroup's instance IDs. Neither source present → ⚪ (do not assume).
6. Container Insights (if enabled) `node_cpu_utilization`, `node_memory_utilization`, `node_filesystem_utilization` for the nodegroup's nodes, 30d @ 3600s via `get-metric-data` (`Average`, `Maximum`, `p95`).
7. Cluster-side snapshot (point in time only — it is the scheduler's view, not 30d history): `kubectl top nodes -l eks.amazonaws.com/nodegroup=<ng>` (actual use) and `kubectl describe nodes -l eks.amazonaws.com/nodegroup=<ng>` — the **Allocated resources** section lists summed pod *requests* vs `Allocatable` per node.
8. 30d request : allocatable ratio and pending pods, from kube-state-metrics via the cluster's Prometheus (**examples — adapt label names to your setup; kube-state-metrics v2 exposes node labels only if allowlisted**):
   - requests vs allocatable per resource: `sum by (resource) (kube_pod_container_resource_requests{node=~"<nodes-of-ng>"})` vs `sum by (resource) (kube_node_status_allocatable{node=~"<nodes-of-ng>"})`
   - pending pods: `sum(kube_pod_status_phase{phase="Pending"})` and `sum(kube_pod_status_unschedulable)`, over 7d
   - no Prometheus: Container Insights `pod_status_pending` (**verify the metric name and dimensions** in your Container Insights version) and `kubectl get events -A --field-selector reason=FailedScheduling` (events are short-lived, ~1h — point-in-time only)
   - **Not** `cluster_failed_node_count` — that counts nodes in a failed state, not unschedulable pods.
9. `kubectl get pdb -A`, `kubectl get hpa -A` — PodDisruptionBudgets and HPAs touching workloads on this nodegroup (**attachment**, see below).

## Evidence thresholds

Thresholds are defaults. "Req" = required: ⚪ on a required row forces Evidence ⚪ → 🔴. Each row applies to a lever that reduces capacity (a, b).

| Signal | Req | 🟢 Threshold (safe to rightsize down) | 🚫 Trigger (do not rightsize down) |
|--------|-----|--------------------------------------|--------------------------------------|
| 30d hourly p95 node CPU utilization | required | ≤ 40% | ≥ 75% — at risk of CPU pressure post-scale-down |
| 30d hourly p95 node memory utilization (Query 5) | **required** | ≤ 50% | ≥ 75% |
| 30d p95 pod-request : node-allocatable (CPU) | required | ≤ 60% | ≥ 80% — scheduler will fail to place pods on smaller / fewer nodes |
| 30d p95 pod-request : node-allocatable (memory) | required | ≤ 70% | ≥ 80% |
| Pending / unschedulable pods (last 7d, Query 8) | required | `0` sustained | recurring — nodegroup is already capacity-constrained |
| 30d node network throughput | optional | well below the instance class's baseline | near the class limit |

**Principle 1 reminder:** `desiredSize` and pod count are **attachment** — they say "this many nodes are configured / pods are scheduled." Actual CPU / memory / network throughput is **activity**. A nodegroup with 10 nodes and 100 idle pods (sleeping `Deployment`s with low requests) is still over-provisioned. Score Dimension 3 on utilization, not on `desiredSize`.

**Keep-alive noise to subtract:** system daemonsets (kube-proxy, aws-node, coredns, fluent-bit, node-problem-detector) consume baseline CPU/memory on every node regardless of workload. Subtract their baseline before judging "workload activity" — measure it (e.g. `kubectl top pods -n kube-system` per node) rather than assuming a percentage. Container Insights `node_cpu_utilization` includes daemonset usage; isolate via `pod_cpu_utilization` aggregated by namespace if available.

## Attachment (Dimension 2 / 4 input)

| Signal | Query | Effect |
|--------|-------|--------|
| PDBs missing for workloads on the nodegroup | 9 | any workload without a PDB → Blast ≥ 🟡 (drain can cause an outage even at a correct size) |
| All workloads have PDBs AND ≥ 2 nodegroups in the cluster | 9 / catalog | eligible for Blast 🟢 |
| Active HPA/VPA on workloads in this nodegroup | 9 | autoscaler-driven resize composes with manual rightsize — check the HPA peak window (replicas at peak × requests must still fit) before finalizing the size; record, no 🚫 |
| Only nodegroup in the cluster, or stateful pods (StatefulSets) | `describe-nodegroup` / kubectl | Blast 🔴 |
| Cluster Autoscaler / Karpenter present, or `ignore_changes` on `desired_size` | 3 | not a score: changes the lever (min/max, not desired) and the rollback path |

## Caveats — capacity-type swap (`ON_DEMAND` → `SPOT`)

This is **not** a Principle 2 cost-direction problem in the usual sense (Spot is priced below On-Demand for the same type), but the discount varies by instance type, AZ and time — take it from the Spot price history / bill, never assume a percentage. It is a **reliability** tradeoff: Spot capacity can be reclaimed with a 2-minute notice. Score separately:

- Workloads tolerating ≤ 2-min interruption (stateless web, batch jobs with checkpointing, build/CI runners): `capacityType: SPOT` is acceptable — 🟢.
- Workloads requiring graceful termination > 2 min, or stateful pods without PDBs: **do not swap**. Spot interruptions cascade into outages. 🔴.
- Mixed nodegroups: split workloads by tolerance, run two nodegroups (`SPOT` + `ON_DEMAND`). Cost-optimize-plan emits this as two coordinated items in 🟡, not one item.

## Reversibility classification
- **Default:** 🟢 for `scalingConfig` changes (min/max size) when Ownership is `terraform` and no `ignore_changes` covers the field: re-apply old IaC, ASG scales back. If `desired_size` is in `ignore_changes` or CA/Karpenter manages it, IaC re-apply does **not** restore it — rollback is `aws eks update-nodegroup-config --scaling-config`. `unmanaged` → 🟡.
- **Default:** 🟡 for `instanceTypes` change: `UpdateNodegroupConfig` cannot change `instanceTypes` (it updates scaling config, labels, taints, update config), so this is a **replacement** — a new nodegroup (or a launch-template version rolled via `update-nodegroup-version`) with drain + replace; Terraform typically replaces the nodegroup (verify for your provider version). Old nodes are gone; re-apply old IaC starts another roll. ~15–45 min RTO depending on size. An architecture change (x86 ↔ arm64) additionally needs a different `amiType` and arm64 images for every workload.
- **Default:** 🟡 for `capacityType: SPOT` reversal: same as instance-type change (rolling replacement).

## Blast radius classification
- **Default:** 🟡 — touches a live nodegroup serving real pods. See the Attachment table for 🟢 / 🔴 bumps.

## Rollback note (informational, shown in plan)
"`scalingConfig` rollback: re-apply old IaC if it owns the field, otherwise `aws eks update-nodegroup-config --scaling-config`; the ASG resizes. `instanceTypes` or `capacityType` rollback: re-apply old IaC, nodegroup is replaced (drain + replace, ~15–45 min). **Pre-rightsize:** confirm PDBs exist for all workloads on this nodegroup (`kubectl get pdb -A -o wide`) — without PDBs, the drain can trigger application outages even on a perfectly-sized target. **Principle 2 reminder:** node *type* changes can be cost-direction traps if the new instance family carries different EBS / network pricing or the workloads need more nodes at a smaller size — verify the bill line items being moved (compute, EBS, data transfer), using bill-derived rates (Principle 4) or the Pricing API, not just the EC2 hourly rate."
