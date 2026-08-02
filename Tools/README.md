# Tools

This folder contains reusable local helpers for project maintenance and source verification.

For switch-by-switch maps, function-pipeline notes, side effects, parity checks, and durable config/state files for maintained helper scripts, see [Tooling Reference](TOOLING_REFERENCE.md). That reference should be extended whenever another tool is audited or a tool starts reading a new shared config file. The broader version process belongs to the [Framework Improvement Lifecycle](../Framework/framework_improvement_lifecycle.md), while the cumulative requirement for when and why checks run belongs to the [Framework Testing Methodology](../Framework/testing_methodology.md).

Paired validation and conformance commands that emit a human-readable summary also support `--json` / `-Json` with matching semantic fields. File-producing tools may instead define structured generated artifacts; see the Tooling Reference rather than assuming every command uses one universal JSON summary.

The runtime-package/module boundaries, command layout, root-discovery contract, parity policy, and wrapper rules live in [ARCHITECTURE.md](../ARCHITECTURE.md#tool-runtime-and-command-architecture). The complete current inventory lives in [Tooling Reference](TOOLING_REFERENCE.md#tool-architecture-inventory). Reusable loaders belong under `Runtime/`, executable user workflows under `Commands/`, registered test runners under `Conformance/`, and repository policy tools under `Static/`; do not add new flat root-level scripts.

## Environment Checks

Use `Test-Python.ps1` to check whether Python is present and actually usable before selecting Python-preferred tools. It tests `python`, `python3`, and `py` in order, verifies that `--version` works, confirms that Python can report `sys.executable`, and checks repository Python requirements from `requirements-python.txt`, including Ruff for source formatting.

Run this probe once for an unfamiliar machine or fresh agent session, then treat the result as the session's Python-availability state. If Python is available, use Python-preferred tools going forward without rerunning the probe before every command. Rerun only if the environment changes, such as PATH edits, Python installation changes, a different shell, a different machine, or a failed Python launch that suggests the earlier state is stale.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-Python.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-Python.ps1 -Json
```

If Python is available but required modules are missing, install the repository Python dependencies:

```powershell
python -m pip install -r requirements-python.txt
```

For the full candidate order, switch behavior, JSON fields, side effects, and latest local check note, see [Tooling Reference](TOOLING_REFERENCE.md#python-environment-check).

## Python Source Formatting

Ruff formats and checks every tracked or nonignored untracked `.py` or `.pyi` source anywhere in the Git worktree. `pyproject.toml` excludes Markdown code fences and owns the Python 3.10 compatibility target, 120-character line length, LF output, and formatting rules.

Check formatting and line length without writing files:

```powershell
python -m ruff format --check .
python -m ruff check .
```

Apply canonical formatting, then verify the remaining line-length gate:

```powershell
python -m ruff format .
python -m ruff check .
```

Ruff handles deterministic mechanical layout. Manually split long strings, regexes, or report rows that the formatter cannot safely rewrite; do not suppress or weaken the line-length rule merely to make the check green. Gitignored local/generated Python files remain outside the default policy unless passed explicitly.

If the probe reports Python unavailable, use the documented PowerShell fallback scripts for that session. If Python is available but a Python tool fails, treat that as a tool/script failure rather than silently falling back.

PowerShell fallback commands use `powershell`, which targets Windows PowerShell 5.1 on many Windows machines even when PowerShell 7 is also installed as `pwsh`. Keep `.ps1` fallback scripts compatible with Windows PowerShell 5.1 syntax and APIs unless a tool explicitly documents a PowerShell 7 requirement.

Use `Test-PowerShell.ps1` to check repository PowerShell module requirements from `requirements-powershell.txt` before using fallback tools or PowerShell maintenance tools that need modules. The PowerShell Obsidian QA exporter requires `powershell-yaml`; source formatting requires `PSScriptAnalyzer`.

Run this probe once for an unfamiliar machine or fresh agent session, then treat the result as the session's PowerShell-module readiness state. Rerun only if the environment changes, such as module installation changes, a different PowerShell edition, a different machine, or a failed fallback command that suggests the earlier state is stale.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-PowerShell.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-PowerShell.ps1 -Json
```

If required PowerShell modules are missing, install them from an internet-enabled PowerShell session as needed. Current-user installs are usually sufficient; maintainers who prefer machine-wide module availability may use `-Scope AllUsers` from an elevated PowerShell session. For the current registry:

```powershell
Install-Module powershell-yaml -Scope CurrentUser -Force -AllowClobber
Install-Module PSScriptAnalyzer -Scope CurrentUser -Force
```

## PowerShell Source Formatting

Use `Format-PowerShell.ps1` to check every tracked or nonignored untracked PowerShell source anywhere in the Git worktree. New scripts and new source directories are discovered automatically. Check mode is the default and does not write files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Static\Format-PowerShell.ps1
```

Use `-Fix` to apply the repository formatter:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Static\Format-PowerShell.ps1 -Fix
```

The formatter uses `Tools/Static/powershell-format-settings.psd1`, writes UTF-8 without a BOM and CRLF line endings, removes optional statement-terminating semicolons, preserves required `for (...)` separators, verifies parse/token equivalence, and rejects lines longer than 200 characters. Gitignored files are excluded from the default repository policy. Use `-Path`, `-MaximumLineLength`, or `-Json` for targeted checks, an explicit line-length gate, or structured results. Relative explicit paths resolve from the repository root. Manual wrapping is still required when a long expression cannot be changed mechanically without obscuring semantics.

## Work-Annotation Validation

Use the canonical Python linter to enforce `WORK_ANNOTATION_STANDARDS.md` across tracked and nonignored untracked implementation surfaces:

```powershell
python Tools\Static\lint_work_annotations.py
python Tools\Static\lint_work_annotations.py --json
```

Every normal run validates the permanent valid/invalid fixture corpus before scanning repository files. Use `--fixtures-only` when changing policy, repeat `--path` for focused diagnosis, and use `--root` only when automatic project discovery is intentionally overridden. `Tools/Static/work-annotations.json` owns the executable tags, owners, extensions, exclusions, prohibited locations, and safety bound. The tool is a canonical repository-policy implementation, not a project-domain feature requiring a PowerShell fallback.

## Continuous Integration

The tracked workflow at `.github/workflows/ci.yml` runs for pull requests, pushes to `main`, and intentional manual dispatches. Ordinary feature-branch checkpoint pushes do not start CI unless that branch already participates in an open pull request. The workflow preserves four stable check names for future repository rules:

- `Workflow Policy`
- `Python Validation`
- `PowerShell 7 Validation`
- `Windows PowerShell 5.1 Validation`

`Workflow Policy` validates every GitHub Actions workflow with `actionlint`. The workflow downloads a checksum-pinned standalone actionlint release for itself; local maintainers may install the official executable system-wide and run this preflight from the repository root:

```powershell
actionlint -color
```

The runtime jobs install their declared dependencies, enforce Python and PowerShell formatting, enforce work-annotation policy, run permanent framework conformance suites, validate the visualization projection, generate redirected QA smoke exports beneath fresh `.tmp/` parents, and reject repository-root or outside-repository QA destinations. Keep action SHAs immutable. Treat the four job names as a public policy surface: rename one only with the same care as changing a required status check.

## Temporary File Cleanup

Use `clean_temp_files.py` to remove disposable local cache directories when Python is available. It is the preferred implementation because it is portable across Windows, macOS, and Linux while matching the rest of the repository's Python-preferred tool convention.

`Clean-TempFiles.ps1` is the Windows PowerShell fallback for users who do not have Python installed.

By default, both scripts only target allowlisted cache directories under the repository root:

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
python Tools\Commands\Maintenance\clean_temp_files.py
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1
```

Use `--delete` / `-Delete` to actually remove the matching cache directories:

Preferred Python:

```powershell
python Tools\Commands\Maintenance\clean_temp_files.py --delete
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1 -Delete
```

Use `--include-tmp` / `-IncludeTmp` to include direct children of the ignored repository `.tmp/` folder. This is useful after parity checks, bounded-graph experiments, EPUB extraction checks, or other local QA runs:

Preferred Python:

```powershell
python Tools\Commands\Maintenance\clean_temp_files.py --include-tmp
python Tools\Commands\Maintenance\clean_temp_files.py --include-tmp --delete
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1 -IncludeTmp
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1 -IncludeTmp -Delete
```

Tools that create disposable `.tmp` artifacts automatically should use scoped cleanup instead of broad `.tmp` cleanup. Pass the exact path created during that run with `--tmp-path` / `-TmpPath`; the helper will delete only that path and only if it resolves under repository `.tmp/`.

Preferred Python:

```powershell
python Tools\Commands\Maintenance\clean_temp_files.py --tmp-path .tmp\tool-run-id --delete
```

PowerShell fallback:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1 -TmpPath .tmp\tool-run-id -Delete
```

Use `--json` / `-Json` when downstream tooling needs structured results.

The Python Obsidian QA export and visualization refresh helpers invoke the Python cleanup helper at the end of normal runs so transient `__pycache__` folders do not linger. Run the cleanup command directly when a tool exits early, when using fallback scripts, or when reviewing cache cleanup behavior by itself.

For the full cleanup switch map, allowlist, side effects, and Python/PowerShell parity notes, see [Tooling Reference](TOOLING_REFERENCE.md#temporary-file-cleanup).

## Image Manipulation

Use `edit_image.py` for repeatable local image operations when Python with Pillow is available. It is the preferred implementation because it is faster and shares one CLI for crop operations, named crop presets, and EPUB image listing/extraction.

The current archive adapter extracts images from EPUB containers, but the framework model is not EPUB-specific: manga, manhwa, manhua, scans, and other narrative releases may also contain extractable visual assets. Future format adapters should preserve the registered evidence source as provenance, write bulk extraction to ignored staging, and promote only deliberately selected page-ready assets.

Image extraction and crop commands should write bulk official artwork outputs under the ignored local staging umbrella `Artwork/Source/`. Keep that folder out of Git. When a maintained page needs a specific embedded image, copy only that selected page-ready asset into a tracked folder such as `Artwork/page-assets/`.

PowerShell fallbacks are maintained for Windows users who do not have Python installed:

- `Edit-Image.ps1` mirrors crop operations, named crop presets, and EPUB image listing/extraction.

List available presets:

```powershell
python Tools\Commands\Media\edit_image.py --list-presets
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -ListPresets
```

Use the official pathway tarot-card crop preset:

```powershell
python Tools\Commands\Media\edit_image.py --preset PathwayTarotCard --source-image <source-image> --output-image <output-image> --force
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Preset PathwayTarotCard -SourceImage <source-image> -OutputImage <output-image> -Force
```

Name tarot-card crops with the tarot-card slug first and the pathway slug second:

```text
Artwork\Source\tarot-cards\pathways\<tarot-card-slug>-<pathway-slug>-pathway.png
```

Example:

```powershell
python Tools\Commands\Media\edit_image.py --preset PathwayTarotCard --source-image Artwork\Source\extracted\volume-2-faceless\0023-spine-0505-pathways-pathways4.jpeg --output-image Artwork\Source\tarot-cards\pathways\world-planter-pathway.png --force
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Preset PathwayTarotCard -SourceImage Artwork\Source\extracted\volume-2-faceless\0023-spine-0505-pathways-pathways4.jpeg -OutputImage Artwork\Source\tarot-cards\pathways\world-planter-pathway.png -Force
```

Use the official pathway central-symbol crop preset as a review starting point:

```powershell
python Tools\Commands\Media\edit_image.py --preset PathwaySymbol --source-image <source-image> --output-image <output-image> --force
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Preset PathwaySymbol -SourceImage <source-image> -OutputImage <output-image> -Force
```

Name pathway-symbol crops by source section or volume and pathway slug:

```text
Artwork\Source\extracted\pathway-symbols\<section-or-volume>\<pathway-slug>-pathway-symbol.jpg
```

Example:

```powershell
python Tools\Commands\Media\edit_image.py --preset PathwaySymbol --source-image Artwork\Source\extracted\volume-1-clown\0009-spine-0223-pathways-pathways3.jpeg --output-image Artwork\Source\extracted\pathway-symbols\volume-1-clown\sleepless-pathway-symbol.jpg --force
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Preset PathwaySymbol -SourceImage Artwork\Source\extracted\volume-1-clown\0009-spine-0223-pathways-pathways3.jpeg -OutputImage Artwork\Source\extracted\pathway-symbols\volume-1-clown\sleepless-pathway-symbol.jpg -Force
```

Unlike the tarot-card preset, pathway symbols should be visually reviewed per image. The preset captures the common guide-page symbol area, but individual pages may need manual crop refinement before promotion or mapping.

Use an explicit custom crop when a future image job needs different geometry:

```powershell
python Tools\Commands\Media\edit_image.py --operation crop --source-image path\to\source.jpeg --output-image path\to\crop.png --x 24 --y 804 --width 660 --height 1168
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Operation Crop -SourceImage path\to\source.jpeg -OutputImage path\to\crop.png -X 24 -Y 804 -Width 660 -Height 1168
```

For the full image helper switch map, operation aliases, side effects, and Python/PowerShell parity notes, see [Tooling Reference](TOOLING_REFERENCE.md#image-manipulation).

## EPUB Search

Use `search_epub.py` for repeatable novel EPUB sweeps when Python is available. It is the preferred implementation because it is faster, uses only the Python standard library, and exposes reusable functions that can later support generated indexes or frontend tooling. `Search-Epub.ps1` remains the Windows PowerShell fallback with matching behavior.

Current entry discovery is specific to the Book 1 EPUB package layout. Supplying `Source/Circle of Inevitability.epub` currently yields no discovered entries even though the package contains sequential chapter files. The source registry already models COI as work `lotm-2`; a later search-tool migration must select a registered work/source and support its package adapter before COI searches are considered reliable.

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

Most EPUB search workflows follow this shape. Replace the pattern and filters with the evidence boundary for the current question:

```powershell
python Tools\Commands\Media\search_epub.py --pattern "<term-a>|<term-b>" --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -Pattern "<term-a>|<term-b>" -CountsOnly
```

### Survey Counts

Use this first to find candidate chapters and term clusters.

Preferred flags are `--counts-only` / `-CountsOnly`; the shorter aliases `--counts` / `-Counts` are also accepted.

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 10 --end-chapter 47 --pattern "Dunn|Captain|Nighthawk|Nightmare|Sleepless" --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 10 -EndChapter 47 -Pattern "Dunn|Captain|Nighthawk|Nightmare|Sleepless" -CountsOnly
```

Full-book or later-volume sweeps use the same global chapter numbers:

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 483 --end-chapter 732 --pattern "Gehrman|Traveler" --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 483 -EndChapter 732 -Pattern "Gehrman|Traveler" -CountsOnly
```

You can also narrow by volume without remembering the chapter span:

```powershell
python Tools\Commands\Media\search_epub.py --volume 3 --pattern "Gehrman|Traveler" --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -Volume 3 -Pattern "Gehrman|Traveler" -CountsOnly
```

### Term Summary

Use `--term-summary` / `-TermSummary` when comparing competing names or aliases. It aggregates each literal pipe-separated term across the selected entries and splits counts by EPUB volume.

Preferred flags are `--term-summary` / `-TermSummary`; the aliases `--summary-only`, `--summary`, `-SummaryOnly`, and `-Summary` are also accepted.

```powershell
python Tools\Commands\Media\search_epub.py --pattern "savant|artisan|paragon" --term-summary
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -TermSummary
```

Use `--json` / `-Json` when downstream tooling needs structured summary rows:

```powershell
python Tools\Commands\Media\search_epub.py --pattern "savant|artisan|paragon" --term-summary --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -TermSummary -Json
```

### Entry Listing

Use `-ListEntries` to inspect the EPUB's searchable sections without searching for a term.

```powershell
python Tools\Commands\Media\search_epub.py --entry-type All --list-entries
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -EntryType All -ListEntries
```

Examples for non-main sections:

```powershell
python Tools\Commands\Media\search_epub.py --entry-type SideStories --list-entries
python Tools\Commands\Media\search_epub.py --entry-type Appendices --entry-name-pattern "*pathways*" --list-entries
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -EntryType SideStories -ListEntries
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -EntryType Appendices -EntryNamePattern "*pathways*" -ListEntries
```

### Non-Chapter Searches

Search side stories, appendices, artwork text, front matter, or every XHTML section with `--entry-type` / `-EntryType`.

```powershell
python Tools\Commands\Media\search_epub.py --entry-type SideStories --pattern "3-0782" --counts-only
python Tools\Commands\Media\search_epub.py --entry-type Appendices --entry-name-pattern "*pathways*" --pattern "Seer" --counts-only
python Tools\Commands\Media\search_epub.py --entry-type All --pattern "Evernight" --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -EntryType SideStories -Pattern "3-0782" -CountsOnly
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -EntryType Appendices -EntryNamePattern "*pathways*" -Pattern "Seer" -CountsOnly
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -EntryType All -Pattern "Evernight" -CountsOnly
```

### Candidate Hits

Use this to inspect where matches occur without expanding much context.

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 10 --end-chapter 13 --pattern "Dunn|Nighthawk" --max-hits-per-chapter 20
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 10 -EndChapter 13 -Pattern "Dunn|Nighthawk" -MaxHitsPerChapter 20
```

### Context Expansion

Use this after candidate chapters are known.

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 12 --end-chapter 13 --pattern "Dunn|Nighthawk" --context-lines 2 --max-hits-per-chapter 8
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 12 -EndChapter 13 -Pattern "Dunn|Nighthawk" -ContextLines 2 -MaxHitsPerChapter 8
```

### Regex Search

By default, `--pattern` / `-Pattern` treats `|` as a separator between literal search terms. Python also accepts `--query`, `--text`, and `--search`, and PowerShell also accepts `-Query`, `-Text`, and `-Search`, as ergonomic aliases for the same search text. Use `--regex-pattern` / `-RegexPattern` when a regular expression is genuinely needed.

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 1 --end-chapter 1394 --pattern "red (chimney|smokestack)" --regex-pattern --counts-only
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 1 -EndChapter 1394 -Pattern "red (chimney|smokestack)" -RegexPattern -CountsOnly
```

### JSON Output

Use `-Json` when downstream tooling or Codex needs structured results instead of human-readable chapter blocks.

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 17 --end-chapter 17 --pattern "Sleepless" --context-lines 1 --max-hits-per-chapter 1 --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 17 -EndChapter 17 -Pattern "Sleepless" -ContextLines 1 -MaxHitsPerChapter 1 -Json
```

JSON output includes `entry_type`, `volume`, `chapter`, `title`, and `source_path` fields where available.

Use `--include-line-match-counts` / `-IncludeLineMatchCounts` with JSON hit output when a matched line may include the same term more than once or multiple competing terms.

```powershell
python Tools\Commands\Media\search_epub.py --pattern "savant|artisan" --context-lines 2 --max-hits-per-chapter 100 --json --include-line-match-counts
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -Pattern "savant|artisan" -ContextLines 2 -MaxHitsPerChapter 100 -Json -IncludeLineMatchCounts
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
python Tools\Commands\Media\search_epub.py --pattern "savant|artisan|paragon" --term-summary
python Tools\Commands\Media\search_epub.py --pattern "savant|artisan|paragon" --counts-only --json
python Tools\Commands\Media\search_epub.py --pattern "savant|artisan|paragon" --context-lines 2 --max-hits-per-chapter 100 --json --include-line-match-counts

powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -TermSummary
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -CountsOnly -Json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -Pattern "savant|artisan|paragon" -ContextLines 2 -MaxHitsPerChapter 100 -Json -IncludeLineMatchCounts
```

Raw counts can mislead when a term is also a job, epithet, or individual label. For example, `artisan` may outnumber `savant` while mostly referring to an item-maker or a specific person, whereas `Savant pathway` is stronger evidence for the canonical pathway slug.

For the full EPUB search switch map, entry-type behavior, side effects, and Python/PowerShell parity notes, see [Tooling Reference](TOOLING_REFERENCE.md#epub-search).

## Obsidian QA Export

Use `obsidian_qa_export.py` to compile glossary metadata, Relationship Seeds, YAML data-block references, and projected data-block availability into a generated Obsidian-friendly mirror. It is the preferred implementation when Python is available. If Python is unavailable, use the Windows PowerShell fallback `Obsidian-QA-Export.ps1`. The export is a QA view, not a source of truth. Canonical project notes remain under `Glossary_Threads/`, `Investigations/`, `Volumes/`, and related source folders.

The [Architecture Contract](../ARCHITECTURE.md) assigns all graph semantics and generation to the reusable Visualization engine while QA retains orchestration and ignored output destinations. The two directly generated QA relationship graph variants are current transition behavior; migrate their builders into Visualization rather than adding new graph logic to the QA exporter.

Default output goes to ignored local directory `Obsidian_Export/`:

```powershell
python Tools\Commands\QA\obsidian_qa_export.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\QA\Obsidian-QA-Export.ps1
```

Custom `--output-dir` / `-OutputDir` destinations must be child directories beneath the repository root. Safe missing parent directories are created automatically. The repository root itself and paths outside it are rejected before `--clean` / `-Clean` can remove anything; this does not affect the normal `<repo>/Obsidian_Export/` destination.

When `--root` / `-Root` is omitted, project-aware tools use the shared runtime resolver. It checks an explicit root, `KNOWLEDGE_PROJECT_ROOT`, current-directory ancestors, then executable-location ancestors for `Project_Config/project.yaml`; `.git` is not a project marker, and discovery never changes caller location. Commands can therefore launch from repository descendants or unrelated working directories without path-sensitive behavior. The manifest supplies stable content/resource-root IDs, provenance behavior, registry locations, the default QA output path, visualization integration paths, and cleanup helper paths. `Project_Config/schema-packs.yaml` selects reusable contracts from `Framework/Packs/` and explicitly enables project capabilities. Planned capabilities remain declared but unavailable; available or deprecated capabilities remain disabled until enabled. `Project_Config/taxonomy.yaml` defines content-type/category routing and marks which content types participate in QA page discovery; `Project_Config/resources.yaml` separately describes framework assets, non-content assets, source material, tools, configuration, generated outputs, workspace support, and temporary artifacts; `Project_Config/sources.yaml` schema 18 instantiates selected-pack media facets, work/release/container forms, works and evidence services; `Project_Config/entities.yaml` schema 4 optionally instantiates conceptual entities, incarnations, and persistent-identity phases. Taxonomy, resource, source, and entity loaders expose narrow stable-record and alias provider maps to `Project_Config/reconciliation.yaml` schema 4, whose paired resolver preserves resource-bounded branch-aware redirects, merges, splits, retirements, reclassifications, tombstones, privacy-aware labels, and audit history without mutating repository files. `Project_Config/provenance.yaml` schema 3 then composes typed source/entity/reconciliation targets and owns assertions, semantic field paths, evidence locators, stable claims, authority evaluation, and claim supersession. Framework registry loaders share canonical scalar parsing, closed record shapes, parser budgets, strict six-digit timestamp validation, and a core-owned temporal kernel; page-embedded YAML remains outside that contract pending content-index normalization. Both exporters mirror configured QA page types and delegate visualization-style graph generation to the manifest-configured Visualization implementation; transitional QA-specific graph builders remain until the normalized content-index migration. Content-directory names such as `Glossary_Threads/` are LoTM configuration values, not framework assumptions.

Semantic alias resolution is backed by the manifest-selected `Framework/Data/unicode-lookup-16.0.0.json` registry. `lookup_key_config.py` and `Lookup-Key-Config.ps1` provide identical pinned Unicode normalization for Python, PowerShell 7, and Windows PowerShell 5.1; consumers compare their output ordinally instead of using runtime-default case-insensitive collections.

## Aggregate Conformance

Use the paired aggregate runners as the normal entry point for permanent framework conformance. `Tools/Conformance/suites.json` is the shared suite inventory: it defines stable suite IDs, runtime-specific runner paths, and named profiles. Both aggregate implementations validate the registry and reject discovered conformance runners that are neither registered nor explicitly excluded, preventing new suites from silently falling outside the baseline.

```powershell
python Tools\Conformance\run_conformance.py --profile baseline --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Run-Conformance.ps1 -Profile baseline -Json
```

The `baseline` profile runs every registered permanent suite and is the profile used by CI and framework-version validation. The smaller `fast` profile runs project-root, strict-ingestion, lookup-key, schema-pack, taxonomy, resource, temporal, and chronology checks for quick local feedback; it is not a substitute for the baseline. Schema-pack, taxonomy, and resource composition remain in `fast` because their small synthetic corpora diagnose foundational capability, vocabulary, content-routing, and placement failures before downstream registries obscure them. Source, entity, and provenance conformance remain baseline-only because their comprehensive malformed corpora repeatedly compose larger dependency chains. Use repeatable Python `--suite` arguments or a PowerShell `-Suite` array for focused diagnosis, and use `--list` / `-List` to inspect the registered inventory and profiles.

```powershell
python Tools\Conformance\run_conformance.py --profile fast
python Tools\Conformance\run_conformance.py --suite temporal --suite chronology --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Run-Conformance.ps1 -Suite temporal,chronology -Json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Run-Conformance.ps1 -List -Json
```

The current aggregate layer launches each suite in an isolated child runtime. That preserves existing runner behavior and prevents PowerShell script-scope collisions while the shared loaders are migrated into real modules. Once module extraction is complete, safe in-process execution and a separate fast feature-branch CI tier can be evaluated without changing the registry or suite IDs. Visualization and Obsidian QA remain separate compatibility gates because they validate project consumers rather than framework conformance alone.

## Compatibility Validation

Use the canonical compatibility orchestrator after permanent conformance passes. It launches Python, PowerShell 7, and Windows PowerShell 5.1 implementations and compares project-consumer behavior from one registry-driven command:

```powershell
python Tools\Compatibility\run_compatibility.py --profile local
python Tools\Compatibility\run_compatibility.py --profile pull-request
python Tools\Compatibility\run_compatibility.py --profile full-release
```

`Tools/Compatibility/compatibility.json` owns the executable check inventory, representative bounded requests, render probe, timeouts, and profile membership. `local` compares Visualization and QA outputs; `pull-request` adds root-discovery and artifact-lifecycle safety; `full-release` also renders a representative graph. Use `--list` or `--list --json` to inspect the registry, and repeat `--check` for focused diagnosis.

Every run writes to a unique ignored `.tmp/compatibility/` child, hashes protected canonical outputs before and after execution, and removes its scoped output after success. Failed output is retained automatically. Use `--keep-output` only when a successful comparison needs manual inspection; `--output-root` must remain beneath repository `.tmp/`.

## Strict YAML Conformance

Run the dedicated strict-ingestion corpus after changing shared YAML parsing, scalar rules, mapping keys, schema-version handling, byte decoding, parser budgets, or RFC 3339 validation. Both implementations consume `Framework/Data/Strict-Yaml/`, create only uniquely named operating-system temporary files, and remove those files before exit.

```powershell
python Tools\Conformance\Suites\test_strict_yaml.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Strict-Yaml.ps1
```

Use `--json` / `-Json` for matching stable summaries across Python, PowerShell 7, and Windows PowerShell 5.1.

## Lookup-Key Conformance

Run the lookup corpus after changing pinned Unicode data, normalization, aliases, or semantic identifier comparison. The paired runners validate equivalent, distinct, exact-output, Hangul, malformed-registry, and invalid-input cases from `Framework/Data/lookup-key-regression-vectors.json` and `Framework/Data/Lookup-Key/`; temporary registry mutations are removed automatically.

```powershell
python Tools\Conformance\Suites\test_lookup_key.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Lookup-Key.ps1
```

Use `--json` / `-Json` for parity-comparable corpus counts and the pinned Unicode version.

## Schema-Pack Conformance

Run the dedicated schema-pack suite after changing pack shape, dependency composition, capability lifecycle or activation, controlled-value ownership/hierarchy, or occurrence semantic declarations. Both implementations load the canonical project composition, then consume the independent three-pack fixture and 43 structured malformed mutations in `Framework/Data/Schema-Packs/`. A generated 64-pack composition provides a bounded scale check; all operating-system temporary data is removed automatically.

```powershell
python Tools\Conformance\Suites\test_schema_pack.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Schema-Pack.ps1
```

Use `--json` / `-Json` for matching canonical, fixture, malformed-case, and scale counts across Python, PowerShell 7, and Windows PowerShell 5.1.

## Taxonomy Conformance

Run the dedicated taxonomy suite after changing content-type/category shape, lifecycle, category policy, path or metadata strategy, slug rules, templates, placements, reconciliation targets, or QA-page routing. Both implementations load the canonical project taxonomy, then consume the neutral fixture and 48 structured malformed mutations in `Framework/Data/Taxonomy/`. A generated 128-category composition provides a bounded scale check without making LoTM category names part of the framework oracle; all operating-system temporary data is removed automatically.

```powershell
python Tools\Conformance\Suites\test_taxonomy.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Taxonomy.ps1
```

Use `--json` / `-Json` for matching canonical, fixture, malformed-case, invalid-query, and scale counts across Python, PowerShell 7, and Windows PowerShell 5.1.

## Resource Conformance

Run the dedicated resource suite after changing resource-kind/type shape, lifecycle, authority, editor policy, manifest resource roots, placements, tracking, or resource reconciliation targets. Both implementations load the canonical project registry, then consume the neutral fixture and 30 structured malformed mutations in `Framework/Data/Resources/`. A generated 128-type composition provides a bounded scale check without making LoTM resource names part of the framework oracle; all operating-system temporary data is removed automatically.

```powershell
python Tools\Conformance\Suites\test_resource.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Resource.ps1
```

Use `--json` / `-Json` for matching canonical, fixture, malformed-case, invalid-query, and scale counts across Python, PowerShell 7, and Windows PowerShell 5.1.

## Source Conformance

Run the dedicated source suite after changing work/continuity structure, media or structural positions, authority, applicability, adaptations, manifestations, releases, distribution, evidence sources, observations, coverage, identifiers, resource bindings, or source reconciliation/provenance targets. Both implementations load the canonical project registry, then consume the vocabulary-neutral fixture and 65 structured malformed mutations in `Framework/Data/Sources/`. Fifteen invalid service queries and a generated 128-source composition verify service boundaries and bounded scale; all operating-system temporary data is removed automatically.

```powershell
python Tools\Conformance\Suites\test_source.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Source.ps1
```

Use `--json` / `-Json` for matching canonical, fixture, malformed-case, invalid-query, and scale counts across Python, PowerShell 7, and Windows PowerShell 5.1.

## Entity Conformance

Run the dedicated entity suite after changing conceptual entities, category membership, aliases, relationship types or cycles, lineage basis roles, incarnations, applicability bindings, identity phases, phase ordering, or entity reconciliation/provenance targets. Both implementations compose the canonical project and the independent neutral taxonomy/source fixtures, then consume the schema-4 entity fixture and 86 structured malformed mutations in `Framework/Data/Entities/`. Fifteen invalid service queries and a generated 128-entity composition verify ambiguity, query boundaries, and bounded scale; all operating-system temporary data is removed automatically.

```powershell
python Tools\Conformance\Suites\test_entity.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Entity.ps1
```

## Provenance Conformance

Run the dedicated provenance suite after changing assertions, typed provenance subjects, field paths, evidence links or roles, point/range locators, source scope or coverage, observation/effective timing, claim applicability, supersession, or authority evaluation. Both implementations compose the canonical project dependencies and neutral source/entity fixtures, then consume the schema-3 provenance fixture and 68 structured malformed mutations in `Framework/Data/Provenance/`. Four authority vectors, five invalid service queries, and a generated 128-assertion composition verify decision semantics, service boundaries, and bounded scale; all operating-system temporary data is removed automatically.

```powershell
python Tools\Conformance\Suites\test_provenance.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Provenance.ps1
```

Use `--json` / `-Json` for matching canonical, fixture, malformed-case, invalid-query, and scale counts across Python, PowerShell 7, and Windows PowerShell 5.1.

## Reconciliation Conformance

Run the permanent stable-ID reconciliation vectors after changing strict registry ingestion, reconciliation, provider, schema-pack, or lookup ownership behavior. Both tools validate strict UTF-8/BOM behavior, canonical mapping-key/scalar and byte-budget parity, malformed input, bounded branch-aware resolutions, and a 1,500-hop chain using `Framework/Data/Strict-Yaml/` and `Framework/Data/Reconciliation/`; their temporary byte probes and deep-chain files are removed automatically.

```powershell
python Tools\Conformance\Suites\test_reconciliation.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Reconciliation.ps1
```

Use `--json` / `-Json` for matching structured corpus and stress-test counts:

```powershell
python Tools\Conformance\Suites\test_reconciliation.py --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Reconciliation.ps1 -Json
```

## Temporal Conformance

Run the permanent temporal vectors after changing shared time parsing, temporal pack vocabulary, timestamp resolution, source applicability, release/title windows, or provenance timing. Both implementations load `Framework/Data/Temporal/`, reject malformed windows and timestamps, and verify identical precision-aware query and window-overlap outcomes without leaving output files.

```powershell
python Tools\Conformance\Suites\test_temporal.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Temporal.ps1
```

Use `--json` / `-Json` for the same stable summary fields in automation:

```powershell
python Tools\Conformance\Suites\test_temporal.py --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Temporal.ps1 -Json
```

## Chronology Conformance

Run the chronology vectors after changing coordinate-system vocabulary, era, position, or span shapes, comparison behavior, narrative chronology roles, or manifest composition. Both implementations validate `Project_Config/chronology.yaml`, load `Framework/Data/Chronology/`, compare the same positions, and reject the same malformed registries without writing output files. Chronology coordinates are separate from the RFC 3339 civil-time windows exercised by the temporal conformance tools.

```powershell
python Tools\Conformance\Suites\test_chronology.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Chronology.ps1
```

## Occurrence Conformance

Run the occurrence vectors after changing branches, templates, recurrence patterns or executions, phases, schedules, lifecycle, bindings, tracks, transition profiles, causality, outcomes, scoped rules, deterministic evaluation, state acquisition, carryover, chronology composition, or provenance targets. Both implementations validate the empty LoTM project registry, compose `Framework/Data/Occurrence/` with the chronology fixture, answer the same occurrence, boundary, phase, schedule, outcome, state, selection, suppression, and conflict-trace queries, and reject the same malformed mutations. Causal cycles are intentionally accepted; chronology, transition semantics, containment, monotonic track order, lifecycle, typed rule targets, applicability, outcome compatibility, state-chain continuity, and carryover applicability remain constrained.

```powershell
python Tools\Conformance\Suites\test_occurrence.py
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Suites\Test-Occurrence.ps1
```

The generated structure mirrors active canonical pages by type and adds QA reports. Pages with `Status: Stub` are excluded by default; pass `--include-stubs` / `-IncludeStubs` when stub pages should be mirrored for local inspection. Pending pages are treated as normal QA candidates unless the source page itself is omitted by status.

```text
Obsidian_Export/
  Characters/
  Artifacts/
  Factions/
  Concepts/
  Events/
  Items/
  Knowledge_Sources/
  Locations/
  Pathways/
  Volumes/
  _Generated/
    relationship-index.md
    QA-relationship-graph.mmd
    QA-relationship-node-graph.mmd
    visualization-relationship-graph.mmd
    repo-refresh-check/
      volume-1-knowledge-graph.mmd
      volume-1-knowledge-graph-timing-spoiler-free.mmd
      refresh-check-report.md
      refresh-check-snapshot.json
      refresh-check-settings.json
    bounded-pages/
      Characters/
        Dunn Smith - chapter-30.md
    data-reference-index.md
    orphan-report.md
    suspicious-edges.md
```

Each mirror note includes source metadata, a canonical source link, outgoing Relationship Seed edges, incoming edges, data-block references, incoming data-block references, and seed-file evidence.

`QA-relationship-graph.mmd` is a QA-only Mermaid graph that labels relationship edges directly. It collapses duplicate `source + relationship + target` seeds into one edge with an `xN` suffix so the diagram stays readable. When a seed declares `projection_source`, the label includes the projected availability history from the matching data-block row. The canonical/public visualization workflow remains under `Visualization/`; this labeled graph is only for local Obsidian inspection.

`QA-relationship-node-graph.mmd` is the same QA relationship set projected through intermediary relationship nodes, which can be easier to read in Mermaid viewers when direct edge labels overlap. The relationship nodes preserve seed/data provenance and projected availability summaries for quick maintainer review.

`visualization-relationship-graph.mmd` is a QA-local unbounded graph generated through the repository visualization helper. It uses the same semantic relationship-node projection style as `Visualization/`, but writes only to the ignored Obsidian export folder and does not render images or update canonical visualization artifacts. Relationship Seeds with `projection_source` are resolved against the seed source page first, so repeated local data-block keys on different pages do not collide.

The `_Generated/repo-refresh-check/` folder is a QA-local dry run of every currently configured repository graph view from `Visualization/config/render-settings.json`. It uses the real visualization refresh helper with rendering disabled, writes Mermaid graph sources, a refresh report, a semantic snapshot, and the generated check settings into the Obsidian export, and does not touch canonical `Visualization/graphs/`, rendered images, the real refresh snapshot, or `Visualization/README.md`. Because it derives from the live render settings each run, future configured graph views should automatically appear in this QA dry run.

Optional bounded output folders are owned by the current QA export run. If bounded graph or bounded page specs are provided, the matching `_Generated/bounded-graphs/` or `_Generated/bounded-pages/` folder is rebuilt from scratch so stale files from earlier sampled boundaries do not linger. If no specs are provided for one of those opt-in bundles, any old folder for that bundle is removed.

Use `--bounded-page` / `-BoundedPage` to generate optional local QA page projections for specific reader/viewer boundaries. The folder is created only when requested. Python uses PyYAML from `requirements-python.txt`; the PowerShell fallback uses `powershell-yaml` from `requirements-powershell.txt`. Those YAML dependencies also load the shared project manifest during normal QA runs.

```powershell
python Tools\Commands\QA\obsidian_qa_export.py --clean --bounded-page "slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=30"
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\QA\Obsidian-QA-Export.ps1 -Clean -BoundedPage 'slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=30'
```

Bounded pages read the canonical page's structured data block and render boundary-filtered QA tables plus matching timeline prose sections when `timeline_entries` map to visible `timeline_id` comments. Character bounded pages include the standard character modules such as first appearance, identity, physical profile, status/origin/location, affiliations, pathway and sequence state, abilities, equipment, personality, relationships, major events, and timeline entries. Optional modules such as associated Tarot card, mythical creature form, uniqueness, knowledge sources/documents, messengers/servants/companions, and prayers/ritual access render only when present in the source data block. They are generated inspection artifacts, not canonical rewritten articles. Before the page's `Subject Visible From` boundary, the output must clearly mark the canonical page as hidden; explicitly modeled anonymous first-appearance beats may still appear as QA preview rows. Their timing display may come from either state-row `availability` ladders or positioned reveal fields such as `position`, `source_refs`, and `graph_display`.

The QA export intentionally exposes modeling issues that reader-facing graphs may hide. It should show duplicate/provisional seeds, seed-vs-data provenance, pending endpoint nodes, and projected availability ladders so maintainers can spot taxonomy drift. `projection_source` is expected to point at structured data-block rows, not visible Markdown tables.

Item and equipment rows follow the project taxonomy in `PROJECT_RULES.md`: minor or disposable equipment remains data-only, recurring local-interest objects may appear in maintainer/local views, and full graph-worthy named non-artifact objects should use `item-*` pages with `possesses-item` or `uses-item` seeds. Relationship status labels should preserve semantics; use `broken` only for actual rupture/failure, not ordinary custody loss.

Knowledge Source pages use `source-*` slugs under `Glossary_Threads/Knowledge_Sources/` for recurring reveal carriers such as diary pages, spellbooks, grimoires, notebooks, scriptures, case files, letters, inscriptions, formula records, murals, or records. The QA export treats them as graphable source nodes so maintainers can inspect access, authorship, translation, and claim-reveal relationships without modeling them as ordinary Items.

The `_Generated` reports flag:

- unknown source/target slugs from Relationship Seeds;
- unknown target slugs from YAML data blocks;
- canonical notes with no generated edges or references;
- self loops;
- duplicate edges;
- same-type known edges;
- missing expected reciprocal edges such as `superior` / `subordinate`.

Use `--clean` to delete and regenerate the export directory:

```powershell
python Tools\Commands\QA\obsidian_qa_export.py --clean
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\QA\Obsidian-QA-Export.ps1 -Clean
```

Use `--json` / `-Json` when downstream tooling needs summary counts:

```powershell
python Tools\Commands\QA\obsidian_qa_export.py --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\QA\Obsidian-QA-Export.ps1 -Json
```

## EPUB Image Extraction

Use `edit_image.py --operation extract-epub-images` to list or extract EPUB image assets in actual spine/reading order. Python also accepts `extract`, `extract-images`, `list-images`, and `list-epub-images`; PowerShell accepts the same aliases through `-Operation`. If Python/Pillow is unavailable, use `Edit-Image.ps1 -Operation ExtractEpubImages` with the same filters in PowerShell form. This is separate from text search because image-bearing XHTML entries include covers, front matter, volume covers, end-of-volume art, pathway guides, character galleries, location galleries, maps, and end-matter artwork.

Both implementations assign an `image_number` based on EPUB spine order so "first image" and "next image" stay reproducible.

### List Images

```powershell
python Tools\Commands\Media\edit_image.py --operation extract-epub-images
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Operation ExtractEpubImages
```

Useful filters:

```powershell
python Tools\Commands\Media\edit_image.py --operation extract-epub-images --start-image-number 1 --end-image-number 12
python Tools\Commands\Media\edit_image.py --operation extract-epub-images --volume 1 --image-type Characters
python Tools\Commands\Media\edit_image.py --operation extract-epub-images --image-type Artwork

powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Operation ExtractEpubImages -StartImageNumber 1 -EndImageNumber 12
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Operation ExtractEpubImages -Volume 1 -ImageType Characters
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Operation ExtractEpubImages -ImageType Artwork
```

### Extract Images

Extract selected images into `.tmp/epub-images` by default:

```powershell
python Tools\Commands\Media\edit_image.py --operation extract-epub-images --start-image-number 1 --end-image-number 4 --extract
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Operation ExtractEpubImages -StartImageNumber 1 -EndImageNumber 4 -Extract
```

Use `--output-dir` / `-OutputDir` to choose another destination, and `--json` / `-Json` when downstream tooling needs structured fields such as `image_number`, `spine_index`, `image_type`, `volume`, `xhtml_path`, `image_path`, `alt`, and `output_path`.
