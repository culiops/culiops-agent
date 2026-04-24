# Changelog

All notable changes to the `culiops` plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
