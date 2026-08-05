# Occurrence, Recurrence, and State Registry Contract

## Ownership

`Project_Config/occurrences.yaml` instantiates occurrence identity, occurrence participation, subjective track entries, recurrence patterns and executions, aggregate recurrence cardinality, phases and schedules, branch topology and lifecycle, subject tracks, transitions, causal relations, outcomes, recurrence rules, state scales, state transitions, and iteration carryover. `Tools/Runtime/Python/knowledge_framework/occurrence_config.py` and `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` are the behaviorally paired schema-9 loaders and query services. V40 separates one concrete happening from each subject's participation in it and from each participation's ordered placement on a track. V42 adds provenance-addressable branch-state histories without converting branch lifecycle into chronology. V43 adds pack-composed epistemic state profiles without treating subject knowledge or belief as objective truth. V44 adds local capability scales without treating credentials, assessments, or elapsed time as demonstrated competence.

Chronology and occurrence identity remain separate. Chronology answers where or when something is positioned and preserves acyclic exact order. The occurrence registry answers which distinct happening, execution, iteration, branch, experienced step, or subject-state change a record represents. Several occurrences may bind one chronology position without becoming the same occurrence.

## Identity Layers

Every mapping key and list-row `id` is a stable kebab-case identifier.

- `branches` form an acyclic parent topology. A child names its parent and fork occurrence, and may declare continuity memberships resolved during project composition.
- `branch_state_transitions` form a contiguous branch-local lifecycle history. Each record names its prior and resulting state, activation occurrence, and optional occurrence transition that caused the change.
- `templates` identify repeatable occurrence roles; they are not concrete happenings.
- `recurrence_patterns` identify reusable cycle or retry structures.
- `recurrences` are concrete executions of one pattern. Executions may nest through acyclic parent recurrence links and have an explicit lifecycle status.
- `iterations` belong to one recurrence, have a unique positive ordinal, and may bind to a parent recurrence's iteration.
- `phases` name non-overlapping ordinal ranges within one concrete recurrence execution.
- `schedules` belong to reusable patterns and define either a civil-calendar cadence or coordinate-step cadence from a typed anchor.
- `occurrences` are concrete identities with a template, branch, optional iteration, and chronology bindings.
- `occurrence_participations` give one subject's involvement in one occurrence a stable identity, role, perspective, status, and optional chronology-context reference.
- `tracks` identify ordered subject or process perspectives without embedding occurrence identity.
- `track_entries` place one participation on one matching-subject track at a unique contiguous positive ordinal. For each recurrence represented directly on a track, iteration ordinals are monotonic; nested child-recurrence segments and repeated occurrences through distinct participations remain legal.

An occurrence binding has its own stable ID, chronology `position_id`, and role. Duplicate semantic bindings are invalid. Two primary bindings may be concurrent or incomparable, but they cannot be positions known to be ordered.

## Participation And Subjective Order

Occurrence, participation, and track-entry identity are independent. One occurrence remains one concrete happening even when the same subject encounters it repeatedly. Each involvement uses a distinct participation. Role, perspective, status, or chronology-context references may distinguish those participations directly. Semantically identical participations are also legal when every record shares a subject-matching track that orders the encounters; identical records without a common ordering track are rejected as unexplained duplication.

A participation may reference an already registered chronology context. The chronology registry owns typed context topology, extratemporal oversight, and cross-context intervention; occurrence participation only consumes those context identities. Participation references and context relations do not imply chronological comparability and never add chronology edges.

Track entries provide subjective or process order. Their ordinals are unique and contiguous within a track; the participation subject must equal the track subject, and one participation can appear only once on one track. Two entries may resolve to the same occurrence when they name distinct participations. Entry-relative navigation remains deterministic in that case. Occurrence-relative navigation remains a convenience for unique occurrences and fails explicitly when the occurrence appears more than once, preventing consumers from silently choosing the wrong subjective visit.

Participation status describes involvement lifecycle, not subject knowledge or objective truth. State availability and acquisition remain `state_transitions`; evidence and authority remain provenance. Both `occurrence-participation` and `occurrence-track-entry` are stable provenance subjects.

## Aggregate Cardinality

`recurrence_cardinalities` describe the realized iteration count of one concrete recurrence without requiring every iteration to be materialized. A record has one typed shape: `exact`, `minimum`, `maximum`, `range`, or `unknown`. Canonical `minimum_count` and `maximum_count` bounds must match that shape, use nonnegative signed 64-bit integers, and never imply an inverted range.

Coverage is independent from the numeric claim. `complete` means the representative list enumerates the exact history, including a valid exact-zero empty history. `representative` names a nonempty subset of same-recurrence iteration IDs; the known subset may exceed a stated lower bound but cannot exceed a stated upper bound. `unmaterialized` names no concrete iterations. A fully enumerated exact list must use `complete`; sparse or selective observations must not masquerade as exhaustive history. Multiple nonduplicate cardinality records may coexist so provenance can resolve source-specific or superseding claims rather than forcing the occurrence loader to choose authority.

Cardinality records describe realized history only. They do not describe expected, permitted, configured, or scheduled future repetitions and never invent missing occurrence identities or iteration ordinals. Their `certainty` is a modeled qualifier; evidence, factual status, source priority, reader/source applicability, and supersession remain provenance-owned through the stable `recurrence-cardinality` target.

## Transitions And Causality

Transitions connect distinct occurrence identities without redefining chronology. Extensible `transition_kind` vocabulary selects a core `transition_profile` through a pack-registered kind/profile pair. Track-attached transitions advance in track order. An `ordered` profile additionally requires forward evidence from a track, recurrence ordinal, or exact chronology and rejects known backward chronology; backward movement uses `jump`.

Recurrence advance increases the iteration ordinal of one execution. Recurrence exit starts inside the named recurrence or a descendant and must target outside that entire containment tree. Branch fork and merge retain their explicit lineage rules. Semantic duplicate transitions and causal relations are invalid, while causal cycles remain legal because causal edges never enter chronology comparison.

## Branch Lifecycle

A branch is never deleted merely because it becomes inactive, pruned, merged, transferred, or otherwise unavailable in a domain-specific sense. `branch_state_transitions` preserve those changes as append-only, provenance-addressable records. Their positive ordinals are unique and contiguous within one branch. The first transition has no prior state; every later transition must continue from the preceding resulting state.

Every lifecycle transition names an activation occurrence. An optional trigger transition must include that occurrence as one endpoint and must involve the affected branch. The first lifecycle transition of a child branch must reference the branch-fork transition that created it. Merge lifecycle changes similarly require a branch-merge trigger. This keeps branch identity, occurrence identity, and transition causality separate while rejecting lifecycle claims that cannot be connected to the branch topology.

Core owns generic states and changes such as emerging, active, inactive, transferred, restored, merged, preserved, initialize, activate, deactivate, transfer, restore, merge, and preserve. Packs may add domain vocabulary. For example, narrative-media owns `pruned` and `prune`; core does not assume that every domain can prune a branch. Change kinds do not hard-code one universal state pair: each record carries explicit prior and resulting states so pack-defined semantics remain inspectable and provenance-backed.

Branch lifecycle ordinals are local sequence coordinates, not chronology positions or reader boundaries. A boundary of zero means before the first recorded lifecycle state, an omitted boundary selects the latest state, and a positive boundary selects the latest transition at or before that branch-local ordinal. Chronology owns temporal comparison. Provenance owns evidence, authority, supersession, and source or reader applicability for every lifecycle claim.

## Outcomes And Rules

`outcomes` record typed results of concrete occurrences for exact subjects, with an optional stable result target. They state what happened; provenance states why the claim is trusted. Packs register canonical incompatible outcome pairs, allowing a domain to reject combinations such as one subject both dying and surviving one occurrence without imposing that policy universally.

`rules` belong to recurrence patterns. Pattern defaults may apply broadly; execution overrides must name concrete recurrences and may replace defaults in the same resolution group. Applicability may narrow a rule by concrete execution, phase, branch, positive iteration range, chronology-position window, and civil effective-time window. These selectors compose; an incomparable or uncertain selector is reported as indeterminate rather than guessed.

Conditions are independently evaluable. Occurrence outcomes name the subject; state availability names the subject, state kind, track, and evaluation boundary; ordinal conditions use a typed comparison and positive value; schedule conditions ask whether a typed cadence is due. Occurrence-reached remains the simple current-template predicate. Ordinal conditions must target their rule's recurrence pattern, and schedule conditions must target a schedule owned by that pattern. Rules retain bounded `all` or `any` logic and typed effects rather than accepting an unrestricted expression language.

Each rule has a nonnegative priority, stable resolution group, and `exclusive` or `accumulate` selection mode. Packs register typed rule-kind/effect-kind and effect-kind/target-type compatibility records. Every effect targeting a recurrence pattern has exactly one typed scope: `owning-pattern` or `external-pattern`. Every effect kind also declares exactly one repetition policy: `idempotent`, `accumulating`, or `invalid`. Duplicate semantic conditions or effects inside one rule are invalid even when their nested IDs differ. Pack composition validates every typed member reference, complete profile/policy ownership, recurrence scope, distinct incompatibility members, one conflict scope, duplicate providers, and empty-vocabulary orphans. It never recovers semantic members by splitting stable IDs.

Within a group, accumulating rule matches compose and the highest-priority exclusive match wins. Selected raw effects are grouped by effect kind and target. A proposed effect retains its repetition policy, contribution count, proposed execution count, contributing rule IDs, and contributing nested effect IDs. Idempotent contributions propose one execution, accumulating contributions propose one per contribution, and repeated invalid contributions propose zero plus a conflict. Incompatibility pairs are either `global` or `same-target`; same-target comparison includes target type and ID. Unequal top-priority effects, scoped incompatible effects, invalid repetition, and competing reset points produce explicit conflicts instead of arbitrary selection.

Evaluation returns `proposed_effects`, `authorized_effects`, and an explicit `execution_disposition` alongside selected rules, traces, and conflicts. Only a conflict-free `selected` evaluation is `authorized`. Any conflict is `blocked-conflict`, any indeterminate result is `blocked-indeterminate`, and no match is `not-applicable`; all three expose no authorized effects while preserving diagnostic proposals where available. Authorization is conflict-wide. Partial execution, compensation, transactions, and effect payload execution are not inferred. Missing effective time required by an applicability window or civil schedule is indeterminate; a supplied time outside the applicable window is a definite non-match. An indeterminate applicability selector may be eliminated only when the rule's independently evaluated conditions prove that it cannot match. Otherwise the unresolved rule remains indeterminate and blocks authorization even when another rule has already produced a proposal.

Schedules are intentionally narrow. `civil-calendar` schedules use day, week, month, or year intervals and an ISO anchor of matching precision. Their projections are limited to civil years `0001` through `9999`; crossing either boundary raises the same controlled error in every runtime. `chronology-step` schedules use unbounded integer coordinate steps from one chronology position and do not cross era-ordinal systems. They are recurrence-policy inputs, not replacements for chronology or release-time registries.

Recurrence lifecycle is coherent: at most one active or terminated iteration exists, either must have the highest ordinal, a terminated iteration requires a terminated execution, a terminated execution ends in a terminated iteration when iterations are present, and a completed execution cannot contain active or terminated iterations. Sparse observations remain legal.

## State Availability And Acquisition

`state_transitions` are reusable core records for what state changed for which subject and when. Each identifies:

- an exact subject and payload target;
- state kind, change kind, and structural change profile;
- discrete, gradual, aggregate, or unknown change shape independently from acquisition or change mechanism;
- prior and resulting availability;
- profile-required, optional, or forbidden prior and resulting completeness;
- profile-required, optional, or forbidden prior and resulting epistemic attitude;
- profile-required, optional, or forbidden prior and resulting capability values;
- activation occurrence, optional governing rule, subject tracks, source targets, and certainty.

Core pack semantic declarations define typed state profiles. Each profile declares whether availability, completeness, attitude, and capability are required, optional, or forbidden; availability remains mandatory for every current profile. Packs map every controlled state kind to exactly one profile. `epistemic-access` requires availability and completeness, `epistemic-belief` requires availability and attitude, `capability-state` requires availability and capability, and `availability-state` requires only availability. Every other dimension is forbidden in those profiles. An unmapped state kind, unknown profile, or profile-incompatible dimension is invalid. A reusable profile may remain dormant when no selected domain pack contributes a kind that uses it.

Change profiles enforce broad invariants such as unavailable-to-available acquisition, equal-state preservation, improvement, degradation, removal into unavailable or inaccessible state, restoration, transfer, merge, derivation, activation, and invalidation. On one track, transitions for the same subject, payload, and state kind form a continuous chain: every later prior dimension must equal the earlier resulting value. Encountering an occurrence does not imply awareness, memory, belief, access, or competence. Change shape describes how progression occurs; mechanism describes what caused it. Neither is inferred from elapsed time, repeated participation, successful outcomes, or assessment records.

## Capability And Proficiency

`state_scales` give capability values a local interpretation. A `qualitative` scale owns stable level IDs with unique contiguous ordinals beginning at zero. A `bounded-integer` scale owns an inclusive signed-64-bit minimum and maximum plus a stable unit ID. Decimal values, implicit percentages, cross-scale conversion, and a universal competence scale are unavailable. A transition's prior and resulting capability must use one known scale and values legal for that scale.

`capability`, `skill`, `proficiency`, `competence`, and `expertise` use `capability-state`. `improve`, `degrade`, and `preserve` enforce increasing, decreasing, or unchanged local rank respectively. Acquisition, transfer, loss, and restoration retain their explicit availability semantics and values rather than being inferred from practice count or time elapsed. Practice and training are mechanisms; discrete, gradual, aggregate, and unknown remain independent change shapes.

`credential`, `qualification`, `license`, and `authorization` use `availability-state` and therefore forbid capability values. An assessment may be provenance evidence for a bounded capability claim, but the occurrence loader never promotes an assessment, credential, successful action, or accumulated duration into competence. State scales and transitions are provenance-addressable, including nested capability value field paths.

Provenance remains the sole owner of whether a state-change claim or payload is verified, inferred, disputed, or superseded. Epistemic attitude describes the subject's modeled stance, not objective truth.

## Carryover

Carryover no longer duplicates a state kind and payload. It references one concrete `state_transition_id` that already applies to the named track. The state must activate no later than the end of the source iteration, remain the applicable state until the target iteration begins, and cross increasing iterations of the same recurrence on a track participating in both. This distinguishes continuous retention from later restoration, transfer, reconstruction, or activation.

## Narrative Time Loops

The narrative-media pack adds time-loop patterns, subjective experience, loop reset and escape transitions, narrative outcomes and incompatibility policy, memory/knowledge/awareness/belief/physical state, and mechanisms such as recovered memory, merged memory, dream, prophecy, revelation, supernatural bestowal, and timeline reconciliation. Memory, knowledge, and awareness use `epistemic-access`; belief uses `epistemic-belief`; physical state is the non-epistemic `availability-state` control. A loop remains distinct occurrences within iterations, never a chronology cycle.

The model can therefore separate the same external coordinate from successive subjective experiences; represent staggered awareness; state exactly when memory becomes available; retain it across selected boundaries; describe reset and termination rules; type different outcomes by pass; nest loops; and let one subject escape without granting that state or track to another.

## Queries

Paired services query branch-state history and state at a branch-local lifecycle ordinal, iteration contents, recurrence cardinality claims, coordinate reuse, participations by occurrence or subject, track entries by occurrence, entry-relative neighbors, unambiguous occurrence-relative neighbors, iteration contents and boundaries on a track, recurrence identity and phase, expected schedule values and due status, incoming carryover, outcomes for an occurrence, rules for a recurrence pattern, state transitions for a subject, the latest applicable state at an unambiguous track occurrence, and deterministic recurrence-rule evaluation with a trace. These answer both what happened and which bounded policy applies without introducing chronological cycles.

## Layering

- Core owns occurrence, participation, track-entry ordering, pattern, execution, aggregate realized-history cardinality, iteration, phase, schedule, branch identity and generic lifecycle, outcome, rule evaluation, semantic declaration validation, deterministic effect resolution, civil schedule boundaries, generic subject-state profiles and continuity, carryover, validation, and queries.
- Domain packs extend branch states and changes, state kinds and their required profile mappings, mechanisms, outcomes, valid rule-kind/effect-kind combinations, recurrence-pattern effect scopes, repetition policy, and globally or same-target incompatible effect-kind pairs.
- Project configuration owns concrete records and source-backed claims.
- Chronology remains the sole owner of acyclic exact temporal comparison.
- Provenance remains the sole owner of evidence and claim authority.

The LoTM project declares only its `main` branch until source-backed occurrences are deliberately modeled.

## Conformance

`Framework/Data/Occurrence/` contains the portable V31-V44 corpus. Its fixture and generated probes cover branch lifecycle and continuity closure, role-distinct and semantically identical ordered repeated participation, subjective track-entry identity and ambiguity rejection, chronology-context references, cardinality shapes and coverage modes, signed 64-bit boundaries, representative and complete histories, typed epistemic and capability profiles, local qualitative and bounded-integer scales, dimension chains, malformed combinations, 128-record scale, typed rule/effect extensions, scoped conflicts, repetition behavior, contributor diagnostics, and fail-closed authorization. Run `python Tools/Conformance/Suites/test_occurrence.py` and `powershell -NoProfile -ExecutionPolicy Bypass -File Tools/Conformance/Suites/Test-Occurrence.ps1` after changing branch identity or lifecycle, occurrence vocabulary, participation, track-entry ordering, registry shape, chronology composition, recurrence cardinality, recurrence policy or lifecycle, schedules, state scales, state profiles or semantics, carryover, provenance targets, or query behavior.
