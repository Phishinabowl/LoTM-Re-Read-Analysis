# Page Schema Discovery Inventory

## Status And Boundary

This document is the noncanonical evidence record for Platform Phase 4.1. It inventories the page
and template structures that exist before the page-schema contract is defined. It does not define
field identity, module identity, normalized content, relationship ownership, physical storage, or
generated editor behavior.

Discovery IDs in this document are stable review handles only. They must not be consumed as field,
module, relationship, or record IDs. A later contract may promote a reviewed candidate through an
explicit mapping rather than silently treating its discovery ID as canonical authority.

Inventory work is read-only with respect to `Glossary_Threads/`. Conflicts remain unresolved until
they receive maintainer disposition. Proposed layers and resolutions are hypotheses for review.

## Source Coverage

### Templates

| Discovery ID | Source | Coverage |
| --- | --- | --- |
| `P4-SOURCE-TEMPLATE-UNIVERSAL` | `Glossary_Threads/TEMPLATE.md` | Shared metadata, prose, first appearance, chronology, related threads, type-specific data placeholder, Relationship Seeds, evidence, and Reader Knowledge Ledger. |
| `P4-SOURCE-TEMPLATE-CHARACTER` | `Glossary_Threads/Characters/TEMPLATE.md` | Character visible modules, optional-module policy, `character_profile`, graph projection guidance, and shared audit layers. |
| `P4-SOURCE-TEMPLATE-PATHWAY` | `Glossary_Threads/Pathways/TEMPLATE.md` | Pathway reveal, sequence/formula, institutional, metaphysical, artwork, and graph projection structures. |
| `P4-SOURCE-TEMPLATE-ITEM` | `Glossary_Threads/Items/TEMPLATE.md` | Item identity, classification, custody, use, related-system, significance, and graph-worthiness structures. |
| `P4-SOURCE-TEMPLATE-KNOWLEDGE` | `Glossary_Threads/Knowledge_Sources/TEMPLATE.md` | Knowledge-carrier identity, format, authorship, custody, source-unit, transfer, quote, interpretation, and claim structures. |

No dedicated template currently exists for Artifact, Concept, Deity, Epoch, Event, Faction, Family,
Location, Mystery, Tarot Card, Timeline, or Uniqueness glossary categories. Those categories inherit
the universal template through project taxonomy and are not evidence for a type-specific module
shape yet.

### Representative Populated Pages

| Discovery ID | Source | Why sampled |
| --- | --- | --- |
| `P4-SOURCE-PAGE-DUNN` | `Glossary_Threads/Characters/character-dunn-smith.md` | Early anonymous display, canonical reveal, dense state progression, equipment, events, eight knowledge units, and eleven projected relationship targets. |
| `P4-SOURCE-PAGE-NEIL` | `Glossary_Threads/Characters/character-old-neil.md` | Knowledge-source access, prayers and rituals, teaching, equipment, seven knowledge units, and eleven projected relationship targets. |
| `P4-SOURCE-PAGE-LEONARD` | `Glossary_Threads/Characters/character-leonard-mitchell.md` | Optional Tarot-card module, Book 1 and Donghua timing, late reveal hiding, four knowledge units, and six projected relationship targets. |
| `P4-SOURCE-PAGE-SEER` | `Glossary_Threads/Pathways/pathway-seer.md` | Populated pathway profile and visible chronology used to test pathway-template completeness. |
| `P4-SOURCE-PAGE-SLEEPLESS` | `Glossary_Threads/Pathways/pathway-sleepless.md` | Dense holder, sequence, reveal-progression, and visible chronology behavior. |

The Phase 4.1 character minimum is satisfied by Dunn Smith, Old Neil, and Leonard Mitchell. The two
pathway pages were added to verify a conflict exposed by the pathway template; they do not expand
this inventory into an all-page migration audit.

## Page Surface Review Frame

Review each inventory candidate against four independent surfaces:

| Surface | Owns | Must not own |
| --- | --- | --- |
| Structured knowledge | Typed facts, state, timing, confidence, relationships, evidence references, and machine validation. | Human narrative voice, generated layout, or authoring instructions. |
| Authored content | Stable human-written summaries, explanations, chronology prose, analysis, uncertainty, and other reader-facing Markdown blocks. | Machine facts that must be inferred by scraping prose or generated prose fabricated from taxonomy values. |
| Presentation | Headings, table layouts, labels, artwork placement, section order, and bounded rendering over eligible structured rows and authored blocks. | Canonical field meaning or unique facts that disappear when the view changes. |
| Maintainer guidance | Authoring help, omission and synchronization rules, investigation boundaries, and migration notes. | Canonical page content emitted merely because a template or editor supports it. |

The intended long-term page is a compound content record: structured state and authored content are
both first-class canonical project content, while presentation is reproducible and maintainer
guidance remains external to page records. This logical separation does not decide whether the
physical representation remains embedded Markdown, uses linked sidecars, moves into a database, or
uses another Phase 13 storage model.

At a reader boundary, a future renderer should determine subject visibility, filter structured rows,
filter authored blocks independently, render eligible authored prose verbatim, generate eligible
tables and indexes, and omit unsupported modules. It must not convert kebab-case values into invented
narrative prose.

## Discovered Surface Layers

| Discovery layer | Current purpose | Provisional treatment |
| --- | --- | --- |
| Visible metadata | Page classification, lifecycle-like status, visibility boundary, confidence, tags, update state, and navigation. | Split machine identity/policy from project presentation during Phase 4.2. |
| Visible prose and tables | Human-authored GitHub article mixed with current presentation. | Preserve authored prose separately; treat repeated table columns and layout as presentation evidence, not authority. |
| Type-specific data block | Page-local structured state used by current QA, bounded pages, and graph projection. | Primary legacy input for future logical normalization; do not copy its definitions into page records. |
| Relationship Seeds | Lightweight graph projection hints with timing and provenance pointers. | Legacy compatibility surface until Phase 6 defines canonical relationship ownership. |
| Evidence Index | Human-facing source and investigation navigation. | Evidence presentation candidate; normalized ownership remains deferred. |
| Reader Knowledge Ledger | Claim, disclosure, adaptation, attribution, evidence, and confidence audit history. | Audit/provenance evidence for Phase 5; do not require ordinary page state to be reconstructed from it. |
| Related Threads | Human navigation and pending-page references. | Presentation/navigation evidence, not relationship authority. |
| Maintainer instructions | Authoring, synchronization, omission, and future-rendering policy. | Move reusable rules into contracts or schema presentation; do not emit them into canonical records. |

## Shared Template Inventory

### Metadata And Navigation

All five templates repeat the following visible metadata labels:

`Type`, `Status`, `First Mention Volume`, `Subject Visible From`, `Current Analysis Status`,
`Confidence Level`, `Spoiler Boundary`, `Reader Knowledge Boundary`, `Tags`, and `Last Updated`.

All five also repeat `Related Threads` and `Related Investigations`. The values are Markdown text and
links rather than a YAML front matter document. `Type`, tags, slug behavior, placement, graph
eligibility, and QA eligibility also have project-level definitions in `Project_Config/taxonomy.yaml`.

### Shared Visible Sections

| Discovery candidate | Present in | Shape | Provisional layer |
| --- | --- | --- | --- |
| `P4-CAND-PURPOSE` | All templates | Human-authored prose. | Generic content module. |
| `P4-CAND-SPOILER-BOUNDARY` | All templates | Human-authored policy prose plus metadata summary. | Narrative-domain visibility module with project presentation. |
| `P4-CAND-READER-BOUNDARY` | All templates | Medium-specific visible bullets plus metadata summary. | Narrative-domain visibility module. |
| `P4-CAND-FIRST-APPEARANCE` | Universal, Character, Pathway | Ordered medium-specific reveal beats; Character adds a structured mirror. | Narrative-domain disclosure module. |
| `P4-CAND-CHRONOLOGY-PROSE` | All templates | Medium-specific human prose subsections. | Narrative-domain chronology presentation module. |
| `P4-CAND-OPEN-QUESTIONS` | All templates | Human-authored unresolved questions. | Generic content module with possible provenance integration later. |
| `P4-CAND-RELATED-THREADS` | All templates | Type/group-specific Markdown navigation lists. | Project presentation module. |
| `P4-CAND-RELATIONSHIP-SEEDS` | All templates | Repeated legacy YAML projection shape. | Legacy adapter surface owned later by Phase 6. |
| `P4-CAND-EVIDENCE-INDEX` | All templates | Human-facing source/investigation index. | Evidence presentation module. |
| `P4-CAND-KNOWLEDGE-LEDGER` | All templates | Embedded claim/audit YAML plus reader-state and adaptation prose. | Legacy claim/provenance input for Phase 5. |

The universal template is explicitly maximal. Type templates are permitted to omit unsupported or
empty sections, so absence alone is not a conflict unless another active rule requires that shape.

## Repeated Structured Shapes

These shapes recur across profile roots. Their listed fields are the union found in the reviewed
templates; individual modules currently use narrower variants.

| Discovery candidate | Observed fields |
| --- | --- |
| `P4-CAND-POSITION` | `medium`, `book`, `volume`, `chapter`, `season`, `installment_type`, `episode`, `release_order`, `timestamp`, `notes`. |
| `P4-CAND-POSITION-RANGE` | `from`, optional `to`, and nested position fields. |
| `P4-CAND-AVAILABILITY` | `medium`, `from`, `status`, `confidence`, `adaptation_relationship`, module-specific changing values, `graph_visibility`, display labels, and `notes`. |
| `P4-CAND-GRAPH-DISPLAY` | `behavior`, `label`, `visible_from`, and `resolves_to_canonical_at`. |
| `P4-CAND-GRAPH-PROJECTION-DISPLAY` | `graph_visibility`, `display_source_label`, `display_target_label`, and `display_relationship_type`. |
| `P4-CAND-SOURCE-REF` | Position fields plus optional source-unit position; current rows usually identify a work but do not carry canonical `source_id`. |
| `P4-CAND-STATE-ROW` | Row selector or stable-looking value, current `status`, current `confidence`, `availability`, and `notes`. |
| `P4-CAND-ARTWORK` | Label/type/file/usage plus varying image number, crop, source file, source crop, alt text, and character artwork fields. |

No canonical shared shape is established here. The observed differences are inputs to the field and
module contracts.

## Character Template Inventory

### Visible And Structured Modules

| Discovery candidate | Visible section | `character_profile` field signature | Requirement evidence | Provisional layer |
| --- | --- | --- | --- | --- |
| `P4-CAND-CHARACTER-SNAPSHOT` | Character Snapshot | No direct structured mirror. | Required minimum. | Narrative character presentation. |
| `P4-CAND-CHARACTER-FIRST-APPEARANCE` | First Appearance / First Meaningful Mention | `first_appearance_beats`: `medium`, `beat_type`, `title`, `position`, `context`, reader/viewer state, `graph_display`, `status`, `confidence`, related timelines/claims, `source_refs`, `notes`. | Required minimum. | Narrative disclosure. |
| `P4-CAND-CHARACTER-IDENTITY` | Names, Aliases & Titles | `identities`: `field`, `value`, `status`, `confidence`, `availability`, `notes`. | Optional when relevant. | Reusable entity description. |
| `P4-CAND-CHARACTER-PHYSICAL` | Physical Profile | `physical_profile`: `field`, `value`, `status`, `confidence`, `availability`, `notes`. | Optional when relevant. | Narrative character description; not universal core. |
| `P4-CAND-CHARACTER-STATUS-LOCATION` | Status, Origin & Location | `status_origin_location`: `field`, `value`, `status`, `confidence`, `availability`, `notes`. | Optional when relevant. | Mixed entity state and project/domain vocabulary. |
| `P4-CAND-CHARACTER-AFFILIATION` | Affiliations | `affiliations`: `organization`, `relationship`, `status`, `confidence`, `availability`, `notes`. | Optional when relevant. | Reusable typed-relationship state candidate. |
| `P4-CAND-CHARACTER-PATHWAY` | Pathway & Ability State | `pathway_state`: `pathway`, `target`, fixed/default relationship, state, availability; `sequence_state`: sequence, name, pathway, state, availability. | Optional when relevant. | LoTM project extension pending broader fantasy evidence. |
| `P4-CAND-CHARACTER-TAROT` | Associated Tarot Card | Card identity/number/target/alias/association, images, state, availability, and graph display. | Omit by default. | LoTM project extension. |
| `P4-CAND-CHARACTER-MYTHICAL-FORM` | Mythical Creature Form State | Form/stage/pathway/threshold, state, availability, and graph display. | Omit by default. | LoTM project extension. |
| `P4-CAND-CHARACTER-UNIQUENESS` | Uniqueness State | Uniqueness/state, current state, availability, and graph display. | Omit by default. | LoTM project extension. |
| `P4-CAND-CHARACTER-ABILITY` | Ability Index | Ability/source/state, availability, and notes. | Optional when relevant. | Narrative character capability candidate. |
| `P4-CAND-CHARACTER-EQUIPMENT` | Equipment & Artifacts | Item/target/type, possession, significance, graph relevance, page worthiness, confidence, availability, and display. | Optional when relevant. | Reusable possession module plus project values. |
| `P4-CAND-CHARACTER-KNOWLEDGE-SOURCE` | Knowledge Sources & Documents | Source/target/type, access, significance, graph relevance, page worthiness, confidence, availability, and display. | Optional specialized module. | Narrative knowledge-access module. |
| `P4-CAND-CHARACTER-PERSONALITY` | Personality | Trait/evidence/state, availability, and notes. | Optional when relevant. | Narrative character description. |
| `P4-CAND-CHARACTER-RELATIONSHIP` | Relationships | Target/relationship/state, availability, and graph display. | Optional when relevant. | Reusable typed-relationship state candidate. |
| `P4-CAND-CHARACTER-COMPANION` | Messenger / Servants / Companions | Entity/type/state, availability, and graph display. | Omit by default. | Domain/project specialization over relationship state. |
| `P4-CAND-CHARACTER-RITUAL` | Prayers & Ritual Access; Prayer / Ritual Texts | Label/type/function/state, availability, concept link, wording, and notes. | Omit by default. | LoTM project extension pending reusable ritual pack. |
| `P4-CAND-CHARACTER-EVENT` | Major Events & Fights | Event/type/part/role/outcome, availability, and graph display. | Optional when relevant. | Narrative participation index; event authority remains external. |
| `P4-CAND-CHARACTER-TIMELINE` | Chronological Development | `timeline_entries`: stable ID, title, medium, range, visibility, type, human prose fields, related records, source refs, and notes. | Required when meaningful chronology exists. | Narrative chronology presentation/state bridge. |

### Representative Character Exercise Matrix

| Candidate | Dunn | Old Neil | Leonard |
| --- | --- | --- | --- |
| Official artwork | Exercised | Omitted | Exercised |
| First appearance beats | Exercised, including anonymous-to-canonical resolution | Exercised | Exercised across Novel and Donghua |
| Identity / physical / status | Exercised | Exercised | Exercised |
| Affiliations / pathway / sequence | Exercised | Exercised | Exercised with late progression |
| Associated Tarot card | Omitted | Omitted | Exercised |
| Ability index | Exercised | Exercised | Exercised |
| Equipment | Exercised | Exercised | Omitted |
| Knowledge sources | Omitted | Exercised | Exercised |
| Personality / relationships / events | Exercised | Exercised | Exercised |
| Prayers and rituals | Omitted | Exercised | Omitted |
| Timeline entries | Exercised | Exercised | Exercised across early and late Book 1 plus Donghua |
| Knowledge units | 8 | 7 | 4 |
| Relationship target rows observed | 11 | 11 | 6 |

None of the sampled pages exercises mythical-creature, Uniqueness, or companion modules. Their
current evidence comes only from the character template.

## Pathway Template Inventory

| Discovery candidate | Visible section | `pathway_profile` field signature | Provisional layer |
| --- | --- | --- | --- |
| `P4-CAND-PATHWAY-IDENTITY` | Purpose, first mention, title display | `reader_boundary`, `stable_slug`, and `name_timeline` with usage, active range, confidence, availability, and display behavior. | LoTM project extension. |
| `P4-CAND-PATHWAY-ARTWORK` | Header and Tarot presentation | `official_artwork` and `associated_tarot_card` crop metadata. | Project presentation/resource integration. |
| `P4-CAND-PATHWAY-HIGHER-ORDER` | Related metaphysical entities | Entity/layer/state, availability, and graph display. | LoTM project extension. |
| `P4-CAND-PATHWAY-SEQUENCE` | Known Sequences | Sequence/name/state; formula source, ingredients, preparation, output, availability; and ability traits, demonstrations, training, limits, unknowns. | LoTM project extension with possible future fantasy-pack decomposition. |
| `P4-CAND-PATHWAY-INSTITUTIONAL-ACCESS` | Institutional Access | Faction/access/confidence, availability, and graph display. | LoTM project extension over relationship state. |
| `P4-CAND-PATHWAY-AFFILIATIONS` | Affiliated Factions | Faction/type/confidence, availability, and graph display. | Typed-relationship candidate. |
| `P4-CAND-PATHWAY-HOLDERS` | Known Holders | Character/status/sequence/name/confidence, availability, adaptation, and graph display. | Typed-relationship candidate with LoTM state. |
| `P4-CAND-PATHWAY-UNIQUENESS` | Associated Uniqueness | Reader-safe name, state, availability/display, article, holder, deity, formula, and notes. | LoTM project extension. |
| `P4-CAND-PATHWAY-MYTHICAL` | Associated Mythical Creature | Concept index and form/stage/threshold state with availability/display. | LoTM project extension. |

The pathway template and both populated pathway pages contain visible Chronological Development
sections but no `timeline_entries` module. The populated pages also lack `timeline_id` comments.

## Item Template Inventory

| Discovery candidate | Visible section | `item_profile` field signature | Provisional layer |
| --- | --- | --- | --- |
| `P4-CAND-ITEM-SNAPSHOT` | Item Snapshot | No direct structured mirror. | Narrative/project presentation. |
| `P4-CAND-ITEM-IDENTITY` | Names & Labels | Field/value/state, availability, and notes. | Reusable entity description. |
| `P4-CAND-ITEM-CLASSIFICATION` | Snapshot and page policy | Item type, significance, graph relevance, page worthiness, artifact boundary, state, availability, notes. | Project classification and projection policy. |
| `P4-CAND-ITEM-CUSTODY` | Ownership / Custody / Access | Target/relationship/possession state, availability, and graph display. | Reusable possession/custody module. |
| `P4-CAND-ITEM-FUNCTION` | Functions & Uses | Function/target/relationship/state, availability, and graph display. | Reusable object-function module. |
| `P4-CAND-ITEM-RELATED-SYSTEM` | Related Concepts / Systems | Target/relationship/state, availability, and graph display. | Typed-relationship candidate. |
| `P4-CAND-ITEM-APPEARANCE` | Appearance / Physical Description | No structured `item_profile` mirror. | Narrative object-description candidate. |

No populated Item page exists yet. The template contains visible chronology but no structured first-
appearance or timeline module.

## Knowledge Source Template Inventory

| Discovery candidate | Visible section | `knowledge_source_profile` field signature | Provisional layer |
| --- | --- | --- | --- |
| `P4-CAND-SOURCE-SNAPSHOT` | Source Snapshot | No direct structured mirror. | Narrative/project presentation. |
| `P4-CAND-SOURCE-IDENTITY` | Names & Labels | Field/value/state, availability, and notes. | Reusable entity description. |
| `P4-CAND-SOURCE-FORMAT` | Format / Medium | Source type, format, language/encoding, completeness, reliability, state, availability, notes. | Narrative publishing/evidence domain candidate. |
| `P4-CAND-SOURCE-AUTHORSHIP` | Authorship / Origin | Target/relationship/state, availability, and graph display. | Typed relationship and provenance candidate. |
| `P4-CAND-SOURCE-ACCESS` | Access / Custody / Readers | Target/relationship/access state, availability, and graph display. | Reusable access/custody module. |
| `P4-CAND-SOURCE-KNOWLEDGE` | Knowledge Entries | Claim/source-unit/batch/fragment/sequence, provider/reader transfer context, target/relationship, quote reference, interpretation, state, availability, and graph display. | Narrative knowledge-carrier module with provenance integration. |
| `P4-CAND-SOURCE-QUOTE-INDEX` | Quote / Evidence Index | No separate structured mirror beyond `knowledge_entries.quote_ref`. | Evidence presentation candidate. |

No populated Knowledge Source page exists yet. The template contains visible chronology but no
structured first-appearance or timeline module.

## Legacy Projection And Audit Inventory

### Relationship Seed Shape

Every reviewed template repeats `relationships[]` with `target`, `relationship_type`, `start`,
`status`, `confidence`, `projection_owner`, `projection_scope`, `projection_source`, `claim_id`,
hidden-endpoint defaults, and `notes`. `start` contains medium, volume, chapter, season, episode, and
release order, but not `book`. The source entity is implicit in the containing page.

The sampled character pages use `projection_source` selector strings such as
`character_profile.affiliations[faction-nighthawks]`. These selectors depend on page-local values
rather than persisted row IDs. Relationship Seeds remain graph hints under current project rules and
must not become Phase 4 relationship authority.

### Reader Knowledge Ledger Shape

The universal and Character templates expose the richest repeated shape: claim ID/text, truth and
confidence, canon scope, occurrence position, tags, disclosure history, adaptation relationships,
subject attribution, related investigations/boards, evidence basis, confidence history, and update
date. Item and Knowledge Source templates use narrower and mutually different examples. Populated
character pages further exercise multiple disclosures, claim supersession, source-page attribution,
and adaptation-specific claim state.

### Maintainer-Only Instructions

Templates currently embed instructions for artwork promotion, filename and folder placement,
controlled tags and values, page-worthiness, section omission, synchronization between visible and
structured layers, source-search boundaries, relationship ownership, graph projection, prose
rendering, and future page links. These instructions are policy evidence. They are not fields to be
emitted by future page generators.

## Conflict Register

All entries are `pending-maintainer-review`. Proposed dispositions identify the current engineering
hypothesis only.

| Finding ID | Class | Evidence and difference | Likely authority | Proposed resolution/disposition | Blocking | Owning phase |
| --- | --- | --- | --- | --- | --- | --- |
| `P4-CONFLICT-001` | Ownership / semantic | Visible `Subject Visible From`, visible Reader Knowledge Boundary, and profile `reader_boundary` overlap but have different described purposes. | Page visibility policy plus narrative disclosure contract. | Define distinct page-title visibility, analysis coverage, and row availability semantics; `requires-normalization`. | Yes | 4.2 and 4.6 |
| `P4-CONFLICT-002` | Naming / lifecycle | Metadata `Status`, `Current Analysis Status`, row `status`, relationship `status`, knowledge `truth_status`, and pack/category lifecycle use overlapping status language. | Owning field contracts and controlled-value namespaces. | Assign distinct field identities and value sources; `requires-normalization`. | Yes | 4.2 |
| `P4-CONFLICT-003` | Structural / controlled value | Dunn and Old Neil carry `data_model_version: page-local-state-v2` and `availability_policy`; Leonard and the Character template omit both. Item and Knowledge Source declare v1; Pathway declares neither. | Future page-schema/version contract. | Remove page-local schema declarations or define one inherited schema/version source; `requires-normalization`. | Yes | 4.2-4.5 |
| `P4-CONFLICT-004` | Timing / type | Position variants disagree about `medium`, `book`, `installment_type`, timestamp, and notes. Relationship Seed `start` omits `book`, while project rules require canonical work identity when known. | Core chronology/source contracts plus narrative position modules. | Define typed reusable position references and a legacy adapter; `requires-normalization`. | Yes | 4.2 and 5.2 |
| `P4-CONFLICT-005` | Requirement / structural | Pathway template and both active pathway pages have meaningful visible chronology but no `timeline_entries` or matching `timeline_id` comments despite current project rules. | Narrative chronology module and existing authoring policy. | Record as current drift and normalize during the Pathway migration wave; `invalid-drift` or `requires-normalization`. | No for Phase 4 contract; yes before Pathway legacy retirement | 4.9 and 13.3 |
| `P4-CONFLICT-006` | Requirement / structural | Item and Knowledge Source templates advertise first appearance in snapshots and visible chronology, but have no explicit first-appearance section, `first_appearance_beats`, or `timeline_entries`. | Type profile requirements over narrative disclosure modules. | Decide whether these are required modules, conditional modules, or snapshot-only presentation; `deferred-decision`. | Yes | 4.6 and 4.9 |
| `P4-CONFLICT-007` | Presentation / structural | Character, Pathway, Item, and Knowledge Source artwork/resource fields have different shapes and provenance detail. | Resource registry integration plus type presentation modules. | Define one resource-reference primitive with type-specific presentation overlays; `requires-normalization`. | No | 4.2-4.5 |
| `P4-CONFLICT-008` | Structural / semantic | Universal, Character, Item, and Knowledge Source Knowledge Unit examples differ in position, disclosure, attribution, evidence, adaptation, and confidence-history fields. | Provenance and future normalized claim contract. | Preserve all observed fields for Phase 5 reconciliation rather than selecting a template winner now; `requires-normalization`. | No for Phase 4 modules | 5.1-5.2 |
| `P4-CONFLICT-009` | Presentation / controlled value | Visible tables use title-cased prose values such as Strong Evidence and Current at boundary; data blocks use kebab-case machine values, but no formal display-label mapping owns the conversion. | Field controlled-value source plus presentation schema. | Formalize machine/display separation and localized labels; `confirmed-equivalent` if mappings prove exact. | Yes | 4.2 and 4.8 |
| `P4-CONFLICT-010` | Requirement / semantic | Populated pages sometimes store explicit `Unknown` rows, while optional-module guidance says to omit empty material. Unknown, absent, not investigated, and not applicable are not formally distinct. | Presence/readiness semantics. | Define explicit unknown/null/omitted/not-applicable behavior by readiness level; `requires-normalization`. | Yes | 4.6 |
| `P4-CONFLICT-011` | Ordering | `state_sort_order` is newest-to-oldest, while first-appearance and chronology policy require oldest-to-newest. Ordering is module-specific but currently looks profile-global. | Module ordering contract. | Move ordering to the module/list definition or define scoped exceptions; `requires-normalization`. | Yes | 4.3 and 4.5 |
| `P4-CONFLICT-012` | Ownership / projection | Facts may appear in prose tables, profile rows, ledger units, Related Threads, and Relationship Seeds. Current policy describes precedence, but the structures do not enforce ownership or equivalence. | Phase 5 normalized records and Phase 6 relationships. | Preserve each legacy layer and produce explicit adapters/equivalence diagnostics; `legacy-compatibility-only`. | No for Phase 4 | 5.2 and 6.3 |
| `P4-CONFLICT-013` | Identity / projection | Many profile rows lack stable row IDs; Relationship Seed `projection_source` relies on bracketed field values or targets. Renames can therefore change selector identity. | Normalized record and relationship identity contracts. | Do not invent IDs in Phase 4; define field/module identity now and derive temporary row IDs in Phase 5.2; `deferred-decision`. | No for Phase 4 | 5.1-5.2 |
| `P4-CONFLICT-014` | Layering | LoTM concepts such as Pathway, Sequence, Uniqueness, associated Tarot cards, and mythical forms coexist beside broadly reusable identity, evidence, custody, and chronology concepts. | Pack/project composition contract. | Keep LoTM terms project-owned until cross-project evidence justifies a reusable pack; `requires-normalization`. | Yes | 4.3 and 4.5 |
| `P4-CONFLICT-015` | Type / ownership | `status_origin_location` combines literal status/origin fields with location and occupation relationships; `equipment_artifacts` can contain artifacts, items, resources, case evidence, or knowledge carriers. | Field/module ownership contract. | Split reusable fields by semantic owner while retaining legacy presentation grouping; `requires-normalization`. | Yes | 4.2-4.5 |
| `P4-CONFLICT-016` | Requirement / presentation | Character Snapshot, Item Snapshot, and Source Snapshot are human summaries without direct structured mirrors, while some snapshot values duplicate structured state. | Authored-block and editor projection contracts. | Preserve authored summaries separately from generated current-state summaries; `requires-normalization`. | Yes | 4.4 and 4.7-4.8 |
| `P4-CONFLICT-017` | Timing / semantic | Pathway `associated_tarot_card` has one undated current association, while character Tarot assignment carries availability and reader-safe graph timing. The same label describes pathway symbolism and character identity assignment. | Separate project field/module definitions. | Keep distinct field identities and require timing only for the character assignment semantics; `intentional-specialization`. | Yes | 4.2-4.3 |
| `P4-CONFLICT-018` | Duplication / drift risk | Shared metadata, seed, and ledger examples are copied into each type template and have already diverged. | Future generated template projection. | Make shared modules authoritative and generate or validate overlays rather than copying definitions; `requires-normalization`. | Yes | 4.3-4.4 and 4.8 |
| `P4-CONFLICT-019` | Layering / ownership | Current templates mix structured facts, authored prose, presentation layout, and maintainer instructions in one document, making schema authority and long-term prose preservation ambiguous. | Page-surface separation plus field, module, authored-block, and presentation contracts. | Treat structured state and authored blocks as canonical content, presentation as reproducible projection, and guidance as external policy; `requires-normalization`. | Yes | 4.1.2-4.8 |

## Maintainer Decisions Required Before Phase 4.1 Closure

The following groups require explicit maintainer review before contract implementation proceeds:

1. Whether the four-surface review frame correctly preserves structured state and authored prose as
   canonical content while separating presentation and maintainer guidance.
2. Whether the proposed conflict dispositions are correct, especially the treatment of current
   pathway chronology as migration drift rather than a Phase 4 source edit.
3. Whether Item and Knowledge Source pages should inherit full first-appearance and timeline modules
   conditionally, or retain a lighter snapshot-only presentation.
4. Whether explicit unknown values should satisfy a recommended field at draft-valid readiness while
   omitted and not-applicable remain distinct states.
5. Whether page-level analysis coverage should remain persisted on page records after the canonical
   visibility and row-availability fields are separated.
6. Whether broadly reusable narrative character modules should initially live in existing narrative
   packs or in a new page-schema-oriented pack family introduced later in Phase 4.

No decision in this section authorizes changes to canonical LoTM pages or templates.
