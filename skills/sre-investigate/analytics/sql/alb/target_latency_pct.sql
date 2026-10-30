-- Target processing time percentiles (seconds) per target and overall (row ALL); requests without a target time are skipped. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT CASE WHEN grouping(target_ip) = 1 THEN 'ALL' ELSE coalesce(target_ip, '-') END AS target_ip,
       count(*) AS requests,
       round(quantile_cont(target_processing_time, 0.50), 3) AS p50_s,
       round(quantile_cont(target_processing_time, 0.90), 3) AS p90_s,
       round(quantile_cont(target_processing_time, 0.95), 3) AS p95_s,
       round(quantile_cont(target_processing_time, 0.99), 3) AS p99_s,
       round(max(target_processing_time), 3) AS max_s
FROM logs
WHERE target_processing_time >= 0
GROUP BY GROUPING SETS ((target_ip), ())
ORDER BY (grouping(target_ip) = 0), requests DESC, target_ip
LIMIT 50
