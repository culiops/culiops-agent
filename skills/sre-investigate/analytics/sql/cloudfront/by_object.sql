-- Requests, bytes and edge result for one object path; required param: object (exact URI path, e.g. /api/orders), a missing param is an error. If sampled: requests and bytes scale by the factor.
WITH p AS (
  SELECT CASE WHEN getvariable('object') IS NULL THEN error('param object is required') ELSE getvariable('object') END AS object
)
SELECT cs_uri_stem, sc_status, x_edge_result_type, count(*) AS requests, sum(sc_bytes) AS bytes
FROM logs, p
WHERE cs_uri_stem = p.object
GROUP BY ALL
ORDER BY requests DESC, sc_status, x_edge_result_type
