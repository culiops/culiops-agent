-- Top 50 referring hosts (from the already-masked Referer) by requests. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT regexp_extract(cs_referer, '^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]*)', 1) AS referer_host,
       count(*) AS requests, count(DISTINCT c_ip) AS distinct_clients
FROM logs
WHERE cs_referer IS NOT NULL AND regexp_extract(cs_referer, '^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]*)', 1) <> ''
GROUP BY ALL
ORDER BY requests DESC, referer_host
LIMIT 50
