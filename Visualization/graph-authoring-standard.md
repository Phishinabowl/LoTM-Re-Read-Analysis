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

Do not overload primary content-node labels with evidence-layer summaries such as `canonical + graph-local` unless that wording is necessary to understand the node itself. Prefer a separate legend, coverage note, output report, or per-edge/per-holder label for evidence-layer explanation.

## Source Expansion

Start with repository-canonical records. If the request exceeds article or Relationship Seed coverage and source access is available, expand into allowed local canonical sources.

For this repository family:

- Novel evidence comes from the local EPUB.
- Subtitle dialogue/timing evidence comes from local `.ass` subtitle files.
- Silent visual evidence requires separate audiovisual verification.

When novel EPUB source expansion is available and suitable for the graph request, use `Tools/Search-Epub.ps1` as the preferred first search path for bounded chapter sweeps, counts, snippets, and repeatable checks. Fall back to another structured EPUB search only if the helper is missing or unusable, and report that degraded path in the output.

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

When reconciling against a prior graph, do not silently drop prior candidates. For every prior candidate that disappears from the new graph, either include it, downgrade it, move it to a more accurate role, or record an exclusion reason in the output report. This applies to holders, pathway controllers, artifacts with sequence-like abilities, variant ladders, named-only pathways, and high-sequence threshold nodes.

## Pathway, Sequence, Role, And Holder Graphs

Pathway, sequence, role, title, affiliation, and "who is what sequence" graphs require a high-coverage discovery pass.

Do not begin only from known glossary nodes or already remembered pathway names.

If EPUB source access is available, run the source-search portions of this pass through `Tools/Search-Epub.ps1` when possible. Use bounded chapter ranges, count sweeps, chapter-ordered snippets, and repeated vocabulary expansion instead of one-off manual text scans.

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
- pathway controller, pathway possessor, or institutional holder
- artifact or item with sequence-like abilities
- source-supported graph-local candidate
- rejected or uncertain with reason
- outside boundary

Every sequence-ladder graph must perform reverse holder coverage:

1. Search for each discovered sequence title.
2. Search for named holders of that title.
3. Search for title-holder appositive forms, such as `Apprentice Fors Wall` or `Xio Derecha, Arbiter`.
4. Search ability-first descriptions later resolved to a sequence or pathway.
5. Search pathway-controller and pathway-possession language, such as `has the pathway in its grasp`, `controls the pathway`, `holds the formulas`, `founded the pathway`, or `family/order/church possesses`.
6. Search artifacts or items whose abilities are explicitly compared to a sequence title or pathway role.
7. Represent unnumbered or likely affiliations explicitly instead of dropping them.

Do not pin uncertain sequence numbers, sequence titles, or holder status more strongly than the source boundary supports.

Pathway controllers, founding families, churches, orders, organizations, and formula possessors are not ordinary holders. Represent them in a dedicated controller/possessor category under the pathway, separate from sequence holder leaves. If a named person, family, or organization is source-supported as a controller or catalyst rather than as a sequence holder, include it in that controller category instead of omitting it or attaching it to an arbitrary sequence.

Artifacts or items with sequence-like abilities are not holders. If the graph scope includes pathway/sequence use or "who/what has what sequence-like abilities," represent such artifacts as artifact/effect nodes attached to the relevant sequence or pathway role. Label them as artifacts, items, or ability analogues, not people.

When title evidence appears before sequence-number context, preserve both reveal points. A label may say, for example, `title known ch13; sequence context ch22`. The graph may connect the holder to the later-learned sequence if the requested reader boundary includes both facts.

## Progression And Holder Placement

When the same entity appears multiple times in an ordered progression, the graph must make the progression visible.

Use one or more of:

- labels such as `stage 1`, `stage 2`, `progression 1/2`, or `then`;
- a small text marker in the holder label, such as `Klein Moretti (1)` and `Klein Moretti (2)`;
- an intermediate `progression` or `advancement` node when the order needs explanation.

Prefer label markers or compact badges over direct edges between repeated holder nodes. Direct progression edges should be used only when the edge itself represents a meaningful advancement event that should affect graph topology. Do not add direct repeated-holder edges merely to make sequence order visible, because those edges can distort placement.

Do not rely only on vertical position or reader inference to show that repeated entity nodes are sequential states rather than duplicates.

Attach holder nodes to the most specific supported parent.

- Confirmed exact holders attach to the confirmed sequence/title node.
- Suspected exact-sequence holders attach to a suspected or candidate sequence node, not to the nearest lower confirmed sequence merely to keep the graph connected.
- If the title is unknown but the sequence threshold is supported, create a node such as `Seq 7: title unknown` or `at least Seq 4: title unknown` and attach the holder there with uncertainty styling.
- If evidence only says a character has power near, comparable to, or approaching a sequence, represent that as a state, comparison, or evidence note rather than as holder membership in that sequence. Do not attach the state/comparison node as a child of the sequence node unless the evidence also supports actual membership in that sequence.

This prevents graphs from implying false advancement, such as attaching a character to `Seq 6` when the evidence only says their power was close to Sequence 6.

High-sequence or threshold evidence should be represented as a threshold, not collapsed to `unknown sequence`.

For example, if source evidence supports that a character is a High-Sequence Beyonder but does not name the exact title, use a node like `High-Sequence / at least Seq 4: title unknown` with the relevant chapter. Do not downgrade the node to plain `unknown sequence` when the source boundary supports a stronger lower bound.

When a pathway has known naming variants, historical variants, factional variants, translation variants, or age-specific versions, preserve that distinction visually. Variant branches should remain close to the main ladder and should rejoin where the source supports convergence. Do not collapse parallel variant ladders into a single distant branch if that makes the equivalence harder to read.

## Layout Semantics

Graph layout should be type-stable.

Top-level grouping should follow the graph's subject semantics, not its evidence source layer, canonicalization status, validation status, or coverage status unless the user explicitly asks for an evidence-audit graph.

Evidence layer, canonicalization status, graph-local status, validation notes, and coverage notes should usually be represented through styling, labels, legends, note branches, or the output report. They should not become the main branches of a content graph.

Before rendering a content graph, inspect the root's direct content children. If the root points first to evidence-layer or workflow nodes such as `repository-canonical`, `source-supported`, `graph-local`, `coverage`, `validation`, or `notes`, and those nodes then own the content, the graph fails layout validation. Restructure it so the root points to semantic subject groups, while evidence/workflow nodes are detached legend or report branches that do not control content placement.

For pathway and sequence maps, choose top-level groups from the subject itself. Depending on the request, good root children include pathway owners/controllers, churches, orders, factions, jurisdictions, pathway families, source-culture variants, or individual pathways. Do not make `Repository-canonical pathway records` and `Source-supported graph-local coverage` the root's main content branches; those are provenance statuses, not subject categories.

Examples of semantic grouping:

- pathway graphs: group by pathway, pathway family, controller/possessor, source-culture variant, or reader-relevant faction;
- artifact graphs: group by artifact, owner/custody chain, ability, usage event, or consequence;
- influence/manipulation graphs: group by manipulator, target, mechanism, event, or confirmed/inferred effect;
- faction graphs: group by faction, hierarchy, operational cell, affiliation, conflict, or jurisdiction;
- event graphs: group by event phase, participant role, cause, consequence, location, or reveal order;
- timeline graphs: group by chronology, chapter/episode, phase, arc, disclosure sequence, or medium boundary.

Within each repeated graph region, use a consistent topology such as:

```text
group
-> pathway/topic/faction
-> ordered sequence/stage/phase chain
-> holder/participant/evidence leaves
```

Nodes with the same semantic role should occupy similar relative positions across the graph. For example, confirmed holders, suspected holders, and graph-local holders may have different border styles, but they are all holder-like nodes and should be placed in the same local region relative to their parent sequence, pathway, event, artifact, or faction.

Do not let confidence classes replace semantic roles. A suspected character holder is still a holder for layout purposes; uncertainty should change styling and label wording, not move it into an unrelated note or evidence region.

For sequence-ladder graphs, the ordered sequence chain is the primary spine. Holder, controller, artifact, note, and evidence nodes should be leaves or local side buckets off the relevant pathway or sequence. Do not put holder-to-holder progression edges, controller nodes, artifacts, or evidence notes into the main sequence chain unless they are themselves ordered stages.

When a sequence has many related holders or artifacts, use a local bucket node such as `Seq 9 holders`, `Seq 5 artifacts`, or `pathway controllers` so the ladder remains readable. The bucket is a layout helper and should be labeled as such when there is any risk of confusion.

Explanatory, validation, legend, coverage, or output-report nodes are not content nodes.

Place these meta nodes in a clearly separated note or appendix branch, usually under a `Legend`, `Notes`, `Coverage`, or `Validation` node. Do not connect meta nodes through content pathways, holder chains, or evidence ladders in ways that affect the placement of the actual graph content.

When a cross-cutting concept, reconstruction, exchange rule, alternate pathway connection, or boundary note would pull an existing ladder or holder into another section, use a local reference/proxy node inside the secondary section. Label it as a reference, proxy, reconstruction, summary, or `see ...` node. Do not directly cross-link into the canonical content node if that link will distort the main layout.

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
