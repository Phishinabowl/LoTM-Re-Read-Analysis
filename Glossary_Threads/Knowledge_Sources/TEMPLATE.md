# Knowledge Source Name

## Metadata

Type: Knowledge Source
Status: Stub
First Mention Volume:
Subject Visible From:
Current Analysis Status: Not Started
Confidence Level: Unknown
Spoiler Boundary:
Reader Knowledge Boundary:
Tags: knowledge-source
Last Updated:

Related Threads:
-

Related Investigations:
-

Use Knowledge Source pages for recurring reveal carriers: diary-page corpora, spellbooks, grimoires, notebooks, scriptures, case files, letters, inscriptions, formula records, murals, records, or similar sources whose claims, quotes, access history, interpretation, or reader-safe chronology need independent tracking. Use Item pages when the object is mainly a possession/tool/access object. Use Artifact pages when the source is primarily a formal mystical artifact or Sealed Artifact.

## Purpose

What source does this page track, what kind of knowledge does it carry, and why does it need its own chronology rather than remaining a local equipment/document row?

## Spoiler Boundary

Record only reader-safe source identity, access, quotes, and claims. Do not import later translated meanings, authorship, manipulation, forgery, or downstream revelations before this page boundary advances.

## Reader Knowledge Boundary

- Novel Volume:
- Novel Chapter:
- Reader knowledge state:
- Donghua:
- Donghua viewer knowledge state:

## Source Snapshot

- Current reader-safe identity:
- Current source type:
- Current format / medium:
- Current known author / origin:
- Current reader / interpreter:
- Current holder / access route:
- Current reliability:
- First appearance:
- Main reader-safe uncertainty:

## Names & Labels

| Field | Value | First reveal / change point | Status | Confidence | Notes |
|---|---|---|---|---|---|
| Primary label |  |  |  |  |  |
| Alternate label |  |  |  |  |  |

## Format / Medium

| Format element | Value | First reveal / change point | Status | Confidence | Notes |
|---|---|---|---|---|---|
| Source type |  |  |  |  |  |
| Physical / sensory form |  |  |  |  |  |
| Language / encoding |  |  |  |  |  |
| Completeness |  |  |  |  |  |
| Reliability |  |  |  |  |  |

## Authorship / Origin

| Author / origin | Relationship | First reveal / change point | Status | Confidence | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Access / Custody / Readers

| Entity | Relationship | First reveal / change point | Status | Confidence | Notes |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## Knowledge Entries

Track each durable claim, quoted passage, formula, event record, concept explanation, or interpretive change that comes from this source. Keep entries in reader-disclosure order for the active boundary.

| Entry / claim | Source unit / position | First reader-safe reveal | Interpretation status | Confidence | Downstream threads | Notes |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Quote / Evidence Index

Use short quote references only. Keep full quote handling compliant with project/source policies.

| Chapter / episode | Source position | Short excerpt / paraphrase | Claim supported | Notes |
|---|---|---|---|---|
|  |  |  |  |  |

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

### Authors / Origins

-

### Readers / Interpreters

-

### Holders / Access Routes

-

### Associated Artifacts

-

### Associated Items

-

### Revealed Concepts / Claims

-

### Associated Events

-

## Knowledge Source Data Block

This block is the structured page-local state model for recurring knowledge carriers. Use metadata, not this data block, for page-level `Subject Visible From`. Use row-level `availability` for source identity, access, interpretation, and claim entries that change by medium or reader position.

```yaml
knowledge_source_profile:
  reader_boundary:
    medium: novel
    book: lotm-1
    volume:
    chapter:
  data_model_version: page-local-state-v1
  state_sort_order: newest-to-oldest
  source_identity:
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
  format_medium:
    - source_type:
      format:
      language_or_encoding:
      completeness:
      reliability:
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
  authorship_origin:
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
  access_custody_readers:
    - target:
      relationship:
      access_status:
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
          access_status:
          status:
          confidence:
          graph_visibility:
          display_source_label:
          display_target_label:
          display_relationship_type:
      notes:
  knowledge_entries:
    - claim_id:
      source_unit_id:
      source_unit_type:
      batch_id:
      fragment_id:
      sequence_index:
      source_position:
      provider:
      provider_role:
      transfer_mode:
      reader:
      reader_access_type:
      holder_understanding:
      intentionality:
      mediation:
      target:
      relationship:
      quote_ref:
        medium:
        book:
        volume:
        chapter:
        season:
        episode:
        release_order:
        source_unit_id:
        source_position:
        quote_policy: short-quote-only
      interpretation_status:
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
          source_unit_id:
          batch_id:
          fragment_id:
          sequence_index:
          provider:
          transfer_mode:
          reader:
          reader_access_type:
          holder_understanding:
          intentionality:
          mediation:
          interpretation_status:
          status:
          confidence:
          graph_visibility:
          display_source_label:
          display_target_label:
          display_relationship_type:
      notes:
```

## Relationship Seeds

Use this section only for graph-worthy Knowledge Source edges. Knowledge Source pages usually own source-as-source edges such as `authored-by`, `records-event`, `contains-formula`, `describes-concept`, `reveals-claim`, or `source-of-information`. Character, faction, location, or event pages may own access/handler/reader edges when those pages are the natural source of the relationship.

Do not add Relationship Seeds for every claim row. Seed only edges that should appear in generated relationship graphs; preserve detailed claim chronology in `knowledge_entries` and Reader Knowledge Ledger units.

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

Add one block for each durable spoiler-timed claim that needs audit history beyond the structured source entry. Keep novel and Donghua disclosure timelines independent.

### Knowledge Unit: Claim Title

```yaml
id: source-claim-id
claim:
truth_status: unresolved
confidence_level: unknown
canon_scope:
occurs_at:
  medium:
  book:
  volume:
  chapter:
  season:
  episode:
  release_order:
tags:
  - volume-
  - reader-knowledge
  - source
disclosures:
  - medium:
    knowledge_state:
    disclosure_type:
    available_from:
      book:
      volume:
      chapter:
      season:
      episode:
      release_order:
    superseded_at:
    superseded_by:
adaptation_relationships:
  - type: pending
    novel_claim_changed:
    notes:
subject_attribution_from:
  - medium:
    position:
      book:
      volume:
      chapter:
      season:
      episode:
      release_order:
    notes:
evidence_basis:
  - source:
    location:
    summary:
    effect_on_confidence:
confidence_history:
  - position:
      medium:
      volume:
      chapter:
      season:
      episode:
    confidence_before:
    confidence_after:
    reason:
    evidence:
related_investigations:
related_boards:
last_updated:
```

#### Reader-State History

-

#### Adaptation Analysis

-

<details>
<summary>Maintainer Notes</summary>

- Page-specific modeling note:

</details>
