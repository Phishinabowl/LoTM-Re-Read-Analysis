# Sleepless / Evernight Pathway Name Arbitration

## Related Glossary Thread

- [Sleepless Pathway](../../../Glossary_Threads/Pathways/pathway-sleepless.md)

## Question

When should reader-boundary tooling switch the pathway's display name from `Sleepless Pathway` to `Evernight Pathway` while keeping `pathway-sleepless.md` as the stable slug?

## Status

Complete for display-name boundary selection. This record only arbitrates the name timeline; it does not expand the active Chapter 47 pathway article with later Sequence structure.

## Search Strategy

- EPUB term summary:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "Evernight pathway|Sleepless pathway|Darkness pathway" -TermSummary`
- Early exact-phrase inspection:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "Evernight pathway" -StartChapter 200 -EndChapter 240 -ContextLines 4 -MaxHitsPerChapter 20 -Json -IncludeLineMatchCounts`
- Early confirmation cluster:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "Evernight pathway" -StartChapter 500 -EndChapter 540 -ContextLines 4 -MaxHitsPerChapter 20 -Json -IncludeLineMatchCounts`
- Pre-exact wording check:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "pathway of the Evernight|Evernight pathway|Sleepless pathway" -StartChapter 1 -EndChapter 240 -TermSummary`

## Findings

- Full-book counts: `Evernight pathway` appears 31 times, `Sleepless pathway` appears 14 times, and `Darkness pathway` appears 0 times in main chapter text.
- Volume split: `Sleepless pathway` dominates Volume 1, while `Evernight pathway` first appears in Volume 2 and becomes the stronger later/global phrase across later volumes.
- Chapter 203 first makes Evernight wording reader-safe for this route by discussing the `pathway of the Evernight` and then tying Death/Corpse Collector interchangeability to the Sleepless pathway. This supports an implied/associated Evernight label before the exact phrase appears.
- Chapter 217 is the first exact `Evernight pathway` phrase found by the EPUB search tool.
- Chapter 526 connects Nightmare effects to the Evernight pathway.
- Chapter 530 explicitly places Death and Evernight as switchable high-Sequence pathways, making the umbrella naming unambiguous.

## Decision

Use `Sleepless Pathway` as the reader-display name from Novel Volume 1, Chapter 22 through Novel Volume 2, Chapter 216.

Allow an implied `Evernight association` from Novel Volume 1, Chapter 203 through Novel Volume 2, Chapter 216. Reader-facing tooling may show this as an implied/associated name, but should keep `Sleepless Pathway` as the main display name until the exact phrase appears.

Use `Evernight Pathway` as the reader-display name from Novel Volume 2, Chapter 217 onward. Chapter 203 is important supporting context, but Chapter 217 is the clean display boundary because it is the first exact phrase.

Keep `Darkness Pathway` as an official-artwork/formal label, not as a main-text reader-display name, because the exact phrase has zero main-text hits in the EPUB sweep.
