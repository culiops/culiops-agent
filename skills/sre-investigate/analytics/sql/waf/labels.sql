-- Top 50 labels attached to requests, with requests and distinct clients. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT label, count(*) AS requests, count(DISTINCT client_ip) AS distinct_clients
FROM (SELECT unnest(labels) AS label, client_ip FROM logs)
GROUP BY label
ORDER BY requests DESC, label
LIMIT 50
