# Narrative Pack Catalog

Schema packs are composable contracts, not project instances. Pack files define capabilities and controlled vocabulary; `Project_Config/schema-packs.yaml` selects packs and activates only the available capabilities a project uses.

## Shared Packs

| Pack | Purpose |
| --- | --- |
| `core` | Domain-neutral identity, strict configuration ingestion, deterministic Unicode lookup keys, bounded auditable stable-ID reconciliation, stable nested-record and claim identity, composite channel-bounded evidence scope, hierarchical locator-level evidence modes, explainable precedence-aware authority, multi-source and claim-level evaluation, point/range evidence locators, semantic provenance paths, structural position validation, shared civil-time windows, ordered chronology coordinate systems, relationships, visibility, projection, and validation. |
| `narrative-media` | Narrative foundation: works, media facets, structural segments, segment-anchored locators, ordering-backed position validation, recursively nested content groups with participation roles, temporally scoped localized title variants, continuity, narrative chronology contexts, reader disclosure, and spoiler bounding. |
| `narrative-publishing` | Prose and sequential-art serialization, editions, localization, packaging, and planned publication-run/textual-history support. |
| `narrative-screen-audio` | Film, television, animation, web series, audio works, episodes, specials, cuts, tracks, embedded visuals, and planned live-performance production/event support. |
| `narrative-adaptation` | Work lineage, parody and other transformative derivatives, segment mappings, adaptation deviations, and authority-aware comparison. |
| `narrative-distribution` | Editions, cuts, builds, manifestation segment mappings, component lineage, release packages/phased runs/events, multi-target source observations, semantically work-scoped coverage ranges, mixed-media evidence locators, uses of core-owned structured time, localized platform catalogs/offerings including video-sharing platforms, identifiers, and regional availability. |
| `narrative-shared-universe` | Optional multiverse, reboot, ambiguity-safe entity identity, semantically directed lineage, incarnation, retcon, and crossover-event support. |
| `narrative-interactive` | Optional branching-story, route, ending, playthrough, campaign, and session support. |
| `narrative-preservation` | Optional missing, partial, reconstructed, archival, and access-state support. |
| `narrative-production` | Scope-backed production origin, authorization, rights basis, and commerciality, plus planned contributor-credit and detailed rights-grant support. |

LoTM currently selects `core`, `narrative-media`, `narrative-publishing`, `narrative-screen-audio`, `narrative-adaptation`, `narrative-distribution`, `narrative-production`, and `narrative-shared-universe`. The shared-universe pack supplies executable shared-universe and entity-incarnation contracts; its crossover-event capability remains planned. Other narrative packs remain discoverable templates for projects that need them; their planned capabilities cannot be activated until the corresponding executable contracts exist.

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

## Capability Honesty

`available` means the selected contract can be instantiated and validated. `planned` means the concept has stable ownership and vocabulary but the repository must not yet store records that depend on it. Applicability scopes, explainable semantic applicability decisions, scoped continuity, claim supersession, production/right contexts, entity relationships, entity incarnations, identity phases, and stable-ID reconciliation are executable. Branching narrative state, crossover events, preservation state, contributor credits, textual witnesses, and detailed rights grants/restrictions remain planned until their paired Python and PowerShell contracts are implemented. Production/right contexts keep production origin, authorization, rights basis, and commerciality independent and make no legal inference from parody or other transformative lineage.
