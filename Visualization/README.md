# Visualization

This folder contains generated visualization artifacts for the Lord of the Mysteries re-read analysis project.

Generated graph files are not the source of truth. The canonical project data remains in:

- Glossary thread metadata
- Embedded Reader Knowledge Ledger sections in glossary threads
- Relationship Seeds
- The controlled relationship taxonomy in `PROJECT_RULES.md`

Generated Mermaid graphs are generated from glossary metadata and Relationship Seeds. If a canonical graph refresh exposes missing, stale, or incorrect information, fix the glossary thread, investigation record, or relationship seed first, then regenerate the graph. Manual maintainer graphs may include clearly marked graph-local evidence before those project-data updates are confirmed.

Page-level reader visibility belongs to glossary metadata through `Subject Visible From`; do not model it as a Relationship Seed. Filtered graph views use that metadata as the node-level gate before applying relationship or claim-level timing.

Configured graph views may declare a `readerBoundary` in `config/render-settings.json`. When present, generation includes only nodes whose `Subject Visible From` is eligible for that medium/volume/chapter boundary and only relationship seeds whose `start.medium`, `start.volume`, and `start.chapter` are eligible. Unknown subject visibility or unknown relationship positions are excluded unless the view explicitly opts into them. The current Volume 1 graph views are novel-only reader-boundary views through Volume 1 Chapter 213, so official-artwork taxonomy seeds and later cosmology links do not appear there.

Shared graph authoring rules live in [Graph Authoring Standard](graph-authoring-standard.md). Use that standard for both AI Agent graph requests and maintainer/project graph work before rendering.

## AI Agent Graph Request Routing

Graph and visualization requests are repository workflow requests by default.

When an AI assistant is asked to create a graph, visualization, Mermaid diagram, relationship map, pathway map, timeline map, or rendered image, it should not begin by creating an ad hoc Mermaid file outside this folder.

First classify the request:

1. **Canonical graph refresh**: update generated graph artifacts from Relationship Seeds and graph inputs.
2. **Repository-local manual graph**: create a manual `.mmd` source under `Visualization/graphs/` and render it through repository tooling.
3. **Chat-only scratch graph**: produce temporary Mermaid only when the user explicitly asks for scratch, temporary, chat-only, or outside-repository output.

Complex, relationship-heavy, evidence-bearing, or rendered graph requests default to repository-local artifacts, not scratch outputs.

For rendered outputs, repository tooling means the visualization helpers documented in [rendering.md](rendering.md), not direct `mmdc` calls. Prefer the Python helper and use the PowerShell helper as the Windows fallback. Direct `mmdc` is a fallback/debug path only, and should be reported as degraded if used because the helper scripts are unavailable or cannot run in the current environment.

## Projection Style

Dense relationship graphs should use semantic relationship nodes instead of long Mermaid edge labels.

Preferred dense projection:

```mermaid
graph TD
  source_node["Source"]
  rel_001["relationship type<br/>timing/status/confidence"]
  target_node["Target"]
  source_node --> rel_001
  rel_001 --> target_node
```

Relationship nodes are generated presentation nodes. They are not glossary nodes and are not canonical project knowledge. They exist to make rendered graphs easier to read, especially when many relationships share the same source, target cluster, or semantic hub.

Simple one-off diagrams may still use edge labels when they remain readable. For repository-wide or relationship-heavy views, prefer relationship nodes by default.

## Current Artifacts

- [Volume 1 Knowledge Graph](graphs/volume-1-knowledge-graph.mmd)
- [Volume 1 Knowledge Graph - Timing Spoiler-Free](graphs/volume-1-knowledge-graph-timing-spoiler-free.mmd)
- [Graph Schema Notes](data/graph-schema.md)
- [Graph Authoring Standard](graph-authoring-standard.md)
- [Rendering Instructions](rendering.md)

The `rendered/` folder contains generated SVG and PNG graph exports for review, sharing, and archive inspection.

## Refresh Tracker

After every graph refresh, update the live refresh tracker below. It summarizes configured views, per-view node and relationship counts, per-view semantic graph changes, rendered files, broken links, orphan nodes, duplicate relationships, and pending graph nodes.

The tracker compares each configured view against the semantic snapshot in `data/refresh-snapshot.json`. Unexpected removed nodes, removed relationships, changed relationship labels, duplicate relationships, broken links, or orphan nodes should be treated as visualization validation issues and reviewed before committing.

<!-- VISUALIZATION-REFRESH-REPORT:START -->
Last Updated: 2026-07-04 10:42:12 -04:00

### Summary

| Metric | Count | Delta |
| --- | ---: | ---: |
| Views Updated | 2 | 0 |
| Rendered Files | 4 | 0 |
| Broken Links | 0 | 0 |
| Pending Nodes | 20 | 0 |
| Validation Issues | 0 | n/a |

### View Summary

| View | Nodes | Delta | Relationships | Delta | Orphan Nodes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Volume 1 Knowledge Graph | 28 | 0 | 75 | 0 | 0 |
| Volume 1 Knowledge Graph - Timing Spoiler-Free | 28 | 0 | 75 | 0 | 0 |

### Semantic Changes

#### Volume 1 Knowledge Graph

- Added nodes: 0
- Removed nodes: 0
- Added relationships: 0
- Removed relationships: 0
- Changed relationship labels: 0
- Duplicate relationships: 0

#### Volume 1 Knowledge Graph - Timing Spoiler-Free

- Added nodes: 0
- Removed nodes: 0
- Added relationships: 0
- Removed relationships: 0
- Changed relationship labels: 0
- Duplicate relationships: 0

### Views

- Volume 1 Knowledge Graph: `Visualization/graphs/volume-1-knowledge-graph.mmd`
- Volume 1 Knowledge Graph - Timing Spoiler-Free: `Visualization/graphs/volume-1-knowledge-graph-timing-spoiler-free.mmd`

### Rendered Outputs

- `Visualization/rendered/volume-1-knowledge-graph.svg` (306748 bytes)
- `Visualization/rendered/volume-1-knowledge-graph.png` (785561 bytes)
- `Visualization/rendered/volume-1-knowledge-graph-timing-spoiler-free.svg` (305686 bytes)
- `Visualization/rendered/volume-1-knowledge-graph-timing-spoiler-free.png` (695182 bytes)

### Hygiene

- Broken links: 0
- Orphan nodes: 0
- Duplicate relationships: 0
- Removed relationships: 0
- Changed relationship labels: 0
- Pending graph nodes: 20

#### Pending Nodes

- `character-azik-eggers.md (artwork backed)`
- `character-bethel-abraham.md (notes: [preliminary planning](../Investigations/Characters/character-bethel-abraham/preliminary-planning-investigation.md))`
- `character-daly-simone.md (artwork backed)`
- `character-frye.md`
- `character-ince-zangwill.md (artwork backed)`
- `character-kenley-white.md`
- `character-klein-moretti.md (artwork backed, 10 images)`
- `character-leonard-mitchell.md (artwork backed)`
- `character-mrs-orianna.md`
- `character-ray-bieber.md`
- `character-royale-reideen.md`
- `character-rozanne.md`
- `character-roselle-gustav.md (artwork backed)`
- `character-seeka-tron.md`
- `faction-nighthawks.md`
- `faction-secret-order.md`
- `pathway-corpse-collector.md`
- `pathway-criminal.md (artwork backed; notes: [preliminary planning](../Investigations/Pathways/pathway-criminal/preliminary-planning-investigation.md))`
- `pathway-mystery-pryer.md (artwork backed)`
- `pathway-prisoner.md (artwork backed)`
<!-- VISUALIZATION-REFRESH-REPORT:END -->

## Refresh Rules

Regenerate graph artifacts when graph inputs change:

- glossary pages are created, deleted, renamed, or moved
- `Relationship Seeds` are added, removed, or changed
- relationship type, status, confidence, source, or target changes
- node type or graph-relevant metadata changes
- the controlled relationship taxonomy changes

Graph regeneration is not required for prose-only investigation updates, typo fixes, wording cleanup, or board prose that does not change graph inputs.

Before editing generated visualization files, recommend the refresh and confirm it with the user.

When a refresh is confirmed, update every configured graph view in `config/render-settings.json` unless the user explicitly narrows the scope. Each configured view owns its Mermaid source path and rendered output paths.

Fresh renders replace stale render files unless the user asks for archived snapshots.

Before choosing a helper on an unfamiliar machine or fresh agent session, run the Python availability probe documented in [Rendering Instructions](rendering.md). Treat the result as the session's Python-availability state. If Python is available, use the Python commands going forward without rerunning the probe before every render command. If Python is unavailable, use the PowerShell fallback command for that session.

Canonical refresh command:

Preferred Python:

```powershell
python Visualization\visualize.py --mode Refresh
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Refresh
```

Compatibility validation command:

Preferred Python:

```powershell
python Visualization\visualize.py --mode Validate
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Validate
```

Validation mode checks glossary node parsing, Relationship Seed parsing, configured graph class/layout validation, and fresh temp graph generation without updating generated graph files, rendered images, the semantic snapshot, or this refresh tracker.

Pure render command for manually authored `.mmd` files:

Preferred Python:

```powershell
python Visualization\visualize.py --mode Render --input-path Visualization\graphs\example.mmd
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Render -InputPath Visualization\graphs\example.mmd
```

Pure render mode uses the same Puppeteer and render-size settings as the canonical refresh command, but it does not regenerate graph files, update the semantic snapshot, or update this refresh tracker.

## Long-Term Vision

The long-term goal is a dynamic graph layer generated from normalized relationship data rather than manually maintained diagrams.

Future graph views may support:

- Dynamic graph generation from Relationship Seeds and normalized graph data
- Timeline filtering by novel chapter, Donghua episode, and in-world chronology
- Reader-state filtering by spoiler boundary and reader knowledge boundary
- Interactive frontend exploration
- Multiple graph views, such as character networks, faction maps, pathway views, artifact causality maps, and event-centered graphs
- Filters by node type, relationship type, confidence, truth status, medium, and controlled taxonomy tags
- Expanded visualization validation for required relationship patterns, stale pending nodes, and generated graph subsets

Until that layer exists, Mermaid files provide a GitHub-visible snapshot of the current graph.
