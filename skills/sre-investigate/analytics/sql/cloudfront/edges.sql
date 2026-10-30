-- Top 50 edge locations by requests, with bytes, distinct clients and 5xx. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT x_edge_location, count(*) AS requests, sum(sc_bytes) AS bytes, count(DISTINCT c_ip) AS distinct_clients,
       count(*) FILTER (WHERE sc_status BETWEEN 500 AND 599) AS status_5xx
FROM logs
GROUP BY ALL
ORDER BY requests DESC, x_edge_location
LIMIT 50
