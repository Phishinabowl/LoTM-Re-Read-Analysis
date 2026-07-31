# Source

Place local source materials here. The entire `Source/` directory is ignored by Git, except that this already tracked documentation file remains in the repository.

`Project_Config/resources.yaml` governs this directory as ignored evidence storage. `Project_Config/sources.yaml` separately defines creative works and continuities, stable evidence-source IDs, media, authority profiles, priority, citation conventions, typed work/source relationships, and optional bindings to files beneath this directory. Local filenames are storage details, not canonical source identities.

## Lord of Mysteries

Place the EPUB here:

```text
Lord of Mysteries - Book 1.epub
```

The EPUB is registered as `lotm-book-1-novel` for work `lotm-1`, the priority-1 primary edition for the `lotm-narrative` comparison group. It is the canonical source of truth for verification across all eight volumes of Book 1, but the file itself is ignored by Git and should not be committed.

Use the EPUB only when chronology, reveal order, reader knowledge state, relationships, or other evidence-sensitive questions require verification.

## Circle of Inevitability

The Book 2 EPUB is stored as:

```text
Circle of Inevitability.epub
```

It is registered as `lotm-book-2-novel` for work `lotm-2`, independently from Book 1's chapter and volume namespace. The package currently exposes 1,180 sequential chapter files but no machine-readable volume boundaries recognized by project tooling. Its volume catalog therefore remains pending verification; do not infer those boundaries from outside knowledge or silently reuse Book 1 ranges.

## Donghua

The creative adaptation is work `lotm-donghua-season-1`, related to novel work `lotm-1` by `adaptation-of` and assigned to the separate Donghua continuity. Its observed release is source `lotm-donghua-release`. Season 1 subtitle files are source `lotm-donghua-subtitles`, related to that release by `subtitle-track-of`. Both evidence sources are priority 2 in the LoTM narrative comparison group. Subtitle files are stored locally under:

```text
Donghua_Subtitles/Season_1/
```

Current coverage includes the 13 regular Season 1 episodes. Special-episode subtitles are not currently present.

The three 2026 specials are registered independently as works `lotm-donghua-special-1`, `lotm-donghua-special-2`, and `lotm-donghua-special-3`, with matching official-release sources. Their story identities are *City of Silver*, *The Marked Hunt Part 1*, and *The Marked Hunt Part 2*: Marked Hunt's part numbering is therefore one lower than its overall special numbering. No subtitle-track sources or local bindings are registered for them yet. When subtitle files become available, add one subtitle source per special, relate each to its matching release with `subtitle-track-of`, and bind it to the corresponding local file or directory.

The files are UTF-8 Advanced SubStation Alpha (`.ass`) subtitles with timestamped English (US) dialogue. Their headers identify Crunchyroll/Tencent provenance and indicate that they were generated through `pysubs2`.

Use subtitles as the canonical source for the dialogue and translated on-screen text contained in this release. Subtitles alone do not verify silent visual details, framing, expressions, object placement, or other information visible only in the animation.

Do not commit subtitle files or reproduce source dialogue in project records. Preserve evidence through episode numbers, timestamps, and paraphrased summaries.
