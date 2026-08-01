# Framework Evolution History

This document records how the reusable knowledge-platform framework evolved, why each version was introduced, and what the pressure testing after each version exposed. It is both a design history and a forward-looking engineering log.

The version numbers here describe the **framework evolution rounds discussed during the extraction project**. They are not interchangeable with every registry's internal `schema_version` or every schema pack's `pack_version`. V1-V15 primarily track the narrative source registry as it grew from schema 1 through schema 15. V16 onward expands the framework through additional registries and shared services, each of which retains its own schema and pack version.

From V30 onward, update this file as part of each version:

1. Add the version section when the implementation is complete.
2. Record the problem, design decision, implementation surface, and reason for the change.
3. Add the subsequent testing section before beginning the next version.
4. Record defects separately from missing capabilities.
5. Link the implementing commit after the version is confirmed.
6. Update the era index when a version begins a genuinely new architectural phase.
7. Record superseded assumptions, architectural extractions, and promotions when they materially apply; do not force a marker into every version.

## Evolution Eras

- **Foundation:** Manifest, architecture, taxonomy, and resource separation
- **V1-V6:** Works, media, manifestations, releases, and distribution
- **V7-V15:** Evidence, authority, production context, scope, and applicability
- **V16-V23:** Entity identity and cross-registry provenance/reconciliation
- **V24-V27:** Deterministic configuration ingestion
- **V28-V32:** Civil time, general chronology, occurrence, recurrence, and transition integrity

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
