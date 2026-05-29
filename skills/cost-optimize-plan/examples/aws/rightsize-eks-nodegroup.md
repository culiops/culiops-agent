---
cloud: aws
action: rightsize
resource_type: eks-nodegroup
applies_when: action == "rightsize" AND resource matches "arn:aws:eks:*:nodegroup/*"
---

# Verify: Rightsize EKS managed nodegroup

Covers three rightsizing levers, which compose: (a) reduce `desiredSize` / `minSize` (scale down), (b) change `instanceTypes` (smaller class or AMD/Graviton swap), and (c) capacity-type swap `ON_DEMAND` → `SPOT` (reliability tradeoff, see Caveats).

## Required IAM
- `eks:DescribeNodegroup`
- `eks:ListNodegroups`
- `autoscaling:DescribeAutoScalingGroups`
- `ec2:DescribeInstances`
- `cloudwatch:GetMetricStatistics`
- `cloudwatch:ListMetrics` (for Container Insights metric discovery)
- Cluster-side (kubectl): `get nodes`, `top nodes`, `describe nodes`, `get pods --all-namespaces` (requires cluster RBAC granting `system:node-reader` and metrics-reader)

## Queries

1. `aws eks describe-nodegroup --cluster-name <cluster> --nodegroup-name <ng>` — captures `instanceTypes[]`, `scalingConfig.{min,desired,max}Size`, `capacityType`, `amiType`, `nodegroupArn`, `resources.autoScalingGroups[]`.
2. `aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names <asg-name>` — current instances per nodegroup; cross-references EC2 instance IDs for utilization queries.
3. For each instance in Query 2: `aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=<id> --start-time <now-14d> --end-time <now> --period 3600 --statistics Average,Maximum` — node-level CPU. **Activity signal — node side.**
4. For each instance: same `GetMetricStatistics` for `NetworkIn` / `NetworkOut` and (if CloudWatch agent installed) `mem_used_percent` — memory baseline. Score ⚪ if no memory data; do not assume.
5. Container Insights (if enabled): `aws cloudwatch get-metric-statistics --namespace ContainerInsights --metric-name node_cpu_utilization --dimensions Name=ClusterName,Value=<cluster>,Name=NodegroupName,Value=<ng> --start-time <now-14d> --end-time <now> --period 3600 --statistics Average,Maximum` — nodegroup-aggregated CPU.
6. Container Insights: `node_memory_utilization` + `node_filesystem_utilization` for the same dimensions.
7. Cluster-side activity (via kubectl, captured to evidence buffer): `kubectl top nodes -l eks.amazonaws.com/nodegroup=<ng>` — current actual CPU/memory in use. `kubectl get pods --all-namespaces --field-selector spec.nodeName=<each-node> -o json | jq '[.items[].spec.containers[].resources.requests | (.cpu // "0"), (.memory // "0")]'` — sum of **requested** resources per node (the scheduler's view, not actual use).
8. (If kube-state-metrics + metrics-server present, via cluster Prometheus or `kubectl top`): `sum(kube_pod_container_resource_requests{nodegroup=<ng>}) by (resource)` vs `sum(kube_node_status_allocatable{nodegroup=<ng>}) by (resource)` — request:allocatable ratio per resource per node.

## Evidence thresholds

| Signal | 🟢 Threshold (safe to rightsize down) | 🚫 Trigger (do not rightsize down) |
|--------|--------------------------------------|--------------------------------------|
| 14d p95 node CPU utilization | ≤ 40% | ≥ 75% — at risk of CPU pressure post-scale-down |
| 14d p95 node memory utilization | ≤ 50% (if available) | ≥ 75% (if available); ⚪ if no memory data |
| 14d p95 pod-request : node-allocatable (CPU) | ≤ 60% | ≥ 80% — scheduler will fail to place pods on smaller / fewer nodes |
| 14d p95 pod-request : node-allocatable (memory) | ≤ 70% | ≥ 80% |
| Pending pods (last 7d, from Container Insights `cluster_failed_node_count` proxy or kube-state-metrics) | `0` sustained | recurring — nodegroup is already capacity-constrained |
| HPA / VPA controllers on workloads in this nodegroup | Reviewed — autoscaler-driven resize composes with manual rightsize | Active HPA scaling at peak → check peak window before fixing nodegroup size |

**Principle 1 reminder:** `desiredSize` and pod count are **attachment** — they say "this many nodes are configured / pods are scheduled." Actual CPU / memory / network throughput is **activity**. A nodegroup with 10 nodes and 100 idle pods (sleeping `Deployment`s with low requests) is still over-provisioned. Score Dimension 3 on utilization, not on `desiredSize`.

**Keep-alive noise to subtract:** system daemonsets (kube-proxy, aws-node, coredns, fluent-bit, node-problem-detector) consume baseline CPU/memory on every node regardless of workload. Subtract their baseline (typically ~5–10% CPU, ~150–300 MB memory per node) before judging "workload activity." Container Insights `node_cpu_utilization` includes daemonset usage; isolate via `pod_cpu_utilization` aggregated by namespace if available.

## Caveats — capacity-type swap (`ON_DEMAND` → `SPOT`)

This is **NOT** a Principle 2 cost-direction problem (Spot is unambiguously cheaper per-hour). It is a **reliability** tradeoff: Spot instances can be reclaimed with 2-minute notice. Score separately:

- Workloads tolerating ≤ 2-min interruption (stateless web, batch jobs with checkpointing, build/CI runners): `capacityType: SPOT` → ~60–90% savings. 🟢.
- Workloads requiring graceful termination > 2 min, or stateful pods without PDBs (PodDisruptionBudgets): **do not swap**. Spot interruptions cascade into outages. 🔴.
- Mixed nodegroups via Karpenter or multiple managed nodegroups: split workloads by tolerance, run two nodegroups (`SPOT` + `ON_DEMAND`). Cost-optimize-plan emits this as two coordinated items in 🟡, not one item.

## Reversibility classification
- **Default:** 🟢 for `scalingConfig` changes (desired/min size): re-apply old IaC, ASG scales back. ~5 min RTO.
- **Default:** 🟡 for `instanceTypes` change: nodegroup roll required (drain + replace). Old node template gone; re-apply old IaC starts a new roll. ~15–45 min RTO depending on size.
- **Default:** 🟡 for `capacityType: SPOT` reversal: same as instance-type change (rolling replacement).

## Blast radius classification
- **Default:** 🟡 — touches a live nodegroup serving real pods. Bump to 🟢 if catalog confirms ≥ 2 nodegroups in the cluster AND PDBs are configured for all workloads on this nodegroup (drain is safe). Bump to 🔴 if this is the cluster's only nodegroup OR if pods on this nodegroup are stateful (StatefulSets without sufficient PV redundancy).

## Rollback note (informational, shown in plan)
"`scalingConfig` rollback: re-apply old IaC, ASG resizes. `instanceTypes` or `capacityType` rollback: re-apply old IaC, nodegroup rolls (drain + replace, ~15–45 min). **Pre-rightsize:** confirm PDBs exist for all workloads on this nodegroup (`kubectl get pdb -A -o wide`) — without PDBs, the drain during reduce can trigger application outages even on a perfectly-sized target. **Principle 2 reminder:** node *type* changes can be cost-direction traps if the new instance family carries different EBS / network pricing — a Graviton swap saves ~20% on compute but EBS gp3 throughput pricing is unchanged; verify the bill line item being moved, not just the EC2 hourly rate."
