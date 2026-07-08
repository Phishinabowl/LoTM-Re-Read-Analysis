# Tooling Reference

This file is the human-facing map for repository helper scripts. It records what each script is for, how Python-preferred and PowerShell-fallback versions line up when a pair exists, which switches are supported, what files are read or written, and how parity or standalone behavior was last checked.

The repository convention is:

- Prefer Python tools when Python is available.
- Keep PowerShell scripts as matching Windows fallbacks for users without Python.
- Treat generated outputs as compiled views unless a tool explicitly edits canonical files.
- Update this reference whenever a script gains, loses, or changes a switch, output, or important side effect.

## Python Environment Check

### Script

| Role | Script | Command |
| --- | --- | --- |
| Environment probe | `Tools/Test-Python.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-Python.ps1` |

Purpose: check whether the local machine has a usable Python command and the repository's required Python modules before choosing Python-preferred tools or documented PowerShell fallbacks. This is a read-only probe and has no Python pair.

### Switch Map

| Purpose | Switch | Default | Notes |
| --- | --- | --- | --- |
| Print JSON summary | `-Json` | off | Emits structured `available`, `ready`, `command`, `version`, `executable`, `requirements_*`, `checked`, and `message` fields for agent workflows. |
| Requirements file | `-RequirementsPath <path>` | `requirements-python.txt` | Checks required Python import modules derived from the repository Python dependency file. |

### Inputs

| Input | Used For |
| --- | --- |
| Local shell PATH | Finds candidate commands in order: `python`, `python3`, then `py`. |
| Candidate command `--version` output | Confirms the command launches and reports a version. |
| Candidate command `-c "import sys; print(sys.executable)"` output | Confirms Python can execute code and reports the underlying executable path. |
| `requirements-python.txt` or supplied requirements path | Defines repository Python packages to validate before treating Python tooling as fully ready. |

### Outputs And Side Effects

| Mode | Output | Side Effect |
| --- | --- | --- |
| Default | Human-readable availability, command, version, executable, and requirement status lines when Python is usable; fallback guidance when unavailable. | None. |
| JSON | Structured availability/readiness record plus the checked candidate list and requirement checks. | None. |

### Behavior Map

| Behavior | PowerShell location |
| --- | --- |
| Parse switches | top-level `param(...)` |
| Define candidate commands | top-level `$candidates = @("python", "python3", "py")` |
| Resolve candidate commands | `Get-Command` loop |
| Validate version launch | candidate `--version` call |
| Validate Python execution | candidate `-c "import sys; print(sys.executable)"` call |
| Read repository requirements | `Get-RequirementModules` |
| Validate Python modules | candidate `-c "import importlib.util ..."` calls |
| Render JSON/human output | bottom script block |

### Important Notes

- Run this once for an unfamiliar machine or fresh agent session, then treat the result as session state.
- Rerun only if the environment changes, such as PATH edits, Python installation changes, a different shell, a different machine, or a failed Python launch that suggests the earlier state is stale.
- If Python is unavailable, use the documented PowerShell fallback scripts for that session.
- If Python is available but `ready` is false because required modules are missing, install the repository dependencies with `python -m pip install -r requirements-python.txt` before using Python helpers that need those modules.
- If Python is available and ready but a Python helper fails, treat that as a helper failure rather than silently falling back.
- Keep PowerShell fallback scripts compatible with Windows PowerShell 5.1 unless a tool explicitly documents a PowerShell 7 requirement.

### Check Recipe

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-Python.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-Python.ps1 -Json
python -m pip install -r requirements-python.txt
```

Last mapped: 2026-07-07.

Last check: 2026-07-07. Normal and JSON modes ran successfully on this machine. The probe detected `python`, `Python 3.14.5`, executable `C:\Users\ptseb\AppData\Local\Python\pythoncore-3.14-64\python.exe`, and `ready: true` after validating `PyYAML` through the `yaml` import module.

## PowerShell Environment Check

### Script

| Role | Script | Command |
| --- | --- | --- |
| Environment probe | `Tools/Test-PowerShell.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-PowerShell.ps1` |

Purpose: check whether the local PowerShell environment has repository-required modules from `requirements-powershell.txt`. This is a read-only probe and has no Python pair.

### Switch Map

| Purpose | Switch | Default | Notes |
| --- | --- | --- | --- |
| Print JSON summary | `-Json` | off | Emits structured `ready`, `powershell_version`, `edition`, `executable`, `requirements_path`, `modules`, and `message` fields. |
| Requirements file | `-RequirementsPath <path>` | `requirements-powershell.txt` | Checks required PowerShell modules from the repository dependency file. |

### Inputs

| Input | Used For |
| --- | --- |
| `$PSVersionTable` | Reports PowerShell version and edition. |
| `requirements-powershell.txt` or supplied requirements path | Defines required PowerShell modules. |
| `Get-Module -ListAvailable` | Checks whether each required module is installed. |

### Outputs And Side Effects

| Mode | Output | Side Effect |
| --- | --- | --- |
| Default | Human-readable PowerShell version, executable, requirements path, and module status lines. | None. |
| JSON | Structured readiness record plus module checks. | None. |

### Important Notes

- Run this once for an unfamiliar machine or fresh agent session, then treat the result as session state.
- Rerun only if the environment changes, such as module installation changes, a different PowerShell edition, a different machine, or a failed fallback command that suggests the earlier state is stale.
- If required modules are missing, install the repository PowerShell dependencies before using fallback features that need those modules.
- `CurrentUser` module installs are usually sufficient. Maintainers who prefer machine-wide module availability may use `-Scope AllUsers` from an elevated PowerShell session.

### Check Recipe

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-PowerShell.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Test-PowerShell.ps1 -Json
Install-Module powershell-yaml -Scope CurrentUser -Force -AllowClobber
```

Last mapped: 2026-07-07.

Last check: 2026-07-07. Normal JSON mode ran successfully on this machine with Windows PowerShell 5.1.19041.7417 and detected `powershell-yaml` 0.4.12 from `C:\Program Files\WindowsPowerShell\Modules\powershell-yaml\0.4.12\powershell-yaml.psd1`.

## Temporary File Cleanup

### Script Pair

| Role | Script | Command |
| --- | --- | --- |
| Preferred implementation | `Tools/clean_temp_files.py` | `python Tools\clean_temp_files.py` |
| Windows fallback | `Tools/Clean-TempFiles.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Clean-TempFiles.ps1` |

Purpose: find and optionally remove allowlisted local cache directories under the repository root. This tool is for disposable tool/runtime artifacts only, not project source files.

### Switch Map

| Purpose | Python switch | PowerShell switch | Default | Notes |
| --- | --- | --- | --- | --- |
| Actually delete cache folders/artifacts | `--delete` | `-Delete` | off | Without this switch, both scripts run in dry-run mode and only report matching paths. |
| Include ignored `.tmp` artifacts | `--include-tmp` | `-IncludeTmp` | off | Adds direct children of repository `.tmp/` to the cleanup target list. The `.tmp` root itself is left in place. |
| Include exact scoped `.tmp` path | `--tmp-path <path>` | `-TmpPath <path>[,<path>]` | none | Adds only the specified existing path(s), and only when they resolve under repository `.tmp/`. Intended for automatic cleanup of artifacts created by the current tool run. |
| Print JSON summary | `--json` | `-Json` | off | Emits structured fields for `repo_root`, `delete`, `allowed_directory_names`, `count`, and `results`. |
| Show CLI help | `--help` | n/a | n/a | Python exposes argparse help. The PowerShell fallback exposes switches through the script `param(...)` block. |

### Inputs

| Input | Used For |
| --- | --- |
| Repository root inferred from the script location | Search boundary. Neither script accepts an alternate root. |
| Recursive directory walk under the repository root | Finds allowlisted cache directory names. |

### Allowlist

By default, only directories with these exact names are considered:

- `.mypy_cache`
- `.pytest_cache`
- `.ruff_cache`
- `.tox`
- `__pycache__`

With `--include-tmp` / `-IncludeTmp`, direct children of the repository `.tmp/` folder are also considered. With `--tmp-path` / `-TmpPath`, only exact existing paths under repository `.tmp/` are considered. Both scripts verify that a resolved match remains inside the repository root before reporting or deleting it, and scoped tmp paths must also remain inside `.tmp/` without targeting `.tmp/` itself.

### Outputs And Side Effects

| Mode | Output | Side Effect |
| --- | --- | --- |
| Default dry run | Human-readable `Would delete: <path>` lines, or `No allowlisted cache directories found.` | None. |
| JSON dry run | JSON summary with `status: would_delete` rows. | None. |
| Delete | Human-readable `Deleted: <path>` lines, or JSON rows with `status: deleted`. | Removes every allowlisted cache directory found under the repository root, direct `.tmp/` children only when explicitly included, and exact scoped `.tmp` paths when provided. |

### Behavior Map

| Behavior | Python function | PowerShell function |
| --- | --- | --- |
| Parse CLI/switches | `main` | top-level `param(...)` |
| Resolve repository root | `get_repo_root` | top-level `$repoRoot` |
| Guard paths under repo | `is_within_repo` | `Test-IsWithinRepo` |
| Find cache directories | `find_cache_dirs` | top-level `Get-ChildItem ... Where-Object` pipeline |
| Find `.tmp` artifacts | `find_tmp_artifacts` | top-level `.tmp` child listing when `-IncludeTmp` is set |
| Find scoped `.tmp` artifacts | `find_scoped_tmp_artifacts`, `is_within_tmp` | `-TmpPath` loop, `Test-IsWithinTmp` |
| Delete cache directories | `clean_cache_dirs` | top-level `Remove-Item` loop |
| Render JSON/human output | `main` | bottom script block |

### Important Differences

- Python has built-in `--help`; PowerShell switch discovery is through the `param(...)` block and this reference.
- Python sorts matches by lowercase path string. PowerShell sorts matches by `FullName`. On Windows, these produce the same order for normal repository paths.

### Parity Check Recipe

Use ignored `.tmp/` folders to create disposable cache targets.

```powershell
New-Item -ItemType Directory -Force -Path .tmp\cleanup-parity\Tools\__pycache__
New-Item -ItemType Directory -Force -Path .tmp\cleanup-parity\Nested\.pytest_cache
New-Item -ItemType Directory -Force -Path .tmp\cleanup-parity\Nested\.ruff_cache

python Tools\clean_temp_files.py --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Clean-TempFiles.ps1 -Json

python Tools\clean_temp_files.py --include-tmp --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Clean-TempFiles.ps1 -IncludeTmp -Json

python Tools\clean_temp_files.py --tmp-path .tmp\cleanup-parity --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Clean-TempFiles.ps1 -TmpPath .tmp\cleanup-parity -Json

python Tools\clean_temp_files.py --delete --json

New-Item -ItemType Directory -Force -Path .tmp\cleanup-parity\Tools\__pycache__
New-Item -ItemType Directory -Force -Path .tmp\cleanup-parity\Nested\.pytest_cache
New-Item -ItemType Directory -Force -Path .tmp\cleanup-parity\Nested\.ruff_cache

powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Clean-TempFiles.ps1 -Delete -Json
```

Automatic tool cleanup should prefer `--tmp-path ... --delete` / `-TmpPath ... -Delete` for exact paths created by the current run. Use `--include-tmp --delete` / `-IncludeTmp -Delete` only when ignored local test outputs under `.tmp/` are no longer needed. This is intentionally opt-in so parity runs that write inspectable outputs under `.tmp/` are not deleted immediately by the tools that created them.

Expected non-semantic differences:

- JSON whitespace from Python `json.dumps` versus PowerShell `ConvertTo-Json`.

Last mapped: 2026-07-07.

Last parity check: 2026-07-07. Dry-run JSON matched semantically for three test cache directories under `.tmp/cleanup-parity/`. Delete-mode JSON matched semantically after recreating the same three test directories between Python and PowerShell runs. Both scripts reported the same allowlist, target paths, counts, and statuses.

## Image Manipulation

### Script Pair

| Role | Script | Command |
| --- | --- | --- |
| Preferred implementation | `Tools/edit_image.py` | `python Tools\edit_image.py` |
| Windows fallback | `Tools/Edit-Image.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1` |

Purpose: run repeatable local image operations. Current operations are fixed-geometry image cropping, named crop presets for official pathway guide assets, and EPUB image listing/extraction in spine order.

### Switch Map

| Purpose | Python switch | PowerShell switch | Default | Notes |
| --- | --- | --- | --- | --- |
| Select operation | `--operation <name>` | `-Operation <name>` | `crop` / `Crop` | Supported operation family: crop or EPUB image listing/extraction. |
| Select crop preset | `--preset <name>` | `-Preset <name>` | none | Presets fill operation, `x`, `y`, `width`, and `height`. |
| List crop presets | `--list-presets` | `-ListPresets` | off | Prints preset names and geometry without reading or writing images. |
| Source image for crop | `--source-image <path>` | `-SourceImage <path>` | none | Required for crop mode unless listing presets. |
| Output image for crop | `--output-image <path>` | `-OutputImage <path>` | none | Required for crop mode unless listing presets. |
| Crop left coordinate | `--x <number>` | `-X <number>` | none / `-1` | Must be non-negative. Presets supply this value. |
| Crop top coordinate | `--y <number>` | `-Y <number>` | none / `-1` | Must be non-negative. Presets supply this value. |
| Crop width | `--width <number>` | `-Width <number>` | none / `-1` | Must be positive. Presets supply this value. |
| Crop height | `--height <number>` | `-Height <number>` | none / `-1` | Must be positive. Presets supply this value. |
| Overwrite crop output | `--force` | `-Force` | off | Required when the crop output path already exists. |
| EPUB path | `--epub-path <path>` | `-EpubPath <path>` | `Source/Lord of Mysteries - Book 1.epub` | Used only for EPUB image listing/extraction. |
| EPUB extraction output directory | `--output-dir <path>` | `-OutputDir <path>` | `.tmp/epub-images` | Used only when `--extract` / `-Extract` is set. |
| First image number | `--start-image-number <number>` | `-StartImageNumber <number>` | `1` | EPUB image numbers are 1-based. |
| Last image number | `--end-image-number <number>` | `-EndImageNumber <number>` | `9999` | Must be greater than or equal to the start image number. |
| Filter by EPUB volume | `--volume <number>` | `-Volume <number>[,<number>]` | none | Python accepts repeated `--volume`; PowerShell accepts an integer array. |
| Filter by image type | `--image-type <type>` | `-ImageType <type>[,<type>]` | `All` | Python accepts repeated `--image-type`; PowerShell accepts a string array. |
| Filter by XHTML entry name/path | `--entry-name-pattern <glob>` | `-EntryNamePattern <glob>` | none | Matches both internal XHTML path and leaf filename. |
| Filter by image name/path | `--image-name-pattern <glob>` | `-ImageNamePattern <glob>` | none | Matches both internal image path and leaf filename. |
| Extract matching EPUB images | `--extract` | `-Extract` | off | Without this switch, EPUB mode lists matching images only. |
| Print JSON | `--json` | `-Json` | off | EPUB mode emits image rows. Crop mode still prints a human-readable line. |
| Show CLI help | `--help` | n/a | n/a | Python exposes argparse help. The PowerShell fallback exposes switches through the script `param(...)` block. |

### Operation Aliases

Crop:

- Python: `crop`, `Crop`
- PowerShell: `Crop` and any case variant of `crop`

EPUB image listing/extraction:

- Python: `extract`, `Extract`, `extractepubimages`, `ExtractEpubImages`, `extract-epub-images`, `extract-images`, `Extract-Images`, `list-epub-images`, `List-Epub-Images`, `listepubimages`, `list-images`, `List-Images`
- PowerShell: same names case-insensitively

### Presets

| Preset | Aliases | Geometry | Purpose |
| --- | --- | --- | --- |
| `PathwayTarotCard` | `pathwaytarotcard`, `pathway-tarot-card`, `pathway-tarot`, `tarot-card` | `x=24 y=804 width=660 height=1168` | Official EPUB pathway guide tarot-card crop. |
| `PathwaySymbol` | `pathwaysymbol`, `pathway-symbol`, `pathway-symbol-crop`, `symbol` | `x=472 y=305 width=486 height=486` | Official EPUB pathway guide central symbol crop. |

### EPUB Image Types

Supported image-type filters:

- `Cover`
- `FrontMatter`
- `VolumeCover`
- `EndOfVolume`
- `Pathways`
- `Characters`
- `Locations`
- `Artwork`
- `Map`
- `BackCover`
- `Other`
- `All`

### Inputs

| Input | Used For |
| --- | --- |
| Source image path | Crop mode. |
| `Source/Lord of Mysteries - Book 1.epub` or supplied EPUB path | EPUB image listing/extraction mode. |
| EPUB `OEBPS/content.opf` | Spine-order image discovery. |
| EPUB XHTML entries | Title, image path, alt text, volume, and type inference. |

### Outputs And Side Effects

| Mode | Output | Side Effect |
| --- | --- | --- |
| `--list-presets` / `-ListPresets` | Plain-text preset lines. | None. |
| Crop | Human-readable write summary. | Writes one cropped image to `--output-image` / `-OutputImage`. |
| EPUB list | Human-readable rows or JSON image rows. | None. |
| EPUB extract | Human-readable rows or JSON image rows with `output_path`. | Copies selected image entries to `--output-dir` / `-OutputDir`. |

Image extraction and bulk crop staging should normally stay under ignored local folders such as `.tmp/` or `Artwork/Source/`. Only deliberately selected page-ready assets under tracked locations should be committed.

### Behavior Map

| Behavior | Python function | PowerShell function |
| --- | --- | --- |
| Parse CLI/switches | `build_parser`, `main` | top-level `param(...)`, bottom `switch` |
| Normalize operation names | `normalize_operation` | `Resolve-OperationName` |
| Normalize preset names | `normalize_preset` | `Resolve-PresetName` |
| List presets | `list_presets` | `Show-Presets` |
| Validate/resolve crop geometry | `resolve_crop` | `Invoke-Crop` |
| Crop image | `crop_image` | `Invoke-Crop` |
| Determine output image format | Pillow save via output extension | `Get-OutputImageFormat` |
| Resolve EPUB-relative image paths | `epub_relative_path` | `Get-RelativePath` |
| Read XHTML title | `xhtml_title` | `Get-XhtmlTitle` |
| Parse image tags | `ImgTagParser.find` | `Get-ImgTags` |
| Infer EPUB volume | `volume_from_href` | `Get-VolumeFromHref` |
| Infer image type | `image_type` | `Get-ImageType` |
| Apply image filters | `selected_image` | `Test-SelectedImage` |
| Discover EPUB images | `discover_epub_images` | `Invoke-ExtractEpubImages` |
| Copy EPUB image entries | `extract_epub_images` | `Copy-ZipEntry`, `Invoke-ExtractEpubImages` |
| Render JSON rows | `extract_epub_images` | `Convert-ImageToJsonObject`, `Invoke-ExtractEpubImages` |

### Important Differences

- Python crop mode depends on Pillow. PowerShell crop mode depends on `System.Drawing`.
- Raw PNG/JPEG byte output from crop mode may differ between Pillow and `System.Drawing` even when dimensions and pixels match. Compare crop parity by image dimensions and pixel data, not raw hash.
- Python has built-in `--help`; PowerShell switch discovery is through the `param(...)` block and this reference.
- PowerShell parameter validation rejects image numbers outside `1..9999` before script logic runs. Python validates the same 1-based boundary inside EPUB mode.

### Parity Check Recipe

List presets:

```powershell
python Tools\edit_image.py --list-presets
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -ListPresets
```

List EPUB images:

```powershell
python Tools\edit_image.py --operation list-images --start-image-number 1 --end-image-number 5 --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Operation List-Images -StartImageNumber 1 -EndImageNumber 5 -Json
```

Extract one EPUB image:

```powershell
python Tools\edit_image.py --operation ExtractEpubImages --start-image-number 1 --end-image-number 1 --output-dir .tmp\image-parity\python-extract --extract --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Operation ExtractEpubImages -StartImageNumber 1 -EndImageNumber 1 -OutputDir .tmp\image-parity\powershell-extract -Extract -Json
```

Crop a synthetic source image and compare dimensions/pixels:

```powershell
python Tools\edit_image.py --operation crop --source-image .tmp\image-parity\source.png --output-image .tmp\image-parity\python-crop.png --x 3 --y 4 --width 7 --height 6 --force
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Edit-Image.ps1 -Operation Crop -SourceImage .tmp\image-parity\source.png -OutputImage .tmp\image-parity\powershell-crop.png -X 3 -Y 4 -Width 7 -Height 6 -Force
```

Expected non-semantic differences:

- JSON whitespace from Python `json.dumps` versus PowerShell `ConvertTo-Json`.
- Extracted `output_path` values differ when different output directories are used.
- Crop command wording uses `crop` in Python output and `Crop` in PowerShell output.

Last mapped: 2026-07-07.

Last parity check: 2026-07-07. Preset listing matched exactly. EPUB JSON listing for images 1-5 matched semantically. Single-image EPUB extraction matched semantically after normalizing `output_path`, and the extracted image hashes matched byte-for-byte. Synthetic crop outputs both produced `7x6` images with matching pixel data.

## EPUB Search

### Script Pair

| Role | Script | Command |
| --- | --- | --- |
| Preferred implementation | `Tools/search_epub.py` | `python Tools\search_epub.py` |
| Windows fallback | `Tools/Search-Epub.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1` |

Purpose: search the local ignored Lord of Mysteries EPUB for source verification. The tool reads EPUB XHTML entries, strips markup, classifies searchable sections, and returns chapter-ordered counts, snippets, context, summaries, or entry listings. It is read-only.

### Switch Map

| Purpose | Python switch | PowerShell switch | Default | Notes |
| --- | --- | --- | --- | --- |
| EPUB path | `--epub-path <path>` | `-EpubPath <path>` | `Source/Lord of Mysteries - Book 1.epub` | Local ignored EPUB source. |
| First chapter | `--start-chapter <number>` | `-StartChapter <number>` | `1` | Must be at least 1. Applies only to entries with chapter numbers. |
| Last chapter | `--end-chapter <number>` | `-EndChapter <number>` | `9999` | Must be greater than or equal to start chapter. |
| Filter by EPUB volume | `--volume <number>` | `-Volume <number>[,<number>]` | none | Python accepts repeated `--volume`; PowerShell accepts an integer array. |
| Filter by entry type | `--entry-type <type>` | `-EntryType <type>[,<type>]` | `Chapters` | Python accepts repeated `--entry-type`; PowerShell accepts a string array. |
| Filter by internal entry path/name | `--entry-name-pattern <glob>` | `-EntryNamePattern <glob>` | none | Matches both internal XHTML path and leaf filename. |
| Search pattern | `--pattern <text>` | `-Pattern <text>` | none | Required unless listing entries. Literal multi-term searches use `|` separators. |
| Search pattern aliases | `--query`, `--text`, `--search` | `-Query`, `-Text`, `-Search` | n/a | Aliases for the same search text. |
| Context lines around hits | `--context-lines <number>` | `-ContextLines <number>` | `0` | Must be non-negative. |
| Max hits shown per chapter/entry | `--max-hits-per-chapter <number>` | `-MaxHitsPerChapter <number>` | `50` | Must be non-negative. Name is historical; it also applies to non-chapter entries. |
| Counts-only mode | `--counts-only` | `-CountsOnly` | off | Counts terms per matching entry instead of returning snippets. |
| Counts-only alias | `--counts` | `-Counts` | n/a | Alias for counts-only mode. |
| Term summary mode | `--term-summary` | `-TermSummary` | off | Aggregates each term across selected entries and splits by EPUB volume. |
| Term summary aliases | `--summary-only`, `--summary` | `-SummaryOnly`, `-Summary` | n/a | Aliases for term summary mode. |
| Include per-line term counts | `--include-line-match-counts` | `-IncludeLineMatchCounts` | off | JSON hit mode only. Adds `line_term_counts`. |
| Treat pattern as regex | `--regex-pattern` | `-RegexPattern` | off | Pattern is used as one regex instead of splitting literal terms on `|`. |
| Case-sensitive matching | `--case-sensitive` | `-CaseSensitive` | off | Default matching is case-insensitive. |
| Print JSON | `--json` | `-Json` | off | Emits structured rows for downstream tooling. |
| List EPUB entries | `--list-entries` | `-ListEntries` | off | Lists selected entries without requiring a search pattern. Cannot combine with term summary. |
| Show CLI help | `--help` | n/a | n/a | Python exposes argparse help. The PowerShell fallback exposes switches through the script `param(...)` block. |

### Entry Types

Supported entry-type filters:

- `Chapters`
- `SideStories`
- `Appendices`
- `Artwork`
- `FrontMatter`
- `Other`
- `All`

### Inputs

| Input | Used For |
| --- | --- |
| Local EPUB file | Source XHTML discovery and search. |
| EPUB `OEBPS/Text/*.xhtml` entries | Search corpus. |
| XHTML chapter headings and filenames | Chapter number, volume, entry type, and title inference. |

### Outputs And Side Effects

| Mode | Output | Side Effect |
| --- | --- | --- |
| `--list-entries` / `-ListEntries` | Human-readable entry rows or JSON entry rows. | None. |
| Counts-only | Human-readable `term=count` rows or JSON count rows. | None. |
| Term summary | Human-readable table or JSON summary rows. | None. |
| Hit/snippet search | Human-readable snippets or JSON hit rows, optionally with context and line match counts. | None. |

This tool must not be used to copy long source passages into tracked notes. Record paraphrased evidence, chapter numbers, and reader-state conclusions.

### Behavior Map

| Behavior | Python function | PowerShell function |
| --- | --- | --- |
| Parse CLI/switches | `build_parser`, `main` | top-level `param(...)` |
| Configure UTF-8 output | `configure_output_encoding` | top-level `$OutputEncoding` / `[Console]::OutputEncoding` |
| Convert XHTML to searchable lines | `convert_xhtml_to_lines` | `Convert-XhtmlToLines` |
| Build search regexes | `make_regex`, `make_single_regex` | `New-SearchRegex` |
| Format snippets | `format_snippet` | `Format-Snippet` |
| Find matched terms | `matched_terms` | `Get-MatchedTerms` |
| Count line-level term matches | `term_match_counts` | `Get-TermMatchCounts` |
| Infer entry title | `get_entry_title` | `Get-EntryTitle` |
| Infer entry metadata | `entry_metadata` | `Get-EntryMetadata` |
| Read EPUB entries | `get_epub_entries` | `Get-EpubEntries` |
| Apply entry filters | `selected_entry` | `Test-SelectedEntry` |
| Format document labels | `document_label` | `Get-DocumentLabel` |
| Render entry JSON objects | `document_json` | `Convert-DocumentToJsonObject` |
| Split literal search terms | `split_terms` | top-level `$terms` construction |
| Build term summary rows | `term_summary_rows` | `New-TermSummaryRows` |
| Format term summary table | `format_term_summary_table` | `Format-TermSummaryTable` |
| Count terms per document | `count_terms` | top-level `$termCounts` loop |
| Search documents and render hits | `search_documents` | bottom search loop |

### Important Differences

- Python has built-in `--help`; PowerShell switch discovery is through the `param(...)` block and this reference.
- Python validates non-negative context and max-hit values through argparse types. PowerShell validates them with `ValidateRange(0, 9999)`.
- JSON whitespace differs between Python `json.dumps` and PowerShell `ConvertTo-Json`.

### Parity Check Recipe

List all EPUB entries:

```powershell
python Tools\search_epub.py --entry-type All --list-entries --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType All -ListEntries -Json
```

Counts-only chapter search:

```powershell
python Tools\search_epub.py --start-chapter 1 --end-chapter 5 --pattern "Klein|Zhou" --counts-only --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 1 -EndChapter 5 -Pattern "Klein|Zhou" -CountsOnly -Json
```

Term summary:

```powershell
python Tools\search_epub.py --start-chapter 1 --end-chapter 10 --pattern "Klein|Zhou" --term-summary --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 1 -EndChapter 10 -Pattern "Klein|Zhou" -TermSummary -Json
```

Context hits with line counts:

```powershell
python Tools\search_epub.py --start-chapter 1 --end-chapter 1 --pattern "Klein|Zhou" --context-lines 1 --max-hits-per-chapter 3 --include-line-match-counts --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 1 -EndChapter 1 -Pattern "Klein|Zhou" -ContextLines 1 -MaxHitsPerChapter 3 -IncludeLineMatchCounts -Json
```

Regex and case-sensitive search:

```powershell
python Tools\search_epub.py --start-chapter 1 --end-chapter 3 --pattern "Klein\b" --regex-pattern --case-sensitive --counts-only --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -StartChapter 1 -EndChapter 3 -Pattern "Klein\b" -RegexPattern -CaseSensitive -CountsOnly -Json
```

Non-chapter appendix search:

```powershell
python Tools\search_epub.py --entry-type Appendices --entry-name-pattern "*pathways*" --pattern "Pathway|Sequence|Seer" --counts-only --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Search-Epub.ps1 -EntryType Appendices -EntryNamePattern "*pathways*" -Pattern "Pathway|Sequence|Seer" -CountsOnly -Json
```

Expected non-semantic differences:

- JSON whitespace from Python `json.dumps` versus PowerShell `ConvertTo-Json`.
- Error wording/format differs because Python errors come from argparse and PowerShell errors come from parameter validation or thrown exceptions.

Last mapped: 2026-07-07.

Last parity check: 2026-07-07. JSON outputs matched semantically for full entry listing (`1553` entries), counts-only chapter search (`9` rows), term summary (`2` rows), context hits with line counts (`3` rows), regex case-sensitive search (`3` rows), empty appendix filter (`0` rows), and non-empty appendix search (`20` rows).

## Visualization Graph Workflow

### Script Pair

| Role | Script | Command |
| --- | --- | --- |
| Preferred implementation | `Visualization/visualize.py` | `python Visualization\visualize.py` |
| Windows fallback | `Visualization/visualize.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1` |

Purpose: generate repository Mermaid graph views from canonical graph inputs, validate generated/manual Mermaid files, render Mermaid files to image outputs through Mermaid CLI, update the visualization refresh report, and write semantic graph snapshots.

### Switch Map

| Purpose | Python switch | PowerShell switch | Default | Notes |
| --- | --- | --- | --- | --- |
| Select mode | `--mode <mode>` | `-Mode <mode>` | `Refresh` | Modes normalize to refresh, render, or validate. |
| Select mode alias | n/a | `-Action <mode>` | n/a | PowerShell alias for `-Mode`. |
| Input Mermaid file for render mode | `--input-path <path>` | `-InputPath <path>` | none | Required for render mode. |
| Input aliases | `--input`, `--graph` | `-Input`, `-Graph` | n/a | Aliases for input path. |
| Render output path(s) | `--output-path <path>` | `-OutputPath <path>[,<path>]` | none | Render mode defaults to SVG and PNG under `Visualization/rendered/` when omitted. Python accepts repeated `--output-path`; PowerShell accepts a string array. |
| Output aliases | `--output`, `--out` | `-Output`, `-Out` | n/a | Aliases for output path. |
| Render settings path | `--settings-path <path>` | `-SettingsPath <path>` | `Visualization/config/render-settings.json` | Controls configured views, render settings, report path, snapshot path, validation settings, and output paths. |
| Settings alias | `--settings` | `-Settings` | n/a | Alias for settings path. |
| Skip rendering during refresh | `--skip-render` | `-SkipRender` | off | Refreshes Mermaid graph sources, report, and snapshot without rendering PNG/SVG outputs. |
| Skip-render alias | `--no-render` | `-NoRender` | n/a | Alias for skip render. |
| Show CLI help | `--help` | n/a | n/a | Python exposes argparse help. The PowerShell fallback exposes switches through the script `param(...)` block. |

### Mode Aliases

Refresh:

- Python: `refresh`, `Refresh`, `update`, `Update`, `generate`, `Generate`
- PowerShell: same names case-insensitively

Render:

- Python: `render`, `Render`, `manual-render`, `Manual-Render`, `pure-render`, `Pure-Render`
- PowerShell: same names case-insensitively

Validate:

- Python: `validate`, `Validate`, `check`, `Check`, `test`, `Test`
- PowerShell: same names case-insensitively

### Inputs

| Input | Used For |
| --- | --- |
| `Visualization/config/render-settings.json` or supplied settings path | Configured views, output paths, validation rules, render dimensions, and report/snapshot destinations. |
| `Visualization/config/puppeteer-config.json` or settings-defined puppeteer config | Browser launch settings for Mermaid CLI rendering. |
| `Glossary_Threads/**/*.md` | Node metadata, `Subject Visible From`, status, type-specific data blocks, first-appearance display rows, and Relationship Seeds. |
| `CURRENT_STATE.md` | Pending graph node report lines. |
| Repository Markdown files | Broken link scan for refresh report hygiene. |
| Existing Mermaid files from configured view inputs | Validate mode checks existing graph class/layout hygiene. |
| Render-mode input Mermaid file | Manual/pure render mode. |

### Outputs And Side Effects

| Mode | Output | Side Effect |
| --- | --- | --- |
| Refresh | Generated Mermaid graph files, refresh report, semantic snapshot, and optionally rendered image outputs. | Mutates every configured view input path, report path, snapshot path, and rendered outputs unless paths are redirected in a supplied settings file. |
| Refresh with skip render | Generated Mermaid graph files, refresh report, semantic snapshot. | Does not render PNG/SVG outputs. Still mutates configured graph/report/snapshot paths. |
| Validate | Human-readable validation summary. | Does not mutate configured graph/report/snapshot/rendered outputs. Generates temporary graph files under the system temp directory and removes them. |
| Render | Human-readable render progress. | Writes rendered output files to explicit `--output-path` / `-OutputPath` values or default `Visualization/rendered/<input-name>.svg/.png`. |

Refresh mode should be treated as a canonical generated-artifact update unless a temporary settings file redirects all outputs into ignored paths.

### Behavior Map

| Behavior | Python function | PowerShell function |
| --- | --- | --- |
| Parse CLI/switches | `parse_args`, `main` | top-level `param(...)`, `Resolve-VisualizationMode`, bottom mode dispatch |
| Resolve repository paths | `resolve_repo_path` | `Resolve-RepoPath` |
| Read/write text files | `read_text`, `write_text` | `Get-Content`, `Set-Content` call sites |
| Compute render size | `get_mermaid_render_size` | `Get-MermaidRenderSize` |
| Validate Mermaid class coverage | `get_mermaid_class_validation`, `assert_mermaid_class_validation` | `Get-MermaidClassValidation`, `Assert-MermaidClassValidation` |
| Validate Mermaid layout hygiene | `get_mermaid_layout_validation`, `assert_mermaid_layout_validation` | `Get-MermaidLayoutValidation`, `Assert-MermaidLayoutValidation` |
| Invoke Mermaid CLI rendering | `invoke_mermaid_render` | `Invoke-MermaidRender` |
| Parse glossary nodes | `read_glossary_nodes` | `Read-GlossaryNodes` |
| Parse anonymized first-appearance displays | `read_first_appearance_graph_displays` | `Read-FirstAppearanceGraphDisplays` |
| Parse Relationship Seeds | `read_relationship_seeds`, `extract_relationship_yaml` | `Read-RelationshipSeeds`, `Get-RelationshipYaml` |
| Parse data-block projections | `read_data_projections`, `make_availability_entry`, `projection_keys_for_row` | `Read-DataProjections`, `New-AvailabilityEntry`, `Get-ProjectionKeysForRow` |
| Filter nodes by reader boundary | `filter_nodes_for_boundary`, `parse_subject_visible_from`, `position_is_visible` | `Select-NodesForBoundary`, `Convert-SubjectVisibleFrom`, `Test-PositionVisible` |
| Add anonymized display nodes | `get_anonymized_node_displays`, `graph_display_is_visible`, `node_is_visible_at_boundary` | `Get-AnonymizedNodeDisplays`, `Test-GraphDisplayVisible`, `Test-NodeVisibleAtBoundary` |
| Filter/project relationships by boundary | `filter_relationships_for_boundary`, `choose_current_availability`, `relationship_strength` | `Select-RelationshipsForBoundary`, `Select-CurrentAvailability`, `Get-RelationshipScore` |
| Find missing visible endpoints | `get_missing_relationship_endpoints` | `Get-MissingRelationshipEndpoints` |
| Format relationship labels | `format_relationship_label`, `format_relationship_node_label`, `format_availability_history` | `Format-RelationshipLabel`, `Format-RelationshipNodeLabel`, `Format-AvailabilityHistory` |
| Write generated Mermaid graph | `write_mermaid_graph` | `Write-MermaidGraph` |
| Regenerate configured graph views | `update_mermaid_graphs` | `Update-MermaidGraphs` |
| Compute graph stats | `get_graph_stats` | `Get-GraphStats` |
| Compare snapshots | `read_previous_snapshot`, `compare_string_set`, `get_duplicate_relationships`, `get_changed_relationships` | `Read-PreviousSnapshot`, `Compare-StringSet`, `Get-DuplicateRelationships`, `Get-ChangedRelationships` |
| Gather report hygiene | `get_pending_graph_nodes`, `get_broken_markdown_links` | `Get-PendingGraphNodes`, `Get-BrokenMarkdownLinks` |
| Update report section | `update_report_section` | `Update-ReportSection` |
| Refresh workflow | `invoke_refresh_mode` | `Invoke-RefreshMode` |
| Render workflow | `invoke_render_mode` | `Invoke-ManualRenderMode` |
| Validate workflow | `invoke_validate_mode` | `Invoke-ValidateMode` |
| Clean disposable Python caches | `clean_disposable_caches` | n/a |

### Important Differences

- Python invokes `Tools/clean_temp_files.py` at the end of normal runs to remove transient Python cache folders. The PowerShell fallback does not call cleanup because it does not create Python cache folders.
- Python has built-in `--help`; PowerShell switch discovery is through the `param(...)` block and this reference.
- Python accepts repeated `--output-path` values. PowerShell accepts one or more `-OutputPath` values as a string array.
- PowerShell also exposes `-Action` as an alias for `-Mode`; Python does not have an `--action` alias.
- Generated text may differ by encoding marker or newline style depending on shell/runtime, but generated graph/report/snapshot semantics should match.
- Rendered SVG/PNG byte output can vary with Mermaid CLI, browser, and runtime details. Render parity should confirm successful output, expected labels, dimensions/settings, and nonzero files; raw image hashes are not the main contract.

### Parity Check Recipe

For refresh parity, copy `Visualization/config/render-settings.json` and rewrite every output path into ignored `.tmp/visualization-parity/...` folders before running refresh. Do not run canonical refresh parity against the live settings unless you intend to update repository artifacts.

Validate mode:

```powershell
python Visualization\visualize.py --mode Validate
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Validate
```

No-render refresh mode with redirected settings:

```powershell
python Visualization\visualize.py --mode Refresh --settings-path .tmp\visualization-parity\python\render-settings.json --skip-render
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Refresh -SettingsPath .tmp\visualization-parity\powershell\render-settings.json -SkipRender
```

Manual render mode with a tiny temporary Mermaid file:

```powershell
python Visualization\visualize.py --mode Render --settings-path .tmp\visualization-parity\python\render-settings.json --input-path .tmp\visualization-parity\render\tiny.mmd --output-path .tmp\visualization-parity\render\python-tiny.svg
powershell -NoProfile -ExecutionPolicy Bypass -File Visualization\visualize.ps1 -Mode Render -SettingsPath .tmp\visualization-parity\powershell\render-settings.json -InputPath .tmp\visualization-parity\render\tiny.mmd -OutputPath .tmp\visualization-parity\render\powershell-tiny.svg
```

Expected non-semantic differences:

- timestamps in reports and snapshots;
- temporary output root paths in reports, snapshots, and settings;
- JSON whitespace/formatting from Python `json.dumps` versus PowerShell `ConvertTo-Json`;
- possible encoding marker/newline differences;
- possible renderer-internal SVG/PNG differences.

Last mapped: 2026-07-07.

Last parity check: 2026-07-07. Validate mode matched exactly: `nodes=14`, `relationships=115`, zero class/layout issues on existing and generated graphs. No-render refresh mode with redirected `.tmp` settings produced matching Mermaid graph files, matching reports after timestamp/path normalization, and matching snapshots after `generated_at`/path normalization. Render mode succeeded for both scripts on a tiny Mermaid file; both SVG outputs were nonzero, the same size in this run (`10814` bytes), and contained the expected `Alpha` and `Beta` labels.

## Obsidian QA Export

### Script Pair

| Role | Script | Command |
| --- | --- | --- |
| Preferred implementation | `Tools/obsidian_qa_export.py` | `python Tools\obsidian_qa_export.py` |
| Windows fallback | `Tools/Obsidian-QA-Export.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Obsidian-QA-Export.ps1` |

Purpose: compile repository metadata, type-specific YAML data blocks, Relationship Seeds, and graph projections into an ignored Obsidian-friendly QA mirror. The export is for maintainer inspection and visual QA; it is not a source of truth.

### Switch Map

| Purpose | Python switch | PowerShell switch | Default | Notes |
| --- | --- | --- | --- | --- |
| Select repository root | `--root <path>` | `-Root <path>` | `.` | All discovered canonical files and output safety checks are resolved from this root. |
| Select export directory | `--output-dir <path>` | `-OutputDir <path>` | `Obsidian_Export` | Relative paths are resolved under the repository root. Output must remain inside the repository root. |
| Include stub pages | `--include-stubs` | `-IncludeStubs` | off | Includes canonical pages whose metadata has `Status: Stub`. Pending pages are not excluded by this switch. |
| Clean before writing | `--clean` | `-Clean` | off | Deletes the selected export directory before regenerating it, after the path safety check. |
| Print JSON summary | `--json` | `-Json` | off | Prints summary counts as JSON instead of human-readable text. Generated files are still written. |
| Generate extra bounded graph(s) | `--bounded-graph <spec>` | `-BoundedGraph <spec>` | none | Repeatable opt-in. Generates no-render Mermaid graphs under `_Generated/bounded-graphs/` in addition to the normal export. Specs are comma-separated key/value pairs such as `name=vol1-ch45,medium=novel,maxVolume=1,maxChapter=45`. Multiple specs may also be separated with semicolons inside one argument, which is the recommended PowerShell form. |
| Generate extra bounded page(s) | `--bounded-page <spec>` | `-BoundedPage <spec>` | none | Repeatable opt-in. Generates boundary-filtered QA Markdown pages under `_Generated/bounded-pages/` in addition to the normal export. Specs are comma-separated key/value pairs such as `slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=30`. Multiple specs may also be separated with semicolons inside one argument, which is the recommended PowerShell form. |
| Show CLI help | `--help` | n/a | n/a | Python exposes argparse help. The PowerShell fallback exposes switches through the script `param(...)` block. |

Bounded graph spec keys:

- `name`: Human-readable graph view name and default output filename stem.
- `file` / `filename` / `file-stem`: Optional explicit output filename stem.
- `medium`: Boundary medium. Defaults to `novel`.
- `maxVolume`, `maxChapter`, `maxSeason`, `maxEpisode`, `maxReleaseOrder`: Reader/viewer boundary values. At least one max boundary is required.
- `includeUnknownSubjects`, `includeUnknownPositions`: Optional booleans. Defaults are `false`.

Bounded page spec keys:

- `slug`: Required canonical source slug, such as `character-dunn-smith`.
- `name`: Optional human-readable label. Defaults to the source page title.
- `file` / `filename` / `file-stem`: Optional explicit output filename stem.
- `medium`: Boundary medium. Defaults to `novel`.
- `maxVolume`, `maxChapter`, `maxSeason`, `maxEpisode`, `maxReleaseOrder`: Reader/viewer boundary values. At least one max boundary is required.
- `includeAnonymousPreview`: Optional boolean. Defaults to `true`. Allows explicitly modeled anonymous first-appearance beats before canonical page visibility.

### Inputs

| Input | Used For |
| --- | --- |
| `Glossary_Threads/**/*.md` | Canonical glossary notes, metadata, YAML data blocks, and Relationship Seeds. |
| `Volumes/**/*.md` | Volume summary pages with metadata, YAML data blocks, or Relationship Seeds. |
| `Visualization/visualize.py` | Python export helper for `visualization-relationship-graph.mmd` and repo refresh dry-run generation. |
| `Visualization/visualize.ps1` | PowerShell export helper for repo refresh dry-run generation. |
| `Visualization/config/render-settings.json` | Source configured view list for `_Generated/repo-refresh-check/`. |
| `Visualization/config/puppeteer-config.json` | Passed through to the visualization refresh helper for dry-run fidelity. Rendering is skipped. |
| `Tools/clean_temp_files.py` | Python export calls this at the end to remove transient Python cache folders. |
| `requirements-python.txt` / `PyYAML` | Python bounded-page generation uses `PyYAML` to parse structured page data blocks. |
| `requirements-powershell.txt` / `powershell-yaml` | PowerShell bounded-page generation uses `powershell-yaml` to parse structured page data blocks. |

### Outputs

Default output root: `Obsidian_Export/`, ignored by Git.

| Output | Description |
| --- | --- |
| Type folders such as `Characters/`, `Artifacts/`, `Items/`, `Knowledge_Sources/`, `Pathways/`, and `Volumes/` | Generated mirror notes grouped by canonical page type. Notes include metadata, first-appearance beat mirrors when present, relationship seeds, data references, incoming references, and seed evidence. |
| `_Generated/relationship-index.md` | Relationship Seed table with source, relationship, target, status, confidence, and seed file. |
| `_Generated/data-reference-index.md` | Non-Relationship-Seed YAML slug references discovered in data blocks. |
| `_Generated/orphan-report.md` | Unknown sources/targets, unknown data targets, and generated notes with no edges or references. |
| `_Generated/suspicious-edges.md` | Self loops, duplicate edge groups, missing expected reciprocals, and same-type known edges. |
| `_Generated/QA-relationship-graph.mmd` | QA-only direct-edge Mermaid relationship graph. Duplicate seeds collapse with `xN` labels. |
| `_Generated/QA-relationship-node-graph.mmd` | QA-only Mermaid graph that projects relationships as intermediary nodes for readability. |
| `_Generated/visualization-relationship-graph.mmd` | Unbounded local QA graph generated with the repository visualization projection style. |
| `_Generated/repo-refresh-check/*.mmd` | No-render dry-run Mermaid files for every configured repository graph view. |
| `_Generated/repo-refresh-check/refresh-check-report.md` | Dry-run refresh report generated through the real visualization refresh helper. |
| `_Generated/repo-refresh-check/refresh-check-snapshot.json` | Dry-run semantic graph snapshot. |
| `_Generated/repo-refresh-check/refresh-check-settings.json` | Generated render settings rewritten to point at the local dry-run bundle. |
| `_Generated/bounded-graphs/*.mmd` | Optional no-render bounded graph outputs requested through `--bounded-graph` / `-BoundedGraph`. This folder is created only when bounded graphs are requested. |
| `_Generated/bounded-graphs/bounded-graphs-report.md` | Optional refresh report for the requested bounded graph bundle. |
| `_Generated/bounded-graphs/bounded-graphs-snapshot.json` | Optional semantic graph snapshot for the requested bounded graph bundle. |
| `_Generated/bounded-graphs/bounded-graphs-settings.json` | Optional generated render settings used for the requested bounded graph bundle. |
| `_Generated/bounded-pages/**/*.md` | Optional bounded QA page projections requested through `--bounded-page` / `-BoundedPage`. This folder is created only when bounded pages are requested. Character bounded pages render the standard character modules and present optional modules such as Tarot card, mythical creature form, uniqueness, knowledge sources/documents, messengers/servants/companions, and prayers/ritual access only when the source data block includes them. Bounded-page timing tables can summarize state-row `availability` ladders or positioned reveal fields such as first-appearance `position`, `source_refs`, and `graph_display`. |

The repo refresh check does not update canonical `Visualization/graphs/`, `Visualization/rendered/`, `Visualization/data/refresh-snapshot.json`, or `Visualization/README.md`.

### Behavior Map

| Behavior | Python function | PowerShell function |
| --- | --- | --- |
| Parse CLI/switches | `build_parser`, `main` | top-level `param(...)`, bottom script block |
| Configure UTF-8 output | `configure_output_encoding` | top-level `$OutputEncoding` / `[Console]::OutputEncoding` |
| Read canonical Markdown | `discover_notes`, `read_text` | `Get-CanonicalNotes`, `Read-TextFile` |
| Parse metadata | `parse_metadata`, `extract_section` | `Get-Metadata`, `Get-MarkdownSection` |
| Parse Relationship Seeds | `extract_relationship_yaml`, `parse_relationships`, `make_relationship` | `Get-RelationshipYaml`, `Get-RelationshipsFromYaml`, `New-Relationship` |
| Parse non-seed YAML references | `parse_data_references`, `slug_candidates_from_yaml_value` | `Get-DataReferences`, `Get-SlugCandidatesFromYamlValue` |
| Parse projected data-block availability | `parse_data_projections`, `make_availability_entry`, `projection_keys_for_row` | `Get-DataProjections`, `New-AvailabilityEntry`, `Get-ProjectionKeysForRow` |
| Parse first-appearance beats for mirror notes | `parse_first_appearance_beats` | `Get-FirstAppearanceBeats` |
| Render generated mirror notes | `render_note` | `ConvertTo-NoteMarkdown` |
| Render index/report Markdown | `render_relationship_index`, `render_data_reference_index`, `render_orphan_report`, `render_suspicious_edges` | `ConvertTo-RelationshipIndex`, `ConvertTo-DataReferenceIndex`, `ConvertTo-OrphanReport`, `ConvertTo-SuspiciousEdges` |
| Analyze QA issues | `analyze_orphans`, `analyze_suspicious_edges` | `Get-OrphanAnalysis`, `Get-SuspiciousEdgeAnalysis` |
| Render direct-edge QA graph | `render_labeled_relationship_graph` | `ConvertTo-LabeledRelationshipGraph` |
| Render relationship-node QA graph | `render_relationship_node_graph` | `ConvertTo-RelationshipNodeGraph` |
| Build QA graph labels/provenance | `relationship_provenance_lines`, `relationship_source_lines`, `relationship_source_line`, `format_availability_history`, `format_availability_entry` | `Get-RelationshipProvenanceLines`, `Get-RelationshipSourceLines`, `Format-RelationshipSourceLine`, `Format-AvailabilityHistory`, `Format-AvailabilityEntry` |
| Render visualization-style unbounded graph | `write_visualization_relationship_graph` | `ConvertTo-VisualizationRelationshipGraph` |
| Write repo refresh dry-run bundle | `write_repo_refresh_check`, `repo_relative_path` | `Write-RepoRefreshCheck`, `Get-RepoRelativePath` |
| Parse bounded graph requests | `parse_bounded_graph_specs`, `parse_bounded_graph_spec` | `ConvertFrom-BoundedGraphSpecs`, `ConvertFrom-BoundedGraphSpec` |
| Write optional bounded graph bundle | `write_bounded_graphs` | `Write-BoundedGraphs` |
| Parse bounded page requests | `parse_bounded_page_specs`, `parse_bounded_page_spec` | `ConvertFrom-BoundedPageSpecs`, `ConvertFrom-BoundedPageSpec` |
| Parse and filter bounded character page data | `extract_profile_block`, `parse_profile_yaml`, `filter_profile_rows_for_boundary`, `render_bounded_table` | `Get-ProfileYaml`, `Get-FilteredProfileRowsForBoundary`, `ConvertTo-BoundedTableMarkdown` |
| Write optional bounded page bundle | `write_bounded_pages` | `Write-BoundedPages` |
| Guard output path safety | `ensure_safe_output` | `Assert-SafeOutputPath` |
| Write all export files | `write_export` | `Write-ObsidianExport` |
| Clean disposable Python caches | `clean_disposable_caches` | n/a |

### Important Differences

- Python invokes `Tools/clean_temp_files.py` at the end of normal runs to remove transient cache folders. PowerShell invokes `Tools/Clean-TempFiles.ps1 -Delete` at the end for the same cleanup behavior.
- Python loads `Visualization/visualize.py` directly for the unbounded visualization-style graph and repo refresh dry run. PowerShell mirrors the unbounded graph internally, then shells out to `Visualization/visualize.ps1` for the repo refresh dry run.
- Python bounded-page parsing depends on `PyYAML`. PowerShell bounded-page parsing depends on `powershell-yaml`; use `Tools/Test-PowerShell.ps1` before using `-BoundedPage` on a new machine.
- Python has built-in `--help`; PowerShell switch discovery is through the `param(...)` block and this reference.

### Parity Check Recipe

Use ignored `.tmp/` output folders so comparison runs do not create trackable artifacts.

```powershell
python Tools\obsidian_qa_export.py --clean --output-dir .tmp\obsidian-python-check --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Obsidian-QA-Export.ps1 -Clean -OutputDir .tmp\obsidian-powershell-check -Json

python Tools\obsidian_qa_export.py --clean --output-dir .tmp\obsidian-python-bounded --bounded-graph "name=ch10,medium=novel,maxVolume=1,maxChapter=10" --bounded-graph "name=vol1,medium=novel,maxVolume=1" --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Obsidian-QA-Export.ps1 -Clean -OutputDir .tmp\obsidian-powershell-bounded -BoundedGraph 'name=ch10,medium=novel,maxVolume=1,maxChapter=10;name=vol1,medium=novel,maxVolume=1' -Json

python Tools\obsidian_qa_export.py --clean --output-dir .tmp\obsidian-python-pages --bounded-page "slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=10" --bounded-page "slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=30" --bounded-page "slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=50" --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Obsidian-QA-Export.ps1 -Clean -OutputDir .tmp\obsidian-powershell-pages -BoundedPage 'slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=10;slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=30;slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=50' -Json
```

Compare at minimum:

- generated file counts;
- JSON summary keys and counts;
- `relationship-index.md`;
- `data-reference-index.md`;
- `orphan-report.md`;
- `suspicious-edges.md`;
- `QA-relationship-graph.mmd`;
- `QA-relationship-node-graph.mmd`;
- `visualization-relationship-graph.mmd`;
- `repo-refresh-check/*.mmd`;
- `repo-refresh-check/refresh-check-report.md`;
- `repo-refresh-check/refresh-check-snapshot.json`;
- bounded page outputs when `--bounded-page` / `-BoundedPage` is used, especially Ch10 anonymous preview behavior, Ch30/Ch50 Dunn pathway-state progression, and Old Neil transitional/current character modules.

Expected non-semantic differences:

- output paths in JSON summaries;
- timestamps in refresh-check reports;
- path names inside `refresh-check-settings.json` when different output directories are used;
- JSON formatting differences between Python `json.dumps` and PowerShell `ConvertTo-Json`.

Last mapped: 2026-07-07.

Last parity check: 2026-07-07. Python and PowerShell generated 27 files each with matching file lists for normal exports. The main generated Markdown files, QA Mermaid graphs, visualization-style Mermaid graph, and repo refresh dry-run Mermaid files matched after newline normalization. `refresh-check-snapshot.json` matched semantically after ignoring `generated_at` and normalizing the intentionally different `.tmp` output path. Bounded page parity was checked with Dunn Smith at Novel V1 Ch10, Ch20, Ch30, and Ch50; both implementations generated four bounded pages, preserved Ch10 anonymous preview behavior, and showed Dunn's Sleepless pathway progression as Ch22 strong-evidence at Ch30 and Ch22 strong-evidence -> Ch45 confirmed at Ch50. The bounded character renderer also supports the broader character module set, including optional/specialized modules only when present.

## Configuration Files

This section tracks durable configuration and generated state files that affect helper behavior. Add new entries here when a tool starts reading a new config file, writing a new persistent state file, or depending on a shared registry. Do not list ignored one-run artifacts such as `.tmp/`, `Obsidian_Export/`, Python caches, or rendered files generated from an already listed source config.

| File | Kind | Read By | Written By | Purpose | Update When |
| --- | --- | --- | --- | --- | --- |
| `requirements-python.txt` | Dependency registry | `Tools/Test-Python.ps1`; human setup via `python -m pip install -r requirements-python.txt` | Maintainers | Defines Python packages required by preferred Python helper scripts. | Add or change entries when a Python helper gains or removes a third-party package dependency. |
| `requirements-powershell.txt` | Dependency registry | `Tools/Test-PowerShell.ps1`; human setup via `Install-Module <module> -Scope CurrentUser -Force -AllowClobber` or elevated `-Scope AllUsers` when machine-wide installs are preferred | Maintainers | Defines PowerShell modules required by fallback script features such as bounded Obsidian QA pages. | Add or change entries when a PowerShell helper gains or removes a module dependency. |
| `Visualization/config/render-settings.json` | Source config | `Visualization/visualize.py`, `Visualization/visualize.ps1`, `Tools/obsidian_qa_export.py`, `Tools/Obsidian-QA-Export.ps1` | Maintainers | Defines canonical graph views, source Mermaid paths, rendered output paths, render dimensions, validation settings, reader-boundary filters, report path, and semantic snapshot path. The Obsidian QA export also derives its local `_Generated/repo-refresh-check/` dry-run settings from this file. | Add or remove repository graph views, change render sizes, adjust validation rules, change reader-boundary behavior, or redirect canonical report/snapshot paths. |
| `Visualization/config/puppeteer-config.json` | Source config | `Visualization/visualize.py`, `Visualization/visualize.ps1`, Obsidian QA repo-refresh dry-run helpers through visualization tooling | Maintainers | Configures the browser executable, timeout, and launch args used by Mermaid/Puppeteer rendering. | Browser path changes, rendering starts timing out, CI/local environment changes, or Mermaid rendering needs different launch args. |
| `Visualization/data/refresh-snapshot.json` | Generated semantic state | `Visualization/visualize.py`, `Visualization/visualize.ps1` | `Visualization/visualize.py --mode Refresh`, `Visualization/visualize.ps1 -Mode Refresh` | Stores the last canonical graph semantic snapshot so refresh reports can detect added/removed nodes, relationships, changed labels, duplicates, and other graph hygiene changes. | Update only through a confirmed canonical graph refresh. Do not edit manually except for explicit debugging that is later reverted or regenerated. |

### Future Config Registries

Planned shared registries should be added here once they exist. Likely candidates include a display-label registry for reusable taxonomy values, broader controlled-value taxonomy files, or site-rendering configuration. Until those files exist, `PROJECT_RULES.md` and the type templates remain the source of truth for taxonomy/prose rendering policy.
