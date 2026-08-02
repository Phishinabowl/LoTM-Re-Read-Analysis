# Maintainer Context

This file is maintainer tooling context for a human project maintainer working directly with Codex or a similar development assistant.

This is not the AI Agent bootstrap or operating contract.

For repository-answering behavior, read [README-AI-Agent-Specification.md](README-AI-Agent-Specification.md) first.

## Framework Improvement Mode

When the maintainer asks to resume framework/schema evolution, begin with [Framework Improvement Lifecycle](Framework/framework_improvement_lifecycle.md). It defines the fresh-session orientation order, version-design and proposed-testing requirements, cumulative verification gates, two-part implementation confirmation, pressure-test closure, evolution logging, and next-version handoff.

Do not resume from conversational memory alone. Reconstruct the current state from Git, the lifecycle, [Framework Testing Methodology](Framework/testing_methodology.md), and the latest completed version plus recommendation in [Framework Evolution History](Framework/framework_evolution.md).

## Implementation Work Annotations

Use [Todo Tree And GitHub Working Convention](WORK_ANNOTATION_STANDARDS.md) for durable implementation-local follow-ups, defects, questions, assumptions, workarounds, review needs, and verification needs. Local annotations use `OWNER` or `UNASSIGNED`; public GitHub handles appear only after an issue exists and GitHub establishes the assignment. Never expose the maintainer's real name or private identity.

Todo Tree does not replace `CURRENT_STATE.md`, framework evolution/testing records, or GitHub Issues. At task and branch closure, report annotations added, changed, promoted, reconciled, or removed and route anything that has outgrown a source-local comment to its authoritative artifact.

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

## Git Workflow Notes

- When documentation must cite an implementation commit, use two commits: commit the implementation first, capture its hash, then update and commit the documentation reference. Framework versions must follow the exact confirmation sequence in `Framework/framework_improvement_lifecycle.md`.
- Run `git add` and `git commit` for the documentation-reference commit as separate shell invocations. Combined invocations have intermittently produced `.git/index.lock` permission errors in Codex even when no stale lock exists.
- If that transient error occurs, verify that no partial commit or unexpected worktree change was created, then retry staging and committing separately.
- Never delete `.git/index.lock` unless its existence has been independently confirmed and the lock is known to be stale.

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
