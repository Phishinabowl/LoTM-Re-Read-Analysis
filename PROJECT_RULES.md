# Lord of the Mysteries Re-Read Project

## Project Overview

We are conducting a deep reread analysis of **Lord of the Mysteries (Book 1)**.

### Reader Status

- User has completed all 8 volumes of Lord of the Mysteries (Book 1).
- User has NOT completed all of Circle of Inevitability (Book 2).
- Avoid COI spoilers unless explicitly requested.

### Project Goals

This is not a summary project.

This is an investigation project focused on:

- Chronology
- Character development
- Themes
- Foreshadowing
- Reveal order
- Historical causality
- Family lineages
- Ancient history
- Reader knowledge state

The objective is to reconstruct:

1. What happened.
2. When it happened.
3. Why it happened.
4. What the reader knew at that moment.
5. How later revelations change understanding.

---

# Project File Structure

The project uses the following files and folders:

```text
Boards/
  01_LoTM_Main_Reread_Board.md
  02_LoTM_Ancient_History_Family_Board.md

Volumes/
  TEMPLATE.md
  volume-01-clown.md
  planned volume summary pages

Investigations/
  TEMPLATE.md
  Artifacts/
  Characters/
  Concepts/
  Events/
  Factions/
  Items/
  Knowledge_Sources/
  Locations/
  Pathways/
  Project/
  type-specific source verification records, split by subject and medium

Glossary_Threads/
  TEMPLATE.md
  Artifacts/
  Characters/
  Concepts/
  Deities/
  Epochs/
  Events/
  Factions/
  Families/
  Items/
  Knowledge_Sources/
  Locations/
  Mysteries/
  Pathways/
  Timelines/
  Uniquenesses/
  recurring subject records and embedded spoiler-aware knowledge units

Visualization/
  README.md
  graph-authoring-standard.md
  config/
  data/
  graphs/
  rendered/
  generated graph artifacts, render settings, and provisional graph schema notes

Tools/
  README.md
  Python-preferred helper scripts
  documented PowerShell fallbacks

Artwork/
  README.md
  official-epub-image-map.md
  page-assets/
  tracked page-ready artwork plus ignored local source-artwork workspace

Source/
  README.md
  local EPUB, Donghua subtitles, and future source materials (Git ignored)

Testing/
  local scratch outputs and temporary experiments unless deliberately promoted

Obsidian_Export/
  local generated Obsidian QA mirror and repo graph dry-run bundle (Git ignored)

.obsidian/
  local Obsidian vault settings (Git ignored)

.tmp/
  local scratch workspace (Git ignored)

INDEX.md
CURRENT_STATE.md
PROJECT_RULES.md
00_READ_FIRST_AI_AGENT_BOOTSTRAP.md
README-AI-Agent-Specification.md
MAINTAINER_CONTEXT.md
ASSISTANT_CONTEXT.md (deprecated redirect)
README.md
LICENSE
NOTICE.md
```

These files and folders are the project's working memory.

When conclusions are reached:

- Update the appropriate board(s).
- Create investigation records when appropriate.
- Preserve chronology.
- Preserve reader knowledge state.

## Current State Dashboard Rules

`CURRENT_STATE.md` is the live project dashboard. Keep it aligned with the actual active focus.

Update `CURRENT_STATE.md` whenever:

- the active investigation focus changes;
- a glossary thread is created;
- a glossary thread moves between pending, in-progress, completed, dormant, resolved, or superseded;
- an investigation meaningfully advances a thread's reader boundary;
- a generated/planned thread title becomes a tracked pending item;
- a visualization workflow exposes durable project status or backlog information.

Track glossary pages in three practical groups:

- `Completed Threads`: threads whose current defined scope has been reviewed and recorded.
- `In-Progress Threads`: active or partially built threads, including their current reader boundary and approximate Volume progress.
- `Pending / Deferred Threads`: generated or planned thread titles that do not yet have dedicated glossary pages.

Within `Pending / Deferred Threads`, mark existing pending entries as `(artwork backed)` when official artwork has already been mapped to that subject. If more than one official artwork image maps to the same pending subject, include the count as `(artwork backed, N images)`. If a mapped artwork subject does not already appear elsewhere in the pending backlog, add it to a lowest-priority `Artwork-Backed Pending Threads` subsection instead of promoting it automatically.

When official artwork uses a classic or alternate pathway name that differs from the novel/common name, keep the article slug and primary thread identity aligned to the novel/common name, and preserve the artwork name in the map label, notes, and future pathway alias table. Examples: map Mother artwork to `pathway-planter.md`, Justiciar artwork to `pathway-arbiter.md`, Paragon artwork to `pathway-savant.md`, Red Priest artwork to `pathway-hunter.md`, and Wheel of Fortune artwork to `pathway-monster.md` after term arbitration shows the in-text pathway name is stronger. For Demoness/Assassin, term arbitration favors `pathway-demoness.md`; preserve Assassin as the Sequence 9 name and alternate pathway label where the text uses it. For Monster/Wheel of Fortune/Fate, preserve Wheel of Fortune and Fate as aliases.

For Volume 1 progress percentages, use the current verified chapter boundary divided by 213 total chapters. Treat the percentage as a chapter-boundary indicator, not a guarantee of article quality, cross-link completeness, or adaptation completeness.

When a thread spans more than one medium, track novel and adaptation progress separately where practical. Do not let one medium's progress silently advance another.

Do not create all pending threads just because they appear in `CURRENT_STATE.md`. Pending items are a backlog, not an instruction to scaffold every file.

## Artifact Responsibilities

Use each project artifact for a distinct purpose:

- `Boards`: Analyst-facing volume-level state, major themes, broad conclusions, current research direction, and links to detailed records.
- `Volumes`: Reader-facing end-of-volume dashboards, official volume artwork homes, summary-level developments, and links to glossary/investigation evidence.
- `Glossary_Threads`: Subject-specific information, durable disclosure history, structured reader-state filtering data, and adaptation comparisons.
- `Investigations`: Evidence, verification history, and supported conclusions for questions that required consulting the EPUB.
- `Visualization`: Generated visualization artifacts, such as Mermaid graphs, rendered graph images, and future graph data exports.
- `Tools`: Repeatable local maintenance, source-search, artwork, visualization, Obsidian export, and cleanup helpers. Prefer Python helpers when available and documented PowerShell fallbacks when Python is unavailable.
- `Artwork`: Tracked official artwork metadata and selected page-ready assets. Bulk extraction, intermediate crops, and source-derived staging stay local-only.
- `Source`: Local canonical source materials such as the EPUB and Donghua subtitles. Copyrighted source files stay ignored by Git.
- `Testing`: Local scratch outputs and temporary experiments. Promote durable outputs into the appropriate canonical folder only after maintainer confirmation.
- `Obsidian_Export`: Ignored local QA mirror generated from repository records for Obsidian graph inspection, anomaly detection, relationship review, and no-render repository graph refresh checks.

Do not duplicate granular reveal chronology across boards, volume pages, and glossary threads. Keep the filterable detail in the glossary thread and summarize only the durable volume-level meaning on the appropriate board or volume page.

Boards are analyst-facing overview documents, not the canonical source for automatic spoiler filtering. A future reader-facing system may gate a board by its volume boundary, but glossary knowledge units remain the source for position-specific filtering.

Volume summary pages are reader-facing overview documents for completed volume boundaries. They may include official volume cover/opening art, end-of-volume art, and volume gallery title pages. Subject-specific character, location, pathway, artifact, deity, faction, event, or concept artwork should still map primarily to the corresponding subject page when that page exists.

Planned-but-uncreated volume summary pages should be listed in `INDEX.md` as planned paths and tracked in `CURRENT_STATE.md` under `Planned Volume Summary Pages`. The artwork map may point volume-level artwork at those planned targets before the page exists, but those planned references should remain visibly marked as planned.

## Documentation Ownership

Keep `PROJECT_RULES.md` focused on durable project policy: source of truth, spoiler boundaries, glossary modeling, relationship taxonomy, data-layer responsibilities, and maintenance gates.

Use specialized docs for operational detail:

- `Tools/README.md`: exact helper commands, Python/PowerShell fallbacks, EPUB search, Obsidian QA export, artwork extraction, and cleanup behavior.
- `Visualization/README.md`: current generated graph artifacts, refresh tracker, configured graph views, and visualization workflow entry points.
- `Visualization/graph-authoring-standard.md`: graph intent, graph-local evidence, source expansion, coverage workflow, graph projection, layout semantics, and graph output reporting.
- `Visualization/rendering.md`: render commands, validation modes, render sizing, class/layout validation, and render troubleshooting.
- `Visualization/data/graph-schema.md`: provisional generated graph data fields and presentation-node schema.

When a rule appears in more than one place, keep the policy statement here and put the commands, examples, and troubleshooting details in the narrower document.

## Artwork Asset Safety

Official EPUB artwork metadata is tracked in `Artwork/official-epub-image-map.md`, but bulk source-derived image assets are local-only staging files.

Keep this directory ignored and untracked:

- `Artwork/Source/`

This mirrors the treatment of the source EPUB and subtitle/source-media files: the project can use local assets for inspection, mapping, and page planning without publishing the whole extracted asset set.

When an article intentionally embeds official artwork, promote only that specific page-ready image into a tracked location such as `Artwork/page-assets/`. Do not bulk-promote extracted EPUB images, crop batches, or intermediate working assets.

By default, embedded page images should be clickable links to their own full-size page-ready asset unless a page-specific layout deliberately needs different behavior. Use the same `Artwork/page-assets/` path for both the displayed image and the surrounding link.

---

# Visualization

Visualization files are generated outputs. `Obsidian_Export/` is also a generated output, but it is a local-only QA mirror rather than a GitHub-visible visualization artifact.

The graph source of truth remains:

- Glossary thread metadata
- Embedded Reader Knowledge Ledger sections in glossary threads
- Type-specific data blocks and their row-level `availability` entries
- Relationship Seeds
- Controlled relationship taxonomy in this file

Generated visualization outputs may include:

- Mermaid `.mmd` files
- Rendered SVG or PNG files
- JSON graph data
- Future frontend graph views

Generated Obsidian QA outputs may include:

- Obsidian-friendly mirror notes
- relationship and data-reference indexes
- local-only QA Mermaid `.mmd` files
- a `_Generated/repo-refresh-check/` dry run of configured repository graph views, including generated Mermaid sources, a refresh report, a semantic snapshot, and generated check settings
- orphan, suspicious-edge, duplicate-edge, and unknown-target reports

Do not treat generated graph files, generated Obsidian mirror notes, or generated QA reports as canonical project knowledge.

Do not manually edit generated graph outputs or generated Obsidian export files except for debugging or temporary inspection. Fix durable graph problems by updating the relevant glossary thread, investigation record, Relationship Seed, data block, or controlled taxonomy, then regenerate the output.

For durable canonical graph or Obsidian QA corrections, if a generated view exposes missing or incorrect data:

1. Fix the glossary or investigation record.
2. Update Relationship Seeds or structured data blocks when the relationship or extracted-data model changes.
3. Regenerate the relevant output.

For graph-only maintainer work or Obsidian QA export work, do not silently update glossary threads, investigations, boards, current state, index, Relationship Seeds, or data blocks while producing the generated view. Graph generation may read project records and allowed local sources, include clearly marked graph-local evidence, and report candidate project-data updates. Ask for maintainer confirmation before editing canonical project records.

The Obsidian QA export's `_Generated/repo-refresh-check/` bundle is a local dry run of the configured repository visualization refresh. It is generated inside ignored `Obsidian_Export/`, runs with rendering disabled, and must not be mistaken for updating canonical files under `Visualization/graphs/`, `Visualization/rendered/`, `Visualization/data/refresh-snapshot.json`, or `Visualization/README.md`.

Use the shared [Graph Authoring Standard](Visualization/graph-authoring-standard.md) for graph construction. It defines canonical versus graph-local evidence, source expansion, pathway/sequence coverage, maintainer confirmation, and output reporting.

For dense Mermaid graphs, prefer semantic relationship nodes over long edge labels. A generated relationship node may hold the relationship type, timing, status, confidence, and provenance, with simple arrows from source to relationship node to target. These relationship nodes are presentation artifacts only. They are not glossary nodes, do not create new canonical entities, and must be regenerated from canonical glossary records such as Relationship Seeds and projected type-specific data-block rows.

Use direct edge labels only when the graph remains readable. If rendered labels overlap, collide, or become hard to follow, update the visualization generator or graph projection rather than hand-editing the generated Mermaid.

## Visualization Refresh Gate

Before committing a change, check whether graph inputs changed.

Graph regeneration is recommended when any of these change:

- a glossary page is created, deleted, renamed, or moved;
- `Relationship Seeds` are added, removed, or changed;
- a relationship type, relationship status, relationship confidence, source node, or target node changes;
- a node type changes, such as `concept` to `faction`;
- a graph-relevant type-specific data-block row or row-level `availability` entry changes;
- the controlled relationship taxonomy changes;
- graph-relevant metadata changes, such as thread title, type, status, reader boundary, or spoiler boundary.

Graph regeneration is not required for:

- prose-only investigation updates;
- typo fixes or style cleanup;
- explanation wording that does not change structured data;
- confidence discussion that does not change a structured confidence field;
- board prose that does not alter graph inputs.

When graph regeneration is recommended, tell the user before editing generated visualization files. Treat graph refresh like commits: recommend it when appropriate, but confirm before changing generated graph artifacts.

When a graph refresh is confirmed, update every current graph view unless the user explicitly narrows the scope. This includes all existing Mermaid graph files and their rendered outputs in the currently used formats.

For the current repository, a normal graph refresh means updating:

- `Visualization/graphs/volume-1-knowledge-graph.mmd`
- `Visualization/graphs/volume-1-knowledge-graph-timing-spoiler-free.mmd`
- matching rendered SVG files, when present
- matching rendered PNG files, when present

Fresh renders should replace the stale render files rather than accumulating duplicate dated copies unless the user asks for archived snapshots.

The Obsidian QA export also emits a no-render dry run of these configured views under `Obsidian_Export/_Generated/repo-refresh-check/`. Use it for inspection before deciding whether a real graph refresh is warranted; it does not replace the confirmed canonical refresh workflow above.

For exact visualization helper commands, validation modes, pure-render behavior, render sizing, and troubleshooting, use `Visualization/README.md` and `Visualization/rendering.md`. For graph-local evidence, source expansion, layout semantics, dense graph shape, visual role grammar, and output reports, use `Visualization/graph-authoring-standard.md`.

Use this maintenance lifecycle for project-knowledge changes:

```text
Investigation
↓
Glossary / Relationship Seeds
↓
Bidirectional relationship sweep
↓
Current State update
↓
Index update
↓
Visualization refresh check
↓
Commit review
↓
Commit
```

Graph tooling should support dynamic generation, timeline filtering, reader-state filtering, and multiple graph views without making the rendered graph the source of truth. Configured visualization views may use `readerBoundary` to filter generated nodes by `Subject Visible From` and filter generated relationships by Relationship Seed `start` timing.

---

# Glossary Threads

Glossary thread files track recurring threads, symbols, factions, people, families, concepts, and mysteries that appear across multiple reread moments.

Use glossary threads when a topic becomes too recurring or cross-cutting for a single board entry.

Examples:

- 0-08
- Antigonus
- Medici
- Rose School of Thought
- Adam / Amon
- Gray Fog

Glossary threads must preserve reread chronology and reader knowledge state.

Do not contaminate early entries with future reveals.

## Naming Convention

Use lowercase kebab-case filenames with an entity-type prefix:

```text
artifact-[name].md
character-[name].md
family-[name].md
faction-[name].md
item-[name].md
source-[name].md
location-[name].md
concept-[name].md
event-[name].md
deity-[scope]-[name].md
uniqueness-[name].md
pathway-[name].md
epoch-[name].md
mystery-[name].md
timeline-[name].md
```

Examples:

```text
artifact-0-08.md
artifact-antigonus-notebook.md
character-azik-eggers.md
character-amon.md
family-antigonus.md
family-medici.md
faction-rose-school-of-thought.md
item-copper-whistle.md
source-roselle-diary-pages.md
concept-gray-fog.md
event-great-smog.md
deity-s0-evernight-goddess.md
deity-ats-lord-of-the-mysteries.md
deity-ats-goddess-of-origins.md
deity-od-mother-goddess-of-depravity.md
uniqueness-die-of-probability.md
pathway-seer.md
epoch-fourth-epoch.md
mystery-mr-door.md
timeline-ian-zreal-chain.md
```

If a thread fits multiple categories, choose the category that best matches the analytical purpose of the file.

Use `item-[name].md` for named, recurring, graph-worthy possessions, tools, badges, keys, weapons, instruments, or other important objects that are not best modeled as formal supernatural artifacts or knowledge sources. Item pages are for objects that become independent relationship hubs or recurring reader-facing subjects, such as the copper whistle; ownership, custody, and source-holder details belong in the item data block rather than in the filename. Do not create item pages for ordinary disposable inventory, temporary equipment, one-scene props, or recurring texts whose main function is revealing information.

Use `source-[name].md` for recurring knowledge carriers whose analytical purpose is revealing, preserving, transmitting, translating, or misdirecting information over time. Knowledge Source pages are for diary-page corpora, spellbooks, grimoires, notebooks, scriptures, case files, letters, inscriptions, formula records, murals, records, or similar sources where the important thing is the sequence of claims, quotes, access points, readers, handlers, and interpretations. Do not create a Knowledge Source page for every ordinary document mention; use one when the source is a recurring reveal hub or needs its own chronology of knowledge entries.

For sources encountered as fragments, batches, pages, inscriptions, chapters, files, or excerpts, keep one page for the recurring source and track individual reveal units inside `knowledge_source_profile.knowledge_entries`. Use `source_unit_id` as the stable local identifier for the encountered unit, `source_unit_type` for values such as `diary-page`, `page-batch`, `spellbook-entry`, `inscription`, `case-file`, or `formula-record`, `batch_id` when several units arrive together, `fragment_id` for a specific fragment/page/excerpt inside that batch, and `sequence_index` for reader-order sorting inside the source page. Do not create separate glossary pages for every page or fragment unless that fragment becomes an independent named subject.

Use unit-level provenance fields on `knowledge_entries` when access differs by batch or page. `provider` records who held, supplied, submitted, displayed, or mediated that specific source unit; `provider_role` describes their role; `transfer_mode` distinguishes incidental access, deliberate submission, sale, theft, loan, discovery, ritual access, or archival access; `reader` records who reads or interprets it; `reader_access_type` distinguishes intended recipient, opportunistic reading, authorized review, covert reading, or mediated interpretation; `holder_understanding` records whether the holder understands, partially understands, cannot read, misreads, or merely stores the source; `intentionality` records whether the reveal to the reader/interpreter was intended, accidental, coerced, transactional, or unknown; and `mediation` records direct reading, translation, copied text, paraphrase, summary, vision, or other access mode.

Use `artifact-[name].md` for formal mystical artifacts, sealed artifacts, supernatural objects with established artifact identity, or plot-center objects whose supernatural nature is the analytical point. When uncertain, keep the object in a character, faction, location, or artifact data block with `page_worthiness: candidate` until the page type is clear.

For potion, ritual, charm, ammunition, and crafted supernatural output modeling, keep these analytical roles separate even when the same story object participates in more than one role:

- **Materials** are raw inputs or components, such as herbs, crystals, monster parts, blood, metals, powders, liquids, or other formula ingredients. Record them inline in pathway, ritual, item, artifact, or event data until a recurring material becomes page-worthy.
- **Preparations** are outputs made, charged, consecrated, assembled, or activated by a formula, ritual, prayer, craft process, or supernatural method. This future page family should cover charms, ritual bullets, blessed powders, talismans, prepared ritual tools, and durable or repeatable ritual effects. A preparation may have `physical_form: item`, `physical_form: consumable-item`, or `physical_form: none`.
- **Items** are durable named possessions, tools, or carriers with object identity and custody history. If a preparation becomes a recurring possessed object, track possession on the preparation or item record, but do not promote every made charm or expendable bullet to an Item page by default.
- **Artifacts** are formal supernatural artifacts, Sealed Artifacts, or artifact-identity objects, not merely any supernatural object produced by a ritual.
- **Concepts** own reusable systems and mechanics, such as prayer structures, ritual categories, summoning theory, and pathway theory.

Do not create `Glossary_Threads/Materials/` or `Glossary_Threads/Preparations/` until the project needs dedicated pages and templates. Until then, pathway pages may record formula ingredients inline, concept pages may record reusable ritual mechanics, and item/artifact/source pages may point to those systems when the object or source is graph-worthy.

The overall taxonomy and idea of sefirot should use the shared concept page `concept-sefirot.md`. Individual named sefirot, such as Sefirah Castle, Tenebrous World, Nation of Disorder, Knowledge Moor, City of Calamity, Key of Light, or Brood Hive, should use `location-[name].md` under `Glossary_Threads/Locations/`. This is an intentional pragmatic category choice: named sefirot behave like special places/realms for page organization even when they are not ordinary physical locations.

Deity pages use a required second-level scope in the filename so true gods, Above the Sequences title clusters, and Outer Deity entities do not collapse into each other:

- `deity-s0-[name].md` for Sequence 0 / true god pages.
- `deity-ats-[name].md` for Above the Sequences / Great Old One title-cluster pages.
- `deity-od-[name].md` for Outer Deity / Outer God entity pages.

Keep these pages separate when the same pathway cluster exposes multiple layers. For example, `deity-s0-earth-mother-lilith.md`, `deity-od-mother-goddess-of-depravity.md`, and `deity-ats-goddess-of-origins.md` are all related to the Planter/Moon group without being the same article subject. Use the exact plural `goddess-of-origins` slug for the Chapter 1347 ATS title cluster; treat singular `Goddess of Origin` as a substring or artwork-label/translation variant unless later evidence supports it separately.

Every pathway page should include an `Associated Uniqueness` section when the pathway's Uniqueness is known, implied, or relevant to an Above the Sequences formula. Do not create a dedicated `uniqueness-[name].md` page merely because a formula names a pathway's Uniqueness, such as `Mother Uniqueness` or `The Moon Uniqueness`. Create a dedicated Uniqueness page only when the Uniqueness is named, embodied, or tracked as a distinct item/entity in the story. Use `uniqueness-[name].md`, link it back to the pathway and Sequence 0/deity pages, and preserve holder/accommodation state separately from pathway identity. Example: `uniqueness-die-of-probability.md` is the Monster / Fate / Wheel of Fortune pathway Uniqueness and should cross-link `pathway-monster.md`, `deity-s0-wheel-of-fortune.md`, and relevant character-holder pages such as Will Auceptin and Ouroboros.

Mythical creature forms should be tracked through a shared `concept-mythical-creature-forms.md` concept/index page rather than separate `mythical-creature-*` glossary pages by default. The concept page should keep a table of forms with links to the relevant pathway, character, deity, and evidence records. Character and pathway pages should record the specific form/state in their local tables and data blocks, then use relationship seeds to point to the shared concept when the relationship is graph-worthy.

When recording mythical creature forms, preserve the form version/stage and the Sequence or advancement threshold that unlocks, changes, or upgrades it. Many pathways have multiple form versions tied to progression, so do not collapse a character's early form state and later form state into one row. Character form-state rows should accumulate newest-to-oldest like other mutable character facts, while the concept page can group form versions by pathway and Sequence threshold.

## Folder Organization

Store glossary threads in plural, type-specific subfolders:

```text
Glossary_Threads/Artifacts/
Glossary_Threads/Characters/
Glossary_Threads/Deities/
Glossary_Threads/Families/
Glossary_Threads/Factions/
Glossary_Threads/Items/
Glossary_Threads/Knowledge_Sources/
Glossary_Threads/Locations/
Glossary_Threads/Concepts/
Glossary_Threads/Events/
Glossary_Threads/Uniquenesses/
Glossary_Threads/Pathways/
Glossary_Threads/Epochs/
Glossary_Threads/Mysteries/
Glossary_Threads/Timelines/
```

Retain the entity-type filename prefix inside the matching folder. For example:

```text
Glossary_Threads/Characters/character-amon.md
Glossary_Threads/Artifacts/artifact-0-08.md
Glossary_Threads/Items/item-copper-whistle.md
Glossary_Threads/Knowledge_Sources/source-roselle-diary-pages.md
Glossary_Threads/Deities/deity-s0-evernight-goddess.md
Glossary_Threads/Uniquenesses/uniqueness-die-of-probability.md
Glossary_Threads/Mysteries/mystery-mr-door.md
```

Create a category folder when its first thread is created. Do not add placeholder files solely to make empty folders visible in Git.

Adding a glossary type requires updating the naming convention, controlled domain tags, folder structure, template guidance, and index rules together.

## Metadata Standards

Every glossary thread should begin with a `Metadata` section using the same fields:

```text
Type:
Status:
First Mention Volume:
Subject Visible From:
Current Analysis Status:
Confidence Level:
Spoiler Boundary:
Reader Knowledge Boundary:
Tags:
Last Updated:
```

Use these fields consistently:

- `Type`: Entity type, such as Artifact, Character, Family, Faction, Location, Concept, Event, Pathway, Uniqueness, Epoch, Mystery, or Timeline.
- `Status`: Thread lifecycle, such as Stub, Active, Dormant, Resolved, or Superseded.
- `First Mention Volume`: Earliest known volume where the thread meaningfully appears.
- `Subject Visible From`: Earliest reader position where the page subject, title, or browse/search result is safe to expose as that subject. Use this for page-level filtering. This may be later than the first visual appearance when the subject is initially anonymous, misattributed, or only knowable as a mystery.
- `Current Analysis Status`: Current project state, such as Not Started, In Progress, Needs EPUB Verification, or Verified.
- `Confidence Level`: Confidence in the current interpretation, such as Confirmed, Strong Evidence, Working Theory, Unknown, or Mixed.
- `Spoiler Boundary`: Latest broader canon range this thread is allowed to reference.
- `Reader Knowledge Boundary`: Exact reread point, usually a chapter, that defines what the reader knows for this entry.
- `Tags`: Controlled taxonomy tags from the approved categories below.
- `Last Updated`: Date of the last meaningful file update.

When a thread tracks more than one medium, record each `Reader Knowledge Boundary` independently, such as a novel chapter and a Donghua release position. Never let one medium's boundary silently advance another.

The metadata section may also include:

```text
Related Threads:
- [thread-file]

Related Investigations:
- [investigation-file]
```

Use filenames without paths for metadata references unless a full Markdown link is useful.

## Glossary House Style

Glossary pages are synthesis records. They should be readable as articles while still supporting future filtering, dashboards, and relationship graphs.

Visible prose and tables are the public GitHub-readable article layer. Type-specific data blocks are the structured future-renderer layer. Keep both in sync while the repository remains Markdown-first. Do not remove visible tables merely because the data block can represent the same facts; a later website may generate those tables from structured data, but GitHub pages should remain usable in the meantime.

Structured taxonomy values are not final website prose. Use kebab-case values for stable filtering, grouping, graphing, sorting, reader-boundary logic, and dashboard logic. Use human-written fields such as `summary`, `notes`, `reader_learns`, `changes`, `remains_unknown`, `why_it_matters`, `evidence`, `claim_text`, labels, or future `site_summary` / `display_text` fields for sentences that may appear directly on public pages. Future website renderers should map reusable taxonomy values through a controlled display-label layer, fall back to readable title-casing for unlabeled values, and use prose fields for natural article voice instead of assembling full paragraphs from enum values.

`Glossary_Threads/TEMPLATE.md` is the universal glossary contract and maximal shared shape, not a demand that every stub or lightweight page include every empty section. Use the same top-level section order unless a type-specific template has a strong reason to deviate:

1. Metadata
2. Purpose
3. Spoiler Boundary
4. Reader Knowledge Boundary
5. First Appearance / First Meaningful Mention
6. Chronological Development
7. Open Questions
8. Related Threads
9. Type-Specific Data Block, when present
10. Relationship Seeds
11. Evidence Index
12. Reader Knowledge Ledger
13. Maintainer Notes, when needed

### Type-Specific Glossary Overlays

The universal glossary template defines the shared article contract. Type-specific folders may also define overlay templates when a glossary type has recurring fields that should be easy to extract for graphs, dashboards, or reader-state filters.

Use a type-specific overlay only when it adds predictable structure that the universal template cannot express cleanly. The overlay should preserve the shared metadata, relationship seeds, evidence index, reader knowledge ledger, and optional maintainer notes. Type-specific templates decide which sections are required, optional when relevant, or omitted by default. Do not add empty sections to real pages just to satisfy a maximal template.

Place human-facing type-specific sections near the top of the article after `Reader Knowledge Boundary`. Type-specific overlays may keep `First Appearance / First Meaningful Mention` immediately after the snapshot when first reveal timing is especially important to scan early. Keep machine-readable type-specific data blocks near the bottom of the article, immediately before `Relationship Seeds`, so structured extraction material stays grouped while the main page remains easy for humans to read.

Maintainer Notes are optional page-local implementation notes. Do not include a Maintainer Notes block in every page by default. Add the collapsible block only when a page needs specific modeling, boundary, rendering, future split, or migration notes that do not belong in the reader-facing article flow.

Current type-specific overlays:

- `Glossary_Threads/Pathways/TEMPLATE.md`: pathway pages should expose `Pathway Snapshot`, `Pathway Names / Reader Display Timeline`, `Associated Tarot Card`, `Known Sequences`, `Institutional Access`, `Affiliated Factions`, `Known Holders`, and `Pathway Data Block` sections.
- `Glossary_Threads/Characters/TEMPLATE.md`: character pages should expose `Overall Summary`, `Character Snapshot`, `Names, Aliases & Titles`, `Physical Profile`, `Status, Origin & Location`, `Affiliations`, `Pathway & Ability State`, `Ability Index`, `Equipment & Artifacts`, `Personality`, `Relationships`, `Messenger / Servants / Companions`, `Prayers & Ritual Access`, `Major Events & Fights`, and `Character Data Block` sections. Include `Mythical Creature Form State` and `Uniqueness State` only when the character has relevant reader-safe material for those relationships; do not add empty placeholder sections just because the template supports them.
- `Glossary_Threads/Items/TEMPLATE.md`: item pages should expose `Item Snapshot`, `Names & Labels`, `Ownership / Custody / Access`, `Functions & Uses`, `Related Concepts / Systems`, `Appearance / Physical Description`, and `Item Data Block` sections. Use Item pages for named, recurring, graph-worthy non-artifact objects. Keep minor equipment and disposable possessions in local character, faction, location, or event data blocks without creating a page.
- `Glossary_Threads/Knowledge_Sources/TEMPLATE.md`: knowledge source pages should expose `Source Snapshot`, `Names & Labels`, `Format / Medium`, `Authorship / Origin`, `Access / Custody / Readers`, `Knowledge Entries`, `Quote / Evidence Index`, and `Knowledge Source Data Block` sections. Use Knowledge Source pages for recurring reveal carriers whose claims, quotes, custody/access, interpretation, and reader-safe chronology need to be tracked independently.

### Character Article Overlay

Character pages should include the character overlay once the page has enough verified material to support more than a stub. The overlay is required for active character pilot pages and recommended for any future character page with reader-safe identity, role, affiliation, pathway, relationship, inventory, event-participation, or ability data.

For active or retrofitted character pages, treat these sections as the required minimum unless the page is explicitly a lightweight stub: `Metadata`, `Purpose`, `Spoiler Boundary`, `Reader Knowledge Boundary`, `Overall Summary`, `Character Snapshot`, `First Appearance / First Meaningful Mention`, `Chronological Development`, `Character Data Block`, `Relationship Seeds` when any graph-worthy relationship is known, `Evidence Index`, and `Reader Knowledge Ledger`.

Use these character modules when relevant: `Names, Aliases & Titles`, `Physical Profile`, `Status, Origin & Location`, `Affiliations`, `Pathway & Ability State`, `Ability Index`, `Equipment & Artifacts`, `Personality`, `Relationships`, and `Major Events & Fights`. Omit empty optional modules from real pages until the character has reader-safe material for them.

Omit these specialized modules by default unless they have meaningful reader-safe material: `Mythical Creature Form State`, `Uniqueness State`, `Messenger / Servants / Companions`, `Prayers & Ritual Access`, and `Prayer / Ritual Texts`.

Character pages should include an `Overall Summary` section immediately before `Character Snapshot`. This section should provide a reader-safe synthesis of who the character is at the current boundary. It can be more natural and interpretive than the structured rows, and it may be one paragraph for minor characters or a few concise paragraphs for major characters with more development. It must stay inside the reader boundary and avoid later emotional or plot contamination. The snapshot bullets should summarize the latest reader-safe state without replacing chronological development. Keep state/history tables newest-to-oldest by reveal or change point so the latest visible state appears first at the current reader boundary. Keep `Major Events & Fights`, chronological development, evidence indexes, and reader knowledge ledgers oldest-to-newest because those sections preserve event or reading order.

When official character artwork is mapped and promoted into `Artwork/page-assets/characters/`, place a compact clickable primary character image immediately under the page H1 and before `Metadata`. Omit the image block until a page-ready asset exists; do not link directly to ignored bulk-extracted artwork.

Mutable character facts should accumulate rows instead of overwriting old values. This includes aliases, titles, age, vital status, residence, affiliations, pathway status, Sequence advancement, mythical creature form state, Uniqueness possession/control/accommodation state, equipment/item possession, relationships, companions, and ability access. Future reader-boundary tooling should hide rows after the chosen boundary and compute the current state from the remaining rows.

For type-specific data blocks, every row that describes reader-visible state should support `availability`. Use page metadata `Subject Visible From` as the whole-page gate, then use row-level `availability` as the fact-level gate. Static implementation fields such as `data_model_version`, `stable_slug`, `state_sort_order`, local artwork file paths, or internal usage labels do not need availability unless their display would itself reveal spoiler-sensitive subject information.

Visible character tables and `character_profile` rows should mirror each other when they describe the same extractable state. If they conflict, update both. The visible table remains the GitHub-readable article surface; the data-block row is the future renderer, filtering, and QA source. Do not make future tooling scrape visible tables when a structured row can carry the same data. Order type-specific data-block sections to match the visible page sections as closely as practical; for character pages, place `timeline_entries` after `major_events_fights` because `Chronological Development` follows `Major Events & Fights` in the visible article.

Use snake_case for data-block field names and lowercase kebab-case for controlled values. Reuse generic values across page types where possible. If a value will repeat across multiple page types, define or reference it in `PROJECT_RULES.md`; if it is character-specific, define it in the character template and keep the specific nuance in `notes` rather than inventing one-off values. Repeated controlled values that will be user-visible should eventually receive explicit display labels; rare or temporary values may rely on renderer fallback title-casing until they prove reusable.

Use `Pathway & Ability State` for broad stateful supernatural status such as pathway, Sequence, advancement, digestion, or limitations. Use `Ability Index` for individual capabilities and skills, including pathway abilities, artifact-granted effects, rituals, authority, training, knowledge, or mundane competencies.

Use `Prayers & Ritual Access` for character-specific prayer addresses, exact prayer wording when reader-safe, ritual labels, target functions, and cross-links to `Glossary_Threads/Concepts/concept-prayers-and-rituals.md`. Keep general ritual theory, reusable prayer/ritual type definitions, and cross-character comparisons on the concept page rather than duplicating them inside character pages.

Use `Equipment & Artifacts` for broad local possession, custody, access, use, or investigation state. Add item relevance fields when the row may become graph-visible or page-worthy: `item_significance` (`minor`, `recurring`, `major`), `graph_relevance` (`none`, `local`, `full`), and `page_worthiness` (`none`, `candidate`, `dedicated-page`). Minor or disposable equipment stays data-only. Named recurring non-artifact objects with `page_worthiness: dedicated-page` should use `Glossary_Threads/Items/item-[name].md`. Formal supernatural artifacts should use `Glossary_Threads/Artifacts/artifact-[name].md`.

Use `Glossary_Threads/Knowledge_Sources/source-[name].md` instead of an Item page when the row's main importance is that it reveals or transmits knowledge across multiple reader positions. Roselle diary pages, spellbooks, grimoires, notebooks, scriptures, formula records, case files, letters, inscriptions, murals, and similar carriers may begin as character/faction/location data rows, then graduate to Knowledge Source pages when their quote history, access chain, or claim chronology needs independent tracking.

Use `Major Events & Fights` as the character-local participation/index view, not as the canonical event model. The character page should summarize the character's role, outcome, and reader-safe significance, then link to an event page and event part when those exist. Future event pages should own canonical event classification, multi-part structure, participants, locations, causes, enablers, outcomes, injuries/deaths, artifacts/items/abilities used, knowledge revealed, timeline entries, and event-centered Relationship Seeds.

When an event page exists, character `major_events_fights` rows should include both `event` and, when applicable, `event_part`. Use `event_type: fight` or similar values so future generated character pages can produce a dedicated fights view by filtering event participation rows. A single canonical event may appear as a fight for one character, a reveal for another, and a ritual or disaster on the event page itself.

Default character fact ownership:

- Affiliation, employment, team membership, and institutional role belong first in `Affiliations`.
- Pathway, Sequence, advancement, digestion, broad ability state, and limitations belong first in `Pathway & Ability State`.
- Individual powers, skills, training, ritual access, artifact-granted effects, and mundane competencies belong first in `Ability Index` unless they are better modeled as `Prayers & Ritual Access`.
- Object possession, custody, use, access, or investigation state belongs first in `Equipment & Artifacts`.
- Interpersonal, factional, or entity-to-entity ties that are not affiliation, equipment, pathway, or event participation belong first in `Relationships`.
- Character participation in plot events, fights, investigations, rituals, meetings, disasters, or reveals belongs first in `Major Events & Fights`, with event pages becoming the canonical event hubs once they exist.
- Relationship Seeds project graph-worthy edges from these local rows. They do not replace the visible section or data-block row.
- Order Relationship Seeds by the visible/data-block section they project from when possible. For character pages, that usually means affiliation seeds, pathway/sequence seeds, ability seeds, graph-worthy equipment/artifact seeds, relationship seeds, then major-event participation seeds. This ordering is for maintainer readability only; graph generators should not depend on seed position.

### Pathway Article Overlay

Pathway pages should include the pathway overlay once the page has enough verified material to support more than a stub. The overlay is required for active pathway pilot pages and recommended for any future pathway page with reader-safe sequence, formula, access, holder, or ability data.

When official pathway artwork is mapped and promoted into `Artwork/page-assets/pathways/`, the current lightweight convention is to place a compact clickable primary pathway-guide image immediately under the page H1 and before `Metadata`. Omit the image block until a page-ready asset exists, and keep structured artwork references in the data block when useful for extraction. Avoid adding a separate visible `Official Artwork` metadata list to pathway pages unless a later page-level image pattern calls for one.

Pathway pages should place `Associated Tarot Card` after `Pathway Names / Reader Display Timeline` and before `First Appearance / First Meaningful Mention`. When a crop exists, embed a compact card image that links to the full crop file, with a details list covering card name, card number, associated pathway labels, confidence, and notes. If no official crop is mapped for the page's current reader boundary, use a short status note instead of inventing a card association.

Pathway pages should keep a stable internal slug even when the best reader-facing display name changes over time. Use `Pathway Names / Reader Display Timeline` to track reader-display names, implied reader-display associations, aliases, artwork labels, formal names, and sequence-facing names with reveal timing, display-active range, confidence, and notes. Future reader-boundary tooling should select the newest eligible confirmed reader-display name at or before the chosen boundary while preserving aliases and artwork labels for search, cross-linking, and article notes. Implied or associated name rows should be eligible for badges, subtitles, alternate labels, or "implied as of Chapter X" UI hints, but they should not replace the main display title until an exact or otherwise confirmed reader-display row becomes active. Name rows should accumulate rather than overwriting earlier reader-safe names.

The `Known Sequences` section should appear even when only one Sequence is reader-safe. Each known Sequence should receive its own subsection with a normalized structure for reveal timing, confidence, formula or potion details, abilities, practical demonstrations, training or practice requirements, limitations, reader-safe unknowns, and notes. Keep pathway-wide institutional access in `Institutional Access`, broader faction associations in the `Affiliated Factions` table, and character assignments in the separate `Known Holders` table. Unknown higher Sequences should be marked as unknown or omitted; never fill them from later knowledge outside the current reader boundary.

Pathway formula details should preserve ingredients as materials even before a dedicated Material page type exists. Record known ingredients, quantities, preparation steps, source of the formula, and reader-safe uncertainty in the Sequence row. If a formula or ritual produces a usable supernatural output, classify the output conceptually as a future Preparation rather than defaulting to Item; only model it as an Item when it is a named, recurring possession with custody history. Use Knowledge Source pages when a formula record, diary page, spellbook, or inscription is primarily important because it reveals the formula or pathway knowledge over time.

The `Pathway Data Block` is a structured extraction aid, not a separate source of truth. Keep it aligned with the visible pathway sections, relationship seeds, and reader knowledge ledger. If the data block and prose conflict, resolve the conflict in the canonical article content rather than treating the data block as independently authoritative.

Do not duplicate page-level `Subject Visible From` inside type-specific data blocks or Relationship Seeds by default. Treat the metadata field as the authoritative page-level visibility gate. Data blocks and Relationship Seeds should continue to model extractable facts, states, and graph-worthy relationships, while row-level `availability` handles fact-level spoiler timing and knowledge units preserve audit/explanation history.

### First Appearance Style

The `First Appearance / First Meaningful Mention` section should preserve reader-state distinctions instead of compressing different reveal beats into one line.

Use a simple per-medium bullet block only when first appearance, first naming, first meaningful explanation, and first confirmation are effectively the same moment.

When those beats differ, use short subheadings under the medium, such as:

```markdown
#### First Visual / Functional Appearance

#### First Reference

#### First Named Identification

#### First Meaningful Explanation

#### First Formal Confirmation
```

Only include the beats that actually apply. Each beat should record `Volume`, `Chapter`, `Context`, and `Reader knowledge state` for novel entries, or the equivalent season/episode/timestamp fields for adaptation entries.

Do not use later knowledge to rename an early beat as if the reader could already identify it. For example, a reader may first see an unidentified object before later learning its name or function.

### Chronological Development Style

Every meaningful chronological arc should explain why the project cares about it, not merely list events.

Default novel arc format:

```markdown
#### Chapters X-Y: Arc Name

- What the reader learns:
- What changes:
- What remains unknown:
- Why it matters:
```

Default single-chapter format:

```markdown
#### Chapter X: Event Name

- What the reader learns:
- What changes:
- What remains unknown:
- Why it matters:
```

Default Donghua arc format:

```markdown
#### Season X, Episode Y: Event Name

- Timestamp:
- What the viewer learns:
- What changes:
- What remains unknown:
- Why it matters:
```

Use `What happens`, `When the reader learns the connection`, `Attribution boundary`, `Visual/audio evidence`, `Adaptation difference`, `Institutional detail`, or similar extra labels only when the arc genuinely needs that distinction. Do not add extra labels just for decoration.

For very small bridge entries, still include `Why it matters` and make the limited significance explicit.

### Timeline Entry Style

Chronological Development prose is the GitHub-readable article layer. It should remain clear, useful, and reader-boundary safe while the project is still maintained primarily as Markdown.

Type-specific data blocks should add `timeline_entries` when a page has meaningful chronological prose that future reader-position tooling should reveal, hide, sort, or render dynamically. `timeline_entries` are the structured future-website layer for narrative development. Place them in the data block according to the visible page order for that type rather than defaulting to the top of the block. They do not replace the visible prose yet, and the visible prose should not be parsed heuristically as the source of truth.

Every real Chronological Development subsection on an active or retrofitted page must have a `timeline_id` comment and exactly one matching `timeline_entries.id`. Every `timeline_entries.id` should have a matching visible chronology subsection unless the row is explicitly marked as data-only/internal. Blank template placeholders and lightweight stubs may omit or remove timeline IDs until the entry is populated.

Use the same stable `id` in the visible subsection and the data block when practical:

```markdown
#### Chapters X-Y: Arc Name
<!-- timeline_id: subject-arc-name -->

- What the reader learns:
- What changes:
- What remains unknown:
- Why it matters:
```

Use comments only when they help keep prose and data synchronized. Do not clutter tiny stubs with timeline IDs before a page has enough chronology to model. Once a chronology entry is real, the comment is required.

Each structured timeline entry should preserve:

- `id`: stable semantic row key, usually kebab-case and subject-scoped. Avoid numeric sequence IDs such as `timeline-001` because inserted discoveries should not force later ID renumbering.
- `title`: reader-facing arc label.
- `medium`: `novel`, `donghua`, or another controlled medium when supported.
- `from` and optional `to`: source-position range for the arc.
- `visibility.from`: earliest reader/viewer position where this entry can appear.
- `entry_type`: reusable category such as `recruitment`, `investigation`, `ability-demonstration`, `relationship-change`, `status-change`, `source-access`, `battle`, `reveal`, or `setup`.
- `summary`, `reader_learns`, `changes`, `remains_unknown`, and `why_it_matters`: structured mirrors of the visible prose.
- Optional `related_entities`, `related_claims`, `related_relationships`, `related_events`, and `source_refs`.

Visible chronology subsections and `timeline_entries` should both be sorted oldest-to-newest within each medium by reader/viewer disclosure order, not in-world chronology, unless the section explicitly says otherwise. The two orders should match.

When another investigation surfaces a new chronological entry for an existing article, insert the visible subsection and the `timeline_entries` row into the correct reader/viewer order instead of appending them to the end. Re-sequence the order, not the stable semantic IDs. Only rename an existing `timeline_id` when the ID itself was wrong or misleading, and update every matching reference at the same time.

When visible chronology and `timeline_entries` conflict, fix both. Treat visible prose/tables as the human-facing article surface and `timeline_entries` as the structured renderer source for future websites, dashboards, and reader-position filters.

### Knowledge Unit Style

Knowledge units should keep the structured YAML model from the template. They are intentionally more verbose than prose because they will support future spoiler filtering and dashboards.

Every durable knowledge unit should include:

- `claim`
- `truth_status`
- `confidence_level`
- `canon_scope`
- `occurs_at`
- `tags`
- `disclosures`
- `related_investigations`
- `related_boards`
- `last_updated`
- `Reader-State History`
- `Adaptation Analysis`

Add `evidence_basis` and `confidence_history` only when confidence actually evolves in an analytically meaningful way. Do not force confidence-history blocks onto simple confirmed facts.

### Article Boundary Style

Each article has its own reader boundary based on completed investigations already incorporated into that article.

Do not downgrade or remove established material from one article merely because another active analysis thread is currently working through an earlier chapter.

New work should normally be additive. Remove or rewrite existing material only when it is incorrect, duplicated in a harmful way, or structurally misleading.

## Controlled Tag Taxonomy

Tags are allowed only from controlled categories.

Use tags to support filtering and later dashboard/report generation. Do not use vague, emotional, or one-off tags such as `interesting`, `important`, `really-important`, or joke labels.

Use lowercase kebab-case tags.

Use the same casing split for structured glossary metadata: YAML/data field names use snake_case, while tag-like or enum-like values use lowercase kebab-case. Examples: `reader_boundary`, `relationship_type`, and `possession_status` are field names; `current-at-boundary`, `strong-evidence`, `authorized-access`, `member-of`, and `confirmed-artwork` are controlled or taxonomy-style values.

### Volume Tags

```text
volume-1
volume-2
volume-3
volume-4
volume-5
volume-6
volume-7
volume-8
side-stories
```

### Location Tags

```text
tingen
backlund
bayam
feysac
intis
forsaken-land-of-the-gods
spirit-world
gray-fog
```

### Analysis Tags

```text
chronology
foreshadowing
reader-knowledge
historical-context
identity
acting-method
causality
divination
audiovisual-motif
reveal-order
family-lineage
worldbuilding
theme
```

### Status Tags

```text
resolved
unresolved
active-investigation
needs-epub-verification
verified
working-theory
```

### Divination Method Tags

Use the broad `divination` analysis tag for material substantially involving divination. Add a method tag when the specific technique is known and analytically relevant.

```text
dream-divination
spirit-pendulum-divination
```

Add further divination method tags only when the method is encountered in a source and verified. Do not infer or prepopulate an exhaustive method list.

### Domain Tags

```text
artifact
character
family
faction
item
knowledge-source
location
concept
event
pathway
uniqueness
epoch
mystery
timeline
```

When a needed tag does not fit an existing category, recommend adding it to the taxonomy before using it.

## Cross-Reference Standards

Every glossary thread should include a `Related Threads` section.

Use categories when they clarify the relationship:

```text
Directly Related
Historical Connections
Associated Mysteries
Associated Artifacts
Associated Items
Associated Knowledge Sources
Associated Uniquenesses
Associated Factions
Associated Characters
Associated Pathways
```

Use Markdown links when the target file exists.

Use the target document's human-readable H1 title as the link label for an existing glossary thread. Use a clear human-readable investigation title for investigation links. Do not display a working link as its repository filename.

Examples:

```markdown
[0-08](Glossary_Threads/Artifacts/artifact-0-08.md)
[Beyonder Characteristics](Glossary_Threads/Concepts/concept-beyonder-characteristics.md)
[Church of Evernight Volume 1 Reveal Timeline](Investigations/Factions/faction-church-of-evernight/novel-volume-1-reveal-timeline.md)
```

Mention a nonexistent thread only when its creation is already planned or when the relationship is essential to understanding the current thread. Use a plain filename and do not imply that it is a working link. Avoid seeding speculative references merely because a related thread might exist eventually.

### Bidirectional Navigation Rule

Whenever a glossary page is created, renamed, or newly linked to another existing glossary page, check navigation from both directions.

If Page A links to Page B and Page B already exists, review Page B for whether it should link back to Page A in `Related Threads` or another appropriate visible section.

After navigation changes, perform a relationship/link sweep to confirm that existing relationship endpoints are discoverable through Markdown links.

Do not manually maintain incoming references, backlinks, generated reference indexes, relationship graphs, or visual maps inside source pages. Use repository generators for compiled views, and fix durable issues by updating canonical glossary threads, investigations, Relationship Seeds, or data blocks.

Do not copy generic automation policy into individual glossary articles. Keep global automation and generator rules in this file, tool docs, or visualization docs. Page-local implementation notes belong only when they explain a specific page's modeling, boundary, rendering, or future split behavior.

When page-local implementation notes are needed, prefer a collapsible block so reader-facing article flow stays clean:

```markdown
<details>
<summary>Maintainer Notes</summary>

- Page-specific modeling note:

</details>
```

Generated website or reader-facing renderers should be able to strip or hide maintainer-note blocks by default, while maintainer views may preserve them.

## Pilot Article Boundary Rule

Pilot articles may be created naturally when another investigation repeatedly depends on a subject, but the new pilot article must stay bounded to the current verified reader position.

A pilot article should synthesize only what is already supported by the active investigation boundary and existing verified records. Do not fully investigate the new subject across the whole volume unless the user explicitly chooses that as the next focus.

When a pilot article is created, apply the current glossary template, metadata standards, relationship seeds, knowledge ledger format, related investigations, and index/navigation expectations immediately so the article does not require a later structural retrofit.

## Relationship Tracking Standards

Glossary threads may include a `Relationship Seeds` section when a relationship is important enough that a future character, faction, artifact, or event graph should be able to use it.

Keep relationship seeds lightweight and reader-boundary aware. They are graph projection records, not a second canon database.

### Canonical Modeling Layers

Use these layers consistently across all glossary page types:

1. **Visible article prose and tables** are the human-readable canonical article surface.
2. **Type-specific data blocks** are the structured page-local state model for future generated pages, dashboards, and reader-position filters. They should carry recurring state such as character affiliations, pathway status, artifact or item custody, location functions, event participation, aliases, access rules, and similar data, including claim availability by medium and reader position when the state can change over time.
3. **Reader Knowledge Ledger knowledge units** are the audit and interpretation layer for reader knowledge. Use them to explain why a claim changes, preserve misconception arcs, cite reveal evidence, compare adaptations, and support QA, but do not make future renderers hunt through knowledge units for ordinary page-local state that belongs in the type-specific data block.
4. **Relationship Seeds** are graph projection hints. They say which node-to-node edge should exist in relationship graphs, which relationship type to use, and the earliest reader-safe point where that edge becomes graph-worthy. When possible, a seed should point to the data-block row it projects.

`timeline_entries` inside type-specific data blocks are part of layer 2. They are the structured version of the visible Chronological Development prose, intended for future website rendering, reader-position filtering, dashboard timelines, and QA checks. They should describe narrative development arcs, not replace state rows, relationship seeds, or knowledge units.

When these layers overlap, resolve the content in this order: article prose/tables define the human-facing article; type-specific data blocks define structured page-local state; Reader Knowledge Ledger entries explain reveal/audit history; Relationship Seeds project graph-worthy edges from that structured state.

Do not use Relationship Seeds to duplicate every data-block row. Use seeds only when the edge should be visible in generated relationship graphs. A data block can list many holders, members, aliases, access points, possessions, equipment rows, or related items without each row becoming a seed immediately.

### Possession, Equipment, and Item Rules

Use the local type-specific data block for broad possession, equipment, access, custody, or use state. A character, faction, location, event, or item page may record minor equipment, temporary custody, ordinary access, lost objects, borrowed tools, and unresolved possession claims without making any of those rows graph-visible.

Use these row-level fields when an object might matter later:

- `item_significance`: `minor`, `recurring`, or `major`
- `graph_relevance`: `none`, `local`, or `full`
- `page_worthiness`: `none`, `candidate`, or `dedicated-page`

Interpret them this way:

- `minor` + `graph_relevance: none` + `page_worthiness: none`: data-only equipment, inventory, or one-scene prop. Do not create an Item page and do not add a Relationship Seed.
- `recurring` + `graph_relevance: local` + `page_worthiness: candidate`: keep the row in local data and consider it for maintainer or local-context graphs. Create an Item page only if later analysis makes the object a durable relationship hub.
- `major` + `graph_relevance: full` + `page_worthiness: dedicated-page`: create or target an `item-*` page when the object is not a formal supernatural artifact, and add the appropriate Relationship Seed.

Use `Glossary_Threads/Items/item-[name].md` for named, recurring, graph-worthy non-artifact objects such as durable possessions, tools, badges, keys, weapons, instruments, or access objects. Use `Glossary_Threads/Knowledge_Sources/source-[name].md` when the object's main function is carrying claims, quotes, formulas, interpretations, or reveal chronology. Use `Glossary_Threads/Artifacts/artifact-[name].md` when the object's supernatural artifact identity, Sealed Artifact status, or mystical-object behavior is the analytical center. Keep ordinary disposable equipment data-only even if it briefly matters in a scene.

Possession/custody rows should preserve state changes in `availability` rather than overwriting the row. For example, a row can move from `possession_status: held` to `possession_status: lost-custody` while the Relationship Seed remains one graph edge whose current display is computed at the selected reader boundary.

### Relationship Seed Ownership

Each semantic edge should normally have one canonical Relationship Seed owner. Other pages may mention the same relationship in prose, related-thread lists, type-specific data blocks, or knowledge units without adding duplicate seeds.

Default ownership rules:

- **Source-owned entity relationships**: for relationships such as `member-of`, `civilian-staff-of`, `works-at`, `pathway-status`, `superior`, `subordinate`, `mentor`, `student`, `artifact-user`, `victim-of`, `protects`, `enemy`, `ally`, and similar entity-to-entity state, put the seed on the source entity's page when that page exists.
- **Event-centered relationships**: put `event-participant`, `event-location`, `event-cause`, `event-enabler`, and `event-outcome` seeds on the event page, even when the edge direction points toward or away from the event.
- **Pathway and metaphysics relationships**: put pathway-wide associations such as `associated-tarot-card`, `associated-sequence-0`, `associated-ats`, `associated-sefirot`, `associated-uniqueness`, and `associated-mythical-creature-form` on the pathway or metaphysics page that owns the association. Character-specific `pathway-status` belongs on the character page when the character page exists; pathway pages may keep holder rows in their data block without duplicating every holder as a Relationship Seed.
- **Location-function relationships**: put `public-cover-for`, `operational-base-for`, and similar location-function seeds on the location page when the source is the location. Put `works-at` or `uses-as-operational-refuge` on the person/faction page when the source is the person/faction and that source page exists.
- **Concept relationships**: put `mechanic-of`, `instance-of`, `trains-in`, `requires-practice`, `uses-method`, and `access-route-to` on the source page when the source exists. A concept page may own seeds only when the concept itself is the graph center or the source page does not yet exist.
- **Item and equipment relationships**: put `possesses-item` on the character, faction, location, or other holder page when that entity is the source and the item is the target. Put item-as-source seeds on the item page when the item itself enables, accesses, calls, identifies, unlocks, explains, or otherwise relates to a concept, system, event, user, or function. Do not seed every equipment row; seed only rows whose `graph_relevance` is `full`, or `local` when the graph view is explicitly maintainer/local.
- **Knowledge source relationships**: put source-as-source seeds on the Knowledge Source page when the source reveals, records, describes, contains, misleads about, or transmits a claim, concept, event, formula, entity, or system. Put reader/handler/access edges on the character, faction, location, or event page when that page is the natural source and the relationship is about access, handling, reading, custody, or interpretation at the reader boundary. Do not model a recurring knowledge source as an Item merely because it is physically held.
- **Provisional semantic-hub seeds**: if a graph-worthy source or target page does not exist yet, an existing semantic hub page may temporarily host a seed so QA graphs can show the pending endpoint. The relationship itself must be true to the hub's subject, not merely co-located with evidence on that page. Mark the seed `projection_scope: provisional`, omit `projection_source` until a stable data row exists, and migrate or remove the seed when the natural owner page is created. Examples: a prayers/rituals concept page may temporarily host `item-copper-whistle -> concept-prayers-and-rituals` because the item is an access object for ritual mechanics; an artifact page should not host that edge merely because an adaptation evidence note on the artifact page mentions the whistle.

Exact duplicate seeds across owner pages should be treated as QA findings unless they are explicitly provisional, represent different relationship types, or record a real reader-state/modeling conflict that needs resolution.

### Relationship State History

Use Relationship Seeds for the graph edge, not for the full state history of the claim.

`start` means the earliest reader-safe point where the relationship becomes graph-worthy. It does not necessarily mean the relationship is already confirmed. If a relationship begins as a clue, inference, or strong evidence and is confirmed later, store that confidence progression in the relevant type-specific data-block row's `availability` list. Use knowledge-unit `disclosures` when the claim needs a fuller reveal/audit explanation.

Do not add multiple Relationship Seeds for the same `source + relationship_type + target` merely to represent confidence progression. Prefer one seed plus a data-block state row that records the availability history. If the seed projects a specific row, add `projection_source`. If the seed also depends on a specific knowledge unit, add `claim_id` with the knowledge unit id so future generators can merge graph projection with reader-state history.

For new or retrofitted structured data, prefer `availability` over single `reveal` fields. Every reader-visible data-block row should be able to carry one or more availability entries:

```yaml
availability:
  - medium: novel
    from: { book: lotm-1, volume: 1, chapter: 22 }
    confidence: strong-evidence
    status: strong-evidence-at-boundary
    graph_visibility: full
    notes: Earliest graph-worthy clue or inference.
  - medium: novel
    from: { book: lotm-1, volume: 1, chapter: 45 }
    confidence: confirmed
    status: current-at-boundary
    graph_visibility: full
    notes: Later confirmation at the active reader boundary.
  - medium: donghua
    from: { season: 1, episode: TBD, release_order: TBD }
    confidence: TBD
    status: pending-adaptation-verification
    adaptation_relationship: pending
```

Legacy `reveal` fields may remain on older rows until the page is migrated. Do not mix novel and Donghua timing into one blended field.

Use `graph_visibility` only when a row can project into relationship graphs. It controls whether the relationship renders at that reader position, not whether the underlying true relationship exists in canon:

- `hidden`: render nothing. This is the default before the reader knows the relationship exists.
- `anonymized`: render a generic source, target, or relationship label because the reader can see that an unknown actor/force/relationship exists.
- `partial`: render some real pieces while withholding other pieces, such as showing the source but using a safer relationship label.
- `full`: render the true eligible source, target, and relationship type.

Do not anonymize future knowledge by default. Use `anonymized` or `partial` only when the text has made the unknown actor, force, relationship, or pattern reader-visible. Mystery mechanics such as 0-08 should usually progress through a ladder like `hidden` -> `anonymized` or `partial` -> `full`, with each rung tied to an actual reader-visible clue or reveal.

Optional display override fields inside an availability entry:

```yaml
graph_visibility: anonymized
display_source_label: Unknown Influence
display_target_label: Unknown Figure
display_relationship_type: affects
display_notes: Reader can see the anomalous pattern, but not the true source or mechanism.
```

Recommended optional fields for future-proof seeds:

```yaml
projection_owner: source-page
projection_scope: canonical
projection_source: character_profile.pathway_state[pathway-sleepless]
claim_id: subject-claim-id
default_hidden_source_behavior: hide
default_hidden_target_behavior: hide
```

Use `projection_scope: canonical` for the normal owner seed, `projection_scope: provisional` for temporary hub-owned seeds, and `projection_scope: local-context` only when a duplicate is intentionally kept because the page-local context changes interpretation. Avoid `local-context` unless a QA review would otherwise incorrectly treat the seed as accidental duplication.

Relationship graph renderers should evaluate visibility in this order:

1. Hide the relationship if the source page fails `Subject Visible From`.
2. Hide the relationship if the projected data row or seed is not available at the selected reader position.
3. Hide the relationship if the target page fails `Subject Visible From`, unless the current availability entry explicitly sets `graph_visibility: anonymized` or `graph_visibility: partial` with safe display labels.
4. Render the current availability entry's display labels/type when provided; otherwise render the canonical source, target, and relationship type.

Resolve `projection_source` against the Relationship Seed source page before falling back to any global projection key. Many pages reuse local keys such as `character_profile.affiliations[faction-nighthawks]`; page-local resolution prevents one character, faction, item, or location row from accidentally supplying another page's timing or confidence history.

`projection_source` points to a structured data-block row, not to a human-facing Markdown table. Visible tables may be rewritten, replaced, or generated later; generators should read the type-specific data block and its `availability` list. Use stable row identifiers where possible, usually the row's `target`, `field`, `item`, `function`, or another slug-like key inside the brackets.

If a seed has no stable data-block row yet, leave `projection_source` blank and let QA graphs show seed provenance. Add `projection_source` only after the data row exists and its ownership is clear. Do not point a canonical seed at another page's data row unless the seed is explicitly provisional or local-context and the cross-page dependency is noted.

QA relationship-node graphs should present claim history by source layer:

- The first line is the relationship type, with a duplicate count when multiple source pages currently seed the same `source + relationship_type + target`.
- If a seed has `projection_source` and the projected data row has eligible availability entries, the source line should summarize the data history, such as `character data novel ch22 strong-evidence -> ch45 confirmed`.
- If a seed has no usable `projection_source`, the source line should fall back to seed provenance, such as `faction seed novel ch22 confirmed`.
- Pending adaptation entries with `TBD` timing, `confidence: TBD`, or `adaptation_relationship: pending` should stay in the data block but should not appear in graph labels until they have a real pinned viewer position.
- Do not add duplicate Relationship Seeds merely to make later confirmations appear in graph provenance; add the later state to the projected data row's `availability` ladder.

Use controlled relationship types when possible:

```text
member-of
civilian-staff-of
subordinate-organization
parent-organization
colleague
superior
subordinate
leader-of
mentor
student
enemy
ally
investigates
investigated-by
infiltrates
manipulates
victim-of
protects
affiliated-with
connected-to
uses-as-operational-refuge
public-cover-for
operational-base-for
works-at
artifact-user
artifact-guardian
possesses-item
uses-item
authored-by
read-by
accessed-by
handled-by
translated-by
records-event
contains-formula
describes-concept
reveals-claim
source-of-information
causal-agent
targets
targets-protected-resource
pathway-status
associated-tarot-card
associated-sequence-0
associated-ats
associated-outer-deity
associated-sefirot
associated-uniqueness
associated-mythical-creature-form
possesses-uniqueness
controls-uniqueness
accommodates-uniqueness
has-mythical-creature-form
family
instance-of
regulates-access-to
access-route-to
trains-in
requires-practice
uses-method
mechanic-of
event-participant
event-location
event-cause
event-enabler
event-outcome
```

Use concept relationship types when a concept page is the graph center or when the relationship describes access to, membership in, or practice of a concept:

- `instance-of`: A concrete person, organization, artifact, event, or pathway is an example or holder of the target concept/status at the current reader boundary.
- `regulates-access-to`: A faction, organization, institution, or authority controls, grants, restricts, or supervises access to the target concept/status/resource.
- `access-route-to`: A pathway, formula, institution, event, or method is a route through which the target concept/status/resource can be reached.
- `trains-in`: A person, faction, organization, or institution teaches or supervises practice of the target concept/skill/status.
- `requires-practice`: A concept/status/power requires continued practice, training, or control through the target method/concept.
- `uses-method`: A person, faction, event, pathway, or concept uses the target method/concept in a meaningful reader-safe way.
- `mechanic-of`: A concept, rule, law, process, or substance explains how the target concept/status/system works.

Prefer these over generic `connected-to` when the relationship is concept-specific and reader-safe.

Use pathway metaphysics relationship types when a pathway, character, Uniqueness, deity, tarot card, sefirot, or mythical creature form relationship should be graph-visible:

- `associated-tarot-card`: A pathway or Tarot Club identity is associated with a specific tarot card or planned tarot-card concept entry.
- `associated-sequence-0`: A pathway is associated with a Sequence 0 / true-god endpoint or deity page.
- `associated-ats`: A pathway, deity, or pathway group is associated with an Above the Sequences / Great Old One title-cluster page.
- `associated-outer-deity`: A pathway, deity, concept, artifact, location, or event is meaningfully pressured, corrupted, claimed, or influenced by an Outer Deity / Outer God page.
- `associated-sefirot`: A pathway, ATS title cluster, deity, artifact, or concept is associated with a sefirot page.
- `associated-uniqueness`: A pathway is associated with a specific named or planned `uniqueness-*` page. Use only when the Uniqueness itself is reader-safe enough to name, embody, or track as a distinct subject.
- `associated-mythical-creature-form`: A pathway is associated with a specific mythical creature form tracked on `concept-mythical-creature-forms.md`.
- `possesses-uniqueness`: A character, deity, faction, artifact, or other entity possesses a Uniqueness at the reader boundary.
- `controls-uniqueness`: A character, deity, faction, artifact, or other entity controls or can meaningfully use a Uniqueness without necessarily possessing or accommodating it.
- `accommodates-uniqueness`: A character or deity accommodates a Uniqueness as part of advancement/state.
- `has-mythical-creature-form`: A character or deity has, gains, reveals, loses, or is otherwise tied to a mythical creature form tracked on `concept-mythical-creature-forms.md`.

Use `associated-outer-deity` for external pressure/influence, not as a synonym for Sequence 0 or ATS identity. For example, a pathway cluster can have a native ATS formula and also be pressured by a separate Outer Deity.

Tarot-card relationship seed targets may use lightweight graph node slugs such as `tarot-card-the-star` before the project decides whether each card needs a dedicated glossary page. Keep the shared gallery and tarot-card explanation on `concept-tarot-cards.md` unless a specific card becomes article-worthy on its own.

Use item relationship types when an `item-*` page is graph-visible:

- `possesses-item`: A character, faction, location, or other entity holds, owns, carries, stores, or has custody of a named non-artifact item at the reader boundary.
- `uses-item`: A character, faction, event, or system meaningfully uses a named non-artifact item without the relationship primarily being ownership or custody.

Use `artifact-user` and `artifact-guardian` for formal supernatural artifacts, Sealed Artifacts, or artifact pages. Use `possesses-item` and `uses-item` for named non-artifact item pages. Keep ordinary equipment data-only unless the row's `graph_relevance` and `page_worthiness` justify a Relationship Seed.

Use knowledge-source relationship types when a `source-*` page or source candidate is graph-visible:

- `authored-by`: A knowledge source is authored, created, written, dictated, carved, compiled, or otherwise originated by the target.
- `read-by`: A character, faction, or other entity reads or can directly interpret the target knowledge source.
- `accessed-by`: A character, faction, location, event, or system gives access to, obtains access to, or serves as an access route for the target knowledge source.
- `handled-by`: A character, faction, location, or organization physically handles, stores, curates, files, distributes, or administers access to the target knowledge source without necessarily understanding it.
- `translated-by`: A character, faction, system, or method translates, decodes, interprets, or renders the target knowledge source intelligible.
- `records-event`: A knowledge source records, describes, preserves, or testifies about the target event.
- `contains-formula`: A knowledge source contains, preserves, points to, or transmits the target formula, pathway ingredient set, ritual procedure, or structured method.
- `describes-concept`: A knowledge source describes, explains, hints at, or formalizes the target concept.
- `reveals-claim`: A knowledge source reveals a durable claim tracked in a Reader Knowledge Ledger unit or future normalized claim node.

Use `source-of-information` when a person, faction, source, or page is broadly functioning as the reader's source for a concept but the relationship does not need a narrower knowledge-source type yet.

Use the visible section and type-specific data block for detailed state, uncertainty, reveal notes, holders, aliases, title variants, and display timing. Use Relationship Seeds only for positive graph-worthy edges. Do not seed an edge merely because a data block records `unknown`, `null`, or "no reader-safe relationship known."

Use location relationship types when a location page is the graph center or when a relationship describes what a location functionally does for a faction, person, or event:

- `public-cover-for`: A public location, business, address, or identity conceals or fronts for the target faction, organization, operation, or protected activity.
- `operational-base-for`: A location functions as a recurring command point, workplace, resource point, or mission launch site for the target faction, team, or operation.
- `works-at`: A person is based at, employed at, routinely works at, or performs staff duties through the target location.
- `uses-as-operational-refuge`: A person or faction uses the target location as a safe, public, concealed, or strategically useful refuge/contact point during an operation.

Prefer these over generic `connected-to` when the relationship is location-specific and reader-safe.

Use event relationship types when an event page is the graph center:

- `event-participant`: A person, faction, artifact, or other actor directly participates in the event.
- `event-location`: A location is where the event happens or where a key event phase occurs.
- `event-cause`: A prior condition, decision, or pressure causes the event to become necessary or possible.
- `event-enabler`: A person, faction, artifact, resource, or system enables the event without being the event's primary subject.
- `event-outcome`: The event produces a durable result, status change, relationship, or downstream condition.

Prefer these over generic `connected-to` when the relationship is event-specific and reader-safe.

Event relationship direction should be consistent:

- `event-participant`, `event-enabler`, `event-location`, and `event-cause` should point toward the event.
- `event-outcome` should point outward from the event to the durable result, status change, relationship, or downstream condition.

Use `civilian-staff-of` when a character is confirmed as civilian staff within an organization but is not yet a formal member of the organization's Beyonder team. Use `member-of` only when the broader membership relationship is accurate enough for the current reader boundary, or when a more specific staff/member type is not needed.

Use `leader-of` when a person is confirmed as the captain, commander, head, or operational leader of a faction, organization, or team. Use `superior` and `subordinate` for person-to-person reporting relationships.

Use controlled relationship status values:

```text
active
completed
broken
historical
future-boundary
pending
superseded
```

Relationship `status` values apply only inside `Relationship Seeds`. Do not confuse them with knowledge-unit `truth_status` values in the Reader Knowledge Ledger.

Interpret Relationship Seed `status` values consistently:

- `active`: the relationship is ongoing at the selected or declared reader boundary.
- `completed`: the relationship describes a completed action, event role, reveal, or outcome; the consequences may still matter, but the edge is no longer an ongoing state.
- `historical`: the relationship was true earlier but is not current at the boundary, without implying rupture or failure. Prefer this for ended possession, custody, employment, residence, or access when the ending is ordinary or neutral.
- `broken`: use sparingly for a relationship that is explicitly disrupted, breached, severed, failed, escaped, destroyed, or narratively broken. Do not use `broken` as a generic synonym for "no longer holds."
- `future-boundary`: the relationship is known to maintainers but outside the current reader boundary and should not appear in reader-safe graphs.
- `pending`: the relationship is planned, suspected, or awaiting verification; avoid reader-facing projection unless the graph is explicitly a maintainer QA view.
- `superseded`: a later row or seed replaces this modeling claim with a more accurate relationship, target, status, or confidence.

For custody or possession loss, prefer a data-block row state such as `possession_status: lost-custody`, `custody_status: lost-custody`, `status: historical`, or a later availability entry rather than `status: broken`, unless the story frames the custody relationship itself as breached or broken. A future artifact/location/faction taxonomy pass may introduce narrower custody statuses, but until then keep `broken` reserved for actual rupture semantics.

Use the earliest verified or best-known reader-safe start point for the relationship. If the start point is not yet verified, mark it `TBD` and avoid pretending the chronology is settled.

### Relationship Sweep Rule

Whenever relationships are analyzed, added, renamed, or normalized, review them bidirectionally across all affected existing glossary pages.

Relationship updates should branch through linked articles, not stop at the page currently being edited. If a relationship seed touches an existing page, check whether that page needs a reciprocal link, matching relationship seed, updated `Related Threads`, or taxonomy adjustment.

### Taxonomy Gap Rule

If an accurate relationship exists but no controlled relationship type fits, do not force it into `connected-to` by default.

Recommend or define a narrow new relationship type, update `PROJECT_RULES.md`, then apply it consistently to the affected articles.

### Generator Interpretation Rules

Duplicate exact relationship seeds are QA signals by default. They may be acceptable only when they are marked as provisional, intentionally local-context, or represent a known modeling conflict awaiting cleanup.

Graph generators should de-duplicate exact rendered edges for readability while preserving provenance in QA outputs. They should report meaningful conflicts, such as different relationship types, start points, confidence levels, statuses, projection scopes, or notes that change the interpretation.

Multiple relationship types between the same two nodes are allowed when they represent distinct semantic roles. Do not collapse them merely because the node pair is the same.

Duplicate relationship seeds may differ in notes, source file, or article-local status only when that difference is intentional and marked through `projection_scope` or explained in notes. Otherwise, normalize to one canonical owner seed and keep the other page's local context in prose, type-specific data blocks, related-thread lists, or knowledge units.

Graph generators should preserve provenance for drill-down and avoid treating those differences as hard conflicts unless they change the underlying relationship type, chronology, confidence, or factual meaning.

For global graphs, prefer the most generally applicable non-boundary status. For reader-boundary views, prefer the status valid for the selected article or reader position.

Example:

```yaml
- source: character-klein-moretti
  target: faction-church-of-evernight
  relationship_type: civilian-staff-of
  start:
    medium: novel
    volume: 1
    chapter: TBD
  status: active
  confidence: needs-verification
  notes: Klein joins the Tingen Nighthawks under the Church of Evernight structure.
```

Do not manually maintain generated full graph files. Repository automation extracts Relationship Seeds and structured data from glossary threads into Mermaid diagrams, relationship maps, QA mirrors, dashboards, or generated indexes. Manual Mermaid files are allowed only when explicitly classified as repository-local manual graphs under the visualization workflow.

## Open Questions

Every glossary thread should include an `Open Questions` section.

Use it to capture unanswered questions that may later become investigations.

When an open question is answered:

1. Create or update the relevant investigation record if EPUB evidence was used.
2. Update the relevant board if the conclusion changes durable project knowledge.
3. Update the glossary thread to close, revise, or remove the question.
4. Recommend a matching commit if the change satisfies the commit cadence rules.

---

# Embedded Reader Knowledge Ledger

Each glossary thread contains its own Reader Knowledge Ledger section. The ledger stores spoiler-aware knowledge units about that thread for the novel and its adaptations.

Together, the knowledge units should preserve the meaningful disclosure and audit history for durable claims about the glossary subject. Ordinary current-state facts belong in visible page sections and type-specific data blocks; use knowledge units for reveal timing, confidence changes, misconception arcs, adaptation comparison, and evidence-backed interpretation.

Its purpose is to support questions such as:

- What could a novel reader know by a particular chapter?
- What could a Donghua viewer know by a particular released installment?
- Which revelations occur earlier, later, or differently in an adaptation?
- Which theories or misconceptions were reasonable at a historical reader position?

Store each durable claim as a structured YAML block inside the glossary thread where it most naturally belongs. The surrounding Markdown provides explanation, evidence links, and analysis. Do not manually maintain separate claim files or a duplicate JSON database. A future generator may extract the embedded blocks into JSON, dashboards, or spoiler-filtered views.

Give every knowledge unit a stable lowercase kebab-case `id` that is unique across the project. Prefix it with the thread subject when useful, such as `bakerland-mr-ambassador-identity`.

## Knowledge States

Claims may preserve both correct knowledge and historically appropriate reader beliefs.

Allowed disclosure `knowledge_state` values:

```text
clue
confirmed-fact
expanded-fact
strong-evidence
strong-inference
working-theory
reader-misconception
open-question
```

Use `knowledge_state` for the reader or viewer's confidence/state of understanding at that disclosure point:

- `open-question`: The subject or claim is visible as a question, mystery, or unknown.
- `clue`: A meaningful clue is available, but the reader/viewer cannot yet form a stable theory.
- `working-theory`: A plausible interpretation can be formed from available evidence.
- `strong-inference`: The available evidence strongly supports the claim, but it is not explicitly confirmed.
- `strong-evidence`: The claim has substantial support, often across more than one clue or scene, but still falls short of formal confirmation.
- `confirmed-fact`: The claim is directly confirmed for that medium and reader position.
- `expanded-fact`: A previously known or confirmed fact receives additional scope, context, examples, or implications without becoming a separate new core claim.
- `reader-misconception`: A belief that was reasonable at the time but later proves false or misleading.

Use `truth_status` to distinguish the eventual standing of the claim:

```text
true
false
unresolved
contextual
```

A theory or misconception may remain visible within its valid historical window even after it is disproven. Store `knowledge_state`, `available_from`, `superseded_at`, and `superseded_by` on the relevant medium-specific disclosure entry. This allows the same proposition to have different knowledge states in the novel and Donghua without blending their timelines.

Use `occurs_at` when the underlying event happens at a different point from when the reader can understand or attribute it. `occurs_at` records story chronology; `available_from` controls spoiler eligibility. When an event predates the numbered narrative, use a clear phase label such as `pre-chapter-1` and explain it in `notes`.

## Confidence Revision Model

The project uses a lightweight Bayesian-style confidence model: confidence changes when evidence changes.

Do not assign numeric probabilities unless a future tool has a specific reason to do so. Use controlled qualitative confidence states and preserve the evidence trail that caused each revision.

Allowed claim-level `confidence_level` values:

```text
unknown
very-low
low
working-theory
plausible
strong-inference
strong-evidence
confirmed
mixed
disproven
```

Use the smallest confidence increase supported by the evidence. A new clue should usually move a claim from `unknown` to `working-theory` or `plausible`, not directly to `confirmed`.

Confidence should be revised when:

- New evidence supports a claim.
- New evidence weakens or contradicts a claim.
- A later reveal changes an earlier interpretation.
- A source distinction matters, such as novel evidence versus Donghua visual evidence.
- A claim is split into more precise claims because the original wording was too broad.

Every major claim in a knowledge unit may include:

```yaml
confidence_level:
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
```

Use `evidence_basis` for the current support behind the claim. Use `confidence_history` when the evolution of belief is analytically important, especially for mysteries, foreshadowing, reader misconceptions, and claims that move from theory to confirmation.

Do not force confidence history onto every minor fact. A simple confirmed identity, location, or first mention does not need a full revision trail unless the reader's interpretation changes over time.

When an investigation changes confidence, record the change in the investigation conclusion and update the relevant glossary knowledge unit.

## Canon Scope

Allowed `canon_scope` values:

```text
shared
novel-only
donghua-only
adaptation-variant
unresolved-difference
```

One source of truth does not mean one blended chronology. Novel and Donghua disclosures must remain independently filterable.

## Reader Positions

Novel positions use the global chapter number as the primary sortable boundary and retain volume for readability:

```yaml
medium: novel
book: lotm-1
volume: 2
chapter: 000
```

Donghua positions use a machine-sortable release order plus human-readable installment labels:

```yaml
medium: donghua
season: 1
installment_type: special
episode: special-2
release_order: 14
```

`release_order` determines Donghua spoiler eligibility, including specials or other installments that do not fit ordinary episode numbering.

## Disclosure Types

Allowed `disclosure_type` values:

```text
ability-demonstration
choice
consequence
context-link
expanded-explanation
expansion
explicit-explanation
explicit-identification
first-mention
first-appearance
first-clue
first-meaningful-mention
visual-hint
implicit-clue
inference
strong-inference
speculation
rejection
explicit-reveal
confirmation
external-corroboration
limitation
pathway-confirmation
pathway-inference
possibility
practical-confirmation
practical-demonstration
recontextualization
staffing-snapshot
adaptation-only-reveal
early-reveal
```

Use `disclosure_type` for the kind of disclosure event, not the eventual truth of the claim:

- `first-appearance`: The subject appears before the reader/viewer can name or understand it.
- `first-mention`: The subject is named or mentioned for the first time.
- `first-meaningful-mention`: The first mention that gives useful context beyond a name.
- `first-clue`: The first clue that matters for a later interpretation.
- `visual-hint`: A visual-only or primarily visual hint.
- `implicit-clue`: A clue embedded in context, behavior, structure, or implication.
- `context-link`: A disclosure that connects two facts the reader/viewer already had separately.
- `inference`: A conclusion the reader/viewer can infer from available evidence.
- `strong-inference`: A particularly well-supported inference short of explicit confirmation.
- `speculation`: A possibility considered from incomplete evidence.
- `possibility`: A newly available option, route, or scenario.
- `choice`: A character decision or selection that changes reader-state.
- `explicit-identification`: A person, object, institution, or concept is explicitly identified.
- `explicit-explanation`: A mechanism, rule, or meaning is explained directly.
- `expanded-explanation`: A prior explanation is broadened or made more precise.
- `explicit-reveal`: A major direct reveal.
- `confirmation`: A claim is confirmed after prior clue, theory, or inference.
- `practical-demonstration`: A fact or ability is shown in use.
- `ability-demonstration`: An ability is specifically demonstrated.
- `practical-confirmation`: Operational use confirms a prior claim in practice.
- `pathway-inference`: Available evidence supports a pathway/status inference.
- `pathway-confirmation`: A pathway/status relationship is confirmed.
- `staffing-snapshot`: A roster, deployment, or team-status snapshot reveals relationships or roles.
- `limitation`: A constraint, boundary, or failure mode is revealed.
- `consequence`: A durable result or aftermath becomes visible.
- `external-corroboration`: A separate source, institution, character, or medium corroborates the claim.
- `expansion`: A known claim receives additional examples, scope, or implications.
- `recontextualization`: New evidence changes the meaning of earlier evidence.
- `rejection`: A theory or possible model is rejected.
- `adaptation-only-reveal`: A disclosure occurs only in the adaptation.
- `early-reveal`: An adaptation or medium reveals something earlier than another medium.

Use separate disclosure entries for each medium. Never infer Donghua spoiler safety from novel chronology, or novel spoiler safety from Donghua release order.

Use an optional numeric `sequence` when multiple disclosure or state changes occur at the same chapter, episode, or timestamp. Lower values occur first. This allows a theory to be proposed and rejected within one reader position without leaving it active at the end of that position.

## Adaptation Relationships

Allowed adaptation relationship types:

```text
faithful
revealed-earlier
revealed-later
condensed
expanded
recontextualized
omitted
changed
donghua-original
uncertain
pending
```

Record adaptation differences as relationships, not automatically as errors. A claim may use more than one relationship when needed, such as both `condensed` and `revealed-earlier`.

Use `pending` only when the adaptation comparison has not yet been verified. Once the relevant adaptation evidence is reviewed, replace `pending` with a more specific relationship such as `faithful`, `condensed`, `omitted`, `changed`, or `uncertain`.

## Spoiler Filtering

For a selected reader position, display only disclosures available at or before that medium's boundary.

Combined views must evaluate each selected medium independently and then combine only the permitted results. A disclosure in one medium must never silently advance the selected boundary of another medium.

Filtered renderers must apply page-level eligibility before section-level eligibility. Use the page metadata field `Subject Visible From` as the first-pass machine-readable gate. If the selected reader position is before that value, hide the entire page from reader-facing navigation, search, related-thread lists, graph projections, and direct generated output. Do not show a blank page, title-only placeholder, hidden-card shell, or "spoiler removed" stub unless the user has explicitly opted into spoiler placeholders.

Set `Subject Visible From` to the earliest point where the article subject can be exposed under the page title or slug without spoiling attribution. It can match first appearance for openly named subjects, first named identification for characters/places/artifacts, first completion for event pages whose title contains the outcome, or first formal attribution for pages whose subject appears anonymously earlier.

Do not add a standalone reader-facing `Subject Visibility` section by default. Keep the machine-readable value in metadata. If the gate is non-obvious, such as a title that exposes an event outcome or a subject that appears anonymously before it is named, record the rationale under page-local `Maintainer Notes`.

The eventual glossary page should update from the user's selected novel chapter, Donghua release position, or both. Its reader-facing summary and timeline must be constructed only from eligible knowledge units. Freeform analysis elsewhere in the Markdown file is project working material and must not be assumed spoiler-safe for automatic display.

Filtered renderers should hide optional sections when all section content is filtered out for the selected reader position. A table with zero eligible rows, an optional prose section with no eligible reader-safe content, or an embedded media/detail section whose source fact is not yet eligible should collapse rather than display empty scaffolding. Durable structural sections such as page title, metadata needed by the renderer, and reader-boundary state may remain visible.

Embedded page header images are exempt from spoiler-filter hiding. Header images function as page identity/official artwork anchors and may remain visible at any reader position even when later artwork mapping or detailed image metadata is not otherwise eligible. By default, these embedded header images should link to their full-size page-ready asset. Other in-page images, cards, galleries, and visual evidence sections should follow normal section/content eligibility unless a future rule explicitly marks them as page-header artwork.

Use optional `subject_attribution_from` entries when a generic claim becomes knowable before the reader can connect it to the glossary subject that stores it. `available_from` controls when the claim itself is knowable; `subject_attribution_from` controls when it may appear on that subject's generated page.

Example:

```text
Hidden mastermind may detect investigation:
  available_from: Donghua Episode 8
  subject_attribution_from for 0-08: Donghua Episode 13
```

Never delay `available_from` merely to avoid leaking a later subject attribution.

## Knowledge Unit Workflow

Create an embedded knowledge unit when a durable claim has meaningful spoiler timing, adaptation significance, or historical reader-state value.

When a knowledge unit is created or materially changed:

1. Preserve the disclosure boundary for every represented medium.
2. Link supporting investigations when EPUB evidence was consulted.
3. Link related glossary threads and boards when relevant.
4. Recommend a matching commit when the change satisfies the commit cadence rules.

---

# Canonical Sources

## Novel EPUB

The EPUB:

```text
Lord of Mysteries - Book 1.epub
```

is the canonical source of truth.

Do not use external summaries, wikis, fandom pages, Reddit posts, or memory when verification is required.

Use the EPUB.

### EPUB Sweep Tool

Use `Tools/search_epub.py` for repeatable novel EPUB checks when Python is available. `Tools/Search-Epub.ps1` is the Windows PowerShell fallback and should remain behaviorally compatible. Use `Tools/Test-Python.ps1` as the canonical local Python availability probe when the environment is unknown, then retain the result as session state instead of probing before every command. Exact commands, flags, aliases, examples, switch maps, and parity notes live in `Tools/README.md` and `Tools/TOOLING_REFERENCE.md`.

When a task requires novel EPUB source expansion and this helper is available, use the Python helper as the preferred first EPUB search path because it is faster and can grow into reusable search/index functionality. Use the PowerShell helper when Python is unavailable. This applies to graph-building coverage sweeps as well as article and investigation verification. If both helpers are missing or unusable, use another structured EPUB search method and report the degraded path.

The helpers search the full Book 1 EPUB by actual chapter number rather than Volume 1 filenames. They can narrow by chapter range, volume, entry type, and entry filename pattern. Use side-story, appendix, artwork, front-matter, other, or all-entry filters when the evidence may live outside the main chapter stream.

The standard EPUB evidence workflow is:

1. Run a survey count across the bounded chapter range.
2. Inspect candidate hits in chapter order.
3. Expand local context around relevant hits.
4. Add newly discovered terms, names, aliases, locations, abilities, motifs, and paraphrases to the search vocabulary.
5. Repeat the survey/context loop until the active arc is covered.
6. Record chapter references and paraphrased evidence in the investigation file.
7. Do not paste long EPUB passages into tracked records.

When choosing a canonical page slug or primary article name from competing names, run a term-arbitration sweep rather than relying on memory or raw search totals. Count all candidate terms across the full relevant range, split them by term and volume, then inspect context around hits in chapter order. Classify each usage by function: primary subject name, alias/title, sequence name, ordinary-language usage, person/role label, or artwork/formal label. Prefer the slug that best matches repeated in-text subject usage, and preserve alternate names in the article alias table and artwork-map notes. Raw counts can mislead when one term is also an occupation, epithet, or individual label.

## Donghua Subtitles

Local `.ass` subtitle files are the canonical source for the dialogue and translated on-screen text contained in that subtitle release.

Record subtitle provenance and coverage. Translation wording may differ between official or fan releases, so do not silently combine subtitle editions.

Subtitle evidence can verify:

- Dialogue
- Narration represented in the subtitle track
- Translated signs or on-screen text represented in the subtitle track
- Episode-relative timestamps

Subtitle evidence alone cannot verify:

- Silent visual clues
- Framing or camera emphasis
- Character expressions
- Object placement or appearance not described in text
- Animation-only chronology that requires watching the scene

Label evidence as `Subtitle Evidence`, `Visual Evidence`, or `Episode Evidence` when the distinction matters. `Episode Evidence` requires support from both the audiovisual episode and its dialogue or text.

Do not commit subtitle source files or reproduce their dialogue in project records. Use episode numbers, timestamps, and paraphrased evidence summaries.

When subtitle evidence is consulted for a formal conclusion, create or update the relevant investigation record just as with EPUB evidence.

---

# Two Operating Modes

## Mode 1: Discussion Mode (Default)

This is the default mode for open-ended lore discussion, memory reconstruction, thematic analysis, and exploratory conversation.

Start here unless verification, tooling work, QA, graph generation, article editing, or another repository-maintenance task is required.

### Goal

Reconstruct understanding from memory.

### Preferred Workflow

1. Ask questions.
2. Let the user reconstruct events.
3. Compare memories.
4. Identify gaps.
5. Build working theories.

Do **not** immediately search the EPUB for ordinary discussion.

The user specifically enjoys discovering forgotten connections through discussion.

The EPUB is an archive, not the first step.

Use it when verification is needed, when the user asks for source-backed work, or when a repository-maintenance task depends on pinned evidence.

---

## Mode 2: Investigation Mode

Switch to Investigation Mode when:

- Chronology is unclear.
- Motivations are disputed.
- Reader knowledge timing matters.
- Character relationships are uncertain.
- Historical connections need verification.
- A board update requires confidence.
- The user explicitly requests verification.
- The task is tooling, QA, graph generation, article editing, or another repository-maintenance operation that depends on source-backed evidence.

### Investigation Workflow

1. Define the question.
2. Identify the endpoint event.
3. Bound the investigation window.
4. Search the relevant source.
5. Collect evidence.
6. Draw conclusions.

Never reverse steps 5 and 6.

**Evidence first. Conclusion second.**

### Investigation Methodology

**Search broadly. Validate locally. Record evidence, not isolated keywords.**

An investigation is an evidence-acquisition process, not a single keyword lookup.

1. Reconstruct the subject from memory.
2. Form working hypotheses and identify likely related concepts.
3. Define the source, bounded scope, and endpoint event or reveal.
4. Build a search vocabulary from names, aliases, effects, events, motifs, associated characters, locations, and likely paraphrases.
5. Sweep the bounded source chronologically as a survey pass.
6. Treat search matches and audiovisual observations as candidate evidence, not conclusions.
7. Expand the surrounding textual or audiovisual context for each candidate.
8. Use the survey to identify natural analysis arcs, such as reveal clusters, investigation sequences, action incidents, bridge chapters, or aftermath sections.
9. Order those arcs by reader/viewer sequence and explicitly note filler or bridge gaps between them.
10. Present the ordered arc list to the user before turning the survey into a completed article or broad final synthesis.
11. Work through each arc collaboratively with the user in sequence, adding or revising evidence as the discussion clarifies reader knowledge, emphasis, adaptation differences, and interpretation.
12. Record verified evidence in chronological order as each arc is accepted.
13. Repeat the search-and-context loop until the active arc is complete.
14. Perform a final completeness sweep using terminology and connections discovered during the investigation only after the arcs have been reviewed.
15. Update the investigation record, glossary timeline, knowledge units, relationship seeds, and any warranted board or index references.

The relevant source may be the EPUB, Donghua subtitles, the audiovisual episode, or a combination of them. Match the evidence label and confidence level to what was actually examined.

Search vocabulary should evolve during the investigation. Finding one relevant passage or scene may reveal new names, effects, phrases, relationships, or motifs that require another chronological sweep.

### Survey Pass vs. Collaborative Analysis

A full chronological source sweep is allowed to find the shape of the subject, but it is not the same thing as completing the analysis.

For glossary or board work where the user is actively collaborating:

1. Use the broad sweep to propose natural arcs.
2. Include bridge or filler gaps when chapters connect two larger arcs without forming a major reveal on their own.
3. Move through those arcs with the user in order.
4. Do not condense a full-volume survey into finished glossary prose, knowledge units, relationship seeds, or board conclusions without user review.
5. Keep later survey findings as provisional evidence until the project reaches that arc collaboratively.

This preserves the value of evidence acquisition while preventing the analysis from skipping the user's memory, questions, and interpretation.

---

# Two Parallel Boards

## Board 1

### `01_LoTM_Main_Reread_Board.md`

Tracks:

- Volume progression
- Character arcs
- Themes
- Worldbuilding
- Important reveals
- Chronology
- Reader perspective

This board follows the reread progression.

---

## Board 2

### `02_LoTM_Ancient_History_Family_Board.md`

Tracks:

- Antigonus
- Medici
- Tudor
- Trunsoest
- Salinger
- Abraham
- Amon
- Adam
- Rose School of Thought
- Fourth Epoch
- Third Epoch
- Historical factions

This board must remain chronological.

Record:

- When the reader learned information.
- What chapter/volume revealed it.
- What the reader still did not know.

Never contaminate this board with future reveals.

---

# Investigation Standards

If answering a question from EPUB evidence:

## Evidence

### Chapter X

- What happened
- Why it matters

### Chapter Y

- What happened
- Why it matters

## Conclusion

Supported conclusion.

If verification has not occurred, explicitly state:

> Investigation incomplete. EPUB not yet verified.

Do not guess.

### Records

- Put investigations in the `Investigations` folder.
- Glossary-linked investigations should mirror the `Glossary_Threads` type structure and use one stable subject folder per glossary thread.
- Every glossary-linked investigation must include a `Related Glossary Thread` section near the top with a working backlink labeled by the glossary thread's human-readable H1 title.
- Use date-based filenames only for project-wide, board-level, or one-off investigations whose identity is genuinely the research event rather than a glossary subject.

Glossary-linked path format:

```text
Investigations/[Type]/[thread-filename-without-extension]/[medium]-[scope].md
```

Examples:

```text
Investigations/Artifacts/artifact-0-08/novel-volume-1-reveal-timeline.md
Investigations/Artifacts/artifact-0-08/donghua-season-1-reveal-timeline.md
Investigations/Factions/faction-church-of-evernight/novel-volume-1-reveal-timeline.md
Investigations/Factions/faction-church-of-evernight/donghua-season-1-reveal-timeline.md
Investigations/Project/2026-07-01_board-methodology.md
```

### Investigation Granularity

Group investigations by subject and bounded analytical scope, not by individual lookup or calendar day.

- Use one focused file for a genuinely standalone question.
- For glossary reconstruction, use one living investigation per subject, medium, and bounded arc, such as one novel volume or one Donghua season.
- Use `reveal-timeline` as the default scope name for glossary investigations because their normal purpose is reconstructing the subject's reader-safe disclosure chronology.
- Append additional checks to the existing file when the subject, medium, and scope remain the same.
- Create a new file when the medium or bounded arc changes, or when a separate dispute would make the existing record difficult to understand.
- Do not include investigation dates in glossary-linked filenames. The durable identity is the subject, source, and scope, not the day the research happened.
- Mark a living investigation `In Progress` until its bounded timeline is complete; completed checks inside it should still be clearly labeled as verified.

---

# Board Maintenance Rules

The board files are living project artifacts.

When a meaningful conclusion is reached:

1. Determine whether Board 1 should be updated.
2. Determine whether Board 2 should be updated.
3. Preserve chronology.
4. Preserve reader knowledge state.
5. Avoid future contamination.

Chronology corrections are important.

Causality corrections are important.

Small observations that do not affect understanding do not require board updates.

---

# Index Maintenance

`INDEX.md` is the GitHub navigation hub for project files.

When any of the following are created, recommend updating `INDEX.md` as part of the same change:

- A glossary thread
- An investigation record
- A board

Index updates should be committed with the related project knowledge update when they are part of the same confirmed change.

---

# Commit Cadence

Commit only when project knowledge changes.

Do not commit for:

- Discussion
- Hypotheses

Commit after:

- Board updates
- Completed investigations
- Chronology corrections
- Durable conclusions

---

# Board and Commit Review Habit

After each substantive exchange, check whether the discussion produced project knowledge that should be preserved.

If preservation may be appropriate:

- Recommend any board updates.
- Recommend any investigation record updates.
- Recommend the matching commit, if the update would satisfy the commit cadence rules.

Do not modify files or create commits without user confirmation.

---

# Current Methodology Reminder

Prefer:

```text
Memory reconstruction
↓
Working theory
↓
EPUB verification (if needed)
↓
Board update
```

Not:

```text
EPUB search
↓
Immediate answer
```

The goal is understanding and investigation, not simply retrieving facts.
