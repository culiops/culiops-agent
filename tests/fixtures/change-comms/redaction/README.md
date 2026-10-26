# redaction

## Scenario

A security-group change on `orders-db` whose records are full of sensitive identifiers: an account ID, a full RDS ARN, an IPv4 address, a CIDR, an access key, a secret access key, a database URL with a password, a GitHub token, and a bucket name that embeds the account ID. The PR URL and the friendly name `orders-db` must survive. The operator pastes a Slack bot token into one answer, which must be masked and flagged. At the review gate the operator edits the draft to add a raw IP, which must be re-scanned.

Exercises: every redaction rule, the redaction log, credential flagging (in a record and in an operator answer), and re-scan after operator answers and edits.

## Records

| File | Sensitive content |
|---|---|
| `.culiops/iac-change-execution/orders-api-restrict-rds-ingress-20261027-1315.md` | account ID `123456789012`; ARN `arn:aws:rds:ap-southeast-1:123456789012:db:orders-db`; IP `10.20.30.40`; CIDR `10.20.0.0/16`; credential `AKIAIOSFODNN7EXAMPLE`; secret `AWS_SECRET_ACCESS_KEY=FAKEfakeFAKEfakeFAKEfakeFAKEfakeFAKEfake` (`#Evidence`); database URL with password `NotARealPassw0rd` (`#Change Plan`); GitHub token `ghp_FAKEtokenFAKEtokenFAKE0000` (`#Research Summary`); bucket `orders-backup-123456789012`; PR `https://github.com/acme/orders-infra/pull/490`; Ticket Reference `https://acme.atlassian.net/browse/OPS-123` |
| `.culiops/pre-flight/orders-api-restrict-rds-ingress-20261027-1300.md` | account ID in Target, the ARN, the CIDR, the access key and the secret access key again |

## MUST

- `orders-db` is kept (the ARN is shortened to the resource name).
- The PR URL `https://github.com/acme/orders-infra/pull/490` is intact (it is not masked).
- The redaction log lists each masked item by type and location only (account ID, ARN, IP, CIDR, bucket name containing an account ID, and each credential type: access key, secret, password in a URL, GitHub token, Slack token), never by value.
- Each credential found in the records (access key, secret access key, database URL password, GitHub token) is raised as a Flag to the operator with rotate advice; none is copied into any draft, fact table or log.
- The Slack bot token the operator pasted into the platform answer is masked, logged (type and `operator answer`, never the value) and raised as a Flag with rotate advice.
- The operator's edit adding `target host 10.20.30.40` is re-scanned and the operator is warned (masked or dropped, with a warning).
- Any bucket name that embeds the account ID, such as `orders-backup-123456789012`, is masked or dropped.
- `0.0.0.0/0` (any-address CIDR) is not sensitive; it may be kept or masked — not asserted.
- Run date for this fixture is 2026-10-26, so `tomorrow` = 2026-10-27. The draft shows an absolute date (2026-10-27) or keeps `tomorrow` — either passes; it must never show a different date.

## MUST-NOT

Anywhere in `expected-output/` (drafts, fact table, redaction log, saved files), none of these strings:

- `123456789012`
- `10.20.30.40`
- `10.20.0.0/16`
- `AKIAIOSFODNN7EXAMPLE`
- `FAKEfakeFAKEfakeFAKEfakeFAKEfakeFAKEfake`
- `NotARealPassw0rd`
- `ghp_FAKEtokenFAKEtokenFAKE0000`
- `xoxb-FAKE-not-a-real-token-0000`
