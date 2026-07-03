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

The project uses the following files:

```text
Source/
├── README.md
└── Lord of Mysteries - Book 1.epub

Boards/
├── 01_LoTM_Main_Reread_Board.md
└── 02_LoTM_Ancient_History_Family_Board.md

Investigations/
├── TEMPLATE.md
├── Artifacts/
│   └── artifact-[name]/
├── Characters/
├── Factions/
├── Concepts/
└── Project/

Glossary_Threads/
├── TEMPLATE.md
├── Artifacts/
├── Characters/
├── Families/
├── Factions/
├── Locations/
├── Concepts/
├── Events/
├── Pathways/
├── Epochs/
├── Mysteries/
└── Timelines/

INDEX.md
CURRENT_STATE.md
PROJECT_RULES.md
00_READ_FIRST_AI_AGENT_BOOTSTRAP.md
README-AI-Agent-Specification.md
MAINTAINER_CONTEXT.md
ASSISTANT_CONTEXT.md (deprecated redirect)
README.md
```

These files are the project's working memory.

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

For Volume 1 progress percentages, use the current verified chapter boundary divided by 213 total chapters. Treat the percentage as a chapter-boundary indicator, not a guarantee of article quality, cross-link completeness, or adaptation completeness.

When a thread spans more than one medium, track novel and adaptation progress separately where practical. Do not let one medium's progress silently advance another.

Do not create all pending threads just because they appear in `CURRENT_STATE.md`. Pending items are a backlog, not an instruction to scaffold every file.

## Artifact Responsibilities

Use each project artifact for a distinct purpose:

- `Boards`: Volume-level state, major themes, broad conclusions, current research direction, and links to detailed records.
- `Glossary_Threads`: Subject-specific information, complete reveal timelines, reader-state filtering data, and adaptation comparisons.
- `Investigations`: Evidence, verification history, and supported conclusions for questions that required consulting the EPUB.
- `Visualization`: Generated visualization artifacts, such as Mermaid graphs, rendered graph images, and future graph data exports.

Do not duplicate granular reveal chronology across boards and glossary threads. Keep the filterable detail in the glossary thread and summarize only the durable volume-level meaning on the appropriate board.

Boards are analyst-facing overview documents, not the canonical source for automatic spoiler filtering. A future reader-facing system may gate a board by its volume boundary, but glossary knowledge units remain the source for position-specific filtering.

---

# Visualization

Visualization files are generated outputs.

The graph source of truth remains:

- Glossary thread metadata
- Reader Knowledge Ledgers
- Relationship Seeds
- Controlled relationship taxonomy in this file

Generated visualization outputs may include:

- Mermaid `.mmd` files
- Rendered SVG or PNG files
- JSON graph data
- Future frontend graph views

Do not treat generated graph files as canonical project knowledge.

Do not manually edit generated graph outputs except for debugging or temporary inspection. Fix durable graph problems by updating the relevant glossary thread, investigation record, Relationship Seed, or controlled taxonomy, then regenerate the graph.

For durable canonical graph corrections, if a graph exposes missing or incorrect data:

1. Fix the glossary or investigation record.
2. Update Relationship Seeds when the relationship model changes.
3. Regenerate the graph output.

For graph-only maintainer work, do not silently update glossary threads, investigations, boards, current state, index, or Relationship Seeds while producing the graph. Graph generation may read project records and allowed local sources, include clearly marked graph-local evidence, and report candidate project-data updates. Ask for maintainer confirmation before editing canonical project records.

Use the shared [Graph Authoring Standard](Visualization/graph-authoring-standard.md) for graph construction. It defines canonical versus graph-local evidence, source expansion, pathway/sequence coverage, maintainer confirmation, and output reporting.

For dense Mermaid graphs, prefer semantic relationship nodes over long edge labels. A generated relationship node may hold the relationship type, timing, status, and confidence, with simple arrows from source to relationship node to target. These relationship nodes are presentation artifacts only. They are not glossary nodes, do not create new canonical entities, and must be regenerated from Relationship Seeds.

Use direct edge labels only when the graph remains readable. If rendered labels overlap, collide, or become hard to follow, update the visualization generator or graph projection rather than hand-editing the generated Mermaid.

## Visualization Refresh Gate

Before committing a change, check whether graph inputs changed.

Graph regeneration is recommended when any of these change:

- a glossary page is created, deleted, renamed, or moved;
- `Relationship Seeds` are added, removed, or changed;
- a relationship type, relationship status, relationship confidence, source node, or target node changes;
- a node type changes, such as `concept` to `faction`;
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

Use this canonical refresh command from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\render-graphs.ps1
```

Use pure render mode for manually authored or temporary Mermaid files that should not trigger graph regeneration:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\render-mermaid.ps1 -InputPath Visualization\graphs\example.mmd
```

Pure render mode may write rendered SVG or PNG outputs, but it must not regenerate Mermaid graph files from Relationship Seeds, update the visualization snapshot, or update the refresh tracker.

Before graph rendering work, confirm that the expected visualization tooling is present: `Visualization/render-graphs.ps1`, `Visualization/render-mermaid.ps1`, `Visualization/config/puppeteer-config.json`, and `Visualization/config/render-settings.json`. If any are missing, report the render path as degraded before using a fallback.

Visualization renderers should scale viewport dimensions for large graphs using the shared render settings. Do not assume one fixed Mermaid render size works for every graph. If a large graph renders cramped, clipped, or unreadably small, adjust render-size settings or use the shared auto-size helper rather than hand-editing graph content solely to fit the canvas.

Wide fan-out is a known Mermaid layout pattern. When one hub node connects to many targets or many sources converge on one target, renderers should use fan-out-aware sizing and graph authors should expect the graph to need more horizontal room. If auto-sizing alone does not make the graph readable, improve the graph projection by adding meaningful intermediate grouping nodes, relationship nodes, local reference/proxy nodes, or split views. Do not treat wide fan-out as a data error by itself.

Ordered graph content should preserve order visually. When graph nodes represent a sequence, timeline, phase list, rank ladder, chapter/episode progression, investigation chain, or other ordered series, prefer child-to-child chains over direct sibling fan-out from one parent. Flat fan-out is appropriate for unordered peer sets; ordered-series fan-out should be fixed in the graph projection or generator.

Dense knowledge graphs should use a connected semantic spine and styled nodes by default. Prefer ordinary styled group nodes over many Mermaid `subgraph` clusters. Use `subgraph` only for a few broad regions, intentional cluster views, or user-requested cluster boxes. Dense maps with many disconnected cluster islands should be fixed in the graph projection or generator before rendering.

Content graphs should be grouped by subject semantics, not by evidence source layer, canonicalization status, validation status, or coverage status unless the graph is explicitly an evidence audit. Evidence and canonicalization status should usually appear through styling, labels, legends, note branches, or output reports.

Dense graph styling should follow a visual role grammar rather than one-off decorative coloring. Use fill color to distinguish semantic roles, border style to distinguish uncertainty or boundary status, text prefixes to preserve accessible meaning, and topology to show structure. The exact palette may evolve, but role-to-style mapping should remain consistent inside a graph. This applies across graph domains, including pathway maps, artifact maps, influence maps, faction maps, event maps, location maps, and character relationship maps.

Repeated entity nodes in ordered graphs must show their progression explicitly, preferably with label markers, compact badges, or advancement/state nodes. Use direct progression edges only when the edge itself is meaningful and should affect graph topology. Do not rely on layout position alone to show that two appearances of the same person, artifact, faction, or concept are sequential states.

Uncertain, inferred, graph-local, or provisional nodes should keep the same local placement as confirmed nodes of the same semantic type. For example, a suspected holder is still holder-like for layout purposes; uncertainty belongs in the label and styling, not in a distant note cluster.

For ladder-style graphs, keep the ordered sequence, phase, rank, or step chain as the primary spine. Attach holders, artifacts, controllers, notes, and evidence as leaves or local buckets rather than interrupting the spine.

When reconciling against an older graph or user-provided reference graph, do not silently drop candidates. Include them, downgrade them, move them to a more accurate role, or report why they were excluded.

Styled Mermaid graphs must pass class coverage validation before rendering. If a graph uses `classDef` or `class` statements, every declared or edge-used node should have an explicit class assignment. Fix missing classes, class references to nonexistent nodes, undefined classes, and semantic class mismatches in the Mermaid source or generator before publishing a render.

Sectioned Mermaid graphs should preserve layout islands. If a node has canonical placement in one section, do not link a different summary, reconstruction, or boundary-note section directly to that same node when it will pull edges across the whole graph. Create a local reference/proxy node inside the secondary section instead, and label it as a reference to the canonical node or pathway/sequence.

Avoid duplicate visible labels across different node IDs unless one of the nodes is explicitly labeled as a reference/proxy. Reference/proxy-like node IDs should also say `reference`, `proxy`, `reconstruction`, `summary`, or `see ...` in the rendered node label.

Legend, coverage, validation, output-report, and explanatory nodes should live in a separate note or appendix branch so they do not distort the layout of primary content nodes.

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

Future graph tooling should support dynamic generation, timeline filtering, reader-state filtering, and multiple graph views without making the rendered graph the source of truth.

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
location-[name].md
concept-[name].md
event-[name].md
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
concept-gray-fog.md
event-great-smog.md
pathway-seer.md
epoch-fourth-epoch.md
mystery-mr-door.md
timeline-ian-zreal-chain.md
```

If a thread fits multiple categories, choose the category that best matches the analytical purpose of the file.

## Folder Organization

Store glossary threads in plural, type-specific subfolders:

```text
Glossary_Threads/Artifacts/
Glossary_Threads/Characters/
Glossary_Threads/Families/
Glossary_Threads/Factions/
Glossary_Threads/Locations/
Glossary_Threads/Concepts/
Glossary_Threads/Events/
Glossary_Threads/Pathways/
Glossary_Threads/Epochs/
Glossary_Threads/Mysteries/
Glossary_Threads/Timelines/
```

Retain the entity-type filename prefix inside the matching folder. For example:

```text
Glossary_Threads/Characters/character-amon.md
Glossary_Threads/Artifacts/artifact-0-08.md
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
Current Analysis Status:
Confidence Level:
Spoiler Boundary:
Reader Knowledge Boundary:
Tags:
Last Updated:
```

Use these fields consistently:

- `Type`: Entity type, such as Artifact, Character, Family, Faction, Location, Concept, Event, Pathway, Epoch, Mystery, or Timeline.
- `Status`: Thread lifecycle, such as Stub, Active, Dormant, Resolved, or Superseded.
- `First Mention Volume`: Earliest known volume where the thread meaningfully appears.
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

Use the same top-level section order as `Glossary_Threads/TEMPLATE.md` unless there is a strong reason to deviate:

1. Metadata
2. Purpose
3. Spoiler Boundary
4. Reader Knowledge Boundary
5. First Appearance / First Meaningful Mention
6. Chronological Development
7. Open Questions
8. Related Threads
9. Relationship Seeds
10. Evidence Index
11. Reader Knowledge Ledger
12. Future Automation Notes
13. Notes

### Type-Specific Glossary Overlays

The universal glossary template defines the shared article contract. Type-specific folders may also define overlay templates when a glossary type has recurring fields that should be easy to extract for graphs, dashboards, or reader-state filters.

Use a type-specific overlay only when it adds predictable structure that the universal template cannot express cleanly. The overlay should preserve the shared metadata, relationship seeds, evidence index, reader knowledge ledger, future automation notes, and notes sections.

Place type-specific extraction sections after `Reader Knowledge Boundary` and before `First Appearance / First Meaningful Mention`. This keeps high-value structured facts close to the article boundary while preserving chronological development as the main prose record.

Current type-specific overlays:

- `Glossary_Threads/Pathways/TEMPLATE.md`: pathway pages should expose `Pathway Snapshot`, `Known Sequences`, `Institutional Access`, `Affiliated Factions`, `Known Holders`, and `Pathway Data Block` sections.

### Pathway Article Overlay

Pathway pages should include the pathway overlay once the page has enough verified material to support more than a stub. The overlay is required for active pathway pilot pages and recommended for any future pathway page with reader-safe sequence, formula, access, holder, or ability data.

The `Known Sequences` section should appear even when only one Sequence is reader-safe. Each known Sequence should receive its own subsection with a normalized structure for reveal timing, confidence, formula or potion details, abilities, practical demonstrations, training or practice requirements, limitations, reader-safe unknowns, and notes. Keep pathway-wide institutional access in `Institutional Access`, broader faction associations in the `Affiliated Factions` table, and character assignments in the separate `Known Holders` table. Unknown higher Sequences should be marked as unknown or omitted; never fill them from later knowledge outside the current reader boundary.

The `Pathway Data Block` is a structured extraction aid, not a separate source of truth. Keep it aligned with the visible pathway sections, relationship seeds, and reader knowledge ledger. If the data block and prose conflict, resolve the conflict in the canonical article content rather than treating the data block as independently authoritative.

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
location
concept
event
pathway
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

Do not manually maintain incoming references or backlinks yet. Backlinks, generated reference indexes, relationship graphs, and visual maps should be left for future automation once the repository is larger.

## Pilot Article Boundary Rule

Pilot articles may be created naturally when another investigation repeatedly depends on a subject, but the new pilot article must stay bounded to the current verified reader position.

A pilot article should synthesize only what is already supported by the active investigation boundary and existing verified records. Do not fully investigate the new subject across the whole volume unless the user explicitly chooses that as the next focus.

When a pilot article is created, apply the current glossary template, metadata standards, relationship seeds, knowledge ledger format, related investigations, and index/navigation expectations immediately so the article does not require a later structural retrofit.

## Relationship Tracking Standards

Glossary threads may include a `Relationship Seeds` section when a relationship is important enough that a future character, faction, artifact, or event graph should be able to use it.

Keep relationship seeds lightweight and reader-boundary aware. They are not a separate database yet; they are structured notes for future extraction.

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
source-of-information
causal-agent
targets
targets-protected-resource
pathway-status
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

Use the earliest verified or best-known reader-safe start point for the relationship. If the start point is not yet verified, mark it `TBD` and avoid pretending the chronology is settled.

### Relationship Sweep Rule

Whenever relationships are analyzed, added, renamed, or normalized, review them bidirectionally across all affected existing glossary pages.

Relationship updates should branch through linked articles, not stop at the page currently being edited. If a relationship seed touches an existing page, check whether that page needs a reciprocal link, matching relationship seed, updated `Related Threads`, or taxonomy adjustment.

### Taxonomy Gap Rule

If an accurate relationship exists but no controlled relationship type fits, do not force it into `connected-to` by default.

Recommend or define a narrow new relationship type, update `PROJECT_RULES.md`, then apply it consistently to the affected articles.

### Generator Interpretation Rules

Duplicate exact relationship seeds are acceptable when they provide article-local context or bidirectional coverage across existing glossary pages.

Graph generators should de-duplicate exact rendered edges and report only meaningful conflicts, such as different relationship types, start points, confidence levels, statuses, or notes that change the interpretation.

Multiple relationship types between the same two nodes are allowed when they represent distinct semantic roles. Do not collapse them merely because the node pair is the same.

Duplicate relationship seeds may differ in notes, source file, or article-local status because each glossary page frames the same edge from its own reader boundary and analytical purpose.

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

Do not manually maintain full graph files yet. Future automation may extract relationship seeds from glossary threads into Mermaid diagrams, relationship maps, dashboards, or generated indexes.

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

Together, the knowledge units must form a complete disclosure timeline for the glossary subject. Record every meaningful reveal point, including multiple disclosure entries from the same medium when a subject progresses from mention, to clue, to inference, to explicit reveal or confirmation.

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

The eventual glossary page should update from the user's selected novel chapter, Donghua release position, or both. Its reader-facing summary and timeline must be constructed only from eligible knowledge units. Freeform analysis elsewhere in the Markdown file is project working material and must not be assumed spoiler-safe for automatic display.

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

Use `Tools/Search-Epub.ps1` for repeatable novel EPUB checks.

When a task requires novel EPUB source expansion and this helper is available, use it as the preferred first EPUB search path. This applies to graph-building coverage sweeps as well as article and investigation verification. If the helper is missing or unusable, use another structured EPUB search method and report the degraded path.

The standard EPUB evidence workflow is:

1. Run a survey count across the bounded chapter range.
2. Inspect candidate hits in chapter order.
3. Expand local context around relevant hits.
4. Add newly discovered terms, names, aliases, locations, abilities, motifs, and paraphrases to the search vocabulary.
5. Repeat the survey/context loop until the active arc is covered.
6. Record chapter references and paraphrased evidence in the investigation file.
7. Do not paste long EPUB passages into tracked records.

Example survey count:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 10 -EndChapter 47 -Pattern "Dunn|Captain|Nighthawk|Nightmare|Sleepless" -CountsOnly
```

Example context expansion:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 12 -EndChapter 13 -Pattern "Dunn|Nighthawk" -ContextLines 2 -MaxHitsPerChapter 8
```

By default, `-Pattern` treats `|` as a separator between literal terms. Use `-RegexPattern` only when a regular expression is needed.

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

This is the default mode.

Start here unless verification is required.

### Goal

Reconstruct understanding from memory.

### Preferred Workflow

1. Ask questions.
2. Let the user reconstruct events.
3. Compare memories.
4. Identify gaps.
5. Build working theories.

Do **not** immediately search the EPUB.

The user specifically enjoys discovering forgotten connections through discussion.

The EPUB is an archive, not the first step.

Use it only when needed.

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
