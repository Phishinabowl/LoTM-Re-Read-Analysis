# Knowledge Platform Implementation Plan

This plan coordinates the remaining framework, schema-composition, normalized-content,
Visualization, QA, LoTM migration, analytical-projection, pack-management, and interface work.
It is an execution checklist rather than an architecture contract or historical log.

Use this document together with:

- `ARCHITECTURE.md` for component ownership and dependency boundaries;
- `Framework/framework_improvement_lifecycle.md` for every numbered framework version;
- `Framework/testing_methodology.md` for cumulative verification and pressure testing;
- `Framework/framework_evolution.md` for confirmed implementation and test history;
- `Tools/Compatibility/compatibility.json` for executable consumer-regression coverage; and
- `Tools/CI_implementation_plan.md` for the completed tooling, conformance, CI, and extraction
  foundation on which this plan depends.

## Operating Rules

- Complete phases in dependency order unless this plan explicitly allows parallel work.
- Treat implementation phases and framework versions as separate scales. A phase may contain zero,
  one, or several framework versions; version boundaries are chosen through the improvement
  lifecycle rather than predicted permanently by this roadmap.
- Treat each numbered framework-schema change as a framework version and use the full improvement
  lifecycle, including proposed tests, two-part confirmation, pressure testing, and evolution
  closure.
- Update this checklist as each subphase is confirmed. A checked item means implemented, tested,
  documented, committed, and pushed unless its wording explicitly describes a design decision.
- Add or revise permanent conformance, compatibility, and static-policy coverage as behavior moves
  into shared services. Do not create a second test inventory in this document.
- Keep every declared `planned` capability traceable to an implementation phase, an explicitly
  accepted deferral, or a documented removal decision. Update that mapping whenever pack
  capabilities or roadmap prerequisites change.
- Preserve current LoTM canonical files and generated-output behavior until a phase's equivalence
  gate passes.
- Perform logical migration before physical migration. Existing files may feed a new normalized
  model before their canonical storage layout changes.
- Use previewed migration services for repository-wide physical changes. Do not perform a manual
  big-bang rewrite.
- Keep framework packs, services, and contracts free of LoTM vocabulary and paths.
- Stop at each major phase, and at migration subphases when useful, for maintainer review.

## Completion Definitions

### Logical Migration

Legacy canonical files are parsed into the new effective schema and normalized content model.
Consumers use the new services, but the canonical files may remain byte-for-byte unchanged.

### Physical Migration

Canonical page or registry storage is deliberately rewritten, split, moved, or assigned persisted
identities through a previewed and validated migration operation.

### Consumer Equivalence

For reviewed representative inputs, a migrated consumer preserves all intended information and
either matches the prior output or records an accepted, explained improvement. Output filenames,
artifact ownership, cleanup behavior, reader boundaries, provenance, and cross-runtime semantics
remain protected.

## Phase 0: Completed Foundation

- [x] Establish the reusable core and narrative schema-pack library.
- [x] Separate framework contracts, project configuration, canonical content, resources, and
  generated views.
- [x] Add strict project, pack, taxonomy, resource, source, entity, provenance, chronology,
  reconciliation, and occurrence loaders.
- [x] Establish Python and PowerShell runtime parity for framework-owned contracts.
- [x] Add aggregate conformance, compatibility, static-policy, CI, and extraction-readiness gates.
- [x] Define graph ownership under Visualization and the normalized-content boundary.
- [x] Define the local-first JSON, SQLite, DuckDB/Parquet, and optional Databricks/Delta analytical
  projection direction.
- [x] Retain current Visualization and Obsidian QA behavior as compatibility-protected consumers.

## Phase 1: Temporal And Recurrence Model Stabilization

V38 is the fixed entry point to this phase, not its completion condition. Later version numbers and
scope divisions are provisional: each preceding pressure test may split, combine, reorder, or add
work through the normal framework improvement lifecycle. Phase 2 must not begin merely because an
earlier stabilization gate passed. It begins only after the retained Loki and Derrick scenarios plus
the later Primer, Arrival, Memento, Doctor Who, and Westworld probes have been implemented or
explicitly reviewed and deferred at the expanded stabilization gate.

### Phase 1.1 V38 Definition

- [x] Re-enter framework improvement mode through the lifecycle document.
- [x] Recover the confirmed V37 implementation and testing state.
- [x] Define V38 around typed effect semantics and fail-closed execution.
- [x] Include the two retained V37 declaration defects and conflict-wide execution behavior.
- [x] Select required conformance, parity, compatibility, and pressure-test coverage before editing.

### Phase 1.2 V38 Implementation And Closure

- [x] Implement V38 across contracts, packs, Python, PowerShell, fixtures, and documentation.
- [x] Complete the two-part implementation confirmation with the implementation commit recorded in
  `framework_evolution.md`.
- [x] Run the cumulative V38 pressure test under `Framework/testing_methodology.md`.
- [x] Record findings, update durable methodology where needed, confirm, and push the testing record.
- [x] Verify the LoTM Visualization and QA compatibility baseline remains green.

### Phase 1.3 Aggregate And Uncertain Recurrence Cardinality

- [x] Define a bounded framework version after V38 for exact, minimum, maximum, ranged, unknown,
  and aggregate recurrence cardinality.
- [x] Represent large or source-unspecified repetition counts without inventing concrete iterations.
- [x] Permit representative concrete iterations to coexist with an aggregate execution history.
- [x] Preserve evidence, certainty, and reader/source applicability for every cardinality assertion.
- [x] Prove Loki's centuries of Loom attempts without asserting an unsupported exact total.
- [x] Replay retry, recurring medical episode, scheduled legal obligation, and scientific-trial
  scenarios so the capability remains domain-neutral.
- [x] Complete the version's lifecycle, confirmation, pressure test, and evolution closure.

### Phase 1.4 Participation Identity And Revisited Occurrences

- [x] Define a bounded framework version that separates occurrence identity, participation identity,
  and subjective-track entry identity.
- [x] Permit one subject to participate in or encounter one concrete occurrence more than once
  without duplicating that occurrence.
- [x] Preserve role, perspective, participation status, chronology context, and subjective ordering per
  participation.
- [x] Model Loki's self-pruning occurrence once while retaining his earlier recipient participation
  and later agent participation.
- [x] Test repeated observation, review, intervention, retry inspection, and cross-domain
  participation cases.
- [x] Complete the version's lifecycle, confirmation, pressure test, and evolution closure.

### Phase 1.5 Chronology-Context Topology

- [x] Define a bounded framework version for typed relations among chronology contexts without
  turning those relations into chronological precedence.
- [x] Model relations such as outside, observes, oversees, intervenes-in, projects-into, and
  receives-from through pack-owned vocabulary and validated typed targets.
- [x] Preserve incomparability between chronology coordinates unless an explicit mapping relates
  them.
- [x] Connect interventions to concrete occurrences, branches, and applicability scopes without
  claiming that extratemporal means unordered.
- [x] Prove TVA-local order, timeline oversight, and branch intervention while retaining ordinary
  chronology cycle rejection.
- [x] Replay distributed-system control planes, simulations, archival observation, and other
  non-narrative context-topology cases.
- [x] Complete the version's lifecycle, confirmation, pressure test, and evolution closure.

### Phase 1.6 Timeline-Branch Lifecycle

- [x] Define a bounded framework version for branch identity and state history.
- [x] Support pack-owned branch states such as emerging, active, pruned, transferred, restored,
  merged, preserved, and inactive without assuming every domain uses every state.
- [x] Represent pruning or deactivation as a provenance-backed transition rather than deletion.
- [x] Preserve branch lineage, continuity membership, applicability, and state at a requested
  boundary.
- [x] Model Loki's branching timelines, TVA pruning, restoration/preservation, and final replacement
  structure without collapsing branches into one chronology.
- [x] Replay source-control branches, environment promotion, alternate histories, and scientific
  experiment branches.
- [x] Complete the version's lifecycle, confirmation, pressure test, and evolution closure.

### Phase 1.7 V43 Epistemic State Progression

- [x] Decide that epistemic acquisition and practiced capability reuse one structural
  subject-state transition spine but require separate bounded versions and semantics.
- [x] Define core typed state profiles and pack-owned state-kind mappings that declare which
  availability, completeness, and attitude dimensions each state kind uses.
- [x] Distinguish knowledge, memory, awareness, belief, and non-epistemic physical state without
  treating a subject's state as objective truth.
- [x] Give completeness explicit prior and resulting values, and separate discrete or gradual
  change shape from direct, external, conditional, inferred, merged, synchronized, dream,
  prophecy, revelation, and timeline-reconciliation mechanisms.
- [x] Preserve acquisition, retention, loss, restoration, invalidation, contradiction, source
  evidence, and applicability without inferring them from chronology or occurrence participation.
- [x] Model Loki's progressively completed and retained engineering understanding across Loom
  attempts without labeling it proficiency or quantified expertise.
- [x] Replay Derrick and Colin as independent state controls plus education, incident diagnosis,
  clinical understanding, investigative inference, and scientific learning scenarios.
- [x] Complete V43 implementation confirmation, pressure testing, evolution recording, and plan
  closure.

### Phase 1.8 V44 Capability And Proficiency Progression

- [x] Define capability-state profiles for skill, proficiency, competence, and expertise without
  reusing epistemic access or belief semantics.
- [x] Represent qualitative levels and explicitly bounded quantitative measures without inventing
  unsupported precision or a universal competence scale.
- [x] Support practice-based, continuous, sudden, externally supplied, transferred, and conditional
  capability changes while keeping mechanism separate from progression shape.
- [x] Preserve improvement, retention, degradation, loss, restoration, and transfer as explicit
  provenance-backed transitions rather than inference from elapsed time or attempt counts.
- [x] Keep credentials, qualifications, licenses, authorization, and assessment evidence distinct
  from demonstrated or asserted competence.
- [x] Model Loki's retained and accumulated engineering expertise across Loom attempts using the
  V43 epistemic foundation without collapsing understanding into skill.
- [x] Replay education and credential acquisition, incident-response skill, clinical competence,
  investigative ability, and scientific practice scenarios.
- [x] Complete V44 implementation confirmation, pressure testing, evolution recording, and plan
  closure.

### Phase 1.9 Temporal Stabilization Pressure Test

- [x] Replay the complete source-grounded Loki scenario across both seasons.
- [x] Replay the source-grounded Derrick abandoned-temple loop.
- [x] Exercise aggregate attempts, repeated participation, extratemporal context topology, branch
  lifecycle, retained state, and expertise progression together rather than only in isolation.
- [x] Run the complete cumulative conformance, three-runtime parity, project compatibility, and
  retained cross-industry pressure portfolio.
- [x] Confirm that chronology remains acyclic while causal, recurrence, participation, and context
  topology use their own typed relations.
- [x] Record every remaining limitation as supported, explicitly deferred, or outside the intended
  framework boundary.
- [x] Update the testing methodology and candidate catalog when this phase discovers durable new
  test obligations.
- [x] Confirm and push the final stabilization test record.

Phase 1.9 closed the known V39-V44 temporal gaps. Subsequent deliberate-ambiguity,
participant-relative chronology, and hosted-identity probes exposed three additional reusable
capability boundaries. The following phases reopen Phase 1 without rewriting that earlier result.

### Phase 1.10 V45 Competing Structural Interpretations

- [x] Define stable hypothesis or interpretation identity without treating an interpretation as a
  continuity, branch, source, authority rule, or canonical fact.
- [x] Permit named candidate structures to reference existing occurrences, chronology positions,
  relations, branches, entities, and claims without duplicating those records.
- [x] Represent compatible, competing, and mutually exclusive interpretations while preserving an
  unresolved result when evidence does not justify one winner.
- [x] Keep evidence, source priority, authority, supersession, and applicability in provenance rather
  than allowing interpretation membership to establish truth.
- [x] Query one interpretation's internally coherent structure without injecting its ordering edges
  into canonical chronology or weakening ordinary chronology-cycle rejection.
- [x] Replay Primer's deliberately unresolved chronology, Memento's competing reconstructions, and
  the textual-tradition scenario's competing editorial or scholarly structures, then pressure-test
  IT incident hypotheses, medical differential diagnoses, legal case theories, investigative
  reconstructions, and scientific causal models.
- [x] Complete V45 implementation confirmation, pressure testing, evolution recording, and plan
  closure through the normal framework lifecycle.

### Phase 1.11 V46 Participation Chronology Bindings

- [x] Define the smallest stable many-to-many binding between an occurrence participation or track
  entry and the occurrence chronology bindings that apply to that involvement.
- [x] Permit one participation to belong to multiple chronology systems without duplicating the
  occurrence, participation, or subject.
- [x] Preserve participant-specific personal order, world order, presentation order, and other
  temporal axes without applying every occurrence binding indiscriminately to every participant.
- [x] Retain coordinate incomparability unless ordinary chronology mappings or relations establish
  comparison; participation bindings must never become precedence edges.
- [x] Review and close the participation-relative state-boundary gap for repeated visits to one
  occurrence, using a track-entry boundary when occurrence-relative lookup is ambiguous.
- [x] Replay Doctor Who's Doctor/River meetings and multi-Doctor encounters, retain Arrival's
  backward-causal knowledge as a regression control, and pressure-test distributed event,
  processing, ingestion, business, and observer clocks.
- [x] Complete V46 implementation confirmation, pressure testing, evolution recording, and plan
  closure through the normal framework lifecycle.

### Phase 1.12 V47 Hosted Identity And Embodiment

- [x] Separate a stable identity-bearing subject from the physical or virtual carrier, body,
  control unit, avatar, or runtime that hosts it.
- [x] Define provenance-addressable occupancy and control records with explicit activation and
  termination boundaries plus pack-owned roles such as active, dormant, co-resident, or controlling.
- [x] Permit multiple identities or personas to occupy one carrier and one identity to move or copy
  across carriers without silently asserting identity continuity, equivalence, or replacement.
- [x] Reuse entity incarnation, identity phase, cloning, derivation, reconciliation, occurrence, and
  state services instead of duplicating their ownership inside the hosting contract.
- [x] Preserve carrier lifecycle independently from hosted-identity lifecycle and make current
  occupant/controller queries deterministic at an explicit boundary.
- [x] Replay Westworld's Dolores/Wyatt states, pearls, Host bodies, copied Dolores identities, and
  divergence; retain the continuity/identity scenario as a regression against collapsing hosting
  into incarnation or counterpart identity; then pressure-test software processes and containers,
  agents and runtimes, avatars, simulations, and carefully bounded medical identity/carrier cases.
- [x] Complete V47 implementation confirmation, pressure testing, evolution recording, and plan
  closure through the normal framework lifecycle.

### Phase 1.13 V48 Nested Carrier Topology

- [x] Define provenance-addressable carrier-to-carrier bindings without treating either carrier as
  the identity that occupies or controls it.
- [x] Support pack-owned binding kinds for physical installation/containment and virtual execution
  or projection while keeping domain-facing labels outside core.
- [x] Give each binding explicit activation and optional termination boundaries while preserving
  independent child-carrier, parent-carrier, and identity-occupancy lifecycles.
- [x] Reject self-bindings, cycles, duplicate semantic bindings, unknown carriers, invalid
  boundaries, and attempts to infer identity continuity or direct occupancy from a carrier chain.
- [x] Expose deterministic direct and transitive carrier-chain queries that preserve the distinction
  between direct occupancy and an identity reachable through an installed or hosted child carrier.
- [x] Model a pearl or control unit moving between Host bodies without falsely moving or copying the
  identity stored in that control unit; preserve explicit identity copy/divergence separately.
- [x] Replay Westworld, process/container/VM stacks, agents in runtimes, avatars projected through
  simulation hosts, and carefully bounded device/body examples.
- [x] Add paired Python/PowerShell fixtures, malformed/adversarial vectors, provenance and
  reconciliation closure, scale pressure, project composition, extraction, and compatibility gates.
- [x] Complete V48 implementation confirmation, pressure testing, evolution recording, and plan
  closure through the normal framework lifecycle.

### Phase 1.14 V49 Hosting Pack Boundary Reconciliation

- [x] Inventory every hosting capability, controlled-value namespace, semantic declaration, and
  provider registration currently supplied by core; classify each as universal structure,
  domain-neutral optional capability, or domain-facing vocabulary.
- [x] Keep carrier, binding, occupancy, transition, lifecycle-boundary, provenance, reconciliation,
  and query mechanics in the reusable framework without requiring unrelated projects to activate
  hosted-identity behavior.
- [x] Define the minimal core-owned hosting vocabulary, if any, and relocate narrative/simulation
  terms such as bodies, control units, avatars, vessels, and projection into an appropriate optional
  pack rather than exposing them to every industry.
- [x] Relocate compute-facing terms such as runtimes, containers, virtual hosts, and execution into
  an optional reusable pack that an IT project may select without inheriting narrative vocabulary.
- [x] Leave medical, legal, and other industry-specific carrier terms absent until their own packs
  deliberately define them; an absent pack must disable its vocabulary without producing unrelated
  project errors.
- [x] Decide whether `hosted-identity-embodiment` itself remains a core capability, becomes a
  domain-neutral optional capability pack, or is split into a core service plus opt-in activation;
  record the ownership and dependency rule explicitly.
- [x] Update the LoTM pack selection only for capabilities and vocabulary the project actually uses,
  preserving its empty canonical hosting registry until LoTM records are intentionally authored.
- [x] Add paired composition fixtures proving core-only, narrative-only, compute-only, combined, and
  absent-hosting projects receive exactly their selected vocabulary with no cross-pack leakage.
- [x] Re-run hosted identity, pack composition, project composition, provenance closure, isolated
  extraction, three-runtime parity, malformed/adversarial, and cross-domain pressure through the
  normal framework-version lifecycle.
- [x] Complete V49 implementation confirmation, pressure testing, evolution recording, and plan
  closure before beginning the expanded stabilization replay.

### Phase 1.15 Expanded Stabilization Pressure Test

- [x] Replay the complete retained Loki and Derrick scenarios with V39-V49 active together.
- [x] Replay Primer, Arrival, Memento, Doctor Who, and Westworld through their stable scenario IDs.
- [x] Replay the retained parody/derivation, continuity/identity, serialized-adaptation, and
  textual-tradition scenarios so the expanded temporal work remains compatible with the earlier
  narrative architecture it builds upon.
- [x] Exercise competing structures, backward causal knowledge, unreliable memory, multi-context
  participation, hosted identity, aggregate recurrence, branch lifecycle, and state progression in
  composed rather than isolated probes.
- [x] Run the complete cumulative conformance baseline in all three runtimes, full-release project
  compatibility, static policy, retained cross-industry matrices, adversarial cases, and scale tests.
- [x] Confirm that canonical chronology remains acyclic and that hypotheses, causality,
  participation bindings, identity hosting, recurrence, and context topology retain separate typed
  ownership.
- [x] Perform a pack-boundary audit across every selected and bundled pack before Phase 2. For each
  pack, distinguish reusable mechanics, domain vocabulary, bridge vocabulary, project instances,
  and presentation-only recommendations; verify that unselected families remain absent.
- [x] Review `narrative-preservation`, `narrative-production`, `narrative-distribution`,
  `narrative-interactive`, and `narrative-shared-universe` as extraction candidates. Decide whether
  each remains domain-owned, requires a narrowly scoped reusable foundation and bridge pack, or is
  explicitly deferred pending a second real consumer. Similar terminology alone is not sufficient
  evidence for extraction.
- [x] Record every pack-boundary decision in framework evolution as retained ownership, accepted
  extraction, or explicit deferral, including the cross-domain invariant that justified any
  promotion. Add another framework version only for a concrete executable boundary change.
- [x] Record every remaining limitation as supported, explicitly deferred, or outside the intended
  framework boundary and update the durable methodology when new obligations emerge.
- [x] Decide whether another narrowly scoped framework version is required or Phase 2 may begin.
- [x] Confirm and push the expanded stabilization test record.

### Phase 1.16 V50 Chronology-Position Provider Closure

- [x] Define V50 as a bounded provider-closure correction, not a chronology-schema expansion.
- [x] Register `chronology-position` as a core provenance subject type.
- [x] Expose canonical chronology positions through the Python and PowerShell chronology provider
  surfaces without exposing unrelated coordinate-system, era, span, relation, or mapping records.
- [x] Replace the composed fixture's temporary chronology-context member with a real
  chronology-position member and prove interpretation resolution through the actual provider.
- [x] Add direct chronology and provenance positive/negative coverage for chronology-position lookup,
  assertion dispatch, provider uniqueness, and unknown IDs in both runtimes.
- [x] Update project-composition expectations, core/pack versions, contracts, extraction readiness,
  and framework evolution without changing the chronology registry's persisted schema.
- [x] Run focused chronology, interpretation, provenance, hosting, schema-pack, and project-composition
  suites in Python, PowerShell 7, and Windows PowerShell 5.1.
- [x] Run the complete three-runtime baseline, full-release compatibility, static policy, retained
  structural-interpretation and cross-domain scenarios, adversarial cases, and scale tests.
- [x] Complete the normal two-part V50 implementation and pressure-test confirmation sequence.
- [x] Re-run the expanded stabilization decision and either close the Phase 1 exit gate or record a
  newly evidenced blocker.

### Phase 1 Exit Gate

- [x] No known V37/V38 semantic defect blocks higher-level schema composition.
- [x] Uncertain/aggregate recurrence cardinality is supported or explicitly deferred.
- [x] Repeated participation in one concrete occurrence is supported or explicitly deferred.
- [x] Typed extratemporal chronology-context relations are supported or explicitly deferred.
- [x] Timeline-branch lifecycle is supported or explicitly deferred.
- [x] Knowledge and expertise progression is supported at the agreed boundary or explicitly
  separated into a later capability with maintainer approval.
- [x] The retained Loki and Derrick scenarios pass without invented chronology cycles, occurrence
  duplication, unsupported precision, or silent state transfer.
- [x] Competing structural interpretations are preserved without contaminating canonical chronology.
- [x] One participation can bind to every applicable chronology system without duplication or
  participant ambiguity.
- [x] Hosted identities, carriers, co-occupancy, transfer, copying, and divergence have explicit
  ownership without overloading incarnations or identity phases, and hosting vocabulary remains
  isolated to selected packs rather than bleeding across industries.
- [x] Primer, Arrival, Memento, Doctor Who, and Westworld pass their retained scenario questions.
- [x] Parody/derivation, continuity/identity, serialized adaptation, and textual tradition pass their
  retained scenario questions without weakening their earlier ownership boundaries.
- [x] Framework evolution identifies the accepted next version or Phase 2 handoff after the expanded
  stabilization gate.

## Phase 2: Effective Project Schema Service

### Phase 2.1 Effective-Schema Contract

- [x] Define one domain-neutral `EffectiveProjectSchema` contract.
- [x] Include project identity and schema versions.
- [x] Include selected packs, dependency order, lifecycle, versions, labels, and descriptions.
- [x] Include declared, available, deprecated, planned, enabled, and disabled capabilities.
- [x] Include capability providers and dependency/conflict diagnostics.
- [x] Include composed controlled-value namespaces, definitions, broader-value relationships, and
  owning packs.
- [x] Include current content types, categories, placements, templates, graph/QA eligibility, and
  resource integration where relevant.
- [x] Define deterministic ordering and a stable JSON serialization contract.
- [x] Keep the exported schema generated and diagnostic rather than canonical.

### Phase 2.2 Runtime And Command Surface

- [x] Implement matching effective-schema composition in Python and PowerShell where parity applies.
- [x] Add a headless inspection/export command with human-readable and JSON output.
- [x] Ensure library consumers import the service rather than shelling out to the command.
- [x] Add positive, disabled, planned, deprecated, dependency, ambiguity, malformed, and scale tests.
- [x] Register new permanent coverage in the aggregate conformance inventory.
- [x] Document the API, command, output schema, and compatibility rules.

### Phase 2.3 Initial Consumer Adoption

- [ ] Make QA discover enabled content roots, content types, categories, labels, and eligibility from
  the effective schema.
- [ ] Make Visualization discover graph classes and enabled projection capabilities from the
  effective schema where current configuration permits.
- [ ] Remove replaced consumer-local category and capability allowlists.
- [ ] Preserve current page parsing and graph construction until later phases replace them.

### Phase 2 Exit Gate

- [ ] QA, Visualization, CLI, and future UI code can inspect one identical effective schema.
- [ ] Existing LoTM outputs remain compatibility-equivalent.

## Phase 3: Pack Presentation And Configuration Model

### Phase 3.1 Pack Presentation Metadata

- [ ] Define structured short and long descriptions, intended audience, use cases, examples,
  prerequisites, provided behavior, exclusions, maturity, documentation links, search keywords,
  and optional visual identifiers.
- [ ] Define machine-readable pack classification independently from the existing validation-facing
  `pack_kind`. Include an extensible `family` such as `hosting`, `narrative`, or `preservation`; an
  architectural `role` such as `foundation`, `domain`, `bridge`, or `extension`; and a `scope` such
  as `domain-neutral`, `cross-domain`, or `domain-specific`.
- [ ] Define validation and composition rules for family, role, and scope without assuming that a
  name prefix proves ownership. A bridge must declare all foundations it joins, and a
  domain-neutral pack must not export domain-facing vocabulary.
- [ ] Require friendly labels and useful descriptions for every user-selectable pack and capability.
- [ ] Backfill string-shorthand capabilities that need user-facing metadata.
- [ ] Keep presentation metadata localizable and independent of UI layout code.
- [ ] Define a stable human-facing inspection model for singular pack and capability lookup without
  making CLI layout part of the effective-schema contract.
- [ ] Add ambiguity-safe `--pack PACK_ID` / `-Pack PACK_ID` and
  `--capability CAPABILITY_ID` / `-Capability CAPABILITY_ID` command selectors after the required
  presentation metadata exists.

### Phase 3.2 Capability Grouping

- [ ] Define stable capability groups suitable for wizard steps and editor navigation.
- [ ] Allow packs to contribute capabilities to ordered groups without duplicating capability
  ownership.
- [ ] Represent dependencies, recommendations, conflicts, and planned-only features clearly.
- [ ] Distinguish installed, selected, available, enabled, deprecated, and used-by-project states.
- [ ] Add effective-schema output for groups, presentation metadata, family, architectural role,
  scope, dependency explanations, and bridge relationships.
- [ ] Let headless inspection filter capabilities by group, provider pack, lifecycle, availability,
  activation, and project usage while preserving deterministic result order.
- [ ] Make singular pack/capability inspection explain dependencies, providers, recommendations,
  conflicts, unavailable reasons, and relevant controlled-value contributions.

### Phase 3.3 Plugin And Entitlement Boundary

- [ ] Treat declarative schema packs as versioned plugins without granting arbitrary code execution.
- [ ] Define a separate trusted extension boundary for any future executable plugin.
- [ ] Keep commercial entitlement/licensing outside portable pack semantics.
- [ ] Allow an entitlement service to control discoverability or installation without changing pack
  composition rules.

### Phase 3.4 Planned-Capability Lifecycle And Traceability

- [ ] Make the effective schema expose every declared planned capability with its owning pack,
  dependencies, lifecycle, description, and unavailable reason.
- [ ] Define promotion criteria from `planned` to `available`, including an executable contract,
  matching runtime support where parity applies, permanent positive/malformed/scale coverage,
  documentation, extraction review, and compatibility impact analysis.
- [ ] Require each planned capability to map to a concrete implementation phase or an explicitly
  accepted deferral; reject silent lifecycle drift between pack declarations and this roadmap.
- [ ] Distinguish platform prerequisites from domain-capability delivery so a deferred narrative
  feature does not block unrelated framework, IT, or interface work.
- [ ] Require roadmap, pack metadata, testing methodology, and framework evolution to be updated
  together when a capability is introduced, promoted, deprecated, removed, or materially reshaped.

### Phase 3 Exit Gate

- [ ] A headless client can present packs and capabilities coherently without reading README prose.
- [ ] A headless client can explain whether a pack is a foundation, domain pack, bridge, or
  extension; which family and scope it belongs to; why it was selected; and which vocabulary would
  appear or disappear if its selection changed.
- [ ] Human and JSON clients can inspect one pack or capability by stable ID and navigate its groups,
  dependencies, providers, lifecycle, activation, recommendations, conflicts, and contributions.
- [ ] Every declared planned capability is machine-discoverable and traceable to a delivery phase or
  accepted deferral.
- [ ] No licensing assumption leaks into reusable schema contracts.

## Phase 4: Page Modules, Fields, Defaults, And Validation Levels

### Phase 4.1 Page-Schema Contract

- [ ] Define reusable page modules independently from page instances and Markdown templates.
- [ ] Define field identity, type, cardinality, labels, help text, controlled-value source,
  applicability, ordering, and display hints.
- [ ] Compose modules through core contracts, domain packs, project profiles, content types,
  categories, and project extensions.
- [ ] Prevent page files from copying module or field definitions.
- [ ] Define deterministic composition and conflict behavior.

### Phase 4.2 Requirement Semantics

- [ ] Support `required`, `conditional`, `recommended`, `optional`, `omit-if-empty`, and `derived`
  semantics.
- [ ] Define conditional requirements against enabled capabilities, record lifecycle, other field
  values, and requested readiness level.
- [ ] Define readiness levels such as draft-valid, graph-ready, publishable, and evidence-complete.
- [ ] Ensure incomplete optional release, territory, localization, or evidence details do not block a
  useful draft record.

### Phase 4.3 Defaults And Inference

- [ ] Distinguish literal defaults, inherited context, definitional implications, suggested defaults,
  and computed derivations.
- [ ] Record value origin where persistence or explanation requires it.
- [ ] Permit overrides only where the owning rule declares them valid.
- [ ] Treat source-backed facts such as exact release dates and production details as evidence, not
  silent inference.
- [ ] Prove a Donghua example in which cultural form implies animation while optional release data
  remains absent and production assertions remain explicit.

### Phase 4.4 Template And Editor Schema

- [ ] Generate or validate templates from composed page modules without inserting empty optional
  sections into canonical pages.
- [ ] Expose form-ready schemas through `EffectiveProjectSchema`.
- [ ] Preserve human-authored prose fields separately from taxonomy/display-label conversion.

### Phase 4 Exit Gate

- [ ] A page editor can know what to require, suggest, derive, hide, and omit without hardcoded
  category forms.
- [ ] Existing LoTM templates can be described without forcing all optional modules onto every page.

## Phase 5: Normalized Content And Legacy Compatibility

### Phase 5.1 Normalized Record Contract

- [ ] Finalize normalized identities for pages and non-page content records.
- [ ] Include content type, optional category, canonical location, title, metadata, structured
  modules, relationships, evidence links, visibility, and diagnostics.
- [ ] Define normalized relationship identity, endpoints, type, state history, provenance,
  applicability, and projection metadata.
- [ ] Preserve typed targets below whole-work scope, including segments, content groups,
  manifestations, release objects, continuity memberships, and occurrences, without promoting a
  cut, release, event, or assertion into the wrong identity class.
- [ ] Require an explicit identity decision for paired editions, sibling game versions, rebuilt
  releases, and mechanically equivalent creative variants so similarity does not silently collapse
  distinct works or inflate one work into several manifestations.
- [ ] Permit one resource or source artifact to fulfill several typed semantic roles while retaining
  one resource identity and independent role-specific relationships.
- [ ] Keep normalized records independent of Markdown/YAML physical layout.

### Phase 5.2 Legacy LoTM Adapter

- [ ] Parse current Markdown metadata, embedded structured data blocks, Relationship Seeds, and
  relevant timeline/knowledge records.
- [ ] Derive temporary stable IDs deterministically where persisted IDs do not yet exist.
- [ ] Record every compatibility-derived value and unresolved ambiguity.
- [ ] Preserve legacy source locations for migration reports and diagnostics.
- [ ] Avoid changing canonical LoTM pages during logical migration.

### Phase 5.3 Content Index

- [ ] Build one project-wide normalized content index.
- [ ] Detect duplicate identities, paths, slugs, unresolved endpoints, invalid projection sources,
  schema/module violations, and unsupported legacy constructs.
- [ ] Expose typed query services for consumers.
- [ ] Add JSON snapshots suitable for compatibility comparison without making them canonical.

### Phase 5 Exit Gate

- [ ] Current LoTM content can be represented without information loss.
- [ ] QA and Visualization no longer need to scan Markdown independently once migrated.

## Phase 6: Relationship Ownership And Projection Contract

### Phase 6.1 Canonical Relationship Model

- [ ] Make normalized structured relationships own facts, timing, confidence/state progression,
  provenance, applicability, and stable identity.
- [ ] Define universal relationship fields plus pack/category-specific extensions.
- [ ] Represent continuity and incarnation membership as provenance-backed state history so entry,
  departure, transfer, restoration, ambiguity, and supersession remain queryable at a boundary.
- [ ] Permit applicability and continuity assertions to target manifestations and release objects
  when alternate cuts or editions have different continuity treatment, without requiring them to
  become separate creative works.
- [ ] Allow a continuity transition relationship to reference the occurrence that activates or
  causes it while keeping the in-world occurrence, branch lifecycle, publication decision, and
  continuity relationship as distinct records.
- [ ] Define typed correspondence among release or performance events, diegetic occurrences,
  participant narrative instances, evidence recordings, replays, and reenactments without merging
  their identities or chronology systems.
- [ ] Preserve conflicting and lower-priority evidence rather than overwriting it.
- [ ] Define inverse normalization, deduplication, supersession, and ambiguity behavior.

### Phase 6.2 Thin Projection Declarations

- [ ] Define graph projection declarations that reference canonical relationship IDs.
- [ ] Limit declarations to graph relevance, projection scope, presentation override, and explicitly
  provisional behavior.
- [ ] Preserve pending-page, semantic-hub, anonymous, and local-context use cases.
- [ ] Prevent projection declarations from becoming a second factual history.

### Phase 6.3 Legacy Seed Translation

- [ ] Translate existing Relationship Seeds and `projection_source` references into normalized
  relationships plus projection declarations.
- [ ] Report duplicate, conflicting, orphaned, or unresolvable translations.
- [ ] Retain full QA provenance during translation.
- [ ] Defer physical seed removal until category migrations are confirmed.

### Phase 6 Exit Gate

- [ ] One normalized relationship contract can explain every current QA relationship.
- [ ] No consumer needs to choose independently between seed facts and data-block facts.
- [ ] Marvel/DC acceptance probes can explain continuity transfers, history-changing occurrences,
  and cut-specific continuity claims without overwriting prior states or collapsing record types.

## Phase 7: Visualization Consolidation

### Phase 7.1 Reusable Graph Engine

- [ ] Make Visualization consume effective-schema and normalized-content services.
- [ ] Centralize node eligibility, labels, styles, pending/stub behavior, boundary evaluation,
  relationship deduplication, progression display, and projection filtering.
- [ ] Keep presets, output destinations, and rendering separate from semantic graph construction.
- [ ] Add subject, hop-depth, category, sequence, source, work, and reader-boundary filtering hooks.

### Phase 7.2 Existing Graph Migration

- [ ] Migrate canonical repository graph presets.
- [ ] Migrate the unbounded Visualization relationship graph used by QA.
- [ ] Migrate direct-edge QA relationship graphs.
- [ ] Migrate intermediary relationship-node QA graphs.
- [ ] Preserve timing-bounded graph behavior and pending-node visibility.

### Phase 7 Exit Gate

- [ ] Visualization is the sole owner of all Mermaid graph semantics and generation.
- [ ] Canonical and redirected graph compatibility checks pass across supported runtimes.

## Phase 8: QA Exporter And Bounded Projection Migration

### Phase 8.1 QA Service Boundaries

- [ ] Make QA consume effective schema for content discovery and presentation metadata.
- [ ] Make QA consume the normalized content index for pages, data, relationships, and visibility.
- [ ] Make QA request every graph from Visualization rather than constructing Mermaid directly.
- [ ] Retain QA ownership of mirrors, anomaly reports, inventories, bounded-page requests, and
  maintainer-focused provenance presentation.

### Phase 8.2 Bounded Pages

- [ ] Generalize bounded-page machinery beyond character-specific parsing.
- [ ] Drive bounded sections and tables from composed page modules.
- [ ] Preserve anonymous, hidden, and canonical first-appearance behavior.
- [ ] Preserve medium-specific availability and reader-boundary selection.
- [ ] Keep generated prose extraction honest; do not synthesize unsupported narrative prose.

### Phase 8.3 Full-Binding And Artifact Lifecycle

- [ ] Re-evaluate the planned full-binding option against completed page-schema coverage.
- [ ] Generate all eligible bounded pages only when explicitly requested.
- [ ] Preserve stale-output cleanup, run-scoped temporary ownership, and unrelated-file safety.
- [ ] Keep generated bounded folders absent when no matching request is made.

### Phase 8 Exit Gate

- [ ] QA contains no independent graph semantics or category-specific schema duplication.
- [ ] Python, PowerShell 7, and Windows PowerShell 5.1 retain required consumer parity.

## Phase 9: LoTM Compatibility Freeze Before Physical Migration

### Phase 9.1 Representative Regression Portfolio

- [ ] Preserve the current canonical repository graphs and their semantic snapshots.
- [ ] Preserve all Obsidian mirror notes, indexes, QA reports, and graph variants.
- [ ] Preserve bounded graph and bounded-page requests at representative early, middle, and late
  reader positions.
- [ ] Retain Dunn Smith's anonymous-to-canonical reveal and Sleepless confidence progression.
- [ ] Retain Leonard Mitchell's later reveals and optional Tarot Card module behavior.
- [ ] Retain pending/provisional nodes, source-vs-seed provenance, orphan reporting, and stale-output
  cleanup.

### Phase 9.2 Equivalence Review

- [ ] Compare old and new normalized records and generated artifacts.
- [ ] Classify every difference as equivalent formatting, accepted improvement, fixed defect, or
  regression.
- [ ] Add permanent vectors for every fixed defect or newly durable behavior.
- [ ] Require maintainer approval before enabling the new consumers by default.

### Phase 9 Exit Gate

- [ ] Logical migration is complete and compatibility-protected.
- [ ] Physical LoTM migration can begin without using generated output as authority.

## Phase 10: Generalized Summary Model

### Phase 10.1 Summary Contract

- [ ] Define one reusable summary-page contract with typed targets and coverage.
- [ ] Support work segments, works, content groups, ordered series, franchises, and applicability
  scopes without duplicating source hierarchy.
- [ ] Support chapter, episode, arc, season, volume, book, series, and franchise display scopes as
  pack/project vocabulary.
- [ ] Separate hand-authored canonical summaries from generated summary projections.
- [ ] Define boundary, evidence, artwork, major-development, thread, and structured-prose modules.

### Phase 10.2 LoTM Volume Compatibility Mapping

- [ ] Map `volume-summary` logically into the generalized summary contract without rewriting its
  canonical page or template.
- [ ] Preserve the existing Volume 1 page, template, artwork, links, and graph exclusion behavior.
- [ ] Decide whether the project keeps a specialized volume profile over the generic summary type.
- [ ] Defer physical summary-page conversion to Phase 13 migration services.

### Phase 10 Exit Gate

- [ ] A summary references canonical source-model targets rather than rebuilding book/episode
  hierarchy in page data.

## Phase 11: Generated Data Projections

### Phase 11.1 Projection Metadata

- [ ] Define compiler version, project revision/digest, schema-pack versions, generation time,
  authority policy, applicability context, and reader-boundary metadata.
- [ ] Define deterministic invalidation and rebuild behavior.
- [ ] Keep every output clearly generated and noncanonical.

### Phase 11.2 JSON

- [ ] Export effective schema and normalized content for website, API, interoperability, and
  debugging consumers.
- [ ] Add deterministic snapshots and schema-version handling.

### Phase 11.3 SQLite

- [ ] Add a portable local query projection for QA, editors, and single-machine applications.
- [ ] Define normalized tables, indexes, rebuild behavior, and transaction boundaries.
- [ ] Do not treat SQLite as the canonical collaborative server.

### Phase 11.4 DuckDB And Parquet

- [ ] Add Parquet projections only when concrete analytical queries and schemas are identified.
- [ ] Use DuckDB for local columnar querying, notebooks, profiling, and analytical validation.
- [ ] Keep notebook experiments downstream of shared compiler services.
- [ ] Promote durable notebook logic into runtime modules and permanent tests.

### Phase 11.5 Optional Lakehouse Adapter

- [ ] Defer Delta/Databricks implementation until measured distributed ingestion, scale, governance,
  lineage, or multi-team requirements justify it.
- [ ] Require any lakehouse adapter to consume the same normalized contracts and preserve
  bronze/silver/gold authority semantics.

### Phase 11 Exit Gate

- [ ] Local website, editor, QA, and analytical consumers can use generated projections without
  changing canonical authority.

## Phase 12: Mutation And Migration Services

### Phase 12.1 Planning And Preview

- [ ] Add stable persisted page/content IDs.
- [ ] Build impact reports for schema changes, category renames, page moves, storage splits,
  relationship migrations, pack activation, upgrades, disabling, and removal.
- [ ] Preview canonical edits, file moves, reference changes, generated-output invalidation, and test
  impact.
- [ ] Refuse ambiguous or unsafe plans.

### Phase 12.2 Apply And Recovery

- [ ] Validate proposed state before applying changes.
- [ ] Apply canonical changes as one reviewed operation.
- [ ] Preserve operation records sufficient for diagnosis and recovery.
- [ ] Regenerate or invalidate every affected projection.
- [ ] Expose a complete Git diff for maintainer review.

### Phase 12.3 Editorial Governance Boundary

- [ ] Define content ownership, stewardship, reviewer, approval, and lifecycle metadata separately
  from authorship credits, factual authority, canon status, legal ownership, and Git identity.
- [ ] Preserve review and approval decisions as auditable governance history without converting them
  into source evidence or truth claims.
- [ ] Allow migration plans to identify required reviewers or governed scopes without making the
  mutation service the owner of organization-specific workflow policy.

### Phase 12 Exit Gate

- [ ] Physical migrations no longer depend on hand-editing repeated schema or relationship data.
- [ ] Editorial approval and factual/source authority remain independently explainable.

## Phase 13: Physical LoTM Data Migration

Each wave must parse the legacy representation, propose the new canonical representation, compare
normalized outputs, run relevant conformance and compatibility profiles, receive maintainer review,
and retain rollback through Git. Do not remove a compatibility adapter before its entire migration
wave is confirmed.

### Phase 13.1 Pilot And Storage Decision

- [ ] Decide whether canonical prose and structured records remain embedded or become linked files.
- [ ] Define stable linking, atomic-edit, validation, and missing-sidecar behavior.
- [ ] Pilot the final layout with Dunn Smith before broad migration.
- [ ] Repeat with Old Neil and Leonard Mitchell to exercise optional and late-reveal modules.

### Phase 13.2 Character Wave

- [ ] Migrate the character template and all existing character pages.
- [ ] Migrate character relationships and projection declarations.
- [ ] Remove character-only legacy compatibility after equivalence is confirmed.

### Phase 13.3 Pathway Wave

- [ ] Complete pathway schema/template normalization, including sequences and neighboring pathways.
- [ ] Migrate existing pathway pages and graph projections.

### Phase 13.4 Remaining Glossary Waves

- [ ] Migrate factions and families.
- [ ] Migrate artifacts and items.
- [ ] Migrate locations.
- [ ] Migrate events and event subtypes such as fights.
- [ ] Migrate knowledge sources.
- [ ] Migrate concepts, deities, epochs, tarot cards, and remaining approved categories.
- [ ] Introduce future material or preparation categories only through reviewed pack/taxonomy work.

### Phase 13.5 Non-Glossary Content

- [ ] Migrate investigations.
- [ ] Physically migrate summary pages from the Phase 10 compatibility mapping.
- [ ] Migrate boards, dashboards, and navigation indexes where structured modeling adds value.

### Phase 13.6 Legacy Retirement

- [ ] Remove obsolete duplicated template/schema declarations.
- [ ] Remove migrated Relationship Seed factual duplication.
- [ ] Remove compatibility parsers only after no canonical record depends on them.
- [ ] Run the full-release and framework extraction gates.

### Phase 13 Exit Gate

- [ ] All existing LoTM canonical data uses the accepted schema/storage model.
- [ ] No information present before migration has been silently lost.

## Phase 14: Solution Profiles, Recommendations, And Add-On Lifecycle

### Phase 14.1 Solution Profiles

- [ ] Define versioned industry solutions and starter profiles separately from packs.
- [ ] Keep solution profiles out of pack-role classification: they select and recommend packs but do
  not own controlled vocabulary, runtime mechanics, or project facts.
- [ ] Allow profiles to recommend packs, capabilities, categories, modules, graph presets, and
  project settings without inventing project facts.
- [ ] Add initial narrative profiles such as serialized fiction, shared-universe fiction, screen
  series, and fantasy worldbuilding.
- [ ] Make every recommendation previewable and optional unless required by a selected contract.

### Phase 14.2 Suggested Schemas

- [ ] Define reusable optional schemas such as magic systems without hardcoding them into all
  fantasy projects.
- [ ] Distinguish recommended, selected, enabled, and instantiated state.
- [ ] Record user-selected, inherited, suggested, and derived setting origins.

### Phase 14.3 Add-On Operations

- [ ] Discover compatible add-on packs.
- [ ] Preview dependency selection, capability activation, schema changes, and migrations.
- [ ] Activate additive capabilities without rewriting unrelated records.
- [ ] Block disabling or removing packs while project data still depends on them unless an accepted
  migration resolves that dependency.
- [ ] Prove adding shared-universe/parallel-continuity support to an existing narrative project.

### Phase 14 Exit Gate

- [ ] A project can safely gain a new capability family after creation through shared services.

## Phase 15: Framework Extraction And IT Proof Of Concept

### Phase 15.1 Extracted Framework Product

- [ ] Rehearse the expanded portable bundle including effective schema, page modules, normalized
  content, projections, and mutation services.
- [ ] Decide the physical repository/package distribution model.
- [ ] Keep LoTM as a consumer and permanent compatibility corpus.

### Phase 15.2 IT Solution And Pack

- [ ] Define an IT/operations solution profile and domain packs without narrative vocabulary.
- [ ] Model representative infrastructure, systems, applications, environments, configurations,
  evidence, incidents, changes, diagrams, and vendor references.
- [ ] Define source-priority and authority examples appropriate to operational evidence.
- [ ] Build sample content, summaries, graphs, QA, JSON, and SQLite projections.
- [ ] Use Parquet/DuckDB only where the POC has concrete analytical questions.
- [ ] Pressure-test both ownership directions: whether any supposedly universal behavior still
  belongs in narrative packs, and whether reusable mechanics remain trapped inside a narrative
  pack merely because LoTM was the first consumer.
- [ ] Prove that IT may select `hosting-foundation` and `hosting-compute` without receiving
  narrative hosting vocabulary, while LoTM may select `hosting-foundation` and
  `hosting-narrative` without receiving compute or simulation vocabulary.

### Phase 15 Exit Gate

- [ ] The framework supports a real non-narrative consumer without algorithm forks or LoTM leakage.

## Phase 16: Streamlit And Future Interfaces

### Phase 16.1 Read-Only Workbench

- [ ] Display effective schema, pack/capability state, validation findings, normalized records, QA
  reports, and graph previews through shared services.

### Phase 16.2 Project And Schema Wizards

- [ ] Add industry/profile selection, recommended packs, capability groups, progressive disclosure,
  dependency explanations, and impact previews.
- [ ] Keep setup and editing workflows distinct.

### Phase 16.3 Portable Project Bundles

- [ ] Define a versioned logical project-bundle contract independently from its physical container
  so import, export, validation, and migration services do not depend on ZIP-specific behavior.
- [ ] Use ZIP as the initial portable container format, with a documented extension and media type;
  evaluate alternative containers only when measured size, streaming, random-access, signing, or
  deployment requirements justify them.
- [ ] Keep `project.yaml` at a stable internal location as the bundle entrypoint. Preserve its
  referenced canonical registries, project-owned extension packs, content, and selected resources
  as separate internal files rather than flattening the project into one monolithic YAML document.
- [ ] Add a generated bundle manifest that records the bundle-contract version, project entrypoint,
  included paths, file digests, framework and pack compatibility metadata, and the selected
  inclusion profile without becoming canonical project configuration.
- [ ] Define reviewed inclusion profiles for configuration-only, portable working project, and
  complete archival export. Make generated outputs, ignored workspace state, temporary files,
  source material, and large resources explicit opt-in or opt-out decisions rather than accidental
  ZIP contents.
- [ ] Keep bundle paths portable and relative. Reject absolute paths, traversal, unsafe links,
  duplicate normalized destinations, undeclared files, digest mismatches, and unsupported bundle
  or schema versions before extraction or project mutation.
- [ ] Validate an imported bundle and preview dependencies, missing packs, compatibility findings,
  migrations, file creation, and conflicts before applying it through shared mutation services.
- [ ] Recompose the effective schema from imported canonical files. Never treat an exported
  effective-schema JSON document or another generated projection as canonical bundle input.
- [ ] Add deterministic headless pack/unpack and round-trip tests before exposing bundle operations
  in the interface; the UI remains a client of those shared services.
- [ ] Let project setup export, import, clone, and inspect one portable artifact while still showing
  its internal manifest, registries, content, resources, dependencies, and validation state.

### Phase 16.4 Category And Page Editing

- [ ] Add schema-driven category generator/editor and page generator/editor.
- [ ] Add structured-data editing with required/optional/derived behavior.
- [ ] Add linked prose/data editing without duplicating schema definitions.
- [ ] Route every mutation through preview, validation, and migration services.

### Phase 16.5 Operational Hardening

- [ ] Add authentication, authorization, concurrency, audit, deployment, and server persistence only
  when the chosen product boundary requires them.
- [ ] Add configurable stewardship, review, and approval workflows only through the governance
  contract, keeping workflow identity separate from contributor credit and evidence authority.
- [ ] Re-evaluate SQLite versus a multi-user database for collaborative deployments.
- [ ] Re-evaluate Databricks/Delta only for justified analytical or enterprise ingestion workloads.

### Phase 16 Exit Gate

- [ ] The interface is a replaceable client over tested headless services rather than the owner of
  schema or domain behavior.
- [ ] A project can round-trip through the initial ZIP-based portable bundle without flattening its
  canonical registries, ingesting generated projections as authority, escaping its destination, or
  changing its recomposed effective schema.

## Phase 17: Deferred Capability Delivery Program

This phase is an ordered capability backlog, not a prerequisite for beginning Phases 2-16. Promote
one capability or tightly coupled family at a time through the framework improvement lifecycle.
Consumer evidence may reorder these waves, but a capability must not move from `planned` to
`available` until its executable contract and permanent tests exist.

### Phase 17.1 Core Migration Services

- [ ] Complete the core `migration-services` capability through Phase 12 rather than implementing a
  second migration owner here.
- [ ] Promote it from `planned` only after preview, validation, apply, recovery, projection
  invalidation, and Git-diff contracts pass the Phase 12 exit gate.

### Phase 17.2 Narrative Publishing And Textual History

- [ ] Implement `textual-witnesses` for manuscripts, drafts, fragments, revisions, and parallel text
  versions without treating every witness as a distinct creative work.
- [ ] Implement `editorial-assembly` for compilation, completion, commentary, synthesis, and
  posthumous editing with ordered inputs, contributor roles, provenance, and unresolved scholarly
  alternatives.
- [ ] Implement `publication-runs` for publisher-, imprint-, territory-, date-, serialization-, and
  format-scoped runs beneath works and editions without collapsing manifestations or releases.
- [ ] Preserve collaborative-wiki revisions, editorial rewrites, deletions, restorations, errata,
  and reconstructed text or media as versioned history rather than one overwritten current record.
- [ ] Pressure-test Tolkien-style textual traditions, serialized prose and comics, translated and
  revised editions, incomplete works, posthumous compilations, variant covers, legacy numbering,
  relaunches, and competing stemmata.

### Phase 17.3 Narrative Production, Credits, And Rights

- [ ] Implement `contributor-credits` with contributor identity, role, credited-as text, scope,
  ordering, effective windows, and source-backed uncertainty.
- [ ] Implement `rights-grants-and-restrictions` with parties, assets, right types, instruments,
  territory, windows, exclusivity, restrictions, and obligations while making no automatic legal
  conclusion.
- [ ] Keep authorship, production contribution, ownership, authorization, canon authority, and
  commerciality separate throughout composition and pressure testing.
- [ ] Pressure-test cross-company publications and composite properties without inferring shared
  ownership, continuing authorization, canon equivalence, or unrestricted reuse from creative
  lineage alone.

### Phase 17.4 Preservation And Access

- [ ] Implement `preservation-state` for whole or partial survival, loss, damage, reconstruction,
  archival custody, and supporting evidence.
- [ ] Implement `access-state` for platform, territory, release window, availability, delisting, and
  restoration without conflating access with preservation or rights.
- [ ] Support segment- and release-scoped vaulting, removal, restoration, reconstruction, and
  temporary unavailability so a live service or incomplete archive need not treat a whole work as
  uniformly present or absent.
- [ ] Pressure-test lost media, surviving fragments, archival restorations, regional catalog changes,
  reconstructed episodes, live-service content vaults, and temporarily unavailable works.

### Phase 17.5 Interactive Narrative

- [ ] Implement `branching-narratives` for authored choice points, routes, prerequisites, endings,
  and mutually exclusive claims without overloading continuity or ordinary timeline branches.
- [ ] Implement `narrative-instances` for playthroughs, campaigns, sessions, save states, and
  participant-specific outcomes derived from authored structures.
- [ ] Model aggregate and participant-contributed live-world outcomes separately from authored
  possibilities, individual sessions, later canonical promotion, and retrospective summaries.
- [ ] Preserve save import, character or asset transfer, seasonal state, and shared-world campaign
  progression without inferring that every participant experienced every promoted event.
- [ ] Pressure-test games, visual novels, tabletop campaigns, live-service story revisions, and
  replayed routes with different participant knowledge, including Destiny- and EVE-style collective
  history.

### Phase 17.6 Live And Synchronized Performance

- [ ] Implement `live-performance-productions` for stagings, revivals, tours, venues, casts, and
  production-scoped creative choices.
- [ ] Implement `performance-events` for individual scheduled or recorded performances without
  confusing the event, production, authored work, recording, or release manifestation.
- [ ] Extend the event boundary to synchronized digital performances and one-time live-service
  events while keeping the scheduled event, diegetic occurrence, participant session, recording,
  replay, and later reenactment distinct and explicitly related.
- [ ] Pressure-test theatre, musicals, touring productions, understudy substitutions, revivals, and
  captured live performances alongside Fortnite-style one-time events and historical replays.

### Phase 17.7 Shared-Universe Crossover Events

- [ ] Implement `crossover-events` with ordered core entries, required and optional tie-ins,
  publication-run placement, continuity scope, participant works, and reader-order alternatives.
- [ ] Keep crossover event identity separate from an in-world occurrence, publication event,
  adaptation lineage, or generic content group.
- [ ] Pressure-test comic-event reading orders, television crossovers, film/series tie-ins, and
  continuity-specific retellings, including Marvel/DC main-event, tie-in, alternate-order, and
  cross-company structures.

### Phase 17.8 Shared-Universe Continuity Topology

- [ ] Evaluate and contract a candidate `continuity-systems` capability for universes, multiverses,
  realms, domains, and other named continuity containers without treating a container as a creative
  work or ordinary continuity relationship.
- [ ] Represent scoped membership, containment, externality, accessibility, and movement among
  continuity systems while preserving pairwise branch, counterpart, reset, merge, and restoration
  relationships.
- [ ] Keep continuity topology separate from chronology-context topology, spatial location,
  publication grouping, canon authority, and entity incarnation identity.
- [ ] Pressure-test Battleworld-style constituent domains, DC multiverse/omniverse organization,
  realms external to ordinary universes, and cross-system visitors.
- [ ] Add a pack declaration only when the contract, ownership boundary, runtime behavior, and
  permanent conformance meet the Phase 3.4 promotion criteria.

### Phase 17.9 Narrative Sliding Chronology Policies

- [ ] Evaluate and contract a candidate `sliding-chronology-policies` capability for long-running
  serials whose publication history advances while in-world history remains compressed, revised,
  or only partially mapped.
- [ ] Define versioned, scoped, explainable mapping policies without weakening core exact-position
  semantics or silently extrapolating from sparse chronology anchors.
- [ ] Preserve publication order, story order, reader disclosure, explicit retcons, and unresolved
  chronology as independent structures.
- [ ] Pressure-test long-running Marvel/DC comics, rolling character ages, continuity relaunches,
  and contradictory editorial eras before promoting the capability.
- [ ] Keep the capability narrative-owned unless a cross-domain use case justifies architectural
  promotion through the framework improvement lifecycle.

### Phase 17.10 Versioned Rulesets And Normative Policy

- [ ] Evaluate a domain-neutral candidate for versioned normative rules, effective scope, precedence,
  override, exception, amendment, selected-version context, and directional compatibility without
  treating a rule as a descriptive fact, recurrence rule, provenance authority rule, or continuity.
- [ ] Define narrative-interactive extensions for game mechanics, format legality, campaign or table
  selections, house rules, errata, and mechanically equivalent objects with distinct names, art, or
  creative identity.
- [ ] Pressure-test D&D rules revisions, Magic format legality and mechanically equivalent cards,
  paired game versions, IT policy, medical protocol, and legal/compliance controls before deciding
  whether the foundation belongs in core or a reusable cross-industry pack.
- [ ] Revisit ownership after the Phase 15 IT proof of concept; add pack declarations only after the
  domain-neutral boundary and any narrative bridge have executable contracts and permanent tests.

### Phase 17.11 Promotion And Regression Gate

- [ ] For every promoted capability, add paired runtime fixtures and conformance where parity
  applies, register aggregate coverage, update retained pressure scenarios, and run required
  compatibility and extraction profiles.
- [ ] Update pack versions and lifecycle metadata only in the implementation commit that makes the
  capability usable.
- [ ] Record superseded assumptions, architectural promotions, implementation evidence, pressure
  findings, and any remaining limitations in framework evolution.
- [ ] Reconcile this phase against all pack declarations and confirm that no `planned` capability is
  orphaned from an implementation path or accepted deferral.

### Phase 17 Exit Gate

- [ ] Every currently declared planned capability is implemented, deliberately retained as deferred
  with current rationale, or removed through a documented compatibility decision.
- [ ] No pack advertises an available capability whose executable contract and permanent coverage
  are absent.

## Final Completion Gate

- [ ] Effective schema composition is inspectable and deterministic.
- [ ] Packs, capabilities, modules, defaults, and recommendations are understandable and safely
  composable.
- [ ] Structured facts and graph projection declarations have unambiguous ownership.
- [ ] QA and Visualization share normalized content and one graph engine.
- [ ] Summary pages target the source model instead of duplicating it.
- [ ] LoTM is physically migrated without information loss.
- [ ] JSON, SQLite, and justified analytical projections remain rebuildable.
- [ ] Add-on packs can be installed, activated, upgraded, disabled, and removed safely.
- [ ] Every declared planned capability remains traceable, and every available capability is backed
  by an executable contract and permanent coverage.
- [ ] The extracted framework supports the IT proof of concept.
- [ ] Streamlit and future interfaces depend only on shared headless services.
