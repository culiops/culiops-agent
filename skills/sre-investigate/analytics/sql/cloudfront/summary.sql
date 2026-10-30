-- One-row overview of the CloudFront dataset: window, requests, clients, objects, bytes and status classes. If sampled: requests, bytes and status_* counts scale by the factor; distinct_* are lower bounds.
SELECT min(ts) AS first_ts, max(ts) AS last_ts, count(*) AS requests,
       count(DISTINCT c_ip) AS distinct_clients, count(DISTINCT cs_uri_stem) AS distinct_objects,
       sum(sc_bytes) AS bytes,
       count(*) FILTER (WHERE sc_status BETWEEN 200 AND 299) AS status_2xx,
       count(*) FILTER (WHERE sc_status BETWEEN 300 AND 399) AS status_3xx,
       count(*) FILTER (WHERE sc_status BETWEEN 400 AND 499) AS status_4xx,
       count(*) FILTER (WHERE sc_status BETWEEN 500 AND 599) AS status_5xx
FROM logs
