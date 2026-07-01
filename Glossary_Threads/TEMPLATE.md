# Thread Name

## Metadata

Type:
Status: Stub
First Mention Volume:
Current Analysis Status: Not Started
Confidence Level: Unknown
Spoiler Boundary:
Reader Knowledge Boundary:
Tags:
Last Updated:

Related Threads:
-

Related Investigations:
-

Use only controlled tags from `PROJECT_RULES.md`.

Filename format:

```text
[entity-type]-[kebab-case-name].md
```

Store the file in its matching plural category folder, such as `Characters/`, `Artifacts/`, or `Mysteries/`, while retaining the filename prefix.

Examples:

```text
artifact-0-08.md
character-azik-eggers.md
family-medici.md
faction-rose-school-of-thought.md
concept-gray-fog.md
event-great-smog.md
timeline-ian-zreal-chain.md
```

## Purpose

What recurring thread, symbol, faction, person, family, concept, or mystery does this file track?

## Spoiler Boundary

Record only what is allowed by the broader spoiler boundary and exact reader knowledge boundary. Avoid contaminating early entries with later reveals.

## Reader Knowledge Boundary

Define the exact reread point this thread entry is limited to.

- Volume:
- Chapter:
- Reader knowledge state:

## First Appearance / First Meaningful Mention

Use separate medium subsections when the thread tracks more than one format.

### Novel

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

## Chronological Development

### Novel

#### Volume X

- Chapter:
- What the reader learns:
- What remains unknown:
- Why it matters:

### Donghua

#### Season X, Episode Y

- Release order:
- Timestamp:
- What the viewer learns:
- What remains unknown:
- Why it matters:

## Open Questions

- Question:
- Current confidence:
- Needs EPUB verification:
- Related investigation:

## Related Threads

Use Markdown links when the target file exists, with the target document's human-readable H1 title as the link label. Mention a nonexistent thread as a plain filename only when its creation is already planned or the relationship is essential. Do not seed speculative future references.

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

Use this section only for relationships important enough to support future relationship graphs. Keep entries reader-boundary aware and mark unverified start points as `TBD`.

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

Add one block for each durable spoiler-timed claim. Duplicate the block as needed. Keep novel and Donghua disclosure timelines independent.

Together, these units should form the subject's complete reveal timeline. Add a separate disclosure entry for every meaningful reveal point, including multiple entries from the same medium for first mentions, clues, inferences, explicit reveals, and confirmations.

Future reader-facing pages will filter these entries against the user's selected position. Do not treat unrestricted analysis elsewhere in this file as automatically spoiler-safe.

### Knowledge Unit: Claim Title

```yaml
id: subject-claim-id
claim: Exact fact, inference, theory, misconception, or question
truth_status: unresolved
confidence_level: unknown
canon_scope: shared
occurs_at:
  medium: novel
  book: lotm-1
  volume:
  chapter:
  notes:
tags:
  - reader-knowledge
disclosures:
  - medium: novel
    knowledge_state: open-question
    disclosure_type: first-mention
    available_from:
      book: lotm-1
      volume:
      chapter:
    superseded_at:
    superseded_by:
  - medium: donghua
    knowledge_state: open-question
    disclosure_type: first-mention
    available_from:
      season:
      installment_type: episode
      episode:
      release_order:
    superseded_at:
    superseded_by:
adaptation_relationships:
  - type: uncertain
    novel_claim_changed: false
    notes:
subject_attribution_from:
  - medium: novel
    position:
      book: lotm-1
      volume:
      chapter:
  - medium: donghua
    position:
      season:
      installment_type: episode
      episode:
      release_order:
related_investigations:
related_boards:
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
      release_order:
    confidence_before:
    confidence_after:
    reason:
    evidence:
last_updated:
```

#### Reader-State History

- What each audience could reasonably know:
- How the knowledge state changed:
- How confidence changed as evidence accumulated:

#### Adaptation Analysis

- Differences in timing, presentation, context, omission, condensation, expansion, or meaning:

## Future Automation Notes

Do not manually maintain backlinks, incoming references, generated indexes, relationship graphs, or visual maps yet.

## Notes

-
