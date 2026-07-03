# Read First: AI Agent Bootstrap

If you are an AI assistant opening this repository from a zip, archive, project folder, or file set, read this file first.

## Repository Boundary

Use the repository package the user intentionally provided.

Priority:

1. Attached zip, archive, or uploaded file bundle.
2. Explicit current workspace or project folder.
3. The public GitHub repository, if no local package is available: [Phishinabowl/LoTM-Re-Read-Analysis](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis).

If an attachment exposes an absolute local path, do not inspect sibling folders, parent folders, or similarly named local checkouts unless the user explicitly asks you to use that local workspace.

If using the GitHub repository fallback, remember that ignored local source material is not included. For source-expanded answers that need the novel EPUB or Donghua subtitle files, ask the user to provide those files if they can. If they cannot, state that source expansion is unavailable and continue with repository artifacts only.

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
