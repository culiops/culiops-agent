-- Target processing time percentiles (seconds) per target and overall (row ALL), over requests that have a target time; no_target_time_requests counts the failed or timed-out ones left out, so read the percentiles together with it. If sampled: requests, timed_requests and no_target_time_requests scale by the factor; the percentiles do not scale; max_s is a lower bound on the true max.
SELECT CASE WHEN grouping(target_ip) = 1 THEN 'ALL' ELSE coalesce(target_ip, '-') END AS target_ip,
       count(*) AS requests,
       count(*) FILTER (WHERE target_processing_time >= 0) AS timed_requests,
       count(*) FILTER (WHERE target_processing_time IS NULL OR target_processing_time < 0) AS no_target_time_requests,
       round(quantile_cont(target_processing_time, 0.50) FILTER (WHERE target_processing_time >= 0), 3) AS p50_s,
       round(quantile_cont(target_processing_time, 0.90) FILTER (WHERE target_processing_time >= 0), 3) AS p90_s,
       round(quantile_cont(target_processing_time, 0.95) FILTER (WHERE target_processing_time >= 0), 3) AS p95_s,
       round(quantile_cont(target_processing_time, 0.99) FILTER (WHERE target_processing_time >= 0), 3) AS p99_s,
       round(max(target_processing_time) FILTER (WHERE target_processing_time >= 0), 3) AS max_s
FROM logs
GROUP BY GROUPING SETS ((target_ip), ())
ORDER BY (grouping(target_ip) = 0), requests DESC, target_ip
LIMIT 50
