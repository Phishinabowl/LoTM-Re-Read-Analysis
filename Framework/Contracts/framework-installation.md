# Framework Installation Contract

## Status And Purpose

This Phase 3.2.1 contract is implemented by paired runtime loaders, root discovery, conformance, and
framework-catalog commands.

`Framework/framework.yaml` is the project-independent bootstrap for an installed framework. It
selects the pack root and portable lookup registry needed to construct `FrameworkCatalog` without
reading `Project_Config/`, inferring configuration from filenames, or hardcoding one Unicode data
version in runtime code.

## Canonical Shape

The version 1 manifest has this closed shape:

```yaml
schema_version: 1
framework_id: knowledge-model

paths:
  packs: Packs

registries:
  lookup_keys: Data/unicode-lookup-16.0.0.json
```

- `schema_version` must be integer `1`.
- `framework_id` must be a lowercase kebab-case stable ID.
- `paths` must contain exactly `packs`.
- `registries` must contain exactly `lookup_keys`.
- Paths must be nonempty, forward-slash relative paths confined beneath `Framework/`.
- Absolute paths, backslashes, empty segments, `.` or `..` segments, and resolved escapes fail.
- The selected pack root must exist as a directory.
- The selected lookup registry must exist and pass the lookup-key registry contract.
- Unknown fields fail strict ingestion.

Multiple lookup datasets may coexist beneath `Framework/Data/`. The manifest selects exactly one;
runtimes must never search for `unicode-lookup-*.json` and choose by filename or enumeration order.

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

During Phase 3.2.1, existing project lookup-registry selection remains unchanged. Phase 3.2.2 must
explicitly define and test how a project's pinned lookup registry is reconciled with the framework
default. Runtime code must not silently substitute the framework default for a project selection or
change project inheritance semantics.

## Conformance

Permanent paired coverage must include valid loading, strict shape failures, missing targets,
absolute and escaping paths, explicit-root precedence, environment and ancestor discovery,
multiple installed lookup datasets with one explicit selection, deterministic diagnostics, and
Python/PowerShell 7/Windows PowerShell 5.1 parity.
