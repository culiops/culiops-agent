-- Per day and status for one object path; required param: object (exact URI path, e.g. /media/big.bin). Sampled datasets: multiply counts by the factor sqlq prints.
SELECT CAST(date_trunc('day', ts) AS DATE) AS day, sc_status, count(*) AS requests, sum(sc_bytes) AS bytes,
       count(DISTINCT c_ip) AS distinct_clients
FROM logs
WHERE cs_uri_stem = getvariable('object')
GROUP BY ALL
ORDER BY day, sc_status
