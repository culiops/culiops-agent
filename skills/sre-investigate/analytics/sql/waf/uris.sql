-- Top 50 request paths (masked, no query string) by method with requests and blocked. If sampled: requests and blocked scale by the factor; distinct_clients are lower bounds.
SELECT uri, http_method, count(*) AS requests, count(*) FILTER (WHERE action = 'BLOCK') AS blocked,
       count(DISTINCT client_ip) AS distinct_clients
FROM logs
GROUP BY ALL
ORDER BY requests DESC, uri, http_method
LIMIT 50
