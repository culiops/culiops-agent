-- Top 50 client IPs with request count, share of all requests and 5xx (aggregated; never more than 50). If sampled: requests and status_5xx scale by the factor; shares do not scale.
SELECT client_ip, count(*) AS requests, round(count(*) / sum(count(*)) OVER (), 4) AS share,
       count(*) FILTER (WHERE elb_status_code BETWEEN 500 AND 599) AS status_5xx
FROM logs
GROUP BY client_ip
ORDER BY requests DESC, client_ip
LIMIT 50
