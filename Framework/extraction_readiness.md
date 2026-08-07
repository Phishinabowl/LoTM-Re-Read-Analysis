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
- project taxonomy, resources, sources, entities, reconciliation, chronology, occurrence,
  hosted-identity, structural-interpretation, and provenance instances as applicable;
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
- temporal-window semantics; and
- structural interpretations, deferred claim closure, and canonical-graph isolation.

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

The V46 implementation rehearsal on 2026-08-05 copied 217 portable files. Six suites passed with
matching summaries in Python, PowerShell 7, and Windows PowerShell 5.1 under a neutral core-only
consumer; no LoTM configuration was copied, and all nine guarded project surfaces remained absent.
The portable kernel now includes the schema-10 occurrence runtime and core pack version 37, while
the intentionally small extraction smoke profile remains independent of project-specific occurrence
fixtures.

The V47 implementation rehearsal on 2026-08-05 copied 224 portable files with the same six-suite,
three-runtime semantic parity and all guarded project surfaces absent. The portable kernel now
includes hosted-identity schema 1, manifest schema 11, and core pack version 38. Carrier,
occupancy, and hosting-transition semantics remain domain-neutral and do not copy the empty LoTM
hosting registry into the neutral extraction consumer.

The V48 implementation rehearsal on 2026-08-06 again copied 224 portable files. Its six-suite
smoke profile passed with matching summaries in Python, PowerShell 7, and Windows PowerShell 5.1,
and all guarded project surfaces remained absent. The portable hosted-identity service now uses
schema 2 and core pack version 39. Carrier bindings add pack-typed, occurrence-bounded child/parent
topology plus deterministic direct, transitive, and reachable-occupancy queries without adding a
project registry, LoTM vocabulary, or new extraction dependency.

The V49 implementation rehearsal on 2026-08-06 copied 228 portable files after adding four
optional hosting packs. Its six-suite smoke profile passed with matching summaries in Python,
PowerShell 7, and Windows PowerShell 5.1, and all nine guarded project surfaces remained absent.
Core pack version 40 no longer activates hosting or exports hosting vocabulary. The extracted
kernel instead carries a selectable domain-neutral foundation plus narrative, simulation, and
compute vocabulary extensions. A neutral core-only consumer selects none of them and remains
valid, proving that the added files do not add an activation or project dependency.

The V50 pressure-confirmed rehearsal copied 229 portable files and passed its six portable suites
in Python, PowerShell 7, and Windows PowerShell 5.1. Core pack version 41 and the paired chronology
services expose canonical chronology positions through a detached provider inventory without
copying LoTM configuration or allowing callers to remove registry state. All nine guarded project
surfaces remained absent, and the full compatibility profile preserved canonical Visualization and
QA outputs.

Platform Phase 2.3.5 closed effective-schema consumer adoption on 2026-08-07. The isolated
full-release rehearsal copied 236 portable files and passed its six portable suites in Python,
PowerShell 7, and Windows PowerShell 5.1 while excluding all nine guarded project surfaces. QA and
Visualization now consume direct projections from one in-memory effective schema; the temporary
legacy projection and shadow-comparison APIs are absent. The complete 17-suite baseline and all
seven full-release compatibility checks passed, and canonical Visualization and QA outputs remained
unchanged.

## Known Limits And Next Boundaries

Extraction readiness does not close these known items:

- Recurrence, participation identity, participant-relative chronology selection, exact entry-relative
  state boundaries, branch lifecycle, chronology topology, epistemic state, capability state,
  structural interpretations, hosted identity, nested carrier topology, optional hosting-pack
  isolation, and canonical chronology-position provider closure are implemented and pressure-tested
  through V50. The Phase 1 model gate and Phase 2 effective-schema consumer-adoption gate are closed;
  pack presentation and configuration are the next platform implementation boundary.
- Historical continuity-membership transitions, manifestation- or release-scoped continuity,
  occurrence-linked continuity transitions, first-class continuity systems, and sliding-chronology
  policies remain later normalized-content or deferred narrative capability work. They do not weaken
  the current portable-kernel claim or block Phase 2.
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
