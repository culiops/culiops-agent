-- One-row overview of the WAF dataset: window, requests per action, clients, client keys and rules. If sampled: requests, allowed, blocked, counted and other_actions scale by the factor; distinct_* are lower bounds.
SELECT min(ts) AS first_ts, max(ts) AS last_ts, count(*) AS requests,
       count(*) FILTER (WHERE action = 'ALLOW') AS allowed,
       count(*) FILTER (WHERE action = 'BLOCK') AS blocked,
       count(*) FILTER (WHERE action = 'COUNT') AS counted,
       count(*) FILTER (WHERE action NOT IN ('ALLOW', 'BLOCK', 'COUNT')) AS other_actions,
       count(DISTINCT client_ip) AS distinct_clients, count(DISTINCT client_key) AS distinct_client_keys,
       count(DISTINCT terminating_rule_id) AS distinct_rules
FROM logs
