-- Requests, share and bytes per edge result type (Hit, Miss, RefreshHit, Error, ...; top 50). Sampled datasets: multiply counts by the factor sqlq prints.
SELECT x_edge_result_type, count(*) AS requests, round(count(*) / sum(count(*)) OVER (), 4) AS share,
       sum(sc_bytes) AS bytes
FROM logs
GROUP BY x_edge_result_type
ORDER BY requests DESC, x_edge_result_type
LIMIT 50
