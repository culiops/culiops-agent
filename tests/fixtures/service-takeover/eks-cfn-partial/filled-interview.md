---
template-version: 1
emitted-by: service-takeover
service: search-api
filled-by: Lena M., Omar T.
filled-date: 2026-05-12
---

# Outgoing-Team Interview — search-api

> **Private repo only.** Record references (where a secret lives, who owns it), never values. No tokens/signed links in URLs. Prefer role/team aliases over personal phone numbers.

**Outgoing team:** Search Team (primary contact: Lena M. — lena@example.com)
**Incoming team:** Platform Team
**Handoff date:** 2026-06-22
**Filled in by:** Lena M. and Omar T. on 2026-05-12

---

## Why this document exists

This questionnaire captures the **tribal knowledge** about `search-api` that doesn't live in the catalog or runtime profile — the things only the outgoing team knows.

---

## 1. Service overview

- **Business purpose** — Full-text product search API behind the storefront. Serves the web frontend and the mobile API.
- **Criticality tier** — Tier 1. Search down for an hour degrades conversion but checkout still works.
- **Age** — Created 2023-02 on EC2; moved to EKS (`platform-eks`) in 2024-04.
- **Why it exists** — Keeps search load and index memory off the catalog service. Still current.

## 2. People & ownership

- **Current owners** — Lena M. (tech lead), Omar T. (SRE).
- **On-call schedule** — PagerDuty rotation, weekly handoff Monday 09:00 UTC. Current on-call: Omar.
- **Escalation contacts** — 1. Lena M. 2. Ravi P. (engineering manager, ravi@example.com).
- **Related teams** — Web frontend team, Mobile team, Platform Team (cluster owner).

## 3. SLOs / SLIs

- **Defined SLOs** — Availability 99.9% per calendar month; p95 latency <= 300 ms.
- **SLI implementations** — ALB `HTTPCode_Target_5XX_Count` / `RequestCount` and ALB `TargetResponseTime` p95.
- **Error budget tracking** — Reviewed monthly; last burned 2026-02-09 (INC-2026-02-09).
- **Dashboards** — https://eu-west-1.console.aws.amazon.com/cloudwatch/home#dashboards:name=search-api

## 4. Deploy process

- **How does code reach prod?** GitHub Actions builds the image and runs `helm upgrade --install search-api` into namespace `search` on cluster `platform-eks`, using the EKS access entry of role `search-ci-deployer`.
- **How does config reach prod?** Helm values in the same repo; data-layer settings via CloudFormation change sets.
- **Deploy frequency** — About weekly.
- **Lead time for changes** — Median 1 day.
- **Rollback procedure** — `helm rollback search-api <revision>`; runbook https://docs.example.com/search/runbooks/rollback. Last exercised 2026-03-30.
- **Deploy permissions** — CI role `arn:aws:iam::123456789012:role/search-ci-deployer`; humans in the `search-operators` group.
- **Incoming team's deploy role ARN** — `arn:aws:iam::123456789012:role/platform-team-eks`; EKS access entry created 2026-05-09 and mapped to `search-operators`.

### 4b — IaC & ownership

- **IaC tool and repo** — Helm chart `search-api` in `git.example.com/search/search-deploy` (`charts/search-api`). Data layer in CloudFormation, templates in `git.example.com/search/search-infra`.
- **Terraform state** — Not applicable (no Terraform).
- **Other provisioning tools** — CloudFormation: stack `search-data-stack` (ElastiCache `search-cache`, SQS `search-reindex-queue`, S3 `search-index-snapshots-123456789012`, secret `search/redis-auth`) and stack `search-iam-stack` (IRSA role `search-api-irsa`). Changes go through change sets, never console edits.
- **Kubernetes (if applicable)** — Cluster `platform-eks`, namespace `search`. The incoming team needs RoleBinding `search-operators` -> ClusterRole `edit` in namespace `search`. ServiceAccount `search/search-api` uses IRSA role `arn:aws:iam::123456789012:role/search-api-irsa`.

---

## 5. Alerting & on-call

- **Alarms configured** — `search-alb-5xx-rate`, `search-alb-p95-latency`, `search-reindex-queue-age` (oldest message > 900 s), `search-cache-cpu` (EngineCPUUtilization).
- **Paging path** — All four -> SNS `search-alerts` -> PagerDuty. The integration key lives in PagerDuty (owner Omar), not in AWS.
- **Known noisy alerts** — `search-cache-cpu` fires during the Sunday 01:00 UTC reindex.
- **Top runbook links** — 1. https://docs.example.com/search/runbooks/5xx-spike 2. https://docs.example.com/search/runbooks/reindex-stuck 3. https://docs.example.com/search/runbooks/rollback

## 6. Runbooks & incidents

- **Existing runbooks** — 1. 5xx spike — https://docs.example.com/search/runbooks/5xx-spike 2. Reindex stuck — https://docs.example.com/search/runbooks/reindex-stuck 3. Rollback — https://docs.example.com/search/runbooks/rollback
- **Incidents in last 12 months** — INC-2026-02-09, sev-2, Redis primary failover during a node patch; 22 minutes. Postmortem: https://docs.example.com/postmortems/2026-02-09
- **Recurring issues** — Reindex runs slow when the cache is under memory pressure.
- **Mean time to restore (MTTR)** — About 20 minutes.
- **Change failure rate** — 1 rollback in the last 25 deploys.

## 7. Known landmines

- **Fragile components** — The reindex job assumes `search-cache` is a 2-node group; do not scale it down.
- **"Do not touch on Friday" things** — Node group changes on `platform-eks`.
- **Undocumented quirks** — The ALB is created by the AWS Load Balancer Controller from the Ingress; deleting the Ingress deletes the ALB and its DNS name.
- **Pending tech debt** — Helm values are not validated against a schema.

## 8. Dependencies

- **Upstream callers** — 1. web-frontend (Web team, web@example.com), HTTPS via the ALB. 2. mobile-api (Mobile team, mobile@example.com), HTTPS via the ALB.
- **Downstream services** — 1. ElastiCache `search-cache` (Redis). 2. SQS `search-reindex-queue`. 3. S3 `search-index-snapshots-123456789012`.
- **External APIs** — None.
- **Shared infrastructure** — Cluster `platform-eks` (owned by Platform Team, shared with about 14 workloads).

## 9. Secrets & credentials

> **DO NOT write secret values in this document.** References only.

- **Secret stores in use** — AWS Secrets Manager `search/redis-auth`; Kubernetes Secret `search/search-api-env` (key name `REDIS_AUTH_TOKEN`, synced from the Secrets Manager secret).
- **Who owns rotation** — Search Team (Omar). Manual, yearly.
- **Services that read these secrets** — IRSA role `arn:aws:iam::123456789012:role/search-api-irsa`.
- **Last rotation dates** — `search/redis-auth`: 2026-01-15.

## 10. Compliance, data & disaster recovery

- **PII handling** — Search queries are free text and can contain personal data a customer typed. Query logs are the only place they land; no user identifiers are stored in Redis or S3.
- **Data retention policy** — Index snapshots 30 days (S3 lifecycle); query logs 14 days (log group retention).
- **Backup strategy** — ElastiCache daily snapshot, 7-day retention; S3 snapshot bucket versioned.
- **Last backup-restore test** — 2026-03-02: restored the latest snapshot into a scratch replication group, validated the index loads.
- **Disaster recovery plan** — Single-region (eu-west-1); rebuild from CloudFormation and Helm into eu-central-1 as documented. RTO 4 hours, RPO 24 hours (daily snapshot). Runbook: https://docs.example.com/search/dr-runbook
- **Regulatory constraints** — GDPR (short query-log retention is the control).

## 11. Roadmap & open work

- **Pending changes** — EKS upgrade to the next minor version in Q3 2026 (Platform Team).
- **Known deprecations** — None.
- **Open issues at handoff** — Helm values schema validation (Low).
- **One-quarter outlook** — Quiet; the cluster upgrade is the main change.

---

## For the incoming team — first-day reading checklist

- [ ] Confirm primary contact (Section 2) and have intro meeting scheduled.
- [ ] Confirm IaC repos, CloudFormation stacks and Kubernetes RBAC (Section 4b).
- [ ] Verify rollback procedure (Section 4) and the alert subscriptions (Section 5).
- [ ] Read the DR section (Section 10) and confirm RTO/RPO.
