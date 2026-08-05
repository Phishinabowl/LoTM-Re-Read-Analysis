# Framework Extraction Readiness

## Status

The reusable framework kernel is ready for an isolated-copy foundation. This means the
contracts, packs, runtime loaders, conformance suites, and dependency declarations can run
without LoTM configuration, canonical content, source material, generated QA output, or
visualization state.

This does **not** mean the complete knowledge-platform product is ready to split into a final
standalone repository. Visualization consolidation, normalized content services, mutation and
migration services, non-narrative domain packs, and the Streamlit interface remain later
architecture stages.

## Proven Portable Bundle

The extraction rehearsal currently allowlists:

- `Framework/`
- `Tools/Runtime/`
- `Tools/Conformance/`
- `pyproject.toml`
- `requirements-python.txt`
- `requirements-powershell.txt`

The rehearsal creates a new operating-system temporary directory, copies only that allowlist,
generates a neutral core-only `Project_Config/project.yaml`, adds disposable empty project
registries, and runs portable conformance inside the copy. The temporary tree is removed when
the check finishes.

The copied `Framework/Packs/` library may contain optional reusable narrative packs. Their
presence does not activate them. A consumer selects packs explicitly, and absent capabilities
remain disabled.

## Project-Owned Boundary

A consuming project owns and must supply:

- `Project_Config/project.yaml` and its selected-pack composition;
- project taxonomy, resources, sources, entities, reconciliation, provenance, chronology, and
  occurrence instances as applicable;
- project extension packs and local controlled vocabulary;
- canonical content, evidence, source material, and promoted assets;
- project graph presets, presentation overrides, and generated-output destinations.

The LoTM repository currently supplies those surfaces through `Project_Config/`,
`Glossary_Threads/`, `Volumes/`, `Source/`, `Artwork/`, `Boards/`, `Investigations/`,
`Visualization/`, and the ignored `Obsidian_Export/`. They are consumers of the framework, not
members of the portable kernel.

## Enforced Exclusions

`Tools/Compatibility/verify_framework_extraction.py` fails if an isolated copy contains any of
these project surfaces:

- `Artwork/`
- `Boards/`
- `Glossary_Threads/`
- `Investigations/`
- `Obsidian_Export/`
- `Source/`
- `Testing/`
- `Visualization/`
- `Volumes/`

It also verifies that the LoTM `Project_Config/` was not copied and that the generated consumer
uses the neutral project ID `extraction-smoke`.

## Verification Contract

Run the isolated rehearsal directly with:

```powershell
python Tools\Compatibility\verify_framework_extraction.py --json
```

Run the complete extraction-readiness compatibility gate with:

```powershell
python Tools\Compatibility\run_compatibility.py --profile full-release --json
```

The permanent rehearsal requires matching structured summaries from Python, PowerShell 7, and
Windows PowerShell 5.1 for:

- project-root discovery;
- strict configuration ingestion;
- Unicode lookup-key normalization;
- schema-pack composition;
- temporal-window semantics.

The complete gate additionally verifies current LoTM Visualization and Obsidian QA consumers,
root-independent command execution, generated-artifact lifecycle safety, and byte-identical
nonblank Mermaid rendering without changing canonical outputs.

## Stabilization Evidence

The Phase 9 extraction-readiness baseline on 2026-08-02 established:

- 14 of 14 baseline conformance suites passed in each of Python, PowerShell 7, and Windows
  PowerShell 5.1 with matching semantic summaries;
- all static policy checks passed, including Actions, Python, PowerShell, and work annotations;
- all six full-release compatibility checks passed;
- the isolated rehearsal copied 202 portable files, copied no project configuration, and
  excluded all nine guarded project surfaces;
- current Visualization output remained 15 nodes and 121 relationships;
- 34 redirected QA artifacts matched across runtimes;
- all 12 root-discovery launch combinations passed;
- all six unsafe artifact destinations were rejected;
- all three renderers produced the same nonblank 298,269-byte SVG with SHA-256
  `11b9e70f735004641ab0bd348c21451d1cc2852327caa58d092dd045dfb59f73`;
- canonical outputs remained unchanged and temporary compatibility output was removed.

The retained pressure portfolio also remained coherent. Layer portability received direct
executable proof from the neutral isolated copy. Work/continuity, media/distribution,
evidence/authority, entity/identity, temporal/topology, and recurrence/state semantics retained
their existing conformance and broad narrative candidate coverage. Synthetic IT/operations,
medical, legal/compliance, investigative, and scientific replays found no new core ownership
leak, but they do not substitute for a future non-narrative pack and IT proof of concept.

## Known Limits And Next Boundaries

Extraction readiness does not close these known items:

- Aggregate recurrence cardinality and occurrence-participation identity are now portable through
  V40; chronology-context topology, branch lifecycle, and participation-relative transition/state
  semantics remain later bounded framework work.
- QA graph construction has not yet been fully migrated into one reusable Visualization engine.
- A normalized content index and generalized bounded-page machinery are not yet complete across
  content types.
- The rehearsal proves a portable kernel copy; it does not yet create or maintain a separate
  framework repository.
- No IT, medical, or legal schema pack is currently provided.
- Persisted page IDs, mutation planning, migrations, category/page editors, and Streamlit remain
  future capabilities.

These are staged capabilities, not extraction-baseline regressions. Future work must keep the
portable kernel free of LoTM vocabulary and paths while proving new consumers through the
cumulative methodology in `Framework/testing_methodology.md`.
