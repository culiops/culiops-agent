-- One row: top-1 client IP share of requests, distinct clients and distinct client keys behind the top IP. If sampled: requests and top1_requests scale by the factor; distinct_*, top1_client_keys are lower bounds; top1_share does not scale.
WITH per AS (
  SELECT client_ip, count(*) AS n, count(DISTINCT client_key) AS keys FROM logs GROUP BY client_ip
), top1 AS (
  SELECT client_ip, n, keys FROM per ORDER BY n DESC, client_ip LIMIT 1
)
SELECT (SELECT sum(n) FROM per) AS requests, (SELECT count(*) FROM per) AS distinct_clients,
       (SELECT count(DISTINCT client_key) FROM logs) AS distinct_client_keys,
       t.client_ip AS top1_client, t.n AS top1_requests,
       round(t.n / (SELECT sum(n) FROM per), 4) AS top1_share, t.keys AS top1_client_keys
FROM top1 AS t
