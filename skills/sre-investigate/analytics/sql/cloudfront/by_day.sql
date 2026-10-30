-- Requests, bytes, distinct clients and 4xx/5xx per UTC day. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT CAST(date_trunc('day', ts) AS DATE) AS day, count(*) AS requests, sum(sc_bytes) AS bytes,
       count(DISTINCT c_ip) AS distinct_clients,
       count(*) FILTER (WHERE sc_status BETWEEN 400 AND 499) AS status_4xx,
       count(*) FILTER (WHERE sc_status BETWEEN 500 AND 599) AS status_5xx
FROM logs
GROUP BY ALL
ORDER BY day
