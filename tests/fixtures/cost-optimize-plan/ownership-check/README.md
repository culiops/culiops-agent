# ownership-check - cost-optimize-plan fixture

Two-item report where **both** items belong to a controller, not to Terraform: a Kubernetes PV volume that looks like an orphan, and an Auto Scaling group member that looks like a rightsize candidate. The ownership probe (Query 0b) routes both to ❔ `owned-by-<owner>` and the rest of their playbook queries are skipped. The plan has 0 actionable items and 2 ❔.

## What's modelled

A fictional AWS account `111122223333` (`acme-data`) in `ap-southeast-1`. The upstream waste audit (2026-06-02) did not look at tags or ownership. It found:

1. **`vol-0dddd1`** - 500 GB gp3, `available` since 2026-04-09, $40/mo. The volume carries `kubernetes.io/created-for/pvc/name=data-kafka-2`, `kubernetes.io/created-for/pvc/namespace=streaming` and `ebs.csi.aws.com/cluster=true`. A StatefulSet scaled to 0 leaves its PV's volume `available`. Deleting it would break the PV and lose the data. Correct outcome: **❔ `owned-by-k8s`** (remediate via PVC / PV + StorageClass `reclaimPolicy`).
2. **`i-0eeee1`** - m5.2xlarge, Compute Optimizer says m5.xlarge ($90/mo). The instance carries `aws:autoscaling:groupName=web-asg`. A resize of one member is reverted at the next scale event. Correct outcome: **❔ `owned-by-asg`** (change the launch template).

**IaC repo: simulated** (`~/acme-infra`, Terraform + Helm); `mock-responses/iac-grep-simulated.json` stands in for the grep. The `code:` refs (`asg.tf:12`, `launch_template.tf:5`, `charts/kafka/values.yaml:21`, `charts/kafka/storageclass.yaml:8`) are illustrative. Neither raw resource is declared in code, which is itself the signal.

## The operator question

> "Triage the cost report at .culiops/cloud-cost-investigate/acme-data-waste-20260602-1020.md and build me an execution plan. The IaC repo is ~/acme-infra."

(See `operator-question.md`.)

## What this fixture exercises

- **Constraint 13 (ownership before triage)** and the shared **ownership probe**: tags from the item's own describe call plus an IaC grep decide the owner (`k8s`, `asg`).
- **Constraint 11 (target check first):** `0a` runs before anything else; account = `Scope`.
- **Queries skipped at execution.** The GATE 2 batch lists each playbook's queries as conditional on Query 0b; once `0b` routes an item to ❔, its remaining queries are skipped at execution. The plan lists exactly which were skipped, and none is billed (the rightsize playbook's Cost Explorer requests are avoided).
- **Why the raw resource must not be scored:** for the PV volume, "unattached for 90d" is expected, not waste; for the ASG member, "CPU 9%" is the wrong question when the launch template is the lever.
- **Zero actionable plan with two ❔ items**, each with an actionable Reason that names the real owner and the place to change it.
- **No fabrication of live state:** the plan says the cluster itself was not queried (outside this skill).
- Cross-check: `delete-unattached-ebs.md` Query 1 and `rightsize-ec2.md` Query 0 describe exactly these two routes.

## Files in this fixture

| File | Row | Purpose |
|------|-----|---------|
| `operator-question.md` | - | freeform operator prompt |
| `upstream-report.md` | - | synthetic waste report with the two items (skill input) |
| `mock-responses/sts-get-caller-identity.json` | 0a | target check |
| `mock-responses/describe-volumes-vol-0dddd1.json` | 0b-1 | `available` volume with CSI / PVC tags -> owner k8s |
| `mock-responses/describe-instances-i-0eeee1.json` | 0b-2 | instance with `aws:autoscaling:groupName=web-asg` -> owner asg |
| `mock-responses/iac-grep-simulated.json` | 0b-1, 0b-2 | simulated IaC grep (no raw resource; ASG / chart pointers) |
| `expected-output.md` | - | the plan the skill produces at GATE 3 |
| `DRY-RUN-NOTES.md` | - | gate transitions and acceptance check |

No mocks exist for the skipped playbook queries - they must not run.

## Expected tier outcomes

| # | Item | Upstream priority | Tier | Dominant reason |
|---|------|-------------------|------|-----------------|
| 1 | Delete unattached EBS vol-0dddd1 | 1 ($40) | ❔ Manual review | `owned-by-k8s`: PV backing volume of PVC `streaming/data-kafka-2` |
| 2 | Rightsize i-0eeee1 m5.2xlarge → m5.xlarge | 2 ($90) | ❔ Manual review | `owned-by-asg`: member of `web-asg`; change the launch template |
