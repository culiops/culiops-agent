
# Document Detectors

Each file in this directory describes one document or diagram format that the `service-discovery` skill knows how to parse during real-discovery (Step 2). The skill loads every `*.md` detector file here to decide which files in the target repo contain infrastructure resource hints worth extracting.

Adding support for a new format is a data change: drop a new `<format>.md` file in this directory following the template below. No `SKILL.md` edit required.

## Detector file template

````markdown
---
name: <format-name>
extensions: "<comma-separated list of file extensions>"
type: <structured|text|image>
---

## File signatures
- <list of file extensions, filename patterns, and/or content signals that identify this format>

## Parsing method
<description of how to parse this format and what to look for>

## What to extract
- <list of resource hint categories to extract from this format>

## Extraction examples
<one or more examples showing raw input and the extracted hints>

## Limitations
- <list of known limitations and caveats for this format>
````

A detector may omit any non-frontmatter section if it doesn't apply (the skill treats omission as "unknown for this dimension, ask the operator").

## Model routing

The `type` field in frontmatter determines which model processes files matching the detector:

| Type | Model | Rationale |
|------|-------|-----------|
| `structured` | Sonnet | Deterministic parsing of XML/text grammars; speed and cost efficient |
| `text` | Sonnet | Keyword and pattern extraction from prose; speed and cost efficient |
| `image` | Opus | Vision capability required for diagram interpretation |

## Shipped detectors

(Updated once all detectors are in place.)
