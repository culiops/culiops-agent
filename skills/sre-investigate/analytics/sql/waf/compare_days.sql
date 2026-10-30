-- Per terminating rule: requests on day a vs day b and the delta (b - a), top 50 by absolute change; required params: a, b (YYYY-MM-DD), a missing param is an error. If sampled: requests_a, requests_b and delta (same rate on both days) scale by the factor.
WITH p AS (
  SELECT CAST(CASE WHEN getvariable('a') IS NULL THEN error('param a is required') ELSE getvariable('a') END AS DATE) AS a,
         CAST(CASE WHEN getvariable('b') IS NULL THEN error('param b is required') ELSE getvariable('b') END AS DATE) AS b
)
SELECT terminating_rule_id AS rule,
       count(*) FILTER (WHERE CAST(ts AS DATE) = p.a) AS requests_a,
       count(*) FILTER (WHERE CAST(ts AS DATE) = p.b) AS requests_b,
       count(*) FILTER (WHERE CAST(ts AS DATE) = p.b) - count(*) FILTER (WHERE CAST(ts AS DATE) = p.a) AS delta
FROM logs, p
WHERE CAST(ts AS DATE) IN (p.a, p.b)
GROUP BY terminating_rule_id
ORDER BY abs(delta) DESC, rule
LIMIT 50
