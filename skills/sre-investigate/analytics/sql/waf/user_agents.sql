-- Top 50 user agents with a generic bot/crawler/spider bucket (substring match only). If sampled: requests and blocked scale by the factor; distinct_clients are lower bounds.
SELECT CASE WHEN regexp_matches(lower(user_agent), 'bot|crawler|spider') THEN 'bot/crawler/spider'
            ELSE 'other' END AS ua_bucket,
       left(user_agent, 200) AS user_agent, count(*) AS requests,
       count(*) FILTER (WHERE action = 'BLOCK') AS blocked, count(DISTINCT client_ip) AS distinct_clients
FROM logs
GROUP BY ALL
ORDER BY requests DESC, user_agent
LIMIT 50
