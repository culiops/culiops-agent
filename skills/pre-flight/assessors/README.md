# Assessors

Each file in this directory describes one action type that the `pre-flight` skill knows how to evaluate. The skill loads every `*.md` file here at the start of Step 1 (Detect action type).

Adding support for a new action type is a data change: drop a new `<action-type>.md` file in this directory following the template below. No `SKILL.md` edit required.

## Assessor file template

````markdown
---
name: <action type>
description: <one-line — when this assessor applies>
triggers: <what input patterns activate this assessor>
---

# <Action Type> Assessor

## Input Recognition
How to detect that the operator's input matches this action type.

## L1 — Static Risk Signals
Per-category extraction rules specific to this action type:
### Blast radius
### Reversibility
### Change velocity
### Dependency impact
### Observability readiness
### Cost impact
### Security posture

## L2 — Context Questions
Additional questions beyond the standard 7 that are specific to this action type.

## L3 — Live Query Hooks
Which signals from `examples/<cloud>.md` to run, and how to interpret results for scoring.

## Rationalization Prevention
Action-type-specific traps.
````

An assessor may omit any non-frontmatter section if it doesn't apply (the skill uses generic scoring for that category).

## Shipped assessors

| Assessor | Evaluates | Notes |
|----------|-----------|-------|
| [`iac-change.md`](iac-change.md) | IaC plan/diff outputs (Terraform, Helm, Pulumi, CloudFormation, Bicep, Ecspresso, Lambroll) | v1 assessor |
