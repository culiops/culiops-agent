# Changelog

All notable changes to the `culiops` plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
