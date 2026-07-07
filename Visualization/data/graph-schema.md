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
- `node_type`: Controlled glossary type, such as Character, Artifact, Item, Knowledge Source, Faction, Concept, Event, Pathway, Location, Deity, Uniqueness, Family, Epoch, Mystery, or Timeline. Provisional graph-local node types such as Tarot may also appear when relationship seeds intentionally target lightweight nodes before a dedicated glossary page exists.
- `source_file`: Glossary file where the node is defined, if it exists.
- `source_layer`: Whether the node is repository-canonical, source-supported graph-local, or external/unsupported.
- `canonicalization_status`: Whether the node is already represented in project records, graph-local only, or a candidate project-data update.
- `subject_visible_from`: Page-level reader-safe visibility gate from glossary metadata. Use this to decide whether the node itself can appear in reader-facing navigation, search, or filtered graph views.
- `status`: Page completion state from glossary metadata. Reader-visible pending pages may render with a dashed pending-node outline, while pending pages outside the selected reader boundary should remain hidden. Missing glossary pages may render as graph-local pending endpoints only when relationship or projected data timing proves they are visible inside the selected reader boundary.
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

Relationship Seeds that project type-specific data rows should resolve `projection_source` relative to the seed source page before falling back to any global key. This avoids collisions between repeated local row keys such as `character_profile.affiliations[faction-nighthawks]` across multiple character pages. `projection_source` points to structured data-block rows, not human-facing Markdown tables; generated graphs should read row-level `availability` from the data block and treat prose tables as display surfaces that may later be generated.

Named non-artifact objects should use canonical Item nodes only when they are recurring, graph-worthy, or page-worthy. Minor possessions, disposable equipment, and ordinary access items can remain data-block rows with `graph_relevance: none` and no Relationship Seed. Item and equipment rows should use `item_significance`, `graph_relevance`, and `page_worthiness` to decide whether they stay data-only, appear only in local maintainer graphs, or become full graph nodes with `possesses-item` / `uses-item` seeds.

Potion, formula, and ritual modeling should distinguish inputs from outputs and object identity. Materials are raw inputs/components and may remain inline in pathway, ritual, item, artifact, or event data until a recurring material becomes page-worthy. Preparations are outputs made, charged, consecrated, assembled, or activated by a formula, ritual, prayer, or craft process; this future node family can cover charms, ritual bullets, blessed powders, talismans, prepared tools, and durable or repeatable ritual effects. A preparation may also become possession-trackable when it has `physical_form: item` or `physical_form: consumable-item`, but that does not make every preparation an Item node. Pure ritual effects should not be projected as possession nodes unless the current graph view explicitly models effects.

Recurring knowledge carriers should use canonical Knowledge Source nodes when their source identity, access chain, quotes, interpretation changes, or claim chronology matter independently. Use `source-*` nodes for diary-page corpora, spellbooks, grimoires, notebooks, scriptures, case files, letters, inscriptions, formula records, murals, or similar reveal carriers. Do not model these as Item nodes merely because they are physical objects.

Knowledge Source `knowledge_entries` should expose stable source-unit fields when the source is encountered in pages, batches, fragments, inscriptions, chapters, files, or excerpts. `source_unit_id` is the preferred row key for graph projection; `source_unit_type`, `batch_id`, `fragment_id`, `sequence_index`, and `source_position` preserve local ordering and citation context without creating separate glossary nodes for every fragment.

Knowledge Source entries may also expose unit-level provenance fields such as `provider`, `provider_role`, `transfer_mode`, `reader`, `reader_access_type`, `holder_understanding`, `intentionality`, and `mediation`. These distinguish incidental access from deliberate submission, direct reading from translation or mediation, and reader-safe understanding from later reinterpretation.

Type-specific data blocks may expose `timeline_entries` as the structured companion to visible Chronological Development prose. These entries are not relationship records by default. They support future website rendering, reader-position filtering, dashboard timelines, and QA checks that compare visible Markdown chronology with structured chronology. Every real visible chronology subsection should have a stable semantic `timeline_id` matched to one `timeline_entries.id`, and both layers should stay in the same reader/viewer order within each medium. A timeline entry can reference graph entities, claims, relationships, or events through related fields, but graph projection should still come from Relationship Seeds or explicit graph-local modeling.

Relationship Seed `status` values describe the seed edge, not the full item, artifact, or character state. Use `historical` for relationships that were true earlier but are no longer current without implying rupture. Reserve `broken` for a relationship that is explicitly breached, severed, failed, destroyed, or narratively broken. For custody or possession loss, prefer row-level state such as `possession_status: lost-custody` or `custody_status: lost-custody` plus a current/historical availability ladder rather than labeling the edge `broken`.

Graph generators should apply page visibility, row availability, and relationship display state in that order. Hidden source or target pages should suppress the edge unless the current availability entry explicitly provides an anonymized or partial display label. Anonymized nodes are presentation artifacts, not canonical glossary nodes.

QA relationship-node graph labels should summarize provenance by source layer. A seed with `projection_source` should render the projected data row's meaningful availability history, such as `character data novel ch22 strong-evidence -> ch45 confirmed`; a seed without a usable projection should render seed provenance, such as `faction seed novel ch22 confirmed`. Pending adaptation rows with only TBD timing should be retained in graph data but omitted from compact graph labels until a real viewer position is verified.

## Presentation Nodes

Rendered Mermaid graphs may introduce generated presentation nodes such as `rel_001`.

These nodes are not canonical graph entities. They represent relationship records visually so dense graphs can place relationship meaning inside layout-aware boxes instead of fragile edge labels.

Rendered Mermaid graphs may also introduce graph-local pending endpoint nodes when a source or target has no glossary page yet but a boundary-visible relationship proves that the endpoint can safely appear. These nodes are not canonical glossary pages and should disappear, change to pending-page nodes, or become solid canonical nodes as page metadata is added.

Presentation relationship nodes may display:

- `relationship_type`
- timing, such as novel chapter or Donghua episode
- relationship status
- confidence level
- projected availability history when a Relationship Seed points at a type-specific data-block row

Timing-spoiler-free views should omit chapter and episode text from presentation nodes while preserving the underlying relationship type, status, and confidence.

## Future Filters

Future graph generation may support filtering by:

- Node type
- Relationship type
- Event type
- Event part
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
- Obsidian QA dry-run graph artifacts under `Obsidian_Export/_Generated/repo-refresh-check/`

Generated outputs should be reproducible from canonical project data.

The Obsidian QA dry-run artifacts are generated from the same configured visualization views with rendering disabled. They are local inspection output and should not be treated as canonical replacements for `Visualization/graphs/`, rendered outputs, the real refresh snapshot, or visualization refresh tracker updates.
