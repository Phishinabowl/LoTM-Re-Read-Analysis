# Thread Name

## Metadata

Type:
Status: Stub
First Mention Volume:
Subject Visible From:
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

If this page embeds official artwork, use a promoted page-ready asset under `Artwork/page-assets/` and make the embedded image clickable to its own full-size asset by default. Keep raw extraction and working-crop paths under `Artwork/Source/` out of rendered Markdown links and image tags; record them only as source/provenance metadata when needed.

This universal template is the shared glossary contract and maximal reference shape. Type-specific templates decide which sections are required, optional when relevant, or omitted by default. Do not add empty sections to real lightweight pages just to satisfy this template; use the relevant sections once the page has enough reader-safe material to support them.

Filename format is governed by `PROJECT_RULES.md`. Use this generic shape only as a quick reminder:

```text
[entity-type]-[kebab-case-name].md
```

Store the file in its matching plural category folder, such as `Characters/`, `Artifacts/`, `Items/`, `Knowledge_Sources/`, `Deities/`, `Uniquenesses/`, or `Mysteries/`, while retaining the filename prefix. For scoped or special filename families such as deity and uniqueness pages, follow `PROJECT_RULES.md` rather than duplicating the rule here.

Examples:

```text
artifact-0-08.md
character-azik-eggers.md
family-medici.md
faction-rose-school-of-thought.md
item-copper-whistle.md
source-roselle-diary-pages.md
concept-gray-fog.md
event-great-smog.md
uniqueness-die-of-probability.md
timeline-ian-zreal-chain.md
```

## Purpose

What recurring thread, symbol, faction, person, family, item, knowledge source, location, event, concept, or mystery does this file track?

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

Use a single block only when all reveal beats happen together. If the subject has layered disclosure, duplicate the beat heading pattern below as needed.

#### First Visual / Functional Appearance

- Volume:
- Chapter:
- Context:
- Reader knowledge state:

#### First Named Identification

- Volume:
- Chapter:
- Context:
- Reader knowledge state:

#### First Meaningful Explanation

- Volume:
- Chapter:
- Context:
- Reader knowledge state:

#### First Formal Confirmation

- Volume:
- Chapter:
- Context:
- Reader knowledge state:

### Donghua

Use the same beat-heading pattern when adaptation first appearance, naming, explanation, or confirmation differs from the novel or from itself.

- Season:
- Episode:
- Release order:
- Timestamp:
- Context:
- Viewer knowledge state:

## Chronological Development

### Novel

#### Volume X
<!-- timeline_id: subject-volume-x-arc (required for real entries; keep matched to timeline_entries.id) -->

- What the reader learns:
- What changes:
- What remains unknown:
- Why it matters:

### Donghua

#### Season X, Episode Y
<!-- timeline_id: subject-donghua-arc (required for real entries; keep matched to timeline_entries.id) -->

- Timestamp:
- What the viewer learns:
- What changes:
- What remains unknown:
- Why it matters:

Use extra labels such as `Attribution boundary`, `Visual/audio evidence`, `Adaptation difference`, or `Institutional detail` only when the arc genuinely needs them.

Mirror meaningful visible first-appearance beats in the type-specific data block so future website renderers can rebuild this section without inferring it from aliases, relationship rows, timeline entries, or knowledge units. Use a type-appropriate field such as `first_appearance_beats`, keep it near the start of the data block to match this page order, and preserve the same medium, position, context, and reader/viewer knowledge state.

Use `timeline_id` comments for every real visible chronology subsection, and keep each one matched to exactly one structured `timeline_entries.id` row in the type-specific data block. Blank placeholders and lightweight stubs may remove the example comment until the entry is populated. Keep the Markdown prose readable for GitHub, and use the data-block row as the future website/source-rendering structure.

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

## Type-Specific Data Block

Use the matching category template for this section when one exists. Replace this placeholder with the concrete heading, such as `Character Data Block` or `Pathway Data Block`, and keep the block immediately before `Relationship Seeds`.

Omit this section for lightweight stubs or categories whose data block shape has not been defined yet. Do not invent a generic schema just to fill this slot.

Visible prose and tables are the GitHub-readable article layer. Type-specific data blocks are the future renderer, filtering, and QA layer. When a visible table and data-block row describe the same extractable state, keep both synchronized; do not rely on future tooling to scrape the visible table. Order type-specific data-block sections to match the visible page sections as closely as practical, so a maintainer can compare prose, tables, and structured rows without jumping around the file.

Structured taxonomy values are not final website prose. Use kebab-case values for stable filtering, grouping, graphing, and reader-boundary logic; use human-written fields such as `summary`, `notes`, `reader_learns`, `changes`, `remains_unknown`, `why_it_matters`, `evidence`, or future `site_summary` / `display_text` fields for prose that may appear directly on a public page. Future renderers should map common taxonomy values through display labels, fall back to readable title-casing when needed, and use prose fields for natural sentences instead of trying to assemble article voice from enum values.

For any row that describes reader-visible state, use row-level `availability` instead of a single blended reveal field. `Subject Visible From` gates the whole page; `availability` gates individual facts after the page is visible. Each availability entry may include `graph_visibility` when the row can project into a relationship graph. Use `hidden` by default before the relationship itself is reader-visible, and reserve `anonymized` or `partial` for cases where the story has made an unknown actor, force, or relationship pattern visible without revealing the true source, target, or label.

When a page has meaningful `Chronological Development` prose, add a type-specific `timeline_entries` array so future reader-position renderers can reveal and sort the prose without scraping Markdown headings. Place `timeline_entries` in the data block at the point that corresponds to `Chronological Development` in the visible article order, not at the top of the block by default. The visible prose should remain the GitHub-readable article layer; `timeline_entries` should mirror its timing, summary, reader-learns, changes, unknowns, and why-it-matters fields as structured data. Keep visible chronology subsections and `timeline_entries` in the same oldest-to-newest reader/viewer order within each medium; insert newly discovered arcs into the correct position without renaming stable semantic IDs.

For pages with meaningful `First Appearance / First Meaningful Mention` prose, add a type-specific `first_appearance_beats` array or equivalent type-local field. Each row should mirror one visible beat and carry `medium`, `beat_type`, `title`, `position`, `context`, `reader_knowledge_state` or `viewer_knowledge_state`, optional `graph_display`, `status`, `confidence`, optional related timeline/claim references, and source refs. Keep early anonymous, partial, or ambiguous beats named from the reader's knowledge at that point rather than from later confirmation. Use `graph_display.behavior: anonymized-node` only when a reader-boundary graph or future site should show a safe presentation node before the canonical page title is reader-safe.

## Relationship Seeds

Use this section only for relationships important enough to support future relationship graphs. Relationship Seeds are graph projection hints, not full state histories or replacements for data blocks and knowledge units.

Prefer one canonical seed owner for each semantic edge. Store local rosters, holders, access rows, aliases, detailed state, and confidence progression in the visible section and type-specific data block. Use Reader Knowledge Ledger disclosures for reveal/audit explanation, adaptation comparison, and misconception or supersedence notes that need narrative context.

Keep entries reader-boundary aware and mark unverified start points as `TBD`. `start` is the earliest reader-safe point where the edge becomes graph-worthy, not necessarily the confirmation point.

When a seed projects a data-block row, set `projection_source`. QA graph labels should then summarize that row's meaningful availability history, while pending/TBD adaptation rows remain in the data block until they are verified.

`projection_source` should point to a structured data-block row on the seed source page, not to a visible Markdown table. For possession, custody, and equipment state, seed only graph-worthy edges; keep minor/disposable rows data-only.

Order Relationship Seeds by the visible/data-block section they project from when possible. For example, keep affiliation-derived seeds near other affiliation seeds, ability-derived seeds near ability seeds, relationship-derived seeds near relationship seeds, and event-derived seeds near event seeds. This ordering is for maintainer readability only; graph generators should not depend on seed order.

Use `status: broken` only for relationships that are explicitly ruptured, breached, failed, destroyed, or narratively broken. For ordinary ended custody, possession, residence, access, or employment, prefer projected data-block state such as `possession_status: lost-custody` with `status: historical` where needed.

Omit this section on actual pages only when no graph-worthy relationships have been identified yet.

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

Add one block for each durable spoiler-timed claim. Duplicate the block as needed. Keep novel and Donghua disclosure timelines independent.

Together, these units should preserve the subject's durable disclosure and audit history. Add separate disclosure entries for meaningful reveal points, including multiple entries from the same medium when a claim progresses from first mention, to clue, to inference, to explicit reveal, or to confirmation. Keep ordinary current-state facts in the visible sections and type-specific data block.

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

<!-- Add a collapsible Maintainer Notes block only when this page needs page-specific modeling, boundary, rendering, future split, or migration notes. Do not add empty maintainer-note placeholders to real pages. -->
