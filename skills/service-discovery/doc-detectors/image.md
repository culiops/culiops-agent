---
name: image
extensions: ".png, .svg, .jpg, .jpeg, .webp"
type: image
---

## File signatures
- `*.png`, `*.svg`, `*.jpg`, `*.jpeg`, `*.webp`
- Filename patterns that increase relevance (only process images matching these unless the operator explicitly includes others):
  - `*arch*` (architecture)
  - `*infra*` (infrastructure)
  - `*diagram*` (diagram)
  - `*topology*` (topology)
  - `*network*` (network)
  - `*deploy*` (deployment)
  - `*system*` (system)
  - `*overview*` (overview)
- Non-matching filenames are skipped unless the operator includes them via explicit path

## Parsing method
Claude vision capability. Send the image to Opus with the following analysis prompt:

```
Analyze this infrastructure or architecture diagram. Extract the following as structured lists:

1. **Resources**: For each resource visible in the diagram, provide:
   - Type (e.g., RDS, EC2, Lambda, S3, Load Balancer, Cache, Queue)
   - Name (label text on or near the resource)
   - Cloud provider (if identifiable from icons, shapes, or labels)
   - Confidence: "high" if the resource type is clearly indicated by a cloud-provider icon or explicit label, "low" if inferred from shape or position alone
   - Mark uncertain items with [uncertain]

2. **Relationships**: For each connection/arrow in the diagram, provide:
   - Source resource
   - Target resource
   - Label on the connection (if any)
   - Confidence: "high" if the arrow and endpoints are clear, "low" if inferred

3. **Cloud context**:
   - Cloud provider(s) identified
   - Region(s) mentioned
   - Account/project identifiers visible
   - VPC/network boundaries shown

4. **Service boundaries**: Logical groupings visible (boxes, shaded areas, labeled regions)

If you cannot confidently identify a resource type, still list it with [uncertain] and describe what you see (shape, color, position). Prefer over-reporting with uncertainty markers to under-reporting.
```

Return the structured lists exactly as produced by the model. Do not attempt post-processing or confidence filtering — the operator will review all items.

## What to extract
- **Resource types**: from cloud-provider icons, shape conventions (cylinder = database, hexagon = service), and label text
- **Resource names**: from label text on or adjacent to shapes
- **Relationships**: from arrows and connection lines between resources
- **Cloud context**: from provider logos, region labels, account annotations
- **Service boundaries**: from visual groupings (boxes, shaded regions, dashed borders)

## Extraction examples

An image showing an AWS architecture with an ALB forwarding to two ECS services, each connecting to an RDS database, all inside a VPC labeled "us-east-1":

**Extracted hints:**

- Resource: type=ALB, name="api-alb", cloud=AWS, confidence=high
- Resource: type=ECS Service, name="order-service", cloud=AWS, confidence=high
- Resource: type=ECS Service, name="payment-service", cloud=AWS, confidence=high
- Resource: type=RDS, name="orders-db", cloud=AWS, confidence=high
- Resource: type=RDS, name=[uncertain] (second database icon, label not readable), cloud=AWS, confidence=low
- Relationship: api-alb → order-service, confidence=high
- Relationship: api-alb → payment-service, confidence=high
- Relationship: order-service → orders-db, confidence=high
- Relationship: payment-service → [uncertain database], confidence=low
- Context: cloud=AWS, region=us-east-1, boundary=VPC

## Limitations
- **Lowest reliability**: image analysis produces the least reliable resource hints of any detector; always requires operator confirmation before hints are used
- **Operator confirmation essential**: never auto-merge image-extracted hints into the resource inventory without explicit operator review
- **Hand-drawn and whiteboard diagrams**: lower quality input produces lower confidence output; heavily stylized or hand-drawn diagrams may yield mostly `[uncertain]` items
- **SVG special case**: SVG files contain text as XML elements; attempt text extraction from the SVG XML first (treat as structured data), and fall back to vision only if the SVG structure is too complex to parse as text
- **Token-heavy**: image analysis consumes significantly more tokens than text-based extraction; budget accordingly and prefer other detectors when the same information is available in a structured or text format
- **Screenshot artifacts**: screenshots of web consoles or dashboards may contain UI chrome, tooltips, and overlapping elements that confuse resource identification
- **Multi-page or composite images**: a single image file may contain multiple diagrams or views tiled together; each sub-diagram may represent different aspects of the architecture
