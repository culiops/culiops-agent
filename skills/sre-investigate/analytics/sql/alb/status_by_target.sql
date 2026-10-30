-- Top 50 targets by requests with the status classes they returned; target_ip - means the LB answered without a target. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT coalesce(target_ip, '-') AS target_ip, count(*) AS requests,
       count(*) FILTER (WHERE target_status_code BETWEEN 200 AND 299) AS target_2xx,
       count(*) FILTER (WHERE target_status_code BETWEEN 300 AND 399) AS target_3xx,
       count(*) FILTER (WHERE target_status_code BETWEEN 400 AND 499) AS target_4xx,
       count(*) FILTER (WHERE target_status_code BETWEEN 500 AND 599) AS target_5xx,
       count(*) FILTER (WHERE target_status_code IS NULL) AS no_target_response,
       count(*) FILTER (WHERE elb_status_code BETWEEN 500 AND 599) AS elb_5xx
FROM logs
GROUP BY ALL
ORDER BY requests DESC, target_ip
LIMIT 50
