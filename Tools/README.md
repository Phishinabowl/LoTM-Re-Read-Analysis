# Tools

This folder contains reusable local helpers for project maintenance and source verification.

## Environment Checks

Use `Test-Python.ps1` to check whether Python is present and actually usable before selecting Python-preferred tools. It tests `python`, `python3`, and `py` in order, verifies that `--version` works, and confirms that Python can report `sys.executable`.

Run this probe once for an unfamiliar machine or fresh agent session, then treat the result as the session's Python-availability state. If Python is available, use Python-preferred tools going forward without rerunning the probe before every command. Rerun only if the environment changes, such as PATH edits, Python installation changes, a different shell, a different machine, or a failed Python launch that suggests the earlier state is stale.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-Python.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-Python.ps1 -Json
```

If the probe reports Python unavailable, use the documented PowerShell fallback scripts for that session. If Python is available but a Python tool fails, treat that as a tool/script failure rather than silently falling back.

## Temporary File Cleanup

Use `clean_temp_files.py` to remove disposable local cache directories when Python is available. It is the preferred implementation because it is portable across Windows, macOS, and Linux while matching the rest of the repository's Python-preferred tool convention.

`Clean-TempFiles.ps1` is the Windows PowerShell fallback for users who do not have Python installed.

Both scripts only target allowlisted cache directories under the repository root:

```text
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.tox
```

By default, both scripts run in dry-run mode and only list what they would delete.

Preferred Python:

```powershell
python Tools\clean_temp_files.py
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Clean-TempFiles.ps1
```

Use `--delete` / `-Delete` to actually remove the matching cache directories:

Preferred Python:

```powershell
python Tools\clean_temp_files.py --delete
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Clean-TempFiles.ps1 -Delete
```

Use `--json` / `-Json` when downstream tooling needs structured results.

## Image Manipulation

Use `edit_image.py` for repeatable local image operations when Python with Pillow is available. It is the preferred implementation because it is faster and shares one CLI for crop operations, named crop presets, and EPUB image listing/extraction.

PowerShell fallbacks are maintained for Windows users who do not have Python installed:

- `Edit-Image.ps1` mirrors crop operations, named crop presets, and EPUB image listing/extraction.

List available presets:

```powershell
python Tools\edit_image.py --list-presets
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -ListPresets
```

Use the official pathway tarot-card crop preset:

```powershell
python Tools\edit_image.py --preset PathwayTarotCard --source-image Artwork\extracted\volume-2-faceless\0023-spine-0505-pathways-pathways4.jpeg --output-image Artwork\tarot-cards\pathways\world-planter-pathway.png --force
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Preset PathwayTarotCard -SourceImage Artwork\extracted\volume-2-faceless\0023-spine-0505-pathways-pathways4.jpeg -OutputImage Artwork\tarot-cards\pathways\world-planter-pathway.png -Force
```

Use an explicit custom crop when a future image job needs different geometry:

```powershell
python Tools\edit_image.py --operation crop --source-image path\to\source.jpeg --output-image path\to\crop.png --x 24 --y 804 --width 660 --height 1168
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Operation Crop -SourceImage path\to\source.jpeg -OutputImage path\to\crop.png -X 24 -Y 804 -Width 660 -Height 1168
```

## EPUB Search

Use `search_epub.py` for repeatable novel EPUB sweeps when Python is available. It is the preferred implementation because it is faster, uses only the Python standard library, and exposes reusable functions that can later support generated indexes or frontend tooling. `Search-Epub.ps1` remains the Windows PowerShell fallback with matching behavior.

Both scripts read the local ignored EPUB, discover chapter files by parsing their XHTML chapter headings, strip XHTML tags, decode HTML entities, and print chapter-ordered counts or snippets.

The tool is for evidence acquisition. Do not copy long source passages into tracked notes. Record paraphrased evidence, chapter numbers, and reader-state conclusions.

Chapter ranges are validated from 1 to 9999, and reversed ranges fail fast. The tools search by actual chapter number across the full Book 1 EPUB rather than assuming Volume 1 filenames.

By default, the tools search main chapter entries only. Use `--entry-type` / `-EntryType` to search or list other EPUB sections:

```text
Chapters
SideStories
Appendices
Artwork
FrontMatter
Other
All
```

Use `--volume` / `-Volume` to narrow chapter searches by EPUB volume, `--start-chapter` / `--end-chapter` or `-StartChapter` / `-EndChapter` to narrow by actual chapter number, and `--entry-name-pattern` / `-EntryNamePattern` to match internal EPUB filenames such as `*pathways*` or `*side_stories*`.

### Survey Counts

Use this first to find candidate chapters and term clusters.

Preferred flags are `--counts-only` / `-CountsOnly`; the shorter aliases `--counts` / `-Counts` are also accepted.

```powershell
python Tools\search_epub.py --start-chapter 10 --end-chapter 47 --pattern "Dunn|Captain|Nighthawk|Nightmare|Sleepless" --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 10 -EndChapter 47 -Pattern "Dunn|Captain|Nighthawk|Nightmare|Sleepless" -CountsOnly
```

Full-book or later-volume sweeps use the same global chapter numbers:

```powershell
python Tools\search_epub.py --start-chapter 483 --end-chapter 732 --pattern "Gehrman|Traveler" --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 483 -EndChapter 732 -Pattern "Gehrman|Traveler" -CountsOnly
```

You can also narrow by volume without remembering the chapter span:

```powershell
python Tools\search_epub.py --volume 3 --pattern "Gehrman|Traveler" --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Volume 3 -Pattern "Gehrman|Traveler" -CountsOnly
```

### Term Summary

Use `--term-summary` / `-TermSummary` when comparing competing names or aliases. It aggregates each literal pipe-separated term across the selected entries and splits counts by EPUB volume.

Preferred flags are `--term-summary` / `-TermSummary`; the aliases `--summary-only`, `--summary`, `-SummaryOnly`, and `-Summary` are also accepted.

```powershell
python Tools\search_epub.py --pattern "savant|artisan|paragon" --term-summary
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -TermSummary
```

Use `--json` / `-Json` when downstream tooling needs structured summary rows:

```powershell
python Tools\search_epub.py --pattern "savant|artisan|paragon" --term-summary --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -TermSummary -Json
```

### Entry Listing

Use `-ListEntries` to inspect the EPUB's searchable sections without searching for a term.

```powershell
python Tools\search_epub.py --entry-type All --list-entries
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType All -ListEntries
```

Examples for non-main sections:

```powershell
python Tools\search_epub.py --entry-type SideStories --list-entries
python Tools\search_epub.py --entry-type Appendices --entry-name-pattern "*pathways*" --list-entries
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType SideStories -ListEntries
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType Appendices -EntryNamePattern "*pathways*" -ListEntries
```

### Non-Chapter Searches

Search side stories, appendices, artwork text, front matter, or every XHTML section with `--entry-type` / `-EntryType`.

```powershell
python Tools\search_epub.py --entry-type SideStories --pattern "3-0782" --counts-only
python Tools\search_epub.py --entry-type Appendices --entry-name-pattern "*pathways*" --pattern "Seer" --counts-only
python Tools\search_epub.py --entry-type All --pattern "Evernight" --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType SideStories -Pattern "3-0782" -CountsOnly
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType Appendices -EntryNamePattern "*pathways*" -Pattern "Seer" -CountsOnly
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType All -Pattern "Evernight" -CountsOnly
```

### Candidate Hits

Use this to inspect where matches occur without expanding much context.

```powershell
python Tools\search_epub.py --start-chapter 10 --end-chapter 13 --pattern "Dunn|Nighthawk" --max-hits-per-chapter 20
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 10 -EndChapter 13 -Pattern "Dunn|Nighthawk" -MaxHitsPerChapter 20
```

### Context Expansion

Use this after candidate chapters are known.

```powershell
python Tools\search_epub.py --start-chapter 12 --end-chapter 13 --pattern "Dunn|Nighthawk" --context-lines 2 --max-hits-per-chapter 8
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 12 -EndChapter 13 -Pattern "Dunn|Nighthawk" -ContextLines 2 -MaxHitsPerChapter 8
```

### Regex Search

By default, `--pattern` / `-Pattern` treats `|` as a separator between literal search terms. Python also accepts `--query`, `--text`, and `--search`, and PowerShell also accepts `-Query`, `-Text`, and `-Search`, as ergonomic aliases for the same search text. Use `--regex-pattern` / `-RegexPattern` when a regular expression is genuinely needed.

```powershell
python Tools\search_epub.py --start-chapter 1 --end-chapter 1394 --pattern "red (chimney|smokestack)" --regex-pattern --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 1 -EndChapter 1394 -Pattern "red (chimney|smokestack)" -RegexPattern -CountsOnly
```

### JSON Output

Use `-Json` when downstream tooling or Codex needs structured results instead of human-readable chapter blocks.

```powershell
python Tools\search_epub.py --start-chapter 17 --end-chapter 17 --pattern "Sleepless" --context-lines 1 --max-hits-per-chapter 1 --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 17 -EndChapter 17 -Pattern "Sleepless" -ContextLines 1 -MaxHitsPerChapter 1 -Json
```

JSON output includes `entry_type`, `volume`, `chapter`, `title`, and `source_path` fields where available.

Use `--include-line-match-counts` / `-IncludeLineMatchCounts` with JSON hit output when a matched line may include the same term more than once or multiple competing terms.

```powershell
python Tools\search_epub.py --pattern "savant|artisan" --context-lines 2 --max-hits-per-chapter 100 --json --include-line-match-counts
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan" -ContextLines 2 -MaxHitsPerChapter 100 -Json -IncludeLineMatchCounts
```

### Term Arbitration

Use this workflow when choosing a canonical page slug or primary article name from competing terms, aliases, translations, titles, or formal artwork labels.

1. Run a full-book raw count for all candidate terms.
2. Split the terms into separate counts by volume.
3. Inspect context for each candidate hit in chapter order.
4. Classify hits by usage, such as `primary subject name`, `alias/title`, `sequence name`, `ordinary-language usage`, `person/role label`, or `artwork/formal label`.
5. Prefer the slug that best matches repeated in-text subject/pathway usage, not necessarily the raw highest count.
6. Preserve alternate names in the target article alias table and in artwork-map notes.

Example:

```powershell
python Tools\search_epub.py --pattern "savant|artisan|paragon" --term-summary
python Tools\search_epub.py --pattern "savant|artisan|paragon" --counts-only --json
python Tools\search_epub.py --pattern "savant|artisan|paragon" --context-lines 2 --max-hits-per-chapter 100 --json --include-line-match-counts

powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -TermSummary
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -CountsOnly -Json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -ContextLines 2 -MaxHitsPerChapter 100 -Json -IncludeLineMatchCounts
```

Raw counts can mislead when a term is also a job, epithet, or individual label. For example, `artisan` may outnumber `savant` while mostly referring to an item-maker or a specific person, whereas `Savant pathway` is stronger evidence for the canonical pathway slug.

## EPUB Image Extraction

Use `edit_image.py --operation extract-epub-images` to list or extract EPUB image assets in actual spine/reading order. Python also accepts `extract`, `extract-images`, `list-images`, and `list-epub-images`; PowerShell accepts the same aliases through `-Operation`. If Python/Pillow is unavailable, use `Edit-Image.ps1 -Operation ExtractEpubImages` with the same filters in PowerShell form. This is separate from text search because image-bearing XHTML entries include covers, front matter, volume covers, end-of-volume art, pathway guides, character galleries, location galleries, maps, and end-matter artwork.

Both implementations assign an `image_number` based on EPUB spine order so "first image" and "next image" stay reproducible.

### List Images

```powershell
python Tools\edit_image.py --operation extract-epub-images
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Operation ExtractEpubImages
```

Useful filters:

```powershell
python Tools\edit_image.py --operation extract-epub-images --start-image-number 1 --end-image-number 12
python Tools\edit_image.py --operation extract-epub-images --volume 1 --image-type Characters
python Tools\edit_image.py --operation extract-epub-images --image-type Artwork

powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Operation ExtractEpubImages -StartImageNumber 1 -EndImageNumber 12
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Operation ExtractEpubImages -Volume 1 -ImageType Characters
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Operation ExtractEpubImages -ImageType Artwork
```

### Extract Images

Extract selected images into `.tmp/epub-images` by default:

```powershell
python Tools\edit_image.py --operation extract-epub-images --start-image-number 1 --end-image-number 4 --extract
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Operation ExtractEpubImages -StartImageNumber 1 -EndImageNumber 4 -Extract
```

Use `--output-dir` / `-OutputDir` to choose another destination, and `--json` / `-Json` when downstream tooling needs structured fields such as `image_number`, `spine_index`, `image_type`, `volume`, `xhtml_path`, `image_path`, `alt`, and `output_path`.
