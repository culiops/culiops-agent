-- 5xx by who produced them: lb_generated (target_status_code is - / NULL, the LB answered) vs target_generated. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT elb_status_code,
       CASE WHEN target_status_code IS NULL THEN 'lb_generated' ELSE 'target_generated' END AS origin,
       count(*) AS requests
FROM logs
WHERE elb_status_code BETWEEN 500 AND 599
GROUP BY ALL
ORDER BY elb_status_code, origin
LIMIT 50
