-- Requests per minute with 4xx/5xx, LB-generated 5xx and p95 target processing time. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT date_trunc('minute', ts) AS minute, count(*) AS requests,
       count(*) FILTER (WHERE elb_status_code BETWEEN 400 AND 499) AS status_4xx,
       count(*) FILTER (WHERE elb_status_code BETWEEN 500 AND 599) AS status_5xx,
       count(*) FILTER (WHERE elb_status_code BETWEEN 500 AND 599 AND target_status_code IS NULL) AS lb_generated_5xx,
       round(quantile_cont(target_processing_time, 0.95) FILTER (WHERE target_processing_time >= 0), 3) AS p95_target_seconds
FROM logs
GROUP BY ALL
ORDER BY minute
