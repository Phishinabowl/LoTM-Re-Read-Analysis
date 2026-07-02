# Visualization

This folder contains generated visualization artifacts for the Lord of the Mysteries re-read analysis project.

Generated graph files are not the source of truth. The canonical project data remains in:

- Glossary thread metadata
- Reader Knowledge Ledgers
- Relationship Seeds
- The controlled relationship taxonomy in `PROJECT_RULES.md`

Mermaid graphs are generated from glossary metadata and Relationship Seeds. If a graph exposes missing, stale, or incorrect information, fix the glossary thread, investigation record, or relationship seed first, then regenerate the graph.

## Current Artifacts

- [Volume 1 Knowledge Graph](graphs/volume-1-knowledge-graph.mmd)
- [Volume 1 Knowledge Graph - Timing Spoiler-Free](graphs/volume-1-knowledge-graph-timing-spoiler-free.mmd)
- [Graph Schema Notes](data/graph-schema.md)
- [Rendering Instructions](rendering.md)

The `rendered/` folder is reserved for future generated SVG or PNG graph exports.

## Refresh Tracker

After every graph refresh, update the live refresh tracker below. It summarizes node count, relationship count, semantic graph changes, views updated, rendered files, broken links, orphan nodes, duplicate relationships, and pending graph nodes.

The tracker compares the current graph against the semantic snapshot in `data/refresh-snapshot.json`. Unexpected removed nodes, removed relationships, changed relationship labels, duplicate relationships, broken links, or orphan nodes should be treated as visualization validation issues and reviewed before committing.

<!-- VISUALIZATION-REFRESH-REPORT:START -->
Last Updated: 2026-07-02 02:06:03 -04:00

### Summary

| Metric | Count | Delta |
| --- | ---: | ---: |
| Nodes | 26 | 0 |
| Relationships | 72 | 0 |
| Views Updated | 2 | 0 |
| Rendered Files | 4 | 0 |
| Broken Links | 0 | 0 |
| Orphan Nodes | 0 | 0 |
| Pending Nodes | 17 | 0 |
| Validation Issues | 0 | n/a |

### Semantic Changes

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

- `Visualization/rendered/volume-1-knowledge-graph.svg` (136398 bytes)
- `Visualization/rendered/volume-1-knowledge-graph.png` (451848 bytes)
- `Visualization/rendered/volume-1-knowledge-graph-timing-spoiler-free.svg` (136084 bytes)
- `Visualization/rendered/volume-1-knowledge-graph-timing-spoiler-free.png` (471047 bytes)

### Hygiene

- Broken links: 0
- Orphan nodes: 0
- Duplicate relationships: 0
- Removed relationships: 0
- Changed relationship labels: 0
- Pending graph nodes: 17

#### Pending Nodes

- `character-azik-eggers.md`
- `character-daly-simone.md`
- `character-frye.md`
- `character-ince-zangwill.md`
- `character-kenley-white.md`
- `character-klein-moretti.md`
- `character-leonard-mitchell.md`
- `character-mrs-orianna.md`
- `character-ray-bieber.md`
- `character-royale-reideen.md`
- `character-rozanne.md`
- `character-roselle-gustav.md`
- `character-seeka-tron.md`
- `faction-nighthawks.md`
- `faction-secret-order.md`
- `pathway-corpse-collector.md`
- `pathway-mystery-pryer.md`
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

When a refresh is confirmed, update every current graph view unless the user explicitly narrows the scope. For this repository, that means both current Mermaid graph files plus fresh replacement renders in the currently used formats:

- `graphs/volume-1-knowledge-graph.mmd`
- `graphs/volume-1-knowledge-graph-timing-spoiler-free.mmd`
- matching rendered SVG files, when present
- matching rendered PNG files, when present

Fresh renders replace stale render files unless the user asks for archived snapshots.

Canonical refresh command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\render-graphs.ps1
```

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
