# Examples: Redaction Rules for `change-comms`

Reference for the redaction pass of the `change-comms` skill. Run it on every draft, after drafting and again after every operator answer and edit, and once over the full text of every source record read with patterns 1-11 (so an identifier that was summarised away is still logged, as `dropped`). Pattern 12 applies to drafts only; plan text in a record gets no log row. All sample values below are obviously fake.

## Patterns

Apply in this order (whole private-key blocks first, then ARNs, so an account ID inside an ARN is never half-masked). The patterns are a floor. Judgement may add a mask, never remove one: a private or internal-looking value is still masked, and a value that looks sensitive but matches no pattern may be masked too (logged like any other).

| # | Identifier | Match (guide) | Replace with |
|---|---|---|---|
| 1 | Private key block | `-----BEGIN [A-Z ]*PRIVATE KEY-----` through the next `-----END [A-Z ]*PRIVATE KEY-----` (or the end of the text) | `<redacted-secret>` for the whole block |
| 2 | ARN | ``arn:aws[a-z-]*:[a-z0-9-]+:[a-z0-9-]*:[0-9]*:[^\s,;)`]*[^\s.,;)`]`` | its resource name: the last segment after `/` or `:`. Trailing punctuation (`.`, `,`, `)`, `;`, a closing backtick) stays outside the match and is kept |
| 3 | 12-digit account ID | `(?<![0-9])[0-9]{12}(?![0-9])` | `<account-id>` |
| 4 | Password in a URL | userinfo in any scheme: `[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@` | `<scheme>://<redacted-secret>@`, keeping the scheme and the host |
| 5 | CIDR | IPv4 or IPv6 address followed by `/<prefix>` | `<cidr>` |
| 6 | IPv4 / IPv6 | `\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b`; IPv6 = a colon-separated hex form that contains `::` or at least one hex letter `a-f` (covers `::1`, `fe80::1`, `2001:db8::8a2e:370:7334`). Not IPv6: `HH:mm` or `HH:mm:ss` times (digits only), MAC-like values (`00:1a:2b:3c:4d:5e`, six 2-digit groups) and hash prefixes (`sha256:7a1c…`) | `<ip>` |
| 7 | Access key | `\b(AKIA\|ASIA)[A-Z0-9]{16}\b` | `<redacted-secret>` |
| 8 | GitHub token | `\bgh[pousr]_[A-Za-z0-9]{20,}`, `\bgithub_pat_[A-Za-z0-9_]{20,}` | `<redacted-secret>` |
| 9 | Slack token | `\bxox[abpr]-[A-Za-z0-9-]{10,}` | `<redacted-secret>` |
| 10 | JWT-shaped token | `eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+`, and `Bearer \S+` | `<redacted-secret>` |
| 11 | Inline credential | `(?i)[a-z_]*(secret\|password\|passwd\|token\|api[_-]?key)[a-z_]*["']?\s*[=:]\s*\S+`; also Kubernetes credential material: the value of `client-key-data`, `client-certificate-data` or `certificate-authority-data` in a kubeconfig, and every value under a Secret's `data:` or `stringData:` | `<redacted-secret>` |
| 12 | Plan, diff or state output | any `terraform plan`, diff or state text, including counts such as "1 to add, 1 to destroy" | never in a draft; summarise in words from the Change Plan. The fact table may cite counts |

Examples (input then output):

| Input | Output |
|---|---|
| `arn:aws:elasticache:eu-west-1:210987654321:cluster:billing-sessions` | `billing-sessions` |
| `arn:aws:iam::210987654321:role/billing-deploy` | `billing-deploy` |
| `billing-210987654321-invoices` (embedded in a bucket name) | `billing-<account-id>-invoices` |
| `172.31.8.9` | `<ip>` |
| `172.31.0.0/20` | `<cidr>` |
| `AKIAEXAMPLEEXAMPLE00` | `<redacted-secret>` |
| `mysql://ledger:example-only@billing-ledger.internal:3306/ledger` | `mysql://<redacted-secret>@billing-ledger.internal:3306/ledger` |
| `ghp_EXAMPLEexampleEXAMPLE00` | `<redacted-secret>` |
| `xoxp-EXAMPLE-only-0000` | `<redacted-secret>` |
| `STRIPE_API_KEY=example_only_value` | `<redacted-secret>` |
| `client-key-data: ZXhhbXBsZS1vbmx5` (kubeconfig) | `<redacted-secret>` |
| `-----BEGIN RSA PRIVATE KEY-----` … `-----END RSA PRIVATE KEY-----` | `<redacted-secret>` |

Friendly resource names (`billing-sessions`, `billing-api`) stay: a message without them is useless. Pattern 3 matches an account ID wherever it is embedded; it only requires that the digits are not part of a longer digit run.

A credential (patterns 1, 4, 7-11) is more than a mask, whether it was found in a record or typed by the operator in any answer or edit. Besides the log entry, raise one `Flag:` line to the operator in chat: the type and the location (`record#section` or `operator answer`), a note that the value was exposed, and advice to rotate it. Never repeat the value.

## Exemptions

Only these are left unmasked:

- The PR URL and the ticket URL, in the fields where they belong.
- The source-path column of the fact table (`record: <path>#<section>`). It is shown to the operator at GATE 2 and saved in the `.culiops/` file, but never goes into a draft.

Anything else sitting in the same line or field is still scanned. An exemption never covers a value the operator typed into a draft, and a URL that carries a password (pattern 4) is never exempt.

## Log format

The log is shown with the drafts and saved with them. It is a Markdown table, outside every `text` fence:

| # | Type | Found in (record#section) | Replaced with |
|---|---|---|---|
| 1 | account ID | `.culiops/iac-change-execution/billing-api-move-cache-20261104-2050.md#Change Plan` | `<account-id>` |
| 2 | ARN | `.culiops/pre-flight/billing-api-move-cache-20261104-2035.md#Blast Radius` | `billing-sessions` (dropped) |
| 3 | IPv4 | operator edit (heads-up draft) | `<ip>` |
| 4 | access key | `.culiops/iac-change-execution/billing-api-move-cache-20261104-2050.md#Execution Log` | `<redacted-secret>` (dropped) |
| 5 | Slack token | operator answer | `<redacted-secret>` (dropped) |

- **The original value is never written to the log**, not even partly (no last four digits, no first octet). The log records the type, the location and the replacement only.
- "Found in" is `record#section`, or `operator edit (<message type> draft)` or `operator answer` for values that did not come from a record. One row per type per location. When the identifier is embedded in another name, the type says so: `account ID (in bucket name)`.
- "Replaced with" is the replacement. `(dropped)` after it marks an original value that never reached a draft or the fact table (its section was summarised or not used); the cell still shows what it would have been replaced with. Row 2: the ARN in the Blast Radius was not used, so it is logged as its resource name, `billing-sessions` (dropped). Rows 1 and 3 reached the fact table or a draft, masked, so they carry no marker. Rows 4 and 5 are credentials, so each also has a `Flag:` line.
- An empty log is stated as `Redaction log: nothing masked`, so the operator can tell "clean" from "not checked". A value that was dropped counts as masked and gets a row; never drop one silently.

## Re-scan after answers and edits

When the operator answers a question or edits a draft at the review gate, run the full pattern pass again on the typed text before presenting or saving anything. The operator's own typing is not trusted: a raw IP, CIDR or account ID typed into an answer or edit is masked and logged, even if it looks private or harmless, and the operator is told which value type was masked (never the value itself). A credential typed by the operator is masked, logged and flagged with rotate advice, the same as one found in a record. If the operator really needs the raw value in the message, the skill does not include it; the operator adds it by hand after copying.
