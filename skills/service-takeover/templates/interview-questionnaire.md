---
template-version: 1
emitted-by: service-takeover
---

# Outgoing-Team Interview — <service-name>

**Outgoing team:** <team-name> (primary contact: <name> <email>)
**Incoming team:** <team-name>
**Handoff date:** <date>
**Filled in by:** <name(s)> on <date(s)>

---

## Why this document exists

This questionnaire captures the **tribal knowledge** about `<service-name>` that doesn't live in the catalog or runtime profile — the things only the outgoing team knows. The incoming team will read this on day one. Please be honest about gaps; "unknown" or "no SLO defined" is more useful than guesses.

Fill in answers under each `_To be filled in: ___` marker. Sections may be answered async; no synchronous meeting is required. The incoming team will follow up on partial sections after reading the first pass.

---

## 1. Service overview

- **Business purpose** — what does this service do, from a non-technical standpoint?
  _To be filled in: ___
- **Criticality tier** — what happens if it's down for 1 hour? 1 day? (Tier 0 / 1 / 2 / 3 if your org uses tiers)
  _To be filled in: ___
- **Age** — when was this service created? Major architectural eras?
  _To be filled in: ___
- **Why it exists** — what was the motivating problem? Is that problem still current?
  _To be filled in: ___

## 2. People & ownership

- **Current owners** — names + roles + GitHub/Slack handles.
  _To be filled in: ___
- **On-call schedule** — rotation tool (PagerDuty / Opsgenie / etc.), rotation cadence, current on-call.
  _To be filled in: ___
- **Escalation contacts** — who do you call when the primary on-call doesn't answer?
  _To be filled in: ___
- **Related teams** — teams that depend on or interact with this service.
  _To be filled in: ___

## 3. SLOs / SLIs

- **Defined SLOs** — list each SLO (e.g., "99.9% availability over 30 days"). If none, say so.
  _To be filled in: ___
- **SLI implementations** — which metrics measure each SLO? Where are they computed?
  _To be filled in: ___
- **Error budget tracking** — is the error budget monitored? When was it last burned?
  _To be filled in: ___
- **Dashboards** — paths/URLs to operational dashboards.
  _To be filled in: ___

## 4. Deploy process

- **How does code reach prod?** CI/CD tool, deploy script, manual steps.
  _To be filled in: ___
- **How does config reach prod?** Same as code? Separate path?
  _To be filled in: ___
- **Deploy frequency** — deploys per day/week/month (DORA: deploy frequency).
  _To be filled in: ___
- **Lead time for changes** — from commit to prod (DORA: lead time).
  _To be filled in: ___
- **Rollback procedure** — exact steps. When was rollback last exercised?
  _To be filled in: ___
- **Deploy permissions** — who can deploy? IAM role / user list.
  _To be filled in: ___

## 5. Alerting & on-call

- **Alarms configured** — list critical alarms (CloudWatch / PagerDuty / Prometheus).
  _To be filled in: ___
- **Paging path** — which alarms page, where, with what severity.
  _To be filled in: ___
- **Known noisy alerts** — alarms that fire often but aren't actionable.
  _To be filled in: ___
- **Top runbook links** — paths/URLs to the top 3–5 runbooks (full list goes in Section 6).
  _To be filled in: ___

## 6. Runbooks & incidents

- **Existing runbooks** — list all known runbooks with paths/URLs and a one-line description.
  _To be filled in: ___
- **Incidents in last 12 months** — list each incident with date, severity, root cause, postmortem link.
  _To be filled in: ___
- **Recurring issues** — patterns of failure that come back periodically.
  _To be filled in: ___
- **Mean time to restore (MTTR)** — typical recovery time for sev-1 incidents (DORA: MTTR).
  _To be filled in: ___
- **Change failure rate** — what % of deploys cause user-visible degradation (DORA: change failure rate)?
  _To be filled in: ___

## 7. Known landmines

- **Fragile components** — things that break easily; treat carefully.
  _To be filled in: ___
- **"Do not touch on Friday" things** — actions known to cause incidents.
  _To be filled in: ___
- **Undocumented quirks** — surprising behavior, workarounds, hacks.
  _To be filled in: ___
- **Pending tech debt** — known issues queued up to fix.
  _To be filled in: ___

## 8. Dependencies

- **Upstream callers** — services that call this one. Names, owning teams, contacts, contract/SLA.
  _To be filled in: ___
- **Downstream services** — services this one calls. Names, owning teams, contracts/SLAs.
  _To be filled in: ___
- **External APIs** — third-party APIs used. Vendor, contract owner, billing impact, rate limits.
  _To be filled in: ___
- **Shared infrastructure** — clusters, VPCs, accounts shared with other services. Ownership / contention notes.
  _To be filled in: ___

## 9. Secrets & credentials

> **DO NOT write secret values in this document.** Write **references** (where they live, who manages rotation, which services can read).

- **Secret stores in use** — AWS Secrets Manager / SSM Parameter Store / HashiCorp Vault / etc.
  _To be filled in: ___
- **Who owns rotation** — team responsible for rotating each secret class.
  _To be filled in: ___
- **Services that read these secrets** — which IAM principals or service identities.
  _To be filled in: ___
- **Last rotation dates** — when secrets were last rotated (if known).
  _To be filled in: ___

## 10. Compliance, data & disaster recovery

- **PII handling** — does this service handle personally identifiable information? What kind? How is it protected?
  _To be filled in: ___
- **Data retention policy** — how long is data kept? Auto-purge schedules?
  _To be filled in: ___
- **Backup strategy** — what's backed up, how often, where, retention.
  _To be filled in: ___
- **Last backup-restore test** — when was a restore last successfully tested?
  _To be filled in: ___
- **Disaster recovery plan** — RTO (recovery time objective), RPO (recovery point objective), DR runbook path.
  _To be filled in: ___
- **Regulatory constraints** — SOC2, HIPAA, GDPR, PCI, etc., if applicable.
  _To be filled in: ___

## 11. Roadmap & open work

- **Pending changes** — in-flight projects affecting this service.
  _To be filled in: ___
- **Known deprecations** — components scheduled to be replaced/removed.
  _To be filled in: ___
- **Open issues at handoff** — bugs, work items, P0s carrying over.
  _To be filled in: ___
- **One-quarter outlook** — what does the incoming team need to know about the next 3 months?
  _To be filled in: ___

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
