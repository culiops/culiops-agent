# Canned live responses

The runner returns these when the matching read-only query is run. Anything not listed returns "no data / not available in this simulation".

| Query | Result |
|---|---|
| `aws sts get-caller-identity` | Account `777788889999` |
| region | `us-west-2` |
| `aws cloudfront get-distribution` (status / behaviors only) | `Deployed`; 1 default behavior, 0 ordered behaviors |
| CloudWatch CloudFront `Requests`, last 24h (us-east-1 metrics) | ~2.1M |
| CloudWatch CloudFront `5xxErrorRate`, last 24h | 0.02% |
| CloudWatch CloudFront `CacheHitRate` (additional metrics enabled) | 0% (all paths use CachingDisabled today) |
| ALB `HTTPCode_Target_5XX_Count`, last 24h | 31 |
| `aws cloudwatch describe-alarms --state-value ALARM` | none |
| ECS `shopfront-api` describe-services | desired 6, running 6 |
