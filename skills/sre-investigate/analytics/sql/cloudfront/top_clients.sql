-- Top 50 client IPs with request count, share of all requests and bytes (aggregated; never more than 50). Sampled datasets: multiply counts by the factor sqlq prints.
SELECT c_ip, count(*) AS requests, round(count(*) / sum(count(*)) OVER (), 4) AS share, sum(sc_bytes) AS bytes
FROM logs
GROUP BY c_ip
ORDER BY requests DESC, c_ip
LIMIT 50
