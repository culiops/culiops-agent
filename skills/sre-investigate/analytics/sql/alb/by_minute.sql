-- Requests per minute with 4xx/5xx, 5xx with no target response (timeouts and refused connections included) and p95 target time over requests that have one. If sampled: requests, status_*, no_target_5xx and no_target_time_requests scale by the factor; p95_target_seconds does not scale.
SELECT date_trunc('minute', ts) AS minute, count(*) AS requests,
       count(*) FILTER (WHERE elb_status_code BETWEEN 400 AND 499) AS status_4xx,
       count(*) FILTER (WHERE elb_status_code BETWEEN 500 AND 599) AS status_5xx,
       count(*) FILTER (WHERE elb_status_code BETWEEN 500 AND 599 AND target_status_code IS NULL) AS no_target_5xx,
       count(*) FILTER (WHERE target_processing_time IS NULL OR target_processing_time < 0) AS no_target_time_requests,
       round(quantile_cont(target_processing_time, 0.95) FILTER (WHERE target_processing_time >= 0), 3) AS p95_target_seconds
FROM logs
GROUP BY ALL
ORDER BY minute
