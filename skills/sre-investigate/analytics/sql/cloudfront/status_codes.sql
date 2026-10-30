-- Requests, share and bytes per HTTP status code returned to the viewer. If sampled: requests and bytes scale by the factor; share do not scale.
SELECT sc_status, count(*) AS requests, round(count(*) / sum(count(*)) OVER (), 4) AS share,
       sum(sc_bytes) AS bytes
FROM logs
GROUP BY sc_status
ORDER BY requests DESC, sc_status
LIMIT 50
