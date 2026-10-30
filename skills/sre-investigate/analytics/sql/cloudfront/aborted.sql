-- Top 50 objects with aborted downloads: GET 200 with edge result Error (CloudFront's did-not-finish definition), ClientCommError, or a non-HEAD 200 that sent fewer bytes than sc_content_len (sc_bytes includes headers, so very short truncations are missed); 206 partials are not covered. If sampled: aborted_requests and requests scale by the factor; distinct_clients are lower bounds; aborted_share do not scale.
WITH a AS (
  SELECT cs_uri_stem, c_ip,
         coalesce(x_edge_detailed_result_type = 'ClientCommError', false)
         OR coalesce(cs_method = 'GET' AND sc_status = 200 AND x_edge_result_type = 'Error', false)
         OR coalesce(cs_method IS DISTINCT FROM 'HEAD' AND sc_status = 200 AND sc_content_len > sc_bytes, false) AS is_aborted
  FROM logs
)
SELECT cs_uri_stem, count(*) FILTER (WHERE is_aborted) AS aborted_requests, count(*) AS requests,
       round(count(*) FILTER (WHERE is_aborted) / count(*), 4) AS aborted_share,
       count(DISTINCT c_ip) FILTER (WHERE is_aborted) AS distinct_clients
FROM a
GROUP BY cs_uri_stem
HAVING aborted_requests > 0
ORDER BY aborted_requests DESC, cs_uri_stem
LIMIT 50
