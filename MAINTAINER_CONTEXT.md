# Maintainer Context

This file is maintainer tooling context for a human project maintainer working directly with Codex or a similar development assistant.

This is not the AI Agent bootstrap or operating contract.

For repository-answering behavior, read [README-AI-Agent-Specification.md](README-AI-Agent-Specification.md) first.

## User Preferences

- Completed all 8 volumes of LoTM.
- Has not completed all of COI.
- Strong at systems thinking and thematic analysis.
- Weaker at chronology, family lineages, and reveal order.
- Prefers Socratic investigation style.
- Start with memory reconstruction.
- Use EPUB only when verification is needed.
- For repo-only or build-pilot-from-existing-data passes, follow Repository Mode search discipline even in Codex maintainer work: do not seed searches with pretrained knowledge, model memory, fan knowledge, or outside-known terms unless the user explicitly opts into Hybrid/Research work.
- Evidence first, conclusion second.
- End responses with the next investigation question.
- Preserve novel and Donghua disclosure timelines independently.
- Embed Reader Knowledge Ledger units in glossary threads for durable spoiler-timed claims, including theories and misconceptions.
- Treat structured YAML knowledge-unit blocks as canonical; do not maintain separate claim files or duplicate JSON manually.
- Use local Donghua `.ass` files as canonical evidence for their subtitle dialogue and timestamps, while treating silent visual details as separate visual evidence.
- Keep all local source media under `Source/`, which is ignored by Git; preserve only paraphrased evidence and references in tracked records.
- Keep bulk official artwork staging local-only under ignored `Artwork/Source/`; track only deliberately selected page-ready assets under `Artwork/page-assets/`.
- After completing a commit and push, continue directly into the next discussion or investigation question unless the user pauses or changes direction.

The user is strongest at:

- Systems thinking
- Themes
- Character motivations
- Large-scale causality

The user is weaker at:

- Chronology
- Reveal order
- Family lineages
- Epoch history
- Historical sequencing

Assist accordingly.
