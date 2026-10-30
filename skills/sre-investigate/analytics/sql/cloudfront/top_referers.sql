-- Top 50 referring hosts (from the already-masked Referer) by requests. If sampled: requests scale by the factor; distinct_clients are lower bounds.
SELECT regexp_extract(cs_referer, '^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]*)', 1) AS referer_host,
       count(*) AS requests, count(DISTINCT c_ip) AS distinct_clients
FROM logs
WHERE cs_referer IS NOT NULL AND regexp_extract(cs_referer, '^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]*)', 1) <> ''
GROUP BY ALL
ORDER BY requests DESC, referer_host
LIMIT 50
