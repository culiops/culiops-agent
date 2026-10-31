-- Top 50 top-level non-terminating (count-mode) rule matches by rule and action; rule-group count matches are not here, they live in rule_group_matches. If sampled: requests scale by the factor; distinct_clients are lower bounds.
SELECT regexp_extract(m, '^(.*):([^:]*)$', 1) AS rule_id, regexp_extract(m, '^(.*):([^:]*)$', 2) AS rule_action,
       count(*) AS requests, count(DISTINCT client_ip) AS distinct_clients
FROM (SELECT unnest(non_terminating_rules) AS m, client_ip FROM logs)
GROUP BY ALL
ORDER BY requests DESC, rule_id, rule_action
LIMIT 50
