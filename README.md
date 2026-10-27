# CuliOps

DevOps / SRE / cloud / platform-engineering skills for [Claude Code](https://claude.com/claude-code).

CuliOps ships skills that activate automatically when you ask Claude to do operations work — discovering a service's resources, executing infrastructure-as-code change requests, investigating incidents, and more. Supported stack: **AWS + Terraform (ecspresso, lambroll) + Kubernetes (Helm, Kustomize, raw manifests)**. CloudFormation, SAM, Serverless Framework, CDK and Ansible are recognised (so a skill can tell you a resource is owned by one of them), but not supported: the skill says so and stops.

GCP, Azure, Pulumi and Bicep support was removed in v0.11.0. The last multi-cloud version is kept at tag [`archive/multi-cloud-v0.10.0`](https://github.com/culiops/culiops-skills/tree/archive/multi-cloud-v0.10.0).

## Status

`v0.12.0` — Skills shipped:

- **service-discovery** — scan a service's IaC code — or its documentation and diagrams when no IaC exists — and produce a troubleshooting-oriented inventory document (resource catalog, naming patterns, dependencies, per-alarm investigation runbooks). IaC path works with Terraform, Helm, Kustomize, raw Kubernetes manifests, ecspresso, lambroll; CloudFormation / SAM / Serverless / CDK / Ansible repos are recognised and stop (CloudFormation-only repos are offered the real-discovery path). Real-discovery path works with Draw.io, Mermaid, PlantUML diagrams, Markdown/text docs, and architecture images, verified against live AWS / Kubernetes APIs (read-only).
- **pre-flight** — evaluate the risk of a proposed production action (IaC change, CLI command, or agent action) across 11 categories, including application compatibility (reads the app source locally or through `gh` when the change touches what the app depends on). Produces a go/no-go risk report with per-category scoring and actionable mitigations.
- **iac-change-execution** — execute infrastructure changes safely with research-plan-approve-implement-verify workflow. Supports PR and direct-apply paths, multi-phase changes, and integrates with service-discovery and pre-flight.
- **cloud-cost-investigate** — read-only cloud cost investigation in three modes (anomaly, waste, attribution). Produces a report with prioritized remediation list and source-labelled savings estimates. Works with AWS (Cost Explorer + Compute Optimizer + CloudWatch) and Kubernetes (OpenCost / Kubecost).
- **cost-optimize-plan** — reads a `cloud-cost-investigate` report and produces a tiered, verified execution plan. Per-action safety verification ("no GetObject in 90d, no DNS pointing at it, no IAM principals with active usage") and four-dimension triage (reversibility, blast radius, evidence, dependency) assigns each item to 🟢 Fast win / 🟡 Coordinated / 🔵 Requires owner confirmation / 🔴 Risky / 🚫 Do not act / ❔ Manual review. Triage is governed by four Guiding Principles — verify activity, not attachment; verify the cost-change direction; scale the verification window to the action's destructiveness (resize ≥30d, delete 60–180d); cost from the bill and attribute to the metered dimension — so attached-but-idle resources are not assumed in use, mode-switch savings claims are recomputed before being trusted, short-window "idle" reads don't justify deletes, and idle-but-wired resources route to owner confirmation with a dev-note rather than a blind delete. Read-only. Sits between cloud-cost-investigate (input) and iac-change-execution (downstream); no automation handoff — operator drives. AWS-only in v1 (15 playbooks: 9 delete, 5 rightsize, 1 lifecycle); Kubernetes workload playbooks deferred.
- **runtime-trace** — produce a self-contained AWS runtime profile of a service (tag-scoped spend, control-plane events, wiring, activity baselines, cross-region inventory) from cheap read-only APIs (Cost Explorer, CloudTrail Event history, resource policies / event-source mappings, CloudWatch, Resource Explorer). $1 cost cap, seven gates, every claim traceable; verdicts describe, never prescribe. Useful for service takeovers, drift checks, post-incident retrospectives, pre-cost-opt baselining.
- **service-takeover** — orchestrate AWS (incl. EKS) service handoffs from another team when there's no documentation, no IaC, and only diagrams. Eight gates spanning intake, audit, discovery (delegated to service-discovery), catalog verification, runtime profile (delegated to runtime-trace), tribal-knowledge interview, PRR-style readiness scorecard with strict evidence classes, handoff package assembly. Self-contained output at `.culiops/service-takeover/<service>/`. Resumable across multi-day takeovers.
- **change-comms** — draft the messages people need around an infrastructure change: a heads-up to the people affected (service owners, reviewers, on-call, a manager) before applying, a result message after, and a ticket-closing comment carrying the PR link. Facts come from the `iac-change-execution` and `pre-flight` records or the operator, and every fact is sourced; anything missing becomes a visible `<TODO>`. Paste-ready English, plain text by default, with formatting notes for Google Chat, Slack, Microsoft Teams, Jira, Linear and GitHub / GitLab. Common identifier and credential patterns (account IDs, ARNs, IPs, CIDRs, cloud keys, tokens, passwords in URLs, private keys, Kubernetes credentials) are redacted, with a redaction log; a credential found in a record or pasted by the operator is also flagged for rotation. Draft-only: it never sends anything. Output at `.culiops/change-comms/`.

Planned (not yet shipped):

- `incident-investigation` — future skill.

## Installation

Install via Claude Code's plugin system. From any Claude Code session:

```
/plugin marketplace add culiops/culiops-skills
/plugin install culiops@culiops
```

The repo was renamed from `culiops-agent` on 2026-10-27. The old path still redirects, and the plugin name `culiops` did not change, so existing installs keep working.

That's it — skills are now available. Start a new conversation and they'll activate automatically when you ask for relevant work (e.g. "discover this service's resources").

To update later:

```
/plugin marketplace update culiops
```

To uninstall:

```
/plugin uninstall culiops@culiops
```

### Requirements

- Claude Code with plugin support (see [Claude Code docs](https://code.claude.com/docs/en/plugins)).
- For individual skills, stack-specific CLI tools (`aws`, `kubectl`, `helm`, `kustomize`, `terraform`, …) installed locally — each skill's prerequisites section tells you exactly what it needs before it will run.

## Skill Reference

Each skill has its own `SKILL.md` under `skills/<name>/`:

- [`skills/service-discovery/SKILL.md`](skills/service-discovery/SKILL.md)
- [`skills/pre-flight/SKILL.md`](skills/pre-flight/SKILL.md)
- [`skills/iac-change-execution/SKILL.md`](skills/iac-change-execution/SKILL.md)
- [`skills/cloud-cost-investigate/SKILL.md`](skills/cloud-cost-investigate/SKILL.md)
- [`skills/cost-optimize-plan/SKILL.md`](skills/cost-optimize-plan/SKILL.md)
- [`skills/runtime-trace/SKILL.md`](skills/runtime-trace/SKILL.md)
- [`skills/service-takeover/SKILL.md`](skills/service-takeover/SKILL.md)
- [`skills/change-comms/SKILL.md`](skills/change-comms/SKILL.md)

## Output Convention

All documents produced by any `culiops` skill are written under **`.culiops/<skill-name>/`** at your repo root. For example, `service-discovery` writes catalogs to `.culiops/service-discovery/<service>[-<instance>].md`. This keeps plugin-generated artifacts separate from hand-written docs, makes them easy to find or regenerate, and lets you gitignore the whole `.culiops/` tree as a group if you prefer not to commit generated content.

## Design Philosophy

- **Iron Laws and gated workflows.** Every skill has explicit STOP gates where Claude must wait for human confirmation. No silent assumptions.
- **Focused stack, generic within it.** Skills go deep on AWS + Terraform + Kubernetes rather than shallow across every cloud, and make no company-specific assumptions (naming, account layout, Git host, ticket system). Stack-specific examples live in `examples/` subdirectories. Document formats are extensible via data-only additions (`doc-detectors/`).
- **Evidence-backed.** Every plan or finding cites code (`path:line`) and live read-only evidence, cross-checked; drift is surfaced, and an unverified claim never justifies a destroy, replace or resize.
- **Book-informed design.** Skills are designed against industry best practices (Google SRE Book, *Infrastructure as Code*, *The Phoenix Project*, etc.) — wisdom is baked in invisibly, not cited.
- **Dynamic model routing.** Each skill's `## Model Routing` section maps workflow steps to model tiers (opus for safety-critical analysis, sonnet for mechanical steps). The orchestrating model reads these hints and dispatches subagents accordingly — reducing cost and latency without compromising safety. Production-conservative by default: only route to a cheaper model when a human gate catches errors or the step is purely mechanical.

## Repository Layout

```
.claude-plugin/     Plugin + marketplace manifests
skills/<name>/      One directory per skill; each has SKILL.md, examples/, and data directories (tool-detectors/, doc-detectors/, cloud-discovery/, assessors/)
tests/fixtures/     End-to-end fixtures each skill is validated against
CHANGELOG.md        Release history
```

## Contributing

Issues and PRs welcome. New skills should follow the same shape:

- A `SKILL.md` with Iron Law, constraints, rationalization prevention, red flags, and a gated workflow.
- A `## Model Routing` section in `SKILL.md` mapping each workflow step to a model tier (`opus` / `sonnet` / `orchestrator`) with inputs, outputs, and rationale. See existing skills for the table format. Route conservatively — if a step's error could affect safety, keep it on opus.
- Stack-specific `examples/` with read-only CLI templates and least-privilege guidance.
- At least one end-to-end fixture under `tests/fixtures/` with a `DRY-RUN-NOTES.md`.

## License

MIT — see [LICENSE](LICENSE).
