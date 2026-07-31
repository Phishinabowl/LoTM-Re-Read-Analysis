# Narrative Source Registry Contract

`Project_Config/sources.yaml` schema version 3 is the executable project-instance contract for selected narrative packs. `Tools/source_config.py` and `Tools/Source-Config.ps1` enforce the same fields and reference rules.

## Media Facets

The registry instantiates four selected-pack namespaces before defining medium profiles:

- `media_modalities`: labeled modality IDs from `source.media-modality`.
- `cultural_forms`: labeled cultural forms from `source.cultural-form`, each linked to one instantiated modality.
- `release_forms`: labeled work/release forms from `source.release-form`.
- `container_formats`: labeled evidence containers from `source.container-format`.

Every `mediums` entry must declare at least one `modality_id` and may declare cultural forms whose linked modalities are present. The medium continues to own position fields, sorting fields, and citation formats because it is the reader-boundary channel.

Every work must declare `work_type`, `medium_id`, `release_form_id`, and `work_status`. These axes are independent: `medium_id` selects the reader-position profile, while `release_form_id` describes the creative unit. Every evidence source must declare one or more `container_format_ids`; container identity does not alter the work's medium or release form.

## Work Structure And Ordering

`segments` is a stable-ID mapping for configurable work parts. A segment declares its work, type, label, optional positive ordinal, and optional parent segment. Parent chains must remain inside one work and cannot cycle. Segment types come from `source.segment-type`.

`ordering_schemes` stores named orders independently of group membership. Each scheme declares an ordering type from `source.ordering-type` and a non-empty list of unique work or segment targets with unique positive ordinals. Projects may therefore preserve publication, release, story, production, and recommended orders simultaneously.

The existing verified `volumes` catalog remains a specialized convenience for work-local novel chapter boundaries. It does not replace the generic segment model.

## Continuity And Authority

Continuity membership and relationship statuses come from the selected-pack `source.membership-status` namespace rather than loader-local allowlists. Authority profiles determine accepted statuses, continuity precedence, source-priority direction, comparable derivative relationships, conflict behavior, and deviation ownership.

Work-level continuity membership is executable. Segment- and claim-scoped continuity, entity incarnations, and retcon/supersession records remain planned capabilities and must not be approximated with page-local enums.

## Adaptation Mappings

`adaptation_mappings` maps a source work to a target work and may narrow either side to registered segments. Empty segment lists mean the mapping applies at work scope. Mapping types come from `source.adaptation-mapping-type`; statuses use the same controlled membership-status vocabulary as other canon-bearing relationships.

Mappings preserve direction and provenance. They may represent direct correspondence, omission, combination, splitting, reordering, expansion, condensation, adaptation-original material, or recontextualization. Adaptation mappings do not overwrite source-work claims.

## Validation Boundary

The paired loaders currently validate media facets, work/release identity, work groups, continuities, authority profiles, segments, named ordering schemes, work and adaptation relationships, source containers, evidence sources, aliases, volume catalogs, citation schemas, and resource bindings.

Capabilities marked `planned` in any pack are outside this executable boundary. A future schema version must add paired validation before a project may activate or instantiate those capabilities.
