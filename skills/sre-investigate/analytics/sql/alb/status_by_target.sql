-- Top 50 targets (ip and port) by requests with the status classes they returned; target_ip - means no target responded (LB answer, timeout, refused connection). If sampled: every count scales by the factor.
SELECT coalesce(target_ip, '-') AS target_ip, target_port, count(*) AS requests,
       count(*) FILTER (WHERE target_status_code BETWEEN 200 AND 299) AS target_2xx,
       count(*) FILTER (WHERE target_status_code BETWEEN 300 AND 399) AS target_3xx,
       count(*) FILTER (WHERE target_status_code BETWEEN 400 AND 499) AS target_4xx,
       count(*) FILTER (WHERE target_status_code BETWEEN 500 AND 599) AS target_5xx,
       count(*) FILTER (WHERE target_status_code IS NULL) AS no_target_response,
       count(*) FILTER (WHERE elb_status_code BETWEEN 500 AND 599) AS elb_5xx
FROM logs
GROUP BY target_ip, target_port
ORDER BY requests DESC, target_ip, target_port
LIMIT 50
