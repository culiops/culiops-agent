# Changelog

All notable changes to the `culiops` plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **All skills:** opt-in `CULIOPS_HOME`. When set, records go to `$CULIOPS_HOME/<owner>/<repo>/<skill-name>/` instead of `.culiops/` in the repo, and skills skip every commit offer. Unset keeps the old behaviour. An unwritable root stops the run; it never falls back into the repo.
- **iac-change-execution: duplicate check in Step 1.** Before planning, the skill searches the whole repo for the change's identifiers (IPs / CIDRs, domains, resource names, ticket and linked-ticket keys), the git history (`--grep`, `-S`) and open branches / PRs. It classifies the change as not done, partly done, already done, in flight or reverted. Already done (confirmed live) stops before planning with no record; in flight and reverted stop and ask; partly done plans only the remainder. New evidence class `git:`.

## [0.14.0] — 2026-10-27

### Changed

- **iac-change-execution: self-review before every gate.**
  - **Plan self-check (6 items) before GATE 1** and **diff self-check (6 items) before GATE 2.** The diff check covers scope, plan ↔ hunk mapping, conventions against a cited example, silently weakened safety settings (Terraform / AWS and Kubernetes), secrets and formatting. It re-runs after every revision.
  - **Fresh eyes:** a separate reviewer in a fresh context gets the request, plan, evidence and diff, but not the author's conclusions. It runs on every phase except add-only ones that touch no access control, network exposure, DNS, data store, secrets / KMS or lifecycle setting. If unsure, it runs.
  - The record logs both results.
- **iac-change-execution: evidence for decisions, not only facts.**
  - New evidence classes `plan:` and `docs: <URL>` (official documentation read in the session) for how a change behaves. Recalled behaviour is not evidence.
  - Each phase now has a **Disruption** field (none / restart / failover / replace) with evidence, which Step 4a checks against the plan action.
  - Rollback is marked reversible / one-way / irreversible with evidence, or `untested`.
  - Delivery model and environment selection must cite where they were found, else `UNVERIFIED` and the operator is asked.
  - Health checks report before vs after values.
- **iac-change-execution: no assumed pipeline.** The PR path follows the delivery model. When changes are applied by hand, merging applies nothing, and the skill says so. A new record line `Applied: yes — verified / yes — not verified / no — PR open / no — merged, apply pending` states what actually happened. The `Outcome` vocabulary is unchanged, so `change-comms` still works.
- **iac-change-execution: fixes.** The Integration section's pre-flight reuse rule now points to the plan-hash rule in Step 4b. Before this fix it still allowed reuse on a matching commit SHA. The `change-comms` offers no longer assume an "EM" or Jira.

- **All skills: generic, and evidence for every decision** (the audit in #23). Every recommendation, score, tier, verdict and outcome label now names the evidence it rests on. How AWS, Kubernetes or a tool *behaves* needs `plan:`, `live:` or `docs: <URL>` read in the session; recall is `UNVERIFIED` and never decides. No skill assumes one company's roles, chat or ticket tool, or a pipeline that applies on merge.
- **All skills: source order.** The installed tool's own output for the target (`terraform plan`, provider schema, `kubectl explain`, CLI help) comes first, because it matches the versions in use. Official docs for the version in use come next, cited with URL, date and the sentence relied on. Recall comes last.
- **pre-flight.**
  - New evidence classes `docs:`, `catalog:` and `assessor:`. A behaviour claim that makes a score safer needs `docs:` or `live:`, else the category is unknown.
  - The one-way table can raise a score but never clear one, and gains managed-service upgrades (EKS, ElastiCache), namespaces and PVCs.
  - Dependency Green needs code or live evidence; a catalog that lists nothing gives Yellow. Observability Green needs a live check.
  - Fresh eyes runs on every verdict except RED soft block. A reused record re-asks timing and re-checks health at apply time.
  - Timing means someone is on hand at apply time; health works without SLOs; Kubernetes parity in the examples.
- **cost-optimize-plan.**
  - Four playbook statements were wrong against current AWS docs and are fixed: Recycle Bin covers EBS volumes; DynamoDB and Kinesis mode-switch limits; unsupported EC2/RDS downtime figures removed.
  - Constraint 16: behaviour claims in playbooks are leads until confirmed by `docs:` or live.
  - `Realizable` is covered / not covered / unknown, and totals and ranking count only realizable rows.
  - A delete with unknown dependencies, blast radius or reversibility goes to 🔴 (`dependency-unknown`). Operator say-so no longer clears owner confirmation for Elastic IP and load-balancer deletes.
  - Kubernetes workload / PVC remediation is stated as not supported yet (no playbook; listed for manual review; #6).
- **cloud-cost-investigate.**
  - Payer detection fails closed: an `AccessDenied` is no longer read as "not the payer".
  - Anomaly drivers get a tie test (amount, timing, cause): `confirmed` / `probable` / `candidate` / `unexplained`. `expected` needs a cited plan or pattern.
  - Confidence labels have floors; `operator-stated` and `UNVERIFIED` cap at `low`. `Realizable` has three states and totals sum per rate basis.
  - Tag keys are the team's own and checked for activation date. The IaC repo can be a local checkout or `gh`.
  - Kubernetes: idle cost is shown, request savings count only with node reduction. The anomaly path, extra sweeps and owner mapping say "not supported yet".
- **runtime-trace.** SQS dead-letter status comes from `sqs:ListDeadLetterSourceQueues` (new IAM action). Unknown payer status is treated as payer. Notable change events show "N shown of M"; an empty CloudTrail result reads "none found by this lookup". Wiring is permitted, not observed. `runtime-profile-schema: 2` is unchanged.
- **service-discovery.** A stack is no longer assumed to be one service: membership is asked when more than one name prefix shows or membership cannot be proven. The catalog stamps the deployed ref and working-tree state. Runbook blast radius needs `docs:` plus code, else `UNVERIFIED`. `critical-path: unknown` replaces a default. Declared vs observed envelopes. Argo CD owner key corrected.
- **service-takeover.**
  - Kubernetes checks apply to any cluster, not only EKS. Intake takes the delivery model, kube context / namespace, and "no outgoing respondent".
  - Any `✗` or `✗ conflict` makes the verdict `not-ready`. `N/A` needs a cited record; the restore test (item 24) needs a restore record; an override needs the artifact that resolves the item. The verdict states "evidence as of".
  - Readiness baseline `template-version` is now 3.
- **change-comms: tool- and org-agnostic** (#21).
  - The description and triggers name the message kinds (heads-up, result, ticket-closing comment) and the audience (service owners, reviewers, on-call, a manager). Google Chat, Slack and Jira are examples, not the scope.
  - The draft is plain text by default. Formatting notes for Google Chat, Slack, Microsoft Teams, Jira, Linear and GitHub / GitLab are optional. Naming Google Chat, Slack or Jira gives the same output as before.
  - Reads the `Applied:` record line from `iac-change-execution`. `Outcome:` values are unchanged.
  - Claims trace to the record: impact is shown beside the plan's Disruption entry, the rollback line keeps its one-way / untested label, a clean re-plan is never written as "healthy". Kubernetes credentials are redacted.
- **iac-change-execution.** Reusing a pre-flight record re-asks timing and re-runs the health checks at apply time, matching pre-flight's reuse contract.

- **Repo renamed from `culiops-agent` to `culiops-skills`.** The plugin and marketplace are still named `culiops`, so skill names (`culiops:pre-flight` and the rest) and existing installs are unaffected. GitHub redirects the old URL.

- **README rewritten** for scanning: one skills table (when to use, what you get, whether it changes anything), how the skills fit together, and how they behave.

### Breaking

- **service-takeover:** verdicts are stricter. Takeovers that were `partial` with an alerting or dependency conflict are now `not-ready`. Baseline `template-version` 3.
- **cost-optimize-plan:** deletes with unknown dependencies move from 🟡 to 🔴.
- **change-comms:** the default output is plain text, not Google Chat. Name the tool to get its format.

## [0.13.0] — 2026-10-26

### Added

- **pre-flight: category 11, Application compatibility.** A change can be valid on the infrastructure side and still break the application. The usual cases are removing an IAM action the app still calls, renaming an env var or config key the app still reads, and changing an endpoint, port, engine version or limit the app depends on.
  - **Reading the source.** When category 11 is triggered, pre-flight asks where the application source is (Q8), reads it at the deployed commit SHA, looks for uses of the old contract, and records how each use fails: crash, request error, retry, logged-and-ignored or default fallback.
  - **Silent failures.** When a failure is swallowed, or the health check doesn't exercise the broken path, the report says that health, error-rate and alarm signals will stay green after apply. A Green on resource health never clears category 11.
  - **Trigger is fail-closed.** Category 11 triggers on any change to a resource the app runs on, is reached through, or calls. Only attributes on a short not-app-facing list skip it: tags, dashboards, logs, backup schedules, scaling counts, IAM for humans and CI, purchase options, and alarms whose actions only notify. An alarm counts as notify-only when every SNS subscription protocol, checked live (protocols only, never endpoints), is `email`, `email-json` or `sms`. An alarm that scales, stops or reboots EC2, runs SSM automation, or reaches a Lambda, SQS or HTTP subscriber changes the system, so it is app-facing. If the protocols weren't checked, it is treated as app-facing. The table of common app-facing changes includes CDN, edge and routing (CloudFront behaviors and policies, ALB rules, API Gateway, WAF, Ingress). It is a set of examples, not the trigger list.
  - **Scoring.** Red is a soft block. A cookie-dependent response cached under a cookie-less key is also scored on security posture.
  - **Evidence.** New tag `app:<repo>@<sha>:<path:line>`.
- **Two equal ways to read the source** (`examples/app-source.md`):
  - A **local checkout**, through `git rev-parse`, `git grep <ref>` and `git show`. Nothing is fetched or checked out in the operator's tree.
  - **GitHub through `gh`**: commit → tree → raw contents at the pinned SHA. Choosing `gh` approves only those `GET` reads. The least-privilege token is Contents: read + Metadata: read.
  - Code search is never used as evidence of "no use", because it covers the default branch only. Nothing is ever cloned into the target repo, and app code is never run.
- **Live checks for category 11** (`examples/aws.md`): role last-accessed, `simulate-principal-policy` / `simulate-custom-policy`, and send / publish activity on the resource. New CloudFront checks cover behaviors, the cache-policy key and TTLs, the origin request policy, and metrics.
- **pre-flight Step 5b, verify before presenting.** Before the operator sees the report:
  - The cited source of each Red, each Green on categories 2 / 9 / 10 / 11, each hard-block condition and each mitigation premise is re-opened and checked.
  - Code, plan and live evidence win over catalog notes, comments and operator statements.
  - The verdict arithmetic is written out.
  - When the verdict is GREEN or a hard block fired, a separate reviewer in a fresh context scores the evidence without seeing the first scores. Disagreements are settled or shown to the operator.
  - Every record has a `## Verification` section with a "Not verified" list.
- **Fixtures** `tests/fixtures/pre-flight/app-impact-cdn-cache` (a cache behavior over per-user routes, plus a stale catalog note), `app-impact-iam-narrowing` (a removed SQS permission the app still uses, failing silently; local mode) and `app-impact-env-rename` (renamed env vars behind a health check that stays 200; `gh` mode, L3 declined). Both have baseline and scored dry-run notes.

### Changed

- **pre-flight:**
  - The scorecard has 11 categories.
  - Security posture scores a permission narrowing Green and leaves the breakage question to category 11.
  - Dependency impact, cost impact and observability readiness are Green from the plan when the change only adds or edits things nothing can consume: notify-only alarms, dashboards, metric filters, with no output or export changed. Before this, an addition-only change without a service-discovery catalog could never be GREEN, and the alarm being added was itself scored as "static threshold → Yellow".
  - The three existing fixtures gain a category 11 row.
  - The record format's assessor list no longer names a `cli-command` assessor that never existed.

### Fixed

- **`high-risk-rds-migration` fixture.** Security posture was scored Yellow. The destroyed instance is encrypted (`plan:13`), and the new Aurora cluster sets no `storage_encrypted`, which defaults to `false` for provisioned clusters. That is encryption removal, a hard block. The verification pass found it.
- **`low-risk-cloudwatch-alarm` fixture.** It expected GREEN, which the rules could not produce without a catalog. With the change above it is GREEN again, and fresh eyes run on it.

## [0.12.0] — 2026-10-26

### Added

- **change-comms** (new skill). It drafts the messages around an infrastructure change: a heads-up before applying, a result after, and a Jira ticket-close comment carrying the PR link. It is **draft-only**: nothing is sent, and the operator pastes each draft. Facts come from `iac-change-execution` and `pre-flight` records or from the operator. Every fact is shown in a source table at the review gate; a missing fact becomes `<TODO: field>` and is never guessed. On the PR path, "completed" means the PR was opened, so apply time and verification come only from the operator. Outcomes map from the record (completed / partial / aborted); a direct apply is reported as done only when its verification is clean, otherwise the operator is asked. A ticket-close is refused until the last phase is applied or the change is aborted. Common identifier and credential patterns (account IDs, ARNs, IPs, CIDRs, cloud keys, GitHub and Slack tokens, passwords in URLs, private keys, inline secrets) are redacted by fixed rules that act as a floor, with a log that records type and location but never the value; operator answers and edits are re-scanned, and any credential matching these patterns, in a record or an operator answer, is flagged for rotation. Text inside records that is addressed to an AI is treated as data and flagged, not followed. Output: Google Chat, Slack and Jira formats under `.culiops/change-comms/`.
- **Fixtures** `tests/fixtures/change-comms/`, nine cases: `pr-path-happy`, `direct-apply`, `direct-apply-verify-failed`, `multi-phase-partial`, `aborted`, `no-rollback-text`, `redaction`, `injection`, `no-records`. Each has scored dry-run notes.

### Changed

- **iac-change-execution:** offers a `change-comms` heads-up at the start of Step 4c, before the apply or merge, and offers the result and ticket-close drafts after GATE 5. Both are one-line offers. Nothing is drafted or sent unless the operator asks.

## [0.11.0] — 2026-10-26

A review of all seven skills. The supported stack is narrowed to **AWS + Terraform (ecspresso, lambroll) + Kubernetes (Helm, Kustomize, raw manifests)**, and every skill now follows one evidence rule: each plan, score or finding cites code (`path:line`) and live read-only evidence, cross-checked; drift is surfaced; `UNVERIFIED` never justifies a destroy, replace or resize.

### Breaking

- **Supported stack.** GCP, Azure, Pulumi and Bicep are no longer supported. CloudFormation, SAM, Serverless Framework, CDK and Ansible are recognised (ownership is still detected, including the pre-import CloudFormation / Serverless check) and the skill stops instead of improvising.
- **`runtime-profile-schema: 2`** (runtime-trace). New Wiring block, `no-activity-14d` replaces `idle`, cross-Region claims can be "not verifiable", spend without a scoping tag is "account context - not attributable". service-takeover still accepts a schema-1 profile but marks items 5 and 19 `?` and recommends a re-run.
- **service-takeover scorecard.** Evidence classes `verified` / `attested` / `operator-stated` / `fail` / `conflict` / `unknown` / `N/A`, and a strict verdict: `ready` only when every item is verified, attested or N/A. Takeovers that scored `ready` under v0.10.0 may now score `partial` or `not-ready`.
- **service-discovery catalog.** New `Live` column (Step 2V live cross-check) and `Owner` column; the catalog is stamped with its live-verification status. service-takeover relies on them: scorecard items 4 and 6 count attributed rows and need a live-backed catalog.
- **pre-flight records** carry target, plan hash, plan source, delivery model and caller; iac-change-execution only reuses a record whose plan hash and target match and that is under 24h old.

### Changed

- **iac-change-execution:** code-vs-live evidence table in Step 1 (live reads as one approved batch plus the tool's own drift check); success criteria are commands with expected output; target check (account / region / context / workspace) before every plan and apply; Terraform rollback is revert-and-apply, never an old state file; `kubectl delete -f` is never a rollback; plan / state files never staged; GitOps (Argo CD / Flux) detected, PR path only; PR path follows repo conventions on any Git host; ticket and catalog text treated as data.
- **pre-flight:** every score cites its evidence; Green on reversibility / security needs plan, code or live evidence, resource-health Green needs live evidence; any unknown caps the verdict at YELLOW; one-way in-place update table and rollback limits per tool; secrets never written to records; incident override needs a written justification; adds `kubectl diff`, Kustomize, Argo CD / Flux.
- **cost-optimize-plan:** target check (account = report scope); empty is not zero for metric reads; per-item ownership probe (`unsupported-owner` for CloudFormation); evidence refs on every score, and a delete needs Evidence green to leave Risky; `Realizable` column (RI / SP coverage, cost direction); S3 activity from request metrics / access logs / CloudTrail Lake; separate ALB / NLB / CLB checks; lifecycle expiration treated as irreversible; no hardcoded prices.
- **cloud-cost-investigate:** scoping probe (GATE 1a: caller identity, payer vs member with `LINKED_ACCOUNT` filtering, regions with spend), sweeps per region; no raw output in the report; anomaly usage computed at AmortizedCost with purchases, credits, refunds and tax apart; snapshot orphan and unattached-volume rules tightened; hourly metrics within the 1,440-datapoint limit; Kubernetes efficiency from the allocation API; Cost Explorer priced at $0.01 per page.
- **runtime-trace:** spend attributed only via the scoping tag; audit sidecars hold projected fields only; scoping probe (GATE 1a); CloudTrail Event history used even without a trail; Wiring block from free reads; verdicts describe, never prescribe; IAM policy covers every call the skill makes.
- **service-discovery:** secrets by projection (no Terraform state, `helm get`, `sops -d` or `kubectl get secret`; sensitive values recorded as `<set in file:line>`); optional live cross-check (Step 2V, offered by default); real-discovery results need a membership signal or land in Unattributed; new raw Kubernetes manifest detector; Terraform root rule and OpenTofu / Terragrunt signatures.
- **service-takeover:** conflict check between interview answers and artifacts; optional Step 6 verification batch (offered by default); same-target and freshness checks on every upstream snapshot; one discovery delegation followed by catalog verification; package safety (private-repo banner, references not secrets, ingest secret scan).
- **All skills:** commit only on approval, with default-branch and public-remote checks.
- **Fixtures** updated to the new rules; new `cost-optimize-plan/ownership-check`, `runtime-trace/no-trail-event-history`, `service-discovery/repo-kustomize-manifests`, `service-discovery/repo-cfn-recognition`, `service-takeover/eks-cfn-partial`; `cloud-cost-investigate/attribution-gcp-orders` ported to `attribution-aws-orders`.

### Removed

Everything below is kept at tag [`archive/multi-cloud-v0.10.0`](https://github.com/culiops/culiops-skills/tree/archive/multi-cloud-v0.10.0).

- GCP and Azure examples: `skills/{cloud-cost-investigate,iac-change-execution,pre-flight,service-discovery}/examples/{gcp,azure}.md`.
- GCP and Azure cloud-discovery templates: `skills/service-discovery/cloud-discovery/{gcp,azure}.md`.
- Pulumi and Bicep detectors: `skills/service-discovery/tool-detectors/{pulumi,bicep}.md`; Pulumi / Bicep / CloudFormation handling in pre-flight and iac-change-execution authoring.
- Fixtures: `service-discovery/widgetapi-azure-aks`, `service-discovery/orders-diagrams-only` (its Mermaid / no-region cases ported), `cloud-cost-investigate/attribution-gcp-orders` (ported to AWS), `runtime-trace/cloudtrail-disabled` (replaced by `no-trail-event-history`).

## [0.10.0] — 2026-07-09

### Cost skills — field principles

Field lessons from a real cost-optimization engagement on a staging environment, folded into the existing Principle framework across the four cost skills.

- **Principle 3 (all cost skills): scale the verification window to the action's destructiveness.** idle→resize needs ≥30d, idle→delete 60–180d, at hourly granularity, inspecting the temporal distribution (a single historical burst ≠ steady low use). Replaces the flat 14-day default — the waste sweep is now 30d and delete-candidates pull 60–180d at drill-down; all AWS playbook evidence windows re-tiered accordingly.
- **Principle 4 (all cost skills): cost from the bill, attribute to the metered dimension.** Bill-derived effective rates over list price (new `bill-derived` label); attribute cost to what is actually metered, not the trigger; classify recurring vs residual/self-clearing charges (don't chase a self-clearing line).
- **Principle 1 sharpened:** a delete requires two independent signals — activity=none AND attachment-understood; neither substitutes for the other.
- **Principle 2 extended:** model the transition cost of a mode/tier change, not just the endpoints (a switch can raise cost before it pays off).
- **cost-optimize-plan:** new **🔵 Requires owner confirmation** tier (with a dev-note artifact) for idle-ambiguous resources — streams, caches, idle LBs, scheduled pipelines — where metrics prove no traffic but only an owner can confirm decommissioned vs paused/seasonal; upstream report-freshness gate; mandatory load-balancer dependency checks (Route53 aliases + listeners + target health, not RequestCount alone); mechanical execution-limit surfacing (e.g. Kinesis `UpdateShardCount` staged halving).
- **cloud-cost-investigate:** database rightsize now checks the binding constraint (freeable memory, connections), not CPU by default.
- **iac-change-execution:** mandatory pre-import resource-ownership check (guards the CloudFormation/Serverless dual-ownership drift trap); delete playbooks enumerate the full resource bundle (NAT→EIP+route, LB→listeners/target-groups/DNS); documented `ignore_changes = all` import-to-manage-legacy pattern.
- **pre-flight:** EIP/IP-release external-allowlist check-item (irreversible if a partner firewall allowlists the address); "0 errors" is not "healthy/unused".
- **Fixtures:** new `cost-optimize-plan/window-and-tier-check` (Principle 3 window flip + 🔵 tier + dev-note); extended `cloud-cost-investigate/waste-aws-account` (binding constraint, residual charge, bill-derived rate).

## [0.9.0] — 2026-05-29

### Added

- **Two cross-cutting principles codified in both cost skills** — surfaced from real-case use of `cost-optimize-plan` after v0.8 shipped. Both principles override naive triage shortcuts that pass casual review but produce wrong recommendations.
  - **Principle 1: Verify activity, not attachment.** Evidence of no-use measures *work happening on a resource* (throughput, request / invocation / transaction counts) — never the resources, consumers, policies, or routes configured against it (attachment). Attachment answers "what breaks if I remove this," not "is this in use." Includes the inverse rule (a resource being unattached is not automatic evidence of no-use unless the resource type has no activity dimension — unattached EBS / EIP / orphaned snapshots are exempt). Discounts keep-alive noise (heartbeats, health checks, warm-up probes, provisioned-concurrency pings) by identifying uniform / periodic / workload-independent cadence.
  - **Principle 2: Verify the cost-change direction.** Every savings claim involving a pricing-mode or tier change (provisioned ↔ on-demand, reserved ↔ on-demand, hot ↔ cold tier) must compute the delta from observed throughput × real pricing for both modes. The cheaper mode flips with workload shape — steady → provisioned, spiky / low-baseline → on-demand. Bare "switch mode to save" claims are rejected.
- **`cost-optimize-plan` SKILL.md additions:**
  - New `## Triage Model` → `### Guiding principles` subsection above Dimension 1, carrying both principles with their rules and rationalization stoppers. Dimension references made explicit (Activity → D3 input; Attachment → D2 + D4 input).
- **`cost-optimize-plan` AWS playbook coverage expanded from 9 to 15:**
  - `delete-nat-gateway.md`: activity = `BytesOutToDestination` / `BytesInFromDestination` 14d; ladder fallback names VPC endpoints for AWS-service-destined traffic.
  - `delete-lambda.md`: activity = 30d `Invocations` (subtract `ProvisionedConcurrencyInvocations` keep-warm noise); event source mappings + EventBridge rules scored as attachment (D2). Ladder fallback: memory rightsize.
  - `rightsize-dynamodb.md`: full Principle 2 cost-direction computation required for any provisioned ↔ on-demand mode-switch claim (one switch per 24h); throttles → 🚫 trigger. GSI capacities scored independently.
  - `rightsize-eks-nodegroup.md`: activity = node CPU/memory + scheduled pod requests (Container Insights + kubectl); subtract daemonset baseline before judging idle. Spot conversion noted as reliability tradeoff (not Principle 2 territory).
  - `delete-kinesis-stream.md`: aggressive ladder push — deregister EFO consumers → shard reduce → retention reduce → mode switch (Principle 2 math) → delete. Registered EFO consumers + Lambda mappings + Firehose sources scored as attachment.
  - `rightsize-kinesis-stream.md`: three composable levers (shard-count reduce / retention reduce / mode switch). Per-lever reversibility classification (lever-b retention reduction is 🔴 because records older than new period are immediately deleted). Full Principle 2 cost-direction math for lever-c.
- **`cloud-cost-investigate` SKILL.md additions:**
  - New `## Guiding principles` section between `## Iron Law` and `## Constraints` carrying both principles with rules + rationalization stoppers.
  - Step 2B utilization metrics promoted from *Optional* to **Required (not optional)** for any rightsize / idle-resource candidate whose resource type has an activity dimension. Unattached EBS / EIP / orphaned snapshots explicitly exempted (no activity dimension).
  - Step 4B waste analysis: two new rules cap candidates at `confidence: low` and label `activity-unverified` (Principle 1) or `direction-unverified` (Principle 2) when those checks are missing. Operator can promote via GATE 3 drill-down.
  - Rationalization Prevention table extended with three rows: "nothing attached → waste" (and inverse "attached → in use"); "heartbeat traffic → in use" (keep-alive noise); "switching mode → cheaper" (assumed cost direction).
- **`cloud-cost-investigate` AWS examples extended:**
  - 5 new resource-state sweep patterns in Step 2B: NAT Gateway, Lambda functions, DynamoDB tables, EKS managed nodegroups, Kinesis Data Streams. Each pattern explicitly labels attachment vs activity per Principle 1.
  - "Optional — utilization metrics" renamed to "Utilization metrics (required for activity verification)" matching the SKILL.md promotion. 5 new activity query examples added (one per new resource type) with throttle / keep-alive carve-outs inline.
  - Trailing Principle 2 reminder for DynamoDB and Kinesis mode-switch math (fetch live pricing via `aws pricing get-products`).
- **`tests/fixtures/cost-optimize-plan/principles-check/`**: new 2-item fixture exercising both principles end-to-end. Item #1: Lambda function with 2 attached EventBridge rules but zero 30d invocations → 🟡 Coordinated (Principle 1 prevented incorrect 🚫). Item #2: DynamoDB mode-switch claim with `direction-unverified` upstream label → 🚫 Do not act with recomputed cost-direction math visible in the plan. Validates the new playbooks (`delete-lambda.md`, `rightsize-dynamodb.md`) and both principle disciplines.

### Changed

- **`cost-optimize-plan` v1 scope:** playbook count `9 → 15` (9 delete + 5 rightsize + 1 lifecycle). v1.1+ deferred line for AWS collapsed to a generic "additional resource types added on demand" — every previously-named AWS deferral (NAT Gateway, Lambda, DynamoDB, EKS nodegroup, Kinesis) is now shipped.
- **`tests/fixtures/cost-optimize-plan/no-playbook/`**: swapped the no-playbook scenario from Lambda delete (now covered by `delete-lambda.md`) to Aurora cluster delete (still uncovered in v1). Same scenario shape — single-item upstream report routed to ❔ Manual review with a populated reason column containing a manual-verification checklist (90d activity, Secrets Manager / SSM endpoint references, replicas + Global Database, final-snapshot guidance). History note added so future contributors know why the resource type was swapped.

### Deferred to v1.1+

- GCP / Azure / Kubernetes playbooks (unchanged from v0.8).
- Bulk-execute mode for 🟢 fast wins; plan re-run / dedupe against prior actions; cross-cloud reports (unchanged from v0.8).
- AWS additional resource types beyond the 15 in v1 — added on demand from real-case use, same as the v1 set.

## [0.8.0] — 2026-05-28

### Added

- **`cost-optimize-plan`** skill — read-only triage layer that turns a `cloud-cost-investigate` report into a tiered, verified execution plan. Per-(cloud, action, resource-type) playbooks define verification queries; four-dimension triage (reversibility, blast radius, evidence of no-use, dependency footprint) assigns each item to 🟢 Fast win / 🟡 Coordinated / 🔴 Risky / 🚫 Do not act tiers, plus ❔ Manual review for uncovered types. Sits between `cloud-cost-investigate` (input) and `iac-change-execution` (downstream); no automation handoff — operator drives.
  - `skills/cost-optimize-plan/SKILL.md`: 3-gate workflow (scope → verification batch → plan review), Iron Law (no mutations / no tier without evidence / no execution handoff), 10 constraints, output format with five tier sections, model routing (Opus at Step 4 where judgment matters; haiku/sonnet elsewhere).
  - `skills/cost-optimize-plan/examples/aws.md`: AWS preamble — CLI versions, baseline read-only IAM (`ReadOnlyAccess`), API costs to itemize at GATE 2, throttling notes.
  - `skills/cost-optimize-plan/examples/aws/`: 9 v1 playbooks — `delete-unattached-ebs`, `delete-orphaned-snapshot`, `delete-idle-elastic-ip`, `delete-idle-ec2`, `delete-s3-bucket`, `delete-unused-load-balancer`, `rightsize-ec2`, `rightsize-rds`, `lifecycle-s3`. Each playbook hard-codes its reversibility and blast-radius defaults (not LLM-inferred).
  - `tests/fixtures/cost-optimize-plan/`: 5 fixtures — `happy-path` (3 tiers exercised), `verification-fail` (🚫 triggered by CloudTrail evidence), `no-playbook` (Lambda → ❔ manual review), `missing-catalog` (Dimension 4 ⚪ → 🟡 conservative per tier-rule disambiguation), `query-failure` (IAM denial mid-batch → skill abort with no partial plan committed).
- Integration with existing skills: consumes `cloud-cost-investigate` reports as primary input; optionally consumes `service-discovery` catalogs for Dimension 4 (dependency footprint). Does not invoke pre-flight directly (no IaC diff at this point); per-item evidence vocabulary (Reversibility / Blast Radius / Dependencies) is designed to map onto pre-flight categories #2 / #1 / #4 for downstream re-use. Does not feed `iac-change-execution` automatically — operator opens execution skill manually with plan path + item #.

### Deferred to v1.1+

- GCP / Azure / Kubernetes playbooks.
- AWS NAT Gateway, Lambda delete, DynamoDB rightsize, EKS nodegroup playbooks.
- Bulk-execute mode for 🟢 fast wins; plan re-run / dedupe against prior actions; cross-cloud reports.

## [0.7.1] — 2026-05-13

### Changed

- **runtime-trace SKILL.md polish from v0.7.0 live smoke test.** No functional regressions; three documentation heuristics added to make real-world findings more actionable:
  - **Cost Explorer (Section 2a) — tag-allocation heuristic:** when a tag-filtered query returns $0.00 spend but matching resources exist, the skill now surfaces a TL;DR alert recommending Billing-console activation of the tag as a cost-allocation tag, rather than silently treating the zero as a real attribution.
  - **CloudTrail (Section 2b) — ResourceName filter format note:** clarifies that `LookupAttributes` requires the simple resource name (e.g., `paymentservice`), not the cluster-prefixed composite (e.g., `culishop-lab-paymentservice`). Smoke test surfaced this as the difference between "0 events" and "7 events" on the same resource.
  - **CloudWatch (Section 2c) — coverage heuristic:** when a metric returns fewer than 50% of expected datapoints, the skill now surfaces a Gap distinguishing intermittent operation from partial Container Insights configuration.
- **runtime-trace Testing section** — added a note that JSON sidecar emission (Gate 6) is verified by fixture but not yet exercised in a fully agent-driven live invocation; flag for next end-to-end run.

## [0.7.0] — 2026-05-13

### Added

- **service-takeover skill** — orchestrator that guides an operator through the structured handoff of an AWS service from another team. Eight gates: intake, information audit, diagram extraction (delegates to `service-discovery`), live resource discovery (delegates to `service-discovery`), runtime profile (delegates to `runtime-trace`), outgoing-team interview (doc-driven async, 11 sections), readiness scorecard (PRR-style, 25 items, evidence-backed), handoff package assembly. Resumable across multi-day takeover sessions via a state file. Information-audit gate (1.5) prevents blind sibling invocation by inventorying what we have and proposing cheapest action per gap. Standards-grounded — explicit References block citing SRE book (Ch. 32 PRR + Ch. 6 golden signals), Working Effectively with Legacy Code, Seeking SRE, DevOps Handbook, Accelerate (DORA), AWS Well-Architected (OE pillar), ITIL 4 Service Transition. Five fixtures cover positive (happy-path) + negative paths (partial-interview, existing-stale-catalog, runtime-trace-skipped, interactive-resume).
- **runtime-trace skill** — produces a self-contained AWS runtime profile of a service by querying Cost Explorer (spend), CloudTrail LookupEvents (control-plane events, 90d), CloudWatch GetMetricData (activity baselines, targeted, 200-metric cap), and Resource Explorer (cross-region inventory). Six-gate workflow, $1.00 hard cost cap, $0.25 soft warning, every claim traceable to an API call with JSON sidecars for full reproducibility. Useful for service takeovers (no docs, no IaC), drift checks, post-incident retrospectives, and pre-cost-optimization baselining. Five fixtures cover positive paths (basic / multi-region drift) and negative paths (CloudTrail disabled / Resource Explorer missing / cost-cap exceeded).

## [0.6.0] — 2026-05-12

### Added

- **`cloud-cost-investigate`** skill — read-only cloud cost investigation in three modes (anomaly, waste, attribution) producing a `.culiops/cloud-cost-investigate/` report with prioritized remediation list and source-labelled savings estimates.
  - `skills/cloud-cost-investigate/SKILL.md`: core framework with Iron Law (no mutations / per-batch query approval / source-labelled savings), 5-step gated workflow with mode-specific middle, 4 human gates, 10 constraints, output format.
  - `skills/cloud-cost-investigate/examples/{aws,gcp,azure,kubernetes}.md`: read-only command templates per cloud/platform covering each workflow step. AWS Cost Explorer per-call charges itemized; Compute Optimizer / GCP Recommender / Azure Advisor / OpenCost integration documented.
  - Integration with existing skills: optionally consumes `service-discovery` catalogs; required catalog (or operator-confirmed tag convention) for attribution mode. Does not invoke pre-flight (read-only). Does not feed iac-change-execution automatically.
- `tests/fixtures/cloud-cost-investigate/`: three fixtures — `anomaly-aws-bill-spike` (AWS, anomaly mode, untagged ML compute fleet drives bill spike), `waste-aws-account` (AWS, waste mode, CO + resource-state + utilization with dedup), `attribution-gcp-orders` (GCP, attribution mode, catalog consumption + untraced/context flagging) — each with a recorded dry-run.
- `service-discovery`, `pre-flight`: `## Model Routing` section in each SKILL.md — maps workflow steps to model tiers (opus / sonnet / orchestrator) with input/output contracts and rationale per step. Enables the orchestrating model to route mechanical steps to cheaper/faster models while keeping safety-critical analysis on opus.

## [0.5.0] — 2026-04-24

### Added

- **`service-discovery`: real-infrastructure discovery path** — extends the skill to work when a directory has documentation and diagrams but no IaC. Activates automatically when Step 1 finds no IaC file signatures but detects document/diagram files.
  - **Detection routing**: Step 1 now falls back to document/diagram detection when no IaC is found, automatically routing to the real-discovery workflow (Steps 2R–6R). Hybrid directories (IaC + documents) take the IaC path.
  - **Document detectors** (`skills/service-discovery/doc-detectors/`): 5 shipped detectors — Draw.io (structured XML), Mermaid (structured text), PlantUML (structured text), Markdown/text (keyword extraction), Image (Claude vision). Data-only extensibility: add a new format by dropping a `.md` file.
  - **Cloud discovery templates** (`skills/service-discovery/cloud-discovery/`): 4 shipped templates — AWS (Resource Groups Tagging API, AWS Config), GCP (Cloud Asset Inventory), Azure (Resource Graph), Kubernetes (kubectl label selectors). Data-only extensibility: add a new provider by dropping a `.md` file.
  - **Converging discovery** (Step 4R): document-extracted hints and gated broad cloud queries merge into a single resource list with confidence flags (`undocumented` for cloud-only, `documented-not-found` for docs-only).
  - **Same catalog output**: real-discovery produces identical `.culiops/service-discovery/<service>.md` catalogs, with additional source metadata and confidence flags.
  - **6 operator gates**: one more than the IaC path (broad query approval at 4a). All read-only.
  - **Iron Law extension**: NO WRITE API CALLS. EVER.
  - **Model routing**: 13-row table for real-discovery steps (vision on Opus, mechanical parsing on Sonnet, gates on Orchestrator).
- `tests/fixtures/service-discovery/`: two new fixtures — `payments-docs-only` (AWS, docs + structured diagram + image, exercises all confidence flag outcomes), `orders-diagrams-only` (GCP, Mermaid diagram only, exercises diagrams-without-text scenario) — each with a recorded dry-run.

## [0.4.0] — 2026-04-24

### Added

- **`iac-change-execution`** skill — execute infrastructure changes safely with a 5-step gated workflow (research, plan, implement, execute, verify). First culiops skill that writes to infrastructure.
  - `skills/iac-change-execution/SKILL.md`: core framework with Iron Law, 8 constraints, 5 workflow steps with 5 human gates, multi-phase change support with per-phase gates, two execution paths (PR default / direct apply escape hatch), pre-flight embedded as risk gate, output format for execution records.
  - `skills/iac-change-execution/examples/{aws,gcp,azure,kubernetes}.md`: CLI templates covering research queries (Step 1), verification checks (Step 5), and mutation/apply commands (Step 4) per cloud/platform. Mutation commands flagged with blast radius and elevated permissions.
- Integration with existing skills: consumes service-discovery catalogs for research, invokes pre-flight as embedded risk gate before execution, reuses recent pre-flight records when applicable.
- `tests/fixtures/iac-change-execution/`: three fixtures — `simple-alarm-addition` (single-phase, PR path, Terraform), `multi-phase-rds-upgrade` (multi-phase, direct apply, catalog consumption), `helm-config-update` (Helm, catalog + pre-flight record reuse) — each with a recorded dry-run.

## [0.3.0] — 2026-04-23

### Added

- `pre-flight` skill — 10-category risk assessment framework for evaluating production actions before execution. Produces a go/no-go risk report with per-category scoring, hard/soft block gates, and actionable mitigations.
  - `skills/pre-flight/SKILL.md`: core framework with Iron Law, 10 risk categories, 3-layer context model (L1 static / L2 human / L3 live), traffic-light scoring, multi-Yellow escalation, 7-step gated workflow, and output format.
  - `skills/pre-flight/assessors/README.md`: extensible assessor template (same pattern as tool-detectors).
  - `skills/pre-flight/assessors/iac-change.md`: v1 assessor for Terraform, Helm, Pulumi, CloudFormation, Bicep, ecspresso, lambroll plan/diff outputs.
  - `skills/pre-flight/examples/{aws,gcp,azure,kubernetes}.md`: L3 live health-check query templates per cloud/platform with least-privilege guidance.
- `tests/fixtures/pre-flight/`: three fixtures — `low-risk-cloudwatch-alarm` (all Green), `high-risk-rds-migration` (multiple Reds + hard block), `compound-risk-ecs-update` (multi-Yellow escalation to Red) — each with a recorded dry-run.

## [0.2.0] — 2026-04-15

### Added

- `service-discovery`: extensible per-tool detector files under `skills/service-discovery/tool-detectors/`. Each detector is one markdown file describing file signatures, stack boundary, parameter sources, resource extraction, and typical cross-stack dependencies for one tool. Adding support for a new tool is now a data-only change.
- `service-discovery`: detectors for [ecspresso](https://github.com/kayac/ecspresso) and [lambroll](https://github.com/fujiwara/lambroll).
- `service-discovery`: "Detect unclassified deploy artifacts" sub-step in Step 1 — scans for deploy-shaped files unattributed to any detector and stops to ask the operator (`tool name` / `teach me` / `ignore`). Prevents silent skipping of unrecognized deploy descriptors.
- `tests/fixtures/service-discovery/`: five new fixtures — `repo-ecspresso-only`, `repo-lambroll-only`, `repo-tf-plus-ecspresso`, `repo-unknown-tool`, `repo-sops-only` — each with a recorded dry-run.

### Changed

- `service-discovery` SKILL.md: replaced the inline IaC detection table with a loader instruction that reads `tool-detectors/*.md`. Step 2's resource extraction, Step 3's dependency derivation, and Step 5's Assumptions section now consult the matched detectors.

## [0.1.0] — 2026-04-15

First public release. Ships the plugin scaffold and the first skill, `service-discovery`.

### Added

- Plugin scaffold: `.claude-plugin/plugin.json` manifest, README, MIT LICENSE, `.gitignore`, directory structure (`skills/`, `books/`, `tests/fixtures/`, `notes/`).
- `service-discovery` skill — produces a service-discovery runbook at `.culiops/service-discovery/<service>-<instance>.md` in the target repo. Cloud-agnostic and IaC-agnostic by design.
  - Stack-specific examples under `skills/service-discovery/examples/`: `aws.md`, `gcp.md`, `azure.md`, and orthogonal `kubernetes.md` (on-prem + managed EKS/GKE/AKS, Helm, GitOps).
  - CLI setup, least-privilege IAM preamble, and plan-approve-execute discipline (read-only default; every mutation flagged with blast radius and elevated permission).
  - Output convention: all plugin outputs go under `.culiops/<skill-name>/` in the target repo (shared across future skills).
- Test fixtures validating the skill end-to-end:
  - `tests/fixtures/service-discovery/widgetapi-aws-eks` — Terraform + AWS/EKS + Helm, two environments (prod/staging).
  - `tests/fixtures/service-discovery/widgetapi-azure-aks` — Bicep + Azure/AKS + Helm, same application translated to Azure equivalents (AKS, AGW, AFD, PG Flexible, Azure Cache for Redis, Service Bus, Blob Storage, Key Vault, Workload Identity).
  - Dry-run notes recording gaps surfaced and fixes applied during skill iteration.
