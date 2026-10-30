-- Top 50 objects with aborted transfers (ClientCommError, or fewer bytes sent than the full 200 response). Sampled datasets: multiply counts by the factor sqlq prints.
SELECT cs_uri_stem,
       count(*) FILTER (WHERE x_edge_detailed_result_type = 'ClientCommError'
                          OR (sc_status = 200 AND sc_content_len > sc_bytes)) AS aborted_requests,
       count(*) AS requests,
       round(count(*) FILTER (WHERE x_edge_detailed_result_type = 'ClientCommError'
                                OR (sc_status = 200 AND sc_content_len > sc_bytes)) / count(*), 4) AS aborted_share,
       count(DISTINCT c_ip) FILTER (WHERE x_edge_detailed_result_type = 'ClientCommError'
                                      OR (sc_status = 200 AND sc_content_len > sc_bytes)) AS distinct_clients
FROM logs
GROUP BY cs_uri_stem
HAVING aborted_requests > 0
ORDER BY aborted_requests DESC, cs_uri_stem
LIMIT 50
