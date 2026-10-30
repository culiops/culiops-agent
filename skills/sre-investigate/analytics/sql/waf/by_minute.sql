-- Requests per minute and WAF action; optional param: action (exact, e.g. BLOCK). Sampled datasets: multiply counts by the factor sqlq prints.
SELECT date_trunc('minute', ts) AS minute, action, count(*) AS requests
FROM logs
WHERE getvariable('action') IS NULL OR action = getvariable('action')
GROUP BY ALL
ORDER BY minute, action
