# Item Name

## Metadata

Type: Item
Status: Stub
First Mention Volume:
Subject Visible From:
Current Analysis Status: Not Started
Confidence Level: Unknown
Spoiler Boundary:
Reader Knowledge Boundary:
Tags: item
Last Updated:

Related Threads:
-

Related Investigations:
-

Use Item pages for named, recurring, graph-worthy non-artifact objects. Use Knowledge Source pages for recurring information carriers whose claims, quotes, access history, or interpretation chronology are the analytical center. Use Artifact pages for formal mystical artifacts, Sealed Artifacts, or supernatural objects whose artifact identity is the analytical center. Keep minor equipment, disposable possessions, and ordinary one-scene props inside local data blocks instead of creating Item pages.

## Purpose

What named object does this page track, and why is it important enough to become an independent page rather than a local equipment row?

## Spoiler Boundary

Record only reader-safe item state. Do not import later ownership, function, messenger-system, ritual-system, or artifact-context reveals before this page boundary advances.

## Reader Knowledge Boundary

- Novel Volume:
- Novel Chapter:
- Reader knowledge state:
- Donghua:
- Donghua viewer knowledge state:

## Item Snapshot

- Current reader-safe identity:
- Current object type:
- Current owner / holder / custodian:
- Current function:
- Current graph relevance:
- Current page-worthiness:
- First appearance:
- Main reader-safe uncertainty:

## Names & Labels

| Field | Value | First reveal / change point | Status | Confidence | Notes |
|---|---|---|---|---|---|
| Primary label |  |  |  |  |  |
| Alternate label |  |  |  |  |  |

## Ownership / Custody / Access

| Holder / owner / custodian | Relationship | First reveal / change point | Status | Confidence | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Functions & Uses

| Function / use | User / system | First reveal / change point | Status | Confidence | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Related Concepts / Systems

| Concept / system | Relationship | First reveal / change point | Status | Confidence | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Appearance / Physical Description

| Field | Value | First reveal / change point | Status | Confidence | Notes |
|---|---|---|---|---|---|
| Physical description |  |  |  |  |  |

## Chronological Development

### Novel

#### Volume X

- What the reader learns:
- What changes:
- What remains unknown:
- Why it matters:

### Donghua

#### Season X, Episode Y

- Timestamp:
- What the viewer learns:
- What changes:
- What remains unknown:
- Why it matters:

## Open Questions

- Question:
- Current confidence:
- Needs EPUB verification:
- Related investigation:

## Related Threads

Use Markdown links when the target file exists, with the target document's human-readable H1 title as the link label. Mention a nonexistent thread as a plain filename only when its creation is already planned or the relationship is essential.

### Directly Related

-

### Owners / Holders / Users

-

### Associated Artifacts

-

### Associated Concepts / Systems

-

### Associated Knowledge Sources

-

### Associated Events

-

## Item Data Block

This block is the structured page-local state model for named, recurring, graph-worthy non-artifact items. Use metadata, not this data block, for page-level `Subject Visible From`. Use row-level `availability` for item state that changes by medium or reader position.

Structured taxonomy values are not final website prose. Use kebab-case values for filtering, grouping, graphing, and custody/state logic; use human-written fields such as `summary`, `notes`, `evidence`, or future `site_summary` / `display_text` fields for sentences that may be shown directly to readers. Future renderers should map reusable values through display labels and use prose fields for article voice.

Use `item_significance`, `graph_relevance`, and `page_worthiness` to keep ordinary equipment from becoming graph noise:

- `item_significance`: `minor`, `recurring`, or `major`
- `graph_relevance`: `none`, `local`, or `full`
- `page_worthiness`: `none`, `candidate`, or `dedicated-page`

```yaml
item_profile:
  reader_boundary:
    medium: novel
    book: lotm-1
    volume:
    chapter:
  data_model_version: page-local-state-v1
  state_sort_order: newest-to-oldest
  item_identity:
    - field: primary-label
      value:
      status:
      confidence:
      availability:
        - medium:
          from:
            book:
            volume:
            chapter:
            season:
            episode:
            release_order:
          status:
          confidence:
      notes:
  item_classification:
    - item_type:
      item_significance:
      graph_relevance:
      page_worthiness:
      artifact_boundary:
      status:
      confidence:
      availability:
        - medium:
          from:
            book:
            volume:
            chapter:
            season:
            episode:
            release_order:
          status:
          confidence:
      notes:
  ownership_access:
    - target:
      relationship:
      possession_status:
      status:
      confidence:
      availability:
        - medium:
          from:
            book:
            volume:
            chapter:
            season:
            episode:
            release_order:
          possession_status:
          status:
          confidence:
          graph_visibility:
          display_source_label:
          display_target_label:
          display_relationship_type:
      notes:
  functions_uses:
    - function:
      target:
      relationship:
      status:
      confidence:
      availability:
        - medium:
          from:
            book:
            volume:
            chapter:
            season:
            episode:
            release_order:
          status:
          confidence:
          graph_visibility:
          display_source_label:
          display_target_label:
          display_relationship_type:
      notes:
  related_concepts_systems:
    - target:
      relationship:
      status:
      confidence:
      availability:
        - medium:
          from:
            book:
            volume:
            chapter:
            season:
            episode:
            release_order:
          status:
          confidence:
          graph_visibility:
          display_source_label:
          display_target_label:
          display_relationship_type:
      notes:
```

## Relationship Seeds

Use this section only for graph-worthy Item edges. Item pages often own seeds where the item is the source, such as `uses-item`, `access-route-to`, or concept/system links. Character, faction, or location pages normally own `possesses-item` seeds where that entity is the source and the item is the target.

Do not add Relationship Seeds for minor equipment or disposable possessions. Keep those in local data blocks with `graph_relevance: none`.

When an Item seed projects an `item_profile` row, set `projection_source` to that structured row. Do not point seeds at visible Markdown tables; those tables are a human-facing display layer and may later be generated from the data block.

Use `status: broken` only if the item relationship itself is explicitly ruptured, failed, destroyed, or narratively broken. For normal custody changes, loss, transfer, or no-longer-held state, prefer row-level `possession_status` / `custody_status` changes with `status: historical` where needed.

```yaml
relationships:
  - source:
    target:
    relationship_type:
    start:
      medium:
      volume:
      chapter:
      season:
      episode:
      release_order:
    status:
    confidence:
    projection_owner:
    projection_scope: canonical
    projection_source:
    claim_id:
    default_hidden_source_behavior: hide
    default_hidden_target_behavior: hide
    notes:
```

## Evidence Index

- Chapter:

## Reader Knowledge Ledger

Add one block for each durable spoiler-timed claim. Keep novel and Donghua disclosure timelines independent.

### Knowledge Unit: Claim Title

```yaml
id: item-claim-id
claim:
truth_status: unresolved
confidence_level: unknown
canon_scope:
occurs_at:
  medium:
  book:
  volume:
  chapter:
  notes:
tags:
  - item
disclosures:
  - medium:
    knowledge_state:
    disclosure_type:
    available_from:
      book:
      volume:
      chapter:
    superseded_at:
    superseded_by:
adaptation_relationships:
  - type: pending
    novel_claim_changed: false
    notes:
subject_attribution_from:
evidence_basis:
confidence_history:
related_investigations:
related_boards:
last_updated:
```

#### Reader-State History

-

#### Adaptation Analysis

-
