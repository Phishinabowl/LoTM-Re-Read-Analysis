# Chronology Registry Contract

## Ownership

`Project_Config/chronology.yaml` instantiates domain-neutral chronology primitives owned by the core framework and optional domain annotations owned by selected packs. `Tools/Runtime/Python/knowledge_framework/chronology_config.py` and `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` are the behaviorally paired schema-1 loaders and comparison service.

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

## Narrative Contexts

Narrative contexts require the enabled `narrative-chronology` capability. They bind one coordinate system to registered works and/or continuities and assign a narrative role such as story, backstory, flashback, flashforward, time-travel origin/destination, or alternate timeline. An optional stable branch ID preserves branch identity without pretending every continuity is totally ordered with every other continuity.

Story chronology, causal order, publication/release order, and reader disclosure are separate axes. A narrative context does not make one of those orders stand in for another.

## Layering

- Core packs own coordinate kinds, value domains, direction, zero policy, relation kinds, mapping kinds, position/span validation, and comparison.
- Domain packs own optional annotations such as narrative chronology roles.
- Project configuration owns instantiated systems, era names, labels, contexts, and source-backed anchors.
- Content records will own concrete event/entity positions and provenance when those migrations are reviewed.

The LoTM project therefore stores First through Fifth Epoch labels in `Project_Config/chronology.yaml`; those values do not belong in the reusable narrative-media pack.

## Conformance

`Framework/Data/Chronology/` contains the portable V30 fixture corpus. Run `python Tools/Conformance/Suites/test_chronology.py` and `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Chronology.ps1` after changing chronology vocabulary, registry shape, comparison behavior, project composition, or narrative chronology roles.
