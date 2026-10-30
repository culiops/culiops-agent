-- 5xx split by whether a target answered: no_target_response (target_status_code is -: the LB answered itself, or the target timed out, refused or closed the connection, or none was healthy) vs target_responded; error_reason is the LB's logged reason. If sampled: requests scale by the factor.
SELECT elb_status_code,
       CASE WHEN target_status_code IS NULL THEN 'no_target_response' ELSE 'target_responded' END AS origin,
       coalesce(error_reason, '-') AS error_reason,
       count(*) AS requests
FROM logs
WHERE elb_status_code BETWEEN 500 AND 599
GROUP BY ALL
ORDER BY elb_status_code, origin, error_reason
LIMIT 50
