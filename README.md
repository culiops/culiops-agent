# CuliOps

SRE, cloud-cost and infrastructure-change skills for [Claude Code](https://claude.com/claude-code), for teams on **AWS and Kubernetes**.

You ask Claude for operations work in plain words ("is this safe to apply?", "why did our AWS bill spike?", "we're taking over service X"). The matching skill starts on its own. It shows you every command before it runs, asks for your approval at each step that matters, and backs every finding with evidence you can check.

## Install

In any Claude Code session:

```
/plugin marketplace add culiops/culiops-skills
/plugin install culiops@culiops
```

Start a new conversation and the skills are available. Update with `/plugin marketplace update culiops`, remove with `/plugin uninstall culiops@culiops`.

You also need the CLIs for your stack (`aws`, `kubectl`, `helm`, `kustomize`, `terraform`, …). Each skill lists what it needs, including the read-only permissions, before it runs anything.

## Supported stack

| | Supported | Recognised only |
|---|---|---|
| **Cloud** | AWS, Kubernetes (EKS or any cluster) | — |
| **IaC / deploy tools** | Terraform, ecspresso, lambroll, Helm, Kustomize, raw manifests | CloudFormation, SAM, Serverless Framework, CDK, Ansible |

"Recognised only" means a skill can tell you a resource is owned by one of these tools, then says it is not supported and stops. It never improvises. GCP, Azure, Pulumi and Bicep were removed in v0.11.0; the last multi-cloud version is at tag [`archive/multi-cloud-v0.10.0`](https://github.com/culiops/culiops-skills/tree/archive/multi-cloud-v0.10.0).

## Skills

| Skill | Use it when you say… | You get | Changes anything? |
|---|---|---|---|
| [**service-discovery**](skills/service-discovery/SKILL.md) | "discover service X", "what does X use", "build a runbook for X" | A resource catalog with dependencies, naming patterns and per-alarm runbooks, from IaC code or, without IaC, from docs and diagrams checked against live state | No. Read-only |
| [**runtime-trace**](skills/runtime-trace/SKILL.md) | "runtime profile for X", "what's actually running for X" | What an AWS service really costs, who changes it, what calls it, its activity baseline and where it lives | No. Read-only, API cost capped at $1 |
| [**service-takeover**](skills/service-takeover/SKILL.md) | "we're taking over service X from team Y" | A guided takeover, ending in a readiness scorecard and a handoff package | No. Read-only |
| [**pre-flight**](skills/pre-flight/SKILL.md) | "is this safe to apply?", "pre-flight this plan" | A GREEN / YELLOW / RED risk report across 11 categories, with mitigations | No. Read-only; live checks only if you opt in |
| [**iac-change-execution**](skills/iac-change-execution/SKILL.md) | "resize the database", "add an alarm", "implement this ticket" | The change made in your IaC code: research, plan, code, pre-flight, apply or PR, verify | **Yes.** Edits code; applies only after your approval |
| [**change-comms**](skills/change-comms/SKILL.md) | "draft a heads-up", "tell the service owners" | Paste-ready heads-up, result and ticket-closing messages, with secrets redacted | No. Drafts only, never sends |
| [**cloud-cost-investigate**](skills/cloud-cost-investigate/SKILL.md) | "why did our bill spike?", "where can we save?", "what does X cost?" | A cost report (anomaly, waste or attribution) with a ranked remediation list | No. Read-only |
| [**cost-optimize-plan**](skills/cost-optimize-plan/SKILL.md) | "which of these savings are safe to act on?" | Each recommendation verified and sorted from fast win to do-not-act, with rollback notes | No. Read-only; stops at the plan |

Planned: `incident-investigation`.

## How they fit together

```
Take over a service   service-takeover ──► service-discovery + runtime-trace ──► readiness scorecard

Make a change         iac-change-execution (runs pre-flight) ──► apply or PR ──► change-comms

Cut cost              cloud-cost-investigate ──► cost-optimize-plan ──► iac-change-execution, one item at a time
```

Each skill also runs on its own. `iac-change-execution` runs pre-flight itself. Everywhere else, the skill gives you the exact command for the next one and you run it.

## How the skills behave

- **You approve what matters.** Every skill has stop gates. Commands are shown in one batch before they run, read-only steps are kept apart from changes, and the permissions needed are listed up front.
- **Evidence, not memory.** Every finding and every decision (a score, a tier, a verdict, "safe to delete") cites where it came from: code (`path:line`), a live read-only query, a plan, or official docs read in the session. When code and live state disagree, the skill shows the drift instead of picking one.
- **Current sources first.** Cloud services and tools change faster than any model's training data. So the tool's own output for your target (`terraform plan`, `kubectl explain`, CLI help) comes first, then official docs for the version you run, then recall. Recall is marked `UNVERIFIED` and never decides anything.
- **Fails closed.** Unknown is never treated as safe. An unverified claim can't justify a delete, replace or resize, and a missing signal lowers the verdict.
- **No company assumptions.** Nothing assumes your roles, chat or ticket tool, account layout, naming, Git host, or whether CI applies on merge.

Everything a skill writes goes under `.culiops/<skill-name>/` in your repo, so it's easy to find, regenerate, or gitignore.

## Repository layout

```
.claude-plugin/   Plugin and marketplace manifests
skills/<name>/    SKILL.md plus examples/ and data directories (detectors, assessors, playbooks, templates)
tests/fixtures/   End-to-end fixtures each skill is checked against
CHANGELOG.md      Release history
```

## Contributing

Issues and PRs are welcome. A new skill follows the same shape as the existing ones:

- A `SKILL.md` with an Iron Law, constraints, rationalization prevention, red flags and a gated workflow.
- A `## Model Routing` table that maps each step to a model tier (`opus` for safety-critical analysis, `sonnet` for mechanical steps) with inputs, outputs and rationale. When a mistake in a step could affect safety, keep it on `opus`.
- `examples/` with read-only CLI templates and least-privilege guidance, for AWS and Kubernetes alike.
- At least one end-to-end fixture under `tests/fixtures/` with a `DRY-RUN-NOTES.md`.

The skill designs draw on SRE and infrastructure books (the Google SRE books, *Infrastructure as Code*, *The Phoenix Project* and others).

## License

MIT. See [LICENSE](LICENSE).
