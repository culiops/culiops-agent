-- Top 50 source countries with requests, blocked and distinct clients. If sampled: requests and blocked scale by the factor; distinct_clients are lower bounds.
SELECT country, count(*) AS requests, count(*) FILTER (WHERE action = 'BLOCK') AS blocked,
       count(DISTINCT client_ip) AS distinct_clients
FROM logs
GROUP BY country
ORDER BY requests DESC, country
LIMIT 50
