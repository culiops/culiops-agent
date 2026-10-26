# Operator script — pr-path-happy

Message types requested: heads-up, result, ticket-close (all three in one run). Platform: Google Chat (default).

1. `Use change-comms for the orders-api RDS resize. I need the heads-up, the result and the ticket-close.`
2. `Yes, use the 1015 record and the 1000 pre-flight.` (confirms the sources; the skill must have offered `orders-api-resize-rds-20261027-1015.md` and NOT the stale `orders-api-rotate-logs-20261019-0900.md`)
3. `tomorrow 14:00, 15 min` (window, no timezone given)
4. `ICT` (answer when asked for timezone)
5. `~30-60s Multi-AZ failover, writes may fail briefly` (impact)
6. `Google Chat` (platform; the default is fine)
7. `Looks good, accept the heads-up.` (accepts the heads-up draft)
8. `applied 14:12 ICT, success, connections + error rate normal 15 min` (answer when asked for apply time, apply outcome and verification, before the result draft)
9. `Accept the result.`
10. `Accept the ticket-close.`
