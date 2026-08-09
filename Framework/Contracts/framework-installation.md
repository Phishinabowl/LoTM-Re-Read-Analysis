# Framework Installation Contract

## Status And Purpose

This Phase 3.2.1 contract is implemented by paired runtime loaders, root discovery, conformance, and
framework-catalog commands.

`Framework/framework.yaml` is the project-independent bootstrap for an installed framework. It
selects the pack root, portable lookup registry, and capability roadmap without
reading `Project_Config/`, inferring configuration from filenames, or hardcoding one Unicode data
version in runtime code.

## Canonical Shape

The canonical version 2 manifest has this closed shape:

```yaml
schema_version: 2
framework_id: knowledge-model

paths:
  packs: Packs

registries:
  lookup_keys: Data/unicode-lookup-16.0.0.json
  capability_roadmap: capability-roadmap.yaml
```

- `schema_version` must be integer `1` or `2`; the canonical installation uses `2`.
- `framework_id` must be a lowercase kebab-case stable ID.
- `paths` must contain exactly `packs`.
- Version 2 `registries` must contain exactly `lookup_keys` and `capability_roadmap`. Version 1
  remains a legacy installation shape with only `lookup_keys`, and roadmap-aware services reject it.
- Paths must be nonempty, forward-slash relative paths confined beneath `Framework/`.
- Absolute paths, backslashes, empty segments, `.` or `..` segments, and resolved escapes fail.
- The selected pack root must exist as a directory.
- The selected lookup registry must exist and pass the lookup-key registry contract.
- The selected capability-roadmap registry must exist; its own loader validates roadmap semantics
  against the installed framework catalog.
- Unknown fields fail strict ingestion.

Multiple lookup datasets and roadmap-like files may coexist beneath `Framework/`. The manifest
selects exactly one of each; runtimes must never discover either authority by filename or directory
enumeration. In particular, runtimes must never search for `unicode-lookup-*.json` and choose by
filename or enumeration order.

## Framework Root Discovery

Paired framework commands resolve the installation root in this order:

1. an explicit framework-root argument;
2. `KNOWLEDGE_FRAMEWORK_ROOT` when no explicit root was supplied;
3. ancestors of the current working directory;
4. ancestors of the command or module location;
5. a deterministic root-discovery failure.

A candidate is a framework root only when it contains a valid `Framework/framework.yaml`. A `.git`
directory, `Project_Config/project.yaml`, or `Framework/Packs/` alone is not the marker. An explicit
but invalid root fails without falling through to another source. Discovery must not change the
process working directory, and structured output must not expose absolute machine paths.

## Project Boundary

This manifest describes framework installation defaults and locations. It does not select project
packs, activate capabilities, or replace `Project_Config/project.yaml`.

Project and framework manifests retain independent explicit lookup-registry pins. Catalog-backed
project composition requires those pins to resolve to the same file and requires the project
framework ID to equal the installed framework ID. Disagreement fails before pack selection. Runtime
code never substitutes the framework default for the project pin, copies one registry over another,
or changes project inheritance semantics.

## Conformance

Permanent paired coverage must include valid loading, strict shape failures, missing targets,
absolute and escaping paths, explicit-root precedence, environment and ancestor discovery,
multiple installed lookup datasets with one explicit selection, deterministic diagnostics, and
Python/PowerShell 7/Windows PowerShell 5.1 parity.
