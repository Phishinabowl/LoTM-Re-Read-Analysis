# Occurrence and Recurrence Registry Contract

## Ownership

`Project_Config/occurrences.yaml` instantiates occurrence identity, recurrence structure, branch topology, observation tracks, transitions, causal relations, and carryover. `Tools/occurrence_config.py` and `Tools/Occurrence-Config.ps1` are the behaviorally paired schema-2 loaders and query service.

Chronology and occurrence identity are separate. `Project_Config/chronology.yaml` answers where or when something is positioned and preserves an acyclic ordering relation. The occurrence registry answers which distinct happening, iteration, branch, or experienced step a record represents. Multiple occurrences may bind to one chronology position without becoming the same occurrence.

## Stable Records

Every mapping key and list-row `id` is a stable kebab-case identifier.

- `branches` form an acyclic parent topology. A non-root branch identifies its parent and may identify the occurrence at which it forked.
- `templates` describe repeatable occurrence roles such as an event, action, state, process step, or episode. A template is not itself a concrete occurrence.
- `recurrences` describe nested recurrence structures. Their parent topology is acyclic.
- `iterations` belong to one recurrence, have a unique positive ordinal within it, and may bind to one iteration of the parent recurrence.
- `occurrences` are concrete identities. They reference one template, one branch, an optional iteration, and zero or more chronology-position bindings.
- `tracks` are explicitly ordered participant, observer, or process perspectives over occurrence IDs. They do not alter chronology.

An occurrence binding has its own stable ID, chronology `position_id`, and role. The same chronology position may be reused by any number of distinct occurrences. One occurrence may carry multiple bindings when different coordinates contextualize the same happening. Duplicate semantic bindings are invalid. Two `primary` bindings may be concurrent or incomparable, but they cannot identify positions the chronology service knows are ordered.

## Transitions, Causality, and Carryover

Transitions connect occurrence identities without redefining chronological order. `transition_kind` is extensible domain vocabulary; `transition_profile` selects the core structural invariant. Packs register allowed kind/profile pairs in `occurrence.transition-kind-profile`, preventing a specialized kind from selecting a weaker or unrelated profile. Core profiles cover ordered continuation, jumps, recurrence advance, recurrence exit, branch fork, and branch merge. Every transition attached to a track must advance in that track's declared order even when world chronology moves backward.

Recurrence-advance profiles require endpoints in increasing iterations of the named recurrence. Recurrence-exit profiles require a source inside and a target outside that recurrence. A branch-fork profile must connect the named fork occurrence on the parent branch to an occurrence on the child branch. Every non-root branch has exactly one matching branch-fork transition. Branch-merge endpoints must belong to different branches. Semantic duplicate transitions are invalid.

Causal relations are a directed explanatory graph and may contain cycles. A causal cycle is never fed into chronology comparison, so time-travel causation cannot corrupt acyclic temporal ordering.

Carryover records state what crosses an iteration boundary for one track. Source and target iterations must belong to the same recurrence and advance in ordinal order, and the track must contain occurrences in both iterations. `payload_target_type` and `payload_target_id` identify the exact registry or externally supplied stable target being carried; the broad carryover kind alone is not a payload. Core kinds cover generic state and context; domain packs may specialize memory, knowledge, physical state, awareness, or other retained properties. Semantic duplicate carryover records are invalid, and carryover records remain provenance-addressable.

## Narrative Time Loops

The narrative-media pack adds `time-loop`, `subjective-experience`, `time-travel-jump`, `loop-reset`, `loop-escape`, and narrative carryover kinds. A loop is modeled as a recurrence with distinct occurrence records per iteration, never as a chronological cycle.

This permits all of the following at once:

- one world-time coordinate reused by several loop iterations;
- an acyclic external chronology;
- a participant track ordered as iteration 1, then iteration 2, then iteration 3;
- memory or state crossing reset boundaries;
- nested loops and branch-specific occurrences;
- an exit for one participant without asserting that every participant shares that track.

## Query Semantics

The paired services expose deterministic queries for occurrences in an iteration, occurrences bound to a chronology position, occurrences for one iteration in track order, the previous and next occurrence at an iteration boundary, ordinary track neighbors, carryover into an iteration, and the recurrence containing an occurrence. These queries answer both "what happened during iteration 7?" and "what did this participant experience immediately before iteration 7 began?" without introducing a chronological cycle.

## Layering

- Core owns occurrence/template identity, recurrence and iteration structure, branches, binding coherence, transition profiles, causal edges, tracks, payload-bearing carryover, validation, and queries.
- Domain packs own specialized kinds and semantics such as narrative time loops and subjective experience.
- Project configuration owns instantiated branches, loops, iterations, occurrences, and source-backed claims.
- Chronology remains the sole owner of acyclic temporal comparison.

The LoTM project initially declares only its `main` branch. No loop or occurrence records are fabricated merely to activate the capability.

## Conformance

`Framework/Data/Occurrence/` contains the portable V31-V32 fixture corpus. Run `python Tools/test_occurrence.py` and `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Test-Occurrence.ps1` after changing occurrence vocabulary, registry shape, chronology composition, recurrence validation, transition profiles, carryover payloads, or query behavior.
