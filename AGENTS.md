# LoTM Analysis agent instructions

- Treat authored prose and structured state as distinct canonical content. Preserve authored wording; do not regenerate narrative prose from taxonomy values or structured fields.
- Presentation and generated Obsidian QA exports are projections, not additional sources of truth. Keep generated QA mirrors local/ignored and edit authoritative sources.
- Consult current framework contracts and active plans before schema/template changes. Link to them rather than duplicating evolving schemas in this file.
- Discovery inventories and exploratory stress tests do not silently resolve canonical conflicts. Preserve unresolved decisions for maintainer review; do not convert a read-only probe into implementation.
- Respect visibility independently for structured data and authored content, following the current contracts.

## Local dual-remote publication

- GitHub is the authoritative merge location and the `origin` fetch remote. This checkout has two intentional `origin` push URLs, for GitHub and Azure Repos; `ado` supports independent fetches and parity checks. Verify the actual configuration before publishing.
- On authorized confirmation, publish only the intended branch with `git push origin HEAD`. Do not also push to `ado`, or use `--mirror`, `--all`, `--tags`, or force pushes for routine publication.
- A dual-destination push is not atomic. Inspect both destination results, refresh their tracking references, and verify HEAD, upstream, `origin/<current-branch>`, and `ado/<current-branch>` agree. Diagnose partial publication before retrying; do not overwrite divergent history.
- ADO validation PRs do not authorize independent merges. Initial population of the empty ADO repository and its default-branch choice are separate from normal current-branch publication; publish additional refs only when explicitly authorized.
