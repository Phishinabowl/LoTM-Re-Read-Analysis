# Read First: AI Agent Bootstrap

If you are an AI assistant opening this repository from a zip, archive, project folder, or file set, read this file first.

## Repository Boundary

Use the repository package the user intentionally provided.

Priority:

1. Attached zip, archive, or uploaded file bundle.
2. Explicit current workspace or project folder.
3. The public GitHub repository, if no local package is available: [Phishinabowl/LoTM-Re-Read-Analysis](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis).

If attachment metadata exposes an absolute local path, treat that path as transport metadata only. Do not use the local absolute path, containing directory, sibling folders, parent folders, or similarly named local checkouts as repository evidence. Use only the attached file handle, uploaded file contents, or runtime-extracted archive contents supplied by the tool environment unless the user explicitly asks you to use a local workspace.

## Source Availability Check

During bootstrap, check whether local source materials are available inside the active repository package or current workspace:

- novel EPUB;
- Donghua `.ass` subtitle files.

If these source materials are missing, report that source expansion is currently unavailable and ask the user to provide the missing files if they can.

If the user cannot provide them, continue with repository artifacts only and treat source expansion into the EPUB or subtitles as unavailable for the session.

The public GitHub repository does not include ignored local source materials, so GitHub fallback bootstraps should always perform this availability check and report the missing-source limitation.

If novel EPUB source expansion is available and needed, prefer the repository EPUB search helper `Tools/Search-Epub.ps1` for bounded chapter sweeps before using ad hoc EPUB parsing. If that helper is missing or unusable, report the degraded source-search path.

## Repository Tooling Availability Check

During bootstrap, also check and report whether these repository helpers are present:

- EPUB search helper: `Tools/Search-Epub.ps1`;
- canonical visualization refresh helper: `Visualization/render-graphs.ps1`;
- manual Mermaid render helper: `Visualization/render-mermaid.ps1`;
- Mermaid browser config: `Visualization/config/puppeteer-config.json`;
- shared render settings: `Visualization/config/render-settings.json`.

If visualization helpers or config are missing, report that repository visualization rendering is degraded. Do not call direct `mmdc` equivalent to the repository render workflow when the helper scripts are unavailable.

The active operating contract for repository-answering behavior is:

- [README-AI-Agent-Specification.md](README-AI-Agent-Specification.md)

Read `README-AI-Agent-Specification.md` completely before answering substantive repository questions.

Do not use [MAINTAINER_CONTEXT.md](MAINTAINER_CONTEXT.md) as the AI Agent bootstrap or operating contract. That file is maintainer tooling context for project-maintenance work only.

Do not use [ASSISTANT_CONTEXT.md](ASSISTANT_CONTEXT.md) as the AI Agent bootstrap or operating contract. That file is a deprecated redirect kept only for older chats.

## Visualization And Graph Requests

If the user asks for a graph, visualization, Mermaid diagram, relationship map, pathway map, timeline map, or rendered image, do not handle it as a standalone Mermaid task.

After reading `README-AI-Agent-Specification.md` completely, apply its graph and visualization workflow, especially:

- Section 9: Graph Compilation
- Section 11: Visualization Compilation
- Section 11.16: Graph Request Routing Gate and Repository Rendering Instructions

Then read the local repository visualization contract as implementation guidance if further guidance is needed:

- [Visualization/README.md](Visualization/README.md)
- [Visualization/graph-authoring-standard.md](Visualization/graph-authoring-standard.md)
- [Visualization/rendering.md](Visualization/rendering.md)
- [Visualization/data/graph-schema.md](Visualization/data/graph-schema.md)

Use the AI Agent specification to classify the requested output as one of:

1. canonical graph refresh from Relationship Seeds;
2. repository-local manual graph under `Visualization/graphs/`;
3. chat-only scratch Mermaid.

The local visualization files supplement the AI Agent specification. They do not replace, shorten, or override the full graph and visualization workflow in `README-AI-Agent-Specification.md`.

Use chat-only scratch Mermaid only when the user explicitly asks for an informal scratch diagram or for output outside the repository visualization workflow.
