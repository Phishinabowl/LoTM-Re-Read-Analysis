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
└── (Thread records created over time)

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

Prefer Markdown links when the target file exists.

Use plain planned filenames when the target file does not exist yet.

Do not manually maintain incoming references or backlinks yet. Backlinks, generated reference indexes, relationship graphs, and visual maps should be left for future automation once the repository is larger.

## Open Questions

Every glossary thread should include an `Open Questions` section.

Use it to capture unanswered questions that may later become investigations.

When an open question is answered:

1. Create or update the relevant investigation record if EPUB evidence was used.
2. Update the relevant board if the conclusion changes durable project knowledge.
3. Update the glossary thread to close, revise, or remove the question.
4. Recommend a matching commit if the change satisfies the commit cadence rules.

---

# Canonical Sources

## EPUB

The EPUB:

```text
Lord of Mysteries - Book 1.epub
```

is the canonical source of truth.

Do not use external summaries, wikis, fandom pages, Reddit posts, or memory when verification is required.

Use the EPUB.

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
