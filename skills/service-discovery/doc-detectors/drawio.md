---
name: drawio
extensions: ".drawio, .drawio.xml"
type: structured
---

## File signatures
- `*.drawio`
- `*.drawio.xml`
- XML files with root element `<mxfile>` or `<mxGraphModel>`

## Parsing method
XML parsing of `<mxCell>` elements within `<mxGraphModel>` → `<root>`.

1. **Nodes**: `<mxCell>` elements with a `value` attribute containing a label. Strip HTML tags from values (labels are often wrapped in `<div>`, `<b>`, `<font>`, etc.).
2. **Edges**: `<mxCell>` elements with both `source` and `target` attributes. These represent relationships between nodes.
3. **Shape hints**: The `style` attribute on `<mxCell>` encodes shape type. Cloud-provider stencils embed resource types directly (e.g., `shape=mxgraph.aws4.rds`, `shape=mxgraph.gcp2.cloud_sql`, `shape=mxgraph.azure.database`). Parse the `style` string as semicolon-delimited key=value pairs.
4. **Containers**: `<mxCell>` elements with a non-empty `children` attribute or with `container=1` in the style. These may represent VPCs, regions, accounts, or service boundaries.

## What to extract
- **Resource types**: from shape style values (e.g., `mxgraph.aws4.rds` → RDS, `mxgraph.aws4.lambda` → Lambda) and from label text containing resource type keywords
- **Resource names**: from the `value` attribute (node labels), after stripping HTML
- **Relationships**: from edge `source`/`target` pairs, with optional edge labels from the edge's `value` attribute
- **Cloud context**: from container nodes labeled with regions (e.g., "us-east-1"), accounts, or cloud provider names
- **Service boundaries**: from container/group nodes representing logical groupings (VPC, subnet, availability zone, namespace)

## Extraction examples

**Raw XML fragment:**

```xml
<mxCell id="2" value="&lt;b&gt;api-gateway&lt;/b&gt;" style="shape=mxgraph.aws4.api_gateway;..." vertex="1" parent="vpc-1">
  <mxGeometry x="100" y="200" width="60" height="60" as="geometry"/>
</mxCell>
<mxCell id="3" value="orders-db" style="shape=mxgraph.aws4.rds;..." vertex="1" parent="vpc-1">
  <mxGeometry x="300" y="200" width="60" height="60" as="geometry"/>
</mxCell>
<mxCell id="4" value="" style="edgeStyle=orthogonalEdgeStyle;" edge="1" source="2" target="3" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
<mxCell id="vpc-1" value="us-east-1 / VPC" style="rounded=1;container=1;" vertex="1" parent="1">
  <mxGeometry x="50" y="100" width="400" height="300" as="geometry"/>
</mxCell>
```

**Extracted hints:**

- Resource: type=API Gateway, name="api-gateway", cloud=AWS (from `mxgraph.aws4.*`)
- Resource: type=RDS, name="orders-db", cloud=AWS (from `mxgraph.aws4.*`)
- Relationship: "api-gateway" → "orders-db"
- Context: region=us-east-1, boundary=VPC (from container node "vpc-1")

## Limitations
- **Abbreviated labels**: diagram authors often use short names ("db", "cache") that don't match actual resource names; treat as hints, not authoritative names
- **Nested groups**: container hierarchies may not map cleanly to cloud concepts (a group labeled "Backend" is informational, not a cloud construct)
- **Freeform shapes**: diagrams that use generic rectangles and arrows without cloud stencils yield resource type hints only from label text, which is lower confidence
- **Compressed content**: some `.drawio` files store diagram XML in a deflate-compressed, base64-encoded format inside the `<diagram>` element; decompress before parsing
- **Multi-page diagrams**: a single `.drawio` file may contain multiple `<diagram>` elements (pages); parse all pages
