# Changelog

All notable changes to the `culiops` plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
