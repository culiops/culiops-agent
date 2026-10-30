-- Top 50 matches by rule, location and match type; counts distinct matched values via salted hash, never shows a value. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT terminating_rule_id, matched_field, match_type, count(*) AS requests,
       count(DISTINCT matched_hash) AS distinct_matched_values, count(DISTINCT client_ip) AS distinct_clients
FROM logs
WHERE matched_field IS NOT NULL OR matched_hash IS NOT NULL
GROUP BY ALL
ORDER BY requests DESC, terminating_rule_id, matched_field
LIMIT 50
