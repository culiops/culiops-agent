-- Per day and status for one object path; required param: object (exact URI path, e.g. /media/big.bin), a missing param is an error. If sampled: requests and bytes scale by the factor; distinct_clients are lower bounds.
WITH p AS (
  SELECT CASE WHEN getvariable('object') IS NULL THEN error('param object is required') ELSE getvariable('object') END AS object
)
SELECT CAST(date_trunc('day', ts) AS DATE) AS day, sc_status, count(*) AS requests, sum(sc_bytes) AS bytes,
       count(DISTINCT c_ip) AS distinct_clients
FROM logs, p
WHERE cs_uri_stem = p.object
GROUP BY ALL
ORDER BY day, sc_status
