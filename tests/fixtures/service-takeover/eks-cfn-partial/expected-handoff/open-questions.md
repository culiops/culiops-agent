---
open-questions-schema: 2
service: search-api
generated-at: 2026-05-12T15:55:00Z
high-priority-count: 1
medium-priority-count: 4
low-priority-count: 1
---

# Open Questions — search-api

**Generated:** 2026-05-12T15:55:00Z

## Summary

| Priority | Count |
|---|---|
| High | 1 |
| Medium | 4 |
| Low | 1 |

One High gap (deploy history is a Kubernetes-side fact); the rest are confirmations.

Every `✗ conflict` in the scorecard is High by rule. `◐` and `?` items are listed in the scorecard with the check that would settle each; only the ones that need someone else's action appear here.

---

## High Priority (blockers — resolve before sign-off)

### HIGH-1 — No deploy history for the in-cluster Deployment (item 8 `?`; items 16, 18 unverifiable)

- **Source:** runtime-profile.md Control-Plane Activity and Gaps; readiness-scorecard.md items 8, 16, 18
- **Detail:** CloudTrail Event history holds no Kubernetes API calls, so Helm rollouts are invisible. The 6 management events are CloudFormation and load-balancer-controller changes.
- **Suggested action:** Operator runs `helm history search-api -n search` (not an AWS read) and records the revision count and dates; compare with "about weekly".
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08

---

## Medium Priority (should resolve within 30 days of handoff)

### MED-1 — CloudFormation owns 5 of the 10 rows: confirm the change path (item 4 note)

- **Source:** service-catalog.md Owner column; interview Section 4b
- **Detail:** `search-data-stack` (queue, cache, bucket, secret) and `search-iam-stack` (IRSA role) own these resources. Console edits would drift from the stacks; changes go through change sets.
- **Suggested action:** Get access to the templates (`git.example.com/search/search-infra`), the stack role `search-cfn-service-role` and the change-set process before the first change.
- **Owner:** alice (Platform Team) and Lena M.
- **Target date:** 2026-06-15

### MED-2 — Deploy role and Kubernetes access are unverified (items 2, 15, 16)

- **Source:** readiness-scorecard.md items 2, 15, 16; interview Section 4
- **Detail:** `search-ci-deployer` and the access entry for `platform-team-eks` are interview statements; CloudTrail shows no deploy principal and no AWS action can be simulated.
- **Suggested action:** `aws eks list-access-entries --cluster-name platform-eks` (read-only) and `kubectl auth can-i update deployments -n search` as `platform-team-eks`.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

### MED-3 — Where does the data come from in a Region-loss rebuild? (items 24, 25)

- **Source:** readiness-scorecard.md items 24, 25; interview Section 10; catalog (no cross-Region copy)
- **Detail:** RTO 4 h / RPO 24 h assume a rebuild in eu-central-1, but snapshots and the S3 bucket are single-Region as catalogued. The restore test (2026-03-02) is operator-stated.
- **Suggested action:** Ask the Search Team how data reaches eu-central-1; witness a restore and attest it.
- **Owner:** Omar T. (Search Team) and alice
- **Target date:** 2026-07-15

### MED-4 — ALB clients are interview-stated only (item 19)

- **Source:** readiness-scorecard.md item 19
- **Detail:** web-frontend and mobile-api are named; AWS configuration shows only what the ALB forwards to.
- **Suggested action:** Confirm with the Web and Mobile teams.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

---

## Low Priority

### LOW-1 — EKS in-cluster workloads are not traced

- **Source:** runtime-profile.md Gaps
- **Detail:** Pods, restarts and HPA for `search/search-api` are not in any artifact.
- **Suggested action:** Read them with `kubectl` when needed.
- **Owner:** alice (Platform Team)

---

## Resolved items

*None at this time.*
