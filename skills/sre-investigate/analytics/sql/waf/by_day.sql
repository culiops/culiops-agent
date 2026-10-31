-- Requests per UTC day with allowed/blocked split and distinct clients. If sampled: requests, allowed and blocked scale by the factor; distinct_clients are lower bounds.
SELECT CAST(date_trunc('day', ts) AS DATE) AS day, count(*) AS requests,
       count(*) FILTER (WHERE action = 'ALLOW') AS allowed,
       count(*) FILTER (WHERE action = 'BLOCK') AS blocked,
       count(DISTINCT client_ip) AS distinct_clients
FROM logs
GROUP BY ALL
ORDER BY day
