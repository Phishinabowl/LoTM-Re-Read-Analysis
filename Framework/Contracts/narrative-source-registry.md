# Narrative Source Registry Contract

`Project_Config/sources.yaml` schema version 9 is the executable project-instance contract for selected narrative packs. `Tools/source_config.py` and `Tools/Source-Config.ps1` enforce the same fields and reference rules.

## Media Facets

The registry instantiates four selected-pack namespaces before defining medium profiles:

- `media_modalities`: labeled modality IDs from `source.media-modality`.
- `cultural_forms`: labeled cultural forms from `source.cultural-form`, each linked to one instantiated modality.
- `release_forms`: labeled work/release forms from `source.release-form`.
- `container_formats`: labeled evidence containers from `source.container-format`.

Every `mediums` entry must declare at least one `modality_id` and may declare cultural forms whose linked modalities are present. The medium continues to own position fields, sorting fields, and citation formats because it is the reader-boundary channel. Its required `work_scope_field` names the position field that carries canonical work identity; semantic range and locator validation use that field instead of guessing from field names.

Every work must declare `work_type`, `medium_id`, `release_form_id`, and `work_status`. These axes are independent: `medium_id` selects the reader-position profile, while `release_form_id` describes the creative unit. A work may name a `parent_work_id` when a creative work is genuinely contained by another creative work; parent chains cannot cycle. Works and segments may carry localized titles without changing their stable identity.

Every evidence source must declare one or more `container_format_ids`; container identity does not alter the work's medium or release form.

## Work Structure And Ordering

`segments` is a stable-ID mapping for configurable work parts. A segment declares its work, type, label, optional positive ordinal, and optional parent segment. Parent chains must remain inside one work and cannot cycle. Segment types come from `source.segment-type`.

`content_groups` provide overlapping, optionally nested selections without changing structural parentage or franchise membership. Each member has a globally stable ID, a controlled participation `role`, and a target of type `work`, `segment`, or `content-group`, so a crossover or reading path may distinguish core, required, optional, supplemental, prologue, or epilogue material while composing complete works, individual issues, chapters, episodes, or reusable subgroups. Member role does not imply sequence. Optional parent groups, localized titles, aliases, and an ordering scheme may describe the selection; an ordering scheme must order exactly the typed members. Parent and member nesting form one acyclic group graph.

`numbering_schemes` assign display numbers and aliases to work or segment targets inside an explicit work or work-group scope. Numbering does not imply order: use an ordering scheme for sequence. This separation supports issue `0`, legacy comic numbering, production codes, split issue numbers, and provider numbering without coercing them into integers.

`ordering_schemes` stores named orders independently of group membership. Each entry has a stable ID and a unique work, segment, or content-group target. A `total` ordering uses unique positive ordinals. A `partial` ordering omits ordinals and uses `after_entry_ids` to express acyclic precedence, allowing concurrent, incomparable, or not-yet-fixed branches. Projects may therefore preserve publication, release, story, production, and recommended orders simultaneously without inventing one false universal sequence.

The existing verified `volumes` catalog remains a specialized convenience for work-local novel chapter boundaries. It does not replace the generic segment model.

## Continuity And Authority

Continuity membership and relationship statuses come from the selected-pack `source.membership-status` namespace rather than loader-local allowlists. Authority profiles determine accepted statuses, continuity precedence, source-priority direction, comparable derivative relationships, conflict behavior, and deviation ownership. Repeatable claim-authority rules may override a source's general numeric priority for one controlled claim namespace by matching source IDs, source roles, medium IDs, or evidence modes. Rule IDs are global provenance targets, and one profile may not ambiguously match the same source twice for the same claim namespace. Consumers fall back to ordinary source priority when no claim rule matches.

Work-level continuity membership is executable. Segment- and claim-scoped continuity, entity incarnations, and retcon/supersession records remain planned capabilities and must not be approximated with page-local enums.

## Adaptation Mappings

`adaptation_mappings` maps one or more `basis_inputs` to a target work and may narrow every input and the target to registered segments. Empty segment lists mean work scope. Each basis input states whether it is a primary source, secondary source, prior adaptation, inspiration, or shared property. Mapping types come from `source.adaptation-mapping-type`; statuses use the same controlled membership-status vocabulary as other canon-bearing relationships.

Mappings preserve direction and provenance. They may represent direct correspondence, omission, combination, splitting, reordering, expansion, condensation, adaptation-original material, or recontextualization. Adaptation mappings do not overwrite source-work claims.

## Manifestations And Distribution

Creative identity and distribution identity are separate:

- `works` own the creative unit and its canonical hierarchy.
- `manifestations` own a concrete edition, translation, cut, remaster, episodic recut, compilation cut, or software build of one work. An empty `segment_ids` list means the whole work; a populated list scopes the manifestation without inventing separate works. They may carry language, territory, container, localized-title, and alias metadata.
- `manifestation_segment_mappings` describe retained, omitted, added, altered, replaced, reordered, combined, or split segment correspondence between related manifestations of the same work. Omission has source segments only; addition has target segments only; other mappings require both sides.
- `release_components` represent tracks and bundled components such as subtitles, audio, captions, commentary, deleted scenes, embedded illustrations, posters, inserts, or physical bonuses. A component may identify its originating manifestation. A component without a manifestation must belong to at least one release package, which supports package-only material without a fictional edition. Typed component relationships preserve revisions, translations, dubs, and derivation lineage without promoting every track to a manifestation.
- `release_packages` bundle manifestations, selected segments, components, and containers as box sets, omnibuses, multi-disc sets, collector editions, or other commercial packages.
- `release_runs` compactly describe regular segment releases through an exact total ordering and one or more ordered phases. Every phase owns a contiguous partition of the run, first release window, day/week/month cadence, and batch size; this supports split cours, cadence changes, batch drops, and double releases without flattening them into one false schedule. Platform and territory scope plus typed reschedule, pause, skip, or cancellation exceptions apply to the run.
- `release_events` record a manifestation or package publication, broadcast, theatrical, streaming, physical, or rerelease event. Optional segment scope supports staggered episode or chapter releases.
- `territories` provide stable hierarchical project IDs for worldwide, region, country, market, or custom availability scopes and may retain external territorial codes.
- `platforms` identify providers, broadcasters, stores, retailers, theaters, or libraries.
- `catalog_placements` point to a work, segment, content group, manifestation, or package and preserve how one platform presents it, including provider-defined localized titles, seasons, parts, volumes, collections, and channels.
- `platform_offerings` record subscription, rental, purchase, free, broadcast, archival, or other availability windows for a manifestation or package. Optional segment scope supports incomplete regional catalogs.
- `sources` remain concrete evidence artifacts and declare one or more `work_ids`. Singular release bindings remain convenient for simple artifacts; repeatable typed `observations` identify every manifestation, package, event, component, or platform offering observed by composite evidence. Every observation has a stable ID and must remain inside the source work scope.
- Typed `coverage` entries have stable IDs and identify complete, partial, excerpt, or sample coverage of works, segments, recursively nested content groups, manifestations, components, or packages. Optional position ranges use fields from the source medium profile and compactly delimit partial coverage. Both endpoints must identify the same canonical work through the medium's `work_scope_field`, and that work must be within the coverage target's resolved work scope. Omnibus files, anthology scans, box-set inspections, or archives therefore retain every work in scope, every concrete release object observed, and the exact material covered.
- `identifier_schemes` and `external_identifiers` preserve ISBNs, ISSNs, production codes, provider IDs, and other external identity systems separately from stable internal IDs.

A platform's catalog grouping is not canonical work hierarchy. For example, a service may market episodes as “Season 2” or “Part 3” without creating a new canonical season work. Store that provider label as a catalog placement unless independent creative identity justifies a work.

Language values use BCP-47-style tags; regional values must reference the territory registry. Localized titles belong to the work, segment, content-group, manifestation, package, or catalog context in which they are used. Every title variant identifies its title type, lifecycle status, primary-display role, and optional romanization scheme, allowing official, short, transliterated, literal, marketing, provider, alternate, and retired forms to coexist without ambiguity. Multiple titles may occupy the same locale, territory, title-type, and romanization scope only when their structured validity windows do not overlap; an absent or unknown window is conservatively treated as overlapping. Release and availability windows use structured start/end, precision, certainty, and optional timezone fields rather than opaque date prose. Entity-name localization remains outside this schema until entity incarnations and localized entity labels have their own executable contract.

## Assertion Provenance

`provenance_assertions` is the reusable evidence bridge for factual registry records and globally stable nested records, including content-group members, localized titles, release-run phases, source observations, source-coverage entries and ranges, and claim-authority rules. An assertion declares a controlled `claim_namespace`, snapshots the asserted value, optional dotted/indexed field path, observation time, effective window, and verification state. Every evidence link references a canonical source ID and one or more globally stable locators. Each locator explicitly selects an allowed medium and supplies a valid position for that medium, permitting one source artifact to cite novel text and an embedded illustration without pretending those positions share one schema. The source's `locator_medium_ids` is the allowlist; every locator must also remain inside the source's canonical work scope. Roles distinguish supporting, contradicting, and contextual evidence. Verified and inferred assertions require support, while disputed assertions require both support and contradiction. This central contract avoids adding incompatible citation fields to every record type and can be reused by non-narrative schema packs.

## Validation Boundary

The paired loaders currently validate media facets and explicit work-scope fields; work/release identity and hierarchy; work groups; continuities; claim-aware authority profiles; segments; recursively nested content groups with stable, role-bearing members; nonoverlapping historical localized titles; numbering schemes; total and partial ordering schemes; work and multi-input adaptation relationships; manifestations and segment mappings; package- or manifestation-scoped components and component lineage; release packages/phased runs/events; hierarchical territories; localized platform catalogs and offerings; structured time windows; external identifiers; globally addressable multi-target source observations and coverage ranges; semantically work-scoped composite evidence coverage; multi-position, mixed-media assertion provenance; source containers; aliases; volume catalogs; citation schemas; and resource bindings.

Capabilities marked `planned` in any pack are outside this executable boundary. A future schema version must add paired validation before a project may activate or instantiate those capabilities.
