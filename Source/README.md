# Source

Place local source materials here. The entire `Source/` directory is ignored by Git, except that this already tracked documentation file remains in the repository.

## Novel

Place the EPUB here:

```text
Lord of Mysteries - Book 1.epub
```

The EPUB is the canonical source of truth for verification across all eight volumes of Book 1, but the file itself is ignored by Git and should not be committed.

Use the EPUB only when chronology, reveal order, reader knowledge state, relationships, or other evidence-sensitive questions require verification.

## Donghua

Season 1 subtitle files are stored locally under:

```text
Donghua_Subtitles/Season_1/
```

Current coverage includes the 13 regular Season 1 episodes. Special-episode subtitles are not currently present.

The files are UTF-8 Advanced SubStation Alpha (`.ass`) subtitles with timestamped English (US) dialogue. Their headers identify Crunchyroll/Tencent provenance and indicate that they were generated through `pysubs2`.

Use subtitles as the canonical source for the dialogue and translated on-screen text contained in this release. Subtitles alone do not verify silent visual details, framing, expressions, object placement, or other information visible only in the animation.

Do not commit subtitle files or reproduce source dialogue in project records. Preserve evidence through episode numbers, timestamps, and paraphrased summaries.
