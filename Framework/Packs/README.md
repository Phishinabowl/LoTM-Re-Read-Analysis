# Schema Pack Catalog

Schema packs are composable contracts, not project instances. Pack files define capabilities and controlled vocabulary; `Project_Config/schema-packs.yaml` selects packs and activates only the available capabilities a project uses.

Pack presentation and architectural classification follow
[`Framework/Contracts/schema-pack-presentation.md`](../Contracts/schema-pack-presentation.md).
`pack_kind` remains the compatibility-facing validation class; family, role, scope, declared
domains, and bridge joins are separate machine-readable concerns. IDs and folder names never prove
ownership or scope.

Pack selection and capability activation are different controls. Selecting a pack composes its
controlled vocabulary. Enabling a capability activates executable behavior. A vocabulary-only
extension therefore declares `capabilities: []` rather than inventing an enabled capability whose
state cannot govern its values.

## Inspection Boundaries

`EffectiveProjectSchema` exposes presentation and classification only for packs selected by one
project and capabilities declared by those packs. Its concise overview, detailed sections, and
singular selectors are compiled project views, not a complete framework inventory.

This README remains a human-maintained architectural summary, while schema-pack conformance
validates all 14 installed pack files and their capability presentations. The generated
`FrameworkCatalog` service and report replace README dependence for machine clients. The catalog
preserves independently available packs, dependencies, and
discoverability state without composing every installed pack as though one project selected it.

Catalog discovery starts from `Framework/framework.yaml`, which explicitly selects the installed
pack root and lookup-key registry. It must not infer either input from filenames or depend on
`Project_Config/`; multiple portable lookup datasets may coexist in one framework installation.

The paired `inspect_framework_catalog.py` and `Get-FrameworkCatalog.ps1` commands
inspect that complete project-independent inventory. The existing effective-schema commands remain
separate because they describe one valid project composition. Both command families will consume
the same validated pack/capability records rather than maintaining separate parsers or metadata.

Phase 3.2.2 will make `EffectiveProjectSchema` resolve its selected dependency closure through the
shared catalog model and then add project activation, taxonomy, resources, diagnostics, and later
project registries. An explicit project-root argument on catalog inspection produces the required
derived `FrameworkCatalogProjectView` with selected/enabled/used state after that phase; the base catalog remains
project-independent and never depends on that view.

## Architectural Classification

| Pack | Family | Role | Scope | Domains / joins |
| --- | --- | --- | --- | --- |
| `core` | `platform` | `foundation` | `domain-neutral` | None |
| `hosting-foundation` | `hosting` | `foundation` | `domain-neutral` | None |
| `hosting-compute` | `hosting` | `extension` | `domain-specific` | `compute` |
| `hosting-simulation` | `hosting` | `extension` | `domain-specific` | `simulation` |
| `narrative-media` | `narrative` | `domain` | `domain-specific` | `narrative` |
| `narrative-publishing` | `narrative` | `extension` | `domain-specific` | `narrative` |
| `narrative-screen-audio` | `narrative` | `extension` | `domain-specific` | `narrative` |
| `narrative-adaptation` | `narrative` | `extension` | `domain-specific` | `narrative` |
| `narrative-distribution` | `narrative` | `extension` | `domain-specific` | `narrative` |
| `narrative-production` | `narrative` | `extension` | `domain-specific` | `narrative` |
| `narrative-shared-universe` | `narrative` | `extension` | `domain-specific` | `narrative` |
| `narrative-interactive` | `narrative` | `extension` | `domain-specific` | `narrative` |
| `narrative-preservation` | `narrative` | `extension` | `domain-specific` | `narrative` |
| `hosting-narrative` | `hosting` | `bridge` | `cross-domain` | Domains: `hosting`, `narrative`; joins: `hosting-foundation`, `narrative-media` |

These are authored catalog decisions. Runtime composition validates them but never derives them from
pack IDs, folders, compatibility `pack_kind`, or dependency names. Optional visual presentation is
absent across the current catalog until a renderer-independent identifier receives separate review.

## Shared Packs

| Pack | Purpose |
| --- | --- |
| `core` | Domain-neutral identity, strict configuration ingestion, deterministic Unicode lookup keys, bounded auditable stable-ID reconciliation, stable nested-record and claim identity, composite channel-bounded evidence scope, hierarchical locator-level evidence modes, explainable precedence-aware authority, multi-source and claim-level evaluation, point/range evidence locators, semantic provenance paths, structural position validation, shared civil-time windows, ordered chronology coordinate systems with provenance-addressable positions, occurrence/recurrence identity, aggregate and uncertain recurrence cardinality, scoped recurrence policy and schedules, deterministic rule evaluation and policy integrity, subject-state availability, epistemic change, local capability progression, and competing structural interpretations that remain outside canonical graphs, plus relationships, visibility, projection, and validation. |
| `hosting-foundation` | Optional domain-neutral hosted-identity service: carrier lifecycle and topology, occupancy/control, explicit transitions, generic structural bindings, queries, and provider interfaces. |
| `hosting-narrative` | Optional physical-body and vessel vocabulary for narrative embodiment. |
| `hosting-simulation` | Optional control-unit, avatar, and projection vocabulary for simulated or mediated embodiment. |
| `hosting-compute` | Optional runtime, container, virtual-host, and execution vocabulary for compute hosting. |
| `narrative-media` | Narrative foundation: works, media facets, structural segments, segment-anchored locators, ordering-backed position validation, recursively nested content groups with participation roles, temporally scoped localized title variants, continuity, narrative chronology contexts and time loops, reader disclosure, and spoiler bounding. |
| `narrative-publishing` | Prose and sequential-art serialization, editions, localization, packaging, and planned publication-run/textual-history support. |
| `narrative-screen-audio` | Film, television, animation, web series, audio works, episodes, specials, cuts, tracks, embedded visuals, and planned live-performance production/event support. |
| `narrative-adaptation` | Work lineage, parody and other transformative derivatives, segment mappings, adaptation deviations, and authority-aware comparison. |
| `narrative-distribution` | Editions, cuts, builds, manifestation segment mappings, component lineage, release packages/phased runs/events, multi-target source observations, semantically work-scoped coverage ranges, mixed-media evidence locators, uses of core-owned structured time, localized platform catalogs/offerings including video-sharing platforms, identifiers, and regional availability. |
| `narrative-shared-universe` | Optional continuity and pairwise multiverse relationships, reboots, ambiguity-safe entity identity, semantically directed lineage, incarnations, retcons, and planned crossover-event support. First-class continuity-system containment remains a roadmap candidate. |
| `narrative-interactive` | Optional branching-story, route, ending, playthrough, campaign, session, and collective live-world support. Versioned game mechanics and rulesets remain a roadmap candidate. |
| `narrative-preservation` | Optional missing, partial, reconstructed, archival, and access-state support. |
| `narrative-production` | Scope-backed production origin, authorization, rights basis, and commerciality, plus planned contributor-credit and detailed rights-grant support. |

LoTM currently selects `core`, `hosting-foundation`, `hosting-narrative`, `narrative-media`, `narrative-publishing`, `narrative-screen-audio`, `narrative-adaptation`, `narrative-distribution`, `narrative-production`, and `narrative-shared-universe`. It intentionally does not select simulation or compute hosting vocabulary. The shared-universe pack supplies executable shared-universe and entity-incarnation contracts; its crossover-event capability remains planned. Other narrative packs remain discoverable templates for projects that need them; their planned capabilities cannot be activated until the corresponding executable contracts exist.

## Media Axes

Do not encode every media property in one value.

- A **medium profile** is the reader-position and citation channel used by page data and boundary tools, such as `novel`, `donghua`, or `illustration`.
- A **media modality** describes how the work communicates, such as prose, sequential art, animation, live action, audio, still image, or interactive presentation.
- A **cultural form** preserves a meaningful production tradition such as anime, donghua, manga, manhwa, manhua, or webtoon.
- A **release form** describes the creative unit or packaging level, such as novel, television season, special, film, issue, or collected volume.
- A **container format** describes the concrete evidence container, such as EPUB, print, streaming release, subtitle file, Blu-ray, or app.
- A **manifestation** describes a particular edition, translation, cut, remaster, recut, or build of one creative work.
- A **release event** records when and where that manifestation launched.
- A **platform offering** records how a provider exposed it in a territory and time window.
- A **catalog placement** preserves provider presentation without rewriting canonical work hierarchy.

A Donghua film can therefore use the `donghua` medium profile, `animation` modality, `donghua` cultural form, `film` release form, and a streaming or theatrical container. Official artwork extracted from an EPUB uses the `illustration` profile and `still-image` modality while its source records `epub` and any extracted digital file as containers. `official-epub-artwork` is not a medium.

Claim namespaces, evidence modes, and content-group member roles are pack-owned vocabulary. Claim namespaces and evidence modes may declare a `broader_value`; authority rules inherit down either hierarchy and use explicit precedence to resolve broad defaults against narrow exceptions. Mode-specific rules evaluate the mode selected by the locator, and explainable decisions retain the source, mode, winning rule and precedence, inheritance state, or priority fallback. Position-structure strategies are also pack-owned: narrative publishing contributes `work-volume-catalog`, while narrative media contributes `work-segment-ordering` for stable segments interpreted through an explicit total ordering. Unrelated domains may omit structural validation or supply their own strategy. Downstream projects activate only capabilities supplied by their selected packs, so an absent feature remains disabled rather than becoming an error in an unrelated industry configuration.

## Time And Chronology

Core civil-time windows and chronology coordinates are related but separate. `temporal-windows` owns Gregorian/RFC 3339 effective-time mechanics. `chronology-coordinate-systems` owns project-defined calendar, era-ordinal, ordinal, and relative integer axes. Narrative media adds `narrative-chronology` contexts that bind an axis to works, continuities, branches, and story-time roles without conflating story order with release or reader-disclosure order. Epoch names, fictional calendars, and concrete anchors remain project instances rather than reusable pack values.

Current chronology mappings are explicit and exact; no selected pack supplies a floating or sliding
timescale policy. Current shared-universe vocabulary supplies continuities and pairwise
relationships, not a first-class universe/multiverse/realm containment service. The platform plan
retains both ideas as candidate narrative capabilities. They must not appear in a pack declaration
until ownership, executable behavior, and permanent conformance satisfy the normal promotion gate.

Core `occurrence-recurrence-modeling` keeps concrete happenings, branches, iterations, profiled transitions, causal edges, and tracks separate from chronology coordinates. `occurrence-participation-identity` separates a concrete occurrence from each subject participation and from each participation's stable ordered track entry, permitting repeated encounters without cloning the occurrence. `recurrence-rule-modeling` separates reusable patterns from concrete executions and adds typed outcomes, bounded conditions/effects, and coherent lifecycle. `deterministic-recurrence-rule-evaluation` adds concrete phases, scoped pattern defaults and execution overrides, priority and conflict traces; `recurrence-schedule-modeling` supplies bounded civil-calendar and chronology-step cadence. `recurrence-policy-integrity` enforces pack-owned rule/effect compatibility, same-pattern predicates and control effects, and indeterminate missing-time behavior. Schema-5 pack `semantic_declarations` store transition profiles, outcome incompatibilities, effect target and rule compatibility, recurrence scope, repetition policy, effect incompatibility scope, state-change profiles, typed state profiles, and state-kind/profile mappings as typed records; their member IDs remain atomic controlled values. `semantic-declaration-integrity` validates those records across composed packs without delimiter parsing. Every controlled state kind must map to exactly one known profile. Reusable profiles may remain dormant until a selected downstream pack contributes a matching kind, preserving clean core-only and optional-pack composition. Profiles declare availability, completeness, attitude, and capability as required, optional, or forbidden so domain vocabulary can reuse one structural transition spine without sharing semantics accidentally. Capability values use registry-local qualitative or bounded-integer scales; credentials and qualifications remain availability-only records rather than competence claims. `deterministic-effect-resolution` groups selected semantic effects, preserves contributor IDs and proposed counts, and emits authorized effects only when the complete evaluation is conflict-free and determinate. `civil-schedule-boundary-integrity` gives every runtime the same controlled `0001`-`9999` projection boundary while chronology-step schedules retain their integer coordinate domain. `state-availability-acquisition` records subject state independently from encounter and provenance, while carryover references an applicable state transition across an iteration boundary. Narrative media maps memory, knowledge, and awareness to epistemic access; belief to epistemic belief; and physical state to availability-only state. It adds specialized acquisition mechanisms without turning a subject's access or attitude into objective truth. Causal cycles remain valid; chronological cycles remain invalid.

Recurrence policy governs recurrence execution only. It must not absorb versioned game mechanics, format legality, tabletop selections, organizational policy, clinical protocol, or legal/compliance obligations. A future ruleset capability must model normative versions, scope, precedence, overrides, exceptions, and compatibility explicitly and prove its domain ownership before any pack declares it.

Core `structural-interpretation-modeling` owns stable candidate structures that reuse canonical target IDs while keeping membership and local relations outside chronology, occurrence causality, entity identity, and reconciliation. Comparison sets may be compatible, competing, or mutually exclusive; the service preserves unresolved outcomes and leaves evidence priority, applicability, supersession, and authority to provenance.

Optional `hosting-foundation` keeps an identity-bearing subject separate from the carrier that hosts it. Carrier lifecycle, bounded child/parent bindings, direct and reachable occupancy, co-residence, active control, movement, copies, and handoffs reuse occurrence track-entry boundaries. The foundation owns only generic installation, containment, and attachment vocabulary. Narrative, simulation, compute, and future industry packs add their own carrier and binding kinds without cross-pack leakage. Copy records cite existing identity relationships; hosting never infers continuity, equivalence, replacement, divergence, direct occupancy, or truth from shared carrier, code, memory, appearance, or reachability. An empty hosting registry remains valid when the capability is disabled. An unselected foundation registers no hosting target types; a selected but disabled foundation registers empty typed providers for composition closure; nonempty hosting records fail closed until activation.

## Capability Honesty

`available` means the selected contract can be instantiated and validated. `planned` means the concept has stable ownership and vocabulary but the repository must not yet store records that depend on it. A roadmap candidate is earlier still: it is neither discoverable nor selectable until a reviewed contract and pack declaration exist. Applicability scopes, explainable semantic applicability decisions, scoped continuity, claim supersession, production/right contexts, entity relationships, entity incarnations, identity phases, and stable-ID reconciliation are executable. Branching narrative state, crossover events, preservation state, contributor credits, textual witnesses, and detailed rights grants/restrictions remain planned until their paired Python and PowerShell contracts are implemented. Continuity systems, sliding chronology, versioned normative rulesets, and editorial-governance services remain roadmap candidates. Production/right contexts keep production origin, authorization, rights basis, and commerciality independent and make no legal inference from parody or other transformative lineage.
