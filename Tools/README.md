# Tools

This folder contains reusable local helpers for project maintenance and source verification.

## EPUB Search

Use `Search-Epub.ps1` for repeatable novel EPUB sweeps. The script reads the local ignored EPUB, discovers chapter files by parsing their XHTML chapter headings, strips XHTML tags, decodes HTML entities, and prints chapter-ordered counts or snippets.

The tool is for evidence acquisition. Do not copy long source passages into tracked notes. Record paraphrased evidence, chapter numbers, and reader-state conclusions.

Chapter ranges are validated from 1 to 9999, and reversed ranges fail fast. The script searches by actual chapter number across the full Book 1 EPUB rather than assuming Volume 1 filenames.

By default, the tool searches main chapter entries only. Use `-EntryType` to search or list other EPUB sections:

```text
Chapters
SideStories
Appendices
Artwork
FrontMatter
Other
All
```

Use `-Volume` to narrow chapter searches by EPUB volume, `-StartChapter` / `-EndChapter` to narrow by actual chapter number, and `-EntryNamePattern` to match internal EPUB filenames such as `*pathways*` or `*side_stories*`.

### Survey Counts

Use this first to find candidate chapters and term clusters.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 10 -EndChapter 47 -Pattern "Dunn|Captain|Nighthawk|Nightmare|Sleepless" -CountsOnly
```

Full-book or later-volume sweeps use the same global chapter numbers:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 483 -EndChapter 732 -Pattern "Gehrman|Traveler" -CountsOnly
```

You can also narrow by volume without remembering the chapter span:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Volume 3 -Pattern "Gehrman|Traveler" -CountsOnly
```

### Entry Listing

Use `-ListEntries` to inspect the EPUB's searchable sections without searching for a term.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType All -ListEntries
```

Examples for non-main sections:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType SideStories -ListEntries
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType Appendices -EntryNamePattern "*pathways*" -ListEntries
```

### Non-Chapter Searches

Search side stories, appendices, artwork text, front matter, or every XHTML section with `-EntryType`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType SideStories -Pattern "3-0782" -CountsOnly
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType Appendices -EntryNamePattern "*pathways*" -Pattern "Seer" -CountsOnly
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType All -Pattern "Evernight" -CountsOnly
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
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 1 -EndChapter 1394 -Pattern "red (chimney|smokestack)" -RegexPattern -CountsOnly
```

### JSON Output

Use `-Json` when downstream tooling or Codex needs structured results instead of human-readable chapter blocks.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 17 -EndChapter 17 -Pattern "Sleepless" -ContextLines 1 -MaxHitsPerChapter 1 -Json
```

JSON output includes `entry_type`, `volume`, `chapter`, `title`, and `source_path` fields where available.
