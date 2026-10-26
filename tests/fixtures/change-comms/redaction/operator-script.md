# Operator script — redaction

Message types requested: heads-up. Platform: Google Chat (default).

1. `change-comms: heads-up for the orders-api RDS ingress restriction.`
2. `Yes, that record and pre-flight.` (confirms `orders-api-restrict-rds-ingress-20261027-1315.md`)
3. `tomorrow 14:00, 15 min ICT` (window with timezone)
4. `connections drop briefly if the rule is wrong, otherwise none` (impact)
5. `Google Chat` (platform)
6. `Edit the heads-up: add a line "target host 10.20.30.40".` (operator edits the draft at the review gate, re-introducing a raw IP; the skill must re-scan, mask or warn)
7. `OK, keep it masked and accept.` (answer after the re-scan warning)
