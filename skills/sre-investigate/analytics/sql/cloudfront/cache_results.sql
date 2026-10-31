-- Requests, share and bytes per edge result type (Hit, Miss, RefreshHit, Error, ...; top 50); hit_ratio = Hit / all viewer requests (RefreshHit not counted as a hit). If sampled: requests and bytes scale by the factor; share and hit_ratio do not scale.
-- hit_ratio follows the CloudFront cache statistics report: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cache-statistics.html
WITH g AS (
  SELECT x_edge_result_type, count(*) AS requests, sum(sc_bytes) AS bytes FROM logs GROUP BY x_edge_result_type
)
SELECT x_edge_result_type, requests, round(requests / sum(requests) OVER (), 4) AS share,
       round(coalesce((SELECT sum(requests) FROM g WHERE x_edge_result_type = 'Hit'), 0) / sum(requests) OVER (), 4) AS hit_ratio,
       bytes
FROM g
ORDER BY requests DESC, x_edge_result_type
LIMIT 50
