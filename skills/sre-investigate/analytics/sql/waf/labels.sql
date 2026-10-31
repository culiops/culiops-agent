-- Top 50 labels attached to requests, with requests and distinct clients. If sampled: requests scale by the factor; distinct_clients are lower bounds.
SELECT label, count(*) AS requests, count(DISTINCT client_ip) AS distinct_clients
FROM (SELECT unnest(labels) AS label, client_ip FROM logs)
GROUP BY label
ORDER BY requests DESC, label
LIMIT 50
