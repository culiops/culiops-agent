-- Top 50 objects by bytes served: bytes per distinct client vs object size (repeat_factor well above 1 = repeated full downloads); size is from 200 responses, else an estimate (size_is_estimate). UNRELIABLE if sampled: distinct_clients is a lower bound, so bytes_per_viewer and repeat_factor are inflated; do not use on sampled data (requests and bytes do scale).
WITH per AS (
  SELECT cs_uri_stem, count(*) AS requests, count(DISTINCT c_ip) AS distinct_clients,
         max(sc_content_len) FILTER (WHERE sc_status = 200) AS size_200, max(sc_range_end) + 1 AS size_range,
         max(sc_bytes) AS max_bytes, sum(sc_bytes) AS bytes
  FROM logs
  GROUP BY cs_uri_stem
)
SELECT cs_uri_stem, requests, distinct_clients,
       coalesce(size_200, size_range, max_bytes) AS object_size, size_200 IS NULL AS size_is_estimate, bytes,
       CAST(bytes / nullif(distinct_clients, 0) AS BIGINT) AS bytes_per_viewer,
       round(bytes / nullif(distinct_clients, 0) / nullif(coalesce(size_200, size_range, max_bytes), 0), 2) AS repeat_factor
FROM per
ORDER BY bytes DESC NULLS LAST, cs_uri_stem
LIMIT 50
