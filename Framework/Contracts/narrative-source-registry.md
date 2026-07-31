# Narrative Source Registry Contract

`Project_Config/sources.yaml` schema version 5 is the executable project-instance contract for selected narrative packs. `Tools/source_config.py` and `Tools/Source-Config.ps1` enforce the same fields and reference rules.

## Media Facets

The registry instantiates four selected-pack namespaces before defining medium profiles:

- `media_modalities`: labeled modality IDs from `source.media-modality`.
- `cultural_forms`: labeled cultural forms from `source.cultural-form`, each linked to one instantiated modality.
- `release_forms`: labeled work/release forms from `source.release-form`.
- `container_formats`: labeled evidence containers from `source.container-format`.

Every `mediums` entry must declare at least one `modality_id` and may declare cultural forms whose linked modalities are present. The medium continues to own position fields, sorting fields, and citation formats because it is the reader-boundary channel.

Every work must declare `work_type`, `medium_id`, `release_form_id`, and `work_status`. These axes are independent: `medium_id` selects the reader-position profile, while `release_form_id` describes the creative unit. A work may name a `parent_work_id` when a creative work is genuinely contained by another creative work; parent chains cannot cycle. Works and segments may carry localized titles without changing their stable identity.

Every evidence source must declare one or more `container_format_ids`; container identity does not alter the work's medium or release form.

## Work Structure And Ordering

`segments` is a stable-ID mapping for configurable work parts. A segment declares its work, type, label, optional positive ordinal, and optional parent segment. Parent chains must remain inside one work and cannot cycle. Segment types come from `source.segment-type`.

`numbering_schemes` assign display numbers and aliases to work or segment targets inside an explicit work or work-group scope. Numbering does not imply order: use an ordering scheme for sequence. This separation supports issue `0`, legacy comic numbering, production codes, split issue numbers, and provider numbering without coercing them into integers.

`ordering_schemes` stores named orders independently of group membership. Each entry has a stable ID and a unique work or segment target. A `total` ordering uses unique positive ordinals. A `partial` ordering omits ordinals and uses `after_entry_ids` to express acyclic precedence, allowing concurrent, incomparable, or not-yet-fixed branches. Projects may therefore preserve publication, release, story, production, and recommended orders simultaneously without inventing one false universal sequence.

The existing verified `volumes` catalog remains a specialized convenience for work-local novel chapter boundaries. It does not replace the generic segment model.

## Continuity And Authority

Continuity membership and relationship statuses come from the selected-pack `source.membership-status` namespace rather than loader-local allowlists. Authority profiles determine accepted statuses, continuity precedence, source-priority direction, comparable derivative relationships, conflict behavior, and deviation ownership.

Work-level continuity membership is executable. Segment- and claim-scoped continuity, entity incarnations, and retcon/supersession records remain planned capabilities and must not be approximated with page-local enums.

## Adaptation Mappings

`adaptation_mappings` maps one or more `basis_inputs` to a target work and may narrow every input and the target to registered segments. Empty segment lists mean work scope. Each basis input states whether it is a primary source, secondary source, prior adaptation, inspiration, or shared property. Mapping types come from `source.adaptation-mapping-type`; statuses use the same controlled membership-status vocabulary as other canon-bearing relationships.

Mappings preserve direction and provenance. They may represent direct correspondence, omission, combination, splitting, reordering, expansion, condensation, adaptation-original material, or recontextualization. Adaptation mappings do not overwrite source-work claims.

## Manifestations And Distribution

Creative identity and distribution identity are separate:

- `works` own the creative unit and its canonical hierarchy.
- `manifestations` own a concrete edition, translation, cut, remaster, episodic recut, compilation cut, or software build of one work. An empty `segment_ids` list means the whole work; a populated list scopes the manifestation without inventing separate works. They may carry language, territory, container, localized-title, and alias metadata.
- `release_components` own tracks and bundled components such as subtitles, audio, captions, commentary, deleted scenes, or embedded illustrations.
- `release_packages` bundle manifestations, selected segments, components, and containers as box sets, omnibuses, multi-disc sets, collector editions, or other commercial packages.
- `release_events` record a manifestation or package publication, broadcast, theatrical, streaming, physical, or rerelease event. Optional segment scope supports staggered episode or chapter releases.
- `territories` provide stable hierarchical project IDs for worldwide, region, country, market, or custom availability scopes and may retain external territorial codes.
- `platforms` identify providers, broadcasters, stores, retailers, theaters, or libraries.
- `catalog_placements` point to a work, segment, manifestation, or package and preserve how one platform presents it, including provider-defined titles, seasons, parts, volumes, collections, and channels.
- `platform_offerings` record subscription, rental, purchase, free, broadcast, archival, or other availability windows for a manifestation or package. Optional segment scope supports incomplete regional catalogs.
- `sources` remain concrete evidence artifacts and may bind to the manifestation, package, release event, components, or platform offering they actually observe.
- `identifier_schemes` and `external_identifiers` preserve ISBNs, ISSNs, production codes, provider IDs, and other external identity systems separately from stable internal IDs.

A platform's catalog grouping is not canonical work hierarchy. For example, a service may market episodes as “Season 2” or “Part 3” without creating a new canonical season work. Store that provider label as a catalog placement unless independent creative identity justifies a work.

Language values use BCP-47-style tags; regional values must reference the territory registry. Localized titles belong to the work, segment, manifestation, or catalog context in which they are used. Release and availability windows use structured start/end, precision, certainty, and optional timezone fields rather than opaque date prose. Entity-name localization remains outside this schema until entity incarnations and localized entity labels have their own executable contract.

## Validation Boundary

The paired loaders currently validate media facets, work/release identity and hierarchy, work groups, continuities, authority profiles, segments, localized titles, numbering schemes, total and partial ordering schemes, work and multi-input adaptation relationships, manifestations, release packages/components/events, hierarchical territories, platform catalogs and offerings, structured time windows, external identifiers, source containers, evidence sources, aliases, volume catalogs, citation schemas, and resource bindings.

Capabilities marked `planned` in any pack are outside this executable boundary. A future schema version must add paired validation before a project may activate or instantiate those capabilities.
