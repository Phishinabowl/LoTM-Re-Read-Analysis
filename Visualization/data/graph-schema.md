# Graph Data Schema

This document describes the provisional graph data model for future generated graph data.

The schema is not stable yet. It will evolve as the glossary archive grows, relationship seeds are normalized, and graph generation moves from static Mermaid snapshots toward dynamic data-driven views.

## Source of Truth

Graph data should be generated from project records, not maintained directly.

Canonical inputs include:

- Glossary thread metadata
- Embedded Reader Knowledge Ledger entries in glossary threads
- Type-specific data blocks in glossary threads
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
source_layer:
canonicalization_status:
subject_visible_from:
first_seen_novel_chapter:
first_seen_donghua_episode:
spoiler_boundary:
reader_knowledge_boundary:
tags:
```

Field notes:

- `node_id`: Stable lowercase kebab-case identifier, normally matching the glossary filename without extension.
- `label`: Human-readable display label, usually the glossary page H1.
- `node_type`: Controlled glossary type, such as Character, Artifact, Faction, Concept, Event, Pathway, Location, Deity, Uniqueness, Family, Epoch, Mystery, or Timeline. Provisional graph-local node types such as Tarot may also appear when relationship seeds intentionally target lightweight nodes before a dedicated glossary page exists.
- `source_file`: Glossary file where the node is defined, if it exists.
- `source_layer`: Whether the node is repository-canonical, source-supported graph-local, or external/unsupported.
- `canonicalization_status`: Whether the node is already represented in project records, graph-local only, or a candidate project-data update.
- `subject_visible_from`: Page-level reader-safe visibility gate from glossary metadata. Use this to decide whether the node itself can appear in reader-facing navigation, search, or filtered graph views.
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
claim_id:
medium:
novel_chapter:
donghua_episode:
in_world_chronology:
related_investigation:
source_layer:
canonicalization_status:
projection_owner:
projection_scope:
projection_source:
state_history_source:
availability:
graph_visibility:
display_source_label:
display_target_label:
display_relationship_type:
default_hidden_source_behavior:
default_hidden_target_behavior:
```

Field notes:

- `relationship_id`: Stable generated identifier, likely derived from source, target, relationship type, and start position.
- `source_node`: Source node id.
- `target_node`: Target node id.
- `relationship_type`: Controlled relationship type from `PROJECT_RULES.md`.
- `confidence_level`: Controlled qualitative confidence where applicable.
- `truth_status`: Claim status where applicable, especially when relationships are generated from knowledge units.
- `claim_id`: Optional Reader Knowledge Ledger knowledge-unit id that explains the relationship's claim timing, confidence evolution, supersedence history, or evidence provenance.
- `medium`: Source medium for the relationship disclosure, such as novel, Donghua, or both.
- `novel_chapter`: Novel chapter where the relationship becomes reader-safe or is first verified.
- `donghua_episode`: Donghua episode or release-order position where the relationship becomes viewer-safe or is first verified.
- `in_world_chronology`: Optional story-chronology position when it differs from reader disclosure order.
- `related_investigation`: Supporting investigation record, if the relationship depends on source verification.
- `source_layer`: Whether the relationship is repository-canonical, source-supported graph-local, or external/unsupported.
- `canonicalization_status`: Whether the relationship is already represented in project records, graph-local only, or a candidate project-data update.
- `projection_owner`: The file or ownership role that is expected to provide the canonical Relationship Seed for this edge.
- `projection_scope`: Whether the seed is canonical, provisional, or intentionally local-context.
- `projection_source`: Optional pointer to the type-specific data-block row projected by the Relationship Seed, such as `character_profile.pathway_state[pathway-sleepless]`.
- `state_history_source`: Whether state history should be read from a type-specific data block, the seed itself, a linked knowledge unit, or a future normalized graph table.
- `availability`: Optional normalized list of per-medium reader positions, confidence, status, and adaptation relationship values generated from the projected data-block row.
- `graph_visibility`: Current relationship display state for the selected reader boundary. Allowed values are `hidden`, `anonymized`, `partial`, and `full`.
- `display_source_label`: Reader-safe source label to use when the true source is hidden or partially known.
- `display_target_label`: Reader-safe target label to use when the true target is hidden or partially known.
- `display_relationship_type`: Reader-safe relationship label to use when the true relationship type is hidden or partially known.
- `default_hidden_source_behavior`: Seed-level default for hidden source pages, usually `hide`.
- `default_hidden_target_behavior`: Seed-level default for hidden target pages, usually `hide`.

Relationship records should distinguish the graph edge from the reader-state history of the claim. For example, `novel_chapter` can represent the earliest graph-worthy visibility of an edge, while a linked `projection_source` can preserve that the same edge moved from strong inference to confirmed fact later. A linked `claim_id` may add evidence or interpretive context, but should not be required for ordinary page-local state that is already represented in the type-specific data block.

Graph generators should apply page visibility, row availability, and relationship display state in that order. Hidden source or target pages should suppress the edge unless the current availability entry explicitly provides an anonymized or partial display label. Anonymized nodes are presentation artifacts, not canonical glossary nodes.

## Presentation Nodes

Rendered Mermaid graphs may introduce generated presentation nodes such as `rel_001`.

These nodes are not canonical graph entities. They represent relationship records visually so dense graphs can place relationship meaning inside layout-aware boxes instead of fragile edge labels.

Presentation relationship nodes may display:

- `relationship_type`
- timing, such as novel chapter or Donghua episode
- relationship status
- confidence level

Timing-spoiler-free views should omit chapter and episode text from presentation nodes while preserving the underlying relationship type, status, and confidence.

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
