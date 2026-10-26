# Examples: Redaction Rules for `change-comms`

Reference for the redaction pass of the `change-comms` skill. Run it on every draft, after drafting and again after every operator edit, and once over the full text of every source record read with patterns 1-7 (so an identifier that was summarised away is still logged, as `dropped`). Pattern 8 applies to drafts only; plan text in a record gets no log row. All sample values below are obviously fake.

## Patterns

Apply in this order (ARNs first, so an account ID inside an ARN is never half-masked). Match on identifier type, not on judgement: a private or internal-looking value is still masked.

| # | Identifier | Match (guide) | Replace with |
|---|---|---|---|
| 1 | ARN | ``arn:aws[a-z-]*:[a-z0-9-]+:[a-z0-9-]*:[0-9]*:[^\s,;)`]*[^\s.,;)`]`` | its resource name: the last segment after `/` or `:`. Trailing punctuation (`.`, `,`, `)`, `;`, a closing backtick) stays outside the match and is kept |
| 2 | 12-digit account ID | `(?<![0-9])[0-9]{12}(?![0-9])` | `<account-id>` |
| 3 | CIDR | IPv4 or IPv6 address followed by `/<prefix>` | `<cidr>` |
| 4 | IPv4 / IPv6 | `\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b`; IPv6 = a colon-separated hex form that contains `::` or at least one hex letter `a-f` (covers `::1`, `fe80::1`, `2001:db8::8a2e:370:7334`). Not IPv6: `HH:mm` or `HH:mm:ss` times (digits only) MAC-like values (`00:1a:2b:3c:4d:5e`, six 2-digit groups) and hash prefixes (`sha256:7a1c…`) | `<ip>` |
| 5 | Access key | `\b(AKIA\|ASIA)[A-Z0-9]{16}\b` | `<redacted-secret>` |
| 6 | JWT-shaped token | `eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`, and `Bearer \S+` | `<redacted-secret>` |
| 7 | Inline credential | `(?i)(password\|secret\|token)\s*[=:]\s*\S+` | `<redacted-secret>` |
| 8 | Plan, diff or state output | any `terraform plan`, diff or state text, including counts such as "1 to add, 1 to destroy" | never in a draft; summarise in words from the Change Plan. The fact table may cite counts |

Examples (input then output):

| Input | Output |
|---|---|
| `arn:aws:rds:ap-southeast-1:123456789012:db:orders-db` | `orders-db` |
| `arn:aws:iam::123456789012:role/orders-deploy` | `orders-deploy` |
| `orders-123456789012-logs` (embedded in a bucket name) | `orders-<account-id>-logs` |
| `10.20.30.40` | `<ip>` |
| `10.20.0.0/16` | `<cidr>` |
| `AKIAIOSFODNN7EXAMPLE` | `<redacted-secret>` |
| `password=hunter2` | `<redacted-secret>` |

Friendly resource names (`orders-db`, `orders-api`) stay: a message without them is useless. Pattern 2 matches an account ID wherever it is embedded; it only requires that the digits are not part of a longer digit run.

A credential found in a record is more than a mask. Besides the log entry, raise one `Flag:` line to the operator in chat: the type and the location, a note that the value appears in a record, and advice to rotate it. Never repeat the value.

## Exemptions

Only these are left unmasked:

- The PR URL and the ticket URL, in the fields where they belong.
- The source-path column of the fact table (`record: <path>#<section>`). It is shown to the operator at GATE 2 and saved in the `.culiops/` file, but never goes into a draft.

Anything else sitting in the same line or field is still scanned. An exemption never covers a value the operator typed into a draft.

## Log format

The log is shown with the drafts and saved with them. It is a Markdown table, outside every `text` fence:

| # | Type | Found in (record#section) | Replaced with |
|---|---|---|---|
| 1 | account ID | `.culiops/iac-change-execution/orders-api-resize-20261027-1400.md#Change Plan` | `<account-id>` |
| 2 | ARN | `.culiops/pre-flight/orders-api-resize-20261027-1330.md#Blast Radius` | `orders-db` |
| 3 | IPv4 | operator edit (heads-up draft) | `<ip>` |
| 4 | access key | `.culiops/iac-change-execution/orders-api-resize-20261027-1400.md#Execution Log` | `<redacted-secret>` |

- **The original value is never written to the log**, not even partly (no last four digits, no first octet). The log records the type, the location and the replacement only.
- "Found in" is `record#section`, or `operator edit (<message type> draft)` or `operator-supplied` for values that did not come from a record. One row per type per `record#section`. When the identifier is embedded in another name, the type says so: `account ID (in bucket name)`.
- "Replaced with" is the replacement, followed by `(dropped)` when the value never reached a draft or the fact table.
- An empty log is stated as `Redaction log: nothing masked`, so the operator can tell "clean" from "not checked". A value that was dropped counts as masked and gets a row; never drop one silently.

## Re-scan after edits

When the operator edits a draft at the review gate, run the full pattern pass again on the edited text before presenting or saving it. The operator's own typing is not trusted: a raw IP, CIDR or account ID typed into an edit is masked and logged, even if it looks private or harmless, and the operator is told which value type was masked (never the value itself). If the operator really needs the raw value in the message, the skill does not include it; the operator adds it by hand after copying.
