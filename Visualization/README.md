# Visualization

This folder contains generated visualization artifacts for the Lord of the Mysteries re-read analysis project.

Generated graph files are not the source of truth. The canonical project data remains in:

- Glossary thread metadata
- Reader Knowledge Ledgers
- Relationship Seeds
- The controlled relationship taxonomy in `PROJECT_RULES.md`

Mermaid graphs are generated from glossary metadata and Relationship Seeds. If a graph exposes missing, stale, or incorrect information, fix the glossary thread, investigation record, or relationship seed first, then regenerate the graph.

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

## Current Artifacts

- [Volume 1 Knowledge Graph](graphs/volume-1-knowledge-graph.mmd)
- [Volume 1 Knowledge Graph - Timing Spoiler-Free](graphs/volume-1-knowledge-graph-timing-spoiler-free.mmd)
- [Graph Schema Notes](data/graph-schema.md)
- [Rendering Instructions](rendering.md)

The `rendered/` folder is reserved for future generated SVG or PNG graph exports.

## Long-Term Vision

The long-term goal is a dynamic graph layer generated from normalized relationship data rather than manually maintained diagrams.

Future graph views may support:

- Dynamic graph generation from Relationship Seeds and normalized graph data
- Timeline filtering by novel chapter, Donghua episode, and in-world chronology
- Reader-state filtering by spoiler boundary and reader knowledge boundary
- Interactive frontend exploration
- Multiple graph views, such as character networks, faction maps, pathway views, artifact causality maps, and event-centered graphs
- Filters by node type, relationship type, confidence, truth status, medium, and controlled taxonomy tags

Until that layer exists, Mermaid files provide a GitHub-visible snapshot of the current graph.
