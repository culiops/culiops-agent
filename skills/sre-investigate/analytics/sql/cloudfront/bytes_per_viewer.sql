-- Top 50 objects by bytes: bytes per distinct client vs object size; repeat_factor well above 1 means repeated full downloads. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT cs_uri_stem, count(*) AS requests, count(DISTINCT c_ip) AS distinct_clients,
       coalesce(max(sc_content_len), max(sc_bytes)) AS object_size, sum(sc_bytes) AS bytes,
       CAST(sum(sc_bytes) / count(DISTINCT c_ip) AS BIGINT) AS bytes_per_viewer,
       round(sum(sc_bytes) / count(DISTINCT c_ip) / nullif(coalesce(max(sc_content_len), max(sc_bytes)), 0), 2) AS repeat_factor
FROM logs
GROUP BY cs_uri_stem
ORDER BY repeat_factor DESC NULLS LAST, bytes DESC, cs_uri_stem
LIMIT 50
