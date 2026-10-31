---
id: 2026-04-12-static-example-com-prod-origin-504
date: 2026-04-12
service: static-example-com
env: prod
siblings: [all]
window_utc: 2026-04-12T10:10:00Z/2026-04-12T11:20:00Z (ongoing at 11:19)
symptoms: [errors-5xx, timeouts, latency]
cause_category: dependency
cause: CloudFront got no timely answers from its origin origin-static.example.com from 10:12 UTC (504 about 87% of 5xx); what changed at the origin is not known
deps: [origin-static.example.com]
label: Likely
mode: fast
time_to_cause_min: 4
run: runs/static-example-com-prod-20260412-1121
---

What happened: from 10:12 UTC on 2026-04-12 about 6% of requests to static.example.com (CloudFront E3EXAMPLEDIST) returned 5xx, mostly 504, while OriginLatency went from about 89 ms to about 9,100 ms. Edge request volume was normal and the distribution had not changed since 2026-02-18. Still failing when the run ended.

Causal chain:
1. Trigger: the origin or the path to it stopped answering in time at about 10:12 UTC; what changed is unknown. Likely.
2. Mechanism: CloudFront's origin fetches time out (504) or fail (502, 503). Confirmed as observed by CloudFront.
3. Symptom: about 6% of viewer requests get a 5xx. Confirmed.

What found it: CloudFront metrics in three windows (5xxErrorRate, 504ErrorRate, OriginLatency, Requests), with CloudTrail and distribution LastModifiedTime ruling out a CloudFront-side change.

What did not help: schedule, invalidation and repo listings (empty replies); no origin-side data was readable; access logs were not readable by the run.

Follow-ups raised: origin owner to check health and changes around 10:00 to 10:15 UTC; alarm on 5xxErrorRate and OriginLatency; give on-call read access to origin metrics and the distribution's access logs; record origin owner, repo and timezone in environment.md.
