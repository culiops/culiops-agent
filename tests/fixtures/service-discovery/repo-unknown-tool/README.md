# repo-unknown-tool — escape-hatch fixture

A synthetic deploy descriptor for a fictional tool the skill has NEVER heard of (`mycli`). Its only purpose is to exercise the new "Detect unclassified deploy artifacts" sub-step in Step 1.

## What's modelled

A made-up CLI deploy tool whose config (`mycli.yml`) references a service definition (`services/api.json`). Both files have deploy-shaped top-level keys (`service:`, `cluster:`, `image:`).

## What this fixture exercises in the skill

- **Detector loading:** No detector matches.
- **Unclassified-deploy-artifacts escape hatch fires:** the skill recognizes both files have deploy-shape and STOPS, asking the human one of three options (tool name / teach me / ignore).
- **No silent skip:** the skill MUST NOT proceed past Step 1 without resolving the unclassified files.
- **Assumptions section requirement:** if the human chose "teach me" or "ignore", the produced catalog (if generation continues) must include the mandatory caveat line.
