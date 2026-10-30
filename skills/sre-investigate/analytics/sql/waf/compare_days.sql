-- Per terminating rule: requests on day a vs day b and the delta (b - a); required params: a, b (YYYY-MM-DD). Top 50 by absolute change. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT terminating_rule_id AS rule,
       count(*) FILTER (WHERE CAST(ts AS DATE) = CAST(getvariable('a') AS DATE)) AS requests_a,
       count(*) FILTER (WHERE CAST(ts AS DATE) = CAST(getvariable('b') AS DATE)) AS requests_b,
       count(*) FILTER (WHERE CAST(ts AS DATE) = CAST(getvariable('b') AS DATE))
         - count(*) FILTER (WHERE CAST(ts AS DATE) = CAST(getvariable('a') AS DATE)) AS delta
FROM logs
WHERE CAST(ts AS DATE) IN (CAST(getvariable('a') AS DATE), CAST(getvariable('b') AS DATE))
GROUP BY terminating_rule_id
ORDER BY abs(delta) DESC, rule
LIMIT 50
