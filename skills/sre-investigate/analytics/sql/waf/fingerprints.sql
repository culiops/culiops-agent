-- Top 50 TLS fingerprints (JA3, JA4 hashes) with requests, distinct clients and distinct client keys. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT ja3, ja4, count(*) AS requests, count(DISTINCT client_ip) AS distinct_clients,
       count(DISTINCT client_key) AS distinct_client_keys
FROM logs
WHERE ja3 IS NOT NULL OR ja4 IS NOT NULL
GROUP BY ALL
ORDER BY requests DESC, ja3, ja4
LIMIT 50
