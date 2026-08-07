# Framework Evolution History

This document records how the reusable knowledge-platform framework evolved, why each version was introduced, and what the pressure testing after each version exposed. It is both a design history and a forward-looking engineering log.

The end-to-end version process is governed by `Framework/framework_improvement_lifecycle.md`. Cumulative testing requirements are governed by `Framework/testing_methodology.md`. This file records history and handoff state; it does not independently define either workflow.

This file owns numbered semantic/model versions. Confirmed implementation phases from the separate
platform roadmap belong in `Framework/platform_evolution.md`; do not append platform-phase closure
entries here or duplicate a version's detailed pressure history there.

The version numbers here describe the **framework evolution rounds discussed during the extraction project**. They are not interchangeable with every registry's internal `schema_version` or every schema pack's `pack_version`. V1-V15 primarily track the narrative source registry as it grew from schema 1 through schema 15. V16 onward expands the framework through additional registries and shared services, each of which retains its own schema and pack version.

From V30 onward, update this file as part of each version. Follow the lifecycle document for the complete sequence:

1. Open the version section with `Implemented by: pending` after design is settled and before implementation begins. Beginning with V38, include the mandatory `Proposed testing` and `Proposed candidates` fields plus a pending `Testing After Vn` section.
2. Record the problem, design decision, implementation surface, and reason for the change.
3. Run and record the cumulative implementation-conformance and project-compatibility families required by `Framework/testing_methodology.md` before treating implementation as complete.
4. Use the lifecycle's two-part confirmation sequence to replace the pending implementation marker with the exact implementation hash and subject.
5. Replace the pending `Testing After Vn` content before beginning the next version. Record the applicable stable test-family IDs and keep adversarial pressure testing distinct from implementation conformance and compatibility regression.
6. Record defects separately from missing capabilities.
7. Update the era index when a version begins a genuinely new architectural phase.
8. Record superseded assumptions, architectural extractions, and promotions when they materially apply; do not force a marker into every version.
9. End the testing section with a clear next-version recommendation or an explicit reason no immediate version is recommended.
10. Record the candidate-catalog entries used and any catalog addition, revision, replacement, or deliberate non-promotion discovered during pressure testing.

## Evolution Eras

- **Foundation:** Manifest, architecture, taxonomy, and resource separation
- **V1-V6:** Works, media, manifestations, releases, and distribution
- **V7-V15:** Evidence, authority, production context, scope, and applicability
- **V16-V23:** Entity identity and cross-registry provenance/reconciliation
- **V24-V27:** Deterministic configuration ingestion
- **V28-V42:** Civil time, general chronology, occurrence/recurrence integrity, subject-state acquisition, deterministic recurrence policy, extensible semantic resolution, aggregate cardinality, participation identity, chronology-context topology, and timeline-branch lifecycle
- **V43-V44:** Epistemic state and capability/proficiency progression
- **V45-V50:** Competing structural interpretations, participant-relative chronology, hosted identity/embodiment, bounded carrier topology, optional hosting-pack isolation, and chronology-position provider closure

### Marker Conventions

- **Superseded assumption:** Names a prior modeling belief that the version proved incomplete or incorrect.
- **Architectural extraction:** Marks behavior moved out of one consumer or registry into a reusable service or domain component.
- **Architectural promotion:** Marks behavior recognized as domain-neutral and moved into the core framework.

Markers are selective architectural annotations, not mandatory fields. A version may use none, one, or several according to the ownership change it actually made.

## Foundation Before V1

The framework extraction began after the LoTM repository had already developed page templates, taxonomy rules, provenance-rich YAML blocks, reader-bounded graph generation, Obsidian QA exports, and paired Python/PowerShell tooling. Those systems proved the larger idea, but much of their behavior was still encoded in LoTM-specific documentation or directly inside individual scripts.

The extraction foundation established several principles before the numbered schema rounds began:

- Markdown pages remain the human-readable publication layer while structured registries and data blocks provide machine-readable authority.
- Project configuration, reusable framework contracts, domain packs, and project-instance data must be separate layers.
- Taxonomies and capabilities must be executable configuration rather than prose-only allowlists.
- Python and PowerShell implementations must remain behaviorally equivalent.
- A capability is not `available` until the corresponding contract and validation exist; planned vocabulary alone does not make it executable.
- Graphing, QA, future editors, and future domain-specific products should consume shared services rather than reimplementing model logic.

The immediate architecture commits were `39ec486` (manifest-based project configuration), `ced66c2` (reusable framework architecture contract), `9139b2c` and `493e26c` (content taxonomy reconciliation and configuration), and `58ec3c2` (repository content and resource types).

## V1 - Series-Aware Source Registry

**Implemented by:** `0b4c5ff` (`Add series-aware source registry`)

**Superseded assumption:** Volume and chapter numbers identify a position without a work ID.

V1 created the first executable source registry in `Project_Config/sources.yaml`. It separated canonical works, media/position profiles, evidence sources, aliases, evidence modes, comparison groups, priorities, resource bindings, and verified volume catalogs.

The registry explicitly modeled both *Lord of Mysteries* and *Circle of Inevitability* as separate works in one ordered series. Novel positions became work-qualified so identical chapter or volume numbers in different books could not collide. Source priority became scoped to a comparison group and work, allowing the novel to be the primary authority while preserving Donghua-scoped deviations instead of overwriting them.

This version existed because the earlier model treated "novel," "Donghua," EPUB files, adaptations, books, and evidence artifacts too much like interchangeable source labels. V1 made those distinctions machine-readable and gave future sequels stable namespaces.

## Testing After V1

The first tests used LoTM's two novels and Donghua, then mentally expanded the model to franchises with sequels, spinoffs, specials, films, remakes, and parallel canon. They showed that a simple ordered `series` and source-level adaptation pointer were insufficient.

The tests found that the next version needed:

- heterogeneous work groups rather than only one linear series;
- creative works distinct from concrete evidence artifacts;
- explicit continuity membership and continuity relationships;
- typed creative lineage separate from edition, transcript, subtitle, scan, and extract lineage;
- authority profiles instead of one global priority rule; and
- independent works for seasons, specials, films, and other release units with their own spoiler timing.

## V2 - Franchise, Continuity, and Lineage Generalization

**Implemented by:** `8b03985` (`Generalize franchise and adaptation source modeling`)

V2 replaced the narrow series model with typed work groups for franchises, ordered series, adaptation programs, and collections. It introduced continuities, continuity relationships, authority profiles, typed work relationships, and typed source relationships.

Creative lineage such as sequel, prequel, spinoff, side story, adaptation, remake, retelling, crossover, compilation, and inspiration became separate from evidence-artifact lineage such as edition, translation, transcript, subtitle track, dub, scan, extract, and package membership. Donghua Season 1 and each released special became independently addressable works within an adaptation program and adaptation continuity.

This version made comparison policy explicit: a selected authority profile determines which continuities and derivative relationships are comparable, how source priority is interpreted, and where deviations belong.

## Testing After V2

Testing V2 against books, television, film, animation, comics, and mixed-media franchises revealed a deeper portability problem. Terms such as "Donghua," "EPUB artwork," "television special," and "streaming source" mixed several independent dimensions.

The architecture review found that the next version needed:

- reusable schema packs separated from LoTM project instances;
- lifecycle states for capabilities so absent domain features defaulted off cleanly;
- media modality, cultural form, creative/release form, and evidence container as independent axes;
- generic work segments and named ordering schemes; and
- adaptation mappings below whole-work lineage.

The inter-version architecture work was implemented by `21f5da0` (`Separate reusable framework schema packs`) and `9819631` (`Model schema pack capability lifecycles`). Those commits created the pack layer and clarified `planned`, `available`, and `active`/selected behavior before V3 instantiated the broader model.

## V3 - Composable Narrative Media Model

**Implemented by:** `b6482fb` (`Expand narrative framework model`)

**Superseded assumption:** A compound medium label can safely carry modality, cultural form, release form, and container semantics.

**Architectural extraction:** Narrative-media semantics moved out of LoTM-specific and monolithic source assumptions into composable domain packs built above the core framework.

V3 expanded the framework into composable narrative packs: core, narrative media, publishing, screen/audio, adaptation, shared universe, production, preservation, and interactive media. It separated:

- medium profiles used for reader positions and citations;
- modalities such as prose, animation, audio, still image, and interactive media;
- cultural forms such as Donghua, anime, manga, manhua, manhwa, and webtoon;
- release forms such as novel, season, special, film, issue, and collected volume; and
- container formats such as EPUB, print, streaming release, subtitle file, and digital image.

It also introduced stable segments, named ordering schemes, and work/segment adaptation mappings. This allowed an EPUB-contained illustration to remain an illustration carried by an EPUB, and a Donghua film to remain animation in the Donghua tradition with a film release form and an independent distribution container.

## Testing After V3

A broad narrative-media pressure test covered Star Wars, Star Trek, Tolkien's legendarium, Western comics, manga, manhua, manhwa, animation, games, films, television seasons, specials, compilation releases, and spinoffs.

The model represented creative identity well, but testing exposed that "the work" was still carrying too much distribution and edition behavior. The next version needed:

- manifestations for editions, translations, cuts, remasters, recuts, and builds;
- release components for subtitle tracks, embedded art, dubs, and similar pieces;
- territories, platforms, release events, catalog placement, and offerings; and
- explicit release/distribution ordering separate from story or publication order.

## V4 - Manifestations and Distribution

**Implemented by:** `e9129f2` (`Add narrative distribution source model`)

**Superseded assumption:** A creative work and its editions, releases, and distribution are one object.

V4 introduced the narrative-distribution pack and separated creative works from manifestations, release components, release events, catalog placements, and platform offerings. Manifestation relationships modeled edition, translation, cut, remaster, recut, and build lineage.

The LoTM EPUBs became manifestations of their respective novels. Donghua streaming versions became manifestations of screen works, while English subtitles and embedded illustrations became release components. Territories and platforms were made first-class registries even when the LoTM project had no records to instantiate yet.

This version was necessary because a work can have many materially different editions and releases without becoming many different creative works.

## Testing After V4

Testing focused on irregular publication and release ecosystems: collected editions, localized titles, issue numbering that differs from reading order, boxed sets, streaming bundles, platform catalogs, and identifiers supplied by different vendors.

It found that the next version needed:

- stable numbering schemes independent of ordering;
- total and partial ordering modes;
- release packages distinct from manifestations;
- stable external identifier schemes;
- localized titles with scoped history; and
- segment-scoped manifestations and components.

## V5 - Numbering, Packaging, and External Identity

**Implemented by:** `d9fad59` (`Expand narrative source registry to schema v5`)

V5 added numbering schemes, release packages, external identifier schemes, and richer localized-title handling. It strengthened segment scoping across manifestations, components, events, and offerings, and made total versus partial ordering explicit.

The key design decision was that labels and issue/episode numbers do not inherently define order. A project can preserve publication order, release order, production order, recommended order, and story order independently while retaining the exact printed or broadcast labels.

## Testing After V5

Pressure tests used split seasons, cours, omnibus editions, reordered streaming catalogs, compilation films, irregular comic numbering, bonus chapters, and staggered international releases.

They exposed three missing structures:

- curated or overlapping segment groupings that are not parent/child structure;
- mappings between structurally different manifestations; and
- release runs that can partition one ordered work into batches, phases, cadence changes, and exceptions.

The tests also showed that a source may cover more than one work and therefore could not remain permanently bound to one `work_id`.

## V6 - Complex Release Structure

**Implemented by:** `212a190` (`Expand source registry for complex releases`)

**Superseded assumption:** One evidence source belongs to one work.

V6 introduced segment groups, manifestation segment mappings, release runs, and multi-work evidence-source scope. Manifestation mappings could now preserve splits, combinations, omissions, reorderings, and other structural differences between editions or cuts. Release runs represented phased publication or distribution over a declared segment order.

This version made room for cours, batches, split seasons, weekly runs with hiatuses, compilation structures, and sources that legitimately inspect multiple creative works.

## Testing After V6

Testing found that `segment_groups` was too structural and too narrow for reusable, overlapping, or mixed work/segment collections. It also exposed gaps in component lineage and evidence provenance.

The next version needed:

- recursively nestable content groups with stable member identities and roles;
- release-component relationships for revisions, translations, dubs, and derivation;
- bounded source coverage rather than only broad work scope; and
- stable assertions that connect exact claims to exact source positions.

## V7 - Content Groups and Assertion Provenance

**Implemented by:** `55bca1e` (`Generalize narrative source registry contracts`)

**Superseded assumption:** Declaring source coverage is enough to support an individual claim.

V7 replaced narrow segment grouping with generic content groups that can contain works, segments, or nested groups. Members received stable identities and controlled participation roles, while role and order remained independent.

It added release-component lineage, source coverage declarations, and provenance assertions. Assertions could identify a target record and field path, preserve an asserted value, and attach evidence locators. This moved the framework from "a source covers this work" toward "this source position supports this exact claim."

## Testing After V7

Cross-media tests showed that a concrete source may observe several manifestations, components, packages, runs, or events and may need to state that scope explicitly. Merely listing works and coverage ranges could not explain which release object had actually been inspected.

The tests called for:

- globally stable, typed observations;
- observations that can target multiple release-object kinds;
- validation that observations remain inside the source's declared work scope; and
- stricter distinction between evidence scope, coverage, and individual claim locators.

## V8 - Multi-Target Source Observations

**Implemented by:** `cd60966` (`Upgrade source registry to schema v8`)

V8 added typed `observations` to evidence sources. A source could now declare that it directly inspected a manifestation, release component, package, run, event, offering, or other supported release object rather than relying on inference from shared work IDs.

Observation targets became globally addressable and validated against source work scope. Coverage remained the position/channel boundary, and assertion locators remained the exact claim evidence. This preserved three distinct questions: what artifact was observed, what portion/channel the source covers, and where the evidence for a claim appears.

## Testing After V8

Testing source disagreements across novel text, Donghua visuals, dialogue, subtitles, artwork, and release metadata showed that one global source priority remained too coarse.

The next version needed:

- authority rules scoped by claim namespace;
- ranking by source, source role, medium, or evidence mode;
- explicit canonical-work fields in medium positions rather than guessed field names;
- source-specific locator-media allowlists; and
- deterministic handling of overlapping authority rules.

## V9 - Claim-Aware Authority

**Implemented by:** `fd7c907` (`Upgrade narrative source registry to v9`)

**Superseded assumption:** One source-priority ranking applies to every kind of claim.

V9 added claim-authority rules to authority profiles. Different evidence could lead for canonical content, dialogue, visual design, localization, and release metadata without forcing one source to dominate every comparison.

Medium profiles gained an explicit `work_scope_field`, and sources gained locator-media allowlists. Historical localized-title windows and nested content groups received stronger validation. Authority rule matching became explicit and precedence-aware.

## Testing After V9

Tests using hierarchical claim families and irregular work structures found that exact namespace matching was insufficient and that lexically comparing positions could produce false ordering.

The next version needed:

- controlled-value ancestry for claim namespaces;
- explicit rule precedence with rejection of tied winners;
- pack-owned structural position-validation strategies;
- volume/chapter consistency against verified catalogs;
- semantic field-path resolution; and
- point and range locators with structurally meaningful comparison.

## V10 - Structural Position and Hierarchical Authority

**Implemented by:** `26ea362` (`Upgrade narrative source registry to v10`)

V10 added descendant-aware claim authority, explicit precedence, and structural position validators. The initial `work-volume-catalog` strategy validates chapter bounds and volume/chapter agreement without duplicating volume ranges in each medium definition.

It also formalized position sorting and comparison, point/range locator shapes, and semantic provenance field paths. Pending catalogs remained explicitly unverifiable rather than being treated as malformed or silently guessed.

## Testing After V10

Testing comics, episode production codes, irregular installments, and sources with nonnumeric labels showed that volume catalogs were only one structural strategy. The tests also found that authority decisions needed to explain their result, not merely return a winner.

The next version needed:

- ordering-backed structural position validation;
- stable segment fields plus explicit total-order scheme fields;
- temporal-window ordering and overlap checks;
- explainable authority decisions; and
- stronger source-bounded provenance validation.

## V11 - Ordering-Backed Positions and Explainable Decisions

**Implemented by:** `a337d25` (`Upgrade narrative source registry to v11`)

V11 added the `work-segment-ordering` structural validator for irregular issue, episode, chapter, or installment labels. Positions can be compared by a registered ordering ordinal rather than lexical segment ID.

Authority evaluation became explainable, temporal windows were checked for order and overlap, and provenance was tightened so locators had to remain within source scope, coverage, medium, mode, and structural position rules.

## Testing After V11

Tests comparing multiple equally ranked sources exposed an important distinction: a tie can mean corroboration, contradiction, or genuine incomparability. Evidence-mode hierarchies also needed the same descendant behavior as claim namespaces.

The next version needed:

- candidate-set authority evaluation rather than pairwise assumptions;
- stable claim identity and shape consistency;
- distinction between corroborating and conflicting equal-authority values;
- hierarchical evidence modes; and
- channel-scoped coverage that prevents a locator from borrowing unrelated coverage.

## V12 - Multi-Source Evidence Evaluation

**Implemented by:** `d679cc6` (`Upgrade source evidence evaluation to v12`)

V12 added multi-source authority comparison and stable-claim evaluation. It distinguishes a winner, an equal-authority tie, an incomparable set, corroborating values, and conflicting values.

Claim keys became stable across repeated assertions and had to preserve subject, namespace, and field shape. Evidence modes gained hierarchy, and coverage became channel-scoped by medium and evidence mode. Locators could no longer rely on coverage declared for a different channel.

## Testing After V12

Pressure testing deliberately added parody and transformative works, including *Dragon Ball Z Abridged* relative to *Dragon Ball Z* and *Spaceballs* relative to *Star Wars*. This exposed a category error: parody lineage, authorization, commerciality, production origin, and legal rights are related but not equivalent.

The tests found that the next version needed:

- explicit parody and broader derivative-work lineage;
- segment-scoped adaptation mappings for reused or transformed material;
- contributor and production roles separated from creative lineage; and
- production origin, authorization, rights basis, and commerciality stored as independent facts without legal inference.

## V13 - Parody and Production/Rights Separation

**Implemented by:** `3b7df21` (`Model parody and production rights independently`)

**Superseded assumption:** Derivative lineage implies authorization, officiality, commerciality, or legal status.

V13 added parody, retelling, novelization, continuation, and related lineage vocabulary while keeping detailed material correspondence in adaptation mappings. It introduced `work_production_contexts` and expanded the production pack's contributor, authorization, rights-basis, commerciality, and officiality vocabulary.

The governing rule became explicit: being a parody does not prove whether a work is licensed, unlicensed, commercial, fan-made, official, tolerated, infringing, or legally protected. Those are separate claims requiring their own provenance.

## Testing After V13

Segment-level parody, territory-specific licensing, temporary streaming availability, continuity retcons, and changing production status exposed the need for one reusable scoping mechanism.

The next version needed:

- reusable applicability scopes over typed targets;
- territory and effective-time qualification;
- explicit precedence;
- scoped continuity assertions;
- claim supersession history; and
- production/right contexts attached to exact scopes rather than whole works by default.

## V14 - Scoped Narrative State

**Implemented by:** `1797afc` (`Add scoped narrative state model`)

V14 added applicability scopes, scoped continuity assertions, claim supersessions, and scope-backed production/right contexts. Scopes could target works, segments, content groups, relationships, adaptation mappings, manifestations, release components, packages, or stable claims.

Claim supersession preserved replacement, reinterpretation, restoration, and other acyclic claim histories without deleting prior provenance. Production origin, authorization, rights basis, and commerciality remained independent values applied only where their scope resolved to the owning work.

## Testing After V14

Testing found that storing scopes was not enough. Callers would otherwise rebuild containment, territory ancestry, effective-time filtering, and precedence selection differently in every tool.

The next version needed a shared applicability decision service that could:

- discover matching scopes from a typed target;
- follow only explicit containment;
- honor territory ancestry;
- distinguish broad unspecified territory from worldwide applicability;
- treat unknown timing as indeterminate;
- use explicit precedence without hidden specificity; and
- preserve tied winners as explainable ambiguity.

## V15 - Semantic Applicability Resolution

**Implemented by:** `60f707c` (`Add semantic applicability resolution`)

**Superseded assumption:** Storing applicability scopes is sufficient without shared resolution behavior.

**Architectural extraction:** Applicability resolution moved from caller-owned interpretation into paired reusable decision services with explainable outcomes.

V15 added paired Python and PowerShell applicability-decision APIs. The service discovers exact and structurally containing scopes across works, segments, content groups, manifestations, packages, release components, and provenance claims.

Territory matching uses registered ancestry. Bounded time requires a query time; unknown timing produces an indeterminate result. Explicit precedence selects winners, and equal winning precedence remains ambiguous rather than being broken by an undocumented specificity heuristic.

This completed the first major source-registry arc: creative identity, release/distribution structure, evidence, authority, provenance, scoped state, and applicability could now be represented and evaluated together.

## Testing After V15

The next wide pressure test focused on entity identity across adaptations, reboots, alternate universes, shared continuities, crossovers, recasts, regenerated characters, clones, composites, mantle holders, and similarly named subjects.

It found that works and claims were stable, but subjects themselves lacked a dedicated identity layer. The next version needed:

- stable conceptual entities;
- continuity-bound incarnations;
- multi-category membership with one primary category;
- aliases that do not masquerade as IDs;
- scope-backed incarnation appearances; and
- explicit criteria separating an incarnation from a state, role, disguise, portrayal, or graph node.

## V16 - Entity Incarnation Registry

**Implemented by:** `c84a464` (`Add entity incarnation registry contract`)

**Superseded assumption:** One conceptual entity record is sufficient across every continuity.

V16 introduced `Project_Config/entities.yaml`, paired entity loaders, and the narrative entity registry contract. It separated a conceptual entity from continuity-specific incarnations and made category membership explicit.

Incarnation bindings reused source-registry applicability scopes, allowing an incarnation's validity to be tied to exact works, segments, content groups, or claims. The LoTM registry intentionally remained empty because the framework should not invent incarnations before the project identifies a real identity distinction.

## Testing After V16

Entity tests across superhero mantles, comic reboots, alternate-universe counterparts, clones, faction splinters, adaptations, composites, and class/instance relationships found that `counterpart-of` alone was too weak.

The next version needed:

- typed entity relationships with inverse definitions;
- succession, namesake, legacy, mantle, clone, splinter, derivation, composite, inspiration, and instance relationships;
- explicit relationship basis roles where composition matters;
- crossover continuity memberships; and
- direction and cycle policies for hierarchical relationship families.

## V17 - Entity Relationship Modeling

**Implemented by:** `f54257d` (`Expand entity relationship modeling`)

V17 added typed entity and incarnation relationships, relationship-basis roles, and richer continuity membership roles. It supported distinct subjects related through succession, legacy, namesakes, mantle holding, cloning, splintering, derivation, composition, inspiration, class/instance identity, and adaptation counterpart relationships.

The design stored one canonical direction for inverse pairs while retaining symmetric relationships where the semantics genuinely are symmetric.

## Testing After V17

Adversarial identity tests found ambiguity and integrity gaps around aliases, primary taxonomy categories, reciprocal relationship definitions, and cycles. They also showed that "related" entities must not automatically become incarnations of one conceptual entity.

The next version needed:

- plural alias lookup with explicit ambiguity handling;
- rejection of aliases that collide with stable IDs;
- primary-category membership consistency;
- canonical inverse direction and acyclic relationship groups;
- stronger same-subject/continuity rules; and
- clear exclusions for disguises, titles, ordinary state changes, portrayals, designs, manifestations, and graph nodes.

## V18 - Hardened Entity Identity and Lineage

**Implemented by:** `f8accc7` (`Harden entity identity and lineage modeling`)

V18 hardened entity lookup, category validation, inverse normalization, cycle detection, relationship basis validation, and incarnation boundaries. Aliases could legitimately be shared by distinct records, so the API gained ambiguity-safe plural lookup while strict singular lookup became an explicit operation that may fail.

This version also reserved identity phases as a separate future capability rather than overloading incarnations with every persistent transformation.

## Testing After V18

Python, PowerShell 7, and Windows PowerShell 5.1 parity tests exposed that runtime-default lowercase and case-insensitive comparison do not agree for all Unicode text. A name could resolve differently depending on the implementation language or host runtime.

The next version needed:

- one deterministic Unicode normalization algorithm;
- a pinned Unicode data version;
- generated cross-runtime lookup tables and regression vectors;
- ordinal comparison after normalization; and
- a strict boundary between human-facing lookup keys and canonical IDs, schema keys, paths, or language tags.

## V19 - Deterministic Unicode Lookup Keys

**Implemented by:** `05d756b` (`Add deterministic Unicode lookup keys`)

**Superseded assumption:** Runtime-default case normalization is deterministic enough for identity lookup.

**Architectural promotion:** Semantic lookup normalization became a domain-neutral, pinned, cross-runtime framework service.

V19 added the lookup-key normalization contract, a pinned Unicode 16.0.0 data artifact, paired lookup-key tools, and shared normalization for aliases and explicitly case-insensitive semantic values.

Canonical stable IDs and schema keys remained exact machine identifiers. The lookup service performs compatibility normalization and configured case mapping, then consumers compare the resulting key ordinally. This prevents host locale or runtime case-fold behavior from changing identity resolution.

## Testing After V19

Regression vectors caught one remaining PowerShell defect: normalized keys were still compared through a case-insensitive dictionary in some paths. Commit `ba9be36` fixed this by enforcing ordinal equality and adding permanent regression vectors.

The broader test then found an architectural duplication: provenance assertions and supersession logic were embedded in the source registry even though entity, taxonomy, resource, and future page records also needed provenance. The next version therefore needed a domain-neutral, cross-registry provenance service.

## V20 - Cross-Registry Provenance

**Implemented by:** `ab60efb` (`Extract cross-registry provenance service`)

**Superseded assumption:** Provenance belongs inside the narrative source registry.

**Architectural promotion:** Provenance became a domain-neutral service over typed targets supplied by multiple registries.

V20 introduced `Project_Config/provenance.yaml`, the provenance registry contract, and paired provenance loaders. Claims and claim supersession moved out of the narrative source registry and began resolving subjects through typed target providers supplied by multiple registries.

The source registry retained evidence sources, coverage, positions, and authority services. The provenance registry became responsible for stable claims, asserted-value snapshots, field paths, evidence links, and supersession. This clarified ownership and made provenance reusable outside narrative media.

## Testing After V20

Identity testing then focused on one subject persisting through meaningful eras or transformations without becoming a new incarnation: regenerations, reincarnations, restorations, long-lived identity epochs, and other continuity-preserving changes.

The tests found that the next version needed:

- persistent identity phases below entity/incarnation identity;
- scope-backed phase appearances;
- explicit phase succession;
- provenance-addressable phase targets; and
- strong exclusions preventing every age, role, costume, pathway state, or power change from becoming a phase.

## V21 - Persistent Identity Phases

**Implemented by:** `543b14c` (`Add persistent identity phase modeling`)

V21 added identity phases to the entity registry and introduced a shared identity-target-provider contract. A phase remains the same entity or incarnation within one continuity but can carry independently meaningful chronology, relationships, claims, and projection.

Phase succession became explicit, same-subject, same-continuity, inverse-normalized, and acyclic. Scope-backed bindings connected phases to exact narrative applicability without inferring succession from labels or publication order.

## Testing After V21

The next pressure test considered what happens when stable IDs themselves are later discovered to be duplicated, wrongly split, merged, reclassified, retired, or superseded. Editing every reference in place would erase history and make external links brittle.

The tests found that the next version needed:

- a registry-independent reconciliation layer;
- redirects and successor resolution;
- merge, split, retire, present, and tombstone operations;
- aliases and superseded IDs that remain resolvable;
- typed targets across multiple registries; and
- previewable migration services rather than ad hoc repository-wide rewrites.

## V22 - Stable Identity Reconciliation

**Implemented by:** `2430d57` (`Add stable identity reconciliation framework`)

**Superseded assumption:** Aliases are sufficient to preserve every historical stable-ID change.

V22 introduced `Project_Config/reconciliation.yaml`, a reconciliation contract, paired loaders, and target-provider integration across registries. It modeled stable-ID changes as explicit operations rather than destructive renames.

Records could participate in merges, splits, retirement, presentation, tombstoning, reclassification, and deprecation while retaining audit history and resolvable old IDs. The framework also established migration services as an available capability boundary, not as a claim that automatic migration had already run.

## Testing After V22

Adversarial reconciliation tests exposed ambiguity in operational semantics and graph integrity. They covered merge chains, split branches, redirect cycles, alias collisions, unknown terminal IDs, active-record cycles, malformed audits, and contradictory lifecycle states.

The next version needed:

- deterministic terminal resolution;
- branch-aware split results;
- lifecycle/source-state validation;
- operation-specific reason and target rules;
- acyclic active and supersession graphs;
- audit requirements; and
- permanent cross-runtime fixtures for valid and invalid registries.

## V23 - Hardened Reconciliation Semantics

**Implemented by:** `0a6a6fa` (`Harden stable identity reconciliation`)

V23 tightened merge, split, retire, present, tombstone, reclassification, deprecation, and erroneous-record semantics. It added deterministic resolution behavior, cycle detection, alias-conflict checks, audit validation, and operation-specific constraints.

Paired test runners and a reconciliation fixture corpus made these rules executable in Python, PowerShell 7, and Windows PowerShell 5.1 rather than relying on prose examples.

## Testing After V23

The reconciliation fixtures passed semantically valid data but revealed that YAML parsers could disagree before domain validation even began. Duplicate keys, implicit scalar coercion, case-drifted values, timestamps, unknown fields, and malformed nested mappings could enter differently across runtimes.

The next version needed a shared strict-ingestion boundary with:

- duplicate-key rejection;
- closed mapping validation;
- canonical scalar expectations;
- exact controlled-value casing;
- timestamp validation; and
- parser and traversal budgets against pathological input.

## V24 - Strict Configuration Ingestion

**Implemented by:** `658c893` (`Harden configuration ingestion and reconciliation`)

**Superseded assumption:** Successful YAML parsing means every runtime received equivalent executable configuration.

**Architectural promotion:** Strict configuration ingestion became a shared framework boundary rather than registry-local parser behavior.

V24 introduced the strict configuration ingestion contract and paired `strict_yaml` helpers. All registry loaders began sharing a common ingestion boundary instead of depending directly on permissive runtime defaults.

The reconciliation schema advanced with stricter record, target, resolution, audit, timestamp, and controlled-value validation. The fixture corpus expanded to cover duplicate keys, unknown fields, uppercase controlled values, malformed timestamps, branch limits, and contradictory operations.

## Testing After V24

The next parser pressure test deliberately used YAML edge syntax: numeric variants, explicit tags, aliases, anchors, merge keys, document markers, leading zeros, plus signs, hexadecimal values, unquoted timestamps, out-of-range times, and oversized resolution paths.

It found that syntactically parseable YAML was still too broad for deterministic executable configuration. The next version needed a canonical YAML subset and pre-construction lexical checks so Python and PowerShell could reject the same byte sequences for the same reasons.

## V25 - Canonical Configuration Syntax

**Implemented by:** `4c1f8b4` (`Harden canonical configuration ingestion`)

V25 rejected noncanonical schema-version spellings, explicit tags, anchors, aliases, merge keys, document markers, unsupported scalar forms, and invalid timestamp variants. It added record, target, and resolution limits and propagated strict ingestion through all paired registry loaders.

Canonical integers became the only unquoted numeric form. Timestamps had to use the framework's accepted quoted representation. Unknown keys in closed mappings and unsupported schema versions became hard errors.

## Testing After V25

Byte-oriented tests then found cases that parser-level validation could miss or normalize away: UTF byte-order marks, malformed UTF-8, alternate null spellings, empty values, trailing-decimal forms, negative and exponent variants, and files large enough to exhaust parser budgets before structural validation.

The next version needed byte-level preflight before YAML parsing and canonical null/decimal handling shared by both runtimes.

## V26 - Byte-Level Ingestion Hardening

**Implemented by:** `5da44b3` (`Harden byte-level configuration ingestion`)

V26 added UTF-8-without-BOM enforcement, byte-budget validation, and lexical rejection for empty or alternate null forms and noncanonical decimal-like scalars. Strict ingestion now starts from bytes rather than trusting text already decoded or normalized by a host command.

The reconciliation fixture suite gained permanent cases for tilde null, empty null, trailing decimals, negative trailing decimals, and exponent variants.

## Testing After V26

The next adversarial test moved from values to mapping keys. YAML permits booleans, integers, complex nodes, Unicode text, punctuation, empty strings, duplicate keys, and case variants as keys, but executable registry schemas require deterministic machine names.

The tests found that the next version needed:

- string-only mapping keys;
- a canonical lowercase key alphabet;
- duplicate and case-collision rejection before dictionary construction;
- no Unicode or punctuation outside the approved machine-key set; and
- one reusable fixture corpus independent of any one registry.

## V27 - Canonical Mapping Keys

**Implemented by:** `dc41692` (`Enforce canonical configuration mapping keys`)

V27 required nonempty lowercase mapping keys composed only of letters, digits, `_`, `-`, or `.`. It rejects boolean, integer, complex, uppercase, Unicode, punctuation-bearing, empty, duplicate, and case-colliding keys before ordinary mapping construction can hide the problem.

The strict-YAML fixtures moved into their own reusable framework data area and all paired loaders inherited the same key contract.

## Testing After V27

With identity, evidence, scope, and ingestion stabilized, cross-domain tests exposed duplicated temporal logic across source coverage, applicability scopes, localized titles, releases, offerings, provenance, reconciliation audits, IT maintenance windows, and legal effective periods.

The next version needed a domain-neutral temporal kernel that could represent:

- exact and reduced-precision civil timestamps;
- bounded and unbounded intervals;
- inclusive boundary semantics;
- explicit unknown time distinct from omission;
- ordering and overlap; and
- one normalization path shared by every registry and runtime.

## V28 - Shared Temporal Modeling Kernel

**Implemented by:** `0a9b708` (`Add shared temporal modeling kernel`)

**Superseded assumption:** Each registry can safely define its own temporal semantics.

**Architectural promotion:** Civil-time window semantics moved from source-specific handling into the core framework.

V28 introduced the temporal-model contract, paired temporal tools, and permanent valid/invalid window fixtures. Temporal normalization moved out of source-specific code and became a core framework service used by source and provenance registries.

The kernel supported exact timestamps, reduced precision, intervals, explicit unknown values, open bounds, inclusive endpoints, comparison, and overlap. Narrative distribution retained narrative-specific vocabulary while consuming the shared temporal mechanics.

## Testing After V28

Pressure tests across publication dates, streaming windows, licenses, legal effective dates, medical intervals, audit records, certificate validity, and maintenance periods found that storage validation was not enough. Query behavior around partial dates, certainty, complete units, and open intervals remained underspecified.

The next version needed:

- normalized query windows;
- complete-unit expansion for year, month, day, and week precision;
- certainty-aware inclusion and indeterminate outcomes;
- exact known/unknown boundary semantics;
- consistent overlap decisions; and
- six-digit fractional-second parity.

## V29 - Temporal Query and Boundary Semantics

**Implemented by:** `f9a9354` (`Harden temporal query and boundary semantics`)

**Superseded assumption:** A reduced-precision date represents one instant.

V29 added reusable query-window normalization and certainty-aware temporal evaluation. Reduced-precision values can represent complete civil units rather than accidental single instants, and query results distinguish definite matches, definite exclusions, and indeterminate outcomes.

The implementation hardened known versus unknown bounds, open intervals, inclusive/exclusive behavior, overlap logic, calendar limits from year 0001 through 9999, and microsecond precision. Python, PowerShell 7, and Windows PowerShell 5.1 share the same valid-window, invalid-window, query, and overlap vectors.

## Testing After V29

The V29 regression suites remained cross-runtime equivalent. The established suite covered 17 valid windows, 18 malformed rejections, 20 query vectors, 12 overlap vectors, the 1,500-step reconciliation chain, and QA exporter parity.

The subsequent adversarial test found two correctness defects shared by both implementations:

1. `-00:00` is accepted as a known UTC-normalizable offset even though RFC 3339 uses it to communicate that the local offset is unknown. The strict absolute timestamp profile must reject it or preserve its uncertainty; it must not silently become ordinary UTC.
2. An interval strictly after exact year `9999`, or strictly before exact year `0001`, is accepted even though it contains no representable civil instant inside the framework's supported range. Such exclusive-extrema intervals must be rejected as empty.

The broader chronology pressure test used Star Wars BBY/ABY, Middle-earth Ages, Gundam Universal Century, Star Trek stardates, far-future space settings, named epochs, event-relative dating, alternate timelines, branching comics, and LoTM's Epochs. It found that civil time is only one coordinate system.

V30 should therefore begin by closing the two V29 defects and making capability ownership honest, then add a layered chronology model:

- **Core framework:** coordinate systems, arbitrary signed or nonnegative coordinates, year-zero policy, positions, intervals, ordering relations, mappings/anchors, certainty, and partial/incomparable order.
- **Narrative-media pack:** story chronology, continuity and branch bindings, flashbacks, time travel, alternate timelines, and separation of story order from reader disclosure and publication/release order.
- **LoTM project instance:** the actual Epoch names, labels, known ordering rules, calendar behavior, and source-backed anchors.
- **Content records:** concrete positions and provenance.

Causal relationships must remain separate from strict chronological order so time loops do not force invalid ordering cycles. Coordinate systems must not be compared without an explicit mapping, and the framework must support multiple axes and genuinely incomparable positions rather than pretending every timeline forms one total order.

## V30 - Layered Chronology Foundations

**Implemented by:** `efc82f9` (`Add layered chronology foundations`)

**Superseded assumption:** Civil timestamps can represent every meaningful chronology.

**Architectural promotion:** General chronology coordinates and comparison became core framework services, while story-time roles remained a narrative-domain extension and LoTM Epochs remained project-instance data.

V30 first closed the two defects found after V29. Strict RFC 3339 ingestion now rejects `-00:00` rather than silently treating an unknown local offset as UTC, and temporal windows reject exclusive bounds that lie beyond the representable calendar at exact year 0001 or 9999.

It then separated civil effective time from general chronology. The core pack now owns chronology coordinate kinds, integer value domains, ascending and descending directions, zero policies, relation kinds, and mapping kinds. The narrative-media pack adds story-time roles without placing fictional Epoch names or LoTM works in reusable vocabulary. The LoTM project registry instantiates its First through Fifth Epochs and binds that axis to the main novel continuity, but deliberately records no concrete dates or anchors that current evidence does not establish.

Paired Python and PowerShell loaders now validate calendar, era-ordinal, ordinal, and relative axes; era-local direction; positions; open or bounded spans; explicit ordering relations; direct exact mappings; relative-origin cycles; and narrative work, continuity, and branch contexts. Comparison returns `before`, `after`, `concurrent`, or `incomparable` and refuses to manufacture conversions between unrelated axes. Civil timestamps, story chronology, causal order, publication/release order, and reader disclosure remain distinct.

Implementation conformance initially covered negative years, year 12000, BCE/BBY-style descending era values, ascending eras on the same axis, global countdown coordinates, relative origins, direct equivalence, incomparable systems, valid spans, reversed spans, contradictory and duplicate exact relations, exact order cycles, duplicate era ordinals, unknown narrative targets, and relative-origin cycles. V31 later expanded this baseline to thirteen comparison vectors and thirteen malformed chronology registries by adding transitive equivalence/order and combined-graph contradictions.

The temporal suite also grew permanent `-00:00` and exclusive calendar-extrema cases. Its 17 valid windows, 21 malformed windows, 20 query vectors, and 12 overlap vectors remain equivalent across all three runtimes.

Formula-based calendar transformations, uncertain multi-anchor reconciliation, concrete event/content positions with provenance, and richer branch topology are intentionally outside V30. The post-V30 pressure test must determine which of those or other gaps actually justify V31 before its scope is selected.

## Testing After V30

The V30 conformance baseline remained equivalent across Python, PowerShell 7, and Windows PowerShell 5.1: eleven comparison vectors and eleven malformed chronology registries passed in every runtime. The broader pressure test then combined ordinary chronology systems with closed causal loops, reset loops, mutable and branching timelines, nested loops, changing reset points, staggered participant awareness, partial escape, temporal duplicates, and repeated occurrences at one world coordinate. Non-narrative cases included IT retries and rollbacks, distributed execution order, recurring medical episodes, periodic legal obligations, workflow cycles, and repeated scientific trials.

The model handled its intended boundary correctly in several important ways. Separate world and traveler axes represented a backward jump while preserving forward subjective experience; unrelated axes remained incomparable; uncertain conflicting order claims did not become exact order; and an explicit exact `A before B before C before A` chronology was rejected. Negative years, year 12000, mixed-direction eras, relative origins, descending counters, spans, and direct mappings remained valid under the established fixtures.

### Correctness Defects

The executable probes found two defects in V30's exact-order consistency rather than merely absent time-loop features:

1. Intrinsic same-axis order and explicit cross-axis order are validated separately. A configuration containing intrinsic `A1 before A2` plus explicit `A2 before B` and `B before A1` currently loads even though the combined exact order is cyclic.
2. Exact relationships and equivalence mappings are interpreted only one hop at a time. `A equivalent B`, `B equivalent C`, and `A before C` can coexist, while comparison of `A` and `C` without the direct relation remains `incomparable`. Exact equivalence and exact precedence therefore lack the closure needed to detect transitive contradictions and answer derived order consistently.

V31 must close those defects before building higher-level recurrence behavior. Exact chronology must validate one combined graph containing intrinsic coordinate order, relative-origin equivalence, exact mappings, and explicit exact relations without turning uncertain claims into exact edges.

### Missing Capabilities

Time loops demonstrated that chronology coordinates are necessary but not sufficient. V30 has no executable representation for:

- a recurring event template versus distinct occurrence instances;
- an occurrence bound to a world coordinate, loop iteration, branch, and participant track;
- a stable recurrence region, ordered iteration identities, or nested iterations;
- jump, reset, exit, fork, or merge transitions;
- causal relationships that may legitimately cycle without becoming chronological order;
- typed state carryover across reset boundaries;
- participant experience, observation, awareness, or retained memory;
- reset and termination conditions, changing reset points, or partial participant escape;
- referential branch topology beyond an opaque `branch_id`; or
- position-scoped time-travel origin/destination roles rather than axis-wide context labels.

The test also confirmed that V30 deliberately accepts only scalar integer coordinates. Vector clocks and cyclic phase coordinates require separate reviewed contracts; recurrence must not be simulated by weakening strict chronological order or by making one coordinate position stand for several occurrence identities.

### V31 Recommendation

V31 should be **Occurrence and Recurrence Foundations**. Core should gain occurrence-template and occurrence-instance identity, multi-axis coordinate bindings, recurrence and iteration identity, non-chronological transitions, cycle-permitting causal edges, typed carryover, perspective/observation tracks, minimal branch topology, and provenance-addressable query services. The chronology registry should remain the acyclic coordinate and order service consumed by that new layer.

The narrative-media pack should specialize those primitives with time-loop roles, subjective participant histories, awareness, retained memory or knowledge, reset rules, escape conditions, and story-presentation semantics. Project data should own concrete loops, iterations, participants, occurrences, and source-backed claims; the LoTM instance should remain empty until verified material requires one.

V31's acceptance test must answer both "what happened during iteration 7?" and "what did this participant experience immediately before iteration 7 began?" without introducing a chronological cycle. It must also distinguish two occurrences at one world coordinate, permit cyclic causality while rejecting cyclic chronology, support nested loops and staggered awareness, allow one participant to escape while another remains, and let non-narrative projects use recurrence primitives without enabling narrative semantics.

## V31 - Occurrence and Recurrence Foundations

**Implemented by:** `5f7efbb` (`Add occurrence and recurrence foundations`)

**Superseded assumption:** A chronology position and an occurrence at that position can share one identity.

**Architectural promotion:** Occurrence identity, recurrence structure, branch topology, perspective tracks, transitions, causal edges, and typed carryover became core framework services; narrative time-loop and subjective-experience semantics remain in the narrative-media pack.

V31 first repaired the two exact-order defects exposed after V30. The chronology services now collapse exact relative origins, equivalent mappings, and concurrent relations into transitive equivalence classes, then validate intrinsic coordinate order and explicit exact precedence as one combined graph. Comparisons use that closure, so transitive order is answerable and a contradiction cannot hide across coordinate-system boundaries. The permanent chronology corpus now contains thirteen comparison vectors and thirteen malformed registries in every supported runtime.

The new schema-1 occurrence registry composes chronology without weakening it. Stable records represent branches, repeatable templates, recurrence structures, ordered iterations, concrete occurrence identities, chronology-position bindings, subject tracks, transitions, causal relations, and carryover. Branch and recurrence topology remains acyclic; iteration ordinals are unique; nested recurrences identify their parent iteration; reset transitions and carryover advance within one recurrence. Causal edges deliberately permit cycles because they never become chronological `before` edges.

The core pack now owns generic occurrence/recurrence kinds and services. The narrative-media pack adds time loops, subjective experience, time-travel jumps, loop reset/escape, and memory, knowledge, physical-state, and awareness carryover. The LoTM project registry activates only its `main` branch and adds no unverified loop or occurrence data.

Paired query APIs answer occurrence membership by iteration, every occurrence bound to one chronology position, previous and next experience on a track, carryover into an iteration, and recurrence identity for an occurrence. Stable occurrence records are also composed into centralized provenance targeting rather than gaining a second assertion system.

The portable fixture proves that three wakes can occupy the same world-time coordinate while remaining distinct occurrences on forward subjective tracks. One participant carries memory and knowledge and exits the loop; another remains on a shorter track without that carryover or escape transition. It also exercises nested recurrence, branch exit, a permitted causal cycle, and eleven malformed mutations. Ten query groups and all eleven rejection cases pass identically in Python, PowerShell 7, and Windows PowerShell 5.1.

The V31 tooling audit also standardized structured conformance summaries. Chronology, occurrence, temporal, and reconciliation now all preserve their default human-readable output while exposing matching `--json` / `-Json` fields in Python, PowerShell 7, and Windows PowerShell 5.1.

## Testing After V31

The V31 baseline passed identically in Python, PowerShell 7, and Windows PowerShell 5.1: ten occurrence query groups and eleven malformed occurrence registries, thirteen chronology comparisons and thirteen malformed chronology registries, twenty temporal-match and twelve overlap vectors with twenty-one malformed windows, and eight reconciliation vectors with forty malformed registries. The structured JSON summaries also remained identical across all three runtimes.

The broader pressure test covered fixed and changing-reset-point loops, nested loops, staggered participant awareness, partial escape, retained and lost memory, backward world-time travel with forward subjective experience, branch forks and merges, causal cycles, temporal duplicates, and multiple incarnations at one coordinate. Representative narrative patterns included *Groundhog Day*, *Edge of Tomorrow*, *Re:Zero*, *Steins;Gate*, *Dark*, *Primer*, *Tenet*, *Russian Doll*, branching superhero continuities, and alternate-world-line stories. Non-narrative probes included IT retries and rollbacks, distributed process tracks, recurring medical episodes, periodic legal obligations, workflow cycles, and repeated scientific trials.

The central V31 separation held. Distinct occurrences can occupy one world coordinate without sharing identity; chronology remains acyclic while causality may cycle; nested recurrences and participant-specific tracks remain representable; and one participant can leave a loop without forcing every observer onto the escape track. An executable seven-iteration probe answered both which occurrence belongs to iteration seven and which occurrence the participant experienced immediately before it began. A synthetic 1,500-level recurrence hierarchy also loaded successfully, showing no immediate Python scalability failure in the parent-topology validator.

### Correctness Defects

The adversarial probes found four classes of records that V31 accepts even though their declared semantics conflict:

1. One occurrence may have two exact `primary` bindings whose chronology positions are known to be ordered rather than concurrent. Multiple coordinate bindings are valid, but comparable exact primary bindings for one happening cannot contradict each other.
2. A transition may name a track containing both endpoints while pointing backward in that track's declared order. World chronology may move backward during time travel, but a transition attached to a subjective or execution track must still follow that track's direction.
3. Specialized transitions validate unevenly. Reset transitions enforce recurrence membership and forward iteration order, while a `loop-escape` can claim an unrelated recurrence and generic `exit`, `fork`, `merge`, or jump records have no kind-specific endpoint rules.
4. Carryover may be assigned to a track that has no occurrence in either the source or target iteration. It also identifies only a broad kind such as memory or state, so two differently named records can make indistinguishable claims without identifying what actually crossed the boundary.

### Under-Specified Semantics

The test deliberately did not classify every accepted edge case as universally invalid. A child-branch occurrence can currently bind before its named fork occurrence, but retroactive time travel and branch reinterpretation make a blanket chronology rejection unsafe. Iteration statuses can also appear in surprising combinations, but parallel or incompletely observed processes may legitimately prevent one global lifecycle rule. Both need explicit policy rather than assumptions hidden in the loader.

V31 also enumerates concrete recurrence iterations but does not describe a recurrence rule, trigger, expected cadence, reset condition, termination condition, or changing reset-point phase. It has no separate recurrence-template identity for several concrete executions of the same retry or loop pattern. Occurrence outcomes and carryover payloads are not modeled, and nested recurrence invocations are inferred only from each child iteration's parent. These omissions limit periodic legal duties, medical episodes, scheduled jobs, retry policies, changing-save-point stories, and detailed retained-state analysis even though their concrete occurrences can already be listed.

Vector clocks and distributed happens-before queries remain outside the chronology and occurrence contracts. Track order and causal relations can preserve known process observations, but they should not be presented as a substitute for a reviewed partial-order or vector-clock model.

### V32 Recommendation

V32 should be **Occurrence Integrity and Transition Semantics**. It should close the four correctness defects before expanding recurrence authoring: validate coherent exact primary bindings, require track-attached transitions to follow track order, define kind-specific reset/exit/fork/merge/jump endpoint profiles, and make carryover prove track participation while identifying a typed payload or provenance-addressable state target. Branch lineage checks should use explicit transition semantics so retroactive branches are supported intentionally rather than accepted accidentally. Semantic duplicate detection and deterministic iteration-plus-track boundary queries should be added to the portable corpus.

Recurrence schedules, expression languages for reset or termination conditions, outcome taxonomies, recurrence-template versus execution identity, and distributed vector-clock semantics should remain candidates for later versions. V32 should establish trustworthy occurrence edges and state transfer first, giving those later capabilities a reliable substrate.

## V32 - Occurrence Integrity and Transition Semantics

**Implemented by:** `abe8e8c` (`Enforce occurrence transition integrity`)

**Superseded assumption:** A domain transition kind and broad carryover kind provide enough information to validate occurrence edges and retained state.

**Architectural promotion:** Transition profiles, coherent multi-coordinate occurrence identity, explicit branch-lineage edges, and payload-bearing carryover became core framework semantics independent of domain vocabulary.

V32 upgrades the occurrence registry to schema 2. An occurrence may still bind multiple chronology systems, including incomparable world and subjective coordinates, but duplicate semantic bindings are rejected and exact primary positions cannot be known ordered. This preserves legitimate multi-axis identity without allowing one happening to occupy two contradictory exact positions.

Transitions now separate extensible `transition_kind` vocabulary from a core `transition_profile`. The core pack defines ordered, jump, recurrence-advance, recurrence-exit, branch-fork, and branch-merge profiles, while each pack registers which profiles its transition kinds may use. Track-attached transitions must move forward in declared track order; recurrence profiles prove their endpoint scope and direction; branch-fork profiles must match the parent branch's named fork occurrence; and every child branch has exactly one explicit matching fork transition. This supports a retroactive time-travel branch through an explicit forward subjective transition without pretending its world coordinates are chronologically forward.

Carryover now proves that its track participates in both source and target iterations and identifies an exact stable payload through `payload_target_type` and `payload_target_id`. Internal occurrence-registry targets and caller-supplied stable providers can serve as payloads. Semantic duplicate bindings, transitions, and carryover records are rejected so changing IDs cannot disguise duplicate structure; provenance remains the owner of competing evidence or certainty changes.

Paired queries add iteration membership in track order plus previous-before-iteration and next-after-iteration boundaries. The portable fixture exercises all six transition profiles, coherent incomparable primary bindings, explicit branch fork and merge, internal and externally supplied payload targets, nested recurrence, partial escape, repeated coordinates, and cyclic causality. Eighteen query assertions and twenty-seven malformed mutations pass identically in Python, PowerShell 7, and Windows PowerShell 5.1.

The core pack advances to version 23, narrative media advances to version 18 with a core-23 dependency, and the empty LoTM occurrence registry advances to schema 2 without fabricating project events. Recurrence schedules, condition-expression languages, outcome taxonomies, recurrence-template versus execution identity, and distributed vector clocks remain deliberately outside V32.

## Testing After V32

### LoTM Abandoned-Temple Loop

The first V32 test used a source-verified Lord of Mysteries time loop rather than a synthetic pattern. EPUB Chapters 457-458 introduce the City of Silver expedition's encounter with the outsider child Jack and show Colin Iliad defeating him before the party awakens back at its camp. Chapter 460 establishes that this has happened five times with small variations. Derrick does not become aware after the first iteration: when the Tarot gathering draws him above the gray fog, an external force restores the memories of all five completed explorations. Derrick attributes the restoration to Mr. Fool, but Klein is initially surprised by it. Chapters 465-467 cover the deliberately altered sixth pass. Derrick tests possible trigger points, recognizes the cyclic-river and Angel of Fate clues, helps Colin identify the anomalous face on Jack as the loop's anchor, and experiences the cycle breaking when Colin destroys that face. Jack survives the sixth pass; the other expedition members show no immediate awareness of the repeated lives.

A temporary schema-2 probe instantiated six distinct iterations, thirty-two concrete occurrences, Derrick and Colin tracks, five recurrence-advance resets, an externally caused memory-restoration occurrence, five restored-memory payloads entering the sixth iteration, the clue and anchor-destruction causal chain, and a recurrence-exit transition. The V32 Python loader accepted the scenario and correctly answered sixth-iteration membership, Derrick's previous experience at the iteration boundary, Colin's exclusion from Derrick's restoration occurrence, and all five memory payloads entering the final pass. No chronological cycle was introduced.

The test therefore passes V32's structural contract: repeated events retain separate identity, one participant can acquire cross-iteration knowledge without granting it to everyone, subjective order remains forward while the expedition resets, and destroying the anchor can lead to a typed loop exit.

It also exposes two semantic limits rather than V32 integrity defects:

1. `carryovers` can identify the exact memories available in iteration six, but cannot distinguish continuous retention across a reset from memories that were absent and later restored by an external occurrence. The restoration occurrence and causal edge preserve the concrete history, but the acquisition mode and activation point are not first-class carryover semantics.
2. Concrete reset and escape transitions can record what happened, but the registry still cannot declare the governing rule: Colin killing Jack ended each failed pass, while destroying the anomalous face ended the recurrence and allowed Jack to survive. Reset triggers, termination conditions, and typed occurrence outcomes remain outside schema 2.

### Broad Cross-Domain Pressure Test

The full V32 pass retained the LoTM case and widened the test chamber across narrative and non-narrative recurrence. Narrative patterns included continuously remembered loops, delayed awareness, staggered participant entry, partial escape, changing reset points, nested loops, branching world lines, backward world-time jumps, repeated coordinates, and causal cycles. The model was compared against the structural demands of *Groundhog Day*, *Edge of Tomorrow*, *Re:Zero*, *Steins;Gate*, *Dark*, *Primer*, *Russian Doll*, *Palm Springs*, *Outer Wilds*, and the source-verified LoTM abandoned-temple loop. Non-narrative executable probes covered deployment retries, recurring medical observations, twelve-period legal obligations, nested process exit, retained configuration or clinical context, rollback-like jumps, repeated experiments, and partial workflow completion.

The intended V32 separations held. Distinct attempts and episodes remain distinct occurrences even when coordinates repeat; participant, observer, and execution tracks can diverge; inner recurrences can exit into their parent iteration; partial escape and branch transitions do not alter acyclic chronology; exact payload targets support configuration, clinical context, memory, knowledge, and physical state; and causal cycles remain isolated from chronological comparison. A generated registry with 750 iterations, 750 occurrences, 749 reset transitions, and 749 payload-bearing carryovers loaded and answered its final boundary query in approximately 0.14 seconds in Python.

The permanent baselines remained identical in Python, PowerShell 7, and Windows PowerShell 5.1: eighteen occurrence query assertions, twenty-seven malformed occurrence registries, thirteen chronology comparisons, and thirteen malformed chronology registries all passed. Nine additional adversarial mutations were then run in all three runtimes, and all three implementations accepted the same nine cases. Runtime parity therefore held; the acceptances are shared schema-2 behavior.

### Remaining Correctness Defects

The adversarial probes found five integrity classes that V32 does not yet close:

1. `ordered` and `jump` transitions can point from an occurrence back to the identical occurrence when `track_ids` is empty. A concrete transition must connect distinct occurrence identities even though a causal self-edge may remain meaningful.
2. An `ordered` transition can move from an exactly later chronology position to an exactly earlier one. This is accepted both without a track and with a track arranged in the same backward order. Track order currently validates only internal list direction; it does not prove that an `ordered` profile is chronologically ordered or force backward movement to use `jump`.
3. A recurrence-exit transition for an outer recurrence can target an iteration of that recurrence's nested descendant. The direct recurrence IDs differ, but the target has not actually left the outer recurrence's containment hierarchy. Exiting an inner recurrence into its parent remains valid and passed separately.
4. A semantically identical causal relation can be repeated under another stable ID. Transitions and carryovers already reject this disguise; causal structure should follow the same identity rule while provenance owns competing evidence and certainty.
5. A track can reverse or interleave iterations of the same recurrence. One accepted track ordered iteration two before iteration one; another placed the first occurrence of iteration two between two occurrences of iteration one. In the latter case, `next_after_iteration` skipped the already-interleaved occurrence and returned a later one, proving that the boundary query's answer can be structurally false. Same-recurrence iteration order must be monotonic and each iteration's direct track segment must be contiguous, while nested child recurrence segments must remain legal inside a parent iteration.

### Deferred Semantic Limits

The pressure test also confirmed capability gaps that were deliberately outside V32 rather than defects in its implemented claims:

- Carryover cannot distinguish continuously retained state from state that was lost, externally restored, transferred, reconstructed, or activated partway through a later iteration.
- This is not fundamentally a chronology problem. It is a reusable state-availability and knowledge-acquisition problem. A subject may encounter a payload without knowing it, lose access to previously available state, or acquire knowledge continuously, suddenly, externally, partially, conditionally, by inference, through merged memories, through dreams or prophecy, or after timeline reconciliation. Occurrence order and iteration carryover alone cannot answer what the subject knew, believed, suspected, remembered, or could access at a particular occurrence.
- Concrete transitions cannot declare recurrence rules, reset triggers, termination conditions, changing reset points, or typed outcomes such as Jack dying in failed passes and surviving the escape pass.
- An iteration marked `terminated` can be followed by later iterations. This was already identified after V31 as under-specified lifecycle policy; it should be resolved with recurrence rule and execution semantics rather than by assigning hidden meaning to one status value.
- Recurrence definitions still conflate a reusable recurrence pattern with one concrete execution, and branch merges identify directed convergence edges without defining a new multi-parent branch identity.
- Descendant-inclusive nested-iteration boundary queries, distributed vector clocks, and domain-specific condition-expression languages remain separate reviewed capabilities.

### V33 Recommendation

V33 should be **Recurrence Rules and State Acquisition Semantics** while also closing the five remaining V32 integrity defects. State availability and acquisition should become a reusable core capability composed with occurrences and recurrences, not extra loop-only fields on `carryovers`. Core should identify the subject, exact payload, prior and resulting availability or epistemic state, acquisition/change kind, activation occurrence, completeness or scope, and optional typed condition. Generic change kinds should cover acquisition, retention, loss, restoration, transfer, merge, derivation, activation, and invalidation. Carryover then becomes one way availability persists across an iteration boundary rather than a substitute for every state transition.

Domain packs should specialize the core vocabulary without redefining the mechanism. Narrative media can add recovered memory, revelation, prophecy, dream acquisition, merged memories, supernatural bestowal, and timeline-collapse reconciliation. IT can use configuration restoration, synchronization, cache hydration, credential acquisition, and operator notification; medical and legal packs can use diagnosis revision, evidence discovery, testimony, record correction, and conditional disclosure. Provenance must continue to own whether the payload or acquisition claim is verified, inferred, disputed, or superseded, while the new capability owns what state changed for which subject and when.

Alongside that promotion, V33 should define recurrence pattern versus execution identity; model reset and termination rules through typed, provenance-addressable conditions and effects rather than an unrestricted expression language; add typed occurrence outcomes and coherent iteration lifecycle; enforce distinct transition endpoints, chronology-aware ordered profiles, recurrence-containment exits, causal semantic identity, and monotonic contiguous same-recurrence track segments; and preserve legal nested segments, time-travel jumps, causal cycles, partial escape, and sparse observations.

V33 acceptance should replay every permanent V32 vector plus all nine adversarial mutations, the LoTM six-pass restoration case, continuously retained-memory loops, changing-checkpoint loops, partial participant escape, IT retry exhaustion, medical recurrence with later evidence restoration, and legal obligations with explicit cadence and termination. For the LoTM case it must answer what Derrick knew during passes one through five, when the five-pass memory set became available, how that acquisition differed from uninterrupted retention, and why Colin did not gain the same awareness. More generally, the model must answer both experience-boundary and state-availability questions without introducing a chronological cycle, equating experience with knowledge, mistaking externally restored knowledge for uninterrupted memory, or confusing a subject's belief with the payload's provenance-backed truth status.

## V33 - Recurrence Rules and State Acquisition Semantics

**Implemented by:** `433e5d1` (`Add recurrence rules and state acquisition`)

**Superseded assumption:** Carryover can serve as the primary record of memory, knowledge, configuration, or other state merely by naming a kind and payload at an iteration boundary.

**Architectural promotion:** Subject-state availability and acquisition became a reusable core capability. Narrative memory, dream, prophecy, revelation, and timeline-reconciliation mechanisms specialize that service rather than defining a loop-only state model.

V33 upgrades the occurrence registry to schema 3 and closes the five integrity classes found after V32. Transitions must connect distinct occurrences. Ordered transitions require forward track, recurrence-ordinal, or exact chronology evidence and reject known backward chronology. Recurrence exit uses descendant-aware containment, causal relations reject semantic duplicates, and each track's direct occurrences move monotonically through a recurrence's iterations without prohibiting nested child-recurrence segments. Recurrence and iteration lifecycle are now validated together.

Recurrence identity is split into reusable `recurrence_patterns` and concrete `recurrences`. Typed occurrence outcomes record what happened to a subject. Pattern-owned rules combine a bounded `all` or `any` condition list with typed effects for iteration advance, recurrence termination, reset-point change, or state activation. This deliberately avoids an unrestricted expression language while making reset and escape behavior addressable, extensible through packs, and available to provenance.

State change is no longer hidden inside carryover. A `state_transition` identifies the subject, exact payload, generic state and change types, structural change profile, acquisition mechanism, prior and resulting availability, optional epistemic attitude, completeness, activation occurrence, optional governing rule, tracks, typed source targets, and certainty. Structural profiles distinguish acquisition, preservation, removal, restoration, supply, combination, derivation, activation, and invalidation. Same-payload state chains on one track must be continuous. Encounter and experience do not imply awareness or knowledge, and subjective belief remains separate from provenance-backed truth.

Carryover now references a concrete state transition. Validation proves that the state applies to the subject track, activates by the end of the source iteration, remains applicable until the target iteration begins, and crosses increasing iterations of one recurrence. This makes continuously retained memory structurally different from memory restored by an external event in a later pass.

The core pack advances to version 24 with `recurrence-rule-modeling` and `state-availability-acquisition`. Narrative media advances to version 19 with typed narrative outcomes, memory/knowledge/awareness/belief/physical-state kinds, and recovered-memory, dream, prophecy, revelation, supernatural-bestowal, and timeline-reconciliation mechanisms. Outcomes, rules, and state transitions join centralized provenance targeting; evidence and claim authority remain outside the occurrence registry.

Paired Python and native PowerShell services add outcome-by-occurrence, rule-by-pattern, state-by-subject, and state-at-track-boundary queries. The portable fixture now performs 26 behavioral assertions and rejects 47 malformed registries in Python, PowerShell 7, and Windows PowerShell 5.1. The empty LoTM project registry moves to schema 3 without fabricating concrete loop records.

## Testing After V33

### Permanent Baseline

The V33 occurrence corpus passed identically in Python, PowerShell 7, and Windows PowerShell 5.1: 26 behavioral query assertions and 47 malformed registries. The retained chronology, temporal, and reconciliation suites also remained green in all three runtimes. Python and PowerShell provenance composition accepted the new recurrence-pattern, outcome, rule, and state-transition provider types. No regression appeared in exact chronology, branch topology, transition profiles, lifecycle, track order, state-chain continuity, or carryover applicability.

### Source-Grounded LoTM Loop

The first dedicated pressure scenario returned to the source-verified City of Silver abandoned-temple loop from Chapters 457-467. It instantiated six passes, fourteen representative occurrences, Derrick and Colin subjective tracks, Jack's deaths in the five failed passes, the interstitial gray-fog restoration, destruction of the anomalous face, Jack's survival in the final pass, five reset transitions, an exit, reset and termination rules, and an exact memory payload representing the first five explorations.

V33 represented the distinction that V32 could not. Derrick's five-pass memory state was explicitly unavailable through the end of pass five, became available at the gray-fog restoration occurrence, and remained available when pass six began. The previous occurrence before Derrick's sixth iteration was correctly returned as the restoration event. Colin's state remained unavailable at pass six because his track had no matching acquisition. The scenario required zero carryover records: the knowledge was acquired between iterations rather than continuously retained across the fifth reset. A separate continuously remembered three-pass loop used one acquisition plus two carryovers and returned available memory in pass three. The two histories are therefore no longer structurally conflated.

### Broad Executable Scenarios

The executable pressure harness also covered:

- changing checkpoints, with old and new reset-template effects represented behind different state conditions;
- nested recurrence and partial escape, preserving the inner-iteration boundary query while asserting an exit only on the escaping participant's track;
- IT retry exhaustion, where retry-budget state changed from available to unavailable on the third failed attempt;
- medical evidence that progressed unavailable, available, inaccessible, then restored across four recurring visits;
- twelve concrete legal-obligation periods with typed completion outcomes; and
- a 1,000-iteration recurrence, which loaded and answered its final membership query in approximately 0.005-0.007 seconds in Python.

These tests confirm that occurrence identity, pattern/execution separation, lifecycle, typed outcomes, subject-specific state histories, acquisition mechanisms, carryover, nested recurrence, and partial tracks compose cleanly across narrative and non-narrative domains. Dream, prophecy, merged-memory, timeline-reconciliation, and other pack mechanisms use the same validated state-transition structure; they do not require separate chronology primitives.

### Rule-Semantics Boundary

The pressure test found no new chronology or state-chain integrity defect. It did expose that V33's recurrence rules are validated declarative records, not yet an executable policy service:

1. A `state-availability` condition identifies a payload and expected availability but not the subject, state kind, track, or boundary at which availability should be tested. Different subjects can hold different states for the same payload, as Derrick and Colin do, so the condition is not independently evaluable.
2. An `occurrence-outcome` condition identifies a template and outcome kind but not the outcome subject. A generic template can produce outcomes for several participants.
3. Rules have no execution, branch, phase, iteration-range, or effective-window applicability. Changing-checkpoint rules can both be represented, but the registry cannot state that one governs before the checkpoint shift and the other after it except through conditions a future evaluator must interpret.
4. Rules have no priority, exclusivity, conflict detection, or deterministic resolution trace. The IT scenario's final failed attempt simultaneously matches the generic advance-on-failure rule and the terminate-on-exhausted-budget rule. Two rules with the same condition and incompatible effects also load successfully.
5. Legal periods can be enumerated, but cadence, due-window, attempt count, ordinal threshold, and maximum-retry policy are not first-class rule operands. The legal scenario therefore proved occurrence history, not an explicit monthly recurrence policy.
6. Outcome combinations have no pack-defined compatibility policy. The model accepts `died` and `escaped` for one subject at one occurrence. Some narrative settings make that combination meaningful, so incompatibility must be domain-scoped rather than a universal hard-coded rule.

These are limitations in rule applicability and evaluation, not reasons to weaken V33's occurrence, chronology, or state model. Provenance still correctly owns whether each rule, outcome, or state claim is supported; it should not be repurposed as the rule engine.

### V34 Recommendation

V34 should be **Scoped Recurrence Policy and Deterministic Rule Evaluation**. It should make each condition independently evaluable by adding typed subject and boundary selectors to state conditions and subject selectors to outcome conditions. Rules should gain explicit applicability over patterns, concrete executions, branches, phases, and iteration or temporal windows, with project or execution overrides layered over pattern defaults.

Core should provide deterministic matching, priority or exclusivity policy, incompatible-effect detection, and an explainable evaluation result that reports considered rules, matched conditions, selected effects, and rejected conflicts. Bounded predicates should cover iteration ordinal/count, maximum attempts, and composition with chronology or civil-time windows; cadence should remain a typed schedule policy rather than an unrestricted expression language. Domain packs should register outcome compatibility groups and specialized condition/effect vocabulary.

V34 acceptance should evaluate the Derrick reset and termination rules against concrete passes, select the shifted checkpoint only after its activation, terminate the IT retry instead of also advancing it when the budget is exhausted, express and evaluate a monthly legal cadence, and explain every decision without confusing subject state with provenance-backed truth.

## V34 - Scoped Recurrence Policy and Deterministic Rule Evaluation

**Implemented by:** `189a41f` (`Add scoped recurrence policy evaluation`)

**Superseded assumption:** A validated list of typed recurrence conditions and effects is sufficient even when no service can determine which matching rule governs one concrete execution boundary.

**Architectural promotion:** Scoped recurrence-policy evaluation, typed cadence, deterministic resolution, and conflict explanation became core framework services. Domain packs provide vocabulary and incompatible outcome pairs without owning the evaluator.

V34 upgrades the occurrence registry to schema 4 while preserving the bounded rule language introduced in V33. It does not add a general-purpose expression engine. Concrete recurrence `phases` identify non-overlapping ordinal ranges within one execution. Pattern-owned `schedules` model either ISO civil-calendar cadence by day, week, month, or year or fixed integer steps along one chronology coordinate system. Schedules consume temporal and chronology services rather than duplicating either.

Rules now declare `applicability` across application level, concrete recurrences, phases, branches, positive iteration ranges, chronology-position windows, and civil effective-time windows. Pattern defaults cannot name concrete executions. Execution overrides must name at least one compatible recurrence and may use `replace-group` to suppress matching defaults in the same resolution group. Incomparable chronology and uncertain or missing required effective time return an indeterminate applicability result instead of silently matching or failing.

Conditions are independently evaluable. Occurrence-outcome predicates identify the exact subject. State-availability predicates identify subject, state kind, track, payload, and current occurrence boundary. Iteration predicates use a controlled comparison and positive ordinal, while schedule predicates test typed cadence. Occurrence-reached remains the current-template predicate. This closes the Derrick-versus-Colin ambiguity without treating subjective state as objective truth.

Every rule has nonnegative priority, stable resolution group, `exclusive` or `accumulate` selection, and explicit override behavior. The evaluator composes applicability and `all`/`any` condition results, applies matching execution overrides, selects the highest-priority exclusive rule per group, accumulates declared additive rules, and reports equal-priority incompatible choices. It also rejects a selected advance-plus-terminate combination and competing reset targets. Its result contains selected rules and effects, conflicts, and a per-rule trace with applicability, condition outcomes, selection, suppression, and rejection reasons.

Outcome compatibility is pack-defined through canonical unordered pairs. Core registers only generic contradictions; narrative media adds `died-with-survived`. The occurrence loader enforces those pairs only for outcomes sharing occurrence, subject, and result-target scope. Provenance still determines whether an outcome, condition, state, or rule is supported; chronology still determines exact order; the evaluator only decides what the supplied, validated policy means at a requested recurrence boundary.

Core advances to pack version 25 with `deterministic-recurrence-rule-evaluation` and `recurrence-schedule-modeling`. Narrative media advances to version 20 with its scoped outcome incompatibility. The LoTM registry moves to schema 4 but remains empty beyond `main`, adding no fabricated loop records. Paired Python and native PowerShell services expose phase lookup, civil and coordinate schedule calculation and due matching, and deterministic rule evaluation. The permanent fixture now performs 43 queries/evaluations and rejects 61 malformed registries identically in Python, PowerShell 7, and Windows PowerShell 5.1.

## Testing After V34

### Loki Temporal-Architecture Probe

Before the full domain pass, V34 was tested against both seasons of Marvel Studios' *Loki*. The episode-level review separated mechanisms that a casual "time loop" label would conflate: timeline forks and pruning; Loki's punitive Sif memory loop; the TVA Handbook ontological cycle; uncontrolled and later controlled time-slipping through the TVA's own past, present, and future; the self-pruning event encountered twice in Loki's subjective history; repeated Temporal Loom attempts across centuries; retained technical learning; revisiting the He Who Remains decision point; and Loki's eventual destruction of the Loom and preservation of the branching timelines through a replacement structure. Marvel's official coverage confirms that Loki repeatedly relives the Loom scenario over centuries and that the successful resolution is not a repaired Loom but its destruction and replacement.

A temporary schema-4 probe modeled three source-bounded representative Loom passes without asserting a fictional exact total. Early failures selected the pattern-default `advance-iteration` effect. In the late phase, a derived knowledge state made the Loom's impossibility available to Loki; the execution override then suppressed the retry default and selected `terminate-recurrence`, with the evaluation trace identifying both decisions. Loki's knowledge remained available across the modeled resets, the final exit led to a separate aftermath occurrence, and the retained 43-query/60-malformed-case baseline remained green. A TVA-Handbook causal cycle also loaded without introducing a chronology cycle.

The test confirmed four intended separations:

1. The TVA can have an ordered local coordinate system even though it is outside ordinary timeline time. TVA-local and Earth-timeline positions remain incomparable unless a reviewed mapping relates them; "outside time" does not mean unordered.
2. Repeated Loom passes remain distinct occurrence identities at reused TVA-local coordinates while Loki's subjective track advances and retains state.
3. The final policy decision can terminate the retry execution because the original repair objective is impossible, without mislabeling the last repair attempt as successful.
4. Bootstrap causality remains legal in the causal graph while exact chronology remains acyclic.

The same probes exposed four deferred capabilities rather than V34 evaluator defects:

1. Source language such as "centuries" and an unspecified enormous number of attempts cannot be represented as an uncertain, bounded, or aggregate iteration count. Iterations require exact positive ordinals; sparse observations are legal, but compressing an unknown number of passes into ordinal three would be semantically false.
2. Loki experiences the same concrete self-pruning occurrence first as its recipient and later as its agent. Tracks require unique occurrence IDs, so one subject cannot revisit one physical occurrence twice in subjective order without duplicating the happening or inventing unmodeled participation records.
3. Separate chronology systems can preserve TVA-local order and timeline order, but chronology contexts have no typed relations such as `outside`, `oversees`, `observes`, or `intervenes-in`. The framework therefore cannot directly answer which timelines an extratemporal institution oversees or how an intervention relates its local action to a target branch.
4. Occurrence branches have topology but no lifecycle or terminal state. A pruning occurrence can be recorded, but the occurrence registry cannot state that the affected branch was pruned, transferred to the Void, restored, or otherwise inactive at a queried boundary.

Knowledge availability can represent Loki's partial-to-complete understanding and its carryover, but it does not quantify centuries of accumulated expertise. The concrete Loom destruction, timeline transformation, and resulting structure can be represented as occurrences, outcomes, state changes, and causal relations; V34's recurrence evaluator does not need to become a general action or counterfactual-choice engine to own those facts.

### Full V34 Pressure Test

The full post-V34 pass replayed the source-grounded Derrick abandoned-temple loop, changing-checkpoint and retry-exhaustion workflows, recurring medical state, and legal cadence against the executable evaluator. It also pressure-tested the same primitives conceptually against retained-memory loops, moving reset points, asynchronous participant awareness, nested and branching recurrences, manufacturing rework, scientific trial repetition, scheduled compliance obligations, and operational retry or rollback processes. These scenarios deliberately separated chronology, recurrence identity, participant state, policy selection, and evidence authority.

The Derrick fixture represented six distinct passes over a shared recurrence pattern. Passes one through five ended with Jack dead and selected the default advance rule. After the gray-fog restoration occurrence, Derrick's complete five-pass memory became available only on his subjective track; Colin received no corresponding state record. The sixth pass placed Derrick in the aware phase, recorded Jack surviving, suppressed the default reset, and selected the higher-priority termination override. The evaluator therefore answered both what happened in the final pass and what Derrick knew immediately before it without creating a chronology cycle.

The operational fixture combined a changing reset checkpoint with an exhausted retry budget. Early failures selected the old checkpoint and `advance-iteration`; the final failed attempt selected the new checkpoint and `terminate-recurrence`, with both defaults suppressed through scoped execution overrides. The legal fixture produced the expected January-through-December monthly values and distinguished March as due from April as off-schedule. The medical fixture selected its state rule when due and rejected it off-schedule. This confirmed that bounded schedules and deterministic overrides compose across narrative, IT, legal, and medical uses without moving claim authority out of provenance.

The retained conformance suites remained green and behaviorally identical in Python, PowerShell 7, and Windows PowerShell 5.1: thirteen chronology comparisons and thirteen malformed chronology registries; twenty temporal matches, twelve overlap vectors, and twenty-one malformed windows; eight reconciliation vectors, forty malformed reconciliation registries, a 1,500-hop chain, and both limits; plus forty-three occurrence query/evaluation assertions and sixty-one malformed occurrence registries. During the test, one PowerShell-only defect was found and repaired: its semantic recurrence-rule key included nested record IDs and omitted several applicability selectors. All runtimes now reject semantically duplicate rules even when their rule, condition, and effect IDs differ, and that case is permanent conformance data.

### V34 Integrity Gaps

Four shared evaluator or ingestion defects remain for the next version:

1. An `iteration-ordinal` condition may target a recurrence pattern other than its owning rule's pattern. The registry loads it, and evaluation incorrectly applies the current iteration ordinal anyway.
2. A schedule condition may target a schedule owned by another recurrence pattern. The registry loads it, then evaluation raises a pattern-mismatch error instead of rejecting the registry.
3. Recurrence-control effects such as `advance-iteration` and `terminate-recurrence` may target another recurrence pattern. The registry loads them and returns the foreign effect.
4. A rule whose applicability requires an effective-time window or schedule returns `no-match` when effective time is absent because the temporal predicate is rejected before the intended indeterminate branch. Missing required query context must produce `indeterminate`, while a supplied off-schedule time may remain `no-match`.

The pass also confirmed that `rule_kind` and effect compatibility is under-specified. A `termination` rule carrying an `advance-iteration` effect loads successfully. Core should not hard-code every semantic combination, but packs need a controlled compatibility registry that the loader can enforce.

### Deferred Capabilities

The Loki probe's four deferred capabilities remain real but should not be folded into the immediate integrity repair:

- uncertain, bounded, aggregate, or source-unspecified iteration cardinality;
- repeated participation in one concrete occurrence along a subjective track without duplicating the occurrence;
- typed relations among chronology contexts, including extratemporal observation, oversight, and intervention; and
- branch lifecycle such as active, pruned, transferred, restored, merged, or inactive at a boundary.

State transitions also need future semantic depth beyond simple availability: partial or quantitative expertise, acquisition through merged memories, prophecy, dreams, or timeline collapse, and conditional knowledge may eventually become a reusable knowledge-acquisition capability. Legal business-day exceptions, grace periods, and irregular schedule adjustments likewise exceed V34's deliberately bounded cadence model. Decision optimization, counterfactual simulation, and distributed vector-clock semantics remain outside the occurrence evaluator.

### V35 Recommendation

V35 should be **Recurrence Policy Integrity and Indeterminate Context**. It should enforce same-pattern ownership for ordinal and schedule predicates and recurrence-control effects, reject mismatched schedule ownership at ingestion, correct missing required effective time to `indeterminate`, and add pack-registered rule-kind/effect compatibility. Every rejection and indeterminate result should remain explainable in the evaluation trace, and the permanent malformed corpus should gain one vector per repaired boundary in all three runtimes.

The broader cardinality, repeated-participation, extratemporal-context, and branch-lifecycle capabilities should be staged after this correctness release. That keeps V35 small enough to harden V34's contract before the framework expands its temporal topology again.

## V35 - Recurrence Policy Integrity and Indeterminate Context

**Implemented by:** `4efd6b5` (`Harden recurrence policy integrity`)

**Superseded assumption:** A rule is semantically safe whenever each condition and effect independently references a known target of the expected type.

**Architectural promotion:** Same-pattern policy ownership, rule/effect semantic compatibility, and missing-context indeterminacy became explicit core framework guarantees rather than evaluator conventions or domain-specific assumptions.

V35 hardens the schema-4 occurrence contract without changing its stored record shape. The core pack advances to version 26 and adds the enabled `recurrence-policy-integrity` capability. Narrative media now requires core version 26, while projects in unrelated domains may extend the same controlled compatibility vocabulary through their own selected packs.

Iteration-ordinal conditions must target the recurrence pattern that owns their rule. Schedule conditions must use schedules owned by that same pattern. Recurrence-control effects such as `advance-iteration` and `terminate-recurrence` must likewise target the owning pattern. These checks happen during ingestion, so a malformed registry cannot survive loading and fail later during evaluation.

Core now registers valid `rule-kind/effect-kind` pairs separately from existing effect-target-type pairs. The initial domain-neutral combinations are reset/advance, termination/terminate, checkpoint-change/change-reset-point, and state-activation/activate-state. Packs can extend the controlled pair namespace when they add new rule or effect kinds; the evaluator does not infer compatibility from labels.

Applicability evaluation now checks for omitted required effective time before attempting temporal-window matching. A rule that cannot be evaluated without that context reports `indeterminate` and preserves the detail `effective time was not supplied` in its trace. A supplied time outside the window remains a definite non-match. Schedule matching already returned indeterminate when civil effective time was absent, so both applicability and condition paths now share conservative behavior.

The permanent occurrence corpus adds four malformed cases for foreign-pattern ordinal conditions, foreign-pattern schedules, foreign recurrence-control effects, and incompatible rule/effect kinds. It also adds result and trace assertions for missing effective time. Python, PowerShell 7, and Windows PowerShell 5.1 now pass forty-five occurrence query/evaluation assertions and reject sixty-five malformed registries identically. The retained chronology, temporal, and reconciliation suites also remain unchanged and green in all three runtimes.

## Testing After V35

### Ownership And Evaluation Replay

The executable post-V35 pass attacked nested recurrence ownership, domain-pack extensions, multi-effect rules, execution overrides, missing and uncertain temporal context, and civil or coordinate schedule boundaries. A valid inner-loop rule owned its ordinal predicate and advance effect and selected normally. Redirecting that ordinal predicate to the outer pattern was rejected during ingestion. The permanent foreign-schedule, foreign-control-effect, and rule/effect mismatch cases likewise remained rejected in Python, PowerShell 7, and Windows PowerShell 5.1.

Rules carrying two compatible checkpoint effects loaded, and different reset targets produced the expected explicit evaluation conflict. Two equal-priority execution overrides in one exclusive group also produced an explainable conflict with no arbitrary winner. Missing effective time returned `indeterminate` with the trace detail `effective time was not supplied`; unknown and uncertain windows remained indeterminate; a supplied due month selected the scheduled rule; and a supplied time outside the window produced `no-match`.

The structural behaviors shared by the prior Derrick and Loki probes remained intact: a default reset selected advance, the final execution override selected termination, subject state crossed only its declared carryover boundary, and nested recurrence stayed separate from its parent. The same fixture replayed changing-checkpoint conflict handling, retry termination semantics, medical scheduled-state activation, and legal monthly cadence. Civil and coordinate schedules distinguished due, off-schedule, and missing-context results correctly, and leap-day progression produced February 29 followed by March 1.

The retained baselines remained identical in all three runtimes: thirteen chronology comparisons and thirteen malformed chronology registries; twenty temporal matches, twelve overlap vectors, and twenty-one malformed windows; eight reconciliation vectors, forty malformed reconciliation registries, a 1,500-hop chain, and both limits; plus forty-five occurrence query/evaluation assertions and sixty-five malformed occurrence registries.

### Rule-Extension Gaps

The pressure test exposed three related gaps in extensible rule semantics:

1. One rule may contain semantically duplicate conditions under different IDs. The loader accepts both and evaluates the same predicate twice.
2. One rule may contain semantically duplicate effects under different IDs. The loader accepts both and returns duplicate effects to consumers.
3. Pack-defined effects have target-type and rule-kind compatibility but no declared target-scope or conflict semantics. A synthetic `pause-recurrence` effect could target another pattern and load successfully because same-pattern enforcement knows only the built-in advance and terminate effects. The synthetic pause and built-in advance effects could also be selected together without conflict because packs cannot declare them incompatible.

The third result does not mean every effect targeting a recurrence pattern must target its owning pattern. A domain may legitimately define an effect that starts, signals, or alters another pattern. The missing primitive is a pack-declared semantic profile, not a broader hard-coded check. Condition kinds remain executable behavior and therefore cannot become functional merely by adding vocabulary; an extension needs an evaluator implementation as well as controlled values.

### Civil-Schedule Boundary Gap

Civil schedule projection beyond year 9999 is neither bounded nor runtime-equivalent. From a maximum anchor, Python day projection raises `OverflowError`, while Python month and year projection return invalid strings such as `10000-01` and `10000`. Both PowerShell runtimes throw platform exceptions for day, month, and year projection. The API therefore lacks a shared controlled out-of-range result or error contract even though the temporal layer already treats years 0001 through 9999 as its valid civil domain.

### V36 Recommendation

V36 should be **Extensible Policy Semantics and Schedule Boundary Integrity**. It should reject semantically duplicate conditions and effects within one rule; let packs declare effect target-scope profiles such as owning-pattern versus external-pattern-allowed; and let packs declare incompatible effect-kind pairs for deterministic conflict detection. These declarations must augment, not replace, executable evaluator support for condition behavior.

The same version should make civil schedule projection honor the temporal model's 0001-9999 domain and return one controlled, behaviorally identical out-of-range result or exception in Python, PowerShell 7, and Windows PowerShell 5.1. Permanent conformance should include nested duplicates, extension-owned and extension-external targets, extension conflicts, leap day, and maximum day/month/year projection.

These are still integrity repairs to V34-V35 behavior. Uncertain iteration cardinality, repeated participation, extratemporal context relations, branch lifecycle, and deeper knowledge-acquisition semantics should remain staged until the policy and schedule contracts are closed under extension and boundary pressure.

## V36 - Extensible Policy Semantics and Schedule Boundary Integrity

**Implemented by:** `61e4a30` (`Add extensible recurrence policy semantics`)

**Superseded assumption:** Pack-defined effect vocabulary is safely extensible once effect target types and rule-kind compatibility are registered, even if target scope and cross-effect conflicts remain known only to the engine's built-in effect names.

**Architectural promotion:** Recurrence-pattern effect scope, effect-kind incompatibility, duplicate nested-rule semantics, and civil-schedule projection boundaries became explicit core framework contracts shared by all runtimes.

V36 closes the two integrity gaps exposed after V35 without expanding the recurrence rule language into a general-purpose expression engine. The occurrence registry remains schema 4. Core advances to pack version 27 and adds the enabled `extensible-recurrence-policy-semantics` and `civil-schedule-boundary-integrity` capabilities; narrative media now requires core version 27.

Every effect targeting a recurrence pattern must now have exactly one pack-declared target-scope profile. `{effect-kind}-uses-owning-pattern` requires the target to match the pattern owning the rule. `{effect-kind}-allows-external-pattern` permits another known recurrence pattern when the domain semantics require signaling or controlling an external pattern. Missing or ambiguous scope declarations are rejected during ingestion. The built-in advance and terminate effects use owning-pattern scope, while conformance introduces synthetic pause and signal effects to prove that the loader applies the declaration rather than recognizing hard-coded effect names.

Packs may also register canonical unordered effect-kind incompatibility pairs. The evaluator compares all distinct selected effect kinds against the composed pack registry and emits deterministic conflict messages for matching pairs. Core's prior advance-plus-terminate rule is therefore represented as pack data instead of a dedicated evaluator branch. A synthetic `advance-iteration-with-pause-recurrence` pair proves that extension-defined conflicts change evaluator behavior without engine modification. Existing multiple-reset-target conflict detection remains a structural evaluator invariant because it depends on effect targets, not only effect kinds.

Within one recurrence rule, semantic condition and effect identities are now unique independently of their nested record IDs. A repeated condition compares condition kind, target, expected value, subject, state, track, and ordinal value; a repeated effect compares effect kind and target. Duplicate components are rejected before they can inflate match evaluation or duplicate emitted effects. Whole-rule semantic duplicate detection remains in force across separate rule records.

Civil-calendar schedule projection now shares the temporal model's year range of `0001` through `9999`. Year and month schedules validate the computed target year before formatting. Day and week arithmetic normalizes platform overflow into the controlled error `Schedule projection exceeds supported civil range 0001-9999.` Python, PowerShell 7, and Windows PowerShell 5.1 therefore fail identically at the upper boundary. Chronology-step schedules remain integer-coordinate operations and are not constrained to the civil year range.

The permanent occurrence fixture adds leap-day progression, maximum day/month/year anchors, an accumulating conflict resolved through the pack-defined advance/terminate pair, and malformed duplicate condition/effect cases. It now supplies fifty-one stored assertions and sixty-seven malformed mutations. The paired conformance tools add three in-memory extension assertions for owning-pattern enforcement, legal external-pattern targeting, and extension-defined effect conflict, bringing the reported total to fifty-four assertions. All results match in Python, PowerShell 7, and Windows PowerShell 5.1. The retained chronology, temporal, and reconciliation suites remain unchanged and green.

## Testing After V36

### Extension-Policy Adversarial Pass

The post-V36 executable pass built synthetic pause and signal semantics entirely through composed pack vocabulary, then replayed each case in Python, PowerShell 7, and Windows PowerShell 5.1. A recurrence-pattern effect with no scope declaration was rejected. Declaring both owning-pattern and external-pattern scope for one effect was also rejected as ambiguous. An owning-pattern pause rule attached to the nested recurrence selected normally when it targeted that inner pattern, while a signal rule owned by the outer pattern legally targeted the known inner pattern under `allows-external-pattern`. These results were identical in all three runtimes and confirmed that scope enforcement follows pack declarations rather than built-in effect names.

The canonical extension conflict also behaved as designed. When the pack supplied `advance-iteration-with-pause-recurrence`, an outer reset rule and synthetic pause rule both selected and produced an explicit conflict. V36 therefore supports an IT retry policy in which advancing and pausing one retry execution are incompatible, or a narrative policy in which one loop cannot both advance and pause at the same decision boundary, without adding either effect to the evaluator.

The same pass retained the structural behavior needed by the Derrick and Loki scenarios. Derrick's inner or outer loop controls can remain owned by their respective recurrence patterns, and subject memory remains separate from control effects and chronology. A TVA-local policy can emit a typed external signal toward another known recurrence pattern without claiming that the two patterns share one chronology. This improves cross-pattern policy representation but does not resolve the previously recorded Loki gaps for uncertain iteration cardinality, repeated subjective participation in one occurrence, typed extratemporal context relations, or branch lifecycle.

### Civil-Schedule Boundary Pass

Civil schedule projection was tested at the exact upper boundary, one step beyond it, through direct value queries, and indirectly through due matching. Year `9999` and month `9999-12` remained valid. The next year or month returned the exact controlled error `Schedule projection exceeds supported civil range 0001-9999.` Leap-day progression remained correct. A deliberately extreme interval and ordinal also produced the controlled boundary error instead of an integer, formatting, or platform exception. Python, PowerShell 7, and Windows PowerShell 5.1 returned equivalent results throughout.

This behavior composes for narrative anniversaries, medical cadence, legal reporting periods, maintenance schedules, and operational retries as long as they use the supported forward civil interval model. Business calendars, holiday exceptions, grace periods, irregular schedules, and backward civil recurrence remain outside this deliberately narrow schedule contract. Fictional years outside the civil domain continue to belong to integer chronology coordinate systems, which were unaffected by the boundary checks.

The retained conformance stack remained green and behaviorally identical in all three runtimes: thirteen chronology comparisons and thirteen malformed chronology registries; twenty temporal matches, twelve overlap vectors, and twenty-one malformed windows; eight reconciliation vectors, forty malformed reconciliation registries, a 1,500-hop chain, and both limits; plus fifty-four occurrence query, evaluation, and extension assertions and sixty-seven malformed occurrence registries.

### Semantic Declaration And Effect-Resolution Gaps

The pressure test exposed three related gaps beyond V36's intended contract:

1. Effect incompatibility values are described as canonical unordered pairs, but pack composition does not validate their member references or ordering. Reversing the synthetic value to `pause-recurrence-with-advance-iteration` loaded and produced no conflict because the evaluator generates only sorted canonical keys. A typo, reversed declaration, self-pair, or pair naming an unknown effect can therefore remain inert without a pack-level error. Scope declarations have a related lifecycle issue: missing or contradictory declarations are rejected when a concrete effect uses them, but malformed or orphaned declarations are not rejected when packs compose.
2. Incompatibility currently applies globally by effect kind. An outer-pattern advance and an external pause targeting the inner pattern conflicted solely because their kinds matched the registered pair. Some semantics are globally incompatible, but others conflict only when they address the same target or owning pattern. Packs cannot yet declare that conflict scope.
3. Duplicate effects are rejected within one rule, but two independently valid accumulating rules may emit the same effect kind, target type, and target ID twice. The evaluator preserves both selected rule IDs, which is valuable provenance, but its flat effect list gives a downstream executor no deterministic instruction about whether the effect should execute once or twice. In legal and compliance uses, two authorities may independently require one action; in operational uses, duplicate execution may be harmful. Silent deduplication would lose contribution history, while blind repetition is equally unsafe.

Condition vocabulary remains intentionally different from effect metadata. Adding a condition kind still requires executable evaluator support; V36 does not and should not make an unknown predicate functional merely because a pack names it.

### V37 Recommendation

V37 should be **Semantic Declaration Integrity and Effect Resolution**. Pack composition should validate cross-namespace recurrence declarations before project records use them: every scope profile must reference a known recurrence-pattern-capable effect kind, each such effect must have exactly one scope, and every incompatibility pair must reference two distinct known effect kinds in canonical order. The same review should determine whether these compound declarations should remain encoded as controlled-value IDs or become typed pack records with clearer validation and future migration behavior.

Effect incompatibility should gain an explicit scope such as `global` or `same-target`, with deterministic target comparison and trace output. Evaluator results should group semantically identical selected effects into one resolved effect while preserving every contributing rule and nested effect ID; a pack or effect profile should state whether repeated contributions are idempotent, accumulating, or invalid. Permanent conformance should cover reversed and unknown pair members, orphaned and contradictory scope declarations, same-target versus cross-target conflicts, and duplicate contributions from separate selected rules in all three runtimes.

The broader temporal-topology work remains staged after this integrity release: uncertain or aggregate iteration cardinality, repeated participation, extratemporal context relations, branch lifecycle, and deeper knowledge-acquisition semantics are still valid future capabilities. V37 should first make the new V36 extension surface deterministic for pack authors and downstream executors.

## V37 - Semantic Declaration Integrity and Effect Resolution

**Implemented by:** `7991f45` (`Implement V37 semantic effect resolution`)

**Superseded assumption:** It is sufficient to validate recurrence semantic declarations only when a concrete project rule uses them, and selected rule effects can be handed downstream as a flat list without defining repeated-contribution behavior.

**Architectural promotion:** Cross-namespace effect declaration closure and resolved-effect execution semantics became core framework services at pack composition and rule evaluation boundaries.

V37 keeps schema-pack files at schema 2 and the occurrence registry at schema 4. Core advances to pack version 28 with enabled `semantic-declaration-integrity` and `deterministic-effect-resolution` capabilities, and narrative media now requires core version 28. The release uses validated controlled-value namespaces rather than introducing a new top-level pack record family, avoiding an unrelated migration across every existing pack while still making the declarations executable and closed.

Schema-pack composition now validates the complete recurrence effect vocabulary before project registries load. Every effect kind whose target compatibility includes `recurrence-pattern` must have exactly one owning-pattern or external-pattern scope declaration. Every effect kind must have exactly one repetition policy: `idempotent`, `accumulating`, or `invalid`. Scope and repetition declarations must reference known applicable effect kinds. Incompatibility pairs must equal the canonical sorted form of two distinct known effect kinds and must appear under exactly one namespace: global incompatibility or same-target incompatibility. Reversed, unknown, orphaned, missing, contradictory, and multiply scoped declarations fail while packs compose rather than remaining dormant until project data happens to exercise them.

Rule evaluation no longer exposes the raw concatenation of selected effect rows as its execution result. It groups contributions by effect kind, target type, and target ID. Each resolved effect reports repetition policy, contribution count, execution count, contributing rule IDs, and contributing nested effect IDs. Idempotent policy converts any positive number of equivalent contributions into one execution. Accumulating policy preserves one execution per contribution. Invalid policy permits one contribution but converts repeated contributions to zero executions and an explicit conflict. Contributor lineage remains available without treating duplicated execution as provenance.

Effect incompatibility now has explicit scope. Global pairs conflict whenever both kinds are selected. Same-target pairs conflict only when both resolved effects address the same target type and ID, and their message includes that target. Core's advance/terminate incompatibility moves to same-target scope, allowing an owning-pattern action and a permitted external-pattern action to coexist when they concern different recurrences. Competing reset targets remain a structural evaluator conflict independent of pack kind-pair metadata.

The permanent occurrence fixture adds a second independently selected advance contribution and verifies one idempotent resolved effect with both contributor paths. Stored expectations rise from fifty-one to fifty-three. The paired extension probes now cover canonical declaration failures, orphaned and contradictory scope/repetition metadata, global versus same-target conflicts, legal external targeting, and all three repetition policies. Python, PowerShell 7, and Windows PowerShell 5.1 each pass sixty-seven occurrence assertions and reject sixty-seven malformed occurrence registries. The retained chronology, temporal, and reconciliation suites remain green.

The pre-pressure compatibility gate also remains green in all three runtimes. Visualization validation reports fifteen source nodes, 121 relationships, and zero class/layout issues for both configured views. Redirected QA exports produce matching 35-file inventories and summaries with one Novel V1 Chapter 32 bounded graph plus Dunn Smith Chapter 10/32 and Leonard Mitchell Chapter 32 bounded pages; stable Markdown/Mermaid outputs and normalized refresh/bounded snapshot semantics match. Launching normal exports from `Tools/` preserves repository-root discovery. Redirected rendering of the tracked full Volume 1 graph produces the same nonempty 298,269-byte SVG and SHA-256 hash in Python, PowerShell 7, and Windows PowerShell 5.1. No canonical generated output was changed.

## Testing After V37

### Permanent And Compatibility Baseline

The permanent post-V37 stack remained behaviorally identical in Python, PowerShell 7, and Windows PowerShell 5.1. Each occurrence runtime passed sixty-seven query, evaluation, resolution, and extension assertions and rejected sixty-seven malformed occurrence registries. The retained suites also passed thirteen chronology comparisons and thirteen malformed chronology registries; twenty temporal matches, twelve overlap vectors, and twenty-one malformed windows; plus eight reconciliation vectors, forty malformed reconciliation registries, a 1,500-hop chain, and both configured resolution limits. The pre-pressure QA/Visualization compatibility gate recorded with V37 remained the current green baseline; no implementation changed during this pressure pass, so canonical or redirected graph generation did not need to be repeated.

Under the testing methodology formalized after this pass, the retained record covers `CONF-STRICT-INGESTION`, `CONF-TEMPORAL`, `CONF-CHRONOLOGY`, `CONF-RECONCILIATION`, `CONF-OCCURRENCE`, `CONF-PACK-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `SCENARIO-DERRICK`, `SCENARIO-LOKI`, `PRESSURE-ADVERSARIAL`, and `PRESSURE-CROSS-DOMAIN`.

### Semantic-Declaration Adversarial Pass

The permanent V37 declaration vectors continued to reject reversed and unknown incompatibility members, missing or contradictory repetition profiles, orphaned scope declarations against a nonempty effect vocabulary, and one pair declared under both global and same-target scope. The expected valid extensions still composed, proving that the ordinary core and domain-pack path is closed under the cases V37 was designed to repair.

Two wider probes exposed shared behavior in all three runtimes:

1. If the composed effect-kind vocabulary is empty, semantic declaration validation returns immediately. An orphan repetition declaration such as `ghost-effect-uses-idempotent` is therefore accepted rather than rejected. The currently selected core pack always supplies effect kinds, so this does not corrupt the LoTM configuration, but it violates the reusable validator's stated declaration-closure contract and is a V37 correctness defect.
2. Compound incompatibility IDs are not injective. With effect kinds `a`, `a-with-b`, `b-with-c`, and `c`, the single value `a-with-b-with-c` is simultaneously the generated key for the pair `a` plus `b-with-c` and the pair `a-with-b` plus `c`. Pack validation accepted the declaration, and evaluation reported both global conflicts from the one stored value. Stable IDs do not forbid the delimiter token, so canonical sorting cannot recover which two members the author intended. This is an architectural encoding defect rather than a runtime-parity problem.

The collision demonstrates the limitation V37 deliberately risked when it retained compound controlled-value IDs instead of typed declaration records. Adjacent `effect-kind-uses-target-type` and `rule-kind-uses-effect-kind` relationships use the same general encoding pattern and should be audited during the repair, but this test did not claim that every compound namespace in the framework must be migrated at once.

### Effect Resolution And Cross-Domain Pass

Direct resolver probes supplied the same two contributions in reverse lexical order and returned deterministic contributor lineage in every runtime. Under `idempotent`, contribution count two produced execution count one. Under `accumulating`, it produced execution count two. Under `invalid`, it produced execution count zero plus the exact duplicate-effect conflict. Two targets sharing the same text ID but having different target types remained separate resolved effects. A same-target incompatibility reported only the shared target, while a global incompatibility still fired across different targets.

These mechanics compose cleanly across domains. Two legal authorities can contribute one idempotent filing obligation while preserving both rule IDs. Two genuinely additive assessments can produce two accumulating executions. Duplicate medication administration or duplicate deployment actions can use invalid repetition and fail explicitly. A retry can advance one job without conflicting with a stop directed at another job under same-target scope, while a genuinely global emergency policy can prohibit both regardless of target.

One execution-boundary ambiguity remains. A conflicted evaluation retains resolved effects whose individual `execution_count` values may be nonzero; for example, the permanent advance/terminate conflict reports one proposed execution for each effect while the overall status is `conflict`. Current policy tells consumers to treat conflicts as reportable and not guess, so a careful caller can gate on evaluation status. The machine result does not explicitly distinguish diagnostic proposed counts from an authorized executable plan, however, nor does it define whether independent effects may partially execute. Medical, legal, and operational consumers need a fail-closed rule rather than an implied convention.

### Derrick And Loki Replay

The source-grounded Derrick abandoned-temple conclusions remain intact. Distinct passes, Derrick-only restored memory before the sixth pass, Colin's lack of that state, the changed final outcome, and recurrence exit still depend on occurrence identity, subject tracks, state transitions, overrides, and chronology rather than effect duplication. If independent applicable policies both contribute the same reset advance, V37 now collapses them to one idempotent execution while retaining both contributors. If advance and termination remain selected for the same loop, same-target policy reports a conflict; the established final-pass execution override remains the deterministic way to suppress the reset and select termination. No chronology cycle or accidental knowledge transfer is introduced.

The retained Loki model also benefits without changing its topology. Multiple matching reasons to retry the Loom can contribute one idempotent advance, an external signal can address another recurrence without a false same-target conflict, and simultaneous advance/termination of one Loom execution is reported. V37 still does not represent an uncertain or aggregate number of centuries-long attempts, repeated subjective participation in one concrete occurrence, typed extratemporal TVA/timeline relations, branch lifecycle, or quantitative accumulated expertise. Those remain previously identified capabilities rather than regressions in effect resolution.

### V38 Recommendation

V38 should be **Typed Effect Semantics and Fail-Closed Execution**. It should first remove the empty-vocabulary early return and permanently reject every orphan effect declaration, including minimal composed registries. It should then replace delimiter-composed recurrence effect declarations with typed records whose member IDs, scope, and repetition policy are separate validated fields. At minimum this applies to effect target compatibility, rule-kind/effect compatibility, recurrence-pattern scope, repetition policy, and incompatibility members/scope; adjacent compound namespaces should be audited and migrated only where the same ambiguity is real. Existing pack data needs an explicit reviewed migration rather than heuristic parsing of ambiguous IDs.

Evaluation should preserve contribution counts and contributor provenance as diagnostic resolution data while producing an explicit execution disposition. The bounded default should be fail-closed: an evaluation with any unresolved conflict exposes no authorized executions, even though its proposed resolved effects remain inspectable. Partial execution, compensation, transaction boundaries, and effect payload/action semantics should remain unavailable until separately modeled rather than being inferred by consumers.

Permanent V38 conformance should cover an empty effect vocabulary with every orphan declaration family, adversarial delimiter collisions, typed member-reference failures, deterministic migration of the current core declarations, conflict-wide execution blocking, and retained idempotent/accumulating/invalid behavior in all three runtimes. After that integrity boundary is closed, the staged temporal-topology work can resume with uncertain iteration cardinality, repeated participation, extratemporal context relations, and branch lifecycle; deeper knowledge-acquisition semantics remain a separate reusable capability.

## Historical Testing Retention Audit After V37

The testing-methodology formalization was audited against every `Testing After V1` through `Testing After V37` section, the conversation-driven pressure-test portfolio, permanent fixture directories, current conformance tools, and the QA/Visualization parity records. The audit confirmed that strict ingestion, reconciliation, temporal, chronology, occurrence, runtime parity, QA, rendering, Derrick, Loki, adversarial, scale, and broad cross-domain coverage were already represented.

It also found that several durable earlier test dimensions had been compressed too far into the generic `PRESSURE-CROSS-DOMAIN` label. The methodology now retains `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-WORK-CONTINUITY`, `PRESSURE-MEDIA-DISTRIBUTION`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-ENTITY-IDENTITY`, `PRESSURE-TEMPORAL-TOPOLOGY`, and `PRESSURE-RECURRENCE-STATE`. A near-start cross-industry candidate catalog explicitly preserves the mixed-media franchise, serialized-form, parody, fictional-calendar, time-loop, IT/operations, medical, legal/compliance, investigative-evidence, and scientific probes that drove V1-V37 while distinguishing conceptual and synthetic cases from source-grounded scenarios.

Three engineering surfaces were also restored as explicit requirements: `CONF-LOOKUP` for pinned Unicode behavior from V18-V19; `CONF-PROJECT-COMPOSITION` across the foundation and later registry additions; and `PARITY-COMMAND-SURFACE` plus `COMPAT-ARTIFACT-LIFECYCLE` from the tooling, QA, root-discovery, stale-output, and cleanup work. The change-impact matrix now routes changes in each historical model area back to the appropriate retained matrix instead of relying on maintainers to remember the old pressure rounds.

This audit changes testing policy, not framework schema behavior. It reclassifies the unchanged green V37 conformance and compatibility baseline rather than presenting newly added IDs as a new execution. The framework lifecycle now requires every new version to select candidates during design, identify them in the evolution entry, review the catalog again after pressure testing, and promote only durable additions under the methodology's retention rules. V38 remains the next recommended implementation version, and its proposed testing must use the expanded cumulative methodology and candidate catalog.

## Extraction Foundation Stabilization - 2026-08-02

**Implemented by:** `1682a6c` (`Stabilize framework extraction readiness`)

The extraction-readiness program did not advance the framework schema beyond V37. It converted the accumulated architecture and testing policy into an enforceable engineering boundary: shared runtime modules are separated from command adapters; the complete registry surface has paired permanent conformance; compatibility consumers are aggregate-owned; static policies cover Actions, Python, PowerShell, and work annotations; and a neutral consumer can execute an isolated copy without LoTM configuration or content.

The stabilized portable bundle consists of `Framework/`, `Tools/Runtime/`, `Tools/Conformance/`, the Python and PowerShell dependency declarations, and the Python formatter policy. The extraction verifier generates a disposable core-only project rather than copying `Project_Config/`, rejects nine canonical or generated LoTM surfaces, runs five portable suites in all three runtimes, compares structured summaries, and cleans its operating-system temporary tree. `Framework/extraction_readiness.md` now owns the exact allowlist, exclusions, verification contract, and limits of the claim.

### Complete Stabilization Baseline

All fourteen registered baseline conformance suites passed in Python, PowerShell 7, and Windows PowerShell 5.1 with matching semantic summaries. Static checks passed for GitHub Actions, 38 Python files, 39 PowerShell files in both runtimes, 304 annotation-eligible files, and all 22 annotation fixtures. The full-release compatibility profile passed six checks in 148.044 seconds: current Visualization and QA semantics matched across runtimes; all twelve root-launch combinations passed; artifact ownership and six unsafe destinations were enforced; the 202-file isolated copy passed; and all three renderers produced the same nonblank 298,269-byte SVG and SHA-256 hash. Canonical outputs remained unchanged.

The retained pressure portfolio found no new extraction defect. The neutral copy supplied direct evidence for `PRESSURE-LAYER-PORTABILITY`; the unchanged model suites and V37 findings retained the work/continuity, media/distribution, evidence/authority, entity/identity, temporal/topology, recurrence/state, Derrick, and Loki conclusions. Adversarial malformed-input, ambiguity, unsafe-output, cycle, limit, and scale coverage remained green. Broad narrative candidates plus synthetic IT/operations, medical, legal/compliance, investigative, and scientific replays found no LoTM ownership leak into the core. The cross-domain result is architectural evidence, not a substitute for building and testing an actual non-narrative pack.

The selected broad-replay candidates were the repository-grounded LoTM/COI/Donghua project and Derrick scenario; the retained externally source-grounded Loki scenario; conceptual Star Wars/Spaceballs, Star Trek, Tolkien, Marvel/DC, Dragon Ball/DBZA, One Piece, Solo Leveling, Gundam, and rotating serialized-media structures; and synthetic IT/operations, medical, legal/compliance, investigative, and scientific cases. They exercised `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-WORK-CONTINUITY`, `PRESSURE-MEDIA-DISTRIBUTION`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-ENTITY-IDENTITY`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-RECURRENCE-STATE`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, `PRESSURE-SCALE`, `SCENARIO-DERRICK`, and `SCENARIO-LOKI`.

The readiness claim is deliberately bounded. It proves that the framework kernel can be copied and validated independently; it does not claim that all QA graph construction has moved into Visualization, that a normalized content and bounded-page service is complete, that a separate framework repository already exists, or that IT packs, migrations, editors, and Streamlit are implemented.

V38 remains **Typed Effect Semantics and Fail-Closed Execution**. The two known V37 declaration defects and explicit conflict-wide execution disposition remain next-version work. Later temporal-topology and knowledge-acquisition capabilities are unchanged by this stabilization pass.

## V38 - Typed Semantic Declarations and Fail-Closed Execution

**Implemented by:** `5ea5f01` (`Implement V38 typed semantic execution`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-OCCURRENCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-DERRICK`, `SCENARIO-LOKI`, `PRESSURE-RECURRENCE-STATE`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** The repository-grounded LoTM/COI/Donghua project and Derrick abandoned-temple scenario; the retained externally source-grounded Loki scenario; delimiter-colliding synthetic pack identifiers; and synthetic IT/operations retry and deployment effects, medical treatment effects, legal/compliance obligations, and scientific repeated-intervention cases.

**Superseded assumption:** Relationships among controlled vocabulary atoms can be represented safely as delimiter-composed controlled-value IDs, and a conflicted evaluation can expose nonzero execution counts so long as consumers are expected to inspect its overall status first.

**Architectural promotion:** Typed semantic relationships and fail-closed execution authorization become core framework services rather than conventions reconstructed independently by pack authors or downstream consumers.

V38 advances schema-pack files from schema 2 to schema 3. It introduces a bounded typed `semantic_declarations` section while retaining atomic vocabulary under `controlled_values`. The migration covers every currently executable compound semantic family for which the V37 ambiguity is real: transition-kind profiles, outcome incompatibilities, rule-effect target compatibility, rule-kind/effect compatibility, recurrence-pattern effect scope, effect repetition policy, effect incompatibilities with explicit scope, and state-change profiles. The corresponding compound controlled-value namespaces are removed rather than parsed heuristically.

Typed declaration composition must validate every referenced atom, singular profile and policy ownership, recurrence-pattern scope completeness, distinct unordered incompatibility members, one incompatibility scope, duplicate declarations within or across packs, and provider ownership. Orphan declarations must fail even when their referenced vocabulary is empty. Existing canonical and synthetic packs require explicit reviewed migration; schema-2 compound declarations receive no ambiguous compatibility parser.

Rule evaluation separates diagnostic proposals from executable authorization. Proposed effects retain repetition policy, contribution count, proposed execution count, contributing rule IDs, and contributing nested effect IDs. Authorized effects are emitted separately with an explicit execution disposition. Any unresolved conflict or indeterminate evaluation authorizes no effects; conflict blocking applies to the complete evaluation rather than attempting partial execution. No-match evaluations remain non-applicable.

V38 does not introduce partial execution, compensation, rollback, transaction boundaries, effect payload/action execution, or a general-purpose expression language. It also does not implement aggregate recurrence cardinality, repeated participation identity, chronology-context topology, branch lifecycle, or deeper knowledge and skill acquisition. Those remain later stabilization versions after this integrity boundary closes.

Acceptance requires paired schema-pack and occurrence behavior in Python, PowerShell 7, and Windows PowerShell 5.1; permanent positive, malformed, delimiter-collision, empty-vocabulary, composition, authorization, blocking, and retained repetition vectors; deterministic structured parity; the complete registered conformance baseline; cumulative QA and Visualization compatibility; and the selected recurrence, cross-domain, adversarial, portability, and scale pressure portfolio.

## Testing After V38

**Pressure corrections:** `a103827` (`Fix V38 pressure-test findings`)

### Executed Coverage

The cumulative V38 round executed `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-OCCURRENCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, every registered `full-release` compatibility check, both source-format policies, work-annotation validation, the Derrick and Loki retained scenarios, and the recurrence, temporal-topology, portability, adversarial, cross-domain, and scale pressure families selected before implementation. The candidate catalog did not need a new permanent entry: its existing LoTM, Loki, IT/operations, medical, legal/compliance, and scientific candidates exposed the relevant structures without adding a distinct reusable pressure pattern.

### Defects And Corrections

Pressure testing found one implementation defect. Evaluation originally preferred an already selected rule over an unresolved rule, which could authorize an effect while another plausibly applicable policy remained indeterminate. The first global fix also showed why simple precedence reversal was too blunt: a scheduled rule with unknown applicability but definitively false independent conditions must not block an unrelated reset. The corrected tri-state evaluation examines conditions when applicability is indeterminate, eliminates the rule only when those conditions prove it cannot match, and otherwise returns `blocked-indeterminate`. A permanent mixed selected-plus-indeterminate vector now preserves the selected reset as a diagnostic proposal while exposing no authorized effects. Occurrence coverage therefore increased from 67 to 68 query/evaluation assertions while retaining 67 malformed cases.

The scale audit found a coverage gap rather than a runtime defect. The generated 64-pack probe scaled atomic vocabulary but not schema-3 semantic declarations. Every generated pack now owns one transition kind, one transition profile, and one typed mapping between them, proving composition of 64 additional declarations in all three runtimes. The schema-pack suite retains 52 malformed compositions and two delimiter-collision identity pairs. This strengthens the existing `PRESSURE-SCALE` obligation rather than creating another test family.

### Permanent And Compatibility Baseline

The complete registered `baseline` passed all 14 suites with identical semantic summaries in Python, PowerShell 7, and Windows PowerShell 5.1. Measured runtimes were 41.7, 162.2, and 247.3 seconds. Ruff passed 38 files; the PowerShell formatter passed 39 files in both runtimes with no changes or long lines; work-annotation validation passed 308 files and all 22 fixtures. The `full-release` compatibility profile passed all six checks in 170.918 seconds: Visualization retained 15 nodes and 121 relationships; QA retained 16 notes, 121 relationships, 71 data references, and all 34 normalized files; all 12 root launches passed; artifact cleanup and six unsafe-destination rejections passed; isolated extraction copied 205 files and passed its portable suites in all three runtimes; and all renderers produced the same nonblank 298,269-byte SVG. Canonical outputs remained unchanged.

### Derrick, Loki, And Cross-Domain Replay

The repository-grounded Derrick replay remains coherent: passes retain distinct occurrence identities, Derrick-only restored memory precedes the sixth pass, Colin receives no accidental state, reset and termination remain incompatible executable decisions, and exit introduces no chronology cycle. The externally source-grounded Loki replay likewise preserves idempotent retry proposals, conflict-wide blocking, and final termination through an execution override. Synthetic deployment retries, treatment decisions, legal obligations, and scientific interventions all preserve typed ownership, contributor lineage, accumulating versus idempotent repetition, same-target conflict scope, and fail-closed uncertainty without importing narrative vocabulary into core.

### Remaining Limitations

The Loki replay continues to expose supported deferrals rather than V38 regressions: uncertain or aggregate centuries of attempts, repeated participation in one occurrence, typed extratemporal TVA/timeline topology, branch lifecycle, and accumulated knowledge or expertise are not represented yet. These remain explicitly separated capabilities rather than being approximated through V38's effect semantics.

### V39 Recommendation

V39 should be **Aggregate and Uncertain Recurrence Cardinality**. It should support exact, minimum, maximum, ranged, unknown, and aggregate counts; permit representative concrete iterations beside an aggregate history; preserve certainty, provenance, and applicability; and avoid inventing an exact total for Loki's Loom attempts. Repeated participation, chronology-context topology, branch lifecycle, and deeper acquisition semantics remain explicitly excluded for their later bounded versions.

## V39 - Aggregate and Uncertain Recurrence Cardinality

**Implemented by:** `513db0a` (`Implement V39 aggregate recurrence cardinality`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-DERRICK`, `SCENARIO-LOKI`, `PRESSURE-EPISTEMIC-STATE`, `PRESSURE-RECURRENCE-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** The repository-grounded Derrick abandoned-temple loop; the retained externally source-grounded Loki Loom attempts; and synthetic IT deployment retries, recurring medical episodes, scheduled legal obligations, and repeated scientific interventions with exact, bounded, unknown, and representative-only histories.

**Superseded assumption:** A concrete recurrence execution can be described adequately only by enumerating every iteration, and the number of stored iteration rows can stand in for the complete execution history.

**Architectural promotion:** Aggregate recurrence cardinality becomes a stable core occurrence service while evidence, authority, effective timing, and reader/source applicability remain centralized in provenance and source applicability services.

V39 advances the occurrence registry to schema 5 and adds stable `recurrence_cardinalities` records. Each record targets one concrete recurrence and describes realized iteration history through a `cardinality_kind` of `exact`, `minimum`, `maximum`, `range`, or `unknown`. Canonical lower and upper bounds preserve the difference between a precise total, one-sided knowledge, a bounded interval, and absence of a numeric claim without creating placeholder iteration identities.

Cardinality shape is independent from materialization. `coverage_mode` distinguishes a complete concrete enumeration, named representative iterations within a larger or uncertain history, and a wholly unmaterialized aggregate. Complete coverage requires an exact total and an iteration list of that size. Representative coverage requires one or more distinct iterations owned by the recurrence and bounds compatible with that evidence. Unmaterialized coverage requires no concrete iteration references. Every record carries controlled certainty, rejects semantic duplicates, is queryable by recurrence, and becomes a first-class provenance subject.

The occurrence record does not copy source IDs, evidence locators, assertion status, authority, effective windows, or reader boundaries. Provenance assertions target the stable cardinality record or one of its fields; source applicability scopes and provenance timing determine when and for which source context the claim applies. Multiple historically or source-distinct cardinality records may therefore coexist without the occurrence loader selecting factual authority.

V39 is bounded to realized recurrence history. It does not model expected, permitted, configured, or scheduled future counts; synthesize omitted occurrences; assign ordinals to aggregate-only attempts; introduce repeated participation identity; add chronology-context topology; define branch lifecycle; or model accumulated knowledge and expertise. Those remain separate capabilities. Acceptance requires paired schema-5 loading and query behavior, positive and malformed cardinality shapes, complete/representative/unmaterialized coverage, provenance closure, zero and large-count boundaries, deterministic scale behavior, complete three-runtime baseline parity, and unchanged project-consumer compatibility.

## Testing After V39

**Pressure corrections:** `dc45237` (`Fix V39 pressure-test findings`)

### Executed Coverage

The cumulative V39 round executed `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, every registered `full-release` compatibility check, both source-format policies, work-annotation validation, the Derrick and Loki retained scenarios, and the recurrence, evidence-authority, temporal-topology, portability, adversarial, cross-domain, and scale pressure families selected before implementation. The existing LoTM, Loki, IT/operations, medical, legal/compliance, and scientific candidates covered the new semantics without requiring another candidate-catalog entry.

### Defects And Corrections

Pressure testing found no V39 loader or query defect. It did expose a permanent coverage gap: `recurrence-cardinality` was a registered provenance target, but the provenance corpus did not prove a cardinality field through source priority, effective applicability, and authority resolution. The neutral corpus now composes chronology and occurrence fixtures, targets `recurrence-cardinality:inner-minimum-count.minimum_count`, and supplies competing primary and adaptation assertions. At the effective boundary, the primary source wins deterministically without moving source authority into the occurrence loader. Provenance coverage therefore increased from 12 to 14 fixture assertions and from four to five authority vectors while retaining 68 malformed configurations, five invalid queries, and the generated 128-assertion scale extension.

### Permanent And Compatibility Baseline

The complete registered `baseline` passed all 14 suites with matching semantic summaries in Python, PowerShell 7, and Windows PowerShell 5.1. Measured runtimes were 58.9, 216.9, and 331.8 seconds. Ruff passed 38 files; the PowerShell formatter passed 39 files in both runtimes with no changes or long lines; work-annotation validation passed 308 files and all 22 fixtures. The `full-release` compatibility profile passed all six checks in 240.455 seconds: Visualization retained 15 nodes and 121 relationships; QA retained 16 notes, 121 relationships, 71 data references, and all 34 normalized files; all 12 root launches passed; artifact cleanup and six unsafe-destination rejections passed; isolated extraction copied 205 files and passed its portable suites in all three runtimes; and all renderers produced the same nonblank 298,269-byte SVG. Canonical outputs remained unchanged.

### Derrick, Loki, And Cross-Domain Replay

The repository-grounded Derrick loop can now distinguish at least six realized iterations from the smaller representative set that needs concrete identities. Derrick's retained memory, Colin's unaffected state, the recurrence exit, and the chronology remain separate; cardinality adds no cycle and does not synthesize absent passes. The Loki Loom replay can preserve representative attempts while recording an unknown or supported minimum total instead of turning centuries of subjective learning into an invented exact iteration count. That duration remains temporal evidence, not recurrence cardinality.

Synthetic IT deployment retries can record exact or bounded realized attempts while schedules continue to own permitted future retries. Medical recurring episodes can retain representative encounters beside a minimum or ranged history. Legal obligations can distinguish realized misses or completions from future scheduled duties. Scientific interventions can retain sampled trials beside an aggregate count. In each domain, provenance and source applicability determine which count applies; cardinality does not select its own factual authority.

### Remaining Limitations

V39 intentionally cannot represent one participant entering the same concrete occurrence more than once under distinct participation identities. That blocks a faithful account of cases such as Loki interacting with or pruning another participation of himself without cloning the occurrence itself. Typed extratemporal chronology-context topology, branch lifecycle, and accumulated knowledge or expertise also remain deferred. None should be approximated with aggregate cardinality, iteration identity, or provenance records.

### V40 Recommendation

V40 should be **Participation Identity and Revisited Occurrences**. It should give each subject's involvement in an occurrence a stable identity, permit the same subject to participate more than once without duplicating the occurrence, preserve participation-relative order and role/state distinctions, and support provenance targeting. It must remain separate from entity incarnation, recurrence iteration, chronology-context topology, branch lifecycle, and general knowledge acquisition. Derrick should continue to use distinct recurrence iterations, while the Loki replay should prove that two participations of one entity in one occurrence can be distinguished without introducing a chronological cycle.

## V40 - Participation Identity And Revisited Occurrences

**Implemented by:** `73956d4` (`Implement V40 participation identity`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-DERRICK`, `SCENARIO-LOKI`, `PRESSURE-RECURRENCE-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** Loki's self-pruning encounter with distinct recipient and agent participations in one occurrence; the Derrick abandoned-temple loop as a negative control that must continue to use distinct recurrence iterations; and synthetic repeated observation, record review, intervention, retry inspection, medical encounter review, legal evidence review, and scientific re-observation cases.

**Superseded assumption:** An occurrence's presence in a subject track is sufficient identity for that subject's involvement, and one occurrence can appear at most once on one subject track.

**Architectural promotion:** Participation identity and subjective track-entry identity become domain-neutral core occurrence services rather than narrative-only conventions or duplicated occurrence records.

V40 advances the occurrence registry to schema 6. `occurrence_participations` give one subject's involvement in one concrete occurrence a stable identity with a controlled role, perspective, participation status, and optional reference to an already registered chronology context. Multiple participations by the same subject in the same occurrence are legal when their complete semantics differ; exact semantic duplicates are rejected. A participation is neither an entity incarnation nor a recurrence iteration, and its status does not replace subject-state acquisition or provenance.

`track_entries` independently place participations on matching-subject tracks using unique contiguous positive ordinals. This preserves subjective or process order even when two entries resolve to the same occurrence. Entry-relative navigation remains deterministic. Existing occurrence-relative neighbor and state convenience queries remain available for unique track occurrences but fail explicitly when repeated participation makes the occurrence boundary ambiguous.

Both stable record families are provenance subjects. The portable fixture models one self-intervention occurrence with an earlier recipient participation and a later agent participation, distinct chronology-context references, and two independently ordered track entries. The chronology references do not define relations among contexts or add chronology edges; typed chronology-context topology remains V41 work. Core pack 31 supplies domain-neutral participation role, perspective, and status vocabulary plus the `occurrence-participation-identity` capability. Narrative media requires core 31 without redefining the mechanism.

Acceptance requires paired schema-6 loading and query behavior; positive repeated-participation, chronology-context, track-entry, ambiguity, and provenance vectors; malformed target, vocabulary, semantic-duplicate, ownership, and ordinal cases; project capability and provider closure; deterministic three-runtime summaries; the complete aggregate baseline; and unchanged project-consumer compatibility. V40 does not define chronology-context topology, branch lifecycle, participation-relative state acquisition, accumulated expertise, or general knowledge acquisition.

## Testing After V40

**Pressure corrections:** `221df8c` (`Fix V40 repeated participation pressure finding`)

The cumulative V40 pressure round executed `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, every registered `full-release` compatibility check, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, the retained source-grounded Derrick and Loki scenarios, and the selected recurrence/state, evidence-authority, temporal-topology, layer-portability, adversarial, cross-domain, and scale pressure families. The complete 14-suite `baseline` passed in Python, PowerShell 7, and Windows PowerShell 5.1 with canonicalized semantic parity; measured runtimes were 47.9, 171.8, and 284.0 seconds. Full-release compatibility passed all six registered checks in 180.0 seconds, preserving Visualization, QA, root discovery, artifact lifecycle, isolated extraction, rendering, canonical-output protection, and cleanup behavior.

Pressure testing found one V40 implementation defect. The original loader rejected two participations when occurrence, subject, role, perspective, status, and chronology context were identical. That rule contradicted the promised repeated-observation case: two visits may have identical participation semantics while their distinct track entries supply the stable identity and subjective order. The permanent neutral fixture now accepts two semantically identical observer participations only because both are placed on one shared subject-matching track. Semantically identical records that do not share an ordering track remain invalid as unexplained duplicates. The occurrence corpus now passes 87 query/evaluation assertions, 102 malformed cases, a 128-cardinality scale extension, and a 128-participation/track-entry scale extension identically in all three runtimes.

The scenario replay also sharpened the identity-selection rule. Loki's self-pruning remains one concrete occurrence with earlier recipient and later agent participations distinguished by role, chronology context, and track entry. Derrick's abandoned-temple loop remains distinct occurrences in distinct recurrence iterations rather than repeated participations in one occurrence. A subject repeatedly observing the same concrete happening may use ordered participations; a later record review, clinical chart review, legal evidence review, IT retry inspection, scientific re-observation, retry execution, or new intervention is a separate occurrence when the review, inspection, execution, or intervention is itself a new happening. Participation identity therefore does not replace ordinary occurrence or recurrence identity.

The cross-domain replay used synthetic IT/operations, medical, legal/compliance, investigative, and scientific cases plus the existing neutral executable fixture. It found no core ownership leak and required no new catalog candidate: the existing cross-industry catalog already retains these structural patterns. The testing methodology was strengthened so semantically identical ordered participation and unexplained duplicate rejection remain permanent `CONF-OCCURRENCE` obligations.

V40 still intentionally does not define relations among chronology contexts, branch lifecycle, participation-relative transitions or state acquisition, accumulated expertise, or general knowledge acquisition. Those remain `deferred`, not failed V40 behavior. Occurrence-relative navigation and state queries continue to fail explicitly when repeated participation makes their boundary ambiguous; entry-relative navigation is the deterministic supported service.

### V41 Recommendation

V41 should be **Chronology-Context Topology**. It should model typed non-precedence relations such as outside, observes, oversees, intervenes-in, projects-into, and receives-from among chronology contexts; preserve coordinate incomparability unless an explicit mapping relates them; connect cross-context interventions to concrete occurrences and applicability without inventing chronology edges; and keep branch lifecycle, participation-relative state, and knowledge progression outside its bounded scope. The Loki TVA replay should prove TVA-local order, timeline oversight, and intervention while ordinary chronology cycle rejection remains intact, with distributed control planes, simulations, and archival observation providing cross-domain pressure.

## V41 - Chronology-Context Topology

**Implemented by:** `16865c4` (`Implement V41 chronology context topology`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-CHRONOLOGY`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-LOKI`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** TVA-local chronology overseeing and intervening in timeline contexts; cross-context projection and receipt without coordinate equivalence; distributed-system control planes; simulation hosts and simulated worlds; archival observers; and scientific or operational monitoring contexts.

**Superseded assumption:** Chronology contexts are exclusively narrative annotations, and relations among them must either be omitted or approximated as chronology-position order.

**Architectural promotion:** Chronology-context identity and non-precedence topology move from the narrative-media layer into core; domain packs retain ownership only of domain-specific context roles and relation vocabulary extensions.

V41 advances the chronology registry to schema 2. Core contexts bind coordinate systems to optional project targets while pack-owned roles preserve domain meaning. Directed context relations describe topology without contributing comparison edges. Stable typed bindings connect a relation to concrete occurrences, occurrence branches, or applicability scopes, and composed loading validates those targets only after their owning registries exist.

The topology service must answer incoming and outgoing relation queries deterministically, reject unknown contexts, malformed bindings, semantic duplicates, and unregistered vocabulary, and preserve coordinate incomparability unless the chronology registry contains an explicit ordering or mapping primitive. Topology cycles are legal because observation, oversight, projection, and receipt are not chronological precedence; ordinary exact before/after cycles remain invalid.

V41 does not define branch lifecycle, participation-relative state transitions, accumulated expertise, or general knowledge acquisition. Those remain later bounded capabilities rather than implicit consequences of context topology.

## Testing After V41

**Pressure corrections:** `1092846` (`Fix V41 pressure-test findings`)

### Executed Coverage

The cumulative V41 pressure round executed `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-CHRONOLOGY`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, every registered `full-release` compatibility check, both source-format policies, work-annotation and workflow validation, the retained externally source-grounded Loki scenario, and the temporal-topology, layer-portability, adversarial, cross-domain, and scale pressure families selected before implementation. Existing catalog candidates covered the pressure round; no new candidate was required.

### Defects And Corrections

Pressure testing found no V41 loader or query defect. It exposed two permanent-coverage defects. The original chronology fixture exercised only `oversees`, `observes`, and `receives-from`, while intervention bindings were attached to the broader oversight relation. The corrected fixture now distinguishes a control plane that is outside, oversees, and intervenes in an observed timeline; binds intervention to one occurrence, branch, and applicability scope; projects into a simulation context that receives from it; and retains an archival observer. All six core relation types now participate in 11 deterministic incoming or outgoing queries, four contexts and seven relations are independently available to provenance, and the existing 128-relation topology cycle remains legal. The occurrence contract also no longer carries the superseded V40 statement that chronology-context topology is future work.

### Permanent And Compatibility Baseline

The complete registered `baseline` passed all 14 suites with matching semantic summaries in Python, PowerShell 7, and Windows PowerShell 5.1. Measured runtimes were 40.1, 161.3, and 253.8 seconds. Chronology conformance retained 14 position comparisons, 17 malformed registries, typed-target closure, coordinate incomparability, exact-order cycle rejection, and the generated 128-relation cyclic topology probe while expanding from five to 11 context queries. Ruff passed 38 files; the PowerShell formatter passed 39 files in both runtimes with no remaining changes or long lines; work-annotation validation passed 312 files and all 22 fixtures; and actionlint passed every workflow.

The `full-release` compatibility profile passed all six registered checks in 168.632 seconds. Visualization retained 15 nodes and 121 relationships. QA retained 16 notes, 121 relationships, 71 data references, and all 34 normalized files. All 12 root-discovery launches passed; artifact cleanup and six unsafe-destination rejections passed; isolated extraction copied 209 files and passed its portable suites in all three runtimes; and all renderers produced the same nonblank 298,269-byte SVG with identical SHA-256 hashes. Canonical outputs remained unchanged.

### Loki And Cross-Domain Replay

The TVA can be represented as a chronology context with its own locally ordered coordinate system rather than as an unordered or timeless exception. Timeline and branch contexts retain their own coordinates. `outside` and `oversees` describe topology; `intervenes-in` binds the TVA action to the affected occurrence, branch, and applicability scope. Those relations do not make TVA-local and timeline coordinates comparable. Reciprocal receipt and observation paths may form legal topology cycles, while an exact chronological before/after cycle continues to fail.

The same contract models an IT control plane overseeing and intervening in a workload environment, a simulation host projecting into a simulated world, an archive observing an operational context, and a scientific instrument or monitoring service observing and intervening in an experiment. Medical monitoring and legal/compliance oversight use the same core topology without narrative vocabulary. A later review, deployment, intervention, or observation remains its own occurrence; context topology describes where that happening operates, not whether it is the same event.

### Remaining Limitations

V41 intentionally does not model branch creation, pruning, restoration, transfer, merge, or state history. It also does not model Loki's retained learning and accumulated expertise across repeated Loom attempts. Direct context-relation queries are deterministic but do not infer transitive topology paths. Multiple concrete interventions may share one stable topology relation through distinct typed bindings, while the intervention happenings themselves remain occurrence records. These are bounded separations rather than chronology-context failures.

### V42 Recommendation

V42 should be **Timeline-Branch Lifecycle**. It should give branches provenance-backed state histories such as emerging, active, pruned, transferred, restored, merged, preserved, and inactive; preserve lineage, continuity membership, applicability, and state at a requested boundary; and model the TVA's pruning, restoration, preservation, and final replacement structure without collapsing branches into one chronology. Source-control branches, environment promotion, alternate histories, and scientific experiment branches should provide the cross-domain pressure cases. Knowledge, memory, skill, and expertise acquisition remain a separate later capability.

## V42 - Timeline-Branch Lifecycle

**Implemented by:** `8aaedc0` (`Implement V42 timeline branch lifecycle`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-CHRONOLOGY`, `CONF-OCCURRENCE`, `CONF-SOURCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `STATIC-GITHUB-ACTIONS`, `SCENARIO-LOKI`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** Loki's branching timelines, TVA pruning, restored and preserved branches, and final replacement structure; source-control branch creation, archival, restoration, and merge; environment creation, deactivation, promotion, rollback, and preservation; alternate-history branches; and scientific experiment branches with retained lineage.

**Superseded assumption:** Stable branch identity, parent/fork lineage, and a mutable current status or deletion are sufficient to describe branch history.

**Architectural promotion:** Append-only branch lifecycle, continuity membership, and deterministic state-at-lifecycle-boundary queries move into core. Narrative-media owns only narrative-specific lifecycle vocabulary such as pruning.

V42 advances the occurrence registry to schema 7. Branch identity remains stable and acyclic. Optional continuity memberships resolve against the source registry only during composed project loading. Separate branch-state transitions preserve a contiguous branch-local history with explicit prior and resulting states, activation occurrences, and optional occurrence-transition triggers. A child branch begins through its recorded fork trigger, merge state changes require a merge trigger, and lifecycle records remain independently addressable by provenance.

Branch lifecycle order is not chronology. Its positive ordinal is local to one branch, zero means before any recorded state, and an omitted boundary means the latest state. Chronology continues to own temporal comparison; provenance continues to own evidence, authority, supersession, and source or reader applicability. Core registers generic lifecycle vocabulary while packs add domain-specific states and changes without requiring every project to support them.

The paired runtimes must reject unknown branches, continuity memberships, states, changes, activation occurrences, and triggers; noncontiguous ordinals; broken prior/resulting state chains; trigger endpoint mismatches; and child branches whose first lifecycle record is disconnected from the fork that created them. Permanent probes include deterministic boundary queries, 118 malformed mutations, source-continuity composition closure, one provenance-backed branch-state claim, and a generated 128-transition branch history.

V42 does not model knowledge, awareness, memory, skill, proficiency, or accumulated expertise. It does not infer lifecycle transitions from chronology, source continuity, or a domain label. Those remain explicit, provenance-backed project claims and later bounded capabilities.

## Testing After V42

**Pressure corrections:** `26ab95a` (`Fix V42 pressure-test findings`)

### Executed Coverage

The cumulative V42 pressure round executed `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-SOURCE`, `CONF-CHRONOLOGY`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, every registered `full-release` compatibility check, both source-format policies, work-annotation and workflow validation, the retained externally source-grounded Loki scenario, and the recurrence-state, temporal-topology, evidence-authority, layer-portability, adversarial, cross-domain, and scale pressure families selected before implementation. Existing catalog candidates covered the round; no new candidate or test-family ID was required.

### Defects And Corrections

Pressure testing found one loader defect and two permanent-coverage defects. A lifecycle record with `change_kind: merge` could omit its trigger or point to a non-merge transition even though the contract requires a concrete branch merge. Both runtimes now require a matching `branch-merge` trigger, and two new malformed cases retain the missing-trigger and wrong-profile failures.

The positive occurrence fixture had registered pruning, transfer, and restoration vocabulary without making the loader consume it. Its changed branch now progresses through emergence, activation, pruning, transfer, restoration, and merge. Boundary queries increased from 97 to 100 while the generated 128-transition history remained intact. That expectation growth exposed a second defect: PowerShell reported a hard-coded 97-query summary even though it executed the new queries. The PowerShell summary now derives its count from the shared expectations, including mapping-shaped phase vectors, and matches Python at 100. The malformed corpus increased from 116 to 118.

### Permanent And Compatibility Baseline

The complete registered `baseline` passed all 14 suites with matching semantic summaries in Python, PowerShell 7, and Windows PowerShell 5.1. Concurrently measured runtimes were 41.0, 169.2, and 283.3 seconds. Occurrence conformance now reports 100 query/evaluation assertions, 118 malformed registries, source-continuity closure, and generated 128-record branch-state, cardinality, and participation/track-entry probes. The remaining registry counts stayed unchanged. Ruff passed 38 files; the PowerShell formatter passed 39 files in both runtimes with no remaining changes or long lines; work-annotation validation passed 312 files and all 22 fixtures; and actionlint passed every workflow.

The `full-release` compatibility profile passed all six registered checks in 163.213 seconds. Visualization retained 15 nodes and 121 relationships. QA retained 16 notes, 121 relationships, 71 data references, and all 34 normalized files. All 12 root-discovery launches passed; artifact cleanup and six unsafe-destination rejections passed; isolated extraction copied 209 files and passed its portable suites in all three runtimes; and all renderers produced the same nonblank 298,269-byte SVG with identical SHA-256 hashes. Canonical outputs remained unchanged.

### Loki Branch-Lifecycle Replay

Loki's timeline forks retain stable branch identities and parent/fork lineage. TVA pruning is an activation occurrence followed by a `prune` lifecycle change into the narrative-owned `pruned` state; transfer toward the Void, restoration, and later preservation remain separate lifecycle records rather than deletion and recreation. Branch-local ordinals answer the state before pruning, after pruning, after restoration, and at the final known boundary without adding chronology edges. TVA-local order and ordinary timeline coordinates remain separate chronology systems connected by V41 context topology, and provenance remains able to target each lifecycle claim independently.

The Loom's destruction and Loki's preservation of the surviving timelines are concrete occurrences and outcomes. The resulting multiversal replacement structure is not itself a timeline branch and must not be forced into branch lifecycle. It remains an entity, context, or other project target related to those occurrences and branches through the appropriate owning registries. Centuries of accumulated engineering expertise also remain outside branch lifecycle and recurrence cardinality.

### Cross-Domain Replay

Source-control branches can progress from emerging to active to merged or inactive while retaining fork lineage and history after merge. Environment lineages can be activated, deactivated, restored, transferred, or preserved without overwriting earlier deployment state. Alternate histories and experimental branches retain continuity membership and provenance-backed lifecycle claims while chronology remains partial or incomparable where appropriate. A branch label never makes two environment, history, or experiment coordinates comparable.

The replay also sharpened the boundary around what counts as a branch. An environment, clinical course, legal matter, experiment, or control structure should use branch lifecycle only when it represents a forked lineage of happenings or state. Generic entity or resource lifecycle remains owned elsewhere. Promotion destinations, the Void, and replacement structures are related targets, not additional state labels.

### Remaining Limitations

`branch_state_at` returns structural lifecycle state at a branch-local ordinal. It does not yet combine provenance authority and applicability into a source-aware or reader-aware state decision; downstream analytical projection must perform that composition before presenting a gold-layer answer. Lifecycle records also do not carry a generic typed destination or replacement target. A transfer occurrence or relationship can preserve that fact today, but a future reusable binding service may be justified if several lifecycle-bearing registries need the same destination semantics.

V42 still does not quantify knowledge, skill, proficiency, or accumulated expertise, and it does not infer any of them from elapsed time, repeated attempts, or branch survival. Those are missing capabilities rather than V42 regressions.

### V43 Recommendation

V43 should begin Phase 1.7 by deciding the smallest reusable boundary for knowledge, belief, awareness, memory, skill, proficiency, and expertise progression. The design must determine whether epistemic acquisition and practiced capability can share one transition contract without conflating truth, access, confidence, and competence. Loki's retained engineering learning should be the narrative pressure case, with education, credentialing, incident diagnosis, clinical understanding, investigative inference, and scientific learning providing cross-domain pressure. Applicability-aware analytical resolution and generic lifecycle destination bindings should remain recorded boundaries unless that design proves one is a prerequisite rather than a separate later service.

## V43 - Epistemic State Progression

**Implemented by:** `89fa466` (`Implement V43 epistemic state progression`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-DERRICK`, `SCENARIO-LOKI`, `PRESSURE-RECURRENCE-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** Loki's retained and progressively completed understanding across repeated Loom attempts; Derrick's delayed restored knowledge and Colin's independent state as regression controls; direct, gradual, externally supplied, conditional, inferred, merged-memory, dream, prophecy, and timeline-reconciliation acquisition; education and incident diagnosis; clinical understanding and revision; investigative inference and contradictory belief; scientific learning from repeated trials; and physical state as a non-epistemic negative control.

**Superseded assumption:** Availability plus one resulting completeness value and an optional epistemic attitude are sufficient to model both epistemic progression and later practiced competence.

V43 records the Phase 1.7 decision that epistemic acquisition and practiced capability require separate bounded versions. Both may reuse the generic subject-state transition spine, but they must not share meaning merely because both change over time. V43 covers knowledge, memory, awareness, and belief. V44 will cover skill, proficiency, competence, expertise, and qualification evidence.

Core now owns typed state-profile declarations and structural continuity for the dimensions each profile uses. Packs map every controlled state kind to exactly one profile and contribute domain mechanisms. The three composed profiles are `availability-state`, `epistemic-access`, and `epistemic-belief`; the nine composed kind mappings cover four core kinds plus narrative memory, knowledge, awareness, belief, and physical state. Epistemic availability, completeness, and attitude remain independently modeled dimensions with explicit prior and resulting values. A discrete, gradual, aggregate, or unknown change shape remains separate from the mechanism that caused the change. Objective truth, evidence authority, contradiction among claims, supersession, and applicability remain owned by provenance; a subject's belief or access state cannot establish that a payload is true.

V43 advances the occurrence registry from schema 7 to schema 8, core from pack version 33 to 34, and narrative media from 23 to 24. State transitions now carry their derived `state_profile`, explicit `change_shape`, paired prior/resulting completeness, paired prior/resulting attitude, and paired availability. Profile declarations mark each dimension required, optional, or forbidden. Composition rejects missing mappings, unknown profiles, and invalid dimension requirements. Reusable profiles may remain dormant until a selected downstream pack contributes a matching state kind, preserving core-only extraction and optional-pack composition. State-chain continuity compares every dimension used by the profile.

The portable fixture preserves acquisition, retention, loss, restoration, and invalidation without inferring state from elapsed time, occurrence participation, source existence, or repeated exposure. It represents partial-to-complete understanding without numeric precision, belief revision independently from completeness, awareness and memory acquisition, and physical state as a non-epistemic negative control. A provenance assertion targets the resulting completeness field directly, preserving evidence and claim authority outside the state record.

V43 does not model skill, proficiency, competence, expertise, credentials, authorization, practice-derived capability, or bounded quantitative proficiency scales. Those belong to V44. Participation-relative state transitions, generic lifecycle destination bindings, and applicability-aware analytical projection also remain outside V43 unless implementation proves one is a strict prerequisite.

## Testing After V43

**Compatibility correction:** `4a7d6b9` (`Stabilize Mermaid browser rendering`)

### Executed Coverage

The cumulative V43 pressure round executed the complete 14-suite `baseline` profile in Python, PowerShell 7, and Windows PowerShell 5.1; every registered `full-release` compatibility check; Ruff formatting and lint; PowerShell formatting in both supported runtimes; work-annotation fixture and repository validation; actionlint; the retained source-grounded Derrick and Loki scenarios; and `PRESSURE-EPISTEMIC-STATE`, `PRESSURE-RECURRENCE-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`. The existing candidate catalog covered the round, so no new candidate or stable test-family ID was required.

### Compatibility Correction

The first render gate exposed a project-consumer compatibility regression rather than a V43 model defect. The tracked Puppeteer config forced independently updated Microsoft Edge 151 while Mermaid CLI's installed Puppeteer 25.3 runtime expected its version-matched Chrome for Testing 150; the browser process exited before Puppeteer could connect. A temporary Chrome-based diagnostic rendered the representative graph at the prior 298,269-byte size and isolated browser selection as the failure.

The permanent correction removed the machine-specific Edge path, retained Puppeteer's browser download in hosted CI, pinned `puppeteer@25.3.0` beside Mermaid CLI 11.16.0, and documented bundled-browser ownership. The focused three-runtime render check then produced byte-identical 298,269-byte SVGs with matching dimensions and required labels. The subsequent aggregate `full-release` run passed rendering with every other compatibility consumer. This correction changes renderer environment policy only; it does not alter graph semantics or canonical outputs.

### Permanent And Compatibility Baseline

All 14 registered conformance suites passed with the same canonicalized semantic summary SHA-256, `85604836cd5cc7f1f19562a2c3293007f5ae80e603d26b2f66198f442d1402b5`, in Python, PowerShell 7, and Windows PowerShell 5.1. Concurrently measured runtimes were 52.7, 189.4, and 306.6 seconds. The permanent corpus remains at three state profiles, nine state-kind mappings, 111 occurrence query/evaluation assertions, 125 malformed occurrence registries, 18 provenance assertions, and the generated 128-record branch-state, cardinality, participation/track-entry, and provenance scale probes.

Ruff passed all 38 Python files. The PowerShell formatter passed 39 files in both runtimes with no changes or long lines. Work-annotation validation passed 312 eligible files and all 22 fixtures with ten valid annotations. Actionlint passed every workflow. The `full-release` compatibility profile passed all six registered checks in 187.3 seconds: Visualization, QA, root discovery, artifact lifecycle, isolated framework extraction, and rendering. Canonical outputs remained unchanged and temporary artifacts were removed.

### Loki Epistemic-State Replay

The retained source-grounded Loom scenario maps to qualitative epistemic progression without inventing competence. An early transition can make Loki's technical understanding available but partial; a later gradual transition can move the same knowledge payload from partial to complete; subsequent track positions retain that resulting state across representative attempts. Recurrence cardinality continues to own the unknown or bounded number of attempts, chronology and participation own their respective order and identity, and provenance can independently support the completeness claim and its source applicability.

The state record does not infer progression from elapsed centuries, attempt count, branch survival, successful action, or eventual outcome. `complete` means complete access relative to the modeled knowledge payload, not objectively correct knowledge, universal understanding, engineering proficiency, or quantified expertise. The latter capability remains deliberately unavailable until V44.

### Derrick And Colin Replay

Derrick's delayed awareness or restored memory is an `epistemic-access` transition for Derrick, activated before the later recurrence pass and retained only across an explicit applicable boundary. Colin's participation in the same expedition and loop does not create a corresponding state transition, so Colin remains an independent negative control. Reset, carryover, recurrence exit, chronology, and knowledge state retain separate ownership; no chronology cycle or accidental cross-subject state transfer is required.

This replay also preserves the distinction between memory, awareness, knowledge, and belief. Discovering that the expedition is repeating can use awareness or knowledge completeness, retaining the prior pass can use memory, and accepting or rejecting an explanation can use belief attitude. None establishes the objective truth of the explanation without provenance authority.

### Cross-Domain Replay

Education and scientific learning can progress from unavailable through partial to complete understanding without claiming a credential or skill level. Incident diagnosis can be acquired, revised, invalidated, lost, or restored through explicit activation occurrences and source evidence. Clinical understanding can remain distinct from verified patient state and can change when new evidence arrives. Investigative inference can use belief attitude independently from knowledge completeness, preserving uncertainty and contradiction without turning an investigator's conclusion into truth. Physical state remains a non-epistemic `availability-state` control and cannot accept epistemic completeness or attitude fields.

Adversarial pressure retained rejection of unmapped kinds, unknown profiles, absent required dimensions, forbidden dimensions, unknown change shapes, broken state chains, invalid targets, ambiguous queries, and malformed provenance field paths. Core-only extraction retained dormant reusable profiles without importing narrative vocabulary. The existing generated scale probes stayed deterministic and introduced no new traversal or memory concern.

### Remaining Limitations

V43 offers qualitative `none`, `partial`, and `complete` access rather than an arbitrary numeric knowledge scale. It does not derive a current gold-layer answer by combining state, evidence authority, and applicability; analytical projection must still perform that composition. It also does not model skill, proficiency, competence, expertise, practice effects, credentials, qualifications, licenses, assessment results, or authorization. These are intentional boundaries, not V43 regressions.

### V44 Recommendation

V44 should implement **Capability and Proficiency Progression** as Phase 1.8. It should reuse the structural subject-state spine while defining separate capability profiles for skill, proficiency, competence, and expertise; support qualitative levels and only explicitly sourced quantitative measures; separate practice or transfer mechanism from discrete, gradual, or aggregate change shape; preserve improvement, degradation, loss, restoration, and transfer through provenance-backed transitions; and keep credentials, qualifications, licenses, authorization, and assessment evidence distinct from demonstrated or asserted capability. Loki's retained engineering expertise should prove that V44 composes with V43 understanding without collapsing either into the other.

## V44 - Capability And Proficiency Progression

**Implemented by:** `998dceb` (`Implement V44 capability progression`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-LOKI`, `PRESSURE-CAPABILITY-STATE`, `PRESSURE-EPISTEMIC-STATE`, `PRESSURE-RECURRENCE-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** Loki's retained and accumulated Temporal Loom engineering expertise alongside his separate V43 understanding; education plus credential acquisition; incident-response skill; clinical competence and licensing; investigative ability and assessment; scientific practice; externally supplied or transferred capability; degradation, loss, and restoration; qualitative progression rubrics; bounded integer assessment scales; and unsupported decimal or universal-ranking attempts as negative controls.

**Superseded assumption:** Availability, epistemic completeness, or elapsed practice can stand in for a separately modeled capability level.

V44 will reuse V43's subject-state transition spine while adding one profile-governed capability dimension. A state scale will give each transition a named local interpretation rather than making `novice`, `expert`, a percentage, or any other level universal. Qualitative scales will own explicit ordered level IDs. Quantitative scales will be bounded signed integers with a named unit; arbitrary decimals, inferred precision, and cross-scale comparison remain outside this version.

Capability, skill, proficiency, competence, and expertise will use a capability-state profile. Credential, qualification, license, and authorization state will remain availability-only so holding a record or permission cannot prove competence. Assessment results remain evidence or provenance-addressable source material; they may support a capability claim but cannot generate one automatically.

Improvement and degradation will be explicit state changes validated against scale order. Practice and training will be mechanisms, while discrete, gradual, aggregate, or unknown change shape continues to describe progression form. Acquisition, retention, transfer, loss, restoration, improvement, and degradation require explicit activation, source targets, certainty, and ordinary provenance rather than inference from elapsed time, recurrence cardinality, occurrence participation, or successful outcomes.

V44 is expected to advance the schema-pack declaration schema to 4, the occurrence registry to schema 9, and core to pack version 35. It will not add a general decimal measurement system, credential issuer registry, license-governance service, assessment engine, universal competence ontology, cross-scale conversion, or gold-layer authority resolver.

## Testing After V44

**Pressure corrections:** `b0647f4` (`Close V44 pressure-test coverage`)

### Permanent And Compatibility Baseline

The implementation-confirmation pass ran all fourteen registered baseline suites in Python, PowerShell 7, and Windows PowerShell 5.1 with matching semantic summaries. The full-release compatibility profile passed all six registered checks: Visualization, Obsidian QA, root discovery, artifact lifecycle, isolated framework extraction, and three-runtime rendering. Ruff, PowerShell formatting in both runtimes, and work-annotation validation also passed. The resulting V44 baseline uses schema-pack declaration schema 4, occurrence schema 9, core pack version 35, 120 enabled capabilities, 994 controlled values, four state profiles, eighteen state-kind mappings, and sixty-one provenance subject types.

After conceptual pressure analysis, `CONF-OCCURRENCE` and `CONF-PROVENANCE` were rerun directly in all three runtimes. All runs agreed on 128 occurrence queries, 147 rejected occurrence configurations, twenty provenance assertions, 68 rejected provenance configurations, five rejected provenance queries, and the retained 128-record scale probes. Windows PowerShell 5.1 required its ordinary extended timeout but returned the same result; no implementation or parity defect was found.

### Loki Understanding And Expertise Replay

The retained externally source-grounded *Loki* episode review from V34 was replayed through `SCENARIO-LOKI`, `PRESSURE-CAPABILITY-STATE`, `PRESSURE-EPISTEMIC-STATE`, `PRESSURE-RECURRENCE-STATE`, and `PRESSURE-EVIDENCE-AUTHORITY`. Loki's understanding of the Temporal Loom and his engineering expertise can target the same Loom payload, use the same subjective track, cite the same representative attempts, and cross explicitly declared carryover boundaries while remaining separate state chains. `knowledge` uses completeness under `epistemic-access`; `expertise` uses a project-defined local scale under `capability-state`. Neither profile accepts the other's dimension.

The source statement that Loki spent centuries learning and retrying does not authorize an exact attempt count or a universal expertise score. Aggregate or uncertain recurrence cardinality records the unmaterialized attempts, representative occurrences ground the sourced transitions, and gradual or aggregate practice describes progression shape. The final successful intervention is an occurrence and outcome, not automatic proof of expertise. This preserves the distinction between what Loki understood, what he could do, what happened, and what the source actually establishes.

### Cross-Domain And Adversarial Replay

Synthetic replays covered education and credentialing, IT incident response, clinical practice, legal authorization, investigative work, and scientific experimentation under `PRESSURE-CROSS-DOMAIN`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, and `PRESSURE-SCALE`:

- Education separates subject knowledge, practiced ability, assessment evidence, and an awarded qualification. Passing an assessment or receiving a credential does not create a capability transition.
- IT separates incident knowledge from diagnostic or recovery skill and from vendor certification. Repeated successful recoveries do not silently increase proficiency.
- Clinical practice separates understanding, demonstrated competence, licensure, and observations or assessments; no license or outcome is treated as clinical ability.
- Legal and investigative cases separate domain knowledge, practiced analysis, authorization or badge state, and source-governed evidence. Authority to act is not competence, and stronger evidence does not upgrade skill automatically.
- Scientific practice separates theory knowledge, experimental technique, degree or training records, repeated trials, and reproducibility evidence. Trial count and elapsed research time do not imply progression.

The permanent malformed corpus also retained the intended fail-closed boundaries: decimals are rejected, bounded integers must remain within their declared scale, qualitative levels require stable contiguous order, one transition cannot change scales, improvement and degradation must move in the declared direction, credentials forbid capability values, and epistemic profiles cannot receive capability dimensions. Local scales cannot be compared or converted without a future explicit capability; this is an intended boundary rather than a defect.

### Conclusion And Next Step

V44 closes Phase 1.8 without a model, parity, or consumer regression. Capability is now reusable across industries without becoming a universal ranking, credential resolver, assessment engine, or inferred gold-layer truth. Project data must still assert and source each capability transition explicitly. Multidimensional competency frameworks can use separate payloads and scales, but automatic cross-scale conversion, credential governance, and assessment-derived state remain deliberately deferred.

The next step is Phase 1.9, **Temporal Stabilization Pressure Test**, rather than opening V45 immediately. It should replay the complete source-grounded Loki and Derrick scenarios with V39-V44 active together, run the cumulative retained portfolio, classify every remaining temporal limitation, and decide whether the Phase 1 exit gate is satisfied or a narrowly scoped V45 is still required.

## Phase 1 Temporal Stabilization After V44

### Executed Coverage

The Phase 1.9 stabilization round treated V39-V44 as one composed temporal system rather than six independently passing features. It executed the complete fourteen-suite `baseline` profile in Python, PowerShell 7, and Windows PowerShell 5.1 with matching suite inventories and canonicalized semantic summaries. Measured local runtimes were 39.6, 182.4, and 325.1 seconds. All runtimes retained 128 occurrence queries, 147 malformed occurrence cases, 128-record scale probes for cardinality, participation, and branch lifecycle, schema-pack declaration schema 4, occurrence schema 9, 120 enabled capabilities, and sixty-one provenance subject types.

Ruff formatting and lint, PowerShell formatting in both supported runtimes, work-annotation fixtures and repository validation, actionlint, and `git diff --check` all passed. The `full-release` compatibility profile passed all six checks in 159.184 seconds. Visualization retained fifteen nodes and 121 relationships. QA retained sixteen notes, 121 relationships, seventy-one data references, one bounded graph, two bounded pages, and all thirty-four normalized files. All twelve root-discovery launches passed; artifact cleanup preserved unrelated files and rejected six unsafe destinations; isolated extraction copied 209 files and passed its portable suites in all three runtimes; and all renderers produced the same nonblank 298,269-byte SVG with identical SHA-256 hashes. Canonical outputs remained unchanged.

This round adds `PRESSURE-TEMPORAL-COMPOSITION` as a permanent methodology obligation. Future stabilization cannot infer integration from isolated service passes: at least one composed scenario must activate aggregate history, repeated participation, context topology, branch lifecycle, epistemic state, and capability state together. The existing Loki and Derrick candidates remain sufficient, so the candidate catalog did not require a new candidate.

### Complete Loki Replay

The source-grounded two-season Loki scenario remains representable without one overloaded timeline abstraction. The Sif punishment sequence is a recurrence of distinct occurrences. The TVA Handbook ontological cycle is causal rather than chronological, so causality may cycle without creating an exact-order cycle. TVA-local past, present, and future remain locally ordered in their own chronology context while timeline coordinates remain incomparable unless an explicit mapping relates them. Time-slipping and revisitation use concrete occurrences, jumps, and subjective track order rather than contradictory before/after claims.

Loki's self-pruning remains one concrete occurrence with distinct earlier recipient and later agent participations, each placed independently on his subjective track. The model therefore preserves one happening without duplicating it or pretending that participation identity is a recurrence iteration. The TVA context can be outside, oversee, observe, and intervene in timeline contexts; intervention bindings connect those relations to concrete occurrences, branches, and applicability scopes without adding chronology edges.

The Temporal Loom attempts use representative concrete iterations plus an uncertain or supported-minimum aggregate cardinality. The source-supported statement that Loki worked for centuries remains evidence for duration and aggregate progression, not permission to invent an exact attempt total. His partial-to-complete Loom understanding and his novice-to-higher locally scaled engineering expertise are separate state chains. Both may share payloads, tracks, representative attempts, and carryover boundaries, but neither is inferred from elapsed time, attempt count, branch survival, or eventual success.

Timeline forks retain stable branch identity and lineage. Pruning, transfer toward the Void, restoration, and preservation are append-only branch-local lifecycle changes rather than deletion and recreation. The final Loom destruction and recurrence exit are concrete occurrences and outcomes. The surviving branch structure retains its lifecycle, while the replacement multiversal structure is an entity or context target rather than being forced into the identity of a timeline branch. Revisiting the He Who Remains decision point, bootstrap causality, recurrence termination, branch preservation, retained understanding, and accumulated expertise therefore compose without requiring a chronology cycle.

### Derrick Replay

The source-grounded abandoned-temple scenario remains the negative control for several Loki mechanisms. Its six passes are distinct recurrence iterations containing distinct occurrence identities at reused external coordinates; they are not six participations in one occurrence. Passes one through five end with Jack dead and advance the recurrence. Derrick's memories of those passes are unavailable until the interstitial gray-fog restoration occurrence, become available before pass six, and remain specific to Derrick's track. Colin receives no matching transition, preventing silent state transfer.

In pass six, Derrick's restored knowledge supports the changed investigation while the anomalous face's destruction, Jack's survival, and recurrence termination remain outcomes and rule effects rather than epistemic state. The scenario can answer what happened during the sixth pass and what Derrick experienced immediately before it began. No chronology edge returns the sixth pass to the first; recurrence transitions, coordinate reuse, causal relations, and subjective order own those facts separately. Nothing in the scenario requires a capability claim merely because Derrick recognizes the loop or helps resolve it.

### Cross-Domain And Adversarial Replay

The composed model was replayed against retained IT/operations, medical, legal/compliance, scientific, education, investigative, distributed-control-plane, simulation, archive, source-control, and alternate-history cases:

- IT retries can combine bounded or unknown realized history, representative attempts, repeated inspection participations, control-plane intervention, environment branch lifecycle, incident knowledge, and recovery skill without deriving competence from a successful recovery.
- Medical recurrence can separate episodes, repeated review of one observation, monitoring context, forked treatment-course lineage when genuinely present, clinical understanding, practiced competence, licensure, and evidence authority without treating a license or outcome as ability.
- Legal and investigative workflows can separate scheduled obligations, repeated evidence review, oversight contexts, matter branches where lineage exists, subject knowledge, analytical capability, authorization, and source priority.
- Scientific trials can combine aggregate experiments, representative observations, instrumentation topology, experimental branches, learned theory, practical technique, and provenance without turning trial count into knowledge or skill.
- Education and credentialing retain knowledge, practiced capability, assessment evidence, and qualification as separate claims; a credential neither proves objective truth nor creates a capability transition.

Adversarial review retained the expected boundaries: topology cycles do not affect chronology comparison; exact chronology cycles still fail; causal cycles remain legal; repeated occurrence visits require distinct participations and deterministic track entries; recurrence iterations cannot stand in for unmaterialized aggregate attempts; lifecycle ordinals cannot become chronology coordinates; state chains cannot cross subjects, profiles, or scales silently; and provenance remains the owner of authority, applicability, and supersession.

### Limitation Classification

**Supported at the Phase 1 boundary:** exact, bounded, minimum, maximum, ranged, unknown, representative, and unmaterialized realized recurrence histories; repeated participation in one concrete occurrence; typed extratemporal context topology; append-only timeline-branch lifecycle; independent epistemic and capability progression; retained/restored state; deterministic recurrence policy; and acyclic chronology alongside independently typed causal, recurrence, participation, and topology relations.

**Explicitly deferred:** participation-relative state activation when two visits to one occurrence require different state boundaries; applicability-aware gold-layer resolution that combines lifecycle or state claims with provenance authority and reader/source scope; generic typed destination or replacement bindings shared across lifecycle-bearing registries; transitive context-topology inference; and cross-scale capability conversion or credential/assessment-derived capability. These are separable future services and do not block Phase 2 schema composition.

**Outside the intended Phase 1 framework boundary:** automatic synthesis of omitted attempts or occurrences; inference of truth, knowledge, competence, or expertise from elapsed time, repetition, credentials, or successful outcomes; a general action, counterfactual, transaction, or effect-execution engine; and treating every environment, case, clinical course, or experiment as a branch without actual fork lineage.

Civil-calendar schedules remain intentionally bounded to years 0001-9999, while unbounded fictional, negative, and far-future coordinates use chronology-step schedules and chronology registries. Direct context queries remain non-transitive by contract. Entry-relative queries are the required deterministic surface when one subject revisits one occurrence; occurrence-relative convenience queries correctly reject that ambiguous boundary.

### Phase 1 Decision

Phase 1 passes its exit gate. No V37/V38 integrity defect or V39-V44 composition defect blocks the effective project schema service. The retained Loki and Derrick scenarios pass without invented chronology cycles, occurrence duplication, unsupported numeric precision, or silent state transfer. No V45 is justified by this stabilization round. The accepted next step is Phase 2, **Effective Project Schema Service**, beginning with Phase 2.1's domain-neutral `EffectiveProjectSchema` contract.

## Post-Stabilization Pressure Expansion

After the Phase 1.9 record was confirmed, five externally source-grounded probes deliberately widened the candidate portfolio beyond the Loki and Derrick temporal cases. The prior exit decision remains the correct result for the portfolio executed at that gate; these later findings reopen Phase 1 rather than rewriting the historical result.

Source grounding used Shane Carruth's explanation that *Primer* intentionally withholds information unavailable to Abe and Aaron; Eric Heisserer's *Arrival* screenplay and its future Shang disclosure; Christopher Nolan's discussion of *Memento* as an organically unreliable narrator supported by visual and documentary memory aids; the official *Doctor Who* River Song profile's reverse-order meetings; and the *Westworld* creators' and cast's discussion of copied Dolores identities occupying different Host bodies. Exact future implementation probes must retain those evidence boundaries and must not substitute fan reconstruction for source-established mechanics.

### Primer: Deliberately Ambiguous Chronology

The current model can preserve uncertain bounds, incomparable positions, absent exact relations, competing provenance assertions, and explicit unresolved authority. It therefore represents that chronology is unknown. It cannot yet preserve several named, internally coherent structural reconstructions and query each one without either inserting every candidate relation into canonical chronology or flattening the interpretations into opaque assertion values.

This is a reusable gap rather than a Primer-only convenience. IT incident analysis, medical differential diagnosis, legal or investigative reconstruction, and scientific causal modeling also need candidate structures that share canonical records while remaining explicitly hypothetical. Interpretation membership must not establish truth, source priority, continuity, branch identity, or canonical chronology.

**Result:** partially supported; requires a bounded structural-interpretation capability.

### Arrival: Backward Causal Knowledge

The current separation passes this probe. The future Shang conversation remains a future occurrence. Louise's present acquisition of its information is a present epistemic-state transition with the future occurrence as a source and causal contributor. Her present call can help cause the later conversation, producing a legal causal cycle while both occurrence positions remain unchanged and chronology remains acyclic. Nonlinear access does not make every coordinate system comparable.

**Result:** supported; retained as a regression control for structural interpretations and participant-relative chronology.

### Memento: Fundamentally Unreliable Subjective Memory

The current model separates objective occurrence chronology, presentation order, Leonard's subjective track, memory availability and completeness, belief attitude, documentary aids, manipulation, and provenance-backed truth. A memory may be fully available to Leonard while its content remains disputed, false, confabulated, or contradicted. The epistemic record states what Leonard can access or believes; it does not certify the payload.

The later normalized-content and relationship work must preserve stable proposition targets so memories and beliefs can address claims such as an alleged killer relationship rather than only an entity or occurrence. V45 must also prove that competing event reconstructions can reuse those targets without making either interpretation canonical.

**Result:** core epistemic semantics supported; retained as an ambiguity, payload-target, and reconstruction control.

### Doctor Who: Participant-Relative Chronology

Occurrence bindings and independent tracks can currently place one shared meeting on several chronology axes. The remaining defect is association: one `occurrence_participation` carries only one chronology-context reference, while occurrence bindings do not identify which position applies to which participant. A Doctor/River meeting can therefore list both personal positions, but a query cannot distinguish the Doctor-relative binding from the River-relative binding without applying every occurrence position to both participants or inventing duplicate participations.

The same problem occurs in distributed systems when one operation participates in event time, processing time, ingestion time, business time, and observer-local time. The required service is a stable many-to-many binding from participation or track entry to existing occurrence chronology bindings. It must not create precedence, and it should provide a deterministic boundary for state changes during repeated visits to one occurrence.

**Result:** partially supported; requires participant-relative chronology bindings.

### Westworld: Hosted Identity And Embodiment

Entities, continuity-bound incarnations, identity phases, cloning, derivation, and reconciliation can distinguish several Westworld identity relationships. They do not own a body or carrier independently from the identity occupying it, record multiple active or dormant identities in one carrier, move one control unit or identity across carriers, identify the active controller at a boundary, or distinguish copied identities that diverge after transfer.

Treating a Host body as an incarnation or every persona as an identity phase would erase the distinction among persistent identity, physical or virtual carrier, occupancy, control, copying, and divergence. The same need appears outside narrative media in software processes and containers, agents and runtimes, avatars, simulations, and other systems where logical identity and execution carrier are independent.

**Result:** unsupported without approximation; requires a bounded hosted-identity and embodiment capability.

### Durable Testing Promotion

The methodology now retains `SCENARIO-PRIMER`, `SCENARIO-ARRIVAL`, `SCENARIO-MEMENTO`, `SCENARIO-DOCTOR-WHO`, and `SCENARIO-WESTWORLD`. It also adds `PRESSURE-STRUCTURAL-INTERPRETATION`, `PRESSURE-PARTICIPANT-CHRONOLOGY`, and `PRESSURE-HOSTED-IDENTITY` so these discoveries survive context loss and future candidate rotation. Each family includes cross-domain controls and explicit ownership questions rather than relying on a work title as a test specification.

A follow-up audit of the older candidate catalog found four composed regressions that likewise should not depend on candidate rotation. `SCENARIO-PARODY-DERIVATION` preserves the paired parody tests that exposed V13's separation of lineage, production, rights, and legal status. `SCENARIO-SERIALIZED-ADAPTATION` preserves the irregular serialization, manifestation, mapping, and distribution combinations that drove V3-V7. `SCENARIO-CONTINUITY-IDENTITY` preserves the reboot, counterpart, recast, regeneration, mantle, clone, composite, and crossover distinctions that drove V16-V18. `SCENARIO-TEXTUAL-TRADITION` preserves the work, evidence artifact, edition, compilation, posthumous publication, editorial reconstruction, and competing-text questions represented by Tolkien's legendarium and provides an additional V45 ambiguity control.

These four scenarios retain stable structural questions, not unverified franchise lore. Concrete title-specific claims remain conceptual until source-grounded, and the serialized scenario deliberately rotates an additional work so permanent coverage does not become overfit to one publication ecosystem.

### Revised Phase 1 Recommendation

Phase 1 reopens for three bounded versions followed by another stabilization gate:

1. V45 should implement **Competing Structural Interpretations** without moving evidence authority out of provenance or candidate edges into canonical chronology.
2. V46 should implement **Participation Chronology Bindings** and close participant-relative state boundaries without duplicating occurrences or participations.
3. V47 should implement **Hosted Identity And Embodiment** while preserving the existing entity, incarnation, phase, relationship, occurrence, state, and reconciliation ownership boundaries.

The stabilization phase should then replay the V45-V47 scenarios together with Loki, Derrick, the four promoted foundational narrative scenarios, the complete permanent baseline, full project compatibility, and the retained cross-industry portfolio. V47 pressure later inserted bounded V48 carrier-topology work before that replay, and the post-V48 layer audit subsequently inserted V49 hosting pack-boundary reconciliation. The current plan therefore owns V49 under Phase 1.14 and the expanded V39-V49 gate under Phase 1.15. Phase 2 must wait until that gate either passes or explicitly defers a remaining capability with maintainer approval.

## V45 - Competing Structural Interpretations

**Implemented by:** `2ea19e4` (`Implement V45 structural interpretations`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-INTERPRETATION`, `CONF-PROVENANCE`, `CONF-CHRONOLOGY`, `CONF-OCCURRENCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `PARITY-COMMAND-SURFACE`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-PRIMER`, `SCENARIO-MEMENTO`, `SCENARIO-TEXTUAL-TRADITION`, `PRESSURE-STRUCTURAL-INTERPRETATION`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-WORK-CONTINUITY`, `PRESSURE-ENTITY-IDENTITY`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** Externally source-grounded Primer ambiguity and Memento reconstruction controls; a conceptual Tolkien textual-tradition reconstruction unless exact publication claims are separately source-grounded; synthetic IT incident hypotheses, medical differential diagnoses, legal case theories, investigative reconstructions, and scientific causal models; compatible, competing, and mutually exclusive sets; canonical and deferred provenance-claim members; local precedence, causal, correspondence, and candidate-equivalence relations; unresolved authority, ties, and incomparable evidence; malformed inverse definitions, duplicate structures, cycles, provider collisions, and recursive interpretation attempts.

**Superseded assumption:** Preserving uncertainty about individual records is sufficient to represent several named, internally coherent candidate structures.

**Architectural promotion:** Structural interpretation becomes a domain-neutral core service rather than a narrative chronology convention.

V45 introduces an independently versioned structural-interpretation registry. An interpretation owns stable candidate identity, typed membership references, interpretation-local relations, and membership in comparison sets. It is not a continuity, branch, source, authority rule, canonical chronology, or factual assertion. Candidate structures reuse canonical record IDs instead of copying occurrences, positions, relations, branches, entities, or claims.

Relation definitions follow the established typed-relationship contract: packs allow relation IDs while the project registry declares inverse, symmetry, canonical direction, and local acyclic-group behavior. Candidate edges are validated and queried only inside their owning interpretation. They never enter canonical chronology closure, occurrence causality, entity reconciliation, or another registry's graph.

Compatible, competing, and mutually exclusive sets remain conservative. The structural service reports compatible coexistence or an unresolved candidate set and never chooses a winner from membership, lifecycle, order, or relation count. Provenance may target every structural record, and ordinary claim authority may compare source-backed assertions, but evidence, source priority, applicability, supersession, and factual resolution remain provenance-owned.

Claim membership uses a deliberate two-stage composition boundary. Canonical targets resolve when interpretations load. `provenance-claim` IDs remain typed deferred references until provenance loads with interpretation records exposed as subjects; project composition then validates those claim keys. This permits claims to support interpretations and interpretations to include claims without a circular registry owner.

V45 adds interpretation schema 1, project manifest schema 10, core pack version 36, a paired `interpretation` conformance suite, and provenance/project-composition integration coverage. It does not add probabilistic ranking, automatic theory generation, nested interpretations, an arbitrary expression engine, canonical graph mutation, interpretation-ID reconciliation, a general analytical truth resolver, or UI/editor behavior.

## Testing After V45

### Executed Coverage

The V45 implementation-confirmation baseline passed all fifteen registered conformance suites in Python, PowerShell 7, and Windows PowerShell 5.1 with matching canonicalized semantic summaries. The `full-release` compatibility profile passed all six registered checks: Visualization, Obsidian QA, root discovery, artifact lifecycle, isolated framework extraction, and three-runtime rendering. Ruff, PowerShell formatting in both supported runtimes, work-annotation validation, and workflow policy also remained green. Canonical generated output was unchanged and redirected artifacts were removed.

Post-confirmation focused execution replayed `CONF-INTERPRETATION`, `CONF-PROVENANCE`, and `CONF-CHRONOLOGY` in all three runtimes. Interpretation summaries matched at three candidate structures, seven members, four local relations, three comparison sets, seven relation types, four provenance target types, 36 rejected configurations, eight rejected queries, and a generated 128-member/127-relation structure. Provenance matched at twenty-one composed assertions, one claim-supersession relation, five authority vectors, 68 rejected configurations, five rejected queries, and 128 additional scale assertions. Chronology retained fourteen comparison vectors, eleven context queries, seventeen rejected fixtures, and its 128-relation context scale probe. No interpretation-local relation entered canonical chronology or changed an occurrence, entity, branch, claim, or source record.

### Narrative Reconstruction Replay

The retained externally source-grounded *Primer* control now passes `SCENARIO-PRIMER` and `PRESSURE-STRUCTURAL-INTERPRETATION`. Several candidate reconstructions can reuse the same occurrence and chronology-position records while declaring different local precedence or causal edges. Competing or mutually exclusive sets remain explicitly unresolved, and missing source information remains missing rather than being filled by a preferred fan reconstruction. Local acyclicity protects each candidate without weakening canonical chronology-cycle rejection.

The retained externally source-grounded *Memento* control now separates objective occurrences, presentation order, subjective track order, memory state, documentary aids, and normalized claims from candidate event reconstructions. Interpretations may reuse those occurrences and claims and relate them locally through precedence, causality, correspondence, or candidate equivalence. A fully available memory or coherent reconstruction still does not certify its payload, override provenance, or become canonical fact.

The conceptual Tolkien textual-tradition control likewise permits competing editorial or scholarly structures to reference shared works, source segments, evidence artifacts, editions, and claims without duplicating or redefining them. Exact publication or textual-history claims still require separate source grounding. An interpretation can organize a proposed reconstruction, but it cannot silently become canonical work structure, continuity, source authority, or accepted textual history.

### Cross-Domain And Adversarial Replay

Synthetic cross-domain replays confirmed the domain-neutral boundary:

- IT incident hypotheses can be competing root-cause structures or compatible contributing-failure structures while logs, observations, and source authority remain provenance-owned.
- Medical differential diagnoses can organize candidate findings and causal relations without asserting a diagnosis, ranking probability, or becoming a clinical decision engine.
- Legal case theories and investigative reconstructions can share people, events, evidence, and claims while remaining unresolved and without inferring guilt, liability, or an official finding.
- Scientific causal models can reuse observations, trials, entities, and claims while preserving incompatible or source-incomparable explanations without inventing statistics or model selection.

Adversarial pressure retained fail-closed rejection of recursive or nested interpretation targets, interpretation-local precedence cycles, self-relations, duplicate canonical or inverse edges, malformed inverse declarations, unknown providers, provider collisions, missing deferred claims, duplicate comparison sets, and attempts to use lifecycle as acceptance state. Schema 1 intentionally permits only flat candidate structures; a candidate may reference canonical records and claims but cannot contain another interpretation or its internal records. Compatible sets report coexistence, while competing and mutually exclusive sets remain unresolved. None selects a winner from membership, relation count, lifecycle, or evidence presence.

### Findings And V46 Recommendation

No implementation defect, parity defect, compatibility regression, or new durable test-family requirement was found. The existing candidate catalog and `PRESSURE-STRUCTURAL-INTERPRETATION` family covered the round, so the testing methodology did not need revision. Probabilistic ranking, automatic hypothesis generation, nested interpretations, interpretation-ID reconciliation, analytical truth resolution, and UI/editor behavior remain explicit later capabilities rather than V45 failures.

V46 should proceed with **Participation Chronology Bindings**. It should let one occurrence participation or track entry bind to several applicable chronology positions and contexts without duplicating the occurrence, while permitting another participant in that same occurrence to receive a different set. It must preserve incomparable chronology systems, repeated participation, participant-relative state boundaries, and exact rejection of bindings unrelated to the occurrence. *Doctor Who* and *Arrival* remain the primary narrative controls, with distributed event, workflow, healthcare, legal, and scientific chronology systems providing cross-domain pressure. Hosted identity and embodiment remain reserved for V47.

## V46 - Participation Chronology Bindings

**Implemented by:** `1185e0d` (`Implement V46 participation chronology bindings`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-CHRONOLOGY`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `PARITY-COMMAND-SURFACE`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-DOCTOR-WHO`, `SCENARIO-ARRIVAL`, `SCENARIO-DERRICK`, `SCENARIO-LOKI`, `PRESSURE-PARTICIPANT-CHRONOLOGY`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-TEMPORAL-COMPOSITION`, `PRESSURE-EPISTEMIC-STATE`, `PRESSURE-CAPABILITY-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** Externally source-grounded Doctor/River reverse-order meetings and multi-Doctor encounters; externally source-grounded *Arrival* backward-causal knowledge as a negative control; retained Derrick and Loki repeated-participation/state controls; synthetic distributed event, processing, ingestion, business, observer, and control-plane clocks; workflow, clinical-course, legal-case, and experiment-relative axes; one participation using several position/context pairs; distinct participants selecting different bindings from one occurrence; track-entry-specific additions; repeated visits with exact state activation boundaries; incomparable positions; cross-occurrence links, context/coordinate mismatch, duplicate effective links, unknown targets, ambiguous occurrence-level state lookup, and oversized link sets.

**Superseded assumption:** Occurrence-level chronology bindings plus one optional participation context are sufficient to identify which temporal positions apply to each involvement.

**Architectural promotion:** Participant-relative chronology selection and entry-relative state boundaries become domain-neutral occurrence services rather than narrative time-travel conventions.

V46 adds stable participation-chronology link records. Each link belongs to either one occurrence participation or one track entry, references one existing binding on that same occurrence, and may identify the chronology context in which that position applies. Participation-level links apply to every track entry for that participation; entry-level links add only the positions needed by that placement. Redundant inherited links, cross-occurrence targets, unknown contexts, and context/position coordinate-system mismatches fail closed.

The links select existing position/context pairs but never own positions, compare coordinates, create mappings, or add precedence. Chronology remains the sole owner of coordinate systems, positions, contexts, mappings, and exact order. Occurrence remains the owner of the concrete happening, participation identity, track placement, and this involvement-specific selection layer.

State transitions retain their canonical activation occurrence and may add one exact activation track entry per affected track. A repeated occurrence on a track requires that entry-relative boundary; an unambiguous occurrence may continue using the existing compact form. Entry-relative state lookup, chain validation, and carryover validation use the exact track ordinal, while occurrence-relative lookup continues to reject ambiguity rather than choosing one visit.

V46 is expected to advance the occurrence registry to schema 10 and core to pack version 37 without changing the project manifest schema. It will not add vector clocks, chronology inference, automatic personal timelines, participation-relative occurrence-transition endpoints, cross-context precedence, hosted identity or embodiment, a gold-layer truth resolver, or UI/editor behavior.

## Testing After V46

The V46 implementation-validation pass executed all fifteen registered `baseline` suites in Python, PowerShell 7, and Windows PowerShell 5.1. Every suite ID, status, and canonicalized semantic summary matched. Individually measured runtimes were 41.1, 187.3, and 348.7 seconds. The composed project now uses occurrence schema 10, core pack version 37, 122 enabled capabilities, 1,014 controlled values across 132 namespaces, and 66 provenance subject types. Project composition performs two deterministic full loads and rejects thirteen invalid cross-registry compositions.

Occurrence conformance now reports 139 query/evaluation assertions, 160 malformed registries, and generated 128-record participation-chronology-link probes in addition to the existing branch-state, cardinality, and participation/track-entry scale families. The positive fixture proves participant-specific world, personal, control, and presentation selections; inherited plus entry-specific lookup; incomparable axes; and two state changes at distinct entries for one repeated occurrence. Negative vectors reject the legacy singular participation context, unknown or cross-occurrence links, context/coordinate mismatches, semantic duplicates, redundantly inherited entry links, and malformed or missing repeated-visit activation entries. Provenance resolves the new stable link target, and project composition rejects a registry whose required capability is disabled.

The `full-release` compatibility profile passed all six checks in 169.9 seconds. Visualization retained 15 nodes and 121 relationships. QA retained 16 notes, 121 relationships, 71 data references, one bounded graph, two bounded pages, and all 34 normalized files. All twelve root-discovery launches passed; artifact lifecycle rejected six unsafe destinations; isolated extraction copied 217 files and passed six portable suites in all three runtimes; and each renderer produced the same nonblank 298,269-byte SVG with identical SHA-256 hashes. Canonical outputs were unchanged and redirected artifacts were removed.

Ruff formatting and lint passed all 40 Python files. The PowerShell formatter passed all 41 files in both supported runtimes with no changes or over-limit lines. Work-annotation validation passed 319 eligible files and all 22 fixtures, actionlint accepted every workflow, and `git diff --check` was clean. The two-part implementation confirmation records the implementation under `1185e0d`.

### Post-Confirmation Pressure Execution

The V46 pressure round executed `SCENARIO-DOCTOR-WHO`, `SCENARIO-ARRIVAL`, `SCENARIO-DERRICK`, `SCENARIO-LOKI`, `PRESSURE-PARTICIPANT-CHRONOLOGY`, `PRESSURE-TEMPORAL-TOPOLOGY`, `PRESSURE-TEMPORAL-COMPOSITION`, `PRESSURE-EPISTEMIC-STATE`, `PRESSURE-CAPABILITY-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`. It used the complete three-runtime baseline and `full-release` compatibility results recorded above as the unchanged executable closure gate, then reran the focused occurrence suite after implementation confirmation. Python, PowerShell 7, and Windows PowerShell 5.1 again produced identical schema-10 summaries with 139 query/evaluation assertions, 160 malformed registries, and all four 128-record scale families.

The Doctor Who controls were externally source-grounded against the official [River Song character history](https://www.doctorwho.tv/characters/river-song), which describes the Doctor and River as meeting broadly in reverse order, and the official [Day of the Doctor](https://www.doctorwho.tv/stories/the-day-of-the-doctor) and [multi-Doctor story review](https://www.doctorwho.tv/news-and-features/what-are-the-biggest-multi-doctor-stories), which identify the Tenth, Eleventh, War, and other incarnations participating in one cross-period event. The Arrival control used Paramount's [official film synopsis](https://www.paramountpictures.com/movies/arrival) and the archived [official screenplay](https://web.archive.org/web/20161209073228/http://www.paramountguilds.com/pdf/arrival.pdf), particularly the future Shang encounter that supplies Louise with the private number and words used during the earlier call. Derrick and Loki reused their previously recorded source-grounded reviews. Cross-industry probes were synthetic and contained no real patient, case, operational, or experimental data.

### Doctor Who Participant Chronology Replay

One Doctor/River meeting remains one occurrence with universe, Doctor-personal, River-personal, presentation, and any project-supported local bindings. The Doctor's participation selects the shared universe position plus the Doctor-personal position; River's selects the shared position plus River's position; either may select presentation only where that placement requires it. Their personal tracks may order the same meetings differently without a chronology cycle, and one participant never inherits every binding merely because it exists on the occurrence.

A multi-Doctor meeting likewise remains one occurrence. Each incarnation may participate as its existing `entity-incarnation` subject, select the shared world binding and its own personal position, and remain related to the stable Doctor entity through the entity registry. Regeneration and incarnation continuity therefore retain entity and identity-phase ownership. V46 neither duplicates the meeting nor turns conceptual identity into chronology, and no participant-specific selection creates precedence between incomparable systems.

### Arrival Backward-Causality Control

The present phone call and future Shang meeting remain distinct occurrences at their own positions. The future encounter may support a present epistemic transition and a causal relation back to the call; the call may in turn participate in the causal chain leading to that future meeting. Causal cycles remain legal outside exact chronology. Louise's present participation can select the chronology positions applicable to her experience without moving either occurrence, treating future knowledge as physical travel, or making every perceived coordinate comparable. V46 therefore composes with the V43 epistemic-state service but does not absorb its ownership.

### Loki And Derrick Regression Controls

Loki's self-pruning remains one concrete occurrence with earlier recipient and later agent participations. Each participation selects the shared applicable coordinate plus its distinct personal or TVA-context position, and track-entry lookup distinguishes the two visits. A state transition attached to that repeated occurrence can select the exact activation entry rather than choosing the first visit. TVA context topology, branch lifecycle, retained understanding, and accumulated expertise remain separate services.

Derrick's abandoned-temple passes remain distinct occurrences in distinct recurrence iterations that reuse external coordinates; V46 links do not collapse them into repeated participations in one occurrence. Derrick's restored knowledge activates at the exact applicable track boundary before the final pass, while Colin receives no corresponding state transition. The replay still answers what happened in a chosen iteration and what Derrick experienced immediately before it without a chronology cycle or silent cross-subject transfer.

### Cross-Domain And Adversarial Pressure

Synthetic distributed-event probes separated event, processing, ingestion, business, observer, and control-plane axes. Several coordinates may describe one concrete event and be selected per involvement, but an ingestion operation, retry, later log review, or control-plane intervention remains a separate occurrence when it is itself a new happening. The same boundary held for clinical administration versus chart review, a legal incident versus later evidence review, and an experiment versus later instrument or researcher observations. Workflow, clinical-course, case-order, experiment-order, and participant-personal coordinates remained incomparable unless chronology already supplied a relation or mapping.

Adversarial probes retained empty additive selection, different selections for participations sharing an occurrence, inherited participation links plus nonredundant entry additions, exact repeated-visit state activation, and large link sets. Permanent malformed cases reject legacy singular contexts, unknown target types or IDs, unrelated occurrence bindings, unknown contexts, coordinate-system mismatch, semantic duplicates, redundant inherited links, unknown activation entries, wrong-occurrence entries, duplicate entries for one track, and entries outside the transition's affected tracks. No selection created a chronology edge, inferred an automatic personal timeline, or weakened provenance authority.

### Findings And V47 Recommendation

V46 passes. The round found no `implementation-defect`, `parity-defect`, `compatibility-regression`, `missing-capability`, or `accepted-contract-change`. Hosted identity, embodiment, inferred chronology, reverse-index convenience APIs, and UI/editor behavior remain deliberate later boundaries rather than V46 failures. The existing candidate catalog, retained scenario IDs, and `PRESSURE-PARTICIPANT-CHRONOLOGY` family covered the round, so `Framework/testing_methodology.md` required no revision.

V47 should proceed with **Hosted Identity And Embodiment** as already scoped in the platform plan. It should separate identity-bearing subjects from physical or virtual carriers; preserve occupancy, control, transfer, copy, divergence, and carrier lifecycle with explicit boundaries; reuse incarnation, identity-phase, reconciliation, occurrence, and state services; and pressure-test Westworld alongside software processes and containers, agents and runtimes, avatars, simulations, and carefully bounded medical cases. It must not collapse hosting into incarnation identity, infer equivalence from co-residence, or move provenance authority into carrier state.

## V47 - Hosted Identity And Embodiment

**Implemented by:** `0d3a532` (`Implement V47 hosted identity embodiment`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-ENTITY`, `CONF-RECONCILIATION`, `CONF-OCCURRENCE`, `CONF-HOSTING`, `CONF-INTERPRETATION`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `PARITY-COMMAND-SURFACE`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-WESTWORLD`, `SCENARIO-CONTINUITY-IDENTITY`, `SCENARIO-LOKI`, `SCENARIO-DERRICK`, `PRESSURE-HOSTED-IDENTITY`, `PRESSURE-ENTITY-IDENTITY`, `PRESSURE-PARTICIPANT-CHRONOLOGY`, `PRESSURE-EPISTEMIC-STATE`, `PRESSURE-CAPABILITY-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** The retained externally source-grounded *Westworld* control for Dolores/Wyatt identity states, pearls or control units, Host bodies, copied identities, changing control, and later divergence; the retained continuity/identity scenario as a negative control against treating hosting as incarnation, counterpart, phase, or reconciliation; synthetic software processes and containers, agents and runtimes, avatars and simulations, one logical identity moving across execution carriers, one carrier holding active and dormant identities, co-control without automatic priority, carrier destruction without identity retirement, copy with retained source occupancy, control handoff, distinct carrier tracks meeting at one occurrence, unsupported provider types, cross-track boundaries, missing identity relationships, semantic duplicates, and 128-record carrier/occupancy scale; carefully bounded synthetic medical cases that separate a person or legal identity from a body, device, graft, or support system without making clinical, legal, or philosophical identity determinations.

**Superseded assumption:** Entity incarnation, identity phase, derivation, reconciliation, and ordinary state transitions are sufficient to describe every relationship between a stable identity and the body or runtime through which it acts.

**Architectural promotion:** Hosted identity and embodiment become a domain-neutral core service rather than a narrative body/persona convention.

V47 introduces `Project_Config/hosting.yaml` and hosted-identity schema 1. A host carrier owns stable carrier identity, configuration lifecycle, pack-owned kind, and one occurrence-track lifecycle with inclusive activation and optional exclusive termination. Occupancy records bind an existing identity target to one carrier and role over an exact interval. Several identities may occupy one carrier and one identity may occupy several carriers; neither shape asserts equivalence, continuity, replacement, derivation, control priority, or truth.

Move, copy, and control-handoff transitions reuse one concrete occurrence plus exact source and target track entries. Move preserves one identity target across carriers. Copy keeps the source occupancy active, requires a distinct target identity and carrier, and cites an existing identity-relationship record so derivation semantics remain identity-owned. Control handoff changes controlling occupancies on one carrier without asserting identity lineage. Carrier and occupancy termination are exclusive, making current occupant/controller queries deterministic at an explicit boundary while preserving valid co-control as several results.

Carriers are reconciliation and provenance targets; occupancies and transitions are provenance-addressable operational records. Entity, incarnation, phase, derivation, and divergence stay in the identity registry; occurrence and track order stay in occurrence; subject knowledge, capability, and other state stay in state services; evidence and truth resolution stay in provenance. V47 advances the project manifest to schema 11 and core to pack version 38, adds one baseline-only paired hosting suite, and extends project composition, interpretation targeting, provenance closure, isolated extraction, and permanent methodology coverage. It does not add automatic identity continuity, philosophical personhood resolution, singular-controller priority, carrier-specific state machines with repeated activation intervals, inferred moves/copies, medical or legal conclusions, graph/UI behavior, or migration services.

## Testing After V47

The V47 implementation-validation pass executed all sixteen registered `baseline` suites in Python, PowerShell 7, and Windows PowerShell 5.1. Every suite passed with matching IDs, statuses, and canonicalized semantic summaries; individually measured runtimes were 43.4, 198.2, and 357.7 seconds. The focused hosting suite produced the same schema-1 summary in every runtime: three carriers, six occupancies, three transitions, nine service assertions, 31 rejected configurations, seven rejected queries, and generated 128-carrier and 128-occupancy scale probes. Project composition now uses manifest schema 11, core pack version 38, 123 enabled capabilities, 1,039 controlled values across 137 namespaces, 25 reconciliation target types, 69 provenance subject types, and fourteen rejected invalid compositions.

Ruff passed all 42 Python files. The repository PowerShell formatter passed all 43 files in PowerShell 7 and Windows PowerShell 5.1 with no long lines after one mechanical reconciliation-harness correction. Work-annotation validation passed all 22 fixtures and 325 eligible files containing ten valid annotations with no findings, while actionlint passed every workflow. The `full-release` compatibility profile passed all six checks in 176.9 seconds: Visualization retained 15 nodes and 121 relationships; QA retained 16 notes, 121 relationships, 71 data references, and all 34 normalized files; all 12 root launches passed; artifact ownership and six unsafe destinations were enforced; isolated extraction copied 224 files and passed its six portable suites in all three runtimes; and all three renderers produced the same nonblank 298,269-byte SVG and SHA-256 hash. Canonical outputs remained unchanged and redirected artifacts were removed.

### Post-Confirmation Pressure Execution

**Pressure corrections:** `1aba9bd` (`Close V47 pressure-test coverage`)

The V47 pressure round executed `SCENARIO-WESTWORLD`, `SCENARIO-CONTINUITY-IDENTITY`, `PRESSURE-HOSTED-IDENTITY`, `PRESSURE-ENTITY-IDENTITY`, `PRESSURE-PARTICIPANT-CHRONOLOGY`, `PRESSURE-EPISTEMIC-STATE`, `PRESSURE-CAPABILITY-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`. It reused the complete three-runtime baseline and `full-release` compatibility results recorded above as the unchanged implementation-closure gate, then reran `CONF-HOSTING` directly after strengthening its permanent positive fixture. Python, PowerShell 7, and Windows PowerShell 5.1 produced identical schema-1 summaries with three carriers, nine occupancies, three transitions, eleven service assertions, 31 rejected configurations, seven rejected queries, and generated 128-carrier and 128-occupancy scale probes.

The fixture correction closes one `test-coverage-defect`. Active and co-resident occupancy, sequential control, move, copy, and handoff were already executable, but the permanent positive corpus did not explicitly prove the documented dormant and co-control shapes. It now keeps an active and co-resident identity beside a dormant identity on one carrier and returns two simultaneous controllers in stable ID order without selecting a winner. No hosting runtime behavior changed.

### Westworld Hosted-Identity Replay

The replay was externally grounded against the [Season 2 recap](https://www.thewrap.com/westworld-season-2-explained-recap-finale-season-3-premiere/), which records Dolores leaving Westworld in a Charlotte Hale body with Host control-unit pearls, the [creator interview on the Season 3 identity reveal](https://www.thewrap.com/westworld-charlotte-hale-identity-dolores-copies-connells-musashi-evan-rachel-wood-pearls-control-units/), which confirms that Dolores copied herself, and the [Season 3 recap](https://www.denofgeek.com/tv/westworld-season-3-recap-incite-rehoboam-solomon/), which describes Dolores copies in Charlotte Hale, Martin Connells, and Sato bodies and Hale's later divergence from the original plan. These controls establish only the structural facts needed by this test; interpretive identity conclusions remain provenance-scoped claims.

V47 correctly keeps Dolores as a conceptual identity subject; Dolores/Wyatt layering as identity phase, persona, or subject state according to the claim being modeled; each copied and later-diverging Dolores as a distinct identity subject connected through explicit identity lineage; a pearl or control unit and a Host body as carriers rather than incarnations; direct identity occupancy and active control as bounded hosting records; and body destruction or replacement separate from identity retirement. Human Charlotte Hale, a Host body made in her appearance, and the copied Dolores identity controlling that body therefore remain distinct. Shared code, memory, appearance, or body never creates equivalence, continuity, reconciliation, or source authority automatically.

The replay also found one genuine `missing-capability`. A Westworld pearl can carry an identity while being installed in a separate Host body. V47 can register the pearl, the body, and direct occupancy, but it cannot state that one active carrier is installed in or hosted by another over a bounded interval. Duplicating the identity occupancy onto the body would erase the distinction between direct and indirect hosting; treating the pearl and body as one carrier would erase their independent lifecycle; and using an identity move when the pearl changes bodies would falsely say the identity left the pearl. This is carrier topology, not identity lineage, occurrence order, ordinary occupancy, or reconciliation.

### Continuity And Cross-Domain Controls

The retained continuity/identity negative control passed. Recasts, regenerations, alternate counterparts, clones, mantle successors, and continuity-bound incarnations continue to use entity relationships, incarnations, identity phases, and explicit reconciliation where appropriate. Moving one identity among direct carriers creates none of those records, while copying requires a distinct identity subject and an existing identity-relationship target. Co-residence and co-control likewise make no equivalence or shared-identity claim.

Synthetic portability probes reproduced the nested-carrier gap without importing narrative vocabulary. A process may execute in a container hosted by a VM; an agent may occupy a runtime inside a process or device; an avatar may project an identity through a simulation host; and a medical device may be installed in or attached to a body without becoming the person or proving any clinical or legal conclusion. Direct V47 occupancy remains valid at each chosen identity-to-carrier boundary, but the intermediate carrier chain cannot yet be preserved or traversed. All medical, legal, operational, and simulation cases were synthetic and made no real-world identity determination.

Adversarial review retained fail-closed behavior for unknown provider types or IDs, cross-track entries, unsupported roles and transition kinds, reversed or out-of-carrier intervals, missing copy lineage, same-subject copies, subject-changing moves, cross-carrier handoffs, semantic duplicates, invalid provenance targets, and carrier or occupancy scale. Carrier self-binding, nested cycles, transitive traversal, binding lifecycle, and direct-versus-indirect occupant queries are not malformed V47 cases because no carrier-binding surface exists yet; they become mandatory V48 coverage.

### Findings And V48 Recommendation

V47 passes its direct hosted-identity contract. The round found no `implementation-defect`, `parity-defect`, `compatibility-regression`, or `accepted-contract-change`. It corrected one permanent `test-coverage-defect` and identified one bounded `missing-capability`: carrier-to-carrier topology. The durable `SCENARIO-WESTWORLD`, `PRESSURE-HOSTED-IDENTITY`, and change-impact descriptions now retain nested carrier chains, direct/indirect occupancy separation, cycle rejection, and cross-domain stacks, so the finding cannot disappear during later context transitions.

V48 should implement **Nested Carrier Topology** before the expanded stabilization replay. It should add provenance-addressable, pack-typed child/parent carrier bindings with explicit activation and termination boundaries; preserve independent carrier and occupancy lifecycles; reject self-links, cycles, duplicates, and unsupported boundaries; expose deterministic direct and transitive carrier queries without silently promoting indirect occupancy; and model a control unit moving between bodies without moving or copying the identity stored in that unit. Westworld, process/container/VM, agent/runtime, avatar/simulation, and bounded device/body controls should remain the primary pressure portfolio. Phase 1.13 owns that work. At this point in the history, the former expanded stabilization gate moved to Phase 1.14 with V39-V48 composed; the post-V48 layer audit recorded below later inserted V49 as Phase 1.14 and moved stabilization to Phase 1.15.

## V48 - Nested Carrier Topology

**Implemented by:** `0f1a926` (`Implement V48 nested carrier topology`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-ENTITY`, `CONF-RECONCILIATION`, `CONF-OCCURRENCE`, `CONF-HOSTING`, `CONF-INTERPRETATION`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `PARITY-COMMAND-SURFACE`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-WESTWORLD`, `SCENARIO-CONTINUITY-IDENTITY`, `SCENARIO-DOCTOR-WHO`, `PRESSURE-HOSTED-IDENTITY`, `PRESSURE-ENTITY-IDENTITY`, `PRESSURE-PARTICIPANT-CHRONOLOGY`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** The retained externally source-grounded *Westworld* control for an identity-bearing pearl or control unit installed in successive Host bodies while the identity remains directly resident in the control unit; the retained continuity/identity scenario as a negative control against turning carrier reachability into incarnation, equivalence, or reconciliation; synthetic control-unit/body, process/container/virtual-machine, agent/runtime/process, avatar/simulation-host, and bounded device/body chains; physical installation, containment, attachment, virtual execution, and projection vocabulary supplied by packs; direct child/parent lookups, deterministic ancestor/descendant closure, direct versus reachable occupancy, binding activation and exclusive termination, child movement between parents without identity movement, independent carrier termination, unknown endpoints, self-links, static and boundary-specific cycles, semantic duplicates, unsupported kinds, cross-track boundary mismatches, and generated 128-binding chains.

**Superseded assumption:** Direct identity-to-carrier occupancy is sufficient to describe every physical or virtual hosting path through which that identity acts.

**Architectural promotion:** Bounded carrier-to-carrier topology becomes a domain-neutral hosted-identity service rather than a Westworld pearl/body or software container/runtime convention.

V48 adds provenance-addressable `host-carrier-binding` records to the existing hosted-identity registry. A binding relates one child carrier to one parent carrier with a pack-owned kind. Each side keeps its own lifecycle track and receives an explicit inclusive activation entry plus an optional exclusive termination entry. Paired boundaries must resolve to the same activation or termination occurrence, so cross-track synchronization is explicit without inventing an ordering or mapping between chronology systems.

The registry rejects unknown carriers, self-bindings, duplicate semantic intervals, unsupported kinds, boundaries outside either carrier lifecycle, mismatched paired occurrences, and every structural carrier cycle. Direct child and parent queries return only explicit active bindings. Transitive ancestor and descendant queries traverse active bindings deterministically, preserve path distance, and never rewrite an indirect identity as a direct occupant of an ancestor. Reachable-occupant queries therefore return the direct occupancy together with the carrier path through which it is reachable.

Moving a child carrier between parents is represented by ending one binding and activating another. An identity directly occupying that child receives no move, copy, handoff, incarnation, reconciliation, or state record unless the corresponding owning service records one independently. Carrier bindings are provenance targets but not reconciliation targets; carriers retain reconciliation ownership. V48 is expected to advance hosted-identity schema 1 to schema 2 and core pack version 38 to 39 without changing the project manifest schema or adding a new capability or conformance suite.

V48 does not add arbitrary containment graphs, automatic chronology mappings, identity continuity inference, recursive direct occupancy, carrier-specific repeated lifecycle intervals, inferred installation or movement, singular route selection when several active paths exist, philosophical personhood resolution, medical or legal conclusions, graph projection, or editor behavior.

## Testing After V48

The V48 implementation-validation pass executed all sixteen registered `baseline` suites in Python, PowerShell 7, and Windows PowerShell 5.1. Every suite passed with matching IDs, statuses, and canonicalized semantic summaries; exact-final runtimes were 48.0, 205.4, and 369.2 seconds. The composed project retains manifest schema 11 and 123 enabled capabilities while advancing hosted-identity to schema 2 and core to pack version 39. It now contains 138 controlled-value namespaces, 1,045 values, 25 reconciliation target types, and 70 provenance subject types. Project composition completed two deterministic full loads and rejected fourteen invalid cross-registry compositions.

Focused hosting conformance produced the same summary in all three runtimes: eight carriers, six bindings, ten direct occupancies, three transitions, 22 service assertions, 46 rejected configurations, 14 rejected queries, and generated 128-carrier, 128-occupancy, and 127-binding chain probes. The positive fixture moves one identity-bearing control unit between two bodies while its direct occupancy remains on the control unit, separately traverses runtime, process, container, and virtual-machine carriers, and synchronizes a runtime/host binding across independent protagonist and observer tracks through one occurrence. Reachable occupancy returns the exact carrier path and leaves direct virtual-machine occupancy empty. Negative vectors reject unknown or identical endpoints, unsupported kinds, unpaired or mismatched boundaries, out-of-lifecycle intervals, semantic duplicates, and structural cycles.

The `full-release` compatibility profile passed all six checks in 178.3 seconds. Visualization retained 15 nodes and 121 relationships. QA retained 16 notes, 121 relationships, 71 data references, one bounded graph, two bounded pages, and all 34 normalized files. All twelve root-discovery launches passed; artifact lifecycle rejected six unsafe destinations; isolated extraction copied 224 files and passed six portable suites in all three runtimes; and each renderer produced the same nonblank 298,269-byte SVG with identical SHA-256 hashes. Canonical outputs were unchanged and redirected artifacts were removed.

Ruff formatting and lint passed all 42 Python files. The PowerShell formatter passed all 43 files in PowerShell 7 and Windows PowerShell 5.1 with no drift or over-limit lines. Work-annotation validation passed 325 eligible files, ten annotations, and all 22 fixtures with no findings. The implementation is ready for its mandatory two-part confirmation; post-confirmation `SCENARIO-WESTWORLD`, continuity/identity, cross-domain, adversarial, provenance, and scale pressure remain pending.

### Post-Confirmation Pressure Execution

**Pressure corrections:** `92a12d1` (`Close V48 pressure-test coverage`)

The V48 pressure round executed `SCENARIO-WESTWORLD`, `SCENARIO-CONTINUITY-IDENTITY`, `SCENARIO-DOCTOR-WHO`, `PRESSURE-HOSTED-IDENTITY`, `PRESSURE-ENTITY-IDENTITY`, `PRESSURE-PARTICIPANT-CHRONOLOGY`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`. After correcting one permanent coverage gap, the complete sixteen-suite `baseline` passed in Python, PowerShell 7, and Windows PowerShell 5.1 with matching IDs, statuses, and canonicalized semantic summaries. Measured runtimes were 51.4, 209.0, and 371.2 seconds. Focused hosting remained at eight carriers, six bindings, ten occupancies, three transitions, 22 service assertions, 46 rejected configurations, 14 rejected queries, and generated 128-carrier, 128-occupancy, and 127-binding probes.

The `full-release` compatibility profile passed all six checks in 179.8 seconds. Visualization, QA, root discovery, artifact lifecycle, isolated extraction, and rendering all retained their V48 implementation-closure behavior. Canonical outputs remained protected, temporary outputs were removed, and no LoTM-specific project surface entered the isolated framework copy. Ruff passed the changed Python suite, the PowerShell formatter passed all 43 files in both supported runtimes with no drift or over-limit lines, work-annotation validation passed 325 eligible files and all 22 fixtures, actionlint accepted every workflow, and `git diff --check` remained clean.

### Westworld And Continuity Replay

The retained Westworld control now preserves the identity, control-unit, and Host-body layers without duplication. The identity remains directly resident in the pearl or control unit while one binding to a first body terminates and a second binding to another body activates at the shared boundary occurrence. Direct occupancy therefore remains on the control unit, reachable occupancy changes with the active carrier path, and no identity move, copy, handoff, incarnation, reconciliation, or truth claim is inferred. Independent control-unit and body lifecycles remain queryable, and several active routes remain several deterministic paths rather than producing an implicit preferred host.

The continuity/identity and Doctor Who controls remained negative boundaries. Recasts, regenerations, alternate counterparts, clones, mantle successors, identity phases, and continuity-bound incarnations still belong to entity and reconciliation services when applicable. A participant may still bind to several chronology systems without turning those chronology contexts into carriers, and a carrier chain creates no chronology mapping or ordering. Reachability through a body or runtime likewise does not make an indirect occupant a direct occupant, establish identity equivalence, or settle personhood.

### Cross-Domain, Adversarial, And Scale Pressure

The same topology held outside narrative vocabulary. Software identities can occupy a runtime that executes in a process contained in a container hosted by a virtual machine; agents can remain directly bound to their runtime while that runtime changes infrastructure; avatars can project through simulation hosts; and a device can be attached to a body without becoming the person or asserting any clinical or legal conclusion. A permanent cross-track fixture synchronizes one runtime/host activation across protagonist and observer entries only because both entries resolve to the same occurrence; it creates no automatic mapping between those tracks.

Adversarial probes retained fail-closed behavior for unknown endpoints, self-links, unsupported kinds, missing paired entries, activation or termination occurrence mismatches, boundaries outside either carrier lifecycle, semantic duplicates, and structural cycles. The structural-cycle rule remains deliberately conservative: a reversed carrier relationship is rejected even when proposed intervals do not overlap. Interval-aware cyclic reuse, repeated carrier lifecycle intervals, inferred bindings, and automatic route selection remain explicit exclusions rather than hidden partial behavior.

The 127-binding chain returned deterministic transitive paths without recursion failure or direct-occupancy promotion. Multiple active parent routes remained distinct paths. Child-carrier movement changed only active bindings, while identity occupancy stayed on the child. Cross-domain labels remained pack-owned and the LoTM registry remained empty, preserving layer portability.

### Provenance Correction And Findings

The round corrected one `test-coverage-defect`. Hosting conformance already proved that `host-carrier-binding` was a provenance target, and project composition counted the type, but the provenance suite loaded the canonical empty hosting registry and therefore did not exercise an actual assertion against a binding. The paired fixture now loads the focused carrier topology without unrelated occupancy identities, adds a source-backed assertion for `control-unit-body-b.binding_kind`, and verifies dispatch to the `installed-in` binding in all three runtimes. Provenance conformance now passes with 22 assertions, 17 claim keys, 23 evidence links and locators, 68 rejected configurations, five rejected queries, and its existing 128-assertion scale probe. The methodology now states that provider enumeration or counts alone do not prove provenance closure.

### Post-Pressure Layer Audit

V48's registry shape and runtime remain domain-neutral: they know only carriers, bounded carrier bindings, occupancies, transitions, occurrence boundaries, and provider interfaces. Westworld-specific subjects and terminology remain pressure scenarios and fixture examples, while the LoTM hosting registry remains empty. The layer audit nevertheless found one `accepted-contract-change` in pack composition. Core currently supplies a mixed starter vocabulary containing physical bodies, control units, avatars, vessels, runtimes, containers, virtual hosts, execution, and projection. Those values are individually reusable, but exposing all of them through core violates the stricter rule that an unselected domain capability and its vocabulary should remain absent.

The maintainer accepted a V49 **Hosting Pack Boundary Reconciliation** before expanded stabilization. V49 must preserve the generic hosting service while separating minimal universal structure from optional narrative/simulation, compute/runtime, and future industry-specific vocabulary. It must also decide whether hosting activation itself remains core or becomes opt-in, prove core-only and independently selected pack compositions, and keep absent vocabulary disabled without errors. This is a layering correction, not a V48 runtime or scenario failure.

V48 passes its implemented behavioral contract. The pressure round found no `implementation-defect`, `parity-defect`, `compatibility-regression`, or `missing-capability`; it corrected one permanent `test-coverage-defect`, and the subsequent layer audit accepted one bounded pack-ownership change for V49. Existing retained scenario IDs and pressure families cover the behavior, so no new scenario ID is required. Phase 1.13 is complete. Phase 1.14 now owns V49, and Phase 1.15 must perform the expanded stabilization replay with V39-V49 active together before Phase 2 begins.

## V49 - Hosting Pack Boundary Reconciliation

**Implemented by:** `cf3cf64` (`Implement V49 hosting pack boundary reconciliation`)

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-ENTITY`, `CONF-RECONCILIATION`, `CONF-OCCURRENCE`, `CONF-HOSTING`, `CONF-INTERPRETATION`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `PARITY-COMMAND-SURFACE`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-WESTWORLD`, `SCENARIO-CONTINUITY-IDENTITY`, `PRESSURE-HOSTED-IDENTITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

**Proposed candidates:** Core-only and absent-hosting projects; independent foundation, narrative, simulation, compute, and combined pack compositions; the retained *Westworld* control-unit/body scenario; synthetic process/container/virtual-machine and avatar/simulation-host chains; an empty disabled registry; nonempty records attempted without capability activation; selected and unselected carrier and binding kinds; hosting provenance and reconciliation provider exposure; malformed dependencies and vocabulary leakage; and generated carrier, occupancy, and binding scale probes.

**Superseded assumption:** A domain-neutral hosting runtime and all broadly reusable hosting labels can live in core merely because each individual label has uses in more than one domain.

**Architectural extraction:** Hosted-identity activation and vocabulary move out of core into one optional domain-neutral foundation plus independently selectable narrative, simulation, and compute extensions.

V49 advances core to pack version 40 and removes the `hosted-identity-embodiment` capability, hosting controlled-value namespaces, and hosting provider vocabulary from that universal pack. `hosting-foundation` now owns the executable capability, carrier/binding/occupancy/transition mechanics, generic installation/containment/attachment labels, and hosting provenance and reconciliation target types. `hosting-narrative` contributes only physical-body and vessel labels; `hosting-simulation` contributes control-unit, avatar, and projection labels; and `hosting-compute` contributes runtime, container, virtual-host, and execution labels. Medical, legal, and future industry vocabulary remains absent until an owning pack deliberately supplies it.

The LoTM project selects the foundation and narrative extensions because its schema intentionally supports physical embodiment, while simulation and compute vocabulary remain unavailable. An unrelated project may retain an empty schema-2 hosting registry while the capability is disabled. An unselected foundation registers no hosting target types; a selected but disabled foundation registers empty typed providers for composition closure without enabling behavior. Any nonempty hosting record still fails closed until the capability is enabled. The same runtime code therefore remains portable without making hosting mandatory or leaking domain vocabulary.

Paired conformance composes core-only, foundation, narrative, simulation, compute, and combined pack sets and checks the exact carrier and binding vocabulary exposed by each. The behavioral fixture deliberately selects the combined set so prior V47-V48 topology, transition, malformed-input, provenance, and scale coverage remains meaningful after the ownership split. No hosting record schema, query result, chronology boundary, identity rule, or provenance assertion semantics change in V49.

## Testing After V49

The V49 implementation-validation pass executed all sixteen registered `baseline` suites in Python, PowerShell 7, and Windows PowerShell 5.1. Every suite passed with matching IDs, statuses, and canonicalized semantic summaries; exact-final runtimes were 51.7, 220.3, and 394.1 seconds. The composed project retains manifest schema 11, occurrence schema 10, and hosted-identity schema 2 while advancing core to pack version 40. It selects ten packs, enables 124 capabilities, leaves nine disabled, and exposes 25 reconciliation target types and 70 provenance subject types. Project composition completed two deterministic full loads and rejected fourteen invalid cross-registry compositions.

Focused hosting conformance produced the same summary in all three runtimes: eight carriers, six bindings, ten occupancies, three transitions, 22 service assertions, 46 rejected configurations, 14 rejected queries, and generated 128-carrier, 128-occupancy, and 127-binding probes. Six real pack compositions prove that core exposes no hosting capability or vocabulary; foundation exposes only neutral mechanics and labels; narrative, simulation, and compute expose only their owned extensions; and the deliberate combined fixture retains all prior behavioral coverage. An empty disabled registry exposes no hosting provenance or reconciliation providers, while nonempty records fail closed without activation. The narrative-only provenance fixture still resolves an actual carrier-binding assertion, proving closure without depending on simulation or compute terms.

The `full-release` compatibility profile passed all six checks in 189.0 seconds. Visualization retained 15 nodes and 121 relationships. QA retained 16 notes, 121 relationships, 71 data references, one bounded graph, two bounded pages, and all 34 normalized files. All twelve root-discovery launches passed; artifact lifecycle rejected six unsafe destinations; isolated extraction copied 228 files and passed six portable suites in all three runtimes; and each renderer produced the same nonblank 298,269-byte SVG with identical SHA-256 hashes. Canonical outputs were unchanged and redirected artifacts were removed.

Ruff formatting and lint passed all 42 Python files. The PowerShell formatter passed all 43 files in PowerShell 7 and Windows PowerShell 5.1 with no drift or over-limit lines. Work-annotation validation passed 329 eligible files, ten annotations, and all 22 fixtures with no findings. Actionlint and `git diff --check` remained clean. The implementation is ready for its mandatory two-part confirmation; post-confirmation `SCENARIO-WESTWORLD`, pack-isolation, cross-domain, adversarial, provenance, and scale pressure remain pending before Phase 1.14 can close.

### Post-Confirmation Pressure Execution

**Pressure corrections:** `de3c860` (`Fix V49 pressure-test findings`)

The retained Westworld control-unit/body model, synthetic process/container/virtual-host chain, avatar/simulation host, narrative physical-body/vessel composition, core-only project, foundation-only project, and deliberately combined behavioral fixture were replayed through exact pack-isolation probes. Carrier movement remains separate from occupant movement or copying; direct and reachable occupancy remain distinct; all selected domain vocabularies compose without leaking into unselected families. The generated 128-carrier, 128-occupancy, and 127-binding chain retained deterministic traversal and scale behavior.

The pressure pass found two `implementation-defect` issues in V49's pack boundary. First, the three vocabulary extensions declared synthetic `*-hosting-vocabulary` capabilities even though pack selection, not capability activation, controls vocabulary exposure. The schema-pack contract now permits an explicit empty capability list for vocabulary-only packs, the false activations are removed, and paired malformed fixtures still reject missing or non-list capability containers. Second, the disabled hosting registry collapsed an unselected foundation and a selected-but-disabled capability into one provider state. That left selected foundation provenance and reconciliation target vocabulary without registered providers during full project composition. The runtime now distinguishes unavailable, registered-disabled, and enabled states: core-only exposes no hosting target types; selected-disabled exposes empty typed target maps; enabled exposes validated records. Nonempty records still fail closed without activation.

Focused schema-pack, hosting, project-composition, and provenance suites passed with matching structured summaries in Python, PowerShell 7, and Windows PowerShell 5.1. The schema-pack corpus now covers 58 malformed compositions and one legal vocabulary-only extension. Hosting now covers seven exact compositions while retaining eight carriers, six bindings, ten occupancies, three transitions, 22 service assertions, 46 rejected configurations, 14 rejected queries, and the existing scale probes. The canonical project still selects ten packs and exposes 1,038 controlled values, 25 reconciliation target types, and 70 provenance subject types; removing the false narrative vocabulary capability changes the reviewed enabled-capability count from 124 to 123 without changing executable behavior.

All sixteen `baseline` suites then passed with matching semantics in all three runtimes in 50.2, 211.1, and 378.3 seconds. The `full-release` profile passed all six compatibility checks in 181.3 seconds: Visualization retained 15 nodes and 121 relationships; QA retained 16 notes, 121 relationships, 71 data references, one bounded graph, two bounded pages, and all 34 normalized files; all twelve root-discovery launches passed; artifact lifecycle rejected six unsafe destinations; isolated extraction copied 228 files and passed its six portable suites in all three runtimes; and all renderers produced the same nonblank 298,269-byte SVG with identical hashes. Canonical outputs remained unchanged and redirected artifacts were removed.

Ruff formatting and lint passed all 42 Python files. The PowerShell formatter passed all 43 files in both PowerShell runtimes with zero drift and no over-limit lines. Work-annotation validation passed 329 eligible files, ten annotations, and all 22 fixtures; actionlint and `git diff --check` were clean. After correction, the round found no remaining `parity-defect`, `compatibility-regression`, `missing-capability`, or new pack-boundary extraction. No new pressure scenario ID is needed because the durable Westworld, hosted-identity, layer-portability, evidence-authority, adversarial, cross-domain, and scale families now retain both findings. V49 and Phase 1.14 are complete; Phase 1.15 should proceed with the expanded composed stabilization replay before Phase 2.

## Expanded Stabilization After V49

### Loki And Derrick Composed Replay

The first Phase 1.15 checkpoint replayed `SCENARIO-LOKI` and `SCENARIO-DERRICK` against the complete V39-V49 composition rather than treating each framework increment as an isolated success. The source basis remains the previously recorded *Loki* episode research and the repository-grounded *Lord of Mysteries* Chapters 457-467 investigation; no new external or pretrained facts were introduced for this replay.

Derrick's abandoned-temple history remains six distinct recurrence iterations with separate concrete occurrences. His five-pass memory set is unavailable through the fifth pass, becomes available at the interstitial restoration occurrence, and is retained when the sixth pass begins. Colin remains excluded from that acquisition. Reset, termination, and exit remain typed recurrence decisions rather than chronology edges, so the model can answer what occurred in one iteration and what Derrick experienced immediately before it without granting Colin the same state or creating a chronological cycle.

Loki's representative Loom attempts coexist with aggregate or minimum cardinality without inventing an exact total. Distinct recipient and agent participations preserve the self-pruning encounter as one occurrence; TVA-local order remains separate from ordinary timeline coordinates; context topology owns oversight and intervention without manufacturing precedence; branch lifecycle owns fork, prune, restore, and preserve history; epistemic state owns progressive understanding; capability state separately owns engineering expertise; causal bootstrap cycles remain outside acyclic chronology; and the final recurrence termination remains separate from the replacement structure that follows it. V45-V49 structural interpretations, participant chronology bindings, and hosted-identity services do not absorb or rewrite any of those earlier owners.

Focused aggregate conformance ran `schema-pack`, `chronology`, `occurrence`, `provenance`, and `project-composition` in Python, PowerShell 7, and Windows PowerShell 5.1. All five suites passed with matching semantic summaries in 16.2, 107.5, and 223.1 seconds. The composed project selected ten packs with 123 enabled capabilities, 25 reconciliation target types, and 70 provenance subject types; occurrence retained 139 query/evaluation assertions, 160 malformed cases, and all four generated 128-record scale families; chronology retained 14 comparison vectors, 11 context queries, 17 malformed fixtures, and 128 generated context relations.

This checkpoint found no `implementation-defect`, `parity-defect`, `compatibility-regression`, `accepted-contract-change`, or `missing-capability`. The retained scenario questions remain sufficient, so the candidate catalog and permanent methodology require no revision. The next Phase 1.15 checkpoint is the composed `SCENARIO-PRIMER`, `SCENARIO-ARRIVAL`, `SCENARIO-MEMENTO`, `SCENARIO-DOCTOR-WHO`, and `SCENARIO-WESTWORLD` replay.

### Five-Scenario Composed Replay

The second Phase 1.15 checkpoint replayed `SCENARIO-PRIMER`, `SCENARIO-ARRIVAL`, `SCENARIO-MEMENTO`, `SCENARIO-DOCTOR-WHO`, and `SCENARIO-WESTWORLD` against the complete current composition. It reused the externally source-grounded controls recorded during V45-V48 and added no new title-specific claims.

- *Primer* retains several named, internally coherent candidate structures over shared canonical occurrences and positions. Interpretation-local precedence or causality remains local, missing information remains missing, and competing or mutually exclusive sets remain unresolved rather than selecting a canonical winner.
- *Arrival* retains future-to-present causal knowledge acquisition without moving either occurrence. Chronology positions remain fixed and acyclic; causal direction and Louise's epistemic transition remain separate, and participant-relative bindings do not make unrelated chronology systems comparable.
- *Memento* keeps objective occurrence chronology, presentation order, subjective track order, memory availability, belief attitude, documentary evidence, normalized claims, and candidate reconstruction distinct. A coherent or available memory still does not certify its payload or override provenance.
- *Doctor Who* retains one shared occurrence with independently selected universe, participant-personal, presentation, and local chronology bindings. Doctor and River participations may order meetings differently; multi-Doctor involvement uses separate participation, incarnation, and identity records where appropriate rather than cloning the event or inventing precedence.
- *Westworld* preserves conceptual identity, copies or divergence, control units, bodies, nested carrier bindings, direct versus reachable occupancy, co-residence, and active control. Moving a pearl or control unit between bodies changes bounded carrier topology while direct identity occupancy remains on the control unit; no identity move, incarnation, equivalence, reconciliation, or truth claim is inferred.

Focused aggregate conformance ran `schema-pack`, `entity`, `chronology`, `reconciliation`, `occurrence`, `hosting`, `interpretation`, `provenance`, and `project-composition` together. All nine suites passed with matching semantic summaries in Python, PowerShell 7, and Windows PowerShell 5.1 in 33.2, 155.4, and 291.0 seconds. Interpretation retained three structures, seven members, four local relations, three comparison sets, 36 rejected configurations, eight rejected queries, and its 128-member/127-relation scale probe. Hosting retained seven isolated pack compositions, eight carriers, six bindings, ten occupancies, three transitions, 46 rejected configurations, 14 rejected queries, and its 128-carrier/128-occupancy/127-binding scale probes. Entity, chronology, occurrence, reconciliation, provenance, and two complete project loads remained green with their existing malformed, depth, and scale coverage.

This checkpoint found no `implementation-defect`, `parity-defect`, `compatibility-regression`, `accepted-contract-change`, `missing-capability`, or new testing obligation. The retained stable scenario IDs still capture the relevant abstractions, and no candidate-catalog revision is warranted. The next Phase 1.15 checkpoint is the parody/derivation, continuity/identity, serialized-adaptation, and textual-tradition replay against the expanded temporal and identity composition.

### Retained Narrative Architecture Replay

The third Phase 1.15 checkpoint replayed `SCENARIO-PARODY-DERIVATION`, `SCENARIO-CONTINUITY-IDENTITY`, `SCENARIO-SERIALIZED-ADAPTATION`, and `SCENARIO-TEXTUAL-TRADITION` against the complete current composition. These are conceptual architecture regressions over the previously retained examples; this checkpoint introduced no new title-specific factual claims.

- The parody and derivation replay keeps each parody as a distinct creative work with typed lineage and optional segment correspondence. Production origin, authorization, rights basis, commerciality, distribution, officiality, and legal status remain independent evidence-backed claims; no `parody-of` relationship infers any of them.
- The continuity and identity replay keeps conceptual entities, continuity-bound incarnations, alternate counterparts, recasts or regenerations, mantle successors, clones, composites, crossover memberships, and similarly named subjects distinct. Typed relationships and reconciliation may connect those records, but neither aliases nor continuity membership silently assert identity equivalence.
- The serialized-adaptation replay keeps works, structural segments, content groups, numbering, ordering schemes, adaptation mappings, manifestations, release components, packages, runs, events, and platform offerings under separate ownership. Omissions, combinations, splits, recaps, compilations, cours, translations, localizations, reordered releases, hiatuses, and incomplete coverage therefore do not collapse creative structure into publication or distribution state.
- The textual-tradition replay keeps creative works, evidence resources or sources, manifestations or editions, compilations, typed work/source relationships, provenance assertions, and competing interpretations distinguishable. The current boundary can preserve ambiguity without turning a reconstruction into canonical structure. Fine-grained textual witnesses, editorial assembly, publication runs, contributor credits, and detailed rights grants remain declared `planned` capabilities, so exact scholarly stemmata or editorial histories are explicitly deferred rather than approximated by the executable model.

Focused aggregate conformance ran `schema-pack`, `resource`, `source`, `entity`, `temporal`, `chronology`, `reconciliation`, `occurrence`, `interpretation`, `provenance`, and `project-composition` together. All eleven suites passed with matching semantic summaries in Python, PowerShell 7, and Windows PowerShell 5.1 in 41.4, 170.6, and 320.9 seconds. The run retained 58 invalid pack compositions; 30 resource, 65 source, 86 entity, 17 chronology, 40 reconciliation, 160 occurrence, 36 interpretation, 68 provenance, and 14 project-composition invalid cases; the associated query, depth, and 128-record scale families; and a canonical project composition of ten selected packs, 123 enabled capabilities, 25 reconciliation target types, and 70 provenance subject types.

This checkpoint found no `implementation-defect`, `parity-defect`, `compatibility-regression`, or `accepted-contract-change`. It found no new executable `missing-capability`: the textual-history limitations are already accurately declared in pack metadata and remain planned work rather than regressions in the supported boundary. The stable scenario IDs and methodology remain sufficient. The next Phase 1.15 checkpoint is the composed-mechanism probe spanning competing structures, backward causal knowledge, unreliable memory, multi-context participation, hosted identity, aggregate recurrence, branch lifecycle, and state progression.

### Composed Mechanism Probe

The fourth Phase 1.15 checkpoint converted the combined pressure question into a permanent executable probe rather than inferring composition from separately green suites. A shared structural-interpretation fixture now targets the real occurrence, chronology, and hosted-identity fixture providers. The hosting suite in both runtimes loads that interpretation registry and performs eight cross-service assertions: competing occurrence orders remain unresolved; changed-branch history remains pruned at the selected boundary; aggregate recurrence cardinalities preserve minimum, maximum, range, and unknown claims; a backward causal edge does not reverse chronology; recipient and agent participations retain distinct personal contexts; later evidence revises belief without rewriting memory or truth; capability state progresses independently; and a directly hosted identity remains reachable through a moved nested carrier without becoming direct occupancy of the outer carrier.

The first composed load exposed an `implementation-defect`. V45 documented that structural interpretations can reuse canonical chronology-position records, and the standalone interpretation fixture accepted a synthetic `chronology-position` provider, but the executable chronology registry exposes only contexts, context relations, and relation bindings through its real provenance/interpretation provider. Consequently, a project-composed interpretation cannot currently target a chronology position. The permanent positive probe uses the supported `chronology-context` target so it can continue guarding all eight composed mechanisms; the position-provider mismatch remains unresolved and must receive a bounded framework version or an explicit maintainer-approved deferral before Phase 2.

After that distinction was preserved, focused `hosting` conformance passed with matching structured summaries in Python, PowerShell 7, and Windows PowerShell 5.1 in 4.2, 12.5, and 14.9 seconds. Each runtime reported eight composed assertions alongside the existing seven pack compositions, eight carriers, six bindings, ten occupancies, three transitions, 22 direct service assertions, 46 rejected configurations, 14 rejected queries, and 128-carrier, 128-occupancy, and 127-binding scale probes. This checkpoint corrected one `test-coverage-defect`, found one unresolved `implementation-defect`, and found no `parity-defect` or compatibility result yet. The next checkpoint is the complete cumulative conformance, compatibility, static-policy, cross-industry, adversarial, and scale run; its results should determine whether the position defect stands alone or joins other V50 work.

### Cumulative Closure And Cross-Domain Replay

All sixteen registered `baseline` suites passed with matching semantic summaries in Python, PowerShell 7, and Windows PowerShell 5.1. Python completed in 52.9 seconds and PowerShell 7 in 215.2 seconds; Windows PowerShell 5.1 also completed successfully in the same aggregate run. The hosting summary now carries the same eight composed assertions in every runtime. Existing permanent coverage retained 58 invalid pack compositions, 48 taxonomy configurations, 30 resource configurations, 65 source configurations, 86 entity configurations, 68 provenance configurations, 21 malformed temporal windows, 17 chronology fixtures, 40 reconciliation fixtures, 160 occurrence cases, 46 hosting configurations, 36 interpretation configurations, 14 project compositions, the associated invalid-query and parser-budget cases, a 1,500-hop reconciliation chain, and every registered 128-record scale family.

The `full-release` compatibility profile passed all six checks in 175.2 seconds. Visualization remained at 15 nodes and 121 relationships. QA remained at 16 notes, 121 relationships, 71 data references, one bounded graph, two bounded pages, and 34 normalized matching files. All twelve root-discovery launches passed; artifact lifecycle rejected six unsafe destinations while preserving unrelated content; isolated extraction copied 229 files, omitted project-specific surfaces, and passed six portable suites in all three runtimes; and all renderers produced the same nonblank 298,269-byte SVG with identical hashes and semantic dimensions. Canonical outputs were unchanged and run-owned artifacts were removed.

Ruff formatting and lint, the repository PowerShell formatter in both PowerShell runtimes, work-annotation policy, actionlint, and `git diff --check` passed. Work-annotation validation retained 329 eligible files, ten annotations, and all 22 fixtures. No static-policy, runtime-parity, consumer-compatibility, artifact-lifecycle, adversarial, parser-budget, depth, or scale regression was found.

The retained `PRESSURE-CROSS-DOMAIN` matrix then replayed synthetic IT/operations, medical, legal/compliance, law-enforcement/investigative, and scientific compositions. Incident reconstructions can keep candidate order and cause separate from event, processing, and control-plane clocks while retries, rollback branches, operator knowledge, capability, and process/container/VM hosting retain distinct owners. Differential diagnoses can remain competing interpretations over recurring visits, observations, treatment schedules, belief revision, and bounded device/body hosting without converting clinician belief into verified patient state. Legal and investigative theories can remain unresolved over provenance-ranked evidence, effective windows, supersession, and scoped authority without deriving legal conclusions from lineage or metadata. Scientific causal models can reuse trials, observations, recurrence executions, and incomparable clocks without contaminating canonical occurrence order.

Those probes found no second defect, but they reproduced the chronology-position provider gap as a cross-domain limitation: a candidate incident, diagnosis, case, or scientific reconstruction can target chronology contexts and occurrences but cannot directly include an exact chronology-position record through the real provider. The finding therefore has a reusable core invariant and is not a narrative convenience. The next checkpoint is the ownership audit that confirms canonical chronology, hypotheses, causality, participation bindings, hosting, recurrence, and context topology remain separately typed before the pack-boundary review.

### Typed Ownership Audit

The ownership audit traced every composed relation family through its contract, runtime registry, capability boundary, validation rules, queries, and provenance identity. Canonical chronology alone owns position comparison, exact equivalence closure, and the combined acyclic before/after graph. Structural interpretations own only named candidate membership, interpretation-local relations, local cycle rejection, and unresolved comparison sets; their `precedes`, `causes`, or `equivalent-with` labels never enter canonical chronology, occurrence causality, or identity reconciliation.

Occurrence separately owns concrete happenings, causal edges, recurrence and iteration topology, aggregate cardinality, transitions, branch lifecycle, participations, track entries, subject state, and links that select existing chronology bindings. Causal cycles remain legal without becoming chronological cycles. Participation bindings may select several occurrence positions and contexts but cannot create comparison or topology. Branch-state transitions are append-only occurrence records rather than branch deletion or chronology edges. Hosting separately owns carrier lifecycle, bounded child/parent topology, direct and reachable occupancy, control, move, copy, and handoff at occurrence track-entry boundaries; it does not infer identity, incarnation, chronology, continuity, truth, or direct occupancy from reachability. Chronology-context topology remains directed, non-transitive, optionally cyclic, and excluded from position comparison.

The executable implementations preserve these boundaries through separate record types, containers, validators, target-provider namespaces, and query methods rather than labels alone. The composed fixture exercises all of them while the complete baseline proves their malformed and ambiguity boundaries. No ownership collapse, chronology-cycle weakening, or additional defect was found. The chronology-position issue is narrower: the owning chronology record exists and remains correctly ordered, but it is omitted from the provider surface required for interpretation membership and provenance composition. The next checkpoint is the selected/bundled pack-boundary audit and extraction-candidate review.

### Pack Boundary And Extraction Audit

The audit reviewed all fourteen bundled packs, the ten selected by LoTM, their dependency order, capability lifecycle, controlled-value ownership, and absence behavior. No bundled pack contains a LoTM work, page, category, path, character, or project-specific record. Pack labels and descriptions are discovery metadata, not presentation rules or executable project instances.

| Pack | LoTM | Architectural Role | Decision |
| --- | --- | --- | --- |
| `core` | Selected | Reusable mechanics and universal controlled values | Retain as core. |
| `hosting-foundation` | Selected | Optional reusable carrier, topology, occupancy, control, and transition mechanics | Retain as a reusable foundation. |
| `hosting-narrative` | Selected | Narrative bridge vocabulary for physical bodies and vessels | Retain as a bridge; do not promote narrative vocabulary. |
| `hosting-simulation` | Unselected | Simulation bridge vocabulary for control units, avatars, and projection | Retain as an optional bridge. |
| `hosting-compute` | Unselected | Compute bridge vocabulary for runtimes, containers, virtual hosts, and execution | Retain as an optional bridge. |
| `narrative-media` | Selected | Narrative domain foundation | Retain as domain-owned. |
| `narrative-publishing` | Selected | Prose/sequential-art serialization, editions, localization, and publication vocabulary | Retain as domain-owned; textual-witness and editorial capabilities remain planned. |
| `narrative-screen-audio` | Selected | Screen, animation, audio, episodic, special, cut, and performance vocabulary | Retain as domain-owned. |
| `narrative-adaptation` | Selected | Adaptation lineage, mappings, disclosure, scoped continuity, and derivative vocabulary | Retain as domain-owned. |
| `narrative-distribution` | Selected | Manifestation, release, catalog, offering, territory, coverage, and identifier vocabulary | Retain as domain-owned; defer any generic distribution foundation until a second consumer proves shared mechanics. |
| `narrative-production` | Selected | Narrative production context and rights vocabulary | Retain as domain-owned; defer generic rights/licensing extraction until legal or commercial consumers establish a common executable contract. |
| `narrative-shared-universe` | Selected | Multiverse, reboot, retcon, crossover, and continuity-bound incarnation vocabulary | Retain as domain-owned; core entity, occurrence, and reconciliation mechanics are already separate. |
| `narrative-interactive` | Unselected | Planned branching narrative and narrative-instance vocabulary | Retain as domain-owned and planned; workflow or campaign similarities do not justify promotion. |
| `narrative-preservation` | Unselected | Planned narrative survival, reconstruction, archival, and access vocabulary | Retain as domain-owned and planned; defer a generic preservation/access foundation until another industry supplies concrete records and rules. |

The canonical composition exposes only `physical-body` and `vessel` carrier kinds plus the foundation binding kinds. Compute `runtime`, `container`, `virtual-host`, and `executes-in`; simulation `control-unit`, `avatar`, and `projected-through`; interactive branch vocabulary; and preservation/access namespaces remain absent. The seven hosting pack compositions, schema-pack ownership tests, core-only extraction rehearsal, and complete project composition prove absence behavior rather than relying on documentation.

No new extraction is accepted in this checkpoint. Similar words across narrative distribution and software deployment, narrative rights and legal licensing, narrative preservation and records retention, interactive routes and workflows, or shared universes and branch topology are insufficient. A later extraction must identify a second real consumer, isolate a common executable invariant in a narrowly scoped foundation, retain industry vocabulary in bridge/domain packs, and pass core-only plus combined-pack leakage tests. The chronology-position provider defect is the only current change with an already proven cross-domain invariant and therefore remains the sole concrete next-version candidate.

### Stabilization Decision After V49

Phase 1.15 classifies the implemented V39-V49 temporal, interpretation, participation, hosting, identity, pack-isolation, and earlier narrative architecture boundaries as supported. Fine-grained textual witnesses, editorial assembly, publication runs, contributor credits, detailed rights grants, interactive narrative instances, preservation/access state, and crossover events remain accurately declared planned capabilities. Automatic truth resolution, legal conclusions, probabilistic ranking, unrestricted expressions, and project-specific inference remain outside the present framework boundary. The five reviewed extraction candidates retain domain ownership until a second real consumer proves a shared executable contract.

One `implementation-defect` blocks Phase 2: canonical chronology positions cannot participate in structural interpretations or provenance through the real project-composed provider, despite the V45 contract and retained Primer/textual-reconstruction scenarios promising that boundary. The defect is cross-domain because incident, clinical, legal, investigative, and scientific candidate structures may also need to reference an exact project-defined chronology position without converting that candidate relation into canonical order.

V50 should implement **Chronology-Position Provider Closure** as a bounded correction. Core should register `chronology-position` as a provenance subject type. The paired chronology services should expose their existing position records through the shared provenance/interpretation target surface and reject unknown IDs. The composed fixture should return from its temporary context target to a real position target. Interpretation and provenance suites should prove actual dispatch rather than a synthetic provider, while project composition should prove provider uniqueness and complete controlled-value closure. The chronology registry's persisted schema and comparison semantics should not change, and coordinate systems, eras, spans, relations, and mappings should not be promoted without separate evidence.

**Proposed testing:** `CONF-PACK-COMPOSITION`, `CONF-CHRONOLOGY`, `CONF-INTERPRETATION`, `CONF-HOSTING`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `COMPAT-RENDER`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-PRIMER`, `SCENARIO-TEXTUAL-TRADITION`, `PRESSURE-STRUCTURAL-INTERPRETATION`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-CROSS-DOMAIN`, `PRESSURE-ADVERSARIAL`, and `PRESSURE-SCALE`.

Phase 1.16 now owns V50. Phase 2 remains blocked until the correction passes its two-part implementation and pressure-test confirmation and the expanded stabilization decision is replayed. No other V50 scope is accepted by this checkpoint.

## V50 - Chronology-Position Provider Closure

**Implemented by:** `7fe1dc6` (`Implement V50 chronology-position provider closure`)

**Proposed testing:** `CONF-PACK-COMPOSITION`, `CONF-CHRONOLOGY`, `CONF-INTERPRETATION`, `CONF-HOSTING`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `COMPAT-RENDER`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-PRIMER`, `SCENARIO-TEXTUAL-TRADITION`, `PRESSURE-STRUCTURAL-INTERPRETATION`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-CROSS-DOMAIN`, `PRESSURE-ADVERSARIAL`, and `PRESSURE-SCALE`.

**Proposed candidates:** Competing reconstructions that reuse exact chronology positions; the retained *Primer* and textual-tradition scenarios; incident, clinical, legal, investigative, and scientific candidate structures; direct positive and unknown-ID provider queries; provenance assertions over position fields; provider omission, duplicate ownership, and unregistered-type compositions; a canonical project with no instantiated positions; and the existing chronology, interpretation, provenance, hosting, and extraction scale probes.

**Superseded assumption:** Exposing chronology contexts through the shared provider was sufficient for structural interpretations that need to reuse exact canonical chronology coordinates.

**Architectural promotion:** Existing canonical chronology positions become addressable through the core provenance and interpretation provider boundary without changing their storage owner or chronology semantics.

V50 is a bounded provider-closure correction. It does not change chronology schema 2, comparison behavior, coordinate semantics, or persisted project data. Core pack version 41 registers `chronology-position` as one provenance subject type. The paired chronology providers expose the registry's existing canonical position objects and reject unsupported types or unknown IDs. Coordinate systems, eras, spans, chronology relations, and mappings remain unexposed because the Phase 1.15 evidence established no corresponding requirement.

The composed interpretation fixture now targets `civil-anchor` through the real chronology provider instead of using a temporary chronology-context substitute. Paired hosting assertions prove the member resolves while competing structures remain unresolved and the surrounding recurrence, causality, participation, state, branch, and carrier owners remain unchanged. Paired provenance fixtures add an assertion over the position's coordinate-system field and verify that dispatch returns the exact chronology-owned object. Direct chronology tests cover successful lookup, unknown position IDs, unsupported subject types, and exact provider inventory. Project composition advances its reviewed oracle to 1,039 controlled values and 71 provenance subject types while retaining ten packs, 123 enabled capabilities, 25 reconciliation target types, and fourteen rejected invalid compositions.

## Testing After V50

Focused `schema-pack`, `chronology`, `interpretation`, `hosting`, `provenance`, and `project-composition` conformance passed with matching structured semantics in Python, PowerShell 7, and Windows PowerShell 5.1. Direct chronology tests resolve the exact registry-owned `civil-anchor` object and reject an unknown position plus an unsupported subject type. The composed fixture resolves a real chronology-position member, rejects a second provider for that same type, and retains ten cross-service assertions. Provenance validates 23 fixture assertions, including a position field-path assertion, and rejects six invalid service queries. Project composition retains two deterministic loads and fourteen rejected invalid compositions while advancing to core pack 41, 1,039 controlled values, and 71 provenance subject types.

All sixteen registered `baseline` suites then passed against the exact final corpus in Python, PowerShell 7, and Windows PowerShell 5.1. The three aggregate executions completed in 647.8 seconds and returned matching suite IDs, statuses, and canonicalized semantic summaries. Existing malformed, parser-budget, ambiguity, depth, and scale families remained green; chronology now additionally creates 128 canonical positions and verifies complete provider enumeration, while the interpretation and hosting scales retain their 128-member and 128-carrier families.

The `full-release` compatibility profile passed all six checks in 184.0 seconds. Visualization retained 15 nodes and 121 relationships. QA retained 16 notes, 121 relationships, 71 data references, one bounded graph, two bounded pages, and all 34 normalized files. All twelve root-discovery launches passed; artifact lifecycle rejected six unsafe destinations; isolated extraction copied 229 files and passed its six portable suites in all three runtimes; and all renderers produced the same nonblank 298,269-byte SVG with identical hashes. Canonical outputs were unchanged and run-owned artifacts were removed.

Ruff formatting and lint passed all 42 Python files. The repository PowerShell formatter passed all 43 files in PowerShell 7 and Windows PowerShell 5.1 with zero drift and no over-limit lines. Work-annotation validation passed 329 eligible files, ten annotations, and all 22 fixtures; actionlint and `git diff --check` were clean.

The implementation-time retained replay covered `SCENARIO-PRIMER`, `SCENARIO-TEXTUAL-TRADITION`, `PRESSURE-STRUCTURAL-INTERPRETATION`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-CROSS-DOMAIN`, `PRESSURE-ADVERSARIAL`, and `PRESSURE-SCALE`. Candidate structures can now include exact chronology positions in narrative reconstruction, incident analysis, differential diagnosis, legal or investigative theory, and scientific causal models without adding a chronology edge or selecting a winner. Unknown IDs, unsupported types, duplicate providers, and a canonical project with no instantiated positions all fail or remain empty at the correct boundary. Coordinate systems, eras, spans, chronology relations, and mappings remain unavailable as provider targets.

### Post-Confirmation Pressure Execution

**Pressure corrections:** `c88d1c8` (`Fix V50 chronology provider mutation leak`)

An adversarial mutation probe found one bounded `implementation-defect` and cross-runtime parity defect in the newly added Python provider surface. Python returned the registry's mutable position inventory directly, so deleting a key through `provenance_targets()` also deleted canonical chronology state; PowerShell already returned a detached map. The correction makes Python return a detached inventory while preserving each exact chronology-owned record object. The chronology contract and permanent paired suite now require canonical object identity, an empty typed map when no positions exist, and caller-safe inventory mutation. This does not establish a repository-wide immutable-provider policy or copy record objects.

The retained `SCENARIO-PRIMER` and `SCENARIO-TEXTUAL-TRADITION` replays confirm that competing narrative and textual reconstructions can reuse one exact chronology position without manufacturing canonical order, duplicating the position, or selecting a winning interpretation. `PRESSURE-STRUCTURAL-INTERPRETATION` confirms position membership stays interpretation-owned. `PRESSURE-EVIDENCE-AUTHORITY` confirms addressability does not make a claim authoritative: evidence, assertion evaluation, and source precedence remain provenance-owned. `PRESSURE-CROSS-DOMAIN` applies the same boundary to incident reconstruction, differential diagnosis, legal or investigative theories, and scientific causal models.

`PRESSURE-ADVERSARIAL` now explicitly covers unknown position IDs, unsupported subject types, exact provider allowlisting, an empty canonical position inventory, duplicate-provider rejection through composition, and mutation isolation of the returned inventory. Coordinate systems, eras, spans, chronology relations, and mappings remain unavailable as provenance or interpretation targets. `PRESSURE-SCALE` retains deterministic enumeration and lookup for 128 generated positions alongside the existing 128-context topology probe.

After the correction, all sixteen registered `baseline` suites passed in Python, PowerShell 7, and Windows PowerShell 5.1 with matching suite inventories and semantic summaries. The exact final-tree aggregate runtimes were 49.5, 210.2, and 376.7 seconds; each chronology summary reported one empty-provider check and one provider-isolation check. Full-release compatibility passed all six checks in 171.9 seconds with canonical outputs unchanged: Visualization retained 15 nodes and 121 relationships, QA retained 16 notes and 121 relationships across 34 normalized files, isolated extraction copied 229 files and passed all portable suites in all three runtimes, and every renderer produced the same nonblank 298,269-byte SVG hash. Ruff, PowerShell formatting in both runtimes, work-annotation validation, actionlint, and `git diff --check` were clean.

The corrected defect did not alter persisted schemas, project data, chronology comparisons, graph semantics, or generated outputs. No additional `implementation-defect`, `parity-defect`, `compatibility-regression`, or `missing-capability` remains from the V50 pressure set. The expanded stabilization replay therefore closes the Phase 1 framework-model gate and accepts Phase 2's effective project schema service as the next implementation step once this pressure correction is confirmed.
