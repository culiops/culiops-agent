# DRY-RUN-NOTES — query-failure fixture

## Gate transitions

### GATE 1 — Scope confirmation
- Report: `acme-prod-waste-mixed-20260528-1200.md`
- 3 items identified, $240/mo total estimated waste
- Items: vol-0cccc1 ($35), bucket-logs-2019 ($180), prod-old-lb ($25)
- **Operator approves.**

### GATE 2 — Verification batch approval
- Skill lists ~8 queries across 3 items and the IAM permissions required:
  - `ec2:DescribeVolumes` — for vol-0cccc1
  - `cloudtrail:LookupEvents` — for bucket-logs-2019
  - `s3:GetBucketVersioning`, `s3:GetBucketLifecycleConfiguration`, `s3:ListBucketMultipartUploads` — for bucket-logs-2019
  - `elasticloadbalancing:DescribeLoadBalancers`, `elasticloadbalancing:DescribeTargetHealth` — for prod-old-lb
- **Operator approves WITHOUT pre-checking their own IAM** — a realistic flow. The operator may not realize their role lacks `cloudtrail:LookupEvents` until execution hits it.

### Step 3 — Execute verification (FAILS here)
- Query #1: `ec2:DescribeVolumes` for vol-0cccc1 → **succeeds**. Evidence captured in memory.
- Query #2: `cloudtrail:LookupEvents` for bucket-logs-2019 → **`AccessDeniedException`**. **SKILL STOPS.**

### Steps 4, 5 and GATE 3 — NEVER REACHED
- Triage model never applied (no complete evidence set).
- Plan file never written.
- GATE 3 (plan approval) never presented to operator.

---

## What this fixture validates

- **Spec Constraint #8:** Stop on any query failure; surface the failure to the operator. Do not write a partial plan.
- **Iron Law #3:** Do NOT promote item #1 (vol-0cccc1) to a tier just because its queries succeeded. Without a complete evidence set for all batch items, the run is aborted and nothing is committed.
- **Actionable operator guidance:** The skill provides three concrete remediation paths (grant permission, trim item, investigate SCP/boundary) rather than a bare error dump.
- **Mock completeness:** `mock-responses/` contains exactly 2 files — the succeed response and the fail response. No mocks for queries #3+ exist because the skill never attempts them. This mirrors real execution behavior.

---

## Acceptance check

A reviewer confirms:

- **(a)** `expected-output.md` describes an error message (not a plan template) that names the failing query, the affected item, the required permission, and the AWS error string.
- **(b)** No `.culiops/cost-optimize-plan/` plan file would be written in a real run — the skill exits before the write step.
- **(c)** Item #1's successful `ec2:DescribeVolumes` result is NOT incorporated into a partial plan — it is captured in memory only and discarded on abort.
- **(d)** The suggested-next-actions list gives three concrete remediation paths (grant perm / trim item / investigate SCP), giving the operator a clear path forward.
- **(e)** `mock-responses/` has exactly 2 JSON files — omitting queries #3+ matches the skill's actual abort-before-execution behavior.
