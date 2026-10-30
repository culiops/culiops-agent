-- Requests, bytes and edge result for one object path; required param: object (exact URI path, e.g. /api/orders). Sampled datasets: multiply counts by the factor sqlq prints.
SELECT cs_uri_stem, sc_status, x_edge_result_type, count(*) AS requests, sum(sc_bytes) AS bytes
FROM logs
WHERE cs_uri_stem = getvariable('object')
GROUP BY ALL
ORDER BY requests DESC, sc_status, x_edge_result_type
