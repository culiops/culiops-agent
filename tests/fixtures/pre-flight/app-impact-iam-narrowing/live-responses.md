# Canned live responses

The runner returns these when the matching read-only query is run. Any query not listed returns "no data / not available in this simulation".

| Query | Result |
|---|---|
| `aws sts get-caller-identity` | Account `111122223333` |
| region (`aws configure get region` / `AWS_REGION`) | `eu-west-1` |
| `aws ecs describe-services` (cartapi) | desired 3, running 3, pending 0, one PRIMARY deployment |
| `aws cloudwatch describe-alarms --state-value ALARM` (cartapi dimensions) | none |
| CloudWatch ECS CPU / memory, last 1h | CPU avg 21%, memory avg 38% |
| CloudWatch ALB `HTTPCode_Target_5XX_Count`, last 24h | 0 |
| CloudWatch SQS `NumberOfMessagesSent` for `cartapi-ledger.fifo`, last 7d | ~1,150 per day, every day |
| CloudWatch SNS `NumberOfMessagesPublished` for `cart-events`, last 7d | ~1,160 per day |
| `aws iam get-service-last-accessed-details` (cartapi task role) | `sqs` last accessed today; `sns` last accessed today |
| CloudWatch Logs Insights `WARN` count on cartapi log group, last 24h | 0 |
