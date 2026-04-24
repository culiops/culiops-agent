# orders — diagrams-only / GCP fixture (real-discovery path)

A synthetic repo used to validate the `service-discovery` skill's real-discovery path with **diagrams only** — no text documentation and no IaC files. The skill must parse structured and image diagrams without any supporting text context, then use GCP cloud APIs (read-only) to build the service catalog.

## What's modelled

`orders` is a fictional order management API on GCP.

- **Entry point:** Cloud Load Balancing (implicit in Cloud Run) routing HTTPS traffic.
- **Compute:** Cloud Run service (`orders-api`).
- **Database:** Cloud SQL PostgreSQL 15 (`orders-db`).
- **Cache:** Memorystore Redis (`orders-cache`).
- **Async:** Pub/Sub topic (`orders-events`) for order lifecycle events.
- **Storage:** Cloud Storage bucket (`orders-attachments`) for order document uploads.

## What this fixture exercises in the skill

| Principle | Exercised by |
|-----------|--------------|
| Detection routing | No IaC files → doc signatures detected → real-discovery path |
| Diagrams without text documentation | Only `.mmd` and `.png` files — no markdown, no runbooks, no text docs |
| Mermaid structured parsing | `system-architecture.mmd` matched by `doc-detectors/mermaid.md` — flowchart nodes, edges, and subgraph groupings |
| Image vision fallback | `network-topology.png` matched by `doc-detectors/image.md` — placeholder image; DRY-RUN-NOTES describes what vision would extract |
| GCP cloud context and discovery | GCP project `orders-prod`, region `us-central1` — uses `cloud-discovery/gcp.md` templates |
| No text context for cloud resolution | Region not specified in any diagram — skill must ask operator during Step 3R |

## Files

| File | Purpose |
|------|---------|
| `system-architecture.mmd` | Valid Mermaid flowchart with GCP resource nodes, relationships, and project subgraph |
| `network-topology.png` | 1x1 pixel placeholder PNG — simulates a network topology diagram for vision analysis |
