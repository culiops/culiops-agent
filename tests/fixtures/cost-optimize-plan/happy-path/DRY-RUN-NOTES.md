# Dry-run notes — happy-path

## Gate transitions

1. **GATE 1 (Scope)** — Operator provides the path to the upstream report. Skill loads `upstream-report.md`, extracts the 3-item Remediation list, reads `**Cloud:** aws` (single-cloud) and `**Scope:** 123456789012 / acme-prod`. Records the **target**: account 123456789012, region ap-southeast-1 (from the resource IDs). Report `Date:` 2026-05-28 is fresh. $5/mo floor: all 3 items pass ($280, $100, $48). No catalog at `.culiops/service-discovery/`. Skill asks for the IaC repo path; operator supplies `~/acme-infra` (simulated). Operator confirms scope. Approved.

2. **GATE 2 (Verification batch)** — Batch starts with Query 0: `0a` target check, then `0b-1..3` ownership probes. Skill then looks up playbooks: Per Step 2, each item's playbook queries are listed as conditional on Query 0b; here no owner routes to ❔, so none is skipped.
   - Item #1 (rightsize EC2) → `rightsize-ec2.md` (queries 1-6) + the commitment-coverage check for `Realizable` (query 7).
   - Item #2 (lifecycle S3) → `lifecycle-s3.md` (queries 8-14: lifecycle config, versioning, Intelligent-Tiering, size metrics, optional access-pattern evidence via Storage Class Analysis (operator opts in), object-size distribution, bill-derived rates).
   - Item #3 (delete EBS) → `delete-unattached-ebs.md` (queries 15-17).
   All playbooks present, no manual-review items, no dedup opportunities. IAM list and per-query cost itemized (Cost Explorer per request; S3 GETs for the SCA export and inventory report; LookupEvents free). Operator approves the full batch.

3. **Step 3 (Execute)** — `0a` first: `sts get-caller-identity` account = `Scope`. Then `0b` for each item (owners: terraform, terraform, unmanaged — none routes to ❔). All 17 follow-up queries succeed. Empty results (`lookup-events` for the volume, `describe-alarms`, `rbin` rules) are interpreted under the Metrics rule / Constraint 12 only where applicable: `lookup-events` is a management-event source and the describe call succeeded, so empty = no attach/detach.

4. **Step 4 (Triage)** — scoring, rules applied in order, first match wins:
   - **#1:** Rev 🟢 (`code:ec2.tf:17`), Blast 🟡 (TG, no catalog), Evidence 🟢 (all required rows incl. memory: 34.5% → 69.0% < 75%), Dep 🟡 (`code:alb.tf:64`). Realizable ✓. Rule 1 no; rule 2 no (not a delete); rule 3 no; rule 4 yes → **🟡**.
   - **#2:** Rev 🟢 (Transition to Standard-IA, an instantly readable class; terraform with `code:s3.tf:42`), Blast 🟢, Evidence 🟢 (required rows: cost direction net +$97/mo, size within 20%; the optional access-pattern row was run and passes: 0 GETs on aged objects over 115d), Dep 🟢. Rules 1-4 do not fire (not idle-ambiguous, not a delete) → rule 5 → **🟢 Fast win**.
   - **#3:** Rev 🔴 (snapshot not provably valid), Blast 🟢, Evidence 🟢, Dep 🟢. Rule 3 first clause (Reversibility 🔴) → **🔴**. (Evidence is 🟢, so the "delete AND Evidence not 🟢" clause is not the trigger.)
   - Ordering hint: fresh final snapshot before #3.

5. **GATE 3 (Plan review)** — Operator reviews, no revisions, approves. Plan written to `.culiops/cost-optimize-plan/acme-prod-20260528-0921.md`; left uncommitted (the repo does not track `.culiops/`).

## What this fixture validates

- **Target check first** (Constraint 11) and **ownership before triage** (Constraint 13) on a clean run: nothing is routed to ❔.
- **Required memory signal** when the target class has less RAM; present here so the item is not forced 🔴.
- **Evidence refs** on every dimension score (Law 3) and the `Owner` / `Realizable` columns in the 🟡 table; `Owner` in the 🔴 table.
- **Lifecycle to an instantly readable class lands 🟢** (Reversibility 🟢; Glacier Flexible would be 🟡, Expiration 🔴). Evidence is activity-based, not just "no policy exists": the optional SCA row ran and passed, plus the required cost-direction row.
- **Snapshot-validity rule** keeps a delete with an old snapshot at 🔴.
- **Reversibility dominance:** Reversibility 🔴 forces 🔴 even with all other dimensions 🟢.
- **No catalog does not silently produce 🟢 Dependency:** #1 gets 🟡 from a real IaC consumer; #3 gets 🟢 only because the grep ran and found nothing.
- **Plan summary totals $428/mo**, matching the upstream report.

## Acceptance check

A reviewer steps through `upstream-report.md` and each mock and confirms the skill would produce `expected-output.md` (allowing for run-specific timestamps): header has `Target` and `IaC repo(s)`; rows `0a` / `0b-N` present; tiers 🟢 / 🟡 / 🔴 exactly; `Owner` and `Realizable` columns populated with `live:` / `code:` refs; Drift and Gaps as written. Emoji must render; if a renderer strips 4-byte UTF-8 the test is incomplete.
