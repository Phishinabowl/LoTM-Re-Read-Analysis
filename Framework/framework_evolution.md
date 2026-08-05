# Framework Evolution History

This document records how the reusable knowledge-platform framework evolved, why each version was introduced, and what the pressure testing after each version exposed. It is both a design history and a forward-looking engineering log.

The end-to-end version process is governed by `Framework/framework_improvement_lifecycle.md`. Cumulative testing requirements are governed by `Framework/testing_methodology.md`. This file records history and handoff state; it does not independently define either workflow.

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

**Proposed testing:** `CONF-STRICT-INGESTION`, `CONF-PACK-COMPOSITION`, `CONF-OCCURRENCE`, `CONF-PROVENANCE`, `CONF-PROJECT-COMPOSITION`, `PARITY-THREE-RUNTIME`, `PARITY-STRUCTURED-OUTPUT`, `COMPAT-VISUALIZATION`, `COMPAT-QA`, `COMPAT-RENDER`, `COMPAT-ROOT-DISCOVERY`, `COMPAT-ARTIFACT-LIFECYCLE`, `COMPAT-FRAMEWORK-EXTRACTION`, `STATIC-POWERSHELL`, `STATIC-PYTHON`, `STATIC-WORK-ANNOTATIONS`, `SCENARIO-DERRICK`, `SCENARIO-LOKI`, `PRESSURE-RECURRENCE-STATE`, `PRESSURE-EVIDENCE-AUTHORITY`, `PRESSURE-LAYER-PORTABILITY`, `PRESSURE-ADVERSARIAL`, `PRESSURE-CROSS-DOMAIN`, and `PRESSURE-SCALE`.

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

The paired runtimes must reject unknown branches, continuity memberships, states, changes, activation occurrences, and triggers; noncontiguous ordinals; broken prior/resulting state chains; trigger endpoint mismatches; and child branches whose first lifecycle record is disconnected from the fork that created them. Permanent probes include deterministic boundary queries, 116 malformed mutations, source-continuity composition closure, one provenance-backed branch-state claim, and a generated 128-transition branch history.

V42 does not model knowledge, awareness, memory, skill, proficiency, or accumulated expertise. It does not infer lifecycle transitions from chronology, source continuity, or a domain label. Those remain explicit, provenance-backed project claims and later bounded capabilities.

## Testing After V42

Pending implementation confirmation and pressure testing.
