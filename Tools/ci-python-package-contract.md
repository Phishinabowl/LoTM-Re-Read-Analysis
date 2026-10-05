# Python Runtime Package And Component Version Contract

**Status:** CI 3.1.1 assessment and design confirmed on 2026-10-05 from `ee653a6`,
`architecture/ci-testing-modernization`. The maintainer explicitly selects independent Python
versioning starting at 0.1.0 and Python 3.14+ eligibility, with exact 3.14.5 bootstrap/testing.
Backend, artifact and dependency details below are the accepted implementation contract. No
packaging metadata, version module, dependency declaration, runtime behavior or hosted job is
implemented by this document. All five 3.1.1 checklist items are confirmed; implementation is CI 3.1.2 and
installed-artifact proof is 3.1.3. The [modernization plan](ci-testing-modernization-plan.md) owns gates.

## Confirmed Entry Inventory

`pyproject.toml` currently contains only Ruff configuration. Its `target-version = "py310"`
constrains source syntax; it does not declare package eligibility or prove execution on Python 3.10.
There is no `[project]`, `[build-system]`, Python package version or installed-distribution contract.
`knowledge_framework` is an existing regular package under `Tools/Runtime/Python/`.

AST inspection finds 22 Python files, internal relative imports, standard-library imports and
one external import, `yaml`, in `strict_yaml.py`. There are no current non-Python package files,
dynamic module-import loaders or native extensions. The current `requirements-python.txt` mixes
`PyYAML>=6.0.2` with development formatter `ruff==0.16.1`; importing the runtime does not require
Ruff, pytest or Pillow. Package initialization imports runtime services and therefore PyYAML;
build-time version extraction must not require importing that service graph.

31 direct Python consumers insert the source runtime directory into `sys.path`. Source selection
is therefore intentional today; installing a wheel alone does not make these commands test it.

| Direct consumers | Existing surface / implementation proof owner |
| --- | --- |
| Framework CLI (2) | `Commands/Framework/inspect_effective_schema.py`, `inspect_framework_catalog.py`: preserve filenames, arguments, outputs and source imports at 3.1.2. |
| Maintenance/media/QA CLI (4) | `Commands/Maintenance/clean_temp_files.py`; `Commands/Media/edit_image.py`, `search_epub.py`; `Commands/QA/obsidian_qa_export.py`: preserve source entry points; media dependencies stay separate. |
| Compatibility (2) | `Compatibility/run_compatibility.py`, `verify_framework_extraction.py`: preserve runtime discovery/report contracts; explicitly migrate copied build inputs and dependency checks. |
| Conformance suites (21) | All current Python suite files listed below: preserve source fixtures and summaries; add a distinct installed-runtime verification route at 3.1.3. |
| Conformance runner (1) | `Conformance/run_conformance.py`: preserve source runner and registered ordering; subprocesses must not silently substitute installed code. |
| Visualization (1) | `../Visualization/visualize.py`: preserve source imports, dependency availability and accepted output baseline; exclude its implementation from the wheel. |

The 21 direct suite filenames under `Conformance/Suites/` are `test_capability_roadmap.py`,
`test_chronology.py`, `test_distribution_boundary.py`, `test_effective_schema.py`, `test_entity.py`,
`test_framework_catalog.py`, `test_framework_installation.py`, `test_hosting.py`,
`test_interpretation.py`, `test_lookup_key.py`, `test_occurrence.py`, `test_project_composition.py`,
`test_project_paths.py`, `test_provenance.py`, `test_reconciliation.py`, `test_resource.py`,
`test_schema_pack.py`, `test_source.py`, `test_strict_yaml.py`, `test_taxonomy.py` and `test_temporal.py`.
Filenames differ from some registered suite IDs; retain `Conformance/suites.json` as membership authority.

Other declaration consumers are `Commands/Environment/Test-Python.ps1` (currently probes names,
not exact versions and skips requirement flags), `.github/workflows/ci.yml` (two install/cache jobs),
`work-annotations.yml` (exact interpreter), extraction `COPY_FILES`, root setup recipes and
`TOOLING_REFERENCE.md` dependency/configuration rows. The future bootstrap owns strict dependency
and interpreter verification; hosted transport migration remains Phase 6. Native tests, catalogs
and installed-artifact checks must explicitly report which runtime path they exercise.

## Identity, Versions And Interpreter Policy

| Concern | Contract for implementation |
| --- | --- |
| Local installable distribution | `knowledge-framework`; normalized wheel/dist-info names may use underscores. No public registry-name availability or ownership claim. |
| Import | `knowledge_framework`, at the existing source location; no source-tree move or namespace conversion. |
| Initial Python version | `0.1.0`, independent from PowerShell module `0.14.0`. |
| Interpreter eligibility | `Requires-Python: >=3.14`; initially certify CPython 3.14.5 on the adopted Windows/Linux lanes. Eligibility is not proof of every later interpreter release. |
| Source syntax | Preserve Ruff `py310`. Do not add an older Python runtime lane through this lint setting. |
| Backend | `setuptools.build_meta`, explicit package mapping. Build with the standard `build` frontend; no SCM-version plugin, setup.py execution or automatic root discovery. |
| Exact build-tool versions | Select and pin compatible setuptools/build/pip versions during 3.1.2 acquisition/provenance proof; never float during a build. Backend identity is settled here, acquisition versions are not guessed from installed machine state. |

The single authored version authority will be a dependency-free literal
`Tools/Runtime/Python/knowledge_framework/_version.py`, initially `__version__ = "0.1.0"`.
Use setuptools dynamic version metadata pointing to `knowledge_framework._version.__version__`;
literal extraction must work without runtime imports, PyYAML, Git metadata or a checkout.
Package-root `__version__` may re-export that value without maintaining a second literal.
No static `[project].version`, separately edited version text, or conversion from PS/module/schema
numbers is allowed. Generated wheel/sdist metadata is a derived version record.

Installed version comes from standard-library `importlib.metadata` for `knowledge-framework`.
Verification compares it to the imported package version and records the module origin, interpreter,
install mode, distribution location, artifact SHA-256 and source commit captured by the build owner.
Matching version numbers alone do not prove matching bytes. A source checkout that shadows a
different installed distribution must be labeled source mode or rejected by installed-artifact
verification; global metadata is never presented as provenance for unrelated imported source.
An editable install records its source path and does not satisfy wheel-isolation acceptance.

Use three-part component versions. While below 1.0, incompatible public runtime API/behavior or
support changes increment the minor number; compatible additions also increment minor; corrective
implementation/packaging fixes increment patch. Document compatibility impact for every minor
release. A 1.0 stability commitment requires a separate review. Bump for changed released Python
runtime bytes, dependency/interpreter requirements or package metadata that changes the installed
contract. Do not bump for documentation-only, CI-only or external canonical-content changes.
Implementation work may keep its planned release version until its reviewed checkpoint is accepted;
do not assign a fresh release for every edit or rebuild identical artifacts under one released version.

Python and PowerShell change versions only when their own released component changes. Shared
conformance/parity proves semantic compatibility; an acceptance record identifies the tested pair.
Neither version replaces framework/project/pack schema numbers, report contracts, fixture baselines,
numbered semantic-model evolution or platform phase numbers.

## Artifact And External Data Boundary

Explicitly package only `knowledge_framework` from `Tools/Runtime/Python`, with automatic package
discovery disabled and `include-package-data = false`. The initial code allowlist is these 22
existing files plus the proposed `_version.py`:

```text
__init__.py                 capability_roadmap.py       chronology_config.py
effective_schema.py        entity_config.py             framework_catalog.py
framework_config.py        framework_paths.py           hosting_config.py
interpretation_config.py   lookup_key_config.py         occurrence_config.py
project_config.py          project_paths.py             provenance_config.py
reconciliation_config.py   resource_config.py           schema_pack_config.py
source_config.py           strict_yaml.py               taxonomy_config.py
temporal_config.py         _version.py (new at 3.1.2)
```

Standard generated distribution metadata, RECORD and the unchanged root `LICENSE` are permitted.
The existing license reserves rights; retain its bytes and do not substitute an open-source license
or invent permission metadata. Packaging is local installation proof, not external publication.
Source distributions, if built, contain only those sources and explicit build inputs/legal metadata;
inspect their members as well as the wheel. No repository-wide recursive inclusion, implicit README
content or Git plugin file selection. New runtime files/resources require an explicit allowlist review.

Exclude commands, tests, conformance fixtures/runners, PowerShell runtime, CI assets, all Framework
manifests/packs/data, project configuration/registries, canonical pages/templates/Relationship Seeds,
QA/Visualization projections, books/artwork, generated caches and build/environment directories.
There are no console entry points or package resource files in this initial release.

Installation supplies loader code only. Callers still provide external `Framework/framework.yaml`,
`Project_Config/project.yaml`, selected packs, taxonomy/domain registries and the manifest-selected
Unicode lookup-key data. Unicode semantics come from that explicit data, not the interpreter's
Unicode database. Preserve explicit root, environment, working-directory and executable discovery
order; installation must not search site-packages for LoTM or supply implicit defaults.
Missing external roots/data produce existing actionable failures.

Installed proof runs outside the source tree, sanitizes inherited runtime/root overrides and checks
that imported files belong to the owned fresh environment. A neutral external consumer exercises
manifest/catalog/lookup/composition behavior and existing semantic expectations. Merely importing
the package or launching today's source-bootstrapped suites is insufficient wheel proof. Do not
rewrite all existing suite bootstraps to manufacture installed mode; design the explicit verification
adapter at 3.1.3 and retain source conformance independently.

## Dependency Authority And Build Inputs

| Layer | Membership / authority |
| --- | --- |
| Runtime compatibility metadata | `[project].dependencies`: PyYAML only; propose `PyYAML>=6.0.3,<7`. No runtime dependency on build tools or CI/media tools. |
| Reproducible runtime installation | `requirements-python.txt`: exact adopted PyYAML 6.0.3, constrained to package compatibility metadata. Validate package-name membership and satisfaction of metadata bounds; no independently maintained competing runtime graph. |
| Build | Separate exact build-tool declaration for setuptools, build, pip and required transitive tools evaluated in 3.1.2. Install into the owned build environment before invoking the build; no surprise network acquisition during execution. |
| Implementation/policy tests | Development declaration includes runtime pins plus exact pytest/Ruff and evaluated transitive dependencies; Pester/PS tooling remains its own declaration. |
| Synthetic media | Separate Pillow declaration, installed for required PR media groups; it is not an extra or unconditional dependency of the core wheel. |
| Rendering | Existing Node/Mermaid/Puppeteer ownership; excluded from runtime wheel and portable Python requirements. |

Metadata describes eligible dependency versions; bootstrap pins the specific verified environment.
All changes to bounds or pins require consistency checks and affected consumer proof. No development
extras are added just to make the wheel install repository tooling. The accepted declaration/cache
layout remains in the [runtime budget](ci-testing-runtime-budget.md); 3.1.2 evaluates platform wheel
availability, full transitive pins/hashes and missing/offline/corrupt-cache behavior without inventing
hashes or treating a global package list as a lock.

Root `pyproject.toml` will retain Ruff configuration and gain explicit build/package metadata.
Root `LICENSE` becomes a declared build input. Extraction currently copies pyproject and the two
runtime requirement files but not LICENSE: 3.1.2 must explicitly add LICENSE to its copied-file
allowlist, update copied-file expectations truthfully and prove unchanged nine-suite neutral behavior.
Any build-tool declaration needed to rebuild a source artifact/extracted bundle also needs an
explicit copied-input decision; development/media/CI dependencies remain outside extraction.
Do not silently enlarge the extracted framework or infer a wheel contains that complete bundle.

## Review And Verification Gates

3.1.1 verifies the inventory, consumer/dependency mapping, names, single version authority, interpreter
decision, backend and artifact contract. No package installation or wheel success is claimed here.
3.1.2 implements this reviewed contract, pinned/isolated source/editable/build routes, readiness and
declaration consumers; 3.1.3 inspects actual artifact members and verifies fresh wheel installation,
origin/provenance, missing-data failures and retained semantic behavior without checkout leakage.
Required media PR coverage remains a separate native-group adoption gate.

Rollback of this checkpoint is documentary. Later packaging rollback removes only introduced
metadata/version/install paths through review, preserving existing source commands, external data,
semantic fixtures and the independently accepted PS7 retirement.

## Official References

- [Setuptools package mapping and dynamic literal version metadata](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html).
- [Python packaging metadata and Requires-Python](https://packaging.python.org/en/latest/specifications/pyproject-toml/).
- [Standard-library installed distribution metadata](https://docs.python.org/3/library/importlib.metadata.html).
