-- Top 50 client IPs with request count, share of all requests, blocked and distinct client keys (aggregated; never more than 50). Sampled datasets: multiply counts by the factor sqlq prints.
SELECT client_ip, count(*) AS requests, round(count(*) / sum(count(*)) OVER (), 4) AS share,
       count(*) FILTER (WHERE action = 'BLOCK') AS blocked, count(DISTINCT client_key) AS distinct_client_keys
FROM logs
GROUP BY client_ip
ORDER BY requests DESC, client_ip
LIMIT 50
