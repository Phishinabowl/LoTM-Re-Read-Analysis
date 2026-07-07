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

For formula and potion details, preserve material inputs, quantities, preparation instructions, formula source, and reader-safe uncertainty separately. Materials can stay inline until a recurring ingredient becomes page-worthy. If a formula or ritual creates a usable supernatural output, classify that output as a future Preparation rather than defaulting to Item; use Item only for named recurring possessions with custody history, Artifact for formal supernatural artifacts, and Knowledge Source for formula records or texts whose main role is revealing information.

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

Use Markdown links when the target file exists, with the target document's human-readable H1 title as the link label. Mention a nonexistent thread as a plain filename only when its creation is already planned or the relationship is essential. Do not seed speculative future references.

### Directly Related

-

### Historical Connections

-

### Associated Mysteries

-

### Associated Artifacts

-

### Associated Items

-

### Associated Knowledge Sources

-

### Associated Factions

-

### Associated Characters

-

### Associated Pathways

-

## Pathway Data Block

This block is the structured page-local state model for future generated pages, dashboards, reader-position filters, and relationship graphs. It duplicates the high-value pathway facts above in a predictable shape; keep it aligned with the prose and Reader Knowledge Ledger. Use metadata, not this data block, for page-level `Subject Visible From`. If `associated_tarot_card`, `associated_higher_order_entities`, `associated_uniqueness`, or `associated_mythical_creature` names a positive reader-safe target, add the corresponding graph edge in `Relationship Seeds`. Mention related items or knowledge sources in visible sections or related threads when useful, but use dedicated Item or Knowledge Source pages only when the object/source is itself graph-worthy. Do not add relationship seeds for unknown/null placeholder state.

For new or retrofitted rows, prefer `availability` over a single `reveal` field. `availability` preserves novel and Donghua timing independently and can record confidence changes over time. Every row that describes reader-visible state should support availability. Keep legacy `reveal` fields only on unmigrated rows.

Use `graph_visibility` inside an availability entry only when the row can project into relationship graphs. `hidden` means render nothing at that reader point; `anonymized` means use safe generic labels because the reader can see an unknown actor, force, or relationship pattern; `partial` means show some real pieces while withholding others; `full` means show the true eligible source, target, and relationship type.

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
      notes:
  name_timeline:
    - name:
      usage_type:
      display_active:
        from:
        until:
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
      display_behavior:
        primary_title: true/false
        hint_label:
      notes:
  sequences:
    - sequence:
      name:
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
      formula_details:
        - source:
          formula_known_from:
          ingredients:
            - name:
              quantity:
              role:
              material_target:
              confidence:
              notes:
          preparation_steps:
            -
          output:
            output_type: potion | preparation | item | artifact | effect | unknown
            output_target:
            physical_form:
            possession_trackable:
            notes:
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
              notes:
          notes:
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
      notes:
  affiliated_factions:
    - faction:
      affiliation_type:
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
      notes:
  known_holders:
    - character:
      status:
      sequence:
      sequence_name:
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
          adaptation_relationship:
          graph_visibility:
          display_source_label:
          display_target_label:
          display_relationship_type:
          notes:
      notes:
  associated_uniqueness:
    reader_safe_name:
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
        notes:
```

## Relationship Seeds

Use relationship seeds for graph-visible pathway edges, including `associated-tarot-card`, `associated-sequence-0`, `associated-ats`, `associated-outer-deity`, `associated-sefirot`, `associated-uniqueness`, and `associated-mythical-creature-form` when those targets are reader-safe. Relationship Seeds are graph projection hints, not full state histories or replacements for pathway data blocks and knowledge units.

For pathway pages, this page owns pathway-wide metaphysical, institutional, tarot, Sequence 0, ATS, sefirot, Uniqueness, and mythical-creature-form associations. Do not duplicate every known holder as a `pathway-status` seed when the holder/character page exists; keep holder lists and uncertainty in `Known Holders` and `Pathway Data Block`. Use provisional holder seeds only when the holder page does not exist yet and the graph needs the edge.

If confidence or reader-state changes over time, keep one graph edge seed and record the state progression in the data-block row's `availability` list. Use Reader Knowledge Ledger disclosures for audit/explanation. `start` is the earliest reader-safe point where the edge becomes graph-worthy, not necessarily the confirmation point.

For mythical creature forms, target the shared `concept-mythical-creature-forms` concept page and preserve the specific form name in notes/local data. Keep detailed state, holders, notes, title variants, display timing, and uncertainty in the visible sections and `Pathway Data Block`.

Pathway pages should not own ordinary possession/equipment seeds. If a named non-artifact item is important to pathway access, practice, or presentation, track the object on an `item-*` page and let that item page own item-as-source edges such as `access-route-to` or `uses-method` when appropriate.

If a recurring source reveals pathway names, formulas, Sequences, access routes, or pathway history, track it on a `source-*` page and let the Knowledge Source page own source-as-source edges such as `contains-formula`, `describes-concept`, or `reveals-claim` when appropriate.

Use `status: broken` only for pathway relationships that are explicitly ruptured, breached, failed, destroyed, or narratively broken. For ordinary ended access, custody, possession, affiliation, or holder state, prefer projected data-block state plus `status: historical` where needed.

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

Add one block for each durable spoiler-timed pathway claim. Duplicate the block as needed. Keep novel and Donghua disclosure timelines independent.

Together, these units should preserve the pathway's durable disclosure and audit history. Add separate disclosure entries for meaningful reveal points, including multiple entries from the same medium when a claim progresses from first mention, to clue, to inference, to explicit reveal, or to confirmation. Keep ordinary current-state facts in the visible sections and Pathway Data Block.

Future reader-facing pages will filter these entries against the user's selected position. Do not treat unrestricted analysis elsewhere in this file as automatically spoiler-safe.

Use only the controlled ledger values from `PROJECT_RULES.md`:

- `knowledge_state`: `open-question`, `clue`, `working-theory`, `strong-inference`, `strong-evidence`, `confirmed-fact`, `expanded-fact`, or `reader-misconception`.
- `disclosure_type`: `first-appearance`, `first-mention`, `first-meaningful-mention`, `first-clue`, `visual-hint`, `implicit-clue`, `context-link`, `inference`, `strong-inference`, `speculation`, `possibility`, `choice`, `explicit-identification`, `explicit-explanation`, `expanded-explanation`, `explicit-reveal`, `confirmation`, `practical-demonstration`, `ability-demonstration`, `practical-confirmation`, `pathway-inference`, `pathway-confirmation`, `staffing-snapshot`, `limitation`, `consequence`, `external-corroboration`, `expansion`, `recontextualization`, `rejection`, `adaptation-only-reveal`, or `early-reveal`.
- `adaptation_relationships.type`: `pending`, `faithful`, `revealed-earlier`, `revealed-later`, `condensed`, `expanded`, `recontextualized`, `omitted`, `changed`, `donghua-original`, or `uncertain`.

Use `pending` for adaptation relationships only while the adaptation comparison has not yet been verified.

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
  - pathway
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
  - type: pending
    novel_claim_changed: false
    notes: Adaptation comparison not yet verified.
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
