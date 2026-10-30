-- Requests per minute for the 10 busiest terminating rules (time series, one row per minute and rule). If sampled: requests scale by the factor.
WITH top AS (
  SELECT terminating_rule_id FROM logs GROUP BY terminating_rule_id
  ORDER BY count(*) DESC, terminating_rule_id LIMIT 10
)
SELECT date_trunc('minute', ts) AS minute, terminating_rule_id, count(*) AS requests
FROM logs
WHERE terminating_rule_id IN (SELECT terminating_rule_id FROM top)
GROUP BY ALL
ORDER BY minute, terminating_rule_id
