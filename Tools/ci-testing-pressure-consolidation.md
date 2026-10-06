# CI 5.6 Semantic Pressure Coverage Consolidation

**Status:** Locally verified and confirmed by the maintainer on 2026-10-06.
The maintainer approved consolidation into semantic families with preserved question mappings.
The [modernization plan](ci-testing-modernization-plan.md) owns checkpoint closure.

## What Changes And What Remains

The [methodology](../Framework/testing_methodology.md) now has **54 active families**: the same
37 executable/policy/parity families and the existing 17 semantic `PRESSURE-*` families.
The former 17 `SCENARIO-*` IDs remain historical/example references in the
[domain pressure library](../Framework/pressure-scenario-examples.md). Each original question set
is preserved verbatim from `eafcb2a1056fad0220925f10fbb4dbdb856a122e`, with explicit semantic owners.
Earlier 71-family / 34-review records remain dated evidence, not current independent gate counts.

Release readiness now registers **17 blocking reviews**, all with null evidence, instead of 34.
Each semantic review must account for its matrix and all applicable mapped sub-obligations. A
family label or one selected example cannot close missing questions. Pending review still fails
the release outcome; external review-evidence admission remains unimplemented. Ordinary full
verification retains its 74 execution units, 42 conformance obligations and eleven consumer checks.

No executable case, conformance/compatibility suite, fixture, runtime API, source/model contract,
LoTM instance, projection baseline or old runner is removed. This consolidation reduces review
registration and organizes requirements; **no execution-time saving is claimed**. Timing and any
further case reduction belong to 5.7, against the confirmed [5.5 record](ci-testing-acceptance-review.md).

## Ownership And Selection

Semantic requirements are cumulative. Domain collections organize representative applications;
named examples preserve discoveries and evidence context. Narrative/worldbuilding/media is one
collection alongside IT/operations, medical, legal/compliance, investigations and science/research.
These are documentation/selection collections, not new schema packs or runtime storage layouts.

For an affected family, select ordinary, irregular and adversarial cases covering every materially
affected distinction. Compose cases where interaction is the obligation; isolated services cannot
prove composition. Cross-domain pressure retains its required narrative/IT/medical/legal diversity,
with investigation/science examples added when the existing methodology requires them. Rotate
representatives rather than adding an independent mandatory gate for every title. Record the actual
sample, evidence mode, covered questions and unsupported/pending portions. Governed data and exact
real-world/source claims retain their original evidence requirements.

## Supporting Executable Evidence And Unclosed Review Boundaries

The following table links supporting owners and concrete existing fixture surfaces. It is not a
second execution registry. These fixtures were included in the passing 5.5 full profile; no new
story replay or cross-industry project acceptance is inferred from them.

| Semantic family | Supporting existing owner / fixture surface | Required review beyond primitive success |
| --- | --- | --- |
| `PRESSURE-LAYER-PORTABILITY` | installation, schema-pack, project-composition, extraction; [installation fixtures](../Framework/Data/Framework-Installation/), [pack fixtures](../Framework/Data/Schema-Packs/) | Core/pack/project boundaries across selected domains; no LoTM vocabulary leakage or false activation. |
| `PRESSURE-WORK-CONTINUITY` | source, entity, schema-pack; [source expectations](../Framework/Data/Sources/expectations.json) | Derivation, scoped canon/rights independence, optional membership, continuity changes, shared antecedents and distinct work identities. |
| `PRESSURE-MEDIA-DISTRIBUTION` | source, chronology, distribution boundary; [source expectations](../Framework/Data/Sources/expectations.json) | Manifestation/release distinctions, irregular order, segment mappings, reconstruction, localization and continuity applicability without inferred equivalence. |
| `PRESSURE-EVIDENCE-AUTHORITY` | source, provenance, interpretation; [provenance fixtures](../Framework/Data/Provenance/), [interpretation expectations](../Framework/Data/Interpretations/expectations.json) | Scoped authority and indeterminate/conflicting evidence; stewardship, factual truth, creative attribution and legal ownership stay independent. |
| `PRESSURE-RULESET-POLICY` | schema-pack/source/provenance supporting boundaries | A dedicated normative policy/ruleset capability is not supplied by those primitive passes. Preserve the explicit unsupported finding until implemented and proved. |
| `PRESSURE-ENTITY-IDENTITY` | entity, lookup, reconciliation, hosting; [entity expectations](../Framework/Data/Entities/expectations.json), [reconciliation fixtures](../Framework/Data/Reconciliation/) | Counterparts, mantles, clones, composites, recasts, continuity transfer, identity phases and ordinary role/portrayal exclusions remain distinct. |
| `PRESSURE-TEMPORAL-TOPOLOGY` | temporal, chronology, occurrence; [chronology expectations](../Framework/Data/Chronology/expectations.json) | Precedence, causality, recurrence and context topology cannot collapse; scoped sliding/rewritten histories and incomparability need selected composed evidence. |
| `PRESSURE-RECURRENCE-STATE` | occurrence, chronology, provenance; [occurrence expectations](../Framework/Data/Occurrence/expectations.json): iteration occurrences, cardinalities, branch histories and boundary queries | Reset versus termination/exit, distinct occurrences sharing coordinates, partial escape, staggered subjects, source applicability and lifecycle histories. |
| `PRESSURE-EPISTEMIC-STATE` | occurrence, schema-pack, provenance; occurrence transition dimensions and state-at queries | Knowledge/access/memory/belief remain distinct from truth and proficiency; independently situated subjects and altered evidence need composition. |
| `PRESSURE-CAPABILITY-STATE` | occurrence, schema-pack, provenance; occurrence engineering/assessment transitions and bounds | Skill progression cannot be inferred from credentials, authorization, time, attempts, successful actions or retained understanding. |
| `PRESSURE-TEMPORAL-COMPOSITION` | occurrence, chronology, provenance, project composition; occurrence state/participation queries and [composition baseline](../Project_Config/composition-baseline.json) | Positive multi-service composition, restored-state/participation control and at least one non-narrative composition. The canonical LoTM baseline is not that non-narrative proof. |
| `PRESSURE-STRUCTURAL-INTERPRETATION` | interpretation, chronology, provenance; [interpretation expectations](../Framework/Data/Interpretations/expectations.json), [composed registry](../Framework/Data/Interpretations/composed-registry.json) | Competing/incomplete reconstructions retain ambiguity; hypotheses do not become canonical structure or silently select a winner. |
| `PRESSURE-PARTICIPANT-CHRONOLOGY` | occurrence, chronology; occurrence participation/track-entry binding expectations | One occurrence can have distinct applicable personal/world/presentation bindings; backward influence does not move occurrences or create false precedence. |
| `PRESSURE-HOSTED-IDENTITY` | hosting, entity, occurrence, reconciliation; [hosting expectations](../Framework/Data/Hosting/expectations.json) | Copies/divergence, nested carriers, direct/indirect occupancy, control and co-residence require boundary-aware physical/virtual composition. |
| `PRESSURE-CROSS-DOMAIN` | relevant conformance and neutral extraction | Actual selected domain probes remain required; a neutral copied project does not certify medical/legal/IT business semantics. |
| `PRESSURE-ADVERSARIAL` | relevant malformed/query/collision fixtures | Retain change-specific contradictory, ambiguous, empty, cyclic and cross-namespace controls beyond happy paths. |
| `PRESSURE-SCALE` | generated suite scale/limit cases, process budgets | Change-specific deep/wide, memory, termination and throughput evidence remains necessary; current fixture counts are not future performance guarantees. |

The complete 17-row historical scenario mapping and unabridged questions live in the portable library,
not a duplicated rule catalog here. Every original question remains represented even where current
fixtures supply only partial supporting evidence.

## Duplication Dispositions

| Candidate overlap | Shared organization | Retained distinct question / decision |
| --- | --- | --- |
| Derrick and Loki | recurrence, epistemic and temporal composition | Delayed independent awareness/reset-exit controls differ from branch lifecycle, bootstrap causality and knowledge-versus-expertise progression. Consolidate review ownership; remove no fixture. |
| Primer and Memento | structural interpretations and evidence | Unresolved coherent chronology alternatives differ from manipulated memory/belief and presentation order. Preserve both semantic controls. |
| Marvel and DC | continuity, identity, temporal topology and media | Shared-universe counterparts/mantles/composites and rewritten/shared-antecedent histories expose different boundaries. Rotate titles only after covering their mapped distinctions. |
| Reconstruction, textual tradition and serialized adaptation | media, evidence, interpretation and work identity | Missing original witnesses, scholarly alternatives and many-to-one/irregular adaptation mappings are not interchangeable expected outcomes. Preserve requirements without separate franchise gates. |
| Primitive suites and compiled consumers | common supporting data | Loader contracts and integrated/project/output behavior are different boundaries. No conformance/compatibility deduplication is justified by fixture overlap alone. |

## Catalog And Report Safety

Catalog review admission now uses explicit methodology family declarations, not any quoted mention.
A historical scenario alias in prose cannot become an active non-release review. Release readiness
must still include every active semantic family; missing one is rejected. Existing reporting emits
the registered pending family rows (17) without fabricated native test counts or accepted evidence.
Full and feature profile references, deadlines, dependencies, isolation and check identities are unchanged.

Two focused regressions protect the different failure paths: an inactive historical alias in a
non-release profile, and omission of an active semantic family from release readiness. They join
the existing mandatory catalog group. Declared inventory becomes 439 pytest / 49 Pester; mandatory
infrastructure becomes 333, with ci-catalog 70. No new group or production harness is registered.

The portable extraction allowlist already copies the entire `Framework` directory. A private
copy-only rehearsal includes the new library and methodology without changing the allowlist or
runtime code. Its extra documentation file affects copied-file accounting, not semantic suite membership.
This is copy/link proof, not a new full extraction execution.

## Verification And Rollback

Ignored `.tmp/ci-phase56/` retains the original mapping snapshot, textual-preservation audit, focused
tests and plan evidence. The audit verifies 17 original question sets verbatim, 17 known semantic
owners, 54 active families, unchanged ordered 74-unit full membership, all null blocking reviews,
pending-review failure and 309 unchanged protected runtime/fixture/contract/pack/project files.
The 5.5 full proof supplies unchanged domain evidence; focused catalog/scope/aggregate/report/gate
tests cover the actual CI changes. Full timing requalification belongs to 5.7.

Final focused Windows coverage passes 70 catalog cases, 137 scope/core-aggregate cases and 50
report/gate cases (**257 total**). The same complete affected groups pass **257 cases on WSL**.
These are correctness checks, not isolated per-profile latency measurements. No repeated full
domain run is substituted for the unchanged recorded baseline or the required 5.7 timing work.

Ruff lint/format and `git diff --check` pass. Annotation policy passes 22/22 fixtures across 467
files; all 128 checked documentation links resolve. Pending pressure reviews remain unresolved;
the maintainer confirmed this consolidation checkpoint without accepting those domain reviews.

Rollback reverts methodology, example library, release-review registration, catalog admission and
mapping/history updates together. Restore the former 34 independent review entries if consolidation
is rejected. Preserve source questions, missing-capability findings and the untouched executable corpus.
Do not claim a named story replay or accepted release review from organization alone.
