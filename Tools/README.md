# Tools

This folder contains reusable local helpers for project maintenance and source verification.

## EPUB Search

Use `Search-Epub.ps1` for repeatable novel EPUB sweeps. The script reads the local ignored EPUB, strips XHTML tags, decodes HTML entities, and prints chapter-ordered counts or snippets.

The tool is for evidence acquisition. Do not copy long source passages into tracked notes. Record paraphrased evidence, chapter numbers, and reader-state conclusions.

Chapter ranges are validated from 1 to 999, and reversed ranges fail fast.

### Survey Counts

Use this first to find candidate chapters and term clusters.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 10 -EndChapter 47 -Pattern "Dunn|Captain|Nighthawk|Nightmare|Sleepless" -CountsOnly
```

### Candidate Hits

Use this to inspect where matches occur without expanding much context.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 10 -EndChapter 13 -Pattern "Dunn|Nighthawk" -MaxHitsPerChapter 20
```

### Context Expansion

Use this after candidate chapters are known.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 12 -EndChapter 13 -Pattern "Dunn|Nighthawk" -ContextLines 2 -MaxHitsPerChapter 8
```

### Regex Search

By default, `-Pattern` treats `|` as a separator between literal search terms. Use `-RegexPattern` when a regular expression is genuinely needed.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 1 -EndChapter 213 -Pattern "red (chimney|smokestack)" -RegexPattern -CountsOnly
```

### JSON Output

Use `-Json` when downstream tooling or Codex needs structured results instead of human-readable chapter blocks.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 17 -EndChapter 17 -Pattern "Sleepless" -ContextLines 1 -MaxHitsPerChapter 1 -Json
```
