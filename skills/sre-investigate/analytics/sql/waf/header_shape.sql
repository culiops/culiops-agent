-- Top 50 header-name shapes (names and order only, no values) with requests and distinct clients. If sampled: requests scale by the factor; distinct_clients are lower bounds.
SELECT left(array_to_string(header_names, ','), 300) AS header_shape, len(header_names) AS header_count,
       count(*) AS requests, count(DISTINCT client_ip) AS distinct_clients
FROM logs
GROUP BY ALL
ORDER BY requests DESC, header_shape
LIMIT 50
