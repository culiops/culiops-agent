# Operator script — multi-phase-partial

Message types requested: heads-up, result, ticket-close. Platform: Google Chat (default).

1. `change-comms: heads-up, result and ticket-close for the orders-api Postgres engine upgrade.`
2. `Yes, that record.` (confirms `orders-api-upgrade-postgres-engine-version-20261027-1600.md`)
3. `2026-10-28 22:00 ICT, 2h` (window, covers all three phases; timezone given up front)
4. `~5-10 min of downtime during the engine upgrade restart` (impact)
5. `Google Chat` (platform)
6. `Accept the heads-up.`
7. `phase 2 applied 2026-10-28 22:40 ICT, success, engine shows 15.4 and available, error rate normal` (answer when asked for apply time, outcome and verification for the phase the result covers)
8. `Accept the result.`
9. `Also give me the ticket-close.` (the skill must refuse: not the last phase and not aborted)
10. `OK, skip the ticket-close for now.` (answer after the refusal)
