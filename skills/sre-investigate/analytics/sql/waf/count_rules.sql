-- Top 50 non-terminating (count-mode) rule matches by rule and action. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT regexp_extract(m, '^(.*):([^:]*)$', 1) AS rule_id, regexp_extract(m, '^(.*):([^:]*)$', 2) AS rule_action,
       count(*) AS requests, count(DISTINCT client_ip) AS distinct_clients
FROM (SELECT unnest(non_terminating_rules) AS m, client_ip FROM logs)
GROUP BY ALL
ORDER BY requests DESC, rule_id, rule_action
LIMIT 50
