# Source

Place local source materials here. The entire `Source/` directory is ignored by Git, except that this already tracked documentation file remains in the repository.

`Project_Config/resources.yaml` governs this directory as ignored evidence storage. `Project_Config/sources.yaml` defines the stable evidence-source IDs, media, priority, citation conventions, derivation relationships, and optional bindings to files beneath this directory. Local filenames are storage details, not canonical source identities.

## Lord of Mysteries

Place the EPUB here:

```text
Lord of Mysteries - Book 1.epub
```

The EPUB is registered as `lotm-book-1-novel` for work `lotm-1`, the priority-1 original source for the `lotm-narrative` comparison group. It is the canonical source of truth for verification across all eight volumes of Book 1, but the file itself is ignored by Git and should not be committed.

Use the EPUB only when chronology, reveal order, reader knowledge state, relationships, or other evidence-sensitive questions require verification.

## Circle of Inevitability

The Book 2 EPUB is stored as:

```text
Circle of Inevitability.epub
```

It is registered as `lotm-book-2-novel` for work `lotm-2`, independently from Book 1's chapter and volume namespace. The package currently exposes 1,180 sequential chapter files but no machine-readable volume boundaries recognized by project tooling. Its volume catalog therefore remains pending verification; do not infer those boundaries from outside knowledge or silently reuse Book 1 ranges.

## Donghua

Season 1 subtitle files are registered as `lotm-donghua-subtitles`, a transcript derived from the priority-2 `lotm-donghua` adaptation of work `lotm-1`. They are stored locally under:

```text
Donghua_Subtitles/Season_1/
```

Current coverage includes the 13 regular Season 1 episodes. Special-episode subtitles are not currently present.

The files are UTF-8 Advanced SubStation Alpha (`.ass`) subtitles with timestamped English (US) dialogue. Their headers identify Crunchyroll/Tencent provenance and indicate that they were generated through `pysubs2`.

Use subtitles as the canonical source for the dialogue and translated on-screen text contained in this release. Subtitles alone do not verify silent visual details, framing, expressions, object placement, or other information visible only in the animation.

Do not commit subtitle files or reproduce source dialogue in project records. Preserve evidence through episode numbers, timestamps, and paraphrased summaries.
