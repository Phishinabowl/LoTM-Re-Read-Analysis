# Structural Interpretation Registry

## Purpose

`Project_Config/interpretations.yaml` represents named candidate structures without converting a hypothesis into canonical chronology, continuity, branch identity, evidence, authority, or fact. The paired Python and PowerShell loaders own strict schema validation, target resolution, interpretation-local relationship integrity, comparison-set queries, and provenance-addressable record identity.

The registry is domain-neutral. Narrative reconstructions, incident hypotheses, differential diagnoses, legal or investigative theories, and scientific causal models use the same structural boundary while packs retain their own relation vocabulary.

## Ownership Boundary

An interpretation owns only:

- stable identity and lifecycle for one candidate structure;
- typed membership references to canonical records or provenance claims;
- candidate relations among members inside that interpretation; and
- sets declaring interpretations compatible, competing, or mutually exclusive.

Canonical registries continue to own the referenced records. Chronology owns canonical temporal comparison and closure. Occurrence owns concrete happenings and causality. Entity and reconciliation services own identity. Provenance owns evidence, source priority, authority, applicability, supersession, and factual assertions. Interpretation membership or relation presence never establishes truth and never mutates a referenced record.

## Registry Shape

Schema 1 contains:

- `relation_types`: project definitions for pack-allowed interpretation relation IDs;
- `interpretations`: stable candidate-structure records;
- `members`: stable typed references belonging to exactly one interpretation;
- `relations`: interpretation-local edges between member IDs; and
- `comparison_sets`: groups of two or more interpretations with one comparison mode.

Every mapping key and row `id` is a lowercase kebab-case stable ID. Unknown fields, duplicate IDs, missing references, duplicate semantic records, invalid inverse definitions, and prohibited cycles fail closed.

### Relation Types

A relation type declares `label`, `inverse_type`, `symmetric`, `canonical_direction`, and optional `acyclic_group`. Its ID must be supplied by the composed `interpretation.relation-type` controlled-value namespace. Inverse definitions must be reciprocal. Symmetric types must name themselves as inverse, cannot claim canonical direction, and cannot enter an acyclic group. Non-symmetric inverse pairs must agree on acyclic-group ownership and define exactly one canonical direction.

The type definition controls storage shape only. It does not promote an interpretation-local `precedes`, `causes`, `corresponds-with`, or `equivalent-with` relation into chronology, occurrence causality, adaptation mapping, reconciliation, or any other canonical service.

### Interpretations

An interpretation contains `lifecycle`, `label`, and optional `description`. Lifecycle uses the pack-controlled `interpretation.lifecycle` namespace. `active` and `retired` describe record availability, not acceptance or rejection of the hypothesis.

### Members

A member contains `id`, `interpretation_id`, `target_type`, and `target_id`. Within one interpretation, one typed target may appear only once. Supported targets come from installed provenance-target providers plus `provenance-claim`.

Canonical target IDs resolve through installed providers while the interpretation registry loads. That includes exact `chronology-position` records when an interpretation needs to reuse a canonical coordinate without changing canonical chronology. Claim IDs are deferred because provenance also consumes interpretation records as subjects. Project composition must load the structural registry, load provenance with structural interpretation targets available, then validate every deferred `provenance-claim` member against the completed provenance claim-key inventory. No other unresolved target is legal.

Interpretations cannot contain themselves, another interpretation, or another interpretation's member, relation, or comparison set in schema 1. This prevents recursive hypothesis graphs and keeps the dependency boundary acyclic.

### Relations

A relation contains `id`, `interpretation_id`, `source_member_id`, `relationship_type`, and `target_member_id`. Both endpoint members must belong to the named interpretation. Self-relations and duplicate canonical or inverse shapes are invalid.

Relations in the same non-null `acyclic_group` must remain acyclic inside each interpretation. Cycles in one candidate structure never weaken canonical chronology validation; they fail only that interpretation registry. Relation traversal and cycle checks never cross interpretation identity.

### Comparison Sets

A comparison set contains `label`, `comparison_mode`, and at least two unique `interpretation_ids`. Comparison mode uses `interpretation.comparison-mode`:

- `compatible`: the structures may coexist;
- `competing`: the structures offer different explanations without asserting logical exclusivity; and
- `mutually-exclusive`: no more than one structure may ultimately be selected.

The structural registry never selects a winner. Its deterministic decision query reports all members and returns `compatible` for a compatible set or `unresolved` for competing and mutually exclusive sets. Provenance claims may target the set or its interpretations and existing authority services may compare those claims, but structural membership cannot manufacture evidence or an accepted result.

## Query Contract

Paired runtimes expose deterministic queries for:

- members and relations belonging to one interpretation;
- comparison sets containing one interpretation;
- one interpretation's complete local structure;
- one comparison set's conservative decision; and
- exact provenance-target lookup.

Unknown IDs fail explicitly. List-backed member and relation queries preserve registry order; mapping-backed comparison-set queries sort by stable ID and never depend on display labels or hash-map iteration.

## Provenance And Composition

`structural-interpretation`, `structural-interpretation-member`, `structural-interpretation-relation`, and `structural-interpretation-set` are provenance subject types. Claim namespace `structural-interpretation` may describe support, contradiction, comparison, or a proposed resolution without changing the structural records themselves.

Project composition must reject provenance-provider collisions, unresolved claim members, target-type mismatches, or an interpretation claim that names a nonexistent record. The LoTM project may keep the registry structurally empty until a source-grounded competing reconstruction is intentionally modeled.

## Explicit Exclusions

Schema 1 does not provide probabilistic ranking, Bayesian inference, automatic hypothesis generation, nested interpretations, arbitrary expression evaluation, canonical graph mutation, repository migration, reconciliation of interpretation IDs, or a gold-layer truth resolver. It does not infer that a source-backed interpretation is correct, that a rejected claim deletes a candidate, or that mutually exclusive candidates must have a winner.

## Conformance

`Framework/Data/Interpretations/` owns portable positive, malformed, decision, and integration fixtures. The paired `interpretation` conformance suite validates schema, relationship shape, local acyclicity, target resolution, deferred claim validation, conservative comparison decisions, provenance targeting, and Python/PowerShell summary parity. Project composition additionally proves that interpretations can reference canonical providers and claims without creating a loader cycle or changing canonical chronology closure.
