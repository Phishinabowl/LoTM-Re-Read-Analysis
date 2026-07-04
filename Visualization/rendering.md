# Rendering Graph Exports

This document records the current working process for rendering Mermaid graph files into shareable image exports.

Rendered files are generated artifacts. If a rendered graph exposes incorrect data, update the source glossary records or Relationship Seeds, regenerate the Mermaid file, and then rerender the image.

## Recommended Outputs

For sharing:

- Use PNG for Discord and other chat previews.
- Keep SVG for archive and zoomable inspection.

The first graph was rendered to:

- `Visualization/rendered/volume-1-knowledge-graph.png`
- `Visualization/rendered/volume-1-knowledge-graph.svg`

## Tool

Use Mermaid CLI:

```powershell
npm install -g @mermaid-js/mermaid-cli
```

The default `mmdc` browser launch may time out on Windows. The working approach is to point Puppeteer at local Microsoft Edge through the permanent render config in `Visualization/config`.

Mermaid CLI is the underlying renderer, not the project workflow entry point. For repository graph work, call the Python visualization helper below first. Use the PowerShell helper as the Windows fallback. Direct `mmdc` commands are fallback/debug commands only.

## Permanent Render Config

Puppeteer launch settings live at:

- `Visualization/config/puppeteer-config.json`

Graph render settings live at:

- `Visualization/config/render-settings.json`

If Edge is installed elsewhere, update `executablePath` in the Puppeteer config. Chrome can also be used if available.

## Availability Checks

Before running visualization helpers on an unfamiliar machine or fresh agent session, check whether Python is available:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-Python.ps1
```

For structured agent workflows, use JSON output:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-Python.ps1 -Json
```

Also confirm the render config files exist:

- `Visualization/config/puppeteer-config.json`
- `Visualization/config/render-settings.json`

Treat the probe result as the session's Python-availability state. If Python is available, use Python-preferred commands going forward without rerunning the probe before every render command. Rerun only if the environment changes, such as PATH edits, Python installation changes, a different shell, a different machine, or a failed Python launch that suggests the earlier state is stale.

If Python is unavailable, use the PowerShell fallback commands below for that session. If Python is available but a Python helper fails, treat that as a helper failure rather than silently falling back. If both helpers fail or required config is missing, report repository visualization rendering as degraded before using direct `mmdc`.

## Render Commands

From the repository root, render every configured graph view and write the refresh report:

Preferred Python:

```powershell
python Visualization\visualize.py --mode Refresh
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Refresh
```

To update only the refresh report without rerendering images:

Preferred Python:

```powershell
python Visualization\visualize.py --mode Refresh --skip-render
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Refresh -SkipRender
```

To render a manually authored Mermaid file without regenerating repository graph views or updating the refresh tracker, use pure render mode:

Preferred Python:

```powershell
python Visualization\visualize.py --mode Render `
  --input-path Visualization\graphs\example.mmd
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Render `
  -InputPath Visualization\graphs\example.mmd
```

By default, pure render mode writes both SVG and PNG files to `Visualization/rendered/` using the input filename. You can pass one or more explicit outputs:

Preferred Python:

```powershell
python Visualization\visualize.py --mode Render `
  --input-path Visualization\graphs\example.mmd `
  --output-path Visualization\rendered\example.svg `
  --output-path Visualization\rendered\example.png
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Render `
  -InputPath Visualization\graphs\example.mmd `
  -OutputPath Visualization\rendered\example.svg,Visualization\rendered\example.png
```

Use pure render mode for one-off, manually authored, or agent-drafted Mermaid files. Use the canonical refresh command only when generated graph artifacts should be rebuilt from Relationship Seeds.

Use `-NoProfile` to keep local shell profile output from contaminating command output.

Do not treat a direct `mmdc -p Visualization/config/puppeteer-config.json ...` command as equivalent to pure render mode. The helpers are the repository workflow layer. They apply shared render settings and validation expectations before calling the renderer.

If an execution environment cannot write under `Visualization/`, the preferred degraded path is still to run `Visualization\visualize.py --mode Render` or `Visualization\visualize.ps1 -Mode Render` with an accessible input path and explicit output path, when possible. Use direct `mmdc` only after the helper scripts are unavailable, fail, or cannot be run against the accessible paths. When direct `mmdc` is used, label the render as a degraded fallback.

The helpers read `Visualization/config/render-settings.json`, render every configured view to every configured output, update the semantic graph snapshot, and update the live refresh tracker in:

- `Visualization/README.md`

The semantic snapshot is stored at:

- `Visualization/data/refresh-snapshot.json`

The snapshot lets the tracker report added or removed nodes, added or removed relationships, changed relationship labels, duplicate relationships, broken links, orphan nodes, and pending graph nodes across refreshes.

## Automatic Render Size

The render scripts use the `autoSize` block in `Visualization/config/render-settings.json` to increase Mermaid viewport size for larger graphs.

The default dimensions remain `width` and `height`. When `autoSize.enabled` is true, the renderer counts Mermaid node and edge lines, estimates graph complexity, detects high fan-out hubs, and increases render width and height in bounded steps.

This keeps small graphs fast and compact while giving large relationship maps more room to lay out cleanly. If a large graph still renders cramped or clipped, adjust:

- `complexityUnit`
- `widthStep`
- `heightStep`
- `fanOutThreshold`
- `fanOutWidthStep`
- `maxWidth`
- `maxHeight`

Wide fan-out graphs are expected. If one source, target, group, artifact, pathway, or concept connects to many neighbors, Mermaid often spreads the graph horizontally and may need extra width before the first render looks sensible. The render helpers use `fanOutThreshold` and `fanOutWidthStep` to widen those graphs automatically.

Fan-out sizing only gives the layout room. It does not decide semantic grouping. When a hub still produces messy crossings after auto-sizing, prefer one of these projections:

- group related leaves under intermediate semantic nodes;
- split the graph into narrower topic-specific views;
- use relationship-node projection for long relationship explanations;
- use local reference/proxy nodes when a summary or reconstruction would otherwise pull edges across unrelated sections.

## Ordered-Series Layout

Ordered information should usually render as a chain, not as a flat fan.

This rule is universal. It applies to pathway sequences, artifact custody chains, influence cascades, relationship progressions, timelines, phases, stages, ranks, steps, chapters, episodes, investigation beats, and any other ordered progression.

Preferred projection:

```mermaid
graph TB
  parent["Topic"]
  step1["Step 1"]
  step2["Step 2"]
  step3["Step 3"]
  parent --> step1
  step1 --> step2
  step2 --> step3
```

Avoid this shape when the children are ordered:

```mermaid
graph TB
  parent["Topic"]
  parent --> step1["Step 1"]
  parent --> step2["Step 2"]
  parent --> step3["Step 3"]
```

Flat fan-out is appropriate for unordered peer sets. Ordered-series fan-out usually makes Mermaid stretch the graph horizontally and hides the progression the graph is meant to show.

If the same entity appears more than once in an ordered series, make the repeated-state progression explicit in the graph source before rendering. Prefer visible label markers or compact badges. Use direct progression edges between repeated-state nodes only when the edge itself is meaningful and should affect topology. Do not add extra edges merely to show order, and do not depend on layout position alone to show that repeated nodes represent sequential states.

The layout validator can flag nodes with too many direct ordered-series children. The configured patterns are intentionally generic, such as `Seq 9`, `Phase 1`, `Step 1`, `Chapter 1`, and `Episode 1`.

For ladder-style graphs, keep the ordered sequence, phase, rank, or step chain as the primary spine. Related holders, artifacts, controllers, notes, and evidence nodes should attach as leaves or local buckets rather than interrupting the spine.

## Dense Knowledge Graph Shape

Dense knowledge graphs should usually be one connected styled-node map, not many Mermaid `subgraph` clusters.

Preferred projection:

```mermaid
graph TB
  root["Boundary / scope"]
  group_a["Evidence group A"]
  entity_a["Entity A"]
  detail_a["Detail A"]
  root --> group_a
  group_a --> entity_a
  entity_a --> detail_a
```

Avoid using a separate Mermaid `subgraph` cluster for every topic, pathway, faction, character, timeline arc, or evidence group unless the user explicitly asks for cluster boxes. Mermaid clusters are useful for a few large visual regions, but many clusters often become disconnected islands and force the render into a wide strip.

For dense generated or agent-drafted views:

- use styled group nodes instead of many cluster boxes;
- connect the graph through a visible semantic spine, such as `root -> group -> entity -> detail`;
- define node classes for important visual roles;
- keep content nodes on the content spine and put legend, coverage, validation, and explanatory nodes in a separate note or appendix branch;
- group content by subject semantics rather than evidence source layer, canonicalization status, validation status, or coverage status unless the graph is explicitly an evidence audit;
- make the root's direct content children semantic subject groups, not provenance or workflow groups such as `repository-canonical`, `source-supported`, `graph-local`, `coverage`, `validation`, or `notes`;
- reserve `subgraph` for a few broad regions or intentionally separate diagrams.

The layout validator can flag dense graphs that have no class definitions, too many subgraph clusters, or too many disconnected components.

## Visual Role Grammar

Dense graphs should expose their meaning through a consistent visual grammar. The exact palette may evolve, but the method should remain stable:

- fill color communicates the node's semantic role;
- border style communicates certainty, incompleteness, or boundary status;
- label prefixes communicate reader-facing interpretation in text;
- topology communicates structure and chronology.

Recommended role classes include:

- `root` or `main` for the graph boundary or scope;
- `group` for organizing buckets or evidence regions;
- `entity`, `character`, `actor`, `target`, `pathway`, `concept`, `faction`, `artifact`, `location`, `event`, `mechanism`, `effect`, or similar domain roles for major subjects;
- `sequence`, `step`, or `stage` for ordered progression nodes;
- `holder`, `owner`, `possessor`, `participant`, `member`, `student`, `mentor`, `manipulator`, `victim`, or similar assignment/participation roles for people or entities connected to a subject;
- `relationship` for generated relationship presentation nodes;
- `uncertain`, `boundary`, or `note` for inferred, missing, ambiguous, unresolved, or reader-boundary material.

Uncertainty should be visible without relying only on words. Use dashed or otherwise distinct border styling for uncertainty-like classes such as `uncertain`, `boundary`, and `note`.

Confidence styling should not override layout role. A suspected holder, inferred participant, graph-local character, or provisional owner should still be placed with the same local topology as confirmed nodes of that semantic type. Use border style, label wording, and class assignment to show uncertainty.

Labels should still carry the semantic meaning in text. Examples include `holder:`, `owner:`, `participant:`, `manipulates:`, `affected:`, `member:`, `mentor:`, `likely holder:`, `holder-like:`, `generic holder:`, `Boundary note`, and `Seq 9:`. Color and line style help scanning, but text remains the accessible source of meaning.

The class validator can flag dense graphs where label wording implies one visual role but the node is assigned to another. For example, a node labeled `Seq 9...` should use a progression role class, and a node labeled `likely holder...` should use an uncertainty-style class. Keep graph-specific roles consistent inside each view: artifact maps may emphasize owners, locations, effects, and custody events; influence maps may emphasize actors, mechanisms, targets, and affected events; character relationship maps may emphasize characters, factions, relationships, statuses, and shared events.

## Class Coverage Validation

The render scripts validate Mermaid class coverage before rendering styled graphs.

When a graph uses `classDef` or `class` statements, every declared or edge-used node must have an explicit class assignment. The validator also reports class assignments that reference missing nodes, nodes assigned to undefined classes, and configured semantic pattern mismatches.

The current semantic pattern check includes sequence-like node ids. For example, a node such as `seer7_unknown` must be assigned to the `sequence` class when rendering a graph that defines sequence styling.

This prevents styled graphs from silently falling back to Mermaid default node styling.

## Layout-Island Validation

Sectioned graphs should avoid direct cross-section links into nodes that already belong to another branch.

When a graph uses section nodes such as `group`, a summary or reconstruction section should not directly link to an existing `holder` or `sequence` node if that node already has a non-section owner elsewhere in the graph. Use a local reference/proxy node instead.

Preferred projection:

```mermaid
graph TD
  late_group["Late reconstruction"]
  late_ince["Ince Zangwill<br/>late reconstruction reference"]
  late_nightwatcher["Nightwatcher advancement<br/>see Sleepless Seq 4"]
  late_group --> late_ince
  late_ince --> late_nightwatcher
```

Avoid:

```mermaid
graph TD
  late_group["Late reconstruction"]
  sl4["Seq 4: Nightwatcher"]
  h_ince_nightwatcher["holder: Ince Zangwill"]
  sl4 --> h_ince_nightwatcher
  late_group --> h_ince_nightwatcher
```

The second shape forces Mermaid to place one node in two visual sections and usually creates long crossing edges.

The layout validator also checks for accidental duplicate visual labels across ordinary nodes. If two node IDs render with the same visible label, either collapse them into one canonical node or label the secondary node explicitly as a reference/proxy.

Proxy/reference-like node IDs, such as `late_ince_ref`, must label themselves as a reference, proxy, reconstruction, summary, or `see ...` node. This keeps local layout helpers from looking like separate canonical entities.

Legend, coverage, validation, output-report, and explanatory nodes should be rendered as a separate note or appendix branch. They should not be connected through the same content spine as pathways, holders, timelines, artifacts, factions, events, or other primary graph entities.

## Deferred Validation Ideas

These graph hygiene checks are worth revisiting after more examples exist, but should not become hard validation yet:

- Section or group nodes with too many direct children may need subgroups or split views.
- Fan-out hubs may eventually get a warning when they exceed the configured `fanOutThreshold`, but current examples are still too few for a hard rule.
- Dense manual graphs that mix hierarchy, evidence, reconstruction, and holder edges with identical arrow semantics may need edge-purpose conventions.
- Declared but disconnected nodes may indicate stale graph fragments, but some draft graphs may use them intentionally.

## Dense Graph Readability

The graph generator projects relationship-heavy views through generated relationship nodes:

```mermaid
graph TD
  source_node["Source"]
  rel_001["relationship type<br/>timing/status/confidence"]
  target_node["Target"]
  source_node --> rel_001
  rel_001 --> target_node
```

This keeps long semantic labels out of Mermaid edge labels, where they tend to overlap when many edges share a hub. The `rel_###` nodes are presentation artifacts only; relationship seeds remain canonical.

Timing-spoiler-free views use the same projection, but omit chapter and episode timing from the relationship node text.

Direct `mmdc` commands remain useful for debugging a single view or recovering when the helper scripts cannot run. They are not the default repository render workflow:

```powershell
mmdc -p Visualization\config\puppeteer-config.json `
  -i Visualization\graphs\volume-1-knowledge-graph.mmd `
  -o Visualization\rendered\volume-1-knowledge-graph.svg `
  -b white `
  -w 2400 `
  -H 1800
```

```powershell
mmdc -p Visualization\config\puppeteer-config.json `
  -i Visualization\graphs\volume-1-knowledge-graph.mmd `
  -o Visualization\rendered\volume-1-knowledge-graph.png `
  -b white `
  -w 2400 `
  -H 1800 `
  -s 2
```

The first PNG export produced a readable Discord-friendly image around `4768 x 1426` pixels and about `428 KB`.

Keep the generated PNG/SVG exports only when they are useful project artifacts.

## Troubleshooting

If `mmdc` times out after 30 seconds even on a tiny test graph, it is likely failing to launch its default browser. Use the Puppeteer config above.

Tiny test graph:

```powershell
"graph TD`nA[Alpha] --> B[Beta]" | mmdc `
  -p Visualization\config\puppeteer-config.json `
  -i - `
  -o Visualization\rendered\_mmdc-test.svg
```

Delete `_mmdc-test.svg` after confirming the renderer works.
