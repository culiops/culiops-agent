-- Top 50 referring pages (masked Referer without query or fragment) by requests. If sampled: requests scale by the factor; distinct_clients are lower bounds.
SELECT regexp_replace(cs_referer, '[?#].*$', '') AS referer_page,
       count(*) AS requests, count(DISTINCT c_ip) AS distinct_clients
FROM logs
WHERE cs_referer IS NOT NULL
GROUP BY ALL
ORDER BY requests DESC, referer_page
LIMIT 50
