# Tooling Reference

This file is the human-facing map for repository helper scripts. It records what each script is for, how Python-preferred and PowerShell-fallback versions line up when a pair exists, which switches are supported, what files are read or written, and how parity or standalone behavior was last checked.

`Framework/framework_improvement_lifecycle.md` is authoritative for the end-to-end version workflow. `Framework/testing_methodology.md` is authoritative for cumulative test requirements, stable families, retention rules, impact matrix, comparison standards, and result classification. This reference remains authoritative for exact commands, tool-specific output contracts, normalization recipes, and dated parity executions.

Paired validation and conformance commands must expose `--json` / `-Json` whenever they emit a human-readable summary. The 2026-08-01 executable audit confirmed structured output for the environment probes, cleanup, EPUB search, EPUB image operations, Obsidian QA export, chronology, occurrence, temporal, and reconciliation commands. Configuration loaders are libraries rather than summary commands. Visualization remains a file-producing multi-mode command whose structured contracts are its Mermaid graphs, refresh report, and semantic snapshot; a future CLI JSON mode must define mode-specific fields rather than reusing an ambiguous generic summary.

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

Last check: 2026-08-01. Normal and JSON modes ran successfully on this machine. The probe detected `python`, Python 3.14.5, executable `C:\Users\ptseb\AppData\Local\Python\pythoncore-3.14-64\python.exe`, and `ready: true` after validating `PyYAML` through `yaml` and Ruff 0.16.1 through `ruff`.

## Python Source Formatting

### Tool And Configuration

| Role | Tool / File | Command |
| --- | --- | --- |
| Canonical formatter | Ruff from `requirements-python.txt` | `python -m ruff format .` |
| Read-only formatting check | Ruff from `requirements-python.txt` | `python -m ruff format --check .` |
| Line-length check | Ruff `E501` policy from `pyproject.toml` | `python -m ruff check .` |

Purpose: deterministically format and check every tracked or nonignored untracked `.py` and `.pyi` source in the Git worktree. Ruff is the formatter engine rather than a repository-specific wrapper.

### Formatting Contract

- `pyproject.toml` owns the Python 3.10 compatibility target, 120-character line length, spaces, double quotes, LF output, stable trailing-comma behavior, and the current deliberately narrow `E501` lint selection.
- Ruff's include list is limited to `.py` and `.pyi`; Markdown code fences are canonical project content and must not be formatted as Python.
- `.gitattributes` owns LF checkout line endings for Python source.
- Default discovery respects Gitignore and automatically includes new nonignored Python files and source folders.
- Ruff performs mechanical layout. Long strings, regexes, and report expressions it cannot safely split must be wrapped manually without changing their runtime values.
- Broader Ruff lint families are not part of this formatting baseline. Enable them only through a separately reviewed policy change with existing violations reconciled deliberately.

### Check Recipe

```powershell
# Read-only repository check
python -m ruff format --check .
python -m ruff check .

# Apply formatting, then check nonmechanical line-length cases
python -m ruff format .
python -m ruff check .
```

Last mapped: 2026-08-01.

Last check: 2026-08-01. Ruff 0.16.1 formatted 21 of 22 existing Python files; one was already canonical. After 54 residual semantic lines were split manually, all 22 files passed format and `E501` checks with a measured physical maximum of 120 characters. Repository-wide discovery excluded Markdown and was verified with a temporary nonignored root-level Python source.

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
Install-Module PSScriptAnalyzer -Scope CurrentUser -Force
```

Last mapped: 2026-08-01.

Last check: 2026-08-01. JSON mode ran successfully in PowerShell 7.6.3 and Windows PowerShell 5.1.19041.7548. Both runtimes detected the machine-wide `powershell-yaml` and `PSScriptAnalyzer` requirements.

## PowerShell Source Formatting

### Script

| Role | Script | Command |
| --- | --- | --- |
| PowerShell static formatter and check | `Tools/Format-PowerShell.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Format-PowerShell.ps1` |

Purpose: deterministically format and statically check maintained PowerShell sources. This tool has no Python pair because its behavior depends on the PowerShell parser and `PSScriptAnalyzer`; it does not implement a project-domain feature that requires a fallback runtime.

### Parameter Map

| Purpose | Parameter | Default | Notes |
| --- | --- | --- | --- |
| Select files or directories | `-Path <string[]>` | all tracked and nonignored untracked repository PowerShell sources | Explicit directories recursively include `.ps1`, `.psm1`, and `.psd1` sources. Relative paths resolve from the repository root. |
| Maximum physical line length | `-MaximumLineLength <int>` | `200` | Values from 80 through 1000 are accepted. Any longer line fails the check even after formatting. |
| Apply changes | `-Fix` | off | Without this switch the command is read-only and exits nonzero when a file differs from canonical formatting. |
| Print JSON summary | `-Json` | off | Emits readiness, mode, file/change counts, line-length results, and per-file details. |

### Formatting Contract

- `Tools/powershell-format-settings.psd1` owns PSScriptAnalyzer layout settings.
- `.gitattributes` owns CRLF checkout line endings for `.ps1`, `.psm1`, and `.psd1` files.
- Default discovery uses Git's tracked-plus-untracked, exclude-standard inventory, so new nonignored scripts and source folders require no formatter configuration change.
- Gitignored local or generated PowerShell files are outside the default repository policy; pass an explicit `-Path` when they need an ad hoc check.
- Output is UTF-8 without a BOM and uses CRLF.
- Optional statement-terminating semicolons are removed; syntax-required `for (...)` separators are retained.
- Source must parse before and after formatting, and every non-newline/non-semicolon token must remain equivalent.
- Trailing whitespace and lines longer than the configured maximum fail the check.
- Complex semantic expressions that remain overlong must be wrapped manually and then rechecked.

### Check Recipe

```powershell
# Read-only default check under Windows PowerShell 5.1
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Format-PowerShell.ps1

# Apply canonical formatting
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Format-PowerShell.ps1 -Fix

# PowerShell 7 structured check
pwsh -NoProfile -File Tools\Format-PowerShell.ps1 -Json
```

Last mapped: 2026-08-01.

Last check: 2026-08-01. PowerShell 7.6.3 and Windows PowerShell 5.1.19041.7548 each discovered all 26 tracked or nonignored untracked repository PowerShell sources and checked them with zero pending changes, zero lines above 200 characters, successful parsing, and identical source acceptance. A temporary nonignored root-level script was discovered automatically by both runtimes during the discovery regression.

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

Both current implementations discover the Book 1 EPUB layout. They do not yet consume `Project_Config/sources.yaml`, accept a registered work ID, or discover entries in the current COI EPUB package. Passing the COI path returns an empty entry list and must not be interpreted as an empty book. Multi-book search support requires registry-backed work/source selection plus package-specific discovery adapters.

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
| Select mode | `--mode <mode>` | `-Mode <mode>` | `Refresh` | Modes normalize to refresh, render, validate, or QA relationship graph generation. |
| Select mode alias | n/a | `-Action <mode>` | n/a | PowerShell alias for `-Mode`. |
| Input Mermaid file for render mode | `--input-path <path>` | `-InputPath <path>` | none | Required for render mode. |
| Input aliases | `--input`, `--graph` | `-Input`, `-Graph` | n/a | Aliases for input path. |
| Render output path(s) | `--output-path <path>` | `-OutputPath <path>[,<path>]` | none | Render mode defaults to SVG and PNG under `Visualization/rendered/` when omitted. Python accepts repeated `--output-path`; PowerShell accepts a string array. |
| Output aliases | `--output`, `--out` | `-Output`, `-Out` | n/a | Aliases for output path. |
| Select QA relationship graph output | `--graph-path <path>` | `-GraphPath <path>` | none | Required only for QA relationship mode. Relative paths resolve beneath the repository root. |
| Preserve confirmed confidence labels | `--include-confirmed-confidence` | `-IncludeConfirmedConfidence` | off | Includes `confirmed` in relationship labels. The Obsidian QA exporters enable this for maintainer provenance review. |
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

QA relationship graph:

- Python: `qa-relationship`, `Qa-Relationship`, `qa-relationship-graph`, `Qa-Relationship-Graph`, `unbounded-relationship`, `Unbounded-Relationship`
- PowerShell: the same hyphenated names case-insensitively, plus `QaRelationship`

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
| Glossary nodes, Relationship Seeds, and projected data-block availability | QA relationship mode writes the unbounded visualization-style graph requested by the QA exporter. |

### Outputs And Side Effects

| Mode | Output | Side Effect |
| --- | --- | --- |
| Refresh | Generated Mermaid graph files, refresh report, semantic snapshot, and optionally rendered image outputs. | Mutates every configured view input path, report path, snapshot path, and rendered outputs unless paths are redirected in a supplied settings file. |
| Refresh with skip render | Generated Mermaid graph files, refresh report, semantic snapshot. | Does not render PNG/SVG outputs. Still mutates configured graph/report/snapshot paths. |
| Validate | Human-readable validation summary. | Does not mutate configured graph/report/snapshot/rendered outputs. Generates temporary graph files under the system temp directory and removes them. |
| Render | Human-readable render progress. | Writes rendered output files to explicit `--output-path` / `-OutputPath` values or default `Visualization/rendered/<input-name>.svg/.png`. |
| QA relationship | One unbounded Mermaid graph at `--graph-path` / `-GraphPath`. | Writes only the requested graph. Does not update canonical refresh reports, snapshots, configured views, or rendered images. |

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
| Write unbounded QA relationship graph | `write_unbounded_relationship_graph` | `Write-UnboundedRelationshipGraph` |
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

Last parity check: 2026-08-01. Python, PowerShell 7, and Windows PowerShell 5.1 Validate runs matched exactly (`nodes=15`, `relationships=121`, zero class/layout issues for both existing and freshly generated configured views). Redirected Obsidian QA runs exercised each runtime's Visualization helper for the unbounded relationship graph, configured no-render refresh, and a Novel V1 Ch32 bounded graph. Generated Mermaid files matched after newline normalization, and refresh/bounded snapshot node, relationship, view, orphan, pending, and broken-link semantics matched after runtime path and timestamp normalization. Redirected Render runs over the tracked full Volume 1 graph each produced the same nonempty `298269`-byte SVG with an identical SHA-256 hash.

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
| Select repository root | `--root <path>` | `-Root <path>` | Auto-detected | When omitted, searches upward from the current directory and then the script directory. Explicit roots remain authoritative. Project identity comes from `Project_Config/project.yaml`; content-directory names do not participate in root detection. |
| Select export directory | `--output-dir <path>` | `-OutputDir <path>` | `Obsidian_Export` | Relative paths are resolved under the repository root. The destination must be a child of the repository root; the root itself and outside paths are rejected. Safe missing parent directories are created automatically. |
| Include stub pages | `--include-stubs` | `-IncludeStubs` | off | Includes canonical pages whose metadata has `Status: Stub`. Pending pages are not excluded by this switch. |
| Clean before writing | `--clean` | `-Clean` | off | Deletes the selected export directory before regenerating it, after the path safety check. |
| Print JSON summary | `--json` | `-Json` | off | Prints summary counts as JSON instead of human-readable text. Generated files are still written. |
| Generate extra bounded graph(s) | `--bounded-graph <spec>` | `-BoundedGraph <spec>` | none | Repeatable opt-in. Generates no-render Mermaid graphs under `_Generated/bounded-graphs/` in addition to the normal export. Specs are comma-separated key/value pairs such as `name=vol1-ch45,medium=novel,maxVolume=1,maxChapter=45`. Multiple specs may also be separated with semicolons inside one argument, which is the recommended PowerShell form. The folder is rebuilt from scratch when specs are provided and removed when no bounded graphs are requested, preventing stale sampled graphs from lingering. |
| Generate extra bounded page(s) | `--bounded-page <spec>` | `-BoundedPage <spec>` | none | Repeatable opt-in. Generates boundary-filtered QA Markdown pages under `_Generated/bounded-pages/` in addition to the normal export. Specs are comma-separated key/value pairs such as `slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=30`. Multiple specs may also be separated with semicolons inside one argument, which is the recommended PowerShell form. The folder is rebuilt from scratch when specs are provided and removed when no bounded pages are requested, preventing stale sampled pages from lingering. |
| Show CLI help | `--help` | `-Help`, `-?`, `-h` | n/a | Python exposes argparse help. The PowerShell fallback prints script-specific help and exits without generating the export. |

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
| `Project_Config/project.yaml` | Identifies the project and configures modeled content roots, provenance behavior, registry discovery, QA output, visualization integration, and cleanup helpers. |
| `Framework/Data/unicode-lookup-16.0.0.json` | Supplies pinned Unicode normalization data for runtime-independent semantic alias lookup. |
| `Project_Config/taxonomy.yaml` | Selects content types eligible for QA page discovery; currently `glossary-page` and `volume-summary`, excluding `investigation-record`. |
| Taxonomy-selected QA page roots; currently `Glossary_Threads/**/*.md` and `Volumes/**/*.md` | Canonical notes, metadata, YAML data blocks, and Relationship Seeds. |
| Configured visualization helpers; currently `Visualization/visualize.py` and `Visualization/visualize.ps1` | Visualization-style graph and repo refresh dry-run generation. |
| Configured render settings and Puppeteer config under `Visualization/config/` | Source view list and dry-run fidelity settings. Rendering is skipped. |
| Configured cleanup helpers under `Tools/` | End-of-run transient cache cleanup. |
| `requirements-python.txt` / `PyYAML` | Python project-manifest and structured page-data parsing. |
| `requirements-powershell.txt` / `powershell-yaml` | PowerShell project-manifest and structured page-data parsing. `PSScriptAnalyzer` from the same registry is used by the repository PowerShell formatter. |

### Outputs

Default output root: the manifest's `paths.qa_export`, currently `Obsidian_Export/` and ignored by Git.

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
| `_Generated/bounded-graphs/*.mmd` | Optional no-render bounded graph outputs requested through `--bounded-graph` / `-BoundedGraph`. This folder is created only when bounded graphs are requested, rebuilt from scratch for each bounded-graph run, and removed by QA export runs that do not request bounded graphs. |
| `_Generated/bounded-graphs/bounded-graphs-report.md` | Optional refresh report for the requested bounded graph bundle. |
| `_Generated/bounded-graphs/bounded-graphs-snapshot.json` | Optional semantic graph snapshot for the requested bounded graph bundle. |
| `_Generated/bounded-graphs/bounded-graphs-settings.json` | Optional generated render settings used for the requested bounded graph bundle. |
| `_Generated/bounded-pages/**/*.md` | Optional bounded QA page projections requested through `--bounded-page` / `-BoundedPage`. This folder is created only when bounded pages are requested, rebuilt from scratch for each bounded-page run, and removed by QA export runs that do not request bounded pages. Character bounded pages render the standard character modules and present optional modules such as Tarot card, mythical creature form, uniqueness, knowledge sources/documents, messengers/servants/companions, and prayers/ritual access only when the source data block includes them. Bounded-page timing tables can summarize state-row `availability` ladders or positioned reveal fields such as first-appearance `position`, `source_refs`, and `graph_display`. |

The repo refresh check does not update canonical `Visualization/graphs/`, `Visualization/rendered/`, `Visualization/data/refresh-snapshot.json`, or `Visualization/README.md`.

### Behavior Map

| Behavior | Python function | PowerShell function |
| --- | --- | --- |
| Parse CLI/switches | `build_parser`, `main` | top-level `param(...)`, bottom script block |
| Render CLI help | argparse generated help | `Show-Help` |
| Resolve repository root | `resolve_project_root`, `is_project_root` in `project_config.py` | `Resolve-KnowledgeProjectRoot`, `Test-KnowledgeProjectRoot` in `Project-Config.ps1` |
| Load and validate project configuration | `load_project_config`, `resolve_manifest_path` in `project_config.py` | `Get-KnowledgeProjectConfig`, `Resolve-ProjectManifestPath` in `Project-Config.ps1` |
| Select taxonomy-enabled QA page roots | `load_taxonomy_config`, `TaxonomyConfig.content_roots_for_qa_pages` | `Get-KnowledgeTaxonomyConfig`, `Get-TaxonomyQaPageContentRoots` |
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
| Request visualization-style unbounded graph | `write_visualization_relationship_graph` -> configured `write_unbounded_relationship_graph` | configured `visualize.ps1 -Mode QaRelationship` -> `Write-UnboundedRelationshipGraph` |
| Write repo refresh dry-run bundle | `write_repo_refresh_check`, `repo_relative_path` | `Write-RepoRefreshCheck`, `Get-RepoRelativePath` |
| Parse bounded graph requests | `parse_bounded_graph_specs`, `parse_bounded_graph_spec` | `ConvertFrom-BoundedGraphSpecs`, `ConvertFrom-BoundedGraphSpec` |
| Write optional bounded graph bundle | `write_bounded_graphs` | `Write-BoundedGraphs` |
| Parse bounded page requests | `parse_bounded_page_specs`, `parse_bounded_page_spec` | `ConvertFrom-BoundedPageSpecs`, `ConvertFrom-BoundedPageSpec` |
| Parse and filter bounded character page data | `extract_profile_block`, `parse_profile_yaml`, `filter_profile_rows_for_boundary`, `render_bounded_table` | `Get-ProfileYaml`, `Get-FilteredProfileRowsForBoundary`, `ConvertTo-BoundedTableMarkdown` |
| Write optional bounded page bundle | `write_bounded_pages` | `Write-BoundedPages` |
| Guard output path safety | `ensure_safe_output` | `Assert-SafeOutputPath` |
| Write all export files | `write_export` | `Write-ObsidianExport` |
| Clean disposable caches | `clean_disposable_caches` | `Invoke-DisposableCacheCleanup` |

### Important Differences

- Python invokes the manifest-configured Python cleanup helper at the end of normal runs. PowerShell invokes the manifest-configured PowerShell cleanup helper with `-Delete` for the same behavior.
- Both implementations auto-detect the repository root when `--root` / `-Root` is omitted, so they may be launched from the repository root, `Tools/`, or another descendant directory. Detection does not depend on `.git` or a domain-specific content folder; explicit roots are validated against `Project_Config/project.yaml`.
- Both implementations accept existing or not-yet-created export directories beneath the repository root, create missing parent directories, and reject the repository root itself or any outside path before clean-up begins. The default `<repo>/Obsidian_Export/` path remains valid.
- Python loads the manifest-configured Python visualization helper directly for the unbounded visualization-style graph and repo refresh dry run. PowerShell invokes the manifest-configured PowerShell visualization helper for both operations.
- Python QA generation depends on `PyYAML`. PowerShell QA generation depends on `powershell-yaml`; use the environment checks on a new machine before selecting either implementation.
- Python has built-in `--help`; PowerShell supports `-Help`, `-?`, and `-h` through `Show-Help`.

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
- successful creation beneath a fresh, multi-level missing parent directory;
- rejection of the repository root itself and paths outside the repository;
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

Last mapped: 2026-07-31.

Last parity check: 2026-08-01. Python, PowerShell 7, and Windows PowerShell 5.1 each generated the same 35-file inventory and summary counts for a redirected export containing one Novel V1 Ch32 bounded graph plus Dunn Smith Ch10/Ch32 and Leonard Mitchell Ch32 bounded pages. All 29 stable Markdown and Mermaid outputs matched after generated timestamp and newline normalization; the six refresh/bounded report, settings, and snapshot artifacts matched semantically after expected runtime path, timestamp, encoding, and JSON-format differences were normalized. Normal exports launched from `Tools/` also auto-detected the repository root and produced identical summaries (`notes=16`, `relationships=121`, `data_references=71`, no bounded outputs). Prior boundary checks covered Dunn Smith at Novel V1 Ch10, Ch20, Ch30, and Ch50, including anonymous-preview and Sleepless-pathway progression behavior.

Current content-type and ownership regression: both implementations selected taxonomy-enabled `glossary` and `volumes` roots, excluded `investigations`, and produced matching 28-file lists and summary counts (`notes=16`, `relationships=121`, `data_references=71`). After generated timestamps were normalized, all 25 stable Markdown and Mermaid outputs matched exactly. The check moved PowerShell's unbounded visualization-style graph generation into the configured Visualization helper and added a deterministic YAML-block/file tie-breaker to both data-reference index sort orders.

## Configuration Files

This section tracks durable configuration and generated state files that affect helper behavior. Add new entries here when a tool starts reading a new config file, writing a new persistent state file, or depending on a shared registry. Do not list ignored one-run artifacts such as `.tmp/`, `Obsidian_Export/`, Python caches, or rendered files generated from an already listed source config.

| File | Kind | Read By | Written By | Purpose | Update When |
| --- | --- | --- | --- | --- | --- |
| `Project_Config/project.yaml` | Project manifest | `Tools/project_config.py`, `Tools/Project-Config.ps1`, and consumers such as both Obsidian QA exporters | Maintainers | Identifies the project and configures modeled content/resource roots, provenance behavior, registry paths, default QA output, visualization helpers/settings, cleanup helpers, and manifest schema version without coupling framework code to LoTM directory names. | Project identity or paths change, a content/resource root is added, provenance behavior changes, helper locations move, or the manifest schema changes. |
| `Framework/Data/unicode-lookup-16.0.0.json`, `Framework/Data/lookup-key-regression-vectors.json`, `Framework/Data/Strict-Yaml/`, `Framework/Data/Reconciliation/`, `Framework/Data/Temporal/`, `Framework/Data/Chronology/`, and `Framework/Data/Occurrence/` | Pinned framework runtime and conformance data | Strict YAML, lookup, reconciliation, temporal, chronology, and occurrence loaders; paired conformance tools; parity checks; and future semantic identity consumers | Framework maintainers through reviewed data updates | Define deterministic lookup behavior, canonical mapping-key ingestion, branch-aware stable-ID reconciliation vectors, civil-time match/overlap vectors, exact chronology closure, and occurrence/recurrence queries shared by every runtime. | An ingestion, lookup, reconciliation, temporal, chronology, or occurrence algorithm changes, or a discovered portability edge case requires a permanent vector. |
| `Framework/Contracts/README.md`, registry contracts, `Framework/Contracts/strict-configuration-ingestion.md`, `Framework/Contracts/identity-target-provider.md`, and `Framework/Contracts/reconciliation-registry.md` | Framework contract index, registry contracts, strict ingestion rules, and provider boundaries | Framework maintainers and future schema tooling | Framework maintainers | Record executable configuration boundaries, shared YAML semantics, schema ownership, media/work/provenance semantics, identity phases, typed providers, and read-only stable-ID reconciliation. | A configuration contract or provider boundary is introduced, stabilized, moved, or assigned a validator. |
| `Framework/Packs/core/pack.yaml` | Core schema pack | Schema-pack and temporal loaders plus future validation/editor/wizard services | Framework maintainers | Declares domain-neutral platform capabilities plus controlled temporal, evidence-source, claim-namespace, and evidence-artifact vocabulary. | A reusable core capability or evidence primitive changes. |
| `Framework/Packs/README.md` and `Framework/Packs/narrative-*/pack.yaml` | Narrative domain pack catalog and companion packs | Schema-pack, source, and entity loaders plus future narrative editors/wizards | Narrative-domain pack maintainers | Split the narrative foundation, publishing, screen/audio, adaptation, shared-universe, interactive, preservation, and production/rights capabilities into composable contracts without LoTM instances. | A reusable narrative concept is introduced, revised, promoted from planned, or assigned to a different owning pack. |
| `Project_Config/schema-packs.yaml` | Schema-pack composition registry | `Tools/schema_pack_config.py`, `Tools/Schema-Pack-Config.ps1`, source/entity loaders, and future schema/editor/wizard services | Maintainers; future setup and pack-management wizards | Selects portable schema packs in dependency order, locates their repository-relative contract files, and explicitly activates available capabilities for this project. | A reusable pack is selected, removed, replaced, or moved, or project capability activation changes. |
| `Project_Config/taxonomy.yaml` | Taxonomy registry | `Tools/taxonomy_config.py`, `Tools/Taxonomy-Config.ps1`, both Obsidian QA exporters, and future content-index, validation, visualization, editor, and migration services | Maintainers through reviewed edits; future category/content-type editors through the mutation service | Defines orthogonal content-type and category IDs, lifecycle, content roots, category policies, path strategies, subject/record slug rules, placements, templates, QA-page eligibility, and graph defaults. | A category/content type is added, promoted, deferred, renamed for display, moved through a planned migration, assigned a template, or given different QA/graph behavior. |
| `Project_Config/resources.yaml` | Resource registry | `Tools/resource_config.py`, `Tools/Resource-Config.ps1`, and future validation, editor, and migration services | Maintainers through reviewed edits; future resource editors through the mutation service | Defines non-content resource kinds/types, authority roles, editor eligibility, placements beneath configured resource roots, tracking expectations, and required-path behavior. | A resource kind/type or placement is added, renamed for display, moved, given different authority/tracking behavior, or exposed to editors. |
| `Project_Config/sources.yaml` | Source and media registry | `Tools/source_config.py`, `Tools/Source-Config.ps1`, provenance validation, and future content-index, visualization, editor, and migration services | Maintainers through reviewed edits; future source editors through the mutation service | Instantiates media facets, works, structures and orderings, continuities, applicability scopes, authority profiles, adaptation/distribution records, evidence sources, coverage, relationships, identifiers, and resource bindings; exposes stable provenance targets plus evidence/position/authority services without owning assertions. | A media facet, work, scope, continuity record, production context, structural record, authority rule, adaptation/distribution record, source, coverage declaration, relationship, identifier, or resource binding changes. |
| `Project_Config/chronology.yaml` | Chronology registry | `Tools/chronology_config.py`, `Tools/Chronology-Config.ps1`, paired chronology conformance tools, and future content-index, visualization, and editor services | Maintainers through reviewed edits; future chronology editors through the mutation service | Instantiates domain-neutral coordinate systems, ordered eras, positions, spans, relations, mappings, and pack-gated narrative work/continuity/branch contexts without redefining civil time. | A chronology axis, era, position, span, relation, anchor, story-time role, or project context changes. |
| `Project_Config/occurrences.yaml` | Occurrence, recurrence-policy, and subject-state registry | `Tools/occurrence_config.py`, `Tools/Occurrence-Config.ps1`, provenance, paired occurrence conformance tools, and future content-index, visualization, and editor services | Maintainers through reviewed edits; future occurrence editors through the mutation service | Instantiates branches, templates, recurrence patterns and executions, iterations, non-overlapping phases, typed schedules, concrete occurrences, chronology bindings, subject tracks, profiled transitions, causal relations, outcomes, scoped defaults and execution overrides, deterministic resolution policy, state transitions, and state-referencing carryover without encoding cycles in chronology. | An occurrence identity, recurrence pattern/execution, phase, schedule, lifecycle, binding, track, transition, causal relation, outcome, rule, state transition, or carryover changes. |
| `Project_Config/entities.yaml` | Entity, incarnation, and identity-phase registry | `Tools/entity_config.py`, `Tools/Entity-Config.ps1`, provenance, and future content-index, visualization, editor, reconciliation, and migration services | Maintainers through reviewed edits; future entity editors through the mutation service | Instantiates conceptual entities, ambiguity-preserving names, canonical and optionally acyclic lineage, continuity-bound incarnations, scope-backed bindings, incarnation relationships, and persistent-identity phases with explicit scope bindings and succession. | A category membership, shared label/alias, relationship policy, justified incarnation split, continuity membership, scoped appearance, persistent-identity phase, or phase/incarnation relationship changes. |
| `Project_Config/reconciliation.yaml` | Stable-ID reconciliation registry | `Tools/reconciliation_config.py`, `Tools/Reconciliation-Config.ps1`, provenance, and future editor/migration services | Maintainers through reviewed edits; future reconciliation editors through the mutation service | Preserves bounded branch-aware redirects, merges, splits, tombstone-backed retirements, cross-type reclassifications, privacy-aware labels, strict audit metadata, and superseded/reversed decisions without mutating repository files. | A stable ID changes disposition, a historical decision is superseded/reversed, any resolution safety bound changes, or a migration establishes a new canonical target or type. |
| `Project_Config/provenance.yaml` | Cross-registry provenance registry | `Tools/provenance_config.py`, `Tools/Provenance-Config.ps1`, and future validation, editor, comparison, and audit services | Maintainers through reviewed edits; future provenance editors through the mutation service | Owns factual assertions, semantic field paths, evidence links and locators, stable claim grouping, authority evaluation, and acyclic scope-backed claim supersession across typed subject providers. | An assertion, evidence locator, claim value/status/timing, subject field path, or claim-supersession edge changes. |
| `requirements-python.txt` | Dependency registry | `Tools/Test-Python.ps1`; human setup via `python -m pip install -r requirements-python.txt` | Maintainers | Defines Python packages required by preferred Python helpers and source maintenance, including `PyYAML` and the pinned Ruff formatter. | Add or change entries when a Python helper or source-maintenance gate gains or removes a third-party package dependency. |
| `requirements-powershell.txt` | Dependency registry | `Tools/Test-PowerShell.ps1`; human setup via `Install-Module <module> -Scope CurrentUser -Force -AllowClobber` or elevated `-Scope AllUsers` when machine-wide installs are preferred | Maintainers | Defines PowerShell modules required by repository tools, including `powershell-yaml` for structured configuration/page data and `PSScriptAnalyzer` for source formatting. | Add or change entries when a PowerShell helper gains or removes a module dependency. |
| `.gitattributes` | Repository text policy | Git, Ruff, and `Tools/Format-PowerShell.ps1` | Maintainers | Enforces LF for Python and CRLF for PowerShell source/module/config files while preserving Git's normalized text storage. | A tracked source extension or repository line-ending policy changes. |
| `pyproject.toml` | Python formatter and narrow lint configuration | Ruff | Maintainers | Defines repository-wide Python source inclusion, Python 3.10 compatibility, canonical formatting, LF output, 120-character line length, and the current `E501` check. | Python compatibility, formatting, inclusion, line-length, or lint policy changes. |
| `Tools/powershell-format-settings.psd1` | Formatter configuration | `Tools/Format-PowerShell.ps1` and `Invoke-Formatter` from `PSScriptAnalyzer` | Maintainers | Defines deterministic PowerShell indentation, brace placement, whitespace, and trailing-whitespace behavior. | A formatting rule changes; rerun `STATIC-POWERSHELL` in both supported PowerShell runtimes. |
| `Visualization/config/render-settings.json` | Source config | `Visualization/visualize.py`, `Visualization/visualize.ps1`, `Tools/obsidian_qa_export.py`, `Tools/Obsidian-QA-Export.ps1` | Maintainers | Defines canonical graph views, source Mermaid paths, rendered output paths, render dimensions, validation settings, reader-boundary filters, report path, and semantic snapshot path. The Obsidian QA export also derives its local `_Generated/repo-refresh-check/` dry-run settings from this file. | Add or remove repository graph views, change render sizes, adjust validation rules, change reader-boundary behavior, or redirect canonical report/snapshot paths. |
| `Visualization/config/puppeteer-config.json` | Source config | `Visualization/visualize.py`, `Visualization/visualize.ps1`, Obsidian QA repo-refresh dry-run helpers through visualization tooling | Maintainers | Configures the browser executable, timeout, and launch args used by Mermaid/Puppeteer rendering. | Browser path changes, rendering starts timing out, CI/local environment changes, or Mermaid rendering needs different launch args. |
| `Visualization/data/refresh-snapshot.json` | Generated semantic state | `Visualization/visualize.py`, `Visualization/visualize.ps1` | `Visualization/visualize.py --mode Refresh`, `Visualization/visualize.ps1 -Mode Refresh` | Stores the last canonical graph semantic snapshot so refresh reports can detect added/removed nodes, relationships, changed labels, duplicates, and other graph hygiene changes. | Update only through a confirmed canonical graph refresh. Do not edit manually except for explicit debugging that is later reverted or regenerated. |

### Configuration Loader Pair

| Behavior | Python function | PowerShell function |
| --- | --- | --- |
| Decode and load strict framework-registry YAML, enforcing UTF-8 and byte budgets before parsing | `decode_yaml_bytes`, `validate_yaml_source`, and `load_yaml_file` in `strict_yaml.py` | strict byte decoding, `Assert-KnowledgeYamlSource`, and `ConvertFrom-KnowledgeYamlFile` in `Strict-Yaml.ps1` |
| Reject unknown keys in a closed mapping | `assert_allowed_keys` in `strict_yaml.py` | `Assert-KnowledgeMapKeys` in `Strict-Yaml.ps1` |
| Validate the shared RFC 3339 audit profile | `is_rfc3339_timestamp` in `strict_yaml.py` | `Test-KnowledgeRfc3339Timestamp` in `Strict-Yaml.ps1` |
| Resolve repository root | `resolve_project_root`, `is_project_root` in `project_config.py` | `Resolve-KnowledgeProjectRoot`, `Test-KnowledgeProjectRoot` in `Project-Config.ps1` |
| Load and validate project manifest | `load_project_config`, `resolve_manifest_path` in `project_config.py` | `Get-KnowledgeProjectConfig`, `Resolve-ProjectManifestPath` in `Project-Config.ps1` |
| Load and validate pinned lookup-key data | `load_lookup_key_config` in `lookup_key_config.py` | `Get-KnowledgeLookupKeyConfig` in `Lookup-Key-Config.ps1` |
| Normalize a semantic lookup value | `LookupKeyConfig.normalize` | `ConvertTo-KnowledgeLookupKey` |
| Compare normalized lookup keys ordinally | Native string equality | `Test-KnowledgeLookupKeysEqual` |
| Load and validate selected schema packs | `load_schema_pack_registry`, `load_pack` in `schema_pack_config.py` | `Get-KnowledgeSchemaPackRegistry`, `ConvertTo-SchemaPackConfig` in `Schema-Pack-Config.ps1` |
| Inspect capability declaration, lifecycle, availability, and activation | `SchemaPackRegistry.capability_declared`, `capability_definitions_for`, `capability_available`, `capability_enabled` | `Test-SchemaPackCapabilityDeclared`, `Get-SchemaPackCapabilityDefinitions`, `Test-SchemaPackCapabilityAvailable`, `Test-SchemaPackCapabilityEnabled` |
| Resolve controlled-value ownership | `SchemaPackRegistry.allowed_values`, `owner_of`, `owns_value` | `Get-SchemaPackAllowedValues`, `Test-SchemaPackOwnsValue` |
| Resolve controlled-value labels, descriptions, and broader values | `SchemaPackRegistry.definition_of` | `Get-SchemaPackValueDefinition` |
| Parse a shared temporal bound or window | `parse_temporal_bound`, `parse_temporal_window` in `temporal_config.py` | `ConvertTo-KnowledgeTemporalBound`, `ConvertTo-KnowledgeTemporalWindow` in `Temporal-Config.ps1` |
| Compare temporal windows and match a precision-aware effective-time query | `temporal_overlap_outcome`, `temporal_windows_overlap`, `temporal_window_match` | `Get-KnowledgeTemporalOverlap`, `Test-KnowledgeTemporalWindowsOverlap`, `Get-KnowledgeTemporalMatch` |
| Normalize a year/month/date/datetime applicability query | `normalize_effective_at` | `ConvertTo-KnowledgeTemporalInstant` |
| Run portable temporal conformance vectors with optional structured summary output | `test_temporal.py` (`--json`) | `Test-Temporal.ps1` (`-Json`) |
| Load and validate chronology coordinate systems and narrative contexts | `load_chronology_registry`, `parse_chronology_registry` in `chronology_config.py` | `Get-KnowledgeChronologyRegistry`, `ConvertTo-KnowledgeChronologyRegistry` in `Chronology-Config.ps1` |
| Compare chronology positions without guessing across axes | `ChronologyRegistry.compare_positions` | `Get-KnowledgeChronologyComparison` |
| Run portable chronology conformance vectors | `test_chronology.py` | `Test-Chronology.ps1` |
| Load and validate occurrence and recurrence structure | `load_occurrence_registry`, `parse_occurrence_registry` in `occurrence_config.py` | `Get-KnowledgeOccurrenceRegistry`, `ConvertTo-KnowledgeOccurrenceRegistry` in `Occurrence-Config.ps1` |
| Query iteration contents and boundaries, coordinate reuse, track neighbors, recurrence identity and phase, schedule values/due status, carryover, outcomes, pattern rules, subject transitions, and state at a track boundary | `OccurrenceRegistry.occurrences_for_iteration`, `occurrences_for_iteration_on_track`, `previous_before_iteration`, `next_after_iteration`, `occurrences_at_position`, `previous_on_track`, `next_on_track`, `recurrence_for_occurrence`, `phase_for_iteration`, `expected_schedule_value`, `schedule_match`, `carryovers_into`, `outcomes_for_occurrence`, `rules_for_pattern`, `state_transitions_for_subject`, `state_at` | `Get-KnowledgeOccurrencesForIteration`, `Get-KnowledgeOccurrencesForIterationOnTrack`, `Get-KnowledgePreviousBeforeIteration`, `Get-KnowledgeNextAfterIteration`, `Get-KnowledgeOccurrencesAtPosition`, `Get-KnowledgePreviousTrackOccurrence`, `Get-KnowledgeNextTrackOccurrence`, `Get-KnowledgeOccurrenceRecurrence`, `Get-KnowledgeRecurrencePhaseForIteration`, `Get-KnowledgeRecurrenceScheduleValue`, `Get-KnowledgeRecurrenceScheduleMatch`, `Get-KnowledgeCarryoversIntoIteration`, `Get-KnowledgeOutcomesForOccurrence`, `Get-KnowledgeRulesForRecurrencePattern`, `Get-KnowledgeStateTransitionsForSubject`, `Get-KnowledgeStateAt` |
| Evaluate scoped recurrence rules with defaults, execution overrides, deterministic selection, and explainable conflicts | `OccurrenceRegistry.evaluate_rules` | `Get-KnowledgeRecurrenceRuleEvaluation` |
| Resolve stable occurrence-registry provenance targets | `OccurrenceRegistry.provenance_target` | `Get-KnowledgeOccurrenceProvenanceTargets` plus typed lookup |
| Run portable occurrence conformance vectors | `test_occurrence.py` | `Test-Occurrence.ps1` |
| Load and validate taxonomy registry | `load_taxonomy_config`, `parse_content_type`, `parse_category` in `taxonomy_config.py` | `Get-KnowledgeTaxonomyConfig`, `ConvertTo-ContentTypeConfig`, `ConvertTo-CategoryConfig` in `Taxonomy-Config.ps1` |
| Load and validate resource registry | `load_resource_config` in `resource_config.py` | `Get-KnowledgeResourceConfig` in `Resource-Config.ps1` |
| Load and validate source registry | `load_source_registry` in `source_config.py` | `Get-KnowledgeSourceRegistry` in `Source-Config.ps1` |
| Load and validate entity/incarnation/phase registry | `load_entity_registry` in `entity_config.py` | `Get-KnowledgeEntityRegistry` in `Entity-Config.ps1` |
| Expose stable reconciliation targets and owned aliases | Matching `reconciliation_targets` and `reconciliation_provider` methods | Matching `Get-Knowledge*ReconciliationTargets` and `Get-Knowledge*ReconciliationProvider` functions |
| Load and validate stable-ID reconciliation | `load_reconciliation_registry` in `reconciliation_config.py` | `Get-KnowledgeReconciliationRegistry` in `Reconciliation-Config.ps1` |
| Resolve a current or historical stable ID | `ReconciliationRegistry.resolve` | `Resolve-KnowledgeReconciliationTarget` |
| Run portable reconciliation conformance and deep-chain tests with optional structured summary output | `test_reconciliation.py` (`--json`) | `Test-Reconciliation.ps1` (`-Json`) |
| Load and validate cross-registry provenance | `load_provenance_registry` in `provenance_config.py` | `Get-KnowledgeProvenanceRegistry` in `Provenance-Config.ps1` |
| Resolve every entity, incarnation, or identity phase matching a stable ID, label, or alias | `EntityRegistry.resolve_entity_ids`, `resolve_incarnation_ids`, `resolve_identity_phase_ids` | `Resolve-KnowledgeEntityIds`, `Resolve-KnowledgeIncarnationIds`, `Resolve-KnowledgeIdentityPhaseIds` |
| Resolve one unambiguous entity, incarnation, or phase, rejecting shared-name ambiguity | `EntityRegistry.resolve_entity_id`, `resolve_incarnation_id`, `resolve_identity_phase_id` | `Resolve-KnowledgeEntityId`, `Resolve-KnowledgeIncarnationId`, `Resolve-KnowledgeIdentityPhaseId` |
| Resolve typed identity subjects/targets, subject phases, and phase bindings/relationships | `EntityRegistry.identity_subject_targets`, `identity_subject_target`, `identity_targets`, `identity_target`, `phases_for_subject`, `bindings_for_identity_phase`, `relationships_for_identity_phase` | `Get-KnowledgeIdentitySubjectTypes`, `Get-KnowledgeIdentitySubjectTarget`, `Get-KnowledgeIdentityTargetTypes`, `Get-KnowledgeIdentityTarget`, `Get-KnowledgeIdentityPhases`, `Get-KnowledgeIdentityPhaseBindings`, `Get-KnowledgeIdentityPhaseRelationships` |
| Select entity relationships, an entity's incarnations, and an incarnation's bindings/relationships | `EntityRegistry.relationships_for_entity`, `incarnations_for_entity`, `bindings_for_incarnation`, `relationships_for_incarnation` | `Get-KnowledgeEntityRelationships`, `Get-KnowledgeEntityIncarnations`, `Get-KnowledgeIncarnationBindings`, `Get-KnowledgeIncarnationRelationships` |
| Resolve stable entity-registry provenance targets | `EntityRegistry.provenance_target` | `Get-KnowledgeEntityProvenanceTarget` |
| Resolve stable source-registry provenance targets | `SourceRegistry.provenance_target` | `Get-KnowledgeSourceProvenanceTarget` |
| Resolve a composed provenance target | `ProvenanceRegistry.provenance_target` | `Get-KnowledgeProvenanceTarget` |
| Resolve canonical source IDs and aliases | `SourceRegistry.resolve_source_id` | `Resolve-KnowledgeSourceId` |
| Resolve canonical work/book IDs and aliases | `SourceRegistry.resolve_work_id` | `Resolve-KnowledgeWorkId` |
| Select every tied highest-precedence scope from candidate scope IDs | `SourceRegistry.highest_precedence_scopes` | `Get-KnowledgeHighestPrecedenceScopes` |
| Discover semantically applicable scopes and return explainable winner, ambiguity, and indeterminate-time state | `SourceRegistry.applicability_decision` | `Get-KnowledgeApplicabilityDecision` |
| Resolve applicability for provenance claims, including subject inheritance | `ProvenanceRegistry.applicability_decision` | `Get-KnowledgeProvenanceApplicabilityDecision` |
| Resolve explainable claim-specific source authority | `SourceRegistry.authority_decision` | `Get-KnowledgeSourceAuthorityDecision` |
| Resolve claim-specific numeric rank with priority fallback | `SourceRegistry.authority_rank` | `Get-KnowledgeSourceAuthorityRank` |
| Compare multiple authority candidates | `SourceRegistry.compare_authority` | `Compare-KnowledgeSourceAuthority` |
| Evaluate all assertions sharing a stable claim identity | `ProvenanceRegistry.evaluate_claim_authority` | `Get-KnowledgeClaimAuthorityEvaluation` |
| Resolve controlled claim/evidence-mode ancestry | `controlled_value_ancestors` | `Get-SourceControlledValueAncestors` |
| Validate and compare evidence positions and declared source bounds | `validate_source_position`, `validate_structural_position`, `compare_positions`, local source-coverage helpers | `Assert-SourceEvidencePosition`, `Assert-SourceStructuralPosition`, `Compare-SourcePositions`, `Assert-SourceLocatorCoverage` |
| Resolve provenance target field paths | `resolve_provenance_field_path` | `Resolve-ProvenanceRecordFieldPath` |
| Select QA page content roots | `TaxonomyConfig.content_roots_for_qa_pages` | `Get-TaxonomyQaPageContentRoots` |
| Validate category/content-type uniqueness | `ensure_unique`, final checks in `load_taxonomy_config` | `Assert-UniqueTaxonomyValue`, final checks in `Get-KnowledgeTaxonomyConfig` |

Last mapped: 2026-08-01.

Last parity check: 2026-08-01. Python, PowerShell 7, and Windows PowerShell 5.1 loaded manifest schema 9, schema-pack registry schema 2, eight selected packs (`core` 28, `narrative-media` 20, `narrative-publishing` 10, `narrative-screen-audio` 11, `narrative-adaptation` 10, `narrative-distribution` 14, `narrative-production` 4, and `narrative-shared-universe` 9), taxonomy schema 2, resource schema 1, source schema 18, entity schema 4, reconciliation schema 4, provenance schema 3, chronology schema 1, occurrence schema 4, and lookup-key schema 1 with Unicode 16.0.0. V37 validates effect declarations during pack composition, scopes incompatibility globally or by target, and resolves duplicate semantic effects with contributor lineage and deterministic execution counts under idempotent, accumulating, or invalid policy. The LoTM occurrence instance contains only `main`; no loop data is fabricated. Thirteen chronology comparisons, thirteen malformed chronology registries, 67 occurrence query/evaluation/extension assertions, and 67 malformed occurrence cases pass identically in all three runtimes alongside the permanent temporal, reconciliation, strict-ingestion, and lookup baselines.

### Project Manifest Contract

`Project_Config/project.yaml` is the bootstrap configuration copied into each framework implementation. `schema_version`, `project_id`, `framework`, and `domain` identify the contract and implementation. All configured paths must be repository-relative; the shared loaders reject absolute paths, paths that escape the repository, missing canonical roots, and missing required helper, config, or registry files.

`paths.content_roots` is an ordered list. Each entry declares a stable `id`, a `path`, and a provenance rule. Content-type records refer to the stable ID so a root path can change through a migration without changing content-type or category identity:

- `child-directory`: derive the provenance label from the first directory beneath the configured root. The LoTM `Glossary_Threads/Characters/` path therefore contributes `character`.
- `fixed`: use `provenance_label` for every record under that root. The LoTM `Volumes/` root therefore contributes `volume`.
- `slug-prefix`: skip path-based provenance and fall back to the record slug prefix.

`paths.resource_roots` declares stable IDs, repository-relative paths, and whether each non-content resource root must exist. Content-root and resource-root IDs share one namespace. `paths.qa_export` defines the default generated QA destination. `paths.visualization` identifies the Python and PowerShell visualization helpers plus render settings and Puppeteer configuration. `paths.cleanup` identifies the matching disposable-cache cleanup helpers.

`registries.schema_packs`, `registries.taxonomy`, `registries.resources`, `registries.sources`, `registries.chronology`, `registries.occurrences`, `registries.entities`, `registries.reconciliation`, `registries.provenance`, and `registries.lookup_keys` locate the selected-pack, content, resource, source, chronology, occurrence/recurrence, entity/incarnation, stable-ID reconciliation, cross-registry provenance, and pinned Unicode lookup-key registries.

### Schema-Pack Contract

`Project_Config/schema-packs.yaml` selects portable packs from `Framework/Packs/` or a project-owned extension location in dependency order. Each pack declares a stable ID, independent pack version, lifecycle, kind (`core`, `domain`, or `extension`), capabilities, dependencies, and namespaced controlled values. A dependent pack must follow every dependency and satisfy its minimum version.

Pack selection makes capability declarations discoverable. String entries are shorthand for lifecycle `available`; mapped definitions may be `planned`, `available`, or `deprecated`. Planned capabilities cannot be enabled, available capabilities may be enabled, and deprecated capabilities remain activatable only for compatibility or migration. `capability_activation.enabled` enables only eligible capabilities used by the project, and `capability_activation.default` must be `disabled`. Missing capabilities therefore disappear cleanly from unrelated industry implementations, while missing pack dependencies and explicit references to unavailable or disabled contracts remain validation errors.

Controlled values use dotted ownership namespaces such as `source.work-type`. Values may be extended by multiple selected packs, but one exact namespace/value pair has one owner. A value may provide a display label, description, and broader value in the same namespace. The current `core` pack owns generic evidence-source roles and evidence-artifact relationships. `narrative-media` owns the foundation and media-axis vocabularies; publishing, screen/audio, adaptation, distribution, production, and shared-universe companion packs own their narrower release, segment, container, lineage, mapping, manifestation, platform, production/rights, and incarnation values. `anime`, `donghua`, `manga`, `manhwa`, `manhua`, and `webtoon` remain meaningful cultural forms while modality is modeled separately. Embedded visuals may originate in EPUBs, comics, scans, or future supported containers; extraction preserves the `illustration` medium profile, still-image modality, source container, evidence provenance, and any promoted page-ready derivative as separate facts. Source and entity loaders reject configured vocabulary outside the aggregate selected-pack contract.

Pack files define reusable semantics and recommendations. Project registries instantiate them. A narrative pack may define `television-special`; it must not define the LoTM work `lotm-donghua-special-1`. Future setup and editor wizards should read pack capabilities and controlled values, then create project-instance configuration through reviewed mutation services.

### Chronology Registry Contract

`Project_Config/chronology.yaml` instantiates coordinate systems separately from RFC 3339 civil timestamps. Coordinate systems may be calendar, era-ordinal, ordinal, or relative integer axes; declare value domains, direction, zero policy, positions, open or bounded spans, explicit relations, exact direct mappings, and optional pack-gated narrative contexts. Era-local direction supports systems whose values count down in one era and up in another. Years below zero and above 9999 remain ordinary chronology coordinates rather than invalid civil timestamps.

The paired comparison APIs return `before`, `after`, `concurrent`, or `incomparable`. They compare coordinates through intrinsic axis order and the transitive closure of exact relations, relative origins, and equivalent mappings. They validate those facts as one combined acyclic order graph. They do not extrapolate mapping formulas, infer calendar conversions, impose total order across branches, or confuse publication, reader disclosure, causal order, and story chronology. The LoTM registry currently instantiates the five Epochs and a novel-story context but deliberately contains no unsupported dates or anchors.

### Occurrence Registry Contract

`Project_Config/occurrences.yaml` keeps concrete occurrences distinct from templates and coordinates, and concrete recurrence executions distinct from reusable patterns. Branch and recurrence parentage is acyclic; lifecycle and same-recurrence track order are coherent; primary bindings cannot contradict exact chronology; transition profiles enforce track, chronology, containment, and branch semantics; causal cycles remain separate from chronology while semantic duplicates are rejected. Non-overlapping execution phases and typed schedules feed bounded rules with subject-qualified conditions, explicit applicability, defaults/overrides, priority, selection mode, conflict reporting, and explainable traces. Pack composition validates rule/effect compatibility, recurrence-pattern effect scope, one repetition policy per effect, and canonical global or same-target incompatibility pairs. Evaluation groups semantic effects and reports contribution count, execution count, and contributing rule/effect IDs. Civil schedule projection is portable only within years `0001` through `9999`, while chronology-step schedules remain integer-coordinate operations. Subject-state transitions identify acquisition, availability, optional attitude, activation, and sources; carryover references the applicable state across a participating iteration boundary. Every stable record shape is exposed to centralized provenance, while chronology and provenance retain order and evidence authority respectively.

### Taxonomy Registry Contract

`Project_Config/taxonomy.yaml` separates `categories` from `content_types`. A Glossary Page requires a category; an Investigation Record permits a category for subject-linked research while allowing uncategorized project investigations; Volume Summary, Analysis Board, Project Dashboard, and Navigation Index records forbid categories. Categories define subject identity once and provide placements under eligible content types, so Character glossary pages and Character investigations share the `character` category without pretending to be the same record type. Fixed-file records identify one existing repository-relative file beneath their content root; root-file records discover matching files directly beneath a root. Default templates are optional for content types that do not scaffold records.

Deferred categories remain visible to planning and future editors but set `canonical_pages_enabled: false` and intentionally omit subject slugs, placements, and graph classes until promotion. The paired taxonomy loaders reject malformed stable IDs, unknown root/content-type references, incompatible category policies, absolute or escaping relative paths, invalid slug regular expressions, missing required templates or fixed files, duplicate metadata types, duplicate subject prefixes, duplicate placements, duplicate fixed record paths, and duplicate graph classes.

The QA exporters now use content-type `qa_page_enabled` values to select page roots, which keeps investigations out of the Obsidian page mirror. Transitional category output maps and graph semantics remain in QA/visualization code until the normalized content-index and visualization migrations replace them.

### Resource Registry Contract

`Project_Config/resources.yaml` separates broad `resource_kinds` from concrete `resource_types`. Kinds provide stable groupings such as asset, source, component, generated output, workspace support, and temporary resource. Types assign lifecycle, authority, editor eligibility, and one or more placements beneath manifest-configured resource roots.

Tracking values describe expected storage behavior: `tracked`, `ignored`, or `mixed`. A required placement must exist; optional ignored roots may be absent from a fresh clone. Resource placement does not make a file a content record or graph node. The paired resource loaders reject malformed IDs, unknown kind/root references, unsupported lifecycle/authority/tracking values, absolute or escaping paths, missing required placements, and duplicate placements.

### Source Registry Contract

`Project_Config/sources.yaml` separates media facets, work groups, continuities, creative works, applicability scopes, scoped continuity and claim supersession, production/right contexts, work segments, named orderings, adaptation mappings, manifestations, release records, platform catalogs/offerings, and evidence sources. A medium is specifically a reader-position/citation profile, references one or more modalities plus compatible cultural forms, identifies the position field that carries canonical work scope, and may select a pack-owned structural-validation strategy. The current novel profile binds `volume` and `chapter` to verified work volume catalogs without duplicating chapter ranges. Works separately declare release form and lifecycle status. Reusable scopes select a controlled target and independently carry territory, effective time, and explicit precedence. The decision APIs discover exact and structurally containing scopes, honor territory ancestry and shared temporal-window semantics, preserve open and exclusive bounds, report uncertain or unknown timing without promoting it to an exact winner, and return all tied highest-precedence winners without hidden specificity. Production contexts retain their owning work and reference one of those scopes for exact applicability. Sources separately declare their concrete container formats and permitted locator media. This allows a Donghua film, segment-scoped web parody, commercial parody film, or EPUB-contained illustration to retain every relevant axis without compound IDs or inferred legal status. Work groups may represent franchises, ordered series, heterogeneous adaptation programs, or unordered collections and may nest beneath a parent group. A work defines stable identity, group and continuity memberships, display aliases, numbering mode, release form, status, and a verified, pending, or inapplicable volume catalog.

Segments provide stable configurable parts beneath a work. Their single parent owns structural containment; `content_groups` separately collect works, segments, or reusable content groups into arcs, sagas, crossovers, publication units, collections, or reading paths. Group members have globally stable IDs and controlled participation roles that do not imply sequence; nested groups remain acyclic, and an optional ordering scheme must exactly cover the typed members. Numbering schemes assign display numbers and aliases without implying sequence, while named total or partial ordering schemes can order works, segments, or groups by release, publication, story, production, or recommendation without overwriting another order. Partial schemes use acyclic predecessor references and allow concurrency. Adaptation mappings connect one or more basis works and optional registered segments to a target using controlled correspondence and basis roles. Manifestations may cover a whole work or selected segments, and mappings between related manifestations describe retained, omitted, added, altered, replaced, reordered, combined, or split material. Release components may originate in a manifestation or exist through package membership; typed component relationships preserve revision, translation, dub, and derivation lineage. Commercial packages, phased release runs, concrete events, and platform offerings own bundled material, schedules, launches, segment scope, and structured availability. Localized title variants have stable IDs, optional validity windows, and distinct title purpose, lifecycle, primary display, and romanization; variants in the same locale scope must have nonoverlapping known windows. Catalog placements target works, segments, content groups, manifestations, or packages without redefining canonical hierarchy. Hierarchical territories and external identifier schemes preserve regional and provider identity separately from internal stable IDs.

A source selects one or more works, a primary medium profile, and an allowlist of locator media. Singular release bindings serve simple evidence artifacts, while repeatable typed observations identify every manifestation, package, event, component, or offering inspected by composite evidence. Stable coverage entries state how much material is present for one locator medium and one or more source-supported evidence modes; range endpoints must use identical fields, name the same canonical work through that medium's configured work-scope field, follow configured sort order, satisfy available structural data, and remain inside the target's resolved work scope. Overlapping declarations for the same target, medium, and mode are invalid. Standalone provenance assertions declare a stable claim key and controlled namespace, target source- or entity-provider records, resolve any dotted/indexed field path against that normalized target, snapshot the asserted value plus observation/effective timing, and attach supporting, contradicting, or contextual evidence through one or more globally stable locators. Repeated claim keys retain one subject/namespace/field shape but may preserve corroborating or conflicting values. Each locator explicitly selects an allowed medium and is either one valid point or a correctly ordered range within matching channel coverage. Verified and inferred assertions require supporting evidence; disputed assertions require both supporting and contradicting evidence.

Creative lineage uses controlled work relationships such as sequel, spinoff, side story, adaptation, remake, retelling, parody, crossover, containment, compilation, and inspiration. A relationship may reference an applicability scope only when that scope resolves entirely to its source work, allowing a parody sketch or segment without claiming that the whole containing work is a parody. Parody lineage remains independent of production origin, authorization, rights basis, commerciality, and distribution; detailed reused, condensed, recontextualized, or original material belongs in adaptation mappings. Scoped continuity can qualify a work, segment, content group, or stable claim. Claim supersession preserves acyclic replacement/reinterpretation history between claims with one subject/namespace/field shape. Evidence-artifact lineage uses separate controlled source relationships such as edition, translation, transcript, subtitle track, dub, scan, extract, and package membership. Every relationship type declares a reciprocal inverse; symmetric types name themselves as their inverse.

Authority profiles define accepted continuity memberships, continuity order, source-priority direction, which derivative-work relationships are comparable, and optional claim-specific rules. Reader positions use canonical `book` work IDs before work-local volume and chapter values. Rules can rank sources by source ID, role, medium, or evidence mode. A rule also applies to descendant claim namespaces and evidence modes; the highest explicit precedence wins and tied winners are rejected. Ordinary source priority remains the fallback. Candidate comparison reports a winner, tie, or incomparable set. Stable-claim evaluation additionally distinguishes equally authoritative conflicting values from corroborating ties. Under the default `lotm-adaptation-comparison` profile, source-scoped claims are preserved and authority varies appropriately among canonical content, dialogue, visual design, localization, and release metadata rather than forcing one artifact to lead every question.

The current Visualization reader-boundary settings and Obsidian bounded graph/page arguments do not yet expose a work selector and are implicitly `lotm-1` workflows. Before generating COI or cross-book bounded output, the normalized content-index/visualization migration must add registry-backed `book`/work selection to those interfaces. A chapter number alone must never select a work.

New evidence-provenance records should use canonical `source_id` values. Legacy evidence labels resolve through aliases during migration. Field-scoped validation must not reinterpret Relationship Seed `source` entity slugs or type-specific causal-source fields as evidence-source IDs.

The paired source loaders reject malformed identity, media, work, continuity, applicability, ordering, authority, adaptation, manifestation, release, territory, platform, source, coverage, relationship, identifier, alias, and resource-binding records. The paired provenance loaders separately reject unsupported or missing cross-registry targets, duplicate assertion or locator IDs, unresolved field paths, invalid claim shapes and statuses, undeclared evidence sources/media/modes, malformed or out-of-scope positions and ranges, evidence outside matching coverage, invalid evidence-role combinations, missing or incompatible supersession claims/scopes, and supersession cycles.

### Entity Registry Contract

`Project_Config/entities.yaml` separates continuity-independent conceptual entities from continuity-bound incarnations and continuity-specific identity phases. Entities declare one primary taxonomy category and one or more total category memberships. Typed entity relationships preserve succession, namesakes, legacy/mantles, cloning, splinters, derivation/composites, inspiration, and class/instance identity. Incarnations reference one entity, one primary continuity, and one or more status-bearing continuity memberships. Scope-backed bindings identify where an incarnation or phase applies without duplicating source-registry target, territory, time, or precedence fields. Identity phases require persistent identity, explicitly type the owning entity/incarnation and continuity, and use inverse-normalized acyclic succession rather than inferred chronology.

The paired entity loaders require the selected and enabled `entity-incarnations` and `entity-identity-phases` capabilities and consume normalized schema-pack, taxonomy, and source registries. They expose ambiguity-preserving plural name resolution, strict singular resolution, entity relationships, entity-to-incarnation, subject-to-phase, and binding/relationship queries; narrow identity/reconciliation target providers; and stable provenance-target lookup for all record layers. Relationship types explicitly declare semantic canonical direction and may share acyclic groups; inverse-form duplicates are one repeated fact. The standalone reconciliation and provenance services consume those typed targets while keeping identity history, assertions, and locators out of `entities.yaml`. The current LoTM registry deliberately contains no entities, incarnations, or phases and provides twenty entity, eight incarnation, and two phase relationship-type definitions. Page linkage and existing-subject migration remain later work.

The loaders reject unsupported schema/capability state, malformed IDs, unknown or empty category memberships, a primary category outside the membership list, unknown entities/continuities/scopes, duplicate aliases, missing primary continuity memberships, unsupported statuses, phase types, basis roles, or binding/relationship types, basis roles on non-lineage relationships, invalid phase subjects or incarnation-continuity combinations, phase bindings without canonical work scope or outside the phase continuity, cross-subject or cross-continuity phase succession, inconsistent inverse definitions, unknown endpoints, self-relationships, cycles, and duplicate or inverse-duplicate bindings/relationships.

### Reconciliation Registry Contract

`Project_Config/reconciliation.yaml` schema 4 is loaded after the project has assembled stable-record providers enabled by its packs. The current LoTM composition supplies 24 target types from taxonomy, resources, sources, and entities, but the loader itself imports no narrative registry and accepts domain-specific providers from other implementations. Each provider has a stable ID plus current-record and alias-key maps. Target-type values and installed providers must close exactly, two providers cannot claim the same type, and a tombstoned stable ID cannot also remain an alias. The root, resolution, record, target, and audit mappings are closed shapes; active present sources permit only redirect compatibility; and record, target, branch, and traversal budgets are mandatory.

Every record preserves a typed source ID, current presence or tombstone state, privacy-aware snapshot/redacted/omitted label mode, pack-approved operation/reason pair, active/superseded/reversed status, and repository-derived or strict explicit audit metadata. Redirect, merge, and split preserve type; reclassification alone crosses type. Active chains must be acyclic and terminate at current records or retirements, while superseded decisions lead to one active decision for the same source. Memoized iterative resolution returns canonical, redirected, ambiguous, or retired outcomes, deduplicated terminal summaries, and ordered branches with independent paths. `resolution.max_records`, `max_targets_per_record`, `max_branches`, and `max_resolution_steps` independently bound registry size, direct fan-out, terminal split expansion, and traversal work. The resolver never chooses or erases a split branch and never mutates a page, path, alias, graph, or registry reference.

The paired conformance tools accept only repository-root and deep-chain-size overrides and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run default corpus and 1,500-hop stress case | `python Tools/test_reconciliation.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Test-Reconciliation.ps1` |
| Emit structured corpus and stress-test counts | `python Tools/test_reconciliation.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Test-Reconciliation.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |
| Override stress depth | `--deep-chain N` | `-DeepChain N` |

Both load the canonical project composition, validate canonical mapping keys through `Framework/Data/Strict-Yaml/`, layer synthetic records into process-local fixture providers, validate the malformed-policy, byte-budget, branch/step-limit, and expected-result corpus in `Framework/Data/Reconciliation/`, create uniquely named malformed-byte and deep-chain files in the operating-system temporary directory, and remove them before exit.

### Provenance Registry Contract

`Project_Config/reconciliation.yaml` schema 4 is loaded after stable-record providers and before provenance. Its paired loaders enforce canonical YAML ingestion, pack/provider closure, alias ownership, record/fan-out/branch/traversal bounds, and history invariants, then resolve current or historical IDs without mutating files. `Project_Config/provenance.yaml` schema 3 then composes source, entity, and reconciliation provenance providers. The paired provenance APIs own assertion parsing, semantic field-path resolution, evidence-link and locator validation, stable claim grouping, scope-backed acyclic claim supersession, cross-registry target integrity, and shared-kernel observation/effective timing. `ProvenanceRegistry.evaluate_claim_authority` / `Get-KnowledgeClaimAuthorityEvaluation` delegate evidence ranking to source authority decisions and then report winner, tie, conflict, or incomparable outcomes.

The source registry remains authoritative for evidence artifacts, permitted media and modes, work and release-object scope, coverage, structural position validation, and authority profiles. Subject registries remain authoritative for normalized target records. Neither source nor entity registries store an assertion collection. A new target registry participates by exposing typed stable-record lookup and supplying its `provenance.subject-type` values through a selected pack.

### Future Config Extensions

Controlled relationship types, field-scoped enums, aliases, and confidence/precedence rules remain planned additions to the taxonomy registry through reviewed migrations. Capability-gated omission of registry files and controlled-value providers remains project-composition/bootstrap work; the current manifest requires its declared registry paths even when a downstream implementation would disable the corresponding capability.
