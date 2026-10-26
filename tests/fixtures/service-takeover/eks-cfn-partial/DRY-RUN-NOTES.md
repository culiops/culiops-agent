# Dry-run notes — eks-cfn-partial

## What this fixture validates

- **Partial verdict, exercised for real:** no `✗`, a single `?` (item 8), and `◐` items that each name their verifying check; `ready` is not reached.
- **CloudFormation owner recognition (M4 scope item):** the catalog's Owner column carries `cloudformation (search-data-stack)` / `(search-iam-stack)` from the `aws:cloudformation:stack-name` tag; the runtime profile's resolved set shows the same owner hints. The note on item 4 and MED-1 record the consequence (changes go through the stack), without changing a mark.
- **EKS gap:** the profile says "EKS in-cluster workloads not traced". Item 7 still passes for the ALB and SQS rows but carries the gap in its notes; item 8 is `?` because the Deployment's rollouts are invisible to CloudTrail; items 2, 16, 18 stay `◐`.
- **Spend not attributable:** no cost-allocation tag, so the profile's Spend section is "Account context — NOT attributable to this service"; the TL;DR does not quote it as the service's cost. No scorecard item depends on spend.
- Interview Section 4b answers (Helm repo, CloudFormation stacks, Kubernetes RBAC and IRSA) feed items 2, 15 and the CFN note.
- Same-target check includes the kube context; one discovery delegation; derived-facts-only probes in eu-west-1; strict verdict; a 2-command Step 6 batch.

---

## Gate transitions

**Gate 1** (13:30Z). Inputs in `input.md`.

**Gate 1.5** (13:33Z-13:42Z). Probes (identity, Event history in eu-west-1, RE aggregator index in eu-west-1; derived facts only). Plan approved.

**Gates 2-3** (13:42Z-14:30Z). One `service-discovery` real-discovery delegation (diagram + AWS + Kubernetes). Snapshot with a same-target check; ownership recognised (5 CFN rows, 3 helm rows).

**Gate 4** (14:30Z-15:00Z). runtime-trace scoped by the catalog's 7 AWS rows. 6 management events (none a deploy to compute); Wiring (queue policy, ALB target group); activity baselines for the ALB and queue only; cross-Region clean (7 of 7).

**Gate 5** (15:00Z-15:30Z). 11 complete, incl. 4b.

**Gate 6** (15:30Z-15:55Z). Batch (2 commands): alarms (4 present: item 10 `✓ verified`), ElastiCache snapshot retention 7 (item 24 stays `◐`). Operator opens the runbook, postmortem and rollback links (13, 14, 17 `✓ verified`) and attests 3, 11, 12. Verdict `partial`.

**Gate 7** (15:55Z-16:00Z). 8 files.

---

## Marks

12 ✓ verified, 3 ✓ attested, 8 ◐, 0 ✗, 0 ✗ conflict, 1 ?, 1 N/A (25 items): 12 + 3 + 8 + 1 + 1 = 25.

## Acceptance check

- Verdict `partial` with exactly one `?` (item 8) and no `✗`.
- Catalog Owner column contains `cloudformation (<stack>)` rows; the runtime profile says "Account context — NOT attributable" and "EKS in-cluster workloads not traced".
- `interview-questionnaire.md` has the 4b block.

Citations in `expected-handoff/readiness-scorecard.md` are package-relative: `interview-questionnaire.md` is the snapshot of `filled-interview.md`; `service-catalog.md` and `runtime-profile.md` are the snapshots of the files under `mock-artifacts/`; `state.md` is `expected-handoff/state.md`. Line numbers refer to those files.
