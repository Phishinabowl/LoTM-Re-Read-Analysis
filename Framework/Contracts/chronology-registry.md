# Chronology Registry Contract

## Ownership

`Project_Config/chronology.yaml` instantiates domain-neutral chronology primitives owned by the core framework and optional domain vocabulary owned by selected packs. `Tools/Runtime/Python/knowledge_framework/chronology_config.py` and `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` are the behaviorally paired schema-2 loaders, comparison service, and chronology-context topology service.

Civil timestamps and effective windows remain owned by `temporal-model.md`. Chronology coordinates do not extend, reinterpret, or weaken RFC 3339. Use chronology coordinates for fictional calendars, named eras, ordinal histories, relative dating systems, scientific or institutional counters, and other axes that are not portable civil timestamps.

## Coordinate Systems

Every coordinate system has a stable ID, label, coordinate kind, integer value domain, default direction, zero policy, aliases, and an origin position only when its kind is `relative`.

- `calendar` identifies a project-defined calendar axis. It does not imply Gregorian or RFC 3339 behavior.
- `era-ordinal` combines an explicitly ordered era with a local integer value.
- `ordinal` is a single ordered integer axis.
- `relative` is an integer axis anchored to a position in another coordinate system.

Value domains are `integer`, `nonnegative-integer`, or `positive-integer`. Direction is `ascending` or `descending`. Zero policy is `present`, `absent`, or `not-applicable`. A system with absent zero must use positive values. Display labels such as `UC 0079` remain presentation data; numeric comparison never destroys their source formatting.

## Eras and Positions

Eras belong only to `era-ordinal` systems and have unique positive ordinals within their system. Era ordinals always express chronological era order; system direction is the default for values inside each era and never reverses those ordinals. An era may override that local direction, allowing one ordered axis to represent systems such as BCE/CE or BBY/ABY where values count down in one era and up in another. Epoch names, ordering, and direction overrides are project-instance data, not generic pack vocabulary.

Positions have stable IDs, one coordinate system, an integer value, optional label, and core temporal certainty. An era is mandatory for `era-ordinal` positions and forbidden elsewhere. Duplicate coordinates are invalid. Relative systems must anchor to a position in another system so their origin cannot recursively define itself.

Positions in one coordinate system are comparable by chronological era ordinal and local value, respecting the era's effective direction within an era. Equal coordinates are concurrent. The exact zero position of a relative system is concurrent with its exact declared origin. Other positions in different systems are incomparable unless exact relationships, relative origins, or equivalent mappings connect their equivalence/order classes.

## Spans

Spans have stable IDs, one coordinate system, at least one endpoint, explicit endpoint inclusivity, and temporal certainty. Every endpoint must reference a position on the span's coordinate system. Two-ended spans must be nonempty and correctly ordered; open-ended spans preserve the omitted side without fabricating an infinity coordinate.

Chronology spans are not civil timestamp windows. They reuse certainty vocabulary while retaining chronology-position endpoints, so a year beyond 9999, a negative ordinal, or a fictional Epoch can remain valid without being forced through RFC 3339.

## Relations and Mappings

Relations preserve explicit `before`, `after`, `concurrent`, or `incomparable` claims between positions. An exact relation must agree with coordinate, relative-origin, or exact-equivalence behavior; an unordered position pair cannot carry duplicate exact relations. Intrinsic coordinate order and every exact relationship are validated as one transitive acyclic graph after exact equivalence closure. Causal relationships are deliberately outside this ordering vocabulary; time-travel causation must not be encoded as a cycle in chronological order.

Mappings connect positions in different coordinate systems as an `anchor` or `equivalent` with explicit certainty. Exact equivalence is transitively closed for comparison and contradiction detection. The service does not infer an offset formula, extrapolate from one anchor, or compare entire axes without a later reviewed mapping contract.

## Chronology Contexts

Chronology contexts require `chronology-contexts`. They give one coordinate system a stable operating context and a pack-owned role. Optional work, continuity, and branch references connect a context to project data without making narrative ownership mandatory. Core supplies domain-neutral roles such as primary, operational, control-plane, simulation, archive, and external. Narrative media extends that same namespace with story, backstory, flashback, flashforward, time-travel origin/destination, and alternate-timeline roles.

A context is not a coordinate, position, occurrence, continuity, or branch. It does not imply that its coordinate system is comparable with another context's coordinate system. Story chronology, causal order, publication/release order, reader disclosure, and operational observation order remain separate axes.

## Context Topology

Context relations require `chronology-context-topology`. They are directed, non-transitive, pack-vocabulary records between two distinct known contexts. Core defines `outside`, `observes`, `oversees`, `intervenes-in`, `projects-into`, and `receives-from`. A semantic duplicate with the same source, relation type, and target is invalid even when certainty differs. Reciprocal or cyclic topology is legal because these relations are not precedence edges.

Each relation may carry stable typed bindings to an `occurrence`, `occurrence-branch`, or `applicability-scope`. Parsing validates binding identity, vocabulary, and local uniqueness. Composed loading validates target existence after the source and occurrence registries are available, avoiding a chronology-to-occurrence dependency cycle. Bindings connect an intervention or observation to concrete data; they do not assert that either context or bound record occurs before another.

Outgoing and incoming relation queries preserve registry order and may be filtered by relation type. Unknown context queries fail explicitly. Positions, contexts, relations, and bindings are independent provenance subjects. The provider exposes the canonical position objects already owned by the registry; it does not copy them or promote coordinate systems, eras, spans, chronology relations, or mappings into provenance subjects.

`compare_positions` and `Get-KnowledgeChronologyComparison` never inspect contexts or context relations. Coordinates in different systems remain incomparable unless positions, relative origins, mappings, or ordinary chronology relations explicitly connect them. A context-topology cycle is therefore legal while a combined exact before/after cycle remains invalid.

## Layering

- Core packs own coordinate kinds, value domains, direction, zero policy, relation kinds, mapping kinds, context identity, context-topology primitives, position/span validation, and comparison.
- Domain packs extend context roles and may extend topology vocabulary without changing precedence semantics.
- Project configuration owns instantiated systems, era names, labels, contexts, and source-backed anchors.
- Content records will own concrete event/entity positions and provenance when those migrations are reviewed.

The LoTM project therefore stores First through Fifth Epoch labels in `Project_Config/chronology.yaml`; those values do not belong in the reusable narrative-media pack.

## Conformance

`Framework/Data/Chronology/` contains the cumulative portable chronology fixture corpus. The V50 fixture includes legal cyclic topology, typed target closure, direct positive and negative chronology-position provider lookup, context provenance targets, and an explicit cross-system incomparability proof. Run `python Tools/Conformance/Suites/test_chronology.py` and `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Chronology.ps1` after changing chronology vocabulary, registry shape, topology behavior, comparison behavior, provenance providers, or project composition.
