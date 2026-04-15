# CuliOps

DevOps / SRE / cloud / platform-engineering skills for [Claude Code](https://claude.com/claude-code), modeled after [`obra/superpowers`](https://github.com/obra/superpowers).

CuliOps ships skills that activate automatically when you ask Claude to do operations work — discovering a service's resources, executing infrastructure-as-code change requests, investigating incidents, and more. Skills are cloud-agnostic and IaC-agnostic by design.

## Status

`v0.1.0` — pilot release. Skills shipped:

- **service-discovery** — scan a service's IaC code and produce a troubleshooting-oriented inventory document (resource catalog, naming patterns, dependencies, per-alarm investigation runbooks). Works with Terraform, Pulumi, CloudFormation, Bicep, Helm/Kustomize.

Planned (not yet shipped):

- `iac-change-execution` — execute infrastructure tickets safely with research-plan-approve-implement workflow.
- `incident-investigation`, `cloud-cost-analytics`, `iac-code-review` — future skills.

## Installation

Install via Claude Code's plugin system. From any Claude Code session:

```
/plugin marketplace add chiplonton/culiops-agent
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

## Output Convention

All documents produced by any `culiops` skill are written under **`.culiops/<skill-name>/`** at your repo root. For example, `service-discovery` writes catalogs to `.culiops/service-discovery/<service>[-<instance>].md`. This keeps plugin-generated artifacts separate from hand-written docs, makes them easy to find or regenerate, and lets you gitignore the whole `.culiops/` tree as a group if you prefer not to commit generated content.

## Design Philosophy

- **Iron Laws and gated workflows.** Every skill has explicit STOP gates where Claude must wait for human confirmation. No silent assumptions.
- **Agnostic by default.** Cloud provider, IaC tool, and ticket system are all configurable per-conversation. Stack-specific examples live in `examples/` subdirectories.
- **Book-informed design.** Skills are designed against industry best practices (Google SRE Book, *Infrastructure as Code*, *The Phoenix Project*, etc.) — wisdom is baked in invisibly, not cited.

## Repository Layout

```
.claude-plugin/     Plugin + marketplace manifests
skills/<name>/      One directory per skill; each has SKILL.md and examples/
tests/fixtures/     End-to-end fixtures each skill is validated against
CHANGELOG.md        Release history
```

## Contributing

Issues and PRs welcome. New skills should follow the same shape: a `SKILL.md` with a gated workflow, stack-specific `examples/`, and at least one end-to-end fixture under `tests/fixtures/`.

## License

MIT — see [LICENSE](LICENSE).
