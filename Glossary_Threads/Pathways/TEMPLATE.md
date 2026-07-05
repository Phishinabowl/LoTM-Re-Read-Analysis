# Pathway Name

<!-- Optional: omit this block until a page-ready official pathway asset is promoted. -->
<a href="../../Artwork/page-assets/pathways/pathway-slug/page-ready-pathway-image.ext"><img src="../../Artwork/page-assets/pathways/pathway-slug/page-ready-pathway-image.ext" alt="Official pathway artwork label" width="360"></a>

## Metadata

Type: Pathway
Status: Stub
First Mention Volume:
Subject Visible From:
Current Analysis Status: Not Started
Confidence Level: Unknown
Spoiler Boundary:
Reader Knowledge Boundary:
Tags: pathway
Last Updated:

Related Threads:
-

Related Investigations:
-

Use only controlled tags from `../../PROJECT_RULES.md`.

Filename format:

```text
pathway-[kebab-case-name].md
```

Store the file in:

```text
Glossary_Threads/Pathways/
```

## Purpose

Track the pathway as it is revealed to the reader, including first mentions, known Sequence ladder, potion or formula details, ability profile, access routes, affiliated factions, known holders, and reader-safe unknowns.

This page should preserve the pathway's reveal order without importing later pathway names, higher Sequences, future organizations, or retrospective reinterpretations before the reader boundary reaches them.

## Spoiler Boundary

Record only what is allowed by the broader spoiler boundary and exact reader knowledge boundary. Avoid contaminating early entries with later pathway structure.

## Reader Knowledge Boundary

- Novel Volume:
- Novel Chapter:
- Reader knowledge state:
- Donghua:
- Donghua viewer knowledge state:

## First Appearance / First Meaningful Mention

Use separate medium subsections when the thread tracks more than one format.

### Novel

#### First Word-Level Mention

- Volume:
- Chapter:
- Context:
- Reader knowledge state:

#### First Meaningful Pathway Explanation

- Volume:
- Chapter:
- Context:
- Reader knowledge state:

### Donghua

- Season:
- Episode:
- Release order:
- Timestamp:
- Context:
- Viewer knowledge state:

## Known Sequences

Record only Sequences that are reader-safe at this article boundary. Unknown higher Sequences should be marked as unknown in `Pathway Snapshot` or `Reader-safe unknowns` rather than filled from later knowledge.

### Sequence 9: Reader-Safe Name

- First reader-safe reveal:
- Confidence:
- Formula / potion details:
- Confirmed abilities or traits:
- Practical demonstrations:
- Training or practice requirements:
- Limitations:
- Reader-safe unknowns:
- Notes:

## Institutional Access

Track pathway-wide institutional access, especially when the same institution controls multiple known Sequences or when access details are not specific to a single Sequence.

| Institution / faction | Access type | First reader-safe reveal | Confidence | Notes |
| --- | --- | --- | --- | --- |

## Affiliated Factions

Track faction associations that matter to the pathway but are broader than one access-control event.

| Faction / organization | Affiliation type | First reader-safe reveal | Confidence | Notes |
| --- | --- | --- | --- | --- |

## Known Holders

Record only character-pathway statuses that are reader-safe at this article boundary. Use confidence carefully when the pathway is confirmed but the exact Sequence is only inferred.

| Character | Status / Sequence | First reader-safe reveal | Confidence | Notes |
| --- | --- | --- | --- | --- |

## Associated Uniqueness

Track the pathway's Uniqueness here even when it does not have a dedicated page. Only link to `Glossary_Threads/Uniquenesses/` when the Uniqueness is named, embodied, or tracked as a distinct item/entity, rather than only appearing as a pathway formula component.

- Reader-safe name:
- First reader-safe reveal:
- Status: known / implied / formula-component / embodied / unknown
- Dedicated article:
- Known holder or accommodation state:
- Related deity / Sequence 0 page:
- Related ATS / Great Old One formula:
- Notes:

## Associated Mythical Creature

Track the pathway's associated mythical creature form here when it becomes reader-safe. Do not create a dedicated mythical-creature page by default; the shared index belongs on `Glossary_Threads/Concepts/concept-mythical-creature-forms.md`.

| Form name | Version / stage | Sequence / threshold | First reader-safe reveal | Status | Confidence | Notes |
|---|---|---|---|---|---|---|

## Chronological Development

### Novel

#### Chapter X: Event Name

- What the reader learns:
- What changes:
- What remains unknown:
- Why it matters:

### Donghua

#### Season X, Episode Y: Event Name

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

### Directly Related

-

### Historical Connections

-

### Associated Mysteries

-

### Associated Artifacts

-

### Associated Factions

-

### Associated Characters

-

### Associated Pathways

-

## Pathway Data Block

This block is a structured extraction aid for future graphs and dashboards. It duplicates the high-value pathway facts above in a predictable shape; the prose, relationship seeds, reader knowledge ledger, and metadata remain authoritative. Use metadata, not this data block, for page-level `Subject Visible From`. If `associated_tarot_card`, `associated_higher_order_entities`, `associated_uniqueness`, or `associated_mythical_creature` names a positive reader-safe target, add the corresponding graph edge in `Relationship Seeds`. Do not add relationship seeds for unknown/null placeholder state.

Use kebab-case values for local Pathway Data Block taxonomy fields such as `status`, `usage_type`, `display_behavior`, `relationship_layer`, `type`, `usage`, and `confidence`. Keep YAML field names such as `reader_boundary`, `stable_slug`, `usage_type`, `display_behavior`, and `relationship_layer` in snake_case.

```yaml
pathway_profile:
  reader_boundary:
    medium: novel
    book: lotm-1
    volume:
    chapter:
  stable_slug: pathway-[name]
  official_artwork:
    - image_number:
      label:
      type:
      file:
      usage:
  associated_tarot_card:
    card_name:
    card_number:
    source_image_number:
    crop_number:
    crop_file:
    confidence:
    notes:
  associated_higher_order_entities:
    - display_name:
      entity:
      relationship_layer: sequence-0 | ats | outer-deity | sefirot | other
      reveal:
        medium:
        volume:
        chapter:
      status:
      confidence:
      notes:
  name_timeline:
    - name:
      usage_type:
      reveal:
        medium:
        volume:
        chapter:
      display_active:
        from:
        until:
      confidence:
      display_behavior:
        primary_title: true/false
        hint_label:
      notes:
  sequences:
    - sequence:
      name:
      reveal:
        medium:
        volume:
        chapter:
      confidence:
      formula_details:
        -
      ability_profile:
        confirmed_traits:
          -
        practical_demonstrations:
          -
        training_or_practice:
          -
        limitations:
          -
        unknowns:
          -
      notes:
  institutional_access:
    - faction:
      access_type:
      reveal:
        medium:
        volume:
      chapter:
      confidence:
      notes:
  affiliated_factions:
    - faction:
      affiliation_type:
      reveal:
        medium:
        volume:
        chapter:
      confidence:
      notes:
  known_holders:
    - character:
      status:
      sequence:
      sequence_name:
      reveal:
        medium:
        volume:
        chapter:
      confidence:
      notes:
  associated_uniqueness:
    reader_safe_name:
    reveal:
      medium:
      volume:
      chapter:
    status:
    dedicated_article:
    holder_or_accommodation_state:
    related_deity:
    related_ats_formula:
    notes:
  associated_mythical_creature:
    concept_index: concept-mythical-creature-forms
    forms:
      - reader_safe_name:
        version_stage:
        sequence_threshold:
        reveal:
          medium:
          volume:
          chapter:
        status:
        notes:
```

## Relationship Seeds

Use relationship seeds for graph-visible pathway edges, including `associated-tarot-card`, `associated-sequence-0`, `associated-ats`, `associated-outer-deity`, `associated-sefirot`, `associated-uniqueness`, and `associated-mythical-creature-form` when those targets are reader-safe. For mythical creature forms, target the shared `concept-mythical-creature-forms` concept page and preserve the specific form name in notes/local data. Keep detailed state, holders, notes, title variants, display timing, and uncertainty in the visible sections and `Pathway Data Block`.

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
    notes:
```

## Evidence Index

- Chapter:

## Reader Knowledge Ledger

Add one block for each durable spoiler-timed pathway claim. Keep novel and Donghua disclosure timelines independent.

### Knowledge Unit: Claim Title

```yaml
id:
claim:
truth_status:
confidence_level:
canon_scope:
occurs_at:
  medium:
  book:
  volume:
  chapter:
  notes:
tags:
  - pathway
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
    notes: Adaptation comparison not yet verified.
related_investigations:
related_boards:
last_updated:
```

#### Reader-State History

- What each audience could reasonably know:
- How the knowledge state changed:
- How confidence changed as evidence accumulated:

#### Adaptation Analysis

- Differences in timing, presentation, context, omission, condensation, expansion, or meaning:

## Future Automation Notes

- The `Pathway Data Block` should remain aligned with the pathway snapshot sections, relationship seeds, and reader knowledge ledger.
- Future spoiler-filtered renderers should collapse optional sections when no rows or prose remain eligible at the selected reader position. Embedded page header images may remain visible at any reader position.
- If this pathway is not reader-safe for a selected position, future renderers should hide the entire page from reader-facing navigation, search, related-thread lists, graph views, and generated output.
- If `Subject Visible From` is not obvious from the first appearance section, add a short note here explaining the page-level gate.

## Notes

-
