# WAF playbook

Backends: CloudWatch (`AWS/WAFV2` metrics through `get-metric-data`) · AWS WAF (`wafv2` list/get calls and `get-sampled-requests`)
verified: docs-only

**Purpose.** This playbook answers three questions. Is the web ACL blocking or challenging real users, and if so which rule, which paths, which countries and clients, since when? Is a spike an attack (volumetric, scraping, credential stuffing), and how concentrated is it? Why are 403s above normal: one client, an attack, or ordinary users whose behaviour changed (a new client release, a link shared widely, a new integration) and now trips a rule? Every answer is compared with the same window seven days earlier.

What WAF data cannot say: the status the origin returned. A `BLOCK` is the WAF's own 403 or custom response; for allowed requests, the real status lives only in the CDN or load balancer access logs, which this version does not read (see [Escalation order](#escalation-order)).

## Escalation order

Cheapest first; stop at the rung that answers the question.

1. **Free metrics, by rule, against −7 days.** `AllowedRequests`, `BlockedRequests`, `CountedRequests`, `ChallengeRequests` and `CaptchaRequests` per rule, for the incident window and the same window a week earlier. This shows which rule moved, and when, at no query cost beyond `get-metric-data`.
2. **Sampled requests,** for the rule that moved, or for the default action to see allowed traffic. Only the last three hours can be sampled, at most 500 requests out of the first 5,000 in the window.
3. **WAF logs.** Not read by this version. When the question needs full counts, TLS fingerprints, or requests older than three hours, record a gap and add to the report's "To confirm, a human would…" list a sentence such as "count the blocked requests for this rule by client and path in the web ACL's logs for the incident hour". Logs arrive minutes to an hour late, so the newest window is always incomplete.
4. **CDN or load balancer access logs** for the status the origin actually returned. Also not read by this version; same treatment as rung 3.

**Find the web ACL and its rules first.** Regional ACLs (load balancers, API Gateway) live in the resource's Region; CloudFront ACLs are always read in `us-east-1` with `--scope CLOUDFRONT`.

```bash
aws wafv2 list-web-acls --profile <profile> --region <region> --scope REGIONAL \
  --query 'WebACLs[].[Name, Id, ARN]' --output text
aws wafv2 list-web-acls --profile <profile> --region us-east-1 --scope CLOUDFRONT \
  --query 'WebACLs[].[Name, Id, ARN]' --output text
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/wafv2/list-web-acls.html -->

The rules, their actions and metric names, and which ones run in COUNT mode:

```bash
aws wafv2 get-web-acl --profile <profile> --region <region> --scope <REGIONAL|CLOUDFRONT> \
  --name <acl-name> --id <acl-id> \
  --query 'WebACL.{defaultAction: DefaultAction, aclMetric: VisibilityConfig.MetricName, rules: Rules[].{name: Name, priority: Priority, action: Action, override: OverrideAction, metric: VisibilityConfig.MetricName, sampled: VisibilityConfig.SampledRequestsEnabled, groupOverrides: Statement.ManagedRuleGroupStatement.RuleActionOverrides}}' \
  --output json > "$RUN/w-acl.json"
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/wafv2/get-web-acl.html -->

A rule with `action` `{"Count": {}}`, a rule group with `override` `{"Count": {}}`, or a managed rule listed in `groupOverrides` with `Count` is a COUNT-mode rule: it matches and labels, but lets the request through.

What the ACL logs, so that absence in the logs is not read as zero:

```bash
aws wafv2 get-logging-configuration --profile <profile> --region <region> --resource-arn <acl-arn> \
  --query 'LoggingConfiguration.{filter: LoggingFilter, redacted: RedactedFields}'
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/wafv2/get-logging-configuration.html -->

A logging filter that keeps only `BLOCK` or `COUNT` means allowed traffic is visible only through sampling and the CDN or load balancer logs. That is a configuration choice; suggest it to the owner if it blocks the investigation, and do not try to reconstruct the missing data another way.

**Rung 1: metrics per rule.** One query file per period, in the run directory. Dimensions are `WebACL` (the ACL's metric name), `Rule` (the rule's metric name, `ALL` for the whole ACL, or `Default_Action` for requests no rule terminated) and `Region`. CloudFront ACLs have no `Region` dimension and are read in `us-east-1`. Statistic `Sum` only.

```json
[ {"Id": "blocked_all", "MetricStat": {"Metric": {"Namespace": "AWS/WAFV2", "MetricName": "BlockedRequests",
    "Dimensions": [{"Name": "WebACL", "Value": "<acl-metric>"}, {"Name": "Rule", "Value": "ALL"}, {"Name": "Region", "Value": "<region>"}]},
    "Period": 300, "Stat": "Sum"}},
  {"Id": "blocked_rule1", "MetricStat": {"Metric": {"Namespace": "AWS/WAFV2", "MetricName": "BlockedRequests",
    "Dimensions": [{"Name": "WebACL", "Value": "<acl-metric>"}, {"Name": "Rule", "Value": "<rule-metric>"}, {"Name": "Region", "Value": "<region>"}]},
    "Period": 300, "Stat": "Sum"}},
  {"Id": "counted_rule2", "MetricStat": {"Metric": {"Namespace": "AWS/WAFV2", "MetricName": "CountedRequests",
    "Dimensions": [{"Name": "WebACL", "Value": "<acl-metric>"}, {"Name": "Rule", "Value": "<count-rule-metric>"}, {"Name": "Region", "Value": "<region>"}]},
    "Period": 300, "Stat": "Sum"}},
  {"Id": "allowed_default", "MetricStat": {"Metric": {"Namespace": "AWS/WAFV2", "MetricName": "AllowedRequests",
    "Dimensions": [{"Name": "WebACL", "Value": "<acl-metric>"}, {"Name": "Rule", "Value": "Default_Action"}, {"Name": "Region", "Value": "<region>"}]},
    "Period": 300, "Stat": "Sum"}} ]
```
<!-- doc: https://docs.aws.amazon.com/waf/latest/developerguide/waf-metrics.html -->

```bash
for w in "incident $START $END" "minus7d <start-minus-7d> <end-minus-7d>"; do
  read -r win ws we <<< "$w"
  aws cloudwatch get-metric-data --profile <profile> --region <region> \
    --start-time "$ws" --end-time "$we" \
    --metric-data-queries file://"$RUN/q-waf-300.json" --output json > "$RUN/m-waf-$win.json"
done
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/cloudwatch/get-metric-data.html -->

Turn each output into a table with the metrics playbook's "GetMetricData to a table" recipe. Every query counts against `budgets.<mode>.cloudwatch_metric_requests`; request only the rules a hypothesis needs, plus `ALL`.

**Rung 2: a sample.** The sample is piped straight into `jq`, and only the fields below are kept: no raw response, with its headers and cookies, is ever written to disk or shown.

```bash
aws wafv2 get-sampled-requests --profile <profile> --region <region> \
  --web-acl-arn <acl-arn> --rule-metric-name <rule-metric> --scope <REGIONAL|CLOUDFRONT> \
  --time-window StartTime=<start-utc>,EndTime=<end-utc> --max-items 500 --output json \
  | jq '{window: (.TimeWindow | map_values(floor | todate)), population: .PopulationSize,
         requests: [.SampledRequests[] | {t: (.Timestamp | floor | todate), action: .Action,
           rule: .RuleNameWithinRuleGroup, weight: .Weight, ip: .Request.ClientIP,
           country: .Request.Country, method: .Request.Method,
           path: (.Request.URI | split("?")[0]),
           ua: ([.Request.Headers[] | select(.Name | ascii_downcase == "user-agent") | .Value][0]),
           headerNames: [.Request.Headers[].Name], labels: [.Labels[]?.Name]}]}' \
  > "$RUN/w-sample-<rule>.json"
```
<!-- doc: https://docs.aws.amazon.com/cli/latest/reference/wafv2/get-sampled-requests.html -->

- `window` is the window WAF actually sampled. On a busy ACL it is shorter than the one requested, because the sample is drawn from the first 5,000 requests. Quote the returned window, never the requested one.
- `population` is the number of requests the sample was drawn from; `weight` says how many requests one sampled row stands for.
- Use `--rule-metric-name Default_Action` to sample requests that no rule terminated, which is the only way to see allowed traffic when the logging filter drops it.

Concentration by client address, weighted:

```bash
jq -r '.requests[] | [.ip, .weight] | @tsv' "$RUN/w-sample-<rule>.json" \
  | awk -F'\t' '{w[$1] += $2; t += $2} END {for (i in w) printf "%d\t%.1f%%\t%s\n", w[i], 100 * w[i] / t, i}' \
  | sort -rn | head -10
```
<!-- doc: https://jqlang.org/manual/ -->

## Identity triangulation

A client is never "one user" on the strength of an IP address. Combine what the sample offers:

- **IP and country,** from the sample;
- **a hashed client key:** the value of the session cookie or client-ID header that the service profile names, hashed in the pipe and cut to 12 characters;
- **header shape:** the ordered list of header names (`headerNames`), which differs between browsers, mobile clients, SDKs and scripts;
- **TLS fingerprint (JA3/JA4):** WAF computes it and writes it to the logs only; sampled requests do not carry it. In this version it is a gap.
<!-- doc: https://docs.aws.amazon.com/sdk-for-kotlin/api/latest/wafv2/aws.sdk.kotlin.services.wafv2.model/-field-to-match/-builder/ja4-fingerprint.html -->

The client key is extracted and hashed without the value ever being printed or stored:

```bash
aws wafv2 get-sampled-requests --profile <profile> --region <region> \
  --web-acl-arn <acl-arn> --rule-metric-name <rule-metric> --scope <REGIONAL|CLOUDFRONT> \
  --time-window StartTime=<start-utc>,EndTime=<end-utc> --max-items 500 --output json \
  | jq -r '.SampledRequests[] | [.Request.ClientIP,
      ((([.Request.Headers[] | select(.Name | ascii_downcase == "cookie") | .Value][0] // "")
        | capture("(^|;\\s*)<cookie-name>=(?<v>[^;]*)") | .v) // "-"), .Weight] | @tsv' \
  | while IFS=$'\t' read -r ip key w; do
      if [ "$key" != "-" ]; then h=$(printf '%s' "$key" | sha256sum | cut -c1-12); else h=none; fi
      printf '%s\t%s\t%s\n' "$ip" "$h" "$w"
    done > "$RUN/w-identity-<rule>.tsv"
```
<!-- doc: https://jqlang.org/manual/ -->

For a client-ID header instead of a cookie, select that header's name and drop the `capture`. Then count distinct hashes per IP and distinct IPs per hash (weighted, as above), and read the result against this table:

| What the sample shows | Likely reading | What to check next |
|---|---|---|
| One IP carries a large share of requests, with many distinct client keys and ordinary header shapes behind it | Shared egress: carrier-grade NAT, a corporate proxy, a VPN exit | Spread of countries and user agents behind it; whether a rate-based rule keyed on IP is what blocks them |
| One client key across many IPs | One client rotating addresses, or one account being abused | That key's request rate and paths; whether the IPs share a country or network |
| Many IPs with the same user agent, the same sparse header-name list and the same path pattern, few or no client keys | A bot fleet | Rate-based and bot-control rule metrics; TLS fingerprints from the logs (gap in this version) |
| A broad rise across normal user agents, countries and header shapes, starting at a deploy, a client release or a campaign | Ordinary users whose traffic changed, tripping a rule (a false positive) or a real customer-driven load change | The rule's own −7 day baseline, the labels it applied, and the changes playbook for what started at that minute |

**COUNT-mode rules: what they would have blocked.** For each COUNT-mode rule, `CountedRequests` against −7 days says how much traffic it would have blocked had it been switched to `BLOCK`. A sample of that rule shows who. This is how to judge the impact of a rule someone wants to enable, and how to spot a rule that was recently switched from COUNT to BLOCK (its `BlockedRequests` appears as its `CountedRequests` disappears; confirm the switch in the changes playbook's CloudTrail recipe).

## Gotchas

- **WAF status is not origin status.** A blocked request never reached the origin; an allowed request's real status is only in the CDN or load balancer logs.
- **No datapoint means zero.** All `AWS/WAFV2` metrics are reported only when non-zero, so a gap in a WAF series is zero, unlike most metrics. Check the dimension values first anyway: a misspelt rule metric name also returns nothing.
- **CloudFront scope.** The ACL, its metrics and its samples are all read in `us-east-1`, and the metrics have no `Region` dimension.
- **Count rules inside rule groups.** A Count action inside a rule group emits metrics with `Rule`, `RuleGroup` and `Region` dimensions, not `WebACL`; rule groups owned by another account show their per-rule metrics only to the owner unless the action is overridden in your ACL.
- **A sample is not a count.** Quote totals from CloudWatch. Quote sample-derived numbers as "in a sample of N out of `population` requests, between `<window start>` and `<window end>` UTC", and say when a weight was applied.
- **Three hours.** Samples older than three hours cannot be requested. For an older incident, rung 1 is all this version can read; the rest is a gap with its "To confirm" sentence.
- **Headers and cookies.** Sampled requests contain every request header, including cookies and authorization headers. Never store or quote a cookie value or an authorization header value: refer to them by header or cookie name, or by the short hash when identity matters. Never quote a full query string or a referer. Quote an IP, a user agent or a hash only when it is the finding; otherwise refer to the client by hash.
- **ACL with no rules.** An ACL associated with an Application Load Balancer but holding no rules or other active configuration publishes no metrics and no samples for it.

## What to write in the ledger

- the ACL (name, scope, Region) and, per rule read, its action, mode (COUNT or not) and metric name;
- per metric query: rule, metric, period, incident and −7 day sums, and the shape (when it started, peak 5-minute value);
- per sample: the rule metric name, the requested window, the returned window, `population`, number of rows and how weights were used;
- concentration results: top IPs and top hashes with their weighted shares, the table row that fits, and the confidence label (a sample-only reading is at most Likely);
- the logging filter (what is and is not logged);
- gaps: logs not read, TLS fingerprints unavailable, samples out of the three-hour range, each with its "To confirm" sentence;
- a deeplink for a human: the WAF console page of the ACL with the rule and window, or the CloudWatch console link for the same metrics. Never a link or note carrying a header or cookie value.
