-- Top 50 user agents with a generic bot/crawler/spider bucket (substring match only). Sampled datasets: multiply counts by the factor sqlq prints.
SELECT CASE WHEN regexp_matches(lower(cs_user_agent), 'bot|crawler|spider') THEN 'bot/crawler/spider'
            ELSE 'other' END AS ua_bucket,
       left(cs_user_agent, 200) AS cs_user_agent, count(*) AS requests,
       count(DISTINCT c_ip) AS distinct_clients, sum(sc_bytes) AS bytes
FROM logs
GROUP BY ALL
ORDER BY requests DESC, cs_user_agent
LIMIT 50
