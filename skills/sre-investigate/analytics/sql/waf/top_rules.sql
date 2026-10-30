-- Top 50 terminating rules (with type and action) by requests and share. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT terminating_rule_id, terminating_rule_type, action, count(*) AS requests,
       round(count(*) / sum(count(*)) OVER (), 4) AS share
FROM logs
GROUP BY ALL
ORDER BY requests DESC, terminating_rule_id, action
LIMIT 50
