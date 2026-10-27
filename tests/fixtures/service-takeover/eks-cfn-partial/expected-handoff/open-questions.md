---
open-questions-schema: 2
service: search-api
generated-at: 2026-05-12T15:55:00Z
high-priority-count: 0
medium-priority-count: 6
low-priority-count: 1
---

# Open Questions — search-api

**Generated:** 2026-05-12T15:55:00Z

## Summary

| Priority | Count |
|---|---|
| High | 0 |
| Medium | 6 |
| Low | 1 |

No item is `✗` or `✗ conflict`, so there is no High item. The in-cluster gaps (`?`) lead the Medium list.

Priority follows the scorecard rule: every `✗` and `✗ conflict` is High; every `?` and `◐` is Medium; notes on `✓` items are Low. Within a level the cheapest resolution comes first (a Step 6 check, then a document to open, then an outgoing-team follow-up). Each entry names its item and mark.

---

## High Priority (blockers — resolve before sign-off)

*None: no item is `✗` or `✗ conflict`.*

---

## Medium Priority (should resolve within 30 days of handoff)

### MED-1 — The in-cluster Deployment has no evidence: no deploy history, baseline or audit-log query (items 7, 8, 9 `?`; items 16, 18 unverifiable)

- **Source:** runtime-profile.md Control-Plane Activity and Gaps; readiness-scorecard.md items 7, 8, 9, 16, 18
- **Detail:** CloudTrail Event history holds no Kubernetes API calls, so Helm rollouts are invisible, and `runtime-trace` does not trace in-cluster workloads. The 6 management events are CloudFormation and load-balancer-controller changes.
- **Suggested action:** Operator runs `helm history search-api -n search` and records the revision count and dates (compare with "about weekly"); queries the cluster's metrics backend for the Deployment over a stated window; queries the control-plane audit log if it is enabled. None of these is an AWS read.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-08

### MED-2 — Alarm and alert-rule coverage is incomplete (item 10, `◐`)

- **Source:** readiness-scorecard.md item 10; interview Section 5
- **Detail:** The 4 named CloudWatch alarms exist, are enabled and have actions, but nothing alarms on the S3 bucket, the cache's errors or latency, or the Deployment, and no cluster alert-rule or notification route was checked.
- **Suggested action:** `kubectl get prometheusrules -n search` (or the monitoring backend's rules listing) plus the notification route; the Search Team adds the missing alarms or records why none is needed; re-run `describe-alarms`.
- **Owner:** alice (Platform Team) and Lena M.
- **Target date:** 2026-06-15

### MED-3 — Deploy role and Kubernetes access are unverified (items 2, 15, 16, `◐`)

- **Source:** readiness-scorecard.md items 2, 15, 16; interview Section 4
- **Detail:** `search-ci-deployer` and the access entry for `platform-team-eks` are interview statements; CloudTrail shows no deploy principal and no AWS action can be simulated.
- **Suggested action:** `aws eks list-access-entries --cluster-name platform-eks` (read-only) and `kubectl auth can-i update deployments -n search` run by a Platform Team member as themselves.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

### MED-4 — External API ownership has no record (item 21, `◐`)

- **Source:** readiness-scorecard.md item 21; interview Section 8
- **Detail:** The interview and the catalog both say no external APIs, but no vendor or contract register is cited, so the item cannot be `N/A`.
- **Suggested action:** Find the vendor or contract register entry that lists none for this service and cite it.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

### MED-5 — ALB clients are interview-stated only (item 19, `◐`)

- **Source:** readiness-scorecard.md item 19
- **Detail:** web-frontend and mobile-api are named; AWS configuration shows only what the ALB forwards to.
- **Suggested action:** Confirm with the Web and Mobile teams.
- **Owner:** alice (Platform Team)
- **Target date:** 2026-06-15

### MED-6 — Where does the data come from in a Region-loss rebuild? (items 24, 25, `◐`)

- **Source:** readiness-scorecard.md items 24, 25; interview Section 10; catalog (no cross-Region copy)
- **Detail:** RTO 4 h / RPO 24 h assume a rebuild in eu-central-1, but snapshots and the S3 bucket are single-Region as catalogued. The restore test (2026-03-02) is a stated date with no record.
- **Suggested action:** Ask the Search Team how data reaches eu-central-1; open the ticket or run log for the restore test, or witness a restore and record it.
- **Owner:** Omar T. (Search Team) and alice
- **Target date:** 2026-07-15

---

## Low Priority

### LOW-1 — CloudFormation owns 5 of the 10 rows: confirm the change path (item 4 note)

- **Source:** service-catalog.md Owner column; interview Section 4b
- **Detail:** `search-data-stack` (queue, cache, bucket, secret) and `search-iam-stack` (IRSA role) own these resources. Console edits would drift from the stacks; changes go through change sets.
- **Suggested action:** Get access to the templates (`git.example.com/search/search-infra`), the stack role `search-cfn-service-role` and the change-set process before the first change.
- **Owner:** alice (Platform Team) and Lena M.

---

## Resolved items

*None at this time.*
