-- Top 50 source countries with requests, blocked and distinct clients. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT country, count(*) AS requests, count(*) FILTER (WHERE action = 'BLOCK') AS blocked,
       count(DISTINCT client_ip) AS distinct_clients
FROM logs
GROUP BY country
ORDER BY requests DESC, country
LIMIT 50
