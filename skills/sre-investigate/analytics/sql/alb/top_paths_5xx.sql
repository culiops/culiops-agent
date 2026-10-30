-- Top 50 request paths (no query string) with 5xx responses; lb_generated counts those the LB produced without a target. Sampled datasets: multiply counts by the factor sqlq prints.
SELECT coalesce(nullif(regexp_extract(url, '^[A-Za-z][A-Za-z0-9+.-]*://[^/?#]*([^?#]*)', 1), ''), '/') AS path,
       elb_status_code, count(*) AS requests,
       count(*) FILTER (WHERE target_status_code IS NULL) AS lb_generated,
       count(DISTINCT client_ip) AS distinct_clients
FROM logs
WHERE elb_status_code BETWEEN 500 AND 599
GROUP BY ALL
ORDER BY requests DESC, path, elb_status_code
LIMIT 50
