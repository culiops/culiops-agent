-- Top 50 request paths (no query string) with 5xx responses; no_target_response counts those where no target answered (LB answer, timeout, refused connection). If sampled: requests and no_target_response scale by the factor; distinct_clients are lower bounds.
SELECT coalesce(nullif(regexp_extract(url, '^[A-Za-z][A-Za-z0-9+.-]*://[^/?#]*([^?#]*)', 1), ''), '/') AS path,
       elb_status_code, count(*) AS requests,
       count(*) FILTER (WHERE target_status_code IS NULL) AS no_target_response,
       count(DISTINCT client_ip) AS distinct_clients
FROM logs
WHERE elb_status_code BETWEEN 500 AND 599
GROUP BY ALL
ORDER BY requests DESC, path, elb_status_code
LIMIT 50
