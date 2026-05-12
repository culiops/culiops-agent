---
template-version: 1
emitted-by: service-takeover
service: payments
filled-by: Bob L., Carol P.
filled-date: 2026-05-10
---

# Outgoing-Team Interview — payments

**Outgoing team:** Pay Team (primary contact: Bob L. — bob@example.com)
**Incoming team:** Platform Team
**Handoff date:** 2026-06-15
**Filled in by:** Bob L. and Carol P. on 2026-05-10

---

## Why this document exists

This questionnaire captures the **tribal knowledge** about `payments` that doesn't live in the catalog or runtime profile — the things only the outgoing team knows. The incoming team will read this on day one.

---

## 1. Service overview

- **Business purpose** — what does this service do, from a non-technical standpoint?
  Processes payment authorization and capture for the e-commerce checkout flow. Every purchase on the storefront goes through this service. It talks to Stripe on the outbound side and receives requests from the checkout-service on the inbound side.

- **Criticality tier** — what happens if it's down for 1 hour? 1 day?
  Tier 0 — revenue-critical. One hour of downtime = ~$50k in lost GMV based on peak-hour rates. One day = complete checkout blackout. PagerDuty P1 on any error-rate spike above 0.5%.

- **Age** — when was this service created? Major architectural eras?
  Created 2021-03. Originally a Node.js monolith running on EC2 (2021-03 to 2022-09). Migrated to Lambda + SQS architecture in 2022-10 when traffic outgrew the single EC2 instance. DynamoDB replaced RDS in 2023-06 to eliminate connection-pool exhaustion during flash sales.

- **Why it exists** — what was the motivating problem? Is that problem still current?
  The original motivation was to isolate payment logic from the checkout monolith for PCI DSS compliance. That isolation requirement is still current and growing — the compliance audit in Q1 2026 confirmed it.

---

## 2. People & ownership

- **Current owners** — names + roles + GitHub/Slack handles.
  Bob L. (tech lead, @bobL on GitHub, @bob on Slack), Carol P. (SRE, @carolP on GitHub, @carol on Slack). Bob owns architecture decisions; Carol owns operational runbooks and on-call rotation.

- **On-call schedule** — rotation tool, cadence, current on-call.
  PagerDuty rotation, weekly handoff Monday 10am UTC. Current on-call: Bob. Rotation includes Bob, Carol, and Dan K. (backup). Escalation to eng-manager Priya M. after 15 min no-ack.

- **Escalation contacts** — who do you call when the primary on-call doesn't answer?
  1. Dan K. (dan@example.com) — secondary on-call. 2. Priya M. (priya@example.com) — engineering manager. 3. Stripe support (support.stripe.com) for Stripe-side incidents. 4. AWS Support (Business tier, case URL in PagerDuty runbook).

- **Related teams** — teams that depend on or interact with this service.
  Checkout team (upstream caller), Billing team (status queries), Notifications team (event consumer), Fraud Detection team (SQS consumer before authorization).

---

## 3. SLOs / SLIs

- **Defined SLOs** — list each SLO. If none, say so.
  SLO-1: Authorization success rate ≥ 99.5% over any rolling 30-day window (excludes Stripe-side failures).
  SLO-2: p99 authorization latency ≤ 500ms over any rolling 7-day window.
  SLO-3: Capture queue age-of-oldest-message ≤ 60s over any rolling 24h window.

- **SLI implementations** — which metrics measure each SLO? Where are they computed?
  SLO-1: CloudWatch custom metric `PaymentsAuthorizationSuccessRate` emitted by payments-authorizer Lambda; 5-min aggregation window. Dashboard: https://us-east-1.console.aws.amazon.com/cloudwatch/home#dashboards:name=payments-slo
  SLO-2: Lambda Duration p99 from CloudWatch namespace AWS/Lambda, dimension FunctionName=payments-authorizer.
  SLO-3: SQS ApproximateAgeOfOldestMessage for payments-capture-queue.

- **Error budget tracking** — is the error budget monitored? When was it last burned?
  Yes. Error budget is tracked weekly in the team's Friday review doc. Last burn-down was 2026-03-12 (INC-2026-03-12, see Section 6) — consumed ~40% of the 30-day authorization SLO budget.

- **Dashboards** — paths/URLs to operational dashboards.
  Main SLO dashboard: https://us-east-1.console.aws.amazon.com/cloudwatch/home#dashboards:name=payments-slo
  Detailed ops dashboard: https://us-east-1.console.aws.amazon.com/cloudwatch/home#dashboards:name=payments-ops
  Cost dashboard: https://us-east-1.console.aws.amazon.com/cost-management/home#/custom

---

## 4. Deploy process

- **How does code reach prod?** CI/CD tool, deploy script, manual steps.
  GitHub Actions. PR merge to `main` triggers `.github/workflows/deploy.yml`. The workflow runs tests, builds a zip artifact, uploads to S3, then calls `aws lambda update-function-code` for each of the three functions. Full pipeline takes ~8 minutes.

- **How does config reach prod?** Same as code? Separate path?
  Environment variables are managed via `aws lambda update-function-configuration` in the same deploy pipeline. Secrets in Secrets Manager are updated manually by Carol or Bob using the AWS console (never committed to git). IaC for config is on the roadmap (Q3 2026, see Section 11).

- **Deploy frequency** — deploys per day/week/month.
  3-5 deploys per week (DORA: deploy frequency ~4/week averaged over last quarter). Peaks at 8-10/week during feature sprints.

- **Lead time for changes** — from commit to prod.
  Median 45 minutes (commit → PR review → merge → deploy pipeline). P95 is 3 hours (waiting for review). DORA: lead time for changes = medium.

- **Rollback procedure** — exact steps. When was rollback last exercised?
  GitHub Actions `revert-and-redeploy` workflow. Trigger: go to Actions tab, run `revert-and-redeploy`, paste the SHA to roll back to, click Run. The workflow fetches the previously deployed artifact from S3 and re-deploys all three Lambdas. Last tested 2026-04-22 during a drill — took 4 minutes end-to-end.

- **Deploy permissions** — who can deploy? IAM role / user list.
  `arn:aws:iam::123456789012:role/payments-deploy-role` (assumed by GitHub Actions OIDC). Humans: Bob and Carol can trigger the workflow. Platform Team's `arn:aws:iam::123456789012:role/platform-team-deploy` will need to be added before handoff date — action item tracked in Section 11.

---

## 5. Alerting & on-call

- **Alarms configured** — list critical alarms.
  1. `payments-auth-error-rate-high` — CloudWatch alarm on PaymentsAuthorizationSuccessRate < 99.5% for 5 minutes. Severity P1.
  2. `payments-capture-queue-depth` — SQS ApproximateNumberOfMessagesVisible > 500 for 10 minutes. Severity P2.
  3. `payments-dlq-messages` — SQS payments-capture-dlq ApproximateNumberOfMessages > 0. Severity P1.
  4. `payments-lambda-errors` — Lambda Errors > 10 in 5 minutes for any payments-* function. Severity P2.
  5. `payments-latency-p99` — Lambda Duration p99 > 500ms for 10 minutes. Severity P2.

- **Paging path** — which alarms page, where, with what severity.
  All five alarms send to PagerDuty via CloudWatch → SNS → PagerDuty integration (service key in Secrets Manager payments/pagerduty-key). P1 alarms wake on-call immediately. P2 alarms send urgent notification with 30-min escalation.

- **Known noisy alerts** — alarms that fire often but aren't actionable.
  `payments-latency-p99` occasionally fires during AWS Lambda cold-starts (typically on Sunday mornings when traffic drops to near-zero overnight and the first Monday requests hit cold containers). Filed to move to provisioned concurrency — not yet done.

- **Top runbook links** — top 3-5 runbooks.
  1. Authorization error spike: https://docs.example.com/payments/runbooks/auth-error-spike
  2. Capture queue backup: https://docs.example.com/payments/runbooks/capture-queue-backup
  3. DLQ triage: https://docs.example.com/payments/runbooks/dlq-triage
  4. Stripe API degradation: https://docs.example.com/payments/runbooks/stripe-degradation
  5. Rollback procedure: https://docs.example.com/payments/runbooks/rollback

---

## 6. Runbooks & incidents

- **Existing runbooks** — all known runbooks.
  1. Authorization error spike — https://docs.example.com/payments/runbooks/auth-error-spike — diagnose and mitigate >1% auth failure rate
  2. Capture queue backup — https://docs.example.com/payments/runbooks/capture-queue-backup — clear message backlog, handle DLQ overflow
  3. DLQ triage — https://docs.example.com/payments/runbooks/dlq-triage — inspect, replay or discard DLQ messages
  4. Stripe API degradation — https://docs.example.com/payments/runbooks/stripe-degradation — detect Stripe-side issues, enable graceful degradation
  5. Rollback procedure — https://docs.example.com/payments/runbooks/rollback — step-by-step rollback using GitHub Actions revert workflow

- **Incidents in last 12 months** — date, severity, root cause, postmortem.
  INC-2026-03-12 — 2026-03-12, sev-2, payment timeout cascade caused by Stripe API latency spike → payments-authorizer Lambda hitting 10s timeout → DLQ fill → capture queue backup. Duration: 47 minutes. Postmortem: https://docs.example.com/postmortems/2026-03-12
  INC-2025-11-28 — 2025-11-28 (Black Friday), sev-3, Lambda throttling during flash sale; added reserved concurrency. Duration: 12 minutes. Postmortem: https://docs.example.com/postmortems/2025-11-28

- **Recurring issues** — patterns that come back periodically.
  1. Cold-start latency spike on Monday mornings — known, provisioned concurrency fix on roadmap.
  2. Stripe API rate limiting during end-of-month settlement batch — Carol added retry with exponential backoff in 2025-09, has not recurred since.

- **Mean time to restore (MTTR)** — typical recovery time for sev-1.
  ~25 minutes based on the two incidents above (47 min and 12 min). Target SLO is <30 min. DORA: MTTR = medium.

- **Change failure rate** — % of deploys causing user-visible degradation.
  1 incident in ~80 deploys over the last 6 months = ~1.25%. DORA: change failure rate = low. The 2026-03-12 incident was not deploy-caused; actual code-deploy failures = 0.

---

## 7. Known landmines

- **Fragile components** — things that break easily.
  The Stripe webhook signature verification in payments-authorizer is fragile — it requires the raw request body before any JSON parsing. If an API Gateway config change alters payload encoding, signature verification silently fails and all webhooks are rejected. Carol has a runbook for this (auth-error-spike).

- **"Do not touch on Friday" things** — actions known to cause incidents.
  Never change the DynamoDB payments-ledger table schema (add/remove GSI, change billing mode) during business hours. DynamoDB schema changes on provisioned tables block reads for up to 90 seconds. Always do these during the Friday 22:00 UTC maintenance window.

- **Undocumented quirks** — surprising behavior, workarounds, hacks.
  1. The reconciler Lambda has a hardcoded `sleep(30)` at startup (line 42 in reconciler/index.py) — this was added to wait for DynamoDB writes to propagate after a deployment but was never removed. It is safe to remove but has not been prioritized.
  2. SQS batch size is set to 1 for payments-capture for debugging traceability — this limits throughput. Can be raised to 10 without code changes but hasn't been tested at scale.

- **Pending tech debt** — known issues queued up to fix.
  1. No IaC — all resources were created by hand. IaC migration is Q3 2026 roadmap.
  2. Provisioned concurrency not configured — cold starts a known pain.
  3. SQS batch size = 1 limits throughput.
  4. API Gateway access logs not enabled.

---

## 8. Dependencies

- **Upstream callers** — services that call this one.
  1. checkout-service — Checkout Team (lead: Maria R., maria@example.com), HTTPS REST via API Gateway, SLA: 99.9% availability, contract: informal agreement in Confluence.
  2. billing-service — Billing Team (lead: Tom S., tom@example.com), HTTPS REST GET /status/{id} only (read-only), no SLA documented.

- **Downstream services** — services this one calls.
  1. Stripe API — external, payments/stripe-api-key in Secrets Manager, HTTPS REST, rate limit 100 req/s on our tier, vendor contact: account manager Sarah at Stripe (sarah@stripe.com), billing impact: ~$4/month (already in spend profile).
  2. fraud-detection — Fraud Team (lead: Ying L., ying@example.com), SQS async, SLA: best-effort (fraud check can be skipped if queue lag > 2s — implemented in authorizer).
  3. notifications-service — Notifications Team (lead: Alex G., alex@example.com), SNS publish-only, SLA: best-effort (failure logged, not retried).

- **External APIs** — third-party APIs used.
  Stripe Payments API (api.stripe.com). Vendor: Stripe Inc. Contract owner: Bob L. (renewal due 2027-03). Billing impact: see spend profile (~$4/month). Rate limit: 100 req/s on current plan. Stripe status page: https://status.stripe.com.

- **Shared infrastructure** — clusters, VPCs, accounts shared with other services.
  Shared prod-main VPC (vpc-abc123) in us-east-1 with all other microservices. The payments Lambdas run inside this VPC for DynamoDB access. No dedicated cluster. NAT Gateway egress shared with ~12 other services — contention not observed but worth monitoring.

---

## 9. Secrets & credentials

> **DO NOT write secret values in this document.** References only.

- **Secret stores in use** — AWS Secrets Manager paths.
  All secrets in AWS Secrets Manager in us-east-1:
  - `payments/stripe-api-key` — Stripe secret key
  - `payments/db-encryption-key` — KMS CMK ARN for DynamoDB encryption
  - `payments/pagerduty-key` — PagerDuty integration key for CloudWatch → SNS alarm routing

- **Who owns rotation** — team responsible for rotating each secret.
  `payments/stripe-api-key`: Pay Team (Bob). Rotated manually when Stripe API keys are cycled. Last rotated 2025-12-01. No auto-rotation configured (Stripe keys require code-side update). Platform Team will own after handoff.
  `payments/db-encryption-key`: KMS auto-rotation enabled (annual). No manual action required.
  `payments/pagerduty-key`: Pay Team (Carol). Rotate if PagerDuty integration is re-keyed.

- **Services that read these secrets** — IAM principals.
  `arn:aws:iam::123456789012:role/payments-lambda-exec` — reads all three secrets at Lambda cold start.
  `arn:aws:iam::123456789012:user/alice` — console read access for debugging (should be removed post-handoff).

- **Last rotation dates** — when secrets were last rotated.
  `payments/stripe-api-key`: 2025-12-01.
  `payments/db-encryption-key`: KMS auto-rotation; last key material rotation 2025-11-15 (KMS console).
  `payments/pagerduty-key`: 2025-08-20 (after PagerDuty service re-key for compliance audit).

---

## 10. Compliance, data & disaster recovery

- **PII handling** — does this service handle PII? What kind? How is it protected?
  Yes. The payments-ledger DynamoDB table stores: customer_id (UUID, not name/email), masked card last-4 (4 digits only), transaction amounts, timestamps. Full card numbers and CVVs are never stored — Stripe tokenizes before our service receives them. PII fields are encrypted at rest via KMS CMK (payments/db-encryption-key). Data subject deletion: legal hold prevents purge until 7-year accounting retention window expires.

- **Data retention policy** — how long is data kept? Auto-purge schedules?
  Transaction records retained 7 years per financial regulation. TTL attribute `expires_at` set on records to auto-expire after 7 years + 90 day grace. Currently ~3.2M records in the table; oldest records will begin expiring 2028-03.

- **Backup strategy** — what's backed up, how often, where, retention.
  DynamoDB PITR (Point-In-Time Recovery) enabled on payments-ledger table — continuous backup, 35-day restore window. No additional snapshots taken (PITR considered sufficient for the RTO/RPO targets). Backup region: us-east-1 only (cross-region backup not enabled).

- **Last backup-restore test** — when was a restore last successfully tested?
  2026-02-15. Carol restored a 24-hour-old snapshot to a test table (`payments-ledger-restore-test`) and validated record counts and a sample of 50 random transactions. Test table deleted after validation. Restore took 18 minutes for ~3M records.

- **Disaster recovery plan** — RTO, RPO, DR runbook.
  Active-passive failover to us-west-2. RTO 30 minutes, RPO 5 minutes (PITR continuous backup lag). DR runbook: https://docs.example.com/payments/dr-runbook. Last DR drill: 2025-11-01 (full failover test, succeeded in 28 minutes).

- **Regulatory constraints** — SOC2, HIPAA, GDPR, PCI, etc.
  PCI DSS SAQ A-EP (we use Stripe.js for card capture; our service handles post-tokenization). Annual external audit. SOC2 Type II — included in company-wide audit scope. GDPR: EU customers' transaction records are subject to right-to-erasure (7-year legal hold overrides until expiry). No HIPAA applicability.

---

## 11. Roadmap & open work

- **Pending changes** — in-flight projects affecting this service.
  1. IaC migration (Terraform) — Q3 2026. Carol is leading. Will touch all 8 resources. Platform Team should be involved in review.
  2. Provisioned concurrency rollout — Q2 2026, Bob. Mitigates Monday cold-start issue.
  3. SQS batch-size tuning (1 → 10) — Q2 2026, Dan. Low risk, pending load test.

- **Known deprecations** — components scheduled to be replaced/removed.
  API Gateway REST API will be migrated to HTTP API in Q4 2026 (cost reduction + lower latency). No user-visible change expected.

- **Open issues at handoff** — bugs, work items, P0s carrying over.
  1. [Medium] Provisioned concurrency not yet configured — cold-start latency risk on low-traffic periods.
  2. [Low] reconciler sleep(30) hardcoded — safe to remove, not yet prioritized.
  3. [Action item] Platform Team IAM role (`platform-team-deploy`) needs to be added to deploy permissions before 2026-06-15 handoff date.
  4. [Action item] alice's console read access to Secrets Manager should be revoked after handoff.

- **One-quarter outlook** — what does the incoming team need to know about next 3 months?
  IaC migration kicks off in Q3 — the Platform Team will be asked to review Terraform modules for all 8 resources. This will be the biggest structural change to the service in 2 years. The Stripe contract renewal is due 2027-03 (not urgent). Keep an eye on the Monday cold-start alarm until provisioned concurrency is rolled out.

---

## For the incoming team — first-day reading checklist

After reading this questionnaire:

- [ ] Confirm primary contact (Section 2) and have intro meeting scheduled.
- [ ] Verify access to dashboards listed in Section 3.
- [ ] Verify rollback procedure (Section 4) is understood — schedule a test.
- [ ] Subscribe to alerts (Section 5) on your phones / paging tool.
- [ ] Read top-3 runbooks (Section 6) and the most recent postmortem.
- [ ] Note the landmines (Section 7) — surface them in team standup before any change.
- [ ] Map dependencies (Section 8) and introduce yourselves to upstream/downstream owners.
- [ ] Verify secret-store access (Section 9) for the incoming team's IAM identities.
- [ ] Read compliance/DR section (Section 10) — confirm RTO/RPO are met by current infra.
- [ ] Review roadmap (Section 11) and decide which items the new team will continue.
