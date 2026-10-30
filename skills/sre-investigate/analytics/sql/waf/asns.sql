-- Top 50 client ASNs with requests, blocked and distinct clients. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT asn, count(*) AS requests, count(*) FILTER (WHERE action = 'BLOCK') AS blocked,
       count(DISTINCT client_ip) AS distinct_clients
FROM logs
WHERE asn IS NOT NULL
GROUP BY asn
ORDER BY requests DESC, asn
LIMIT 50
