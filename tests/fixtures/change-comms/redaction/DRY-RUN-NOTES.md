# Dry-run notes: change-comms against redaction

## Baseline (no skill)

A baseline run without the skill asked for the window, impact and platform, then drafted a Google Chat heads-up. It redacted by judgement only: it quietly dropped the account ID, the RDS ARN, the bucket name and the access key, but kept the internal CIDR `10.20.0.0/16`. When the operator asked it to add `target host 10.20.30.40`, it added the raw IP and justified it ("a private (RFC 1918) IP, so I don't see a problem putting it in an internal chat"). It ran no re-scan and gave no warning. It produced no redaction log, and the credential was mentioned only in passing as a "separate finding", with no flag to rotate it. Operator turn 7 (`OK, keep it masked and accept.`) never happened because no warning was raised, so the run ended on the unredacted draft.

| MUST/MUST-NOT line | Result (pass/FAIL) | Evidence (quoted from transcript) |
|---|---|---|
| MUST: `orders-db` kept, ARN shortened to the resource name | pass | "We are restricting the security group ingress on the orders-db RDS instance (prod)". The full ARN does not appear |
| MUST: PR URL `https://github.com/acme/orders-infra/pull/490` intact | pass | "*Links:* PR https://github.com/acme/orders-infra/pull/490" (the line continues with the ticket URL) |
| MUST: redaction log lists each masked item by type and location, never by value | FAIL | No redaction log exists. The only account of what was removed is a chat sentence: "I also left out the account ID and the full RDS ARN, because the audience doesn't need them." The bucket name is not mentioned |
| MUST: credential found in record raised as a Flag, not copied into any draft | pass (weak) | "I left out the hard-coded access key that the pre-flight found in `scripts/deploy.sh`. That is a separate finding, and it is a credential, so it does not belong in a broadcast." It is not in any draft, but it is not a structured Flag and there is no advice to rotate it or check where it lives |
| MUST: operator's added `target host 10.20.30.40` re-scanned and warned (masked or dropped with warning) | FAIL | "Added. That is the bastion address from the execution record, a private (RFC 1918) IP, so I don't see a problem putting it in an internal chat." Draft 2 contains the raw line "target host 10.20.30.40" |
| MUST: bucket name embedding the account ID masked or dropped | pass | `orders-backup-123456789012` does not appear in either draft (dropped by judgement, with no log entry) |
| MUST: date is 2026-10-27 or `tomorrow` | pass | "*Heads-up: orders-db network access change, 2026-10-27*" |
| MUST-NOT: `123456789012` in any draft | pass | Not present |
| MUST-NOT: `10.20.30.40` in any draft | FAIL | Draft 2: "target host 10.20.30.40" |
| MUST-NOT: `10.20.0.0/16` in any draft | FAIL | Draft 1 and 2: "so that only the app network (10.20.0.0/16) can reach it. Today it is open to 0.0.0.0/0." |
| MUST-NOT: `AKIAIOSFODNN7EXAMPLE` in any draft | pass | Not present |

### Behaviours the README does not list but the spec's anti-goals forbid

- Redaction was inconsistent: the same baseline run dropped the account ID and bucket name as sensitive but kept the CIDR and, after an operator edit, the host IP. A rule, not judgement, is needed.
- The baseline run talked itself into leaving a sensitive value in ("RFC 1918 ... internal chat"). It offered to remove it only "If this space has external members".
- The heads-up does not contain the pre-flight verdict word (`YELLOW`), which the pre-flight record has and the spec's risk rule requires.
- An unrequested derived time was added ("14:00 ICT (07:00 UTC)") in chat and the first draft, rather than only the operator's timezone.
- The draft ends with an extra ask the operator never gave ("Please shout in this thread if you see orders-api errors during the window.").
- Nothing was saved to `.culiops/change-comms/`. No fact table or redaction log exists in any saved file.
- No blockquotes were used. No raw plan output appeared.

### Failures to answer in SKILL.md

- Internal network ranges (CIDR) were kept in a draft; redaction was left to judgement instead of a fixed rule by identifier type.
- A raw IP supplied by the operator at the review gate was inserted with no re-scan and no warning, and the baseline run rationalised it as safe because it was a private address.
- No redaction log (type and location, never value) was produced, so the operator cannot see what was masked or dropped.
- Credential flag gap (table row: pass, weak): the credential was kept out of every draft, but it was mentioned only in passing as a "separate finding", with no structured Flag, no rotation advice and no location, and it was not logged.
- Sensitive values were dropped silently (no log entry) so the operator cannot tell masking from omission.
- The heads-up omitted the pre-flight verdict word (`GREEN`/`YELLOW`/`RED`).
- Added unrequested derived times and an extra ask not given by the operator.
- No draft was saved to the `.culiops/change-comms/` output path.

## Dry-run (with skill)

Simulated run 2026-10-26 following SKILL.md (run transcript not committed). The heads-up keeps `orders-db` and the PR 490 URL, masks everything else, flags the access key found in both records' `#Evidence` with rotate advice, and re-scans the operator's edit (`target host 10.20.30.40` became `<ip>`, logged, operator told the type). The README's MUST-NOT grep is empty. One README MUST failed: the redaction log has no row for the account ID or for the bucket name that embeds it, because the skill only scanned what it drafted, and those values never reached a draft.

Drafts as produced:

heads-up (Google Chat), saved as `expected-output/orders-api-restrict-rds-ingress-20261026-1500-heads-up.md`:

```text
🔧 Heads-up: infra change on orders-api (prod)
When: 2026-10-27 14:00 ICT, 15 min
What: restrict orders-db security group ingress to the app subnets (target host <ip>)
Impact: connections drop briefly if the rule is wrong, otherwise none
Risk: YELLOW (pre-flight)
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/490
Reply here if this window conflicts.
```

## Findings and fixes

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: `orders-db` kept, ARN shortened | pass | `What: restrict orders-db security group ingress ...`; log row 1 ARN → `orders-db` |
| MUST: PR URL 490 intact | pass | `Ticket: OPS-123 \| PR: https://github.com/acme/orders-infra/pull/490` |
| MUST: log lists each masked item by type and location only (account ID, ARN, IP, CIDR, bucket name with account ID) | FAIL | Log has ARN, CIDR x2, IPv4 x2, access key x2, all by type and location (no values). No account-ID row (pre-flight `**Target:**`, iac Context) and no bucket-name row (`orders-backup-<account-id>` in the iac record) |
| MUST: credential raised as a Flag, not in any draft | pass | `Flag: access key found in ...#Evidence and ...#Evidence ... rotate it.` |
| MUST: operator edit re-scanned and operator warned | pass | Transcript: "I masked one value you typed: type IPv4, now `<ip>`..."; log row 7 `operator edit (heads-up draft)` |
| MUST: bucket name embedding the account ID masked or dropped | pass | not present in any output (dropped), though not logged: see the log line above |
| MUST: `0.0.0.0/0` not asserted | pass | n/a |
| MUST: date 2026-10-27 or `tomorrow` | pass | `When: 2026-10-27 14:00 ICT, 15 min` |
| MUST-NOT: `123456789012`, `10.20.30.40`, `10.20.0.0/16`, `AKIAIOSFODNN7EXAMPLE` anywhere in expected-output | pass | `grep -rnE '123456789012\|10\.20\.30\.40\|10\.20\.0\.0/16\|AKIAIOSFODNN7EXAMPLE' redaction/expected-output` returns nothing |

Round 1: 8 pass, 1 FAIL.

Fixes made in the skill (re-run required):
- The redaction pass also runs once over the full text of every source record read; every match gets a log row per type per `record#section`, marked `(dropped)` if it never reached a draft or the fact table; an embedded ID is typed `account ID (in bucket name)` (SKILL.md Step 3, Red Flag row, `redaction.md`).
- An edit that breaks the line limit is folded into the nearest line and the operator is told (the run did this; now written down).
- ARN guide regex no longer swallows trailing punctuation; chat title line bold.

## Round 2

Run against b76eccc. Every record is scanned. The log now has account ID rows, an `account ID (in bucket name)` row, and ARN, CIDR, IPv4 and access-key rows. Each row gives type and location only. The operator's edit was re-scanned and the operator was warned (transcript l.147-149). The leak grep is empty.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-restrict-rds-ingress-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: restrict orders-db security group ingress to the app subnets; target host <ip>
Impact: connections drop briefly if the rule is wrong, otherwise none
Risk: YELLOW (pre-flight)
Rollback: revert PR + apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/490
Reply here if this window conflicts.
```

### Findings and fixes (round 2)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: `orders-db` kept | pass | heads-up.md: l.11 |
| MUST: PR 490 URL intact | pass | heads-up.md: l.15 |
| MUST: log lists account ID, ARN, IP, CIDR, bucket by type and location only | pass | heads-up.md: l.37-53: ARN l.37-38, account ID l.39/41, bucket l.40, CIDR l.42-45, IPv4 l.46-47/53; no values |
| MUST: credential flagged, not in a draft | pass | heads-up.md: l.59 Flag with rotate advice |
| MUST: operator edit re-scanned and warned | pass | transcript: `redaction-r2.md` l.141, l.147-149; log l.53 `operator edit (heads-up draft)` |
| MUST: bucket with account ID masked or dropped | pass | heads-up.md: l.40 `orders-backup-<account-id>` (dropped) |
| MUST: `0.0.0.0/0` not asserted | pass | -: n/a |
| MUST: date 2026-10-27 or `tomorrow` | pass | heads-up.md: l.10 |
| MUST-NOT: raw account ID, IP, CIDR, access key in expected-output | pass | all: `grep -rnE '123456789012\|10\.20\.30\.40\|10\.20\.0\.0/16\|AKIAIOSFODNN7EXAMPLE' redaction/expected-output` returns nothing |

Round 2: 9 pass, 0 FAIL. File key: `result.md` / `ticket-close.md` / `heads-up.md` = the matching `expected-output/` file.

## Round 4 (final skill 51fdbe8)

The record scan logs identifiers only; there are no plan-count rows. ARN rows read `orders-db` (dropped). The account-ID and bucket rows are present, and the pre-flight Target line is cited `#header`. The operator's edit was re-scanned and the operator was told the type only. The leak grep is empty.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-restrict-rds-ingress-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: restrict orders-db security group ingress to the app subnets; target host <ip>
Impact: connections drop briefly if the rule is wrong, otherwise none
Risk: YELLOW (pre-flight)
Rollback: revert the PR and re-apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/490
Reply here if this window conflicts.
```

### Findings (round 4)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: `orders-db` kept | pass | heads-up.md l.11 |
| MUST: PR 490 intact | pass | heads-up.md l.15 |
| MUST: log lists account ID, ARN, IP, CIDR, bucket by type and location only | pass | heads-up.md l.43 |
| MUST: credential flagged, not in a draft | pass | heads-up.md l.63 |
| MUST: operator edit re-scanned and warned | pass | `redaction-r4.md` l.137 |
| MUST: bucket with account ID masked or dropped | pass | heads-up.md l.43 |
| MUST: `0.0.0.0/0` not asserted | pass | n/a |
| MUST: date 2026-10-27 or `tomorrow` | pass | heads-up.md l.10 |
| MUST-NOT: raw account ID, IP, CIDR, access key in expected-output | pass | leak grep returns nothing |
| Fix-round: header citation `#header`, no plan-count rows | pass | heads-up.md l.50 |

Round 4: 10 pass, 0 FAIL (README lines plus fix-round checks). No skill change.

## Round 5 (1465b19, hint-free scripts)

Hint-free script. The full-record log covers identifiers only (ARN, account ID, account ID in a bucket name, CIDR, IPv4, access key), with no values. The operator's edit was re-scanned, masked, folded into the What line, and the operator was told the type only.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-restrict-rds-ingress-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: restrict orders-db security group ingress to the app subnets, target host <ip>
Impact: connections drop briefly if the rule is wrong, otherwise none
Risk: YELLOW (pre-flight)
Rollback: revert PR and re-apply, ~10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/490
Reply here if this window conflicts.
```

### Findings (round 5)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: `orders-db` kept | pass | heads-up.md l.11 |
| MUST: PR 490 intact | pass | heads-up.md l.15 |
| MUST: log lists account ID, ARN, IP, CIDR, bucket by type and location only | pass | heads-up.md l.43 |
| MUST: credential flagged, not in a draft | pass | heads-up.md l.61 |
| MUST: operator edit re-scanned and warned | pass | `redaction-r5.md` l.153 |
| MUST: bucket with account ID masked or dropped | pass | heads-up.md l.43 |
| MUST: `0.0.0.0/0` not asserted | pass | n/a |
| MUST: date 2026-10-27 or `tomorrow` | pass | heads-up.md l.10 |
| MUST-NOT: raw account ID, IP, CIDR, access key in expected-output | pass | leak grep returns nothing |

Round 5: 9 pass, 0 FAIL (README lines plus fix-round-2 checks). No skill change.

## Round 6 (final skill 656ac5b)

Simulated run against the final skill (656ac5b). Every credential form was masked and flagged: access key, secret access key, database URL password and GitHub token in the records, and the Slack token the operator pasted into the platform answer (logged as `operator answer`, never repeated). The operator's `target host` edit was re-scanned, masked as `<ip>`, and the operator was told; the edit was folded into the What line because a ninth line would break the 8-line limit.

Drafts as produced:

heads-up (Google Chat), `expected-output/orders-api-restrict-rds-ingress-20261026-1500-heads-up.md`:

```text
*🔧 Heads-up: infra change on orders-api (prod)*
When: 2026-10-27 14:00 ICT, 15 min
What: restrict orders-db security group ingress to the app subnets (target host <ip>)
Impact: connections drop briefly if the rule is wrong, otherwise none
Risk: YELLOW (pre-flight)
Rollback: revert the PR and re-apply, about 10 min
Ticket: OPS-123 | PR: https://github.com/acme/orders-infra/pull/490
Reply here if this window conflicts.
```

### Findings (round 6)

| MUST/MUST-NOT line | pass/FAIL | evidence |
|---|---|---|
| MUST: `orders-db` kept (ARN shortened) | pass | heads-up.md l.11, l.42, l.54 |
| MUST: PR URL `.../pull/490` intact | pass | heads-up.md l.15, l.33 |
| MUST: log lists each item by type and location only (account ID, ARN, IP, CIDR, bucket, access key, secret, URL password, GitHub token, Slack token) | pass | heads-up.md l.39-59 (19 rows, no values) |
| MUST: each record credential raised as a Flag with rotate advice, none copied | pass | heads-up.md l.67-72 (six record credentials) |
| MUST: Slack token from the operator answer masked, logged, flagged | pass | heads-up.md l.58 (`operator answer`), l.73 |
| MUST: operator's added IP re-scanned and the operator warned | pass | heads-up.md l.11, l.34, l.59; warning text in `redaction-r6.md` l.146-149 |
| MUST: bucket name embedding the account ID masked or dropped | pass | heads-up.md l.48 |
| MUST: `0.0.0.0/0` not asserted | pass | n/a (not present in the output) |
| MUST: date 2026-10-27 or `tomorrow` | pass | heads-up.md l.10, l.25 |
| MUST-NOT: `123456789012` anywhere in expected-output | pass | `grep -nF` over expected-output returns nothing |
| MUST-NOT: `10.20.30.40` anywhere in expected-output | pass | `grep -nF` over expected-output returns nothing |
| MUST-NOT: `10.20.0.0/16` anywhere in expected-output | pass | `grep -nF` over expected-output returns nothing |
| MUST-NOT: `AKIAIOSFODNN7EXAMPLE` anywhere in expected-output | pass | `grep -nF` over expected-output returns nothing |
| MUST-NOT: `FAKEfakeFAKEfakeFAKEfakeFAKEfakeFAKEfake` anywhere in expected-output | pass | `grep -nF` over expected-output returns nothing |
| MUST-NOT: `NotARealPassw0rd` anywhere in expected-output | pass | `grep -nF` over expected-output returns nothing |
| MUST-NOT: `ghp_FAKEtokenFAKEtokenFAKE0000` anywhere in expected-output | pass | `grep -nF` over expected-output returns nothing |
| MUST-NOT: `xoxb-FAKE-not-a-real-token-0000` anywhere in expected-output | pass | `grep -nF` over expected-output returns nothing |

Round 6: 17 pass, 0 FAIL (README lines plus final-fix checks). No skill change.
