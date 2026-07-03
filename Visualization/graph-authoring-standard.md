# Graph Authoring Standard

This document is the shared graph-construction contract for both:

- access-layer AI Agent graph requests, and
- maintainer/project graph work.

It defines how graphs are authored, sourced, validated, and classified before rendering. Rendering mechanics remain in [rendering.md](rendering.md). Repository-maintenance workflow remains in [PROJECT_RULES.md](../PROJECT_RULES.md). Access-layer reasoning, evidence tiers, and output modes remain in [README-AI-Agent-Specification.md](../README-AI-Agent-Specification.md).

## Responsibility Split

Graph work has three separate layers:

1. **Graph intent**: What graph should exist for this request?
2. **Graph authoring**: Which nodes, edges, labels, confidence markers, layout, and source boundaries belong in it?
3. **Graph rendering**: How the Mermaid source becomes SVG/PNG output.

This file owns graph authoring.

## Artifact Intent

Classify every graph request before creating artifacts:

- **Canonical graph refresh**: regenerate existing generated graph artifacts from canonical repository inputs such as Relationship Seeds.
- **Repository-local manual graph**: create a manual `.mmd` source under `Visualization/graphs/` and render it through repository tooling.
- **Chat-only scratch graph**: produce temporary Mermaid only when explicitly requested as scratch, temporary, chat-only, or outside-repository output.

Complex, relationship-heavy, evidence-bearing, or rendered graph requests default to canonical refresh or repository-local manual graph, not scratch output.

## Evidence Layers

Graph data may come from three evidence layers:

- **Repository-canonical**: already recorded in glossary threads, investigations, Reader Knowledge Ledger units, Relationship Seeds, or generated graph inputs.
- **Source-supported graph-local**: found during the graph task in allowed local source material, such as the EPUB or subtitle files, but not yet written back to repository records.
- **Unsupported or external**: outside the repository or outside the allowed source boundary; exclude unless the user explicitly opts into hybrid or research work.

Source-supported graph-local data may appear in a graph when it is supported by the requested source boundary, but it must be visibly distinguished from repository-canonical data.

Recommended labels include:

- `graph-local evidence:`
- `provisional holder:`
- `source-supported, not yet in Relationship Seeds`
- `not canonicalized`
- `candidate project-data update`

Use uncertainty or boundary styling for graph-local content unless the graph's legend defines a more specific provisional style.

## Source Expansion

Start with repository-canonical records. If the request exceeds article or Relationship Seed coverage and source access is available, expand into allowed local canonical sources.

For this repository family:

- Novel evidence comes from the local EPUB.
- Subtitle dialogue/timing evidence comes from local `.ass` subtitle files.
- Silent visual evidence requires separate audiovisual verification.

Source expansion must preserve the requested boundary. Do not include later-volume, later-chapter, adaptation-only, unaudited subtitle, or external material unless the user asks for that source scope.

When source expansion finds supported material not yet in project records, keep it graph-local and report it as a candidate project-data update.

## Maintainer Graph Work

When the maintainer asks for project graph work, graph generation may discover gaps in articles, investigations, metadata, or Relationship Seeds.

Do not silently update glossary threads, investigations, boards, current state, index, or Relationship Seeds as a side effect of graph generation.

Instead:

1. Compile and render the graph using current canonical records plus any clearly marked graph-local evidence.
2. Report proposed project-data updates separately.
3. Explain why each update is warranted and which file(s) would change.
4. Wait for maintainer confirmation before editing canonical project records.
5. After confirmed project-data updates, rerun the appropriate graph refresh or render workflow.

Maintainer graph artifacts may include graph-local evidence so the maintainer can inspect what should be reviewed later in analysis chats.

## User-Facing AI Agent Graphs

When an access-layer AI Agent creates a graph for a user:

- Apply the AI Agent specification's operating mode, evidence hierarchy, reader perspective, source boundary, and output mode first.
- Use this authoring standard for graph construction.
- Distinguish repository-canonical data from source-supported graph-local data in user-facing language.
- Do not mutate repository records unless the user explicitly asks for repository-maintenance work.

If a user asks for "all known" material within a source boundary, that request permits source expansion inside the boundary when repository articles are incomplete.

## Coverage Workflow

Before finalizing a complex graph:

1. Resolve graph intent, perspective, source boundary, and artifact intent.
2. Gather repository-canonical candidates from metadata, Relationship Seeds, glossary threads, investigations, ledgers, graph schemas, and existing generated graph artifacts.
3. If coverage is insufficient and source access is allowed, perform a bounded source-wide candidate discovery pass.
4. Convert candidates into graph nodes/edges with provenance and confidence labels.
5. Reconcile generated candidates against existing graph artifacts or user-provided prior graph drafts when available.
6. Classify every disputed or uncertain candidate as included, included with lower confidence, graph-local, excluded as unsupported, excluded as outside boundary, or deferred because source access is degraded.
7. Run holder, title, source-boundary, layout, class, and render validation before final output.

Existing generated graph artifacts and user-provided prior graphs are coverage references, not canonical truth. Use them as candidate inventories to prevent omissions, then verify candidates against repository records or allowed source evidence.

## Pathway, Sequence, Role, And Holder Graphs

Pathway, sequence, role, title, affiliation, and "who is what sequence" graphs require a high-coverage discovery pass.

Do not begin only from known glossary nodes or already remembered pathway names.

Use generic structural searches inside the requested source boundary, including:

- `Sequence`
- `pathway`
- `potion`
- `formula`
- `Seq`
- numbered sequence/title patterns
- pathway/table/list chapter clusters
- title-holder surface forms
- cautious phrases such as `suspected`, `likely`, `former`, `advanced`, `at least`, `belongs to`, `path of`, and `pathway`

For each discovered pathway, sequence title, role title, affiliation, or holder-like case, classify it as:

- confirmed numbered sequence/title
- confirmed pathway, exact sequence unknown
- likely or inferred affiliation
- named-only pathway-like term
- suspected holder
- former holder
- source-supported graph-local candidate
- rejected or uncertain with reason
- outside boundary

Every sequence-ladder graph must perform reverse holder coverage:

1. Search for each discovered sequence title.
2. Search for named holders of that title.
3. Search for title-holder appositive forms, such as `Apprentice Fors Wall` or `Xio Derecha, Arbiter`.
4. Search ability-first descriptions later resolved to a sequence or pathway.
5. Represent unnumbered or likely affiliations explicitly instead of dropping them.

Do not pin uncertain sequence numbers, sequence titles, or holder status more strongly than the source boundary supports.

## Confidence And Styling

Graph labels and styling must preserve confidence:

- confirmed repository-canonical facts use ordinary confirmed styling;
- source-supported graph-local material uses provisional or uncertainty styling;
- likely, inferred, suspected, unresolved, missing, boundary, or not-confirmed material uses uncertainty styling;
- named-only or pathway-like terms should not be forced into full sequence ladders.

Uncertainty should be visible in both text and style. Do not rely only on color.

## Layout And Rendering

Follow [rendering.md](rendering.md) for layout, class coverage, ordered-series layout, dense graph shape, visual role grammar, render helpers, and fallback rendering.

Use repository render helpers before direct renderer commands:

- `Visualization/render-graphs.ps1` for canonical refreshes.
- `Visualization/render-mermaid.ps1` for manual or agent-drafted Mermaid files.

Direct `mmdc` is fallback/debug only and must be labeled degraded when used because helper scripts are unavailable or cannot run.

## Output Report

For complex maintainer or user-facing graph work, include a short coverage report with:

- artifact intent;
- source boundary;
- repository-canonical inputs used;
- source-expanded graph-local evidence used;
- exclusions or downgraded confidence calls;
- proposed project-data updates, if any;
- render path and degraded-render notes, if any.
