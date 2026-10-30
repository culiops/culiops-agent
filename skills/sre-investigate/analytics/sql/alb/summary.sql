-- One-row overview of the ALB dataset: window, requests, clients, bytes, status classes, LB-generated 5xx and p95 target time. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT min(ts) AS first_ts, max(ts) AS last_ts, count(*) AS requests, count(DISTINCT client_ip) AS distinct_clients,
       sum(sent_bytes) AS sent_bytes,
       count(*) FILTER (WHERE elb_status_code BETWEEN 200 AND 299) AS status_2xx,
       count(*) FILTER (WHERE elb_status_code BETWEEN 300 AND 399) AS status_3xx,
       count(*) FILTER (WHERE elb_status_code BETWEEN 400 AND 499) AS status_4xx,
       count(*) FILTER (WHERE elb_status_code BETWEEN 500 AND 599) AS status_5xx,
       count(*) FILTER (WHERE elb_status_code BETWEEN 500 AND 599 AND target_status_code IS NULL) AS lb_generated_5xx,
       round(quantile_cont(target_processing_time, 0.95) FILTER (WHERE target_processing_time >= 0), 3) AS p95_target_seconds
FROM logs
