# Execution Plan — search-api

**Run:** search-api, account 123456789012, region eu-west-1
**Operator:** arn:aws:iam::123456789012:user/alice
**Generated:** 2026-05-12T13:40:00Z
**Intent:** takeover from Search Team, scheduled for 2026-06-22

---

## What we have

| Source | State | Path | Age |
|---|---|---|---|
| Diagram images | provided | `~/handoff/search-api-architecture.png` | n/a |
| IaC repo | none supplied | Helm chart and CloudFormation templates exist in `git.example.com` (not cloned) | — |
| AWS credentials | configured | profile `prod-main` | live |
| Kubernetes access | configured | context `platform-eks`, namespace `search` (read-only) | live |
| service-discovery catalog | none | — | — |
| runtime-trace profile | none | — | — |
| Scoping primitive | namespace `search` + tag `service=search-api` for discovery; catalog resource set for runtime-trace | provided by operator | n/a |

---

## What we need (per planned step)

| Need | Source | Gap | Proposed action | Cost | Approval |
|---|---|---|---|---|---|
| Operator identity matches intake | AWS STS | unknown | run `aws sts get-caller-identity --profile prod-main --query Account`; the result must equal intake account `123456789012` (stop on mismatch) | $0 | **needed** |
| Discovery (Steps 2–3, one delegation) | diagram + AWS APIs + Kubernetes API | full | no IaC supplied (Helm chart and CloudFormation templates exist in git but were not cloned) -> `service-discovery` real-discovery (docs + live AWS + live Kubernetes). If the repos were supplied: the IaC path with its live cross-check (Step 2V) | $0 (read-only) | **needed** |
| Cross-region inventory | Resource Explorer | unknown | covered by runtime-trace Step 4 | $0 | covered |
| Activity baseline + control-plane events + wiring (Step 4) | CloudWatch + CloudTrail + CE | full | run `runtime-trace` with the catalog's AWS resource set as the scoping primitive. No cost-allocation tag -> spend is "account context, not attributable". EKS in-cluster workloads are not traced (recorded as a gap) | ~$0.02 (Cost Explorer charges) | **needed** |
| CloudTrail Event history probe | CloudTrail API | unknown | run `aws cloudtrail lookup-events --max-results 1 --profile prod-main --region eu-west-1 --query 'Events[0].EventTime'` before Step 4. Record only the derived fact | $0 | **needed** |
| Resource Explorer availability probe | RE API | unknown | run `aws resource-explorer-2 list-indexes --profile prod-main --region eu-west-1 --query 'Indexes[].{Region:Region,Type:Type}'` before Step 4. Record only the derived fact | $0 | **needed** |
| Tribal knowledge (Step 5) | Outgoing team | full | emit questionnaire incl. 4b (IaC & ownership: Helm repo, CloudFormation stacks, RBAC, IRSA); share with Search Team | $0 | proceeds at Step 5 |
| Readiness assessment (Step 6) | All prior artifacts | full | auto-mark from artifacts; `◐` items with a read-only check get a Step 6 verification batch (offered by default; skipping leaves them `◐` and the verdict `partial`); attested only for items 3, 11, 12 | $0 | proceeds at Step 6 |
| Handoff package (Step 7) | All prior artifacts | full | assemble README + snapshots; private-repo reminder before any commit | $0 | proceeds at Step 7 |

---

## Proposed invocations

### For Steps 2–3 (discovery) — to run after this plan is approved

One delegation; no separate diagram and live catalogs.

```
Invoke service-discovery with:
  - mode: real-discovery
  - inputs: ~/handoff/search-api-architecture.png (docs);
            AWS live APIs (account 123456789012, region eu-west-1);
            Kubernetes live API (context platform-eks, namespace search)
  - scoping: namespace search + tag service=search-api
  - output: .culiops/service-discovery/search-api-prod.md
```

### For Step 4 (runtime profile) — to run after Steps 2–3

```
Invoke runtime-trace with:
  - service: search-api
  - account: 123456789012
  - region: eu-west-1
  - scoping-primitive: the resource set from the service-discovery catalog at .culiops/service-discovery/search-api-prod.md
  - intent-category: takeover
  - --redact: not set (internal handoff)
  - output: .culiops/runtime-trace/search-api-runtime-profile.md
```

---

## Approval block

**Recording rule:** targeted CLI commands above are always projected with `--query`. After the operator runs one, this file and `state.md` record only the derived fact (for example "Event history readable: yes", "caller account matches intake: yes"), never the pasted output.

Operator approves this plan by responding "plan approved" or by editing the proposed actions and re-confirming. Until then, no sibling skill is invoked and no CLI command is emitted.

**Approval status:** approved

**Approval timestamp:** 2026-05-12T13:42:00Z

**Operator notes:** "Proceed as proposed. Real-discovery with the kube context is right; the Helm chart and CFN templates stay in git. Share the questionnaire with Lena (lena@example.com) at Step 5."

---

## Addendum — Step 6 verification batch

Proposed at Gate 6 for the `◐` items with a read-only check (10, 24). Approved separately from the Step 1.5 plan.

| Item | Command | Expected derived fact |
|---|---|---|
| 10 | `aws cloudwatch describe-alarms --profile prod-main --region eu-west-1 --alarm-name-prefix search- --query 'MetricAlarms[].{Name:AlarmName,Metric:MetricName,Ns:Namespace,Actions:length(AlarmActions)}'` | which of the 4 named alarms exist, with actions |
| 24 | `aws elasticache describe-replication-groups --profile prod-main --region eu-west-1 --replication-group-id search-cache --query 'ReplicationGroups[].SnapshotRetentionLimit'` | snapshot retention in days |

**Approved:** 2026-05-12T15:33:00Z. Targeted commands are read-only, projected with `--query`, pinned to `--profile prod-main --region eu-west-1`, and run after `aws sts get-caller-identity` re-confirms account 123456789012. Only derived facts are recorded in `readiness-scorecard.md`.
