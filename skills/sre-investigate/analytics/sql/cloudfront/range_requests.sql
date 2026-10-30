-- Top 50 objects fetched with HTTP Range (206 or a range start), with average range size. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT cs_uri_stem, count(*) AS range_requests, count(DISTINCT c_ip) AS distinct_clients,
       round(avg(sc_range_end - sc_range_start + 1)) AS avg_range_bytes, sum(sc_bytes) AS bytes
FROM logs
WHERE sc_range_start IS NOT NULL OR sc_status = 206
GROUP BY ALL
ORDER BY range_requests DESC, cs_uri_stem
LIMIT 50
