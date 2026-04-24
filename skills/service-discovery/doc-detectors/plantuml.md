---
name: plantuml
extensions: ".puml, .plantuml, .pu, .iuml"
type: structured
---

## File signatures
- `*.puml`
- `*.plantuml`
- `*.pu`
- `*.iuml`
- Files beginning with `@startuml`

## Parsing method
Text parsing of PlantUML syntax between `@startuml` and `@enduml` markers.

1. **Diagram type**: infer from keywords after `@startuml`. Relevant types: deployment diagrams (`node`, `database`, `queue`, `artifact`, `cloud`), component diagrams (`component`, `interface`, `package`), network diagrams (`nwdiag`). Skip: class diagrams (`class`, `abstract`), sequence diagrams (`participant`, `actor`), activity diagrams (`start`, `stop`, `:action;`).
2. **Node declarations**: `node "Label" as alias`, `database "Label" as alias`, `queue "Label" as alias`, `cloud "Label" as alias`, `component "Label" as alias`, `storage "Label" as alias`, `artifact "Label" as alias`. The keyword itself provides a resource type hint (database, queue, etc.).
3. **Relationships**: `-->`, `->`, `..>`, `--`, with optional labels `: label`. Extract source, target, and label.
4. **Groupings**: `package "Label" { ... }`, `rectangle "Label" { ... }`, `cloud "Label" { ... }`, `node "Label" { ... }`. Nested groupings represent service boundaries.
5. **Stdlib includes**: `!include <awslib/...>`, `!include <azure/...>`, `!include <gcp/...>`, `!include <cloudinsight/...>`. These import cloud-provider icon macros. After an include, macros like `RDS(alias, "Label", "tech")`, `Lambda(alias, "Label")`, `EC2(alias, "Label")` declare resources with explicit cloud types.

## What to extract
- **Resource types**: from PlantUML keywords (`database`, `queue`, `cloud`, `node`), from stdlib macro names (`RDS`, `Lambda`, `EC2`, `S3Bucket`, `CloudSQL`, `AKS`), and from label text containing resource type keywords
- **Resource names**: from quoted labels in node declarations and stdlib macro invocations
- **Relationships**: from arrows between aliases/nodes, with edge labels
- **Cloud context**: from stdlib include paths (e.g., `<awslib/...>` → AWS), from `cloud` groupings labeled with regions or provider names
- **Service boundaries**: from `package`, `rectangle`, `cloud`, and `node` groupings
- **Technology metadata**: from the third argument of stdlib macros (e.g., `RDS(db, "orders-db", "PostgreSQL")` → engine=PostgreSQL)

## Extraction examples

**Raw PlantUML with AWS stdlib:**

```plantuml
@startuml
!include <awslib/AWSCommon>
!include <awslib/NetworkingContentDelivery/ELBApplicationLoadBalancer>
!include <awslib/Compute/Lambda>
!include <awslib/Database/RDS>
!include <awslib/Database/ElastiCacheForRedis>

rectangle "us-west-2" {
  ELBApplicationLoadBalancer(alb, "api-alb", "HTTPS")

  package "order-service" {
    Lambda(orderFn, "order-handler", "Node.js 20")
  }

  RDS(orderDb, "orders-db", "PostgreSQL 15")
  ElastiCacheForRedis(cache, "session-cache", "Redis 7")
}

alb --> orderFn : /api/orders
orderFn --> orderDb : port 5432
orderFn --> cache : port 6379
@enduml
```

**Extracted hints:**

- Resource: type=ALB, name="api-alb", cloud=AWS, protocol=HTTPS (from `ELBApplicationLoadBalancer` macro)
- Resource: type=Lambda, name="order-handler", cloud=AWS, runtime=Node.js 20 (from `Lambda` macro)
- Resource: type=RDS, name="orders-db", cloud=AWS, engine=PostgreSQL 15 (from `RDS` macro)
- Resource: type=ElastiCache Redis, name="session-cache", cloud=AWS, engine=Redis 7 (from `ElastiCacheForRedis` macro)
- Relationship: api-alb → order-handler (/api/orders)
- Relationship: order-handler → orders-db (port 5432)
- Relationship: order-handler → session-cache (port 6379)
- Context: region=us-west-2 (from rectangle grouping)
- Boundary: service=order-service (from package grouping)

## Limitations
- **Stdlib version variance**: macro names and paths differ between stdlib versions (e.g., `awslib` vs `aws` vs `AWSPuml`); match on macro name patterns rather than exact paths
- **External includes**: `!include` directives referencing URLs or local file paths outside the repo cannot be resolved; record the include as a reference but do not chase it
- **Sequence diagrams**: PlantUML sequence diagrams show message flow between participants, not infrastructure topology; skip these to avoid extracting "participants" as resources
- **Preprocessor directives**: `!define`, `!ifdef`, `!procedure` and other preprocessor features can obscure the actual diagram content; parse the literal text without evaluating preprocessor logic
- **Multi-diagram files**: a single file may contain multiple `@startuml` ... `@enduml` blocks; parse each block independently
