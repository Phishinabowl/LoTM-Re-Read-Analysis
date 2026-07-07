# Lord of the Mysteries Re-Read Analysis

This repository is a working-memory space for a deep reread analysis of **Lord of the Mysteries (Book 1)**.

## AI Agent Bootstrap

If you are an AI assistant opening this repository from a zip, archive, project folder, or file set, start with [Read First: AI Agent Bootstrap](00_READ_FIRST_AI_AGENT_BOOTSTRAP.md).

The active operating contract for repository-answering behavior is [README AI Agent Specification](README-AI-Agent-Specification.md). Read that specification completely before answering substantive repository questions.

[MAINTAINER_CONTEXT.md](MAINTAINER_CONTEXT.md) is maintainer tooling context only. It is not the AI Agent bootstrap or operating contract.

For graph, visualization, Mermaid, relationship-map, pathway-map, or rendered-image requests, follow the repository visualization workflow in [Visualization](Visualization/README.md). Do not create ad hoc graph artifacts outside the repository visualization workflow unless the user explicitly asks for scratch output.

## Repository Notice

This repository is an independent reread analysis project.

No source text is included.

The repository contains notes, chronology analysis, investigations, adaptation comparisons, and research artifacts derived from a personal reread and Donghua analysis of **Lord of the Mysteries**.

The novel EPUB, Donghua subtitle files, bulk extracted artwork, working artwork crops, generated Obsidian QA exports, and any future local source materials are intentionally excluded from version control.

Original repository materials are covered by [LICENSE](LICENSE). Third-party names, artwork, terminology, and related fan-reference materials are covered by the repository [NOTICE](NOTICE.md).

---

The project is focused on investigation rather than summary:

- Chronology
- Reveal order
- Character development
- Themes
- Historical causality
- Family lineages
- Reader knowledge state
- Novel and Donghua disclosure differences
- Spoiler-safe knowledge timelines by chapter and episode

## Spoiler Policy

The user has completed all 8 volumes of **Lord of the Mysteries (Book 1)**.

The user has not completed all of **Circle of Inevitability (Book 2)**. Avoid COI spoilers unless explicitly requested.

## Method

Default workflow:

```text
Memory reconstruction
-> Working theory
-> Source verification, if needed
-> Board update
```

The EPUB is the canonical source for novel verification. Local `.ass` subtitle files are the canonical source for the dialogue, translated text, and timestamps contained in the Donghua subtitle release. Silent visual details require separate visual verification from the episode.

External summaries, wikis, fandom pages, Reddit posts, and memory are not used as evidence when source verification is required.

For clickable navigation, use the [Project Index](INDEX.md).

Reusable helper commands, switch maps, output side effects, and Python/PowerShell parity notes are tracked in the [Tooling Reference](Tools/TOOLING_REFERENCE.md).

## Visualization

Generated visualization artifacts live in [Visualization](Visualization/README.md).

The current GitHub-visible graph is the [Volume 1 Knowledge Graph](Visualization/graphs/volume-1-knowledge-graph.mmd). The graph is generated from glossary metadata, Relationship Seeds, and projected type-specific data-block availability; it is not the source of truth.

Local Obsidian QA mirrors are generated with [Tools/obsidian_qa_export.py](Tools/obsidian_qa_export.py), or the PowerShell fallback [Tools/Obsidian-QA-Export.ps1](Tools/Obsidian-QA-Export.ps1) when Python is unavailable, into the ignored `Obsidian_Export/` folder. They are compiled inspection views for Obsidian graph review, not canonical records and not GitHub-visible visualization artifacts. Each Obsidian QA export also includes `_Generated/repo-refresh-check/`, a dry run of the current configured repository graph views that writes Mermaid sources and a refresh report without touching canonical `Visualization/` outputs.

Graph construction rules shared by maintainer graph work and access-layer AI Agent graph requests live in the [Graph Authoring Standard](Visualization/graph-authoring-standard.md).

Do not embed the full graph in this README; it is maintained as a separate generated artifact.

## Project Structure

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
  type-specific subfolders for source verification records, split by subject and medium

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
  Uniquenesses/
  Pathways/
  Timelines/
  type-specific subfolders for recurring thread records and embedded spoiler-aware knowledge units

Visualization/
  README.md
  graph-authoring-standard.md
  config/
  graphs/
  data/
  rendered/
  generated graph artifacts and provisional graph schema notes

Tools/
  README.md
  Python-preferred helper scripts and documented PowerShell fallbacks

Artwork/
  README.md
  official-epub-image-map.md
  page-assets/
  tracked page-ready artwork and artwork metadata

00_READ_FIRST_AI_AGENT_BOOTSTRAP.md
README-AI-Agent-Specification.md
MAINTAINER_CONTEXT.md
ASSISTANT_CONTEXT.md (deprecated redirect)
CURRENT_STATE.md
PROJECT_RULES.md
INDEX.md
LICENSE
NOTICE.md
```

Embedded Reader Knowledge Ledger entries preserve durable disclosure and audit history, while visible page sections and type-specific data blocks preserve ordinary structured state. Novel chapters and Donghua release order remain independently filterable so a future page can show only what a user should know at their selected position, while also supporting adaptation comparisons.

## Version Control

Git commits should mark durable project knowledge changes, not ordinary discussion.

The entire `Source/` directory is ignored by Git so copyrighted source materials cannot be committed accidentally. The already tracked `Source/README.md` remains as public documentation; the EPUB, Donghua subtitles, and future local source files remain local-only.

Bulk official artwork staging is also ignored by Git. `Artwork/Source/` is the local-only workspace for extracted official artwork and derived working crops; only deliberately selected page-ready assets under `Artwork/page-assets/` should be tracked.

Generated Obsidian QA exports are ignored by Git. Regenerate them locally from canonical repository records instead of editing or committing `Obsidian_Export/`. The export includes QA-only graph dry-run artifacts under `Obsidian_Export/_Generated/repo-refresh-check/`; treat those as local inspection output, not repository graph refreshes.
