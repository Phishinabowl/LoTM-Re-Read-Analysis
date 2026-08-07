# Tooling Reference

This file is the human-facing map for repository helper scripts. It records what each script is for, how Python-preferred and PowerShell-fallback versions line up when a pair exists, which switches are supported, what files are read or written, and how parity or standalone behavior was last checked.

`Framework/framework_improvement_lifecycle.md` is authoritative for the end-to-end version workflow. `Framework/testing_methodology.md` is authoritative for cumulative test requirements, stable families, retention rules, impact matrix, comparison standards, and result classification. This reference remains authoritative for exact commands, tool-specific output contracts, normalization recipes, and dated parity executions.

Paired validation and conformance commands must expose `--json` / `-Json` whenever they emit a human-readable summary. The 2026-08-01 executable audit confirmed structured output for the environment probes, cleanup, EPUB search, EPUB image operations, Obsidian QA export, chronology, occurrence, temporal, and reconciliation commands. Configuration loaders are libraries rather than summary commands. Visualization remains a file-producing multi-mode command whose structured contracts are its Mermaid graphs, refresh report, and semantic snapshot; a future CLI JSON mode must define mode-specific fields rather than reusing an ambiguous generic summary.

The repository convention is:

- Prefer Python tools when Python is available.
- Keep independent PowerShell implementations for the parity-required runtime and command surfaces listed in the migration inventory; preserve documented runtime-specific exceptions.
- Treat generated outputs as compiled views unless a tool explicitly edits canonical files.
- Update this reference whenever a script gains, loses, or changes a switch, output, or important side effect.

## Tool Architecture Inventory

[ARCHITECTURE.md](../ARCHITECTURE.md#tool-runtime-and-command-architecture) owns the current boundaries, root-discovery order, parity policy, and wrapper rules. This inventory accounts for every maintained runtime, command, conformance, environment, and static-policy surface beneath `Tools/`.

### Reusable Runtime Pairs

All rows in this table require independent Python, PowerShell 7, and Windows PowerShell 5.1 semantic parity. Python modules live beneath `Tools/Runtime/Python/knowledge_framework/`. PowerShell implementations are internal parts of `Tools/Runtime/PowerShell/KnowledgeFramework/`, with supported functions exported through `KnowledgeFramework.psd1` and `KnowledgeFramework.psm1` rather than peer-script dot sourcing.

| Python Source | PowerShell Source | Python Module | PowerShell Ownership | Dependency Role |
| --- | --- | --- | --- | --- |
| `Tools/Runtime/Python/knowledge_framework/strict_yaml.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Strict-Yaml.ps1` | `knowledge_framework.strict_yaml` | `KnowledgeFramework` strict-ingestion implementation | Lowest-level strict byte, syntax, scalar, key, timestamp, and parser-budget service. |
| `Tools/Runtime/Python/knowledge_framework/project_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Project-Config.ps1` | `knowledge_framework.project_paths` plus `knowledge_framework.project_config` | `KnowledgeFramework` project-path and manifest implementation | Dependency-light root/path discovery followed by strict manifest loading. |
| `Tools/Runtime/Python/knowledge_framework/lookup_key_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Lookup-Key-Config.ps1` | `knowledge_framework.lookup_key_config` | `KnowledgeFramework` lookup-key implementation | Pinned Unicode lookup normalization and ordinal comparison. |
| `Tools/Runtime/Python/knowledge_framework/schema_pack_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Schema-Pack-Config.ps1` | `knowledge_framework.schema_pack_config` | `KnowledgeFramework` schema-pack implementation | Pack composition, capability state, and controlled-value ownership. |
| `Tools/Runtime/Python/knowledge_framework/effective_schema.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Effective-Project-Schema.ps1` | `knowledge_framework.effective_schema` | `KnowledgeFramework` effective-schema implementation | Deterministic project, pack, capability, controlled-value, taxonomy, resource, and diagnostic composition plus direct consumer projections. |
| `Tools/Runtime/Python/knowledge_framework/taxonomy_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Taxonomy-Config.ps1` | `knowledge_framework.taxonomy_config` | `KnowledgeFramework` taxonomy implementation | Content-type/category routing and validation. |
| `Tools/Runtime/Python/knowledge_framework/resource_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Resource-Config.ps1` | `knowledge_framework.resource_config` | `KnowledgeFramework` resource implementation | Resource-kind/type and placement validation. |
| `Tools/Runtime/Python/knowledge_framework/temporal_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Temporal-Config.ps1` | `knowledge_framework.temporal_config` | `KnowledgeFramework` temporal implementation | Domain-neutral civil-time parsing and comparison. |
| `Tools/Runtime/Python/knowledge_framework/source_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Source-Config.ps1` | `knowledge_framework.source_config` | `KnowledgeFramework` source implementation | Works, media, releases, evidence, applicability, and authority services. |
| `Tools/Runtime/Python/knowledge_framework/chronology_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Chronology-Config.ps1` | `knowledge_framework.chronology_config` | `KnowledgeFramework` chronology implementation | Non-civil coordinate systems, positions, spans, mappings, and ordering. |
| `Tools/Runtime/Python/knowledge_framework/entity_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Entity-Config.ps1` | `knowledge_framework.entity_config` | `KnowledgeFramework` entity implementation | Entities, incarnations, phases, aliases, relationships, and providers. |
| `Tools/Runtime/Python/knowledge_framework/reconciliation_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Reconciliation-Config.ps1` | `knowledge_framework.reconciliation_config` | `KnowledgeFramework` reconciliation implementation | Stable-ID redirects, merges, splits, retirement, and resolution. |
| `Tools/Runtime/Python/knowledge_framework/occurrence_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Occurrence-Config.ps1` | `knowledge_framework.occurrence_config` | `KnowledgeFramework` occurrence implementation | Occurrence, recurrence, aggregate cardinality, state, schedule, rule, and outcome semantics. |
| `Tools/Runtime/Python/knowledge_framework/provenance_config.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Provenance-Config.ps1` | `knowledge_framework.provenance_config` | `KnowledgeFramework` provenance implementation | Assertions, evidence locators, claim evaluation, and cross-registry targets. |

The Python package exports only deliberately supported entry points through `__init__.py`; package consumers use `knowledge_framework.<module>` imports. The PowerShell manifest uses an explicit `FunctionsToExport` list; wildcard exports and command-to-command dot sourcing are prohibited.

### User Command Pairs

These are Python-preferred commands with independent PowerShell fallbacks. Their paths and existing CLI behavior are stable public surfaces.

| Command Pair | Ownership |
| --- | --- |
| `Tools/Commands/QA/obsidian_qa_export.py`, `Tools/Commands/QA/Obsidian-QA-Export.ps1` | Obsidian mirror, bounded-page, and QA orchestration command. |
| `Tools/Commands/Maintenance/clean_temp_files.py`, `Tools/Commands/Maintenance/Clean-TempFiles.ps1` | Scoped cache and temporary-artifact cleanup command. |
| `Tools/Commands/Media/search_epub.py`, `Tools/Commands/Media/Search-Epub.ps1` | EPUB text/search command. |
| `Tools/Commands/Media/edit_image.py`, `Tools/Commands/Media/Edit-Image.ps1` | Image manipulation and EPUB artwork extraction command. |
| `Tools/Commands/Framework/inspect_effective_schema.py`, `Tools/Commands/Framework/Get-EffectiveProjectSchema.ps1` | Generated effective-schema inspection and JSON export command. |

### Conformance Inventory

The aggregate entry points and registry live directly under `Tools/Conformance/`. Individual runners live beneath `Tools/Conformance/Suites/`; fixture data remains under `Framework/Data/`.

| Files | Location | Parity |
| --- | --- | --- |
| `Tools/Conformance/run_conformance.py`, `Tools/Conformance/Run-Conformance.ps1`, `Tools/Conformance/suites.json` | unchanged parent paths | Paired aggregate semantics; each runtime launches its own suite implementations. |
| `Tools/Conformance/Suites/test_project_paths.py`, `Tools/Conformance/Suites/Test-Project-Paths.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_strict_yaml.py`, `Tools/Conformance/Suites/Test-Strict-Yaml.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_lookup_key.py`, `Tools/Conformance/Suites/Test-Lookup-Key.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_schema_pack.py`, `Tools/Conformance/Suites/Test-Schema-Pack.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_taxonomy.py`, `Tools/Conformance/Suites/Test-Taxonomy.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_resource.py`, `Tools/Conformance/Suites/Test-Resource.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_effective_schema.py`, `Tools/Conformance/Suites/Test-Effective-Schema.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_source.py`, `Tools/Conformance/Suites/Test-Source.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_entity.py`, `Tools/Conformance/Suites/Test-Entity.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_provenance.py`, `Tools/Conformance/Suites/Test-Provenance.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_temporal.py`, `Tools/Conformance/Suites/Test-Temporal.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_chronology.py`, `Tools/Conformance/Suites/Test-Chronology.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_reconciliation.py`, `Tools/Conformance/Suites/Test-Reconciliation.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_occurrence.py`, `Tools/Conformance/Suites/Test-Occurrence.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |
| `Tools/Conformance/Suites/test_project_composition.py`, `Tools/Conformance/Suites/Test-Project-Composition.ps1` | `Tools/Conformance/Suites/` with basenames retained | Required. |

Moving an individual suite changes its Python and PowerShell runner paths only in `Tools/Conformance/suites.json`; CI continues to invoke the unchanged aggregate entry points. Discovery rules move with the suite directory and continue rejecting unregistered runners and stale exclusions.

### Environment, Static, And Documentation Files

| Files | Location | Pairing Decision |
| --- | --- | --- |
| `Tools/Commands/Environment/Test-Python.ps1`, `Tools/Commands/Environment/Test-PowerShell.ps1` | `Tools/Commands/Environment/` | Intentional PowerShell-only environment probes; each inspects a different runtime and is not a domain fallback. |
| `Tools/Static/Format-PowerShell.ps1`, `Tools/Static/powershell-format-settings.psd1` | `Tools/Static/` | Intentional PowerShell-only parser-native formatter. Ruff remains configured by root `pyproject.toml`. |
| `Tools/Static/lint_work_annotations.py`, `Tools/Static/work-annotations.json`, annotation fixtures | `Tools/Static/` | Canonical Python repository-policy linter; it does not implement a project-domain feature requiring a PowerShell fallback. |
| `Tools/Compatibility/run_compatibility.py`, `Tools/Compatibility/compatibility.json`, `Tools/Compatibility/verify_framework_extraction.py` | `Tools/Compatibility/` | Canonical Python cross-runtime orchestration and isolated extraction rehearsal; these invoke and compare the paired runtimes rather than replacing a domain implementation. |
| `Tools/README.md`, `Tools/TOOLING_REFERENCE.md` | unchanged | Human command guide and detailed tooling contract. |

The work-annotation linter and cross-runtime compatibility orchestrator belong under `Tools/Static/` and `Tools/Compatibility/` respectively. Each has one canonical Python implementation because one enforces repository text policy and the other explicitly orchestrates and compares all runtimes; neither is a user-facing project-domain fallback.

### Public Entry Rules

- Command paths beneath `Tools/Commands/` are the stable public CLI entry points and preserve documented switch meaning, defaults, help, structured output, exit behavior, and side-effect boundaries.
- Runtime implementations beneath `Tools/Runtime/` are library surfaces, not alternate command entry points.
- Any future path migration must update tracked callers, CI, documentation, imports, module loading, and suite-registry paths in the same migration wave.
- Root-level compatibility wrappers are not retained by default. Any exception must name an external dependency, emit a deprecation warning, and record a removal checkpoint.
- Python commands import package-qualified runtime modules. PowerShell commands import the module manifest. Commands do not import or dot-source peer commands.
- Python implementations do not call PowerShell implementations, and PowerShell implementations do not call Python implementations, except for the compatibility orchestrator whose explicit purpose is cross-runtime comparison.
- Static tools and environment probes are excluded from domain parity only where the inventory explicitly says so.

### Layout Boundary Checks

Phase 2 removed fixed-depth project-root discovery, and Phase 3 established the final runtime and command boundaries. Preserve those results:

- `Format-PowerShell.ps1` uses shared project discovery and Git only for tracked/nonignored source inventory, and resolves its settings beside itself in `Tools/Static/`.
- Python runtime modules use package-relative imports; commands and suites bootstrap `Tools/Runtime/Python` and import package-qualified modules.
- PowerShell commands and suites import `KnowledgeFramework.psd1`; internal loader ordering belongs only to `KnowledgeFramework.psm1`.
- Root-level `Tools/*.py` and `Tools/*.ps1` loader or command implementations are prohibited.

Repository searches and aggregate validation must continue to reject flat loader imports, command-to-command imports, and command/conformance dot-sourcing of loader scripts.

## Project Root Discovery

The paired dependency-light runtime services are `Tools/Runtime/Python/knowledge_framework/project_paths.py` and `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`. Project identity is the presence of `Project_Config/project.yaml`, not `.git` or a domain content folder.

Resolution order is explicit `--root` / `-Root`, absolute `KNOWLEDGE_PROJECT_ROOT`, current-directory ancestors, executable-location ancestors, then a precise failure. An authoritative explicit or environment root with a missing manifest fails instead of falling through. Discovery never changes the caller's working directory. `project-root` is a permanent aggregate conformance suite in both `fast` and `baseline` profiles.

## Python Environment Check

### Script

| Role | Script | Command |
| --- | --- | --- |
| Environment probe | `Tools/Commands/Environment/Test-Python.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-Python.ps1` |

Purpose: check whether the local machine has a usable Python command and the repository's required Python modules before choosing Python-preferred tools or documented PowerShell fallbacks. This is a read-only probe and has no Python pair.

### Switch Map

| Purpose | Switch | Default | Notes |
| --- | --- | --- | --- |
| Print JSON summary | `-Json` | off | Emits structured `available`, `ready`, `command`, `version`, `executable`, `requirements_*`, `checked`, and `message` fields for agent workflows. |
| Select repository root | `-Root <path>` | Auto-detected | Uses the shared project-root contract. Relative requirements paths resolve beneath this root. |
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
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-Python.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-Python.ps1 -Json
python -m pip install -r requirements-python.txt
```

Last mapped: 2026-08-02.

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
| Environment probe | `Tools/Commands/Environment/Test-PowerShell.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-PowerShell.ps1` |

Purpose: check whether the local PowerShell environment has repository-required modules from `requirements-powershell.txt`. This is a read-only probe and has no Python pair.

### Switch Map

| Purpose | Switch | Default | Notes |
| --- | --- | --- | --- |
| Print JSON summary | `-Json` | off | Emits structured `ready`, `powershell_version`, `edition`, `executable`, `requirements_path`, `modules`, and `message` fields. |
| Select repository root | `-Root <path>` | Auto-detected | Uses the shared project-root contract. Relative requirements paths resolve beneath this root. |
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
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-PowerShell.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Environment\Test-PowerShell.ps1 -Json
Install-Module powershell-yaml -Scope CurrentUser -Force -AllowClobber
Install-Module PSScriptAnalyzer -Scope CurrentUser -Force
```

Last mapped: 2026-08-02.

Last check: 2026-08-01. JSON mode ran successfully in PowerShell 7.6.3 and Windows PowerShell 5.1.19041.7548. Both runtimes detected the machine-wide `powershell-yaml` and `PSScriptAnalyzer` requirements.

## PowerShell Source Formatting

### Script

| Role | Script | Command |
| --- | --- | --- |
| PowerShell static formatter and check | `Tools/Static/Format-PowerShell.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Static\Format-PowerShell.ps1` |

Purpose: deterministically format and statically check maintained PowerShell sources. This tool has no Python pair because its behavior depends on the PowerShell parser and `PSScriptAnalyzer`; it does not implement a project-domain feature that requires a fallback runtime.

### Parameter Map

| Purpose | Parameter | Default | Notes |
| --- | --- | --- | --- |
| Select files or directories | `-Path <string[]>` | all tracked and nonignored untracked repository PowerShell sources | Explicit directories recursively include `.ps1`, `.psm1`, and `.psd1` sources. Relative paths resolve from the repository root. |
| Maximum physical line length | `-MaximumLineLength <int>` | `200` | Values from 80 through 1000 are accepted. Any longer line fails the check even after formatting. |
| Apply changes | `-Fix` | off | Without this switch the command is read-only and exits nonzero when a file differs from canonical formatting. |
| Print JSON summary | `-Json` | off | Emits readiness, mode, file/change counts, line-length results, and per-file details. |

### Formatting Contract

- `Tools/Static/powershell-format-settings.psd1` owns PSScriptAnalyzer layout settings.
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
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Static\Format-PowerShell.ps1

# Apply canonical formatting
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Static\Format-PowerShell.ps1 -Fix

# PowerShell 7 structured check
pwsh -NoProfile -File Tools\Static\Format-PowerShell.ps1 -Json
```

Last mapped: 2026-08-01.

Last check: 2026-08-01. PowerShell 7.6.3 and Windows PowerShell 5.1.19041.7548 each discovered all 26 tracked or nonignored untracked repository PowerShell sources and checked them with zero pending changes, zero lines above 200 characters, successful parsing, and identical source acceptance. A temporary nonignored root-level script was discovered automatically by both runtimes during the discovery regression.

## Work-Annotation Validation

### Script

| Role | Script | Command |
| --- | --- | --- |
| Canonical repository-policy linter | `Tools/Static/lint_work_annotations.py` | `python Tools\Static\lint_work_annotations.py` |

Purpose: enforce `WORK_ANNOTATION_STANDARDS.md` without creating a second project-domain implementation. A normal invocation validates the permanent fixture corpus and then scans Git's tracked-plus-nonignored-untracked inventory.

### Parameter Map

| Purpose | Parameter | Default | Notes |
| --- | --- | --- | --- |
| Select project root | `--root PATH` | auto-detected | Uses the shared manifest-based resolver and never changes caller location. |
| Select policy registry | `--policy PATH` | `Tools/Static/work-annotations.json` | Relative paths resolve from the project root; the registry uses a closed schema. |
| Select fixture registry | `--fixtures PATH` | `Tools/Static/Fixtures/Work-Annotations/cases.json` | Relative paths resolve from the project root; fixture cases use a closed schema. |
| Run fixture conformance only | `--fixtures-only` | off | Useful while changing annotation syntax or fixture expectations. |
| Select files or directories | repeat `--path PATH` | full Git inventory | Explicit paths must remain inside the project root. Fixtures still run first. |
| Print JSON summary | `--json` | off | Emits fixture counts, repository counts, stable finding codes, locations, and messages. |

### Policy Contract

- `Tools/Static/work-annotations.json` owns supported tags, the exact `OWNER`/`UNASSIGNED` local-owner list, scannable extensions, self-excluded reference/fixture paths, prohibited locations, and the maximum file size.
- `Tools/Static/Fixtures/Work-Annotations/cases.json` permanently covers valid local, pending, assigned, and unassigned forms plus malformed tags, owners, handles, issue/assignee links, punctuation, ASCII, and prohibited locations.
- Markdown fenced examples are not live annotations. `WORK_ANNOTATION_STANDARDS.md` and the deliberate fixture tree are self-excluded; reader-facing/generated locations are still scanned and rejected when they contain annotations.
- GitHub-linked annotations require matching `GH #number`, full issue URL, and assignment state. The linter validates mirrored syntax and consistency but does not query live GitHub state.
- The command is read-only. It creates no temporary artifacts and supports repository-root, descendant, unrelated-directory, and explicit-root launches.

### Check Recipe

```powershell
python Tools\Static\lint_work_annotations.py
python Tools\Static\lint_work_annotations.py --fixtures-only --json
python Tools\Static\lint_work_annotations.py --path Tools\Runtime --json
```

Last mapped: 2026-08-02.

Last check: 2026-08-02. All 22 valid and invalid fixture cases passed. The default scan checked 276 tracked or nonignored untracked eligible files with zero live annotations and zero findings. Temporary nonignored probes proved that a new implementation annotation is discovered and accepted while the same valid syntax in `Glossary_Threads/` is discovered and rejected as `prohibited-location`; targeted scans of the standards document and fixture tree checked zero files. Automatic executable-based and explicit-root launches from an unrelated directory also passed. Ruff, both PowerShell formatter runtimes, actionlint, and all seven aggregate conformance suites in Python, PowerShell 7, and Windows PowerShell 5.1 remained green. GitHub Actions workflow-dispatch run `30757488670` then passed all four hosted jobs: Workflow Policy in 7 seconds, Python Validation with the new annotation gate in 18 seconds, PowerShell 7 Validation in 2 minutes 21 seconds, and Windows PowerShell 5.1 Validation in 3 minutes 30 seconds.

## Temporary File Cleanup

### Script Pair

| Role | Script | Command |
| --- | --- | --- |
| Preferred implementation | `Tools/Commands/Maintenance/clean_temp_files.py` | `python Tools\Commands\Maintenance\clean_temp_files.py` |
| Windows fallback | `Tools/Commands/Maintenance/Clean-TempFiles.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1` |

Purpose: find and optionally remove allowlisted local cache directories under the repository root. This tool is for disposable tool/runtime artifacts only, not project source files.

### Switch Map

| Purpose | Python switch | PowerShell switch | Default | Notes |
| --- | --- | --- | --- | --- |
| Actually delete cache folders/artifacts | `--delete` | `-Delete` | off | Without this switch, both scripts run in dry-run mode and only report matching paths. |
| Select repository root | `--root <path>` | `-Root <path>` | Auto-detected | Uses the shared project-root contract. |
| Include ignored `.tmp` artifacts | `--include-tmp` | `-IncludeTmp` | off | Adds direct children of repository `.tmp/` to the cleanup target list. The `.tmp` root itself is left in place. |
| Include exact scoped `.tmp` path | `--tmp-path <path>` | `-TmpPath <path>[,<path>]` | none | Adds only the specified existing path(s), and only when they resolve under repository `.tmp/`. Intended for automatic cleanup of artifacts created by the current tool run. |
| Print JSON summary | `--json` | `-Json` | off | Emits structured fields for `repo_root`, `delete`, `allowed_directory_names`, `count`, and `results`. |
| Show CLI help | `--help` | n/a | n/a | Python exposes argparse help. The PowerShell fallback exposes switches through the script `param(...)` block. |

### Inputs

| Input | Used For |
| --- | --- |
| Shared project-root resolver | Search boundary selected by explicit root, environment override, current-directory ancestry, or executable ancestry. |
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

python Tools\Commands\Maintenance\clean_temp_files.py --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1 -Json

python Tools\Commands\Maintenance\clean_temp_files.py --include-tmp --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1 -IncludeTmp -Json

python Tools\Commands\Maintenance\clean_temp_files.py --tmp-path .tmp\cleanup-parity --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1 -TmpPath .tmp\cleanup-parity -Json

python Tools\Commands\Maintenance\clean_temp_files.py --delete --json

New-Item -ItemType Directory -Force -Path .tmp\cleanup-parity\Tools\__pycache__
New-Item -ItemType Directory -Force -Path .tmp\cleanup-parity\Nested\.pytest_cache
New-Item -ItemType Directory -Force -Path .tmp\cleanup-parity\Nested\.ruff_cache

powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Maintenance\Clean-TempFiles.ps1 -Delete -Json
```

Automatic tool cleanup should prefer `--tmp-path ... --delete` / `-TmpPath ... -Delete` for exact paths created by the current run. Use `--include-tmp --delete` / `-IncludeTmp -Delete` only when ignored local test outputs under `.tmp/` are no longer needed. This is intentionally opt-in so parity runs that write inspectable outputs under `.tmp/` are not deleted immediately by the tools that created them.

Expected non-semantic differences:

- JSON whitespace from Python `json.dumps` versus PowerShell `ConvertTo-Json`.

Last mapped: 2026-08-02.

Last parity check: 2026-07-07. Dry-run JSON matched semantically for three test cache directories under `.tmp/cleanup-parity/`. Delete-mode JSON matched semantically after recreating the same three test directories between Python and PowerShell runs. Both scripts reported the same allowlist, target paths, counts, and statuses.

## Image Manipulation

### Script Pair

| Role | Script | Command |
| --- | --- | --- |
| Preferred implementation | `Tools/Commands/Media/edit_image.py` | `python Tools\Commands\Media\edit_image.py` |
| Windows fallback | `Tools/Commands/Media/Edit-Image.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1` |

Purpose: run repeatable local image operations. Current operations are fixed-geometry image cropping, named crop presets for official pathway guide assets, and EPUB image listing/extraction in spine order.

### Switch Map

| Purpose | Python switch | PowerShell switch | Default | Notes |
| --- | --- | --- | --- | --- |
| Select operation | `--operation <name>` | `-Operation <name>` | `crop` / `Crop` | Supported operation family: crop or EPUB image listing/extraction. |
| Select repository root | `--root <path>` | `-Root <path>` | Auto-detected | Relative source, EPUB, and output paths resolve beneath this root. |
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
python Tools\Commands\Media\edit_image.py --list-presets
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -ListPresets
```

List EPUB images:

```powershell
python Tools\Commands\Media\edit_image.py --operation list-images --start-image-number 1 --end-image-number 5 --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Operation List-Images -StartImageNumber 1 -EndImageNumber 5 -Json
```

Extract one EPUB image:

```powershell
python Tools\Commands\Media\edit_image.py --operation ExtractEpubImages --start-image-number 1 --end-image-number 1 --output-dir .tmp\image-parity\python-extract --extract --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Operation ExtractEpubImages -StartImageNumber 1 -EndImageNumber 1 -OutputDir .tmp\image-parity\powershell-extract -Extract -Json
```

Crop a synthetic source image and compare dimensions/pixels:

```powershell
python Tools\Commands\Media\edit_image.py --operation crop --source-image .tmp\image-parity\source.png --output-image .tmp\image-parity\python-crop.png --x 3 --y 4 --width 7 --height 6 --force
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Edit-Image.ps1 -Operation Crop -SourceImage .tmp\image-parity\source.png -OutputImage .tmp\image-parity\powershell-crop.png -X 3 -Y 4 -Width 7 -Height 6 -Force
```

Expected non-semantic differences:

- JSON whitespace from Python `json.dumps` versus PowerShell `ConvertTo-Json`.
- Extracted `output_path` values differ when different output directories are used.
- Crop command wording uses `crop` in Python output and `Crop` in PowerShell output.

Last mapped: 2026-08-02.

Last parity check: 2026-07-07. Preset listing matched exactly. EPUB JSON listing for images 1-5 matched semantically. Single-image EPUB extraction matched semantically after normalizing `output_path`, and the extracted image hashes matched byte-for-byte. Synthetic crop outputs both produced `7x6` images with matching pixel data.

## EPUB Search

### Script Pair

| Role | Script | Command |
| --- | --- | --- |
| Preferred implementation | `Tools/Commands/Media/search_epub.py` | `python Tools\Commands\Media\search_epub.py` |
| Windows fallback | `Tools/Commands/Media/Search-Epub.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1` |

Both current implementations discover the Book 1 EPUB layout. They do not yet consume `Project_Config/sources.yaml`, accept a registered work ID, or discover entries in the current COI EPUB package. Passing the COI path returns an empty entry list and must not be interpreted as an empty book. Multi-book search support requires registry-backed work/source selection plus package-specific discovery adapters.

Purpose: search the local ignored Lord of Mysteries EPUB for source verification. The tool reads EPUB XHTML entries, strips markup, classifies searchable sections, and returns chapter-ordered counts, snippets, context, summaries, or entry listings. It is read-only.

### Switch Map

| Purpose | Python switch | PowerShell switch | Default | Notes |
| --- | --- | --- | --- | --- |
| EPUB path | `--epub-path <path>` | `-EpubPath <path>` | `Source/Lord of Mysteries - Book 1.epub` | Local ignored EPUB source. |
| Select repository root | `--root <path>` | `-Root <path>` | Auto-detected | Relative EPUB paths resolve beneath this root. |
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
python Tools\Commands\Media\search_epub.py --entry-type All --list-entries --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -EntryType All -ListEntries -Json
```

Counts-only chapter search:

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 1 --end-chapter 5 --pattern "Klein|Zhou" --counts-only --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 1 -EndChapter 5 -Pattern "Klein|Zhou" -CountsOnly -Json
```

Term summary:

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 1 --end-chapter 10 --pattern "Klein|Zhou" --term-summary --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 1 -EndChapter 10 -Pattern "Klein|Zhou" -TermSummary -Json
```

Context hits with line counts:

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 1 --end-chapter 1 --pattern "Klein|Zhou" --context-lines 1 --max-hits-per-chapter 3 --include-line-match-counts --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 1 -EndChapter 1 -Pattern "Klein|Zhou" -ContextLines 1 -MaxHitsPerChapter 3 -IncludeLineMatchCounts -Json
```

Regex and case-sensitive search:

```powershell
python Tools\Commands\Media\search_epub.py --start-chapter 1 --end-chapter 3 --pattern "Klein\b" --regex-pattern --case-sensitive --counts-only --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -StartChapter 1 -EndChapter 3 -Pattern "Klein\b" -RegexPattern -CaseSensitive -CountsOnly -Json
```

Non-chapter appendix search:

```powershell
python Tools\Commands\Media\search_epub.py --entry-type Appendices --entry-name-pattern "*pathways*" --pattern "Pathway|Sequence|Seer" --counts-only --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Media\Search-Epub.ps1 -EntryType Appendices -EntryNamePattern "*pathways*" -Pattern "Pathway|Sequence|Seer" -CountsOnly -Json
```

Expected non-semantic differences:

- JSON whitespace from Python `json.dumps` versus PowerShell `ConvertTo-Json`.
- Error wording/format differs because Python errors come from argparse and PowerShell errors come from parameter validation or thrown exceptions.

Last mapped: 2026-08-02.

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
| Select repository root | `--root <path>` | `-Root <path>` | Auto-detected | All relative settings, graph, report, snapshot, and output paths resolve beneath this root without changing caller location. |
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

- Python invokes `Tools/Commands/Maintenance/clean_temp_files.py` at the end of normal runs to remove transient Python cache folders. The PowerShell fallback does not call cleanup because it does not create Python cache folders.
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

Last mapped: 2026-08-02.

Last parity check: 2026-08-01. Python, PowerShell 7, and Windows PowerShell 5.1 Validate runs matched exactly (`nodes=15`, `relationships=121`, zero class/layout issues for both existing and freshly generated configured views). Redirected Obsidian QA runs exercised each runtime's Visualization helper for the unbounded relationship graph, configured no-render refresh, and a Novel V1 Ch32 bounded graph. Generated Mermaid files matched after newline normalization, and refresh/bounded snapshot node, relationship, view, orphan, pending, and broken-link semantics matched after runtime path and timestamp normalization. Redirected Render runs over the tracked full Volume 1 graph each produced the same nonempty `298269`-byte SVG with an identical SHA-256 hash.

## Obsidian QA Export

### Script Pair

| Role | Script | Command |
| --- | --- | --- |
| Preferred implementation | `Tools/Commands/QA/obsidian_qa_export.py` | `python Tools\Commands\QA\obsidian_qa_export.py` |
| Windows fallback | `Tools/Commands/QA/Obsidian-QA-Export.ps1` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\QA\Obsidian-QA-Export.ps1` |

Purpose: compile repository metadata, type-specific YAML data blocks, Relationship Seeds, and graph projections into an ignored Obsidian-friendly QA mirror. The export is for maintainer inspection and visual QA; it is not a source of truth.

### Switch Map

| Purpose | Python switch | PowerShell switch | Default | Notes |
| --- | --- | --- | --- | --- |
| Select repository root | `--root <path>` | `-Root <path>` | Auto-detected | Uses explicit root, `KNOWLEDGE_PROJECT_ROOT`, current-directory ancestors, then executable-location ancestors. Project identity comes from `Project_Config/project.yaml`; content-directory names and `.git` do not participate in root detection. |
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
| Resolve project root | `knowledge_framework.project_paths.resolve_project_root`, `is_project_root` | `Resolve-KnowledgeProjectRoot`, `Test-KnowledgeProjectRoot` from the `KnowledgeFramework` module |
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
python Tools\Commands\QA\obsidian_qa_export.py --clean --output-dir .tmp\obsidian-python-check --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\QA\Obsidian-QA-Export.ps1 -Clean -OutputDir .tmp\obsidian-powershell-check -Json

python Tools\Commands\QA\obsidian_qa_export.py --clean --output-dir .tmp\obsidian-python-bounded --bounded-graph "name=ch10,medium=novel,maxVolume=1,maxChapter=10" --bounded-graph "name=vol1,medium=novel,maxVolume=1" --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\QA\Obsidian-QA-Export.ps1 -Clean -OutputDir .tmp\obsidian-powershell-bounded -BoundedGraph 'name=ch10,medium=novel,maxVolume=1,maxChapter=10;name=vol1,medium=novel,maxVolume=1' -Json

python Tools\Commands\QA\obsidian_qa_export.py --clean --output-dir .tmp\obsidian-python-pages --bounded-page "slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=10" --bounded-page "slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=30" --bounded-page "slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=50" --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\QA\Obsidian-QA-Export.ps1 -Clean -OutputDir .tmp\obsidian-powershell-pages -BoundedPage 'slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=10;slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=30;slug=character-dunn-smith,medium=novel,maxVolume=1,maxChapter=50' -Json
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

Last mapped: 2026-08-02.

Last parity check: 2026-08-01. Python, PowerShell 7, and Windows PowerShell 5.1 each generated the same 35-file inventory and summary counts for a redirected export containing one Novel V1 Ch32 bounded graph plus Dunn Smith Ch10/Ch32 and Leonard Mitchell Ch32 bounded pages. All 29 stable Markdown and Mermaid outputs matched after generated timestamp and newline normalization; the six refresh/bounded report, settings, and snapshot artifacts matched semantically after expected runtime path, timestamp, encoding, and JSON-format differences were normalized. Normal exports launched from `Tools/` also auto-detected the repository root and produced identical summaries (`notes=16`, `relationships=121`, `data_references=71`, no bounded outputs). Prior boundary checks covered Dunn Smith at Novel V1 Ch10, Ch20, Ch30, and Ch50, including anonymous-preview and Sleepless-pathway progression behavior.

Current content-type and ownership regression: both implementations selected taxonomy-enabled `glossary` and `volumes` roots, excluded `investigations`, and produced matching 28-file lists and summary counts (`notes=16`, `relationships=121`, `data_references=71`). After generated timestamps were normalized, all 25 stable Markdown and Mermaid outputs matched exactly. The check moved PowerShell's unbounded visualization-style graph generation into the configured Visualization helper and added a deterministic YAML-block/file tie-breaker to both data-reference index sort orders.

## Effective Project Schema

### Runtime And Command Pair

| Surface | Python | PowerShell |
| --- | --- | --- |
| Reusable service | `Tools/Runtime/Python/knowledge_framework/effective_schema.py` | `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Effective-Project-Schema.ps1`, exported by `KnowledgeFramework.psd1` |
| Public command | `Tools/Commands/Framework/inspect_effective_schema.py` | `Tools/Commands/Framework/Get-EffectiveProjectSchema.ps1` |
| Conformance | `Tools/Conformance/Suites/test_effective_schema.py` | `Tools/Conformance/Suites/Test-Effective-Schema.ps1` |

Library consumers import the service. They must not launch the command to recover the same object.
Python exposes `EffectiveProjectSchema`, `compose_effective_project_schema`,
`load_effective_project_schema`, `compose_effective_consumer_schema_projection`,
`compose_effective_schema_selection`, `effective_schema_json`, and `effective_schema_failure`.
PowerShell exposes `New-KnowledgeEffectiveProjectSchema`, `Get-KnowledgeEffectiveProjectSchema`,
`New-KnowledgeEffectiveConsumerSchemaProjection`, `New-KnowledgeEffectiveSchemaSelection`, and
`New-KnowledgeEffectiveSchemaFailure` from module version 0.6.0.

QA and Visualization compose one effective schema in-process from the project, pack, taxonomy, and
resource objects already loaded by their supported runtime. QA and Visualization use direct
effective projections for discovery and record eligibility. Python QA passes that same composed
object into Visualization's explicit library initializer when requesting graphs. Direct
Markdown/YAML interpretation and generated semantics remain compatibility adapters until later
normalized-content phases replace them. The temporary legacy projection, comparison, and shadow
assertion APIs were retired after Phase 2.3.5 closure.

### Switch Map

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Auto-detect and summarize | `python Tools\Commands\Framework\inspect_effective_schema.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1` |
| Explicit project root | `--root PATH` | `-Root PATH` |
| Canonical JSON on standard output | `--json` | `-Json` |
| Also export canonical JSON | `--output PATH` | `-Output PATH` |
| Export the selected human report | `--report-output PATH` | `-ReportOutput PATH` |
| Append detailed human sections | repeat `--show SECTION` | `-Show SECTION[,SECTION]` |
| Inspect one selected pack | `--pack PACK_ID` | `-Pack PACK_ID` |
| Inspect one selected capability | `--capability CAPABILITY_ID` | `-Capability CAPABILITY_ID` |
| Help | `--help` | `-Help`, `-?`, or `-h` |

The output destination may be absolute or relative but must resolve beneath the detected project
root. Parent directories are created as needed. Human mode prints project identity, contract,
framework/domain, pack and capability counts, controlled-value namespaces, content/resource counts,
and diagnostics. JSON mode emits the contract-defined document. Failed structured composition emits
an `effective-project-schema-result` envelope with `schema: null`, one stable error diagnostic, and a
nonzero exit code; human mode writes the loader error to standard error.

`SECTION` is `overview`, `packs`, `capabilities`, `namespaces`, `content`, `resources`, `diagnostics`,
or `all`. `overview` lists friendly pack/capability labels, stable IDs, and descriptions for the
selected project composition without detailed lifecycle, provider, classification, or dependency
rows.
Python repeats `--show`; PowerShell uses one comma-separated `-Show` value because external `-File`
invocation does not portably bind native arrays. Selections are deduplicated in request order. `all`
expands to the six detailed sections and excludes the redundant overview. With no selection, output
remains the compact summary. Without singular selectors, `--json` / `-Json` always emits the complete canonical
document and ignores presentation selection.

Pack and capability selectors resolve an exact stable ID first, then use the project's pinned
lookup-key normalization. Unknown and ambiguous values fail rather than guessing. The selectors
may be combined with each other and with any human `show` selection. Human mode appends complete
inspection blocks, including authored presentation and pack classification. Structured mode emits
an `effective-project-schema-selection` envelope containing zero or one complete row for each
requested kind and identifying effective-schema contract version 2 as its source. With no selector,
the canonical full-schema JSON and export behavior remains unchanged.

Report export writes the selected compact or expanded human view directly to UTF-8 text without a
byte-order mark, using LF line endings and one final newline. It suppresses the report body on
standard output and prints only a short relative-path confirmation in human mode. It may be combined
with JSON output/export, and its destination follows the same project-root confinement policy.

### Verification

`effective-schema` belongs to both aggregate profiles. Its paired suite covers positive,
available-disabled, planned, deprecated, multiple-provider, dependency-failure, malformed,
deterministic, working-directory-independent path serialization, direct QA/Visualization projection
shape, pack classification and presentation, effective/provider capability presentation, exact and
normalized combined selection, unknown and ambiguous selection, retired shadow-API absence,
path-safety, and generated
400-capability scale behavior. The compatibility check of
the same ID compares complete in-memory JSON, byte-identical canonical file exports, combined
`packs` plus `capabilities` human inspection and byte-identical report exports, deduplicated `all`
expansion, invalid selection, and
malformed-root failure envelopes in Python, PowerShell 7, and Windows PowerShell 5.1 while protecting
canonical outputs.

Focused commands:

```powershell
python Tools\Conformance\run_conformance.py --suite effective-schema --json
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Conformance\Run-Conformance.ps1 -Suite effective-schema -Json
python Tools\Compatibility\run_compatibility.py --check effective-schema --json
```

Last focused parity check: 2026-08-07 for Platform Phase 2.3.5. All three runtimes produced the same
10-pack, 132-capability, 138-namespace effective schema with two deterministic diagnostics. The
paired suite also passed direct QA and Visualization projections, proved all three retired shadow
APIs absent, and completed three deterministic compositions including an unrelated working
directory. The compatibility
check also produced the same 297,916-byte canonical export with SHA-256
`46c42decd28af5e8ba4653e9b51465b0b0289284d3fbb3619c48730d298953e2` and matched the
319-line combined pack/capability report, 1,621-line deduplicated `all` report, and byte-identical
126,473-byte `all` report export with SHA-256
`61e4969cd7fa1fdd1438d95976f5fe3f0d2e58648f8098d7876f64ca40a4da83`. It also matched one
invalid-selector failure and the `malformed-configuration` failure envelope without changing
canonical project output.

## GitHub Actions CI

The tracked `.github/workflows/ci.yml` workflow runs for pull requests, pushes to `main`, and intentional manual dispatches. The tracked `.github/workflows/work-annotations.yml` workflow runs the standalone `Work Annotation Policy` job on every non-`main` branch push. Feature checkpoints therefore receive annotation validation without starting conformance, compatibility, formatting, rendering, or workflow-policy jobs unless the branch also participates in an open pull request. The six stable job/check names are `Work Annotation Policy`, `Workflow Policy`, `Python Validation`, `PowerShell 7 Validation`, `Windows PowerShell 5.1 Validation`, and `Project Compatibility`. Future repository rules may require these names, so avoid casual renames.

`Workflow Policy` installs the checksum-pinned standalone actionlint release declared in the workflow and validates all workflow files. Local preflight uses a system-installed official executable:

```powershell
actionlint -color
```

The runtime jobs install repository dependencies and execute static policy plus the complete registered `baseline` conformance profile in Python, PowerShell 7, and Windows PowerShell 5.1. `Project Compatibility` runs independently on Windows so cross-runtime Visualization, QA, root-discovery, artifact-lifecycle, and canonical-output comparisons are not duplicated across runtime jobs. It selects `pull-request` for PRs and `full-release` for `main` and manual dispatch; Mermaid CLI is installed only for the latter render-bearing profile. Third-party actions are pinned to immutable commit SHAs.

Phase 8 pre-consolidation measurement: manual run `30775535401` at commit `a843616` passed on 2026-08-02 in 5m50s wall-clock. `Workflow Policy` took 7s; Python took 1m07s with 55s in conformance; PowerShell 7 took 3m45s with 2m39s in conformance; and Windows PowerShell 5.1 took 5m46s with 4m36s in conformance. Python setup plus requirements took 4s, while PowerShell requirements took 15s and 19s. The Phase 8 policy retained full PR/main/manual conformance, left ordinary feature-branch pushes quiet, and moved duplicated project-consumer checks into the parallel `Project Compatibility` job. The later standalone annotation workflow intentionally supersedes only the completely quiet feature-push behavior; feature pushes still do not run conformance or compatibility.

Dependency policy after measurement: `setup-python` retains its safe pip cache keyed by `requirements-python.txt`. PowerShell modules are saved fresh into an explicit job-scoped shared module path so PowerShell 7 and Windows PowerShell 5.1 consume the same declarations without relying on runtime-specific user profiles or stale runner state. Actionlint remains checksum-pinned and freshly installed because its measured cost is negligible. Mermaid CLI remains version-pinned and is installed only for `full-release`. The original optimization skipped Puppeteer's browser download and used hosted Microsoft Edge; that assumption was superseded after an independent Edge update broke local rendering. Full-release installation now retains Puppeteer's version-matched Chrome for Testing, while PR compatibility still skips Node entirely. The fresh global installation is intentionally not cached so renderer provenance remains explicit.

Phase 8 post-consolidation validation: manual full-release run `30777449898` at commit `e7204ee` passed all five stable checks on 2026-08-02 in 5m41s wall-clock. `Workflow Policy` took 7s; Python took 1m02s; PowerShell 7 took 2m32s; Windows PowerShell 5.1 took 5m16s; and `Project Compatibility` took 5m36s. The compatibility job spent 3m24s installing pinned Mermaid CLI and 1m35s running all five checks, including three byte-identical renders. Shared job-scoped PowerShell modules loaded successfully in both runtimes. Compared with the 5m50s pre-consolidation run, runtime jobs dropped duplicated consumer checks and the workflow gained registry-driven cross-runtime comparison without increasing the integration wall-clock. Pull requests skip the Mermaid setup and run the four-check `pull-request` profile in parallel with the unchanged full baselines.

## Configuration Files

This section tracks durable configuration and generated state files that affect helper behavior. Add new entries here when a tool starts reading a new config file, writing a new persistent state file, or depending on a shared registry. Do not list ignored one-run artifacts such as `.tmp/`, `Obsidian_Export/`, Python caches, or rendered files generated from an already listed source config.

| File | Kind | Read By | Written By | Purpose | Update When |
| --- | --- | --- | --- | --- | --- |
| `.github/workflows/ci.yml` | Full continuous-integration policy | GitHub Actions, actionlint, maintainers, and future repository rules | Maintainers | Defines five stable full-validation checks, immutable action pins, runtime environments, dependency setup, full conformance, and profile-selected project compatibility for PRs, `main`, and manual dispatches. | A permanent full gate, trigger, runtime, dependency, action pin, compatibility profile, stable check name, or repository-rule requirement changes. |
| `.github/workflows/work-annotations.yml` | Feature-branch annotation policy | GitHub Actions, work-annotation linter, maintainers, and future repository rules | Maintainers | Defines the stable lightweight `Work Annotation Policy` check for every non-`main` branch push without project dependency installation or full validation. | Annotation trigger, Python runtime, action pin, command, permissions, concurrency, timeout, or stable check name changes. |
| `Tools/Conformance/suites.json` | Aggregate conformance registry | `Tools/Conformance/run_conformance.py`, `Tools/Conformance/Run-Conformance.ps1`, CI, and maintainers | Maintainers | Defines stable conformance suite IDs, paired runner paths, named profiles, and discovery exclusions; aggregate validation rejects unregistered or stale runner inventory. | A permanent suite is added, renamed, moved, removed, assigned to a profile, or explicitly excluded from conformance discovery. |
| `Tools/Compatibility/compatibility.json` | Project-compatibility registry | `Tools/Compatibility/run_compatibility.py`, CI, and maintainers | Maintainers | Defines stable compatibility checks, three-runtime execution, representative bounded QA requests, isolated extraction, render assertions, timeouts, and the cumulative `local`, `pull-request`, and `full-release` profiles. | A compatibility check, representative probe, timeout, assertion, or profile membership changes. |
| `Tools/Compatibility/Baselines/lotm-consumers.json` | LoTM consumer compatibility oracle | `Tools/Compatibility/run_compatibility.py`, CI, and maintainers | Maintainers through reviewed output changes | Pins accepted Visualization and QA semantic summaries, complete normalized file inventories, per-file hashes, and aggregate tree hashes so identical cross-runtime regressions cannot pass. It remains project-owned and is excluded from the portable framework rehearsal. | Accepted LoTM content, graph, QA, preset, or representative-boundary behavior intentionally changes after mismatch diagnosis and review. |
| `Tools/Static/work-annotations.json`, `Tools/Static/Fixtures/Work-Annotations/cases.json` | Static-policy registry and conformance fixtures | `Tools/Static/lint_work_annotations.py`, CI, and maintainers | Maintainers | Define executable annotation tags, ownership, eligible/prohibited surfaces, safety bounds, and permanent valid/invalid policy cases. | Annotation syntax, ownership, GitHub tracking, path eligibility, safety bounds, or a permanent regression case changes. |
| `Project_Config/project.yaml` | Project manifest | `Tools/Runtime/Python/knowledge_framework/project_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Project-Config.ps1`, and consumers such as both Obsidian QA exporters | Maintainers | Identifies the project and configures modeled content/resource roots, provenance behavior, registry paths, default QA output, visualization helpers/settings, cleanup helpers, and manifest schema version without coupling framework code to LoTM directory names. | Project identity or paths change, a content/resource root is added, provenance behavior changes, helper locations move, or the manifest schema changes. |
| `Project_Config/composition-baseline.json` | Reviewed project-composition oracle | `Tools/Conformance/Suites/test_project_composition.py`, `Tools/Conformance/Suites/Test-Project-Composition.ps1`, aggregate conformance, CI, and maintainers | Maintainers through reviewed canonical-instance updates | Pins expected project/root identity, registry schemas and counts, selected pack versions, capability state, provider totals, repeated-load passes, and invalid-composition probes without making LoTM values framework fixtures. | A reviewed canonical project registry, selected pack, capability state, provider surface, or composition test obligation intentionally changes. |
| `Framework/Data/unicode-lookup-16.0.0.json`, `Framework/Data/lookup-key-regression-vectors.json`, and the conformance corpora beneath `Framework/Data/` | Pinned framework runtime and conformance data | Strict YAML, lookup, schema-pack, taxonomy, resource, source, entity, provenance, reconciliation, temporal, chronology, and occurrence loaders; paired conformance tools; parity checks; and future semantic identity consumers | Framework maintainers through reviewed data updates | Define deterministic lookup behavior plus vocabulary-neutral positive, malformed, query, ambiguity, authority, boundary, and scale vectors shared by every runtime. Current corpora live in `Lookup-Key/`, `Strict-Yaml/`, `Schema-Packs/`, `Taxonomy/`, `Resources/`, `Sources/`, `Entities/`, `Provenance/`, `Reconciliation/`, `Temporal/`, `Chronology/`, and `Occurrence/`. | A covered registry algorithm changes, or a discovered portability, malformed-input, query, ambiguity, authority, boundary, or scale edge case requires a permanent vector. |
| `Framework/Contracts/README.md`, registry contracts, `Framework/Contracts/strict-configuration-ingestion.md`, `Framework/Contracts/identity-target-provider.md`, and `Framework/Contracts/reconciliation-registry.md` | Framework contract index, registry contracts, strict ingestion rules, and provider boundaries | Framework maintainers and future schema tooling | Framework maintainers | Record executable configuration boundaries, shared YAML semantics, schema ownership, media/work/provenance semantics, identity phases, typed providers, and read-only stable-ID reconciliation. | A configuration contract or provider boundary is introduced, stabilized, moved, or assigned a validator. |
| `Framework/Packs/core/pack.yaml` | Core schema pack | Schema-pack and temporal loaders plus future validation/editor/wizard services | Framework maintainers | Declares domain-neutral platform capabilities plus controlled temporal, evidence-source, claim-namespace, and evidence-artifact vocabulary. | A reusable core capability or evidence primitive changes. |
| `Framework/Packs/README.md` and `Framework/Packs/narrative-*/pack.yaml` | Narrative domain pack catalog and companion packs | Schema-pack, source, and entity loaders plus future narrative editors/wizards | Narrative-domain pack maintainers | Split the narrative foundation, publishing, screen/audio, adaptation, shared-universe, interactive, preservation, and production/rights capabilities into composable contracts without LoTM instances. | A reusable narrative concept is introduced, revised, promoted from planned, or assigned to a different owning pack. |
| `Project_Config/schema-packs.yaml` | Schema-pack composition registry | `Tools/Runtime/Python/knowledge_framework/schema_pack_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Schema-Pack-Config.ps1`, source/entity loaders, and future schema/editor/wizard services | Maintainers; future setup and pack-management wizards | Selects portable schema packs in dependency order, locates their repository-relative contract files, and explicitly activates available capabilities for this project. | A reusable pack is selected, removed, replaced, or moved, or project capability activation changes. |
| `Project_Config/taxonomy.yaml` | Taxonomy registry | `Tools/Runtime/Python/knowledge_framework/taxonomy_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Taxonomy-Config.ps1`, both Obsidian QA exporters, and future content-index, validation, visualization, editor, and migration services | Maintainers through reviewed edits; future category/content-type editors through the mutation service | Defines orthogonal content-type and category IDs, lifecycle, content roots, category policies, path strategies, subject/record slug rules, placements, templates, QA-page eligibility, and graph defaults. | A category/content type is added, promoted, deferred, renamed for display, moved through a planned migration, assigned a template, or given different QA/graph behavior. |
| `Project_Config/resources.yaml` | Resource registry | `Tools/Runtime/Python/knowledge_framework/resource_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Resource-Config.ps1`, and future validation, editor, and migration services | Maintainers through reviewed edits; future resource editors through the mutation service | Defines non-content resource kinds/types, authority roles, editor eligibility, placements beneath configured resource roots, tracking expectations, and required-path behavior. | A resource kind/type or placement is added, renamed for display, moved, given different authority/tracking behavior, or exposed to editors. |
| `Project_Config/sources.yaml` | Source and media registry | `Tools/Runtime/Python/knowledge_framework/source_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Source-Config.ps1`, provenance validation, and future content-index, visualization, editor, and migration services | Maintainers through reviewed edits; future source editors through the mutation service | Instantiates media facets, works, structures and orderings, continuities, applicability scopes, authority profiles, adaptation/distribution records, evidence sources, coverage, relationships, identifiers, and resource bindings; exposes stable provenance targets plus evidence/position/authority services without owning assertions. | A media facet, work, scope, continuity record, production context, structural record, authority rule, adaptation/distribution record, source, coverage declaration, relationship, identifier, or resource binding changes. |
| `Project_Config/chronology.yaml` | Chronology registry | `Tools/Runtime/Python/knowledge_framework/chronology_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Chronology-Config.ps1`, paired chronology conformance tools, and future content-index, visualization, and editor services | Maintainers through reviewed edits; future chronology editors through the mutation service | Instantiates domain-neutral coordinate systems, ordered eras, positions, spans, relations, mappings, and pack-gated narrative work/continuity/branch contexts without redefining civil time. | A chronology axis, era, position, span, relation, anchor, story-time role, or project context changes. |
| `Project_Config/occurrences.yaml` | Occurrence, participation, participant-relative chronology, recurrence-cardinality, recurrence-policy, and subject-state registry | `Tools/Runtime/Python/knowledge_framework/occurrence_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Occurrence-Config.ps1`, provenance, paired occurrence conformance tools, and future content-index, visualization, and editor services | Maintainers through reviewed edits; future occurrence editors through the mutation service | Instantiates branches, templates, concrete occurrences, stable subject participations, participation- and entry-relative selection of existing chronology bindings, ordered track entries, recurrence patterns and executions, aggregate realized-history cardinality, iterations, non-overlapping phases, typed schedules, subject tracks, profiled transitions with exact repeated-visit activation entries, causal relations, outcomes, scoped defaults and execution overrides, deterministic resolution policy, state transitions, and state-referencing carryover without encoding cycles in chronology. | An occurrence or participation identity, participation chronology selection, subjective track entry/order, recurrence pattern/execution/cardinality, phase, schedule, lifecycle, binding, track, transition, causal relation, outcome, rule, state transition, or carryover changes. |
| `Project_Config/interpretations.yaml` | Structural-interpretation registry | `Tools/Runtime/Python/knowledge_framework/interpretation_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Interpretation-Config.ps1`, provenance, paired interpretation conformance tools, and future analytical projection/editor services | Maintainers through reviewed edits; future interpretation editors through the mutation service | Instantiates stable candidate structures, typed canonical or deferred-claim members, interpretation-local relation definitions and edges, and compatible, competing, or mutually exclusive comparison sets without changing canonical graphs or choosing a truth. | An interpretation identity, member, local relation, comparison set, relation definition, lifecycle, or deferred claim reference changes. |
| `Project_Config/entities.yaml` | Entity, incarnation, and identity-phase registry | `Tools/Runtime/Python/knowledge_framework/entity_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Entity-Config.ps1`, provenance, and future content-index, visualization, editor, reconciliation, and migration services | Maintainers through reviewed edits; future entity editors through the mutation service | Instantiates conceptual entities, ambiguity-preserving names, canonical and optionally acyclic lineage, continuity-bound incarnations, scope-backed bindings, incarnation relationships, and persistent-identity phases with explicit scope bindings and succession. | A category membership, shared label/alias, relationship policy, justified incarnation split, continuity membership, scoped appearance, persistent-identity phase, or phase/incarnation relationship changes. |
| `Project_Config/reconciliation.yaml` | Stable-ID reconciliation registry | `Tools/Runtime/Python/knowledge_framework/reconciliation_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Reconciliation-Config.ps1`, provenance, and future editor/migration services | Maintainers through reviewed edits; future reconciliation editors through the mutation service | Preserves bounded branch-aware redirects, merges, splits, tombstone-backed retirements, cross-type reclassifications, privacy-aware labels, strict audit metadata, and superseded/reversed decisions without mutating repository files. | A stable ID changes disposition, a historical decision is superseded/reversed, any resolution safety bound changes, or a migration establishes a new canonical target or type. |
| `Project_Config/provenance.yaml` | Cross-registry provenance registry | `Tools/Runtime/Python/knowledge_framework/provenance_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/Private/Provenance-Config.ps1`, and future validation, editor, comparison, and audit services | Maintainers through reviewed edits; future provenance editors through the mutation service | Owns factual assertions, semantic field paths, evidence links and locators, stable claim grouping, authority evaluation, and acyclic scope-backed claim supersession across typed subject providers. | An assertion, evidence locator, claim value/status/timing, subject field path, or claim-supersession edge changes. |
| `requirements-python.txt` | Dependency registry | `Tools/Commands/Environment/Test-Python.ps1`; human setup via `python -m pip install -r requirements-python.txt` | Maintainers | Defines Python packages required by preferred Python helpers and source maintenance, including `PyYAML` and the pinned Ruff formatter. | Add or change entries when a Python helper or source-maintenance gate gains or removes a third-party package dependency. |
| `requirements-powershell.txt` | Dependency registry | `Tools/Commands/Environment/Test-PowerShell.ps1`; human setup via `Install-Module <module> -Scope CurrentUser -Force -AllowClobber` or elevated `-Scope AllUsers` when machine-wide installs are preferred | Maintainers | Defines PowerShell modules required by repository tools, including `powershell-yaml` for structured configuration/page data and `PSScriptAnalyzer` for source formatting. | Add or change entries when a PowerShell helper gains or removes a module dependency. |
| `requirements-node.txt` | Rendering dependency registry | GitHub Actions `Project Compatibility`; human setup through npm | Maintainers | Pins Mermaid CLI and its Puppeteer peer so local and hosted representative renders share the validated renderer and version-matched Chrome for Testing contract. | Mermaid rendering adopts a reviewed CLI/Puppeteer pair or removes the Node-based renderer dependency. |
| `.gitattributes` | Repository text policy | Git, Ruff, and `Tools/Static/Format-PowerShell.ps1` | Maintainers | Enforces LF for Python and CRLF for PowerShell source/module/config files while preserving Git's normalized text storage. | A tracked source extension or repository line-ending policy changes. |
| `pyproject.toml` | Python formatter and narrow lint configuration | Ruff | Maintainers | Defines repository-wide Python source inclusion, Python 3.10 compatibility, canonical formatting, LF output, 120-character line length, and the current `E501` check. | Python compatibility, formatting, inclusion, line-length, or lint policy changes. |
| `Tools/Static/powershell-format-settings.psd1` | Formatter configuration | `Tools/Static/Format-PowerShell.ps1` and `Invoke-Formatter` from `PSScriptAnalyzer` | Maintainers | Defines deterministic PowerShell indentation, brace placement, whitespace, and trailing-whitespace behavior. | A formatting rule changes; rerun `STATIC-POWERSHELL` in both supported PowerShell runtimes. |
| `Visualization/config/render-settings.json` | Source config | `Visualization/visualize.py`, `Visualization/visualize.ps1`, `Tools/Commands/QA/obsidian_qa_export.py`, `Tools/Commands/QA/Obsidian-QA-Export.ps1` | Maintainers | Defines canonical graph views, source Mermaid paths, rendered output paths, render dimensions, validation settings, reader-boundary filters, report path, and semantic snapshot path. The Obsidian QA export also derives its local `_Generated/repo-refresh-check/` dry-run settings from this file. | Add or remove repository graph views, change render sizes, adjust validation rules, change reader-boundary behavior, or redirect canonical report/snapshot paths. |
| `Visualization/config/puppeteer-config.json` | Source config | `Visualization/visualize.py`, `Visualization/visualize.ps1`, Obsidian QA repo-refresh dry-run helpers through visualization tooling | Maintainers | Configures timeout and launch args while leaving browser selection to Puppeteer's version-matched Chrome for Testing runtime. Machine-specific `executablePath` overrides belong only in ignored diagnostic configs. | Rendering starts timing out, CI/local environment changes, Mermaid rendering needs different launch args, or the bundled-browser policy changes. |
| `Visualization/data/refresh-snapshot.json` | Generated semantic state | `Visualization/visualize.py`, `Visualization/visualize.ps1` | `Visualization/visualize.py --mode Refresh`, `Visualization/visualize.ps1 -Mode Refresh` | Stores the last canonical graph semantic snapshot so refresh reports can detect added/removed nodes, relationships, changed labels, duplicates, and other graph hygiene changes. | Update only through a confirmed canonical graph refresh. Do not edit manually except for explicit debugging that is later reverted or regenerated. |

### Configuration Loader Pair

| Behavior | Python function | PowerShell function |
| --- | --- | --- |
| Decode and load strict framework-registry YAML, enforcing UTF-8 and byte budgets before parsing | `decode_yaml_bytes`, `validate_yaml_source`, and `load_yaml_file` in `strict_yaml.py` | strict byte decoding, `Assert-KnowledgeYamlSource`, and `ConvertFrom-KnowledgeYamlFile` in `Strict-Yaml.ps1` |
| Reject unknown keys in a closed mapping | `assert_allowed_keys` in `strict_yaml.py` | `Assert-KnowledgeMapKeys` in `Strict-Yaml.ps1` |
| Validate the shared RFC 3339 audit profile | `is_rfc3339_timestamp` in `strict_yaml.py` | `Test-KnowledgeRfc3339Timestamp` in `Strict-Yaml.ps1` |
| Validate and run the registered conformance inventory | `Conformance/run_conformance.py` (`--profile`, `--suite`, `--list`, `--json`) | `Conformance/Run-Conformance.ps1` (`-Profile`, `-Suite`, `-List`, `-Json`) |
| Run portable strict-ingestion conformance with structured summary output | `test_strict_yaml.py` (`--json`) | `Test-Strict-Yaml.ps1` (`-Json`) |
| Resolve project root | `knowledge_framework.project_paths.resolve_project_root`, `is_project_root` | `Resolve-KnowledgeProjectRoot`, `Test-KnowledgeProjectRoot` from the `KnowledgeFramework` module |
| Load and validate project manifest | `load_project_config`, `resolve_manifest_path` in `project_config.py` | `Get-KnowledgeProjectConfig`, `Resolve-ProjectManifestPath` in `Project-Config.ps1` |
| Load and validate pinned lookup-key data | `load_lookup_key_config` in `lookup_key_config.py` | `Get-KnowledgeLookupKeyConfig` in `Lookup-Key-Config.ps1` |
| Normalize a semantic lookup value | `LookupKeyConfig.normalize` | `ConvertTo-KnowledgeLookupKey` |
| Compare normalized lookup keys ordinally | Native string equality | `Test-KnowledgeLookupKeysEqual` |
| Run pinned Unicode lookup conformance with structured summary output | `test_lookup_key.py` (`--json`) | `Test-Lookup-Key.ps1` (`-Json`) |
| Load and validate selected schema packs | `load_schema_pack_registry`, `load_pack` in `schema_pack_config.py` | `Get-KnowledgeSchemaPackRegistry`, `ConvertTo-SchemaPackConfig` in `Schema-Pack-Config.ps1` |
| Run schema-pack composition conformance with structured summary output | `test_schema_pack.py` (`--json`) | `Test-Schema-Pack.ps1` (`-Json`) |
| Inspect capability declaration, lifecycle, availability, and activation | `SchemaPackRegistry.capability_declared`, `capability_definitions_for`, `capability_available`, `capability_enabled` | `Test-SchemaPackCapabilityDeclared`, `Get-SchemaPackCapabilityDefinitions`, `Test-SchemaPackCapabilityAvailable`, `Test-SchemaPackCapabilityEnabled` |
| Resolve controlled-value ownership | `SchemaPackRegistry.allowed_values`, `owner_of`, `owns_value` | `Get-SchemaPackAllowedValues`, `Test-SchemaPackOwnsValue` |
| Resolve controlled-value labels, descriptions, and broader values | `SchemaPackRegistry.definition_of` | `Get-SchemaPackValueDefinition` |
| Compose or load the generated effective project schema | `compose_effective_project_schema`, `load_effective_project_schema` in `effective_schema.py` | `New-KnowledgeEffectiveProjectSchema`, `Get-KnowledgeEffectiveProjectSchema` in `Effective-Project-Schema.ps1` |
| Compose a consumer projection | `compose_effective_consumer_schema_projection` | `New-KnowledgeEffectiveConsumerSchemaProjection` |
| Serialize an effective schema or classify failed composition | `effective_schema_json`, `effective_schema_failure` | command serialization plus `New-KnowledgeEffectiveSchemaFailure` |
| Run effective-schema conformance with structured summary output | `test_effective_schema.py` (`--json`) | `Test-Effective-Schema.ps1` (`-Json`) |
| Parse a shared temporal bound or window | `parse_temporal_bound`, `parse_temporal_window` in `temporal_config.py` | `ConvertTo-KnowledgeTemporalBound`, `ConvertTo-KnowledgeTemporalWindow` in `Temporal-Config.ps1` |
| Compare temporal windows and match a precision-aware effective-time query | `temporal_overlap_outcome`, `temporal_windows_overlap`, `temporal_window_match` | `Get-KnowledgeTemporalOverlap`, `Test-KnowledgeTemporalWindowsOverlap`, `Get-KnowledgeTemporalMatch` |
| Normalize a year/month/date/datetime applicability query | `normalize_effective_at` | `ConvertTo-KnowledgeTemporalInstant` |
| Run portable temporal conformance vectors with optional structured summary output | `test_temporal.py` (`--json`) | `Test-Temporal.ps1` (`-Json`) |
| Load and validate chronology coordinate systems, contexts, and non-precedence topology | `load_chronology_registry`, `parse_chronology_registry` in `chronology_config.py` | `Get-KnowledgeChronologyRegistry`, `ConvertTo-KnowledgeChronologyRegistry` in `Chronology-Config.ps1` |
| Query incoming/outgoing context relations and validate typed binding closure | `ChronologyRegistry.context_relations_from`, `context_relations_to`, `validate_context_relation_targets` | `Get-KnowledgeChronologyContextRelationsFrom`, `Get-KnowledgeChronologyContextRelationsTo`, `Assert-KnowledgeChronologyContextRelationTargets` |
| Compare chronology positions without guessing across axes | `ChronologyRegistry.compare_positions` | `Get-KnowledgeChronologyComparison` |
| Run portable chronology conformance vectors | `test_chronology.py` | `Test-Chronology.ps1` |
| Load and validate occurrence and recurrence structure | `load_occurrence_registry`, `parse_occurrence_registry` in `occurrence_config.py` | `Get-KnowledgeOccurrenceRegistry`, `ConvertTo-KnowledgeOccurrenceRegistry` in `Occurrence-Config.ps1` |
| Query branch-state history and state at a branch-local lifecycle ordinal, participation and track-entry identity/order, participant- and entry-relative chronology selections, cardinality claims, iteration contents and boundaries, coordinate reuse, unambiguous track neighbors, recurrence identity and phase, schedule values/due status, carryover, outcomes, pattern rules, subject transitions, and state at an occurrence or exact entry boundary | `OccurrenceRegistry.branch_state_history`, `branch_state_at`, `participations_for_occurrence`, `participations_for_subject`, `chronology_bindings_for_participation`, `chronology_bindings_for_track_entry`, `entries_for_occurrence_on_track`, `previous_track_entry`, `next_track_entry`, `cardinalities_for_recurrence`, `occurrences_for_iteration`, `occurrences_for_iteration_on_track`, `previous_before_iteration`, `next_after_iteration`, `occurrences_at_position`, `previous_on_track`, `next_on_track`, `recurrence_for_occurrence`, `phase_for_iteration`, `expected_schedule_value`, `schedule_match`, `carryovers_into`, `outcomes_for_occurrence`, `rules_for_pattern`, `state_transitions_for_subject`, `state_at`, `state_at_track_entry` | `Get-KnowledgeOccurrenceBranchStateHistory`, `Get-KnowledgeOccurrenceBranchStateAt`, `Get-KnowledgeParticipationsForOccurrence`, `Get-KnowledgeParticipationsForSubject`, `Get-KnowledgeParticipationChronologyBindings`, `Get-KnowledgeTrackEntryChronologyBindings`, `Get-KnowledgeTrackEntriesForOccurrence`, `Get-KnowledgePreviousTrackEntry`, `Get-KnowledgeNextTrackEntry`, `Get-KnowledgeCardinalitiesForRecurrence`, `Get-KnowledgeOccurrencesForIteration`, `Get-KnowledgeOccurrencesForIterationOnTrack`, `Get-KnowledgePreviousBeforeIteration`, `Get-KnowledgeNextAfterIteration`, `Get-KnowledgeOccurrencesAtPosition`, `Get-KnowledgePreviousTrackOccurrence`, `Get-KnowledgeNextTrackOccurrence`, `Get-KnowledgeOccurrenceRecurrence`, `Get-KnowledgeRecurrencePhaseForIteration`, `Get-KnowledgeRecurrenceScheduleValue`, `Get-KnowledgeRecurrenceScheduleMatch`, `Get-KnowledgeCarryoversIntoIteration`, `Get-KnowledgeOutcomesForOccurrence`, `Get-KnowledgeRulesForRecurrencePattern`, `Get-KnowledgeStateTransitionsForSubject`, `Get-KnowledgeStateAt`, `Get-KnowledgeStateAtTrackEntry` |
| Validate branch continuity memberships against the composed source registry | `OccurrenceRegistry.validate_branch_continuity_targets` | `Assert-KnowledgeOccurrenceBranchContinuityTargets` |
| Evaluate scoped recurrence rules with defaults, execution overrides, deterministic selection, and explainable conflicts | `OccurrenceRegistry.evaluate_rules` | `Get-KnowledgeRecurrenceRuleEvaluation` |
| Resolve stable occurrence-registry provenance targets | `OccurrenceRegistry.provenance_target` | `Get-KnowledgeOccurrenceProvenanceTargets` plus typed lookup |
| Run portable occurrence conformance vectors | `test_occurrence.py` | `Test-Occurrence.ps1` |
| Load and validate hosted identity, carrier topology, occupancy, and transitions | `load_hosted_identity_registry` in `hosting_config.py` | `Get-KnowledgeHostedIdentityRegistry` in `Hosting-Config.ps1` |
| Query direct child/parent bindings and active parent/child edges | `HostedIdentityRegistry.bindings_for_child`, `bindings_for_parent`, `parents_at`, `children_at` | `Get-KnowledgeHostCarrierBindingsForChild`, `Get-KnowledgeHostCarrierBindingsForParent`, `Get-KnowledgeHostCarrierParentsAt`, `Get-KnowledgeHostCarrierChildrenAt` |
| Traverse carrier ancestors/descendants and preserve direct versus reachable occupancy | `HostedIdentityRegistry.ancestors_at`, `descendants_at`, `reachable_occupancies_at` | `Get-KnowledgeHostCarrierAncestorsAt`, `Get-KnowledgeHostCarrierDescendantsAt`, `Get-KnowledgeHostCarrierReachableOccupanciesAt` |
| Run portable hosted-identity conformance vectors | `test_hosting.py` | `Test-Hosting.ps1` |
| Load and validate structural interpretations against typed canonical target providers | `load_interpretation_registry` in `interpretation_config.py` | `Get-KnowledgeInterpretationRegistry`, `Get-KnowledgeInterpretationProjectTargetProviders` in `Interpretation-Config.ps1` |
| Query interpretation members, local relations, comparison sets, complete structures, and conservative set decisions | `StructuralInterpretationRegistry.members_for_interpretation`, `relations_for_interpretation`, `comparison_sets_for_interpretation`, `structure_for_interpretation`, `comparison_set_decision` | `Get-KnowledgeInterpretationMembers`, `Get-KnowledgeInterpretationRelations`, `Get-KnowledgeInterpretationComparisonSets`, `Get-KnowledgeInterpretationStructure`, `Get-KnowledgeInterpretationSetDecision` |
| Resolve interpretation provenance targets and close deferred claim IDs | `StructuralInterpretationRegistry.provenance_target`, `validate_claim_targets` | `Get-KnowledgeInterpretationProvenanceTarget`, `Assert-KnowledgeInterpretationClaimTargets` |
| Run portable structural-interpretation conformance vectors | `test_interpretation.py` (`--json`) | `Test-Interpretation.ps1` (`-Json`) |
| Load and validate taxonomy registry | `load_taxonomy_config`, `parse_content_type`, `parse_category` in `taxonomy_config.py` | `Get-KnowledgeTaxonomyConfig`, `ConvertTo-ContentTypeConfig`, `ConvertTo-CategoryConfig` in `Taxonomy-Config.ps1` |
| Run taxonomy configuration conformance with structured summary output | `test_taxonomy.py` (`--json`) | `Test-Taxonomy.ps1` (`-Json`) |
| Load and validate resource registry | `load_resource_config` in `resource_config.py` | `Get-KnowledgeResourceConfig` in `Resource-Config.ps1` |
| Run resource-registry conformance with structured summary output | `test_resource.py` (`--json`) | `Test-Resource.ps1` (`-Json`) |
| Load and validate source registry | `load_source_registry` in `source_config.py` | `Get-KnowledgeSourceRegistry` in `Source-Config.ps1` |
| Run source-registry conformance with structured summary output | `test_source.py` (`--json`) | `Test-Source.ps1` (`-Json`) |
| Load and validate entity/incarnation/phase registry | `load_entity_registry` in `entity_config.py` | `Get-KnowledgeEntityRegistry` in `Entity-Config.ps1` |
| Run entity-registry conformance with structured summary output | `test_entity.py` (`--json`) | `Test-Entity.ps1` (`-Json`) |
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

Last mapped: 2026-08-05.

Last focused parity check: 2026-08-06 for V49 pressure closure. Python, PowerShell 7, and Windows PowerShell 5.1 load manifest schema 11, core pack version 40, occurrence schema 10, and hosted-identity schema 2 with ten selected packs, 138 controlled-value namespaces, 1,038 values, 123 enabled capabilities, 25 reconciliation target types, and 70 provenance subject types. The focused hosting suite composes core-only, foundation, selected-but-disabled foundation, narrative, simulation, compute, and combined pack sets and proves exact vocabulary and provider-state isolation. Its combined fixture uses eight carriers, six bindings, ten occupancies, and three transitions; proves direct and transitive paths, child movement between parents, paired cross-track boundaries, reachable occupancy without direct-occupancy promotion, dormant co-residence, and co-control; rejects 46 invalid configurations and 14 invalid queries; and exercises 128 carriers, 128 occupancies, and a 127-binding chain. The schema-pack suite accepts explicit vocabulary-only extensions while rejecting 58 malformed compositions. All three runtimes emitted matching semantic summaries.

### Project Manifest Contract

`Project_Config/project.yaml` is the bootstrap configuration copied into each framework implementation. `schema_version`, `project_id`, `framework`, and `domain` identify the contract and implementation. All configured paths must be repository-relative; the shared loaders reject absolute paths, paths that escape the repository, missing canonical roots, and missing required helper, config, or registry files.

`paths.content_roots` is an ordered list. Each entry declares a stable `id`, a `path`, and a provenance rule. Content-type records refer to the stable ID so a root path can change through a migration without changing content-type or category identity:

- `child-directory`: derive the provenance label from the first directory beneath the configured root. The LoTM `Glossary_Threads/Characters/` path therefore contributes `character`.
- `fixed`: use `provenance_label` for every record under that root. The LoTM `Volumes/` root therefore contributes `volume`.
- `slug-prefix`: skip path-based provenance and fall back to the record slug prefix.

`paths.resource_roots` declares stable IDs, repository-relative paths, and whether each non-content resource root must exist. Content-root and resource-root IDs share one namespace. `paths.qa_export` defines the default generated QA destination. `paths.visualization` identifies the Python and PowerShell visualization helpers plus render settings and Puppeteer configuration. `paths.cleanup` identifies the matching disposable-cache cleanup helpers.

`registries.schema_packs`, `registries.taxonomy`, `registries.resources`, `registries.sources`, `registries.chronology`, `registries.occurrences`, `registries.entities`, `registries.hosting`, `registries.reconciliation`, `registries.interpretations`, `registries.provenance`, and `registries.lookup_keys` locate the selected-pack, content, resource, source, chronology, occurrence/recurrence, entity/incarnation, hosted-identity, stable-ID reconciliation, structural-interpretation, cross-registry provenance, and pinned Unicode lookup-key registries.

### Schema-Pack Contract

`Project_Config/schema-packs.yaml` selects portable packs from `Framework/Packs/` or a project-owned extension location in dependency order. Each pack declares a stable ID, independent pack version, lifecycle, compatibility kind (`core`, `domain`, or `extension`), capabilities, dependencies, and namespaced controlled values. Schema-5 packs additionally require the presentation and classification contract in `Framework/Contracts/schema-pack-presentation.md`: family, architectural role, scope, explicit domains and bridge joins, localizable pack text, and rich capability presentation. A dependent pack must follow every dependency and satisfy its minimum version.

Pack selection makes capability declarations discoverable. Schema-5 capabilities are mapped definitions with lifecycle `planned`, `available`, or `deprecated` plus a stable localization key, friendly label, and useful description; string shorthand remains accepted only while loading legacy schema-4 packs. Planned capabilities cannot be enabled, available capabilities may be enabled, and deprecated capabilities remain activatable only for compatibility or migration. `capability_activation.enabled` enables only eligible capabilities used by the project, and `capability_activation.default` must be `disabled`. Missing capabilities therefore disappear cleanly from unrelated industry implementations, while missing pack dependencies and explicit references to unavailable or disabled contracts remain validation errors. Pack files keep controlled vocabulary atomic and express executable relationships through typed `semantic_declarations`; loaders reject the superseded delimiter-composed semantic namespaces and enforce exact ownership, known members, completeness, and cross-pack closure.

Controlled values use dotted ownership namespaces such as `source.work-type`. Values may be extended by multiple selected packs, but one exact namespace/value pair has one owner. A value may provide a display label, description, and broader value in the same namespace. The current `core` pack owns generic evidence-source roles and evidence-artifact relationships. `narrative-media` owns the foundation and media-axis vocabularies; publishing, screen/audio, adaptation, distribution, production, and shared-universe companion packs own their narrower release, segment, container, lineage, mapping, manifestation, platform, production/rights, and incarnation values. `anime`, `donghua`, `manga`, `manhwa`, `manhua`, and `webtoon` remain meaningful cultural forms while modality is modeled separately. Embedded visuals may originate in EPUBs, comics, scans, or future supported containers; extraction preserves the `illustration` medium profile, still-image modality, source container, evidence provenance, and any promoted page-ready derivative as separate facts. Source and entity loaders reject configured vocabulary outside the aggregate selected-pack contract.

Pack files define reusable semantics and recommendations. Project registries instantiate them. A narrative pack may define `television-special`; it must not define the LoTM work `lotm-donghua-special-1`. Future setup and editor wizards should read pack capabilities and controlled values, then create project-instance configuration through reviewed mutation services.

### Chronology Registry Contract

`Project_Config/chronology.yaml` instantiates coordinate systems separately from RFC 3339 civil timestamps. Coordinate systems may be calendar, era-ordinal, ordinal, or relative integer axes; declare value domains, direction, zero policy, positions, open or bounded spans, explicit relations, exact direct mappings, pack-gated contexts, and non-precedence context topology. Era-local direction supports systems whose values count down in one era and up in another. Years below zero and above 9999 remain ordinary chronology coordinates rather than invalid civil timestamps. Context topology never makes otherwise unrelated coordinates comparable.

The paired comparison APIs return `before`, `after`, `concurrent`, or `incomparable`. They compare coordinates through intrinsic axis order and the transitive closure of exact relations, relative origins, and equivalent mappings. They validate those facts as one combined acyclic order graph. They do not extrapolate mapping formulas, infer calendar conversions, impose total order across branches, or confuse publication, reader disclosure, causal order, and story chronology. The LoTM registry currently instantiates the five Epochs and a novel-story context but deliberately contains no unsupported dates or anchors.

### Occurrence Registry Contract

`Project_Config/occurrences.yaml` keeps concrete occurrences distinct from templates and coordinates, each subject participation distinct from the occurrence, each ordered track entry distinct from its participation, and concrete recurrence executions distinct from reusable patterns. Branch identity is stable; branch-state transitions preserve append-only lifecycle, activation occurrences, fork or merge triggers, and branch-local state order without deleting inactive records or creating chronology edges. Branch continuity memberships resolve against the source registry during project composition. One subject may revisit one occurrence through semantically distinct participations; contiguous track-entry ordinals preserve subjective order, while occurrence-relative navigation rejects ambiguity. Participation may reference an existing chronology context but does not create context topology or chronology order. Branch and recurrence parentage is acyclic; lifecycle and same-recurrence track order are coherent; primary bindings cannot contradict exact chronology; transition profiles enforce track, chronology, containment, and branch semantics; causal cycles remain separate from chronology while semantic duplicates are rejected. Non-overlapping execution phases and typed schedules feed bounded rules with subject-qualified conditions, explicit applicability, defaults/overrides, priority, selection mode, conflict reporting, and explainable traces. Typed pack declarations validate branch lifecycle vocabulary, transition and state-change profiles, state profiles and mandatory kind mappings, outcome incompatibility, rule/effect and effect/target compatibility, recurrence-pattern scope, repetition policy, and global or same-target effect incompatibility. Evaluation reports `proposed_effects`, `authorized_effects`, contributor lineage, proposed execution counts, and an `execution_disposition`; any conflict or indeterminate applicability leaves authorization empty. Civil schedule projection is portable only within years `0001` through `9999`, while chronology-step schedules remain integer-coordinate operations. Subject-state transitions identify a composed profile, change shape, mechanism, paired availability, profile-governed paired completeness and attitude, activation, and sources. All used dimensions remain continuous along a subject/payload/state chain; carryover references the applicable state across a participating iteration boundary. Every stable record shape is exposed to centralized provenance, while chronology and provenance retain order and evidence authority respectively.

### Taxonomy Registry Contract

`Project_Config/taxonomy.yaml` separates `categories` from `content_types`. A Glossary Page requires a category; an Investigation Record permits a category for subject-linked research while allowing uncategorized project investigations; Volume Summary, Analysis Board, Project Dashboard, and Navigation Index records forbid categories. Categories define subject identity once and provide placements under eligible content types, so Character glossary pages and Character investigations share the `character` category without pretending to be the same record type. Fixed-file records identify one existing repository-relative file beneath their content root; root-file records discover matching files directly beneath a root. Default templates are optional for content types that do not scaffold records.

Deferred categories remain visible to planning and future editors but set `canonical_pages_enabled: false` and intentionally omit subject slugs, placements, and graph classes until promotion. The paired taxonomy loaders reject malformed stable IDs, unknown root/content-type references, incompatible category policies, absolute or escaping relative paths, invalid slug regular expressions, missing required templates or fixed files, duplicate metadata types, duplicate subject prefixes, duplicate placements, duplicate fixed record paths, and duplicate graph classes.

The QA exporters now consume the effective-schema QA projection for enabled roots and content types,
category and fixed-record eligibility, labels and plural labels, placement/export folders, exact slug
patterns and prefixes, and metadata-type graph-class lookup. Exact schema patterns are significant:
for example, the `volume` page prefix must not turn an ordinary `volume-1` data identifier into a
page reference when the configured page pattern requires `volume-01-<slug>`. Transitional
Markdown/YAML parsing, Relationship Seeds, data projections, QA graph rendering, filenames, and
cleanup remain compatibility adapters until the normalized content-index and visualization phases
replace them.

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

### Compatibility Orchestration

`Tools/Compatibility/run_compatibility.py` is the canonical Python orchestrator for cross-runtime
project-consumer comparisons and isolated framework extraction. It loads the strict schema-2
`Tools/Compatibility/compatibility.json` registry, requires Python, PowerShell 7, and Windows
PowerShell 5.1, launches each runtime's own implementation, and does not implement domain behavior
itself. This canonical orchestration exception does not relax parity requirements for Visualization,
QA export, cleanup, conformance, or their runtime services.

| Behavior | Command |
| --- | --- |
| Compare Visualization and redirected QA output during implementation | `python Tools/Compatibility/run_compatibility.py --profile local` |
| Add root-discovery and artifact-lifecycle protection before PR readiness | `python Tools/Compatibility/run_compatibility.py --profile pull-request` |
| Add representative three-runtime rendering for version closure | `python Tools/Compatibility/run_compatibility.py --profile full-release` |
| Rehearse a neutral standalone framework copy directly | `python Tools/Compatibility/verify_framework_extraction.py --json` |

The extraction verifier copies `Framework/`, `Tools/Runtime/`, `Tools/Conformance/`, the Python and PowerShell dependency declarations, and the Python formatter policy into a unique operating-system temporary directory. It does not copy the LoTM `Project_Config/`; it generates a neutral core-only `extraction-smoke` manifest and placeholder consumer registry paths. The copied tree must omit nine canonical or generated project surfaces, then pass project-root, strict-ingestion, lookup-key, schema-pack, temporal, and structural-interpretation conformance with identical structured summaries in Python, PowerShell 7, and Windows PowerShell 5.1. The temporary copy is removed automatically on success or failure.
| Select checks for diagnosis | repeat `--check CHECK_ID` |
| List profiles and checks | `--list`; add `--json` for structured output |
| Select project root or registry | `--root PATH`, `--registry PATH` |
| Retain successful output or choose its scoped destination | `--keep-output`, `--output-root .tmp/PATH` |

The registry rejects unknown top-level and check-specific keys, duplicate IDs or selections, unsupported check kinds, unsafe render paths, invalid timeouts/assertions, stale profile references, and altered required runtime order. The profiles are cumulative: `local` contains `effective-schema`, `visualization`, and `qa`; `pull-request` adds `root-discovery`, `artifact-lifecycle`, and `framework-extraction`; `full-release` adds `render`.

Each run creates one unique child beneath `.tmp/compatibility/`. It compares complete redirected
trees and structured summaries after normalizing only generated timestamps, redirected `.tmp`
output roots, accepted newline differences, and JSON property formatting. It does not normalize
semantic IDs, labels, relationship data, visibility boundaries, counts, inventories, or ordering.
Visualization and QA must also match the project-owned oracle in
`Tools/Compatibility/Baselines/lotm-consumers.json`, including semantic summaries, complete file
inventories, per-file hashes, and aggregate tree hashes. The render check permits renderer-internal
byte differences only while requiring nonblank SVG output, configured labels, minimum size, and
matching semantic dimensions.

Protected canonical Visualization configuration, reports, snapshots, graphs, renders, and the configured QA export are hashed before and after every run. Successful output is removed through the maintained cleanup command unless `--keep-output` is supplied. Failed output is retained for diagnosis. An explicit output root must be a child of repository `.tmp/`; the repository root, `.tmp/` itself, and outside paths are rejected.

Last compatibility check: 2026-08-07 for Platform Phase 2.3.5. The 293.4-second `full-release`
profile passed all seven registered checks after the temporary consumer-shadow APIs were retired.
Visualization preserved 15 nodes, 121 relationships, all five redirected refresh files, refresh
tree SHA-256
`dfb0ffd4a11d304ab2ffd2571bfba4717b087c512d46abd6120f920835577fe6` and unbounded graph SHA-256
`477eb74726f1c8430ad52c5a187db3bfd402404115f36ce2bf1750f8c6531cc4`.
QA preserved 16 notes, 121 relationships, 71 data references, all 34 files, and tree SHA-256
`2b754c78c5ed76d782f152b68d73df680029f1e40e5b7be5c4280fcc9c4bc292`. All twelve root launches,
six unsafe artifact destinations, the 236-file neutral framework extraction, and three identical
298,269-byte nonblank SVG renders passed. Canonical outputs remained unchanged and successful scoped
output was removed.

### Aggregate Conformance

The paired aggregate runners accept an optional repository root, validate `Tools/Conformance/suites.json`, and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run every registered permanent suite | `python Tools/Conformance/run_conformance.py --profile baseline` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Run-Conformance.ps1 -Profile baseline` |
| Run the quick local profile | `python Tools/Conformance/run_conformance.py --profile fast` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Run-Conformance.ps1 -Profile fast` |
| Select focused suites | repeat `--suite SUITE_ID` | pass an array with `-Suite ID1,ID2` |
| List registered suites and profiles | `--list` | `-List` |
| Emit stable aggregate results | `--json` | `-Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

`baseline` is the CI and framework-version conformance profile. `fast` is the local feedback profile; ordinary feature-branch pushes run only the separate hosted work-annotation policy rather than a lighter conformance tier. It does not replace baseline, visualization, or QA compatibility validation. Both implementations detect unregistered discovered conformance runners, missing registered files, stale exclusions, duplicate IDs or paths, invalid profiles, and paths outside the repository. Each suite runs in an isolated child process to preserve script behavior and PowerShell scope isolation. Runtime module extraction alone does not make in-process PowerShell aggregation safe: current suites remain top-level scripts that define functions, import modules with process scope, mutate process-local state, and terminate through script exit behavior. Retain child-process execution until suites expose callable APIs with explicit state-reset and error-return contracts, then prove equivalent isolation before changing the aggregate runner.

Last aggregate parity check: 2026-08-07 for Platform Phase 2.3.5. The `baseline` profile passed all
seventeen registered suites in Python, PowerShell 7, and Windows PowerShell 5.1 with matching suite
IDs, statuses, and canonicalized semantic summaries in 618.5 seconds combined. The effective-schema
suite preserved 10 active packs, 132 declared capabilities, 123
enabled capabilities, nine planned capabilities, 138 controlled-value namespaces, and two
deterministic deferred-category diagnostics while exercising four synthetic lifecycle/provider states,
one classified dependency failure, and a 400-capability scale composition. The complete baseline
also preserved 25 reconciliation target types, 71 provenance subject types, fourteen invalid
cross-registry compositions, every existing registry corpus, and the established hosting and
interpretation scale probes. Source, entity, provenance, hosting, interpretation, and project
composition remain outside the nine-suite `fast` profile because their repeated dependency
composition is materially expensive. Phase 2.3.5 replaced shadow-parity probes with direct consumer
projection and retired-API assertions without changing aggregate profile membership.

### Strict YAML Conformance

The paired strict-ingestion runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run the portable strict-ingestion corpus | `python Tools/Conformance/Suites/test_strict_yaml.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Strict-Yaml.ps1` |
| Emit stable corpus counts | `python Tools/Conformance/Suites/test_strict_yaml.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Strict-Yaml.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners validate portable scalar values and types, canonical mapping keys, forbidden YAML constructs, duplicate keys, exact schema-version typing, strict UTF-8 without BOM, byte/depth/node/scalar budgets, and the shared RFC 3339 profile. Source, byte, and budget probes use uniquely named operating-system temporary directories that are removed before exit.

### Lookup-Key Conformance

The paired lookup runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run pinned Unicode and malformed-registry vectors | `python Tools/Conformance/Suites/test_lookup_key.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Lookup-Key.ps1` |
| Emit stable corpus counts and Unicode version | `python Tools/Conformance/Suites/test_lookup_key.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Lookup-Key.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners load the manifest-selected Unicode registry, consume equivalent, distinct, exact-output, and Hangul vectors, reject non-string and unpaired-surrogate inputs, and apply thirteen process-local malformed registry mutations. Every mutation is written beneath a uniquely named operating-system temporary directory and removed before exit; the 354 KB canonical registry is not duplicated in source control.

### Schema-Pack Conformance

The paired schema-pack runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run canonical, synthetic, malformed, and scale composition checks | `python Tools/Conformance/Suites/test_schema_pack.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Schema-Pack.ps1` |
| Emit stable composition counts | `python Tools/Conformance/Suites/test_schema_pack.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Schema-Pack.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners load the canonical schema-5 selected packs, validate the complete 14-pack catalog and its 136 capability presentations, and consume the shared independent schema-5 corpus plus one-pack schema-4 compatibility fixture in `Framework/Data/Schema-Packs/`. The synthetic composition proves independent compatibility kind and architectural role, foundation/domain/bridge classification, scope and domain closure, exact bridge joins, localizable pack presentation, equivalent multi-provider capability presentation, dependency-version boundaries, lifecycle, activation, controlled-value hierarchy and ownership, and typed occurrence semantic closure. Ninety-one shared structured mutations must be rejected, presentation-only text changes must preserve semantic composition, and two typed pair declarations that collide under the superseded delimiter encoding must remain distinct. A generated 64-pack schema-5 composition must retain exact pack, capability, activation, value, presentation, and typed-declaration counts. Mixed schema-4/schema-5 compositions fail closed. Each case runs in a unique operating-system temporary tree that is removed before exit.

### Taxonomy Conformance

The paired taxonomy runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run canonical, synthetic, malformed, query, and scale checks | `python Tools/Conformance/Suites/test_taxonomy.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Taxonomy.ps1` |
| Emit stable taxonomy counts | `python Tools/Conformance/Suites/test_taxonomy.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Taxonomy.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners load the canonical taxonomy and the vocabulary-neutral corpus in `Framework/Data/Taxonomy/`. The fixture proves active/deferred lifecycle, required/optional/forbidden category policy, all four path strategies, category and record slug modes, all metadata modes, default and overridden templates, fixed records, category placements, reconciliation targets, and QA content-root selection. Forty-eight shared structured mutations must be rejected, two invalid target queries must fail, and a generated 128-category composition must preserve exact counts. Every case runs in a unique operating-system temporary tree that is removed before exit.

### Resource Conformance

The paired resource runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run canonical, synthetic, malformed, query, and scale checks | `python Tools/Conformance/Suites/test_resource.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Resource.ps1` |
| Emit stable resource counts | `python Tools/Conformance/Suites/test_resource.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Resource.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners load the canonical resource registry and the vocabulary-neutral corpus in `Framework/Data/Resources/`. The fixture proves active/deferred lifecycle, all six authority values, editor eligibility, all three tracking modes, required/optional and multiple placements, root-relative resolution, and reconciliation targets. Thirty shared structured mutations must be rejected, two invalid target queries must fail, and a generated 128-type composition must preserve exact counts. Every case runs in a unique operating-system temporary tree that is removed before exit.

### Source Conformance

The paired source runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run canonical, synthetic, malformed, query, and scale checks | `python Tools/Conformance/Suites/test_source.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Source.ps1` |
| Emit stable source counts | `python Tools/Conformance/Suites/test_source.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Source.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners load the canonical source registry and the vocabulary-neutral schema-18 corpus in `Framework/Data/Sources/`. The fixture exercises work and continuity structure, media and both structural-position strategies, authority inheritance and fallback, scoped applicability, adaptations, manifestations, release/distribution records, evidence sources, observations, coverage, identifiers, localized titles, resource bindings, and reconciliation/provenance targets. Sixty-five shared structured mutations must be rejected, fifteen invalid service queries must fail, and a generated 128-source composition must preserve exact counts. Every case runs in a unique operating-system temporary tree that is removed before exit.

### Entity Conformance

The paired entity runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run canonical, synthetic, malformed, query, and scale checks | `python Tools/Conformance/Suites/test_entity.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Entity.ps1` |
| Emit stable entity counts | `python Tools/Conformance/Suites/test_entity.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Entity.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners load the canonical entity registry and compose the vocabulary-neutral schema-4 corpus in `Framework/Data/Entities/` against the independent taxonomy and source fixtures. The fixture proves conceptual entity/category membership, active/deferred lifecycle, ambiguity-safe aliases, canonical/inverse and symmetric relationship semantics, cycle rejection, lineage basis roles, continuity-bound incarnations, applicability bindings, entity- and incarnation-subject identity phases, ordered phase relationships, and reconciliation/provenance targets. Eighty-six shared structured mutations must be rejected, fifteen invalid service queries must fail, and a generated 128-entity composition must preserve exact counts. Every case runs in a unique operating-system temporary tree that is removed before exit.

### Provenance Conformance

The paired provenance runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run canonical, synthetic, malformed, query, authority, and scale checks | `python Tools/Conformance/Suites/test_provenance.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Provenance.ps1` |
| Emit stable provenance counts | `python Tools/Conformance/Suites/test_provenance.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Provenance.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners load the canonical registry chain and compose the vocabulary-neutral schema-3 corpus in `Framework/Data/Provenance/` against independent source, entity, chronology, and occurrence fixtures. Twenty fixture assertions prove assertion shape consistency, typed target lookup including recurrence-cardinality, occurrence-participation, and occurrence-track-entry fields, semantic field paths, evidence roles, point/range locators, source scope and coverage, temporal windows, claim applicability, acyclic supersession, and five winner, corroborating-tie, equal-rank-conflict, or incomparable authority outcomes. Sixty-eight shared structured mutations must be rejected, five invalid service queries must fail, and a generated 128-assertion composition must preserve exact counts. Every case runs in a unique operating-system temporary tree that is removed before exit.

### Hosted Identity Conformance

The paired hosting suites load the canonical empty project registry and a vocabulary-neutral
schema-2 fixture with eight carriers, six child/parent bindings, ten occupancies, and explicit
control-handoff, move, and copy transitions. They verify independent carrier lifecycle, inclusive
activation and exclusive termination, active/dormant/co-resident occupants, deterministic single-
and co-controller sets, paired same- and cross-track binding boundaries, cycle rejection, direct and transitive paths,
reachable occupancy without promotion, identity/relationship provider closure, reconciliation and
provenance targets, 46 invalid configurations, 14 invalid queries, and generated
128-carrier/128-occupancy/127-binding scale probes. The suite is baseline-only and removes its
uniquely named operating-system temporary tree before exit.

| Action | Python | PowerShell |
| --- | --- | --- |
| Run carrier, occupancy, transition, malformed, query, and scale checks | `python Tools/Conformance/Suites/test_hosting.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Hosting.ps1` |
| Emit the stable hosting summary | `python Tools/Conformance/Suites/test_hosting.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Hosting.ps1 -Json` |

### Structural Interpretation Conformance

The paired structural-interpretation runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run canonical, synthetic, malformed, query, and scale checks | `python Tools/Conformance/Suites/test_interpretation.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Interpretation.ps1` |
| Emit stable interpretation counts | `python Tools/Conformance/Suites/test_interpretation.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Interpretation.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners load the canonical empty registry and compose the vocabulary-neutral schema-1 corpus in `Framework/Data/Interpretations/` against typed fixture providers. Three interpretations, seven members, four local relations, and three comparison sets prove stable candidate identity, canonical target reuse, deferred provenance-claim membership, local inverse/cycle behavior, compatible and unresolved conservative decisions, provenance targeting, and canonical-graph isolation. Thirty-six invalid configurations and eight invalid queries must fail, while a generated 128-member structure with 127 relations protects bounded scale. The suite is baseline-only and removes its uniquely named operating-system temporary tree before exit.

### Project Composition Conformance

The paired project-composition runners accept an optional repository root and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run the full canonical composition and invalid wiring probes | `python Tools/Conformance/Suites/test_project_composition.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Project-Composition.ps1` |
| Emit the stable composition summary | `python Tools/Conformance/Suites/test_project_composition.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Project-Composition.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |

Both runners load every manifest-owned canonical registry twice in dependency order and compare the result with `Project_Config/composition-baseline.json`. The reviewed project-instance oracle pins exact root IDs, registry schemas and record counts, selected pack versions, declared/available/enabled capabilities, disabled capability IDs, controlled vocabulary totals, reconciliation and provenance provider totals, and repeat-pass/probe counts. The suite also verifies provider and object closure, deferred interpretation-claim closure, deterministic repeated loads, clean absence of disabled capabilities, and rejection of twelve missing, duplicate, unregistered, or capability-disabled cross-registry compositions. It belongs only to `baseline`; reusable registry semantics remain owned by the neutral fixture suites.

### Reconciliation Registry Contract

`Project_Config/reconciliation.yaml` schema 4 is loaded after the project has assembled stable-record providers enabled by its packs. The current LoTM composition supplies 24 target types from taxonomy, resources, sources, and entities, but the loader itself imports no narrative registry and accepts domain-specific providers from other implementations. Each provider has a stable ID plus current-record and alias-key maps. Target-type values and installed providers must close exactly, two providers cannot claim the same type, and a tombstoned stable ID cannot also remain an alias. The root, resolution, record, target, and audit mappings are closed shapes; active present sources permit only redirect compatibility; and record, target, branch, and traversal budgets are mandatory.

Every record preserves a typed source ID, current presence or tombstone state, privacy-aware snapshot/redacted/omitted label mode, pack-approved operation/reason pair, active/superseded/reversed status, and repository-derived or strict explicit audit metadata. Redirect, merge, and split preserve type; reclassification alone crosses type. Active chains must be acyclic and terminate at current records or retirements, while superseded decisions lead to one active decision for the same source. Memoized iterative resolution returns canonical, redirected, ambiguous, or retired outcomes, deduplicated terminal summaries, and ordered branches with independent paths. `resolution.max_records`, `max_targets_per_record`, `max_branches`, and `max_resolution_steps` independently bound registry size, direct fan-out, terminal split expansion, and traversal work. The resolver never chooses or erases a split branch and never mutates a page, path, alias, graph, or registry reference.

The paired conformance tools accept only repository-root and deep-chain-size overrides and leave no persistent output:

| Behavior | Python | PowerShell |
| --- | --- | --- |
| Run default corpus and 1,500-hop stress case | `python Tools/Conformance/Suites/test_reconciliation.py` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Reconciliation.ps1` |
| Emit structured corpus and stress-test counts | `python Tools/Conformance/Suites/test_reconciliation.py --json` | `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Reconciliation.ps1 -Json` |
| Select repository root | `--root PATH` | `-Root PATH` |
| Override stress depth | `--deep-chain N` | `-DeepChain N` |

Both load the canonical project composition, validate canonical mapping keys through `Framework/Data/Strict-Yaml/`, layer synthetic records into process-local fixture providers, validate the malformed-policy, byte-budget, branch/step-limit, and expected-result corpus in `Framework/Data/Reconciliation/`, create uniquely named malformed-byte and deep-chain files in the operating-system temporary directory, and remove them before exit.

### Provenance Registry Contract

`Project_Config/reconciliation.yaml` schema 4 is loaded after stable-record providers and before provenance. Its paired loaders enforce canonical YAML ingestion, pack/provider closure, alias ownership, record/fan-out/branch/traversal bounds, and history invariants, then resolve current or historical IDs without mutating files. `Project_Config/interpretations.yaml` schema 1 then composes canonical subject providers while preserving `provenance-claim` members as deferred typed IDs. `Project_Config/provenance.yaml` schema 3 composes source, entity, reconciliation, chronology, occurrence, and interpretation provenance providers, then closes those deferred claim references. The paired provenance APIs own assertion parsing, semantic field-path resolution, evidence-link and locator validation, stable claim grouping, scope-backed acyclic claim supersession, cross-registry target integrity, and shared-kernel observation/effective timing. `ProvenanceRegistry.evaluate_claim_authority` / `Get-KnowledgeClaimAuthorityEvaluation` delegate evidence ranking to source authority decisions and then report winner, tie, conflict, or incomparable outcomes.

The source registry remains authoritative for evidence artifacts, permitted media and modes, work and release-object scope, coverage, structural position validation, and authority profiles. Subject registries remain authoritative for normalized target records. Neither source nor entity registries store an assertion collection. A new target registry participates by exposing typed stable-record lookup and supplying its `provenance.subject-type` values through a selected pack.

### Future Config Extensions

Controlled relationship types, field-scoped enums, aliases, and confidence/precedence rules remain planned additions to the taxonomy registry through reviewed migrations. Capability-gated omission of registry files and controlled-value providers remains project-composition/bootstrap work; the current manifest requires its declared registry paths even when a downstream implementation would disable the corresponding capability.
