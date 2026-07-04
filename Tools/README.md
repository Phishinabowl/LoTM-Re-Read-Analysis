# Tools

This folder contains reusable local helpers for project maintenance and source verification.

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

### Term Summary

Use `-TermSummary` when comparing competing names or aliases. It aggregates each literal pipe-separated term across the selected entries and splits counts by EPUB volume.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -TermSummary
```

Use `-Json` when downstream tooling needs structured summary rows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -TermSummary -Json
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

Use `-IncludeLineMatchCounts` with JSON hit output when a matched line may include the same term more than once or multiple competing terms.

```powershell
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
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -TermSummary
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -CountsOnly -Json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -ContextLines 2 -MaxHitsPerChapter 100 -Json -IncludeLineMatchCounts
```

Raw counts can mislead when a term is also a job, epithet, or individual label. For example, `artisan` may outnumber `savant` while mostly referring to an item-maker or a specific person, whereas `Savant pathway` is stronger evidence for the canonical pathway slug.

## EPUB Image Extraction

Use `edit_image.py --operation extract-epub-images` to list or extract EPUB image assets in actual spine/reading order. If Python/Pillow is unavailable, use `Edit-Image.ps1 -Operation ExtractEpubImages` with the same filters in PowerShell form. This is separate from text search because image-bearing XHTML entries include covers, front matter, volume covers, end-of-volume art, pathway guides, character galleries, location galleries, maps, and end-matter artwork.

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
