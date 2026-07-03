# Pathway Name

## Metadata

Type: Pathway
Status: Stub
First Mention Volume:
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

## Pathway Snapshot

- Current reader-safe status:
- Institutional access status:
- Known continuation status:
- Primary reader-facing function:
- Main uncertainty:

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

## Pathway Data Block

This block is a structured extraction aid for future graphs and dashboards. It duplicates the high-value pathway facts above in a predictable shape; the prose, relationship seeds, and reader knowledge ledger remain authoritative.

```yaml
pathway_profile:
  reader_boundary:
    medium: novel
    book: lotm-1
    volume:
    chapter:
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
```

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

## Relationship Seeds

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

## Notes

-
