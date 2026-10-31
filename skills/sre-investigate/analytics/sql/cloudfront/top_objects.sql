-- Top 50 objects (URI path) by requests, with bytes and distinct clients. If sampled: requests and bytes scale by the factor; distinct_clients are lower bounds.
SELECT cs_uri_stem, count(*) AS requests, sum(sc_bytes) AS bytes, count(DISTINCT c_ip) AS distinct_clients
FROM logs
GROUP BY ALL
ORDER BY requests DESC, bytes DESC, cs_uri_stem
LIMIT 50
