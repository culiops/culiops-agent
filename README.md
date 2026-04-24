# CuliOps

DevOps / SRE / cloud / platform-engineering skills for [Claude Code](https://claude.com/claude-code).

CuliOps ships skills that activate automatically when you ask Claude to do operations work — discovering a service's resources, executing infrastructure-as-code change requests, investigating incidents, and more. Skills are cloud-agnostic and IaC-agnostic by design.

## Status

`v0.5.0` — pilot release. Skills shipped:

- **service-discovery** — scan a service's IaC code — or its documentation and diagrams when no IaC exists — and produce a troubleshooting-oriented inventory document (resource catalog, naming patterns, dependencies, per-alarm investigation runbooks). IaC path works with Terraform, Pulumi, CloudFormation, Bicep, Helm/Kustomize, ecspresso, lambroll. Real-discovery path works with Draw.io, Mermaid, PlantUML diagrams, Markdown/text docs, and architecture images, verified against live cloud APIs (read-only).
- **pre-flight** — evaluate the risk of a proposed production action (IaC change, CLI command, or agent action) across 10 categories. Produces a go/no-go risk report with per-category scoring and actionable mitigations.
- **iac-change-execution** — execute infrastructure changes safely with research-plan-approve-implement-verify workflow. Supports PR and direct-apply paths, multi-phase changes, and integrates with service-discovery and pre-flight.

Planned (not yet shipped):

- `incident-investigation`, `cloud-cost-analytics` — future skills.

## Installation

Install via Claude Code's plugin system. From any Claude Code session:

```
/plugin marketplace add culiops/culiops-agent
/plugin install culiops@culiops
```

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
- For individual skills, stack-specific CLI tools (`aws`, `az`, `gcloud`, `kubectl`, `helm`, `terraform`, …) installed locally — each skill's prerequisites section tells you exactly what it needs before it will run.

## Skill Reference

Each skill has its own `SKILL.md` under `skills/<name>/`:

- [`skills/service-discovery/SKILL.md`](skills/service-discovery/SKILL.md)
- [`skills/pre-flight/SKILL.md`](skills/pre-flight/SKILL.md)
- [`skills/iac-change-execution/SKILL.md`](skills/iac-change-execution/SKILL.md)

## Output Convention

All documents produced by any `culiops` skill are written under **`.culiops/<skill-name>/`** at your repo root. For example, `service-discovery` writes catalogs to `.culiops/service-discovery/<service>[-<instance>].md`. This keeps plugin-generated artifacts separate from hand-written docs, makes them easy to find or regenerate, and lets you gitignore the whole `.culiops/` tree as a group if you prefer not to commit generated content.

## Design Philosophy

- **Iron Laws and gated workflows.** Every skill has explicit STOP gates where Claude must wait for human confirmation. No silent assumptions.
- **Agnostic by default.** Cloud provider, IaC tool, and ticket system are all configurable per-conversation. Stack-specific examples live in `examples/` subdirectories. Document formats and cloud discovery APIs are extensible via data-only additions (`doc-detectors/`, `cloud-discovery/`).
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
