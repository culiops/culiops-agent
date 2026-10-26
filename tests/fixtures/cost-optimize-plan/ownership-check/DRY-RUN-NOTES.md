# Dry-run notes - ownership-check

## Gate transitions

1. **GATE 1 (Scope)** - Operator provides the upstream report path and the IaC repo (`~/acme-infra`, simulated). Skill loads `upstream-report.md`, extracts 2 items, reads `**Cloud:** aws`, `**Scope:** 111122223333 / acme-data`. Target: account 111122223333, region ap-southeast-1 (from the resource IDs / report). Report is fresh. $5/mo floor: both pass ($40, $90). No catalog. Approved.

2. **GATE 2 (Verification batch)** - Playbooks: item #1 -> `delete-unattached-ebs.md`; item #2 -> `rightsize-ec2.md`. The batch is shown with Query 0 firm (`0a` target check; `0b-1`, `0b-2` ownership probes) and each playbook's remaining queries listed as **conditional on Query 0b**: they are skipped at execution if the probe routes the item to ❔. Itemized IAM and cost include the rightsize playbook's Cost Explorer requests. Operator approves.

3. **Step 3 (Execute)** - `0a`: `sts get-caller-identity` account 111122223333 = `Scope`. `0b-1`: the volume's own tags show `kubernetes.io/created-for/pvc/name` and `ebs.csi.aws.com/cluster`; the IaC grep for the volume ID finds nothing (the CSI driver created it) -> owner `k8s` -> **❔ `owned-by-k8s`**; the three remaining EBS queries are skipped. `0b-2`: the instance tag `aws:autoscaling:groupName=web-asg` -> owner `asg` -> **❔ `owned-by-asg`**; all remaining rightsize queries are skipped. Nothing else runs. No query fails.

4. **Step 4 (Triage)** - Neither item is scored: Constraint 13 sends `k8s` / `asg` owners to ❔ `owned-by-<owner>` because the remediation target is the owner (PVC / StorageClass; launch template). There is no Evidence to score and none is invented (Law 3: no tier without evidence). Result: 🟢 0, 🟡 0, 🔵 0, 🔴 0, 🚫 0, ❔ 2.

5. **GATE 3 (Plan review)** - Plan drafted with only ❔ populated, each Reason naming the owner and the place to change. Operator approves. Plan written to `.culiops/cost-optimize-plan/acme-data-20260602-1026.md`, uncommitted.

## What this fixture validates

- **The ownership probe runs first and is decisive** - both a controller tag set (k8s) and a group tag (asg) are recognized from the resource's own describe output.
- **Remaining playbook queries are skipped at execution, not run "just in case"** - the plan lists them as skipped; no mock exists for them.
- **A raw-resource verdict would have been wrong in both directions:** a delete of a live PV volume (data loss) and a rightsize that the ASG reverts. The ❔ routing prevents both.
- **0 actionable items, 2 ❔** renders cleanly.
- **The skill stays within its scope:** it states that live cluster state is not queried and does not guess it.
- **Savings copied verbatim, not assessed.**

## Acceptance check

A reviewer confirms: (a) only rows `0a`, `0b-1`, `0b-2` appear in "Verification queries run", and the skipped queries are named; (b) item #1 is ❔ with reason `owned-by-k8s` and item #2 is ❔ with reason `owned-by-asg`, neither in any tier; (c) the summary shows ❔ = 2 and 0 elsewhere; (d) each Reason names the owner's change point (PVC / StorageClass; launch template with code ref); (e) the Gaps state that live cluster state was not queried and that no rightsize evidence exists for the new class; (f) header has `Target` and `IaC repo(s)`.
