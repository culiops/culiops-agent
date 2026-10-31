-- Top 50 client keys (salted hashes of the configured identity cookie or header, never the value) by requests. If sampled: requests and blocked scale by the factor; distinct_ips are lower bounds.
SELECT client_key, count(*) AS requests, count(DISTINCT client_ip) AS distinct_ips,
       count(*) FILTER (WHERE action = 'BLOCK') AS blocked
FROM logs
WHERE client_key IS NOT NULL
GROUP BY client_key
ORDER BY requests DESC, client_key
LIMIT 50
