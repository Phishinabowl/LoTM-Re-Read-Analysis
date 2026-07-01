# Graph Data Schema

This document describes the provisional graph data model for future generated graph data.

The schema is not stable yet. It will evolve as the glossary archive grows, relationship seeds are normalized, and graph generation moves from static Mermaid snapshots toward dynamic data-driven views.

## Source of Truth

Graph data should be generated from project records, not maintained directly.

Canonical inputs include:

- Glossary thread metadata
- Reader Knowledge Ledger entries
- Relationship Seeds
- Controlled relationship and tag taxonomies in `PROJECT_RULES.md`
- Supporting investigation records when evidence provenance is needed

## Node Fields

Potential node fields:

```yaml
node_id:
label:
node_type:
source_file:
first_seen_novel_chapter:
first_seen_donghua_episode:
spoiler_boundary:
reader_knowledge_boundary:
tags:
```

Field notes:

- `node_id`: Stable lowercase kebab-case identifier, normally matching the glossary filename without extension.
- `label`: Human-readable display label, usually the glossary page H1.
- `node_type`: Controlled glossary type, such as Character, Artifact, Faction, Concept, Event, Pathway, or Location.
- `source_file`: Glossary file where the node is defined, if it exists.
- `first_seen_novel_chapter`: Earliest verified novel chapter where the node is meaningfully available to the reader.
- `first_seen_donghua_episode`: Earliest verified Donghua episode or release-order position where the node is meaningfully available to the viewer.
- `spoiler_boundary`: Broad canon boundary for the node's current article.
- `reader_knowledge_boundary`: Exact reader/viewer boundary used by the node's current article.
- `tags`: Controlled tags from `PROJECT_RULES.md`.

## Relationship Fields

Potential relationship fields:

```yaml
relationship_id:
source_node:
target_node:
relationship_type:
confidence_level:
truth_status:
medium:
novel_chapter:
donghua_episode:
in_world_chronology:
related_investigation:
```

Field notes:

- `relationship_id`: Stable generated identifier, likely derived from source, target, relationship type, and start position.
- `source_node`: Source node id.
- `target_node`: Target node id.
- `relationship_type`: Controlled relationship type from `PROJECT_RULES.md`.
- `confidence_level`: Controlled qualitative confidence where applicable.
- `truth_status`: Claim status where applicable, especially when relationships are generated from knowledge units.
- `medium`: Source medium for the relationship disclosure, such as novel, Donghua, or both.
- `novel_chapter`: Novel chapter where the relationship becomes reader-safe or is first verified.
- `donghua_episode`: Donghua episode or release-order position where the relationship becomes viewer-safe or is first verified.
- `in_world_chronology`: Optional story-chronology position when it differs from reader disclosure order.
- `related_investigation`: Supporting investigation record, if the relationship depends on source verification.

## Future Filters

Future graph generation may support filtering by:

- Node type
- Relationship type
- Confidence
- Truth status
- Medium
- Novel chapter
- Donghua episode
- In-world chronology
- Spoiler boundary
- Reader knowledge boundary
- Controlled taxonomy tags

## Rendering Targets

Potential generated outputs include:

- Mermaid `.mmd` files
- SVG or PNG graph renders
- JSON graph data
- Interactive frontend graph views

Generated outputs should be reproducible from canonical project data.
