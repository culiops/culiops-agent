-- One row: how concentrated traffic is on few clients (top-1 and top-10 share, distinct clients). If sampled: requests and top1_requests scale by the factor; distinct_clients are lower bounds; top1_share and top10_share do not scale.
WITH per AS (
  SELECT c_ip, count(*) AS n FROM logs GROUP BY c_ip
), ranked AS (
  SELECT c_ip, n, row_number() OVER (ORDER BY n DESC, c_ip) AS rk FROM per
)
SELECT sum(n) AS requests, count(*) AS distinct_clients,
       max(c_ip) FILTER (WHERE rk = 1) AS top1_client, max(n) FILTER (WHERE rk = 1) AS top1_requests,
       round(max(n) FILTER (WHERE rk = 1) / sum(n), 4) AS top1_share,
       round(sum(n) FILTER (WHERE rk <= 10) / sum(n), 4) AS top10_share
FROM ranked
