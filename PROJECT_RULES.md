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
└── (Investigation records created over time)

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
ASSISTANT_CONTEXT.md
README.md
```

These files are the project's working memory.

When conclusions are reached:

- Update the appropriate board(s).
- Create investigation records when appropriate.
- Preserve chronology.
- Preserve reader knowledge state.

## Artifact Responsibilities

Use each project artifact for a distinct purpose:

- `Boards`: Volume-level state, major themes, broad conclusions, current research direction, and links to detailed records.
- `Glossary_Threads`: Subject-specific information, complete reveal timelines, reader-state filtering data, and adaptation comparisons.
- `Investigations`: Evidence, verification history, and supported conclusions for questions that required consulting the EPUB.

Do not duplicate granular reveal chronology across boards and glossary threads. Keep the filterable detail in the glossary thread and summarize only the durable volume-level meaning on the appropriate board.

Boards are analyst-facing overview documents, not the canonical source for automatic spoiler filtering. A future reader-facing system may gate a board by its volume boundary, but glossary knowledge units remain the source for position-specific filtering.

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

Mention a nonexistent thread only when its creation is already planned or when the relationship is essential to understanding the current thread. Use a plain filename and do not imply that it is a working link. Avoid seeding speculative references merely because a related thread might exist eventually.

Do not manually maintain incoming references or backlinks yet. Backlinks, generated reference indexes, relationship graphs, and visual maps should be left for future automation once the repository is larger.

## Relationship Tracking Standards

Glossary threads may include a `Relationship Seeds` section when a relationship is important enough that a future character, faction, artifact, or event graph should be able to use it.

Keep relationship seeds lightweight and reader-boundary aware. They are not a separate database yet; they are structured notes for future extraction.

Use controlled relationship types when possible:

```text
member-of
subordinate-organization
parent-organization
colleague
superior
subordinate
mentor
student
enemy
ally
investigates
investigated-by
manipulates
victim-of
protects
affiliated-with
artifact-user
artifact-guardian
source-of-information
family
```

Use the earliest verified or best-known reader-safe start point for the relationship. If the start point is not yet verified, mark it `TBD` and avoid pretending the chronology is settled.

Example:

```yaml
- source: character-klein-moretti
  target: faction-church-of-evernight
  relationship_type: member-of
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
confirmed-fact
strong-inference
working-theory
reader-misconception
open-question
```

Use `truth_status` to distinguish the eventual standing of the claim:

```text
true
false
unresolved
contextual
```

A theory or misconception may remain visible within its valid historical window even after it is disproven. Store `knowledge_state`, `available_from`, `superseded_at`, and `superseded_by` on the relevant medium-specific disclosure entry. This allows the same proposition to have different knowledge states in the novel and Donghua without blending their timelines.

Use `occurs_at` when the underlying event happens at a different point from when the reader can understand or attribute it. `occurs_at` records story chronology; `available_from` controls spoiler eligibility. When an event predates the numbered narrative, use a clear phase label such as `pre-chapter-1` and explain it in `notes`.

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
first-mention
visual-hint
implicit-clue
strong-inference
speculation
rejection
explicit-reveal
confirmation
adaptation-only-reveal
early-reveal
```

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
```

Record adaptation differences as relationships, not automatically as errors. A claim may use more than one relationship when needed, such as both `condensed` and `revealed-earlier`.

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
4. Search the EPUB.
5. Collect evidence.
6. Draw conclusions.

Never reverse steps 5 and 6.

**Evidence first. Conclusion second.**

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

- All investigations should be put into the Investigations folder and filenames should be in the same format as the following examples:
  - 2026-06-23_Ian_Zreal_Kaspars.md
  - 2026-06-24_Ambassador_Bakerland.md

### Investigation Granularity

Group investigations by subject and bounded analytical scope, not by individual lookup or calendar day.

- Use one focused file for a genuinely standalone question.
- For glossary reconstruction, use one living investigation per subject, medium, and bounded arc, such as one novel volume or one Donghua season.
- Append additional checks to the existing file when the subject, medium, and scope remain the same.
- Create a new file when the medium or bounded arc changes, or when a separate dispute would make the existing record difficult to understand.
- Keep the original creation date in the filename when a living investigation is updated later.
- Mark a living investigation `In Progress` until its bounded timeline is complete; completed checks inside it should still be clearly labeled as verified.

Examples:

```text
2026-06-30_0-08_Volume_1_Reveal_Timeline.md
2026-06-30_0-08_Donghua_Season_1_Reveal_Timeline.md
2026-07-02_0-08_Volume_2_Reveal_Timeline.md
```

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
