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
- [Graph Schema Notes](data/graph-schema.md)

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
