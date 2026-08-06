# Hosted Identity And Embodiment Registry Contract

## Purpose

`Project_Config/hosting.yaml` schema version 2 separates a stable identity-bearing subject from
the physical or virtual carrier that hosts it. The registry models carrier lifecycle, occupancy,
control, movement, copy, and handoff without treating a body, control unit, avatar, container,
vessel, or runtime as the identity that occupies it.

This is a domain-neutral service. Narrative projects may use it for bodies, personas, control
units, copied minds, or simulated avatars. Other projects may use it for software processes and
containers, agents and runtimes, virtual avatars, or carefully bounded medical identity/carrier
records. Pack vocabulary supplies domain-facing labels; the registry owns only the common
structure.

## Record Families

### Host Carriers

A `host-carrier` has a stable ID, configuration lifecycle, pack-owned carrier kind, label, one
existing occurrence track that owns its operational lifecycle, an inclusive activation entry, and
an optional exclusive termination entry. Carrier lifecycle is independent from every occupant.
Destroying, replacing, or deactivating a carrier does not by itself retire, merge, split, or
reconcile an identity.

Carriers are provenance-addressable and participate in stable-ID reconciliation. Binding,
occupancy, and transition records are provenance-addressable nested operational records, not
reconciliation targets.

### Host Carrier Bindings

A `host-carrier-binding` relates one child carrier to one parent carrier without treating either
carrier as an identity. Its pack-owned kind describes structural use such as installation,
containment, attachment, virtual execution, or projection. Domain packs may add narrower labels;
the registry owns the common child/parent shape only.

Each binding supplies activation entries for both carrier lifecycle tracks. Optional termination
entries must be supplied for both sides together. Paired activation entries resolve to one
occurrence, as do paired termination entries, but each carrier retains its independent track and
lifecycle. Activation is inclusive and termination is exclusive. Moving a child carrier between
parents therefore ends one binding and activates another; it does not move, copy, hand off,
reconcile, or retire the identity directly occupying that child.

Bindings reject unknown or identical endpoints, unsupported kinds, boundaries outside either
carrier lifecycle, mismatched paired occurrences, semantic duplicate intervals, and cycles. A
carrier chain never infers identity continuity, equivalence, incarnation, direct occupancy, or
truth.

### Hosted Identity Occupancies

A `hosted-identity-occupancy` references one identity target supplied through the identity-target
provider boundary, one carrier, one pack-owned role, and inclusive activation plus optional
exclusive termination entries on the carrier lifecycle track. The initial provider supports
`entity`, `entity-incarnation`, and `identity-phase`; future domain registries may supply other
identity-bearing target types without importing narrative semantics into this contract.

Several occupancies may overlap on one carrier. One subject may occupy several carriers. Neither
shape implies equivalence, continuity, replacement, derivation, control, or factual truth. Roles
such as `active`, `dormant`, `co-resident`, and `controlling` describe the occupancy only. A query
returns every applicable occupant or controller in stable ID order rather than inventing a winner.

### Hosted Identity Transitions

A `hosted-identity-transition` references source and target occupancies, one concrete occurrence,
and exact source/target track entries that resolve to that occurrence.

- `move` preserves one exact identity target, crosses carriers, terminates the source occupancy,
  and activates the target occupancy. It does not create an incarnation or reconciliation record.
- `copy` requires distinct identity targets and carriers, keeps the source active at the copy
  boundary, activates the target, and references an existing identity-relationship record.
  Derivation, cloning, counterpart, and divergence semantics remain owned by the identity
  relationship service.
- `control-handoff` transfers the controlling role between distinct identity targets on one
  carrier. It makes no identity-continuity assertion.

The relationship reference on `copy` proves that identity lineage was modeled elsewhere; hosting
does not reinterpret the relationship or infer equivalence from code, memory, appearance, shared
history, or co-residence.

## Boundary And Query Semantics

All operational boundaries reuse existing occurrence track entries. The hosting registry creates
no occurrence, chronology position, track, entry, precedence edge, state transition, or evidence
claim. Activation is inclusive and termination is exclusive. A carrier or occupancy ending at an
entry is therefore inactive at that entry, allowing an exact handoff without overlapping the old
and new controller accidentally.

Occupancy queries require an explicit carrier and track-entry boundary. They reject unknown carriers,
unknown entries, and entries from another track. `occupancies_at` returns every active occupancy;
`controllers_at` filters that set to the `controlling` role. Empty results are valid. Co-control is
represented as several results, not an ambiguity error or automatic priority decision.

Carrier-topology queries accept an explicit boundary-entry mapping keyed by lifecycle track ID.
This keeps incomparable carrier tracks independent: the caller supplies the exact entry for each
track traversed, and the registry never invents a chronology mapping. Direct child/parent queries
return active binding records only. Ancestor and descendant queries return every active path in
deterministic distance, carrier-ID, and binding-ID order. Multiple routes remain multiple paths.

`reachable_occupancies_at` returns direct occupancy records together with the carrier path through
which each is reachable. An empty path is direct occupancy of the requested carrier; a nonempty
path is indirect reachability. The service never copies an indirect occupancy onto an ancestor or
selects one path as canonical.

## Ownership Boundaries

- Entity, incarnation, phase, persona, derivation, cloning, counterpart, and divergence identity
  remain identity-registry concerns.
- Redirect, merge, split, retirement, reclassification, and historical ID resolution remain
  reconciliation concerns.
- Concrete happenings, participation, track placement, and entry order remain occurrence concerns.
- Availability, memory, belief, capability, and other subject-state changes remain state concerns.
- Evidence, claims, applicability, source authority, and truth resolution remain provenance
  concerns.
- Hosting owns only carrier identity, bounded carrier topology, occupancy/control, and explicit
  carrier transitions.

The registry must never infer that a subject moved because two occupancies touch, that a copy is
the same identity because memories match, that a controller is the carrier, or that carrier loss
means identity death. Those conclusions require explicit records in their owning services.

## Loader And Conformance Contract

`Tools/Runtime/Python/knowledge_framework/hosting_config.py` and the manifest-backed PowerShell
`KnowledgeFramework` module are behaviorally paired. They enforce schema and closed-shape
ingestion, pack capability and vocabulary ownership, stable IDs, provider closure, exact boundary
membership, carrier/binding/occupancy interval containment, transition-kind rules, relationship
target resolution, semantic duplicate and cycle rejection, deterministic direct/transitive
queries, provenance targets,
reconciliation-provider shape, and bounded scale.

Portable fixtures live under `Framework/Data/Hosting/`. Run
`python Tools/Conformance/Suites/test_hosting.py` or
`powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Hosting.ps1`.
Add `--json` or `-Json` for matching structured summaries.
