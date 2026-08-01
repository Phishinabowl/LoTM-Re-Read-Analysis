# Occurrence, Recurrence, and State Registry Contract

## Ownership

`Project_Config/occurrences.yaml` instantiates occurrence identity, recurrence patterns and executions, phases and schedules, branch topology, subject tracks, transitions, causal relations, outcomes, recurrence rules, state transitions, and iteration carryover. `Tools/occurrence_config.py` and `Tools/Occurrence-Config.ps1` are the behaviorally paired schema-4 loaders and query services. V35 strengthens semantic integrity without changing the stored registry shape.

Chronology and occurrence identity remain separate. Chronology answers where or when something is positioned and preserves acyclic exact order. The occurrence registry answers which distinct happening, execution, iteration, branch, experienced step, or subject-state change a record represents. Several occurrences may bind one chronology position without becoming the same occurrence.

## Identity Layers

Every mapping key and list-row `id` is a stable kebab-case identifier.

- `branches` form an acyclic parent topology. A child names its parent and fork occurrence.
- `templates` identify repeatable occurrence roles; they are not concrete happenings.
- `recurrence_patterns` identify reusable cycle or retry structures.
- `recurrences` are concrete executions of one pattern. Executions may nest through acyclic parent recurrence links and have an explicit lifecycle status.
- `iterations` belong to one recurrence, have a unique positive ordinal, and may bind to a parent recurrence's iteration.
- `phases` name non-overlapping ordinal ranges within one concrete recurrence execution.
- `schedules` belong to reusable patterns and define either a civil-calendar cadence or coordinate-step cadence from a typed anchor.
- `occurrences` are concrete identities with a template, branch, optional iteration, and chronology bindings.
- `tracks` are ordered subject or process perspectives over occurrence IDs. For each recurrence represented directly on a track, iteration ordinals are monotonic; nested child-recurrence segments remain legal.

An occurrence binding has its own stable ID, chronology `position_id`, and role. Duplicate semantic bindings are invalid. Two primary bindings may be concurrent or incomparable, but they cannot be positions known to be ordered.

## Transitions And Causality

Transitions connect distinct occurrence identities without redefining chronology. Extensible `transition_kind` vocabulary selects a core `transition_profile` through a pack-registered kind/profile pair. Track-attached transitions advance in track order. An `ordered` profile additionally requires forward evidence from a track, recurrence ordinal, or exact chronology and rejects known backward chronology; backward movement uses `jump`.

Recurrence advance increases the iteration ordinal of one execution. Recurrence exit starts inside the named recurrence or a descendant and must target outside that entire containment tree. Branch fork and merge retain their explicit lineage rules. Semantic duplicate transitions and causal relations are invalid, while causal cycles remain legal because causal edges never enter chronology comparison.

## Outcomes And Rules

`outcomes` record typed results of concrete occurrences for exact subjects, with an optional stable result target. They state what happened; provenance states why the claim is trusted. Packs register canonical incompatible outcome pairs, allowing a domain to reject combinations such as one subject both dying and surviving one occurrence without imposing that policy universally.

`rules` belong to recurrence patterns. Pattern defaults may apply broadly; execution overrides must name concrete recurrences and may replace defaults in the same resolution group. Applicability may narrow a rule by concrete execution, phase, branch, positive iteration range, chronology-position window, and civil effective-time window. These selectors compose; an incomparable or uncertain selector is reported as indeterminate rather than guessed.

Conditions are independently evaluable. Occurrence outcomes name the subject; state availability names the subject, state kind, track, and evaluation boundary; ordinal conditions use a typed comparison and positive value; schedule conditions ask whether a typed cadence is due. Occurrence-reached remains the simple current-template predicate. Ordinal conditions must target their rule's recurrence pattern, and schedule conditions must target a schedule owned by that pattern. Rules retain bounded `all` or `any` logic and typed effects rather than accepting an unrestricted expression language.

Each rule has a nonnegative priority, stable resolution group, and `exclusive` or `accumulate` selection mode. Packs register compatible rule-kind/effect-kind pairs, and recurrence-control effects must target their owning pattern. Within a group, accumulating matches compose and the highest-priority exclusive match wins. Unequal top-priority effects, advance-plus-terminate combinations, and competing reset points produce an explicit conflict instead of arbitrary selection. Evaluation returns considered rules, applicability, each condition result, selected rules and effects, suppression or rejection reasons, and conflicts. Missing effective time required by an applicability window or civil schedule is indeterminate; a supplied time outside the applicable window is a definite non-match.

Schedules are intentionally narrow. `civil-calendar` schedules use day, week, month, or year intervals and an ISO anchor of matching precision. `chronology-step` schedules use integer coordinate steps from one chronology position and do not cross era-ordinal systems. They are recurrence-policy inputs, not replacements for chronology or release-time registries.

Recurrence lifecycle is coherent: at most one active or terminated iteration exists, either must have the highest ordinal, a terminated iteration requires a terminated execution, a terminated execution ends in a terminated iteration when iterations are present, and a completed execution cannot contain active or terminated iterations. Sparse observations remain legal.

## State Availability And Acquisition

`state_transitions` are reusable core records for what state changed for which subject and when. Each identifies:

- an exact subject and payload target;
- state kind, change kind, and structural change profile;
- acquisition or change mechanism;
- prior and resulting availability;
- optional prior and resulting epistemic attitude;
- completeness, activation occurrence, optional governing rule, subject tracks, source targets, and certainty.

Change profiles enforce broad invariants such as unavailable-to-available acquisition, equal-state preservation, removal into unavailable or inaccessible state, restoration, transfer, merge, derivation, activation, and invalidation. On one track, transitions for the same subject, payload, and state kind form a continuous chain: a later prior state must equal the earlier resulting state. Encountering an occurrence does not imply awareness, memory, belief, or access.

Provenance remains the sole owner of whether a state-change claim or payload is verified, inferred, disputed, or superseded. Epistemic attitude describes the subject's modeled stance, not objective truth.

## Carryover

Carryover no longer duplicates a state kind and payload. It references one concrete `state_transition_id` that already applies to the named track. The state must activate no later than the end of the source iteration, remain the applicable state until the target iteration begins, and cross increasing iterations of the same recurrence on a track participating in both. This distinguishes continuous retention from later restoration, transfer, reconstruction, or activation.

## Narrative Time Loops

The narrative-media pack adds time-loop patterns, subjective experience, loop reset and escape transitions, narrative outcomes and incompatibility policy, memory/knowledge/awareness/belief/physical state, and mechanisms such as recovered memory, dream, prophecy, revelation, supernatural bestowal, and timeline reconciliation. A loop remains distinct occurrences within iterations, never a chronology cycle.

The model can therefore separate the same external coordinate from successive subjective experiences; represent staggered awareness; state exactly when memory becomes available; retain it across selected boundaries; describe reset and termination rules; type different outcomes by pass; nest loops; and let one subject escape without granting that state or track to another.

## Queries

Paired services query iteration contents, coordinate reuse, iteration contents and boundaries on a track, ordinary track neighbors, recurrence identity and phase, expected schedule values and due status, incoming carryover, outcomes for an occurrence, rules for a recurrence pattern, state transitions for a subject, the latest applicable state at a track occurrence, and deterministic recurrence-rule evaluation with a trace. These answer both what happened and which bounded policy applies without introducing chronological cycles.

## Layering

- Core owns occurrence, pattern, execution, iteration, phase, schedule, branch, outcome, rule evaluation, same-pattern policy integrity, generic subject-state, carryover, validation, and queries.
- Domain packs extend kinds, mechanisms, outcomes, incompatibility pairs, and valid rule-kind/effect-kind or other typed combinations.
- Project configuration owns concrete records and source-backed claims.
- Chronology remains the sole owner of acyclic exact temporal comparison.
- Provenance remains the sole owner of evidence and claim authority.

The LoTM project declares only its `main` branch until source-backed occurrences are deliberately modeled.

## Conformance

`Framework/Data/Occurrence/` contains the portable V31-V35 corpus. Run `python Tools/test_occurrence.py` and `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Test-Occurrence.ps1` after changing occurrence vocabulary, registry shape, chronology composition, recurrence policy or lifecycle, schedules, state semantics, carryover, provenance targets, or query behavior.
