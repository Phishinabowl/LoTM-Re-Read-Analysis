# Declarative Schema-Pack Contract

## Status And Purpose

This contract defines the Phase 3.3.1 safety and ownership boundary for schema packs. A schema pack
is a versioned, data-only extension unit interpreted by trusted framework runtimes. Product and
interface surfaces may describe a pack as a plugin, but its canonical contract identity remains
`schema-pack` so it cannot be confused with an executable extension.

The existing closed schema-pack shape is the executable enforcement boundary. Canonical
`pack.yaml` files may declare portable schema semantics; they cannot supply code, obtain authority,
or change how the loader executes.

## Declarative Authority

A schema pack may author only fields accepted by its supported schema version. Those fields own:

- stable pack identity, schema version, independent pack version, and lifecycle;
- compatibility kind, architectural classification, and human-facing presentation;
- hard pack dependencies expressed by stable pack ID and minimum pack version;
- capability declarations, lifecycle, presentation, groups, and typed relationships;
- controlled-value namespaces and their ownership or hierarchy; and
- supported typed semantic declarations interpreted by the framework runtime.

The pack describes what schema and runtime-backed capabilities are available. It does not contain
the implementation of those capabilities. Trusted framework code remains the execution authority.
A vocabulary-only pack may declare no capabilities without changing this boundary.

Capability lifecycle meanings and transitions follow `capability-lifecycle-and-roadmap.md`.
Delivery phases, accepted deferrals, platform prerequisites, and implementation evidence belong to
the separate framework-level roadmap boundary and must not be added to `pack.yaml`.

Canonical pack identity and semantics are independent of installation source, commercial offering,
customer entitlement, product tier, and project selection. `pack_version` identifies the authored
pack release used for compatibility checks; it is not a SKU, subscription, license tier, or grant.

## Prohibited Executable And Host State

A schema pack must not declare or embed:

- executable entrypoints, scripts, shell commands, or install/update/removal hooks;
- arbitrary language imports, dynamic modules, executable package dependencies, or runtime loading
  instructions;
- filesystem, process, network, environment, secret-store, or other host permissions;
- credentials, tokens, account or tenant identity, or external-service authentication;
- publisher trust, code-signing, sandbox, or executable-extension policy; or
- commercial offerings, SKUs, prices, subscriptions, entitlements, or customer grants.

Unknown fields fail strict ingestion at every closed mapping. A capability declaration cannot add
an `implementation` field, and a pack dependency cannot add an executable package or command. The
loader must not ignore, preserve, or forward such fields for a later consumer.

An HTTPS documentation target remains inert presentation metadata. It does not grant network
permission, require the loader to fetch content, or turn documentation into executable input.

## Loading And Side Effects

Loading a schema pack may read the selected local canonical file and validate it through trusted
runtime services. Pack-controlled values must never cause the loader to:

- execute a process or evaluate code;
- import a module selected by the pack;
- access the network;
- read credentials or host identity;
- install another package; or
- mutate canonical project, pack, or framework files.

Catalog and effective-schema composition remain deterministic functions of validated local
configuration. Generated catalog, project-view, and effective-schema documents remain diagnostic
views and never become executable manifests.

## Commercial Offering Separation

A future commercial offering may grant access to one or more packs, and one pack may appear in more
than one offering. Those many-to-many mappings belong to a host or distribution service outside
portable pack and project configuration. Entitlement may eventually govern offering discovery,
acquisition, installation, or update, but it cannot rewrite an installed pack's declarations,
satisfy technical dependencies, select the pack for a project, or activate its capabilities.

With no entitlement provider configured, valid locally installed declarative packs retain their
current deterministic and offline behavior. Phase 3.3.3 defines the fuller boundary in
`distribution-entitlement-boundary.md`; Phase 14.3 owns eventual add-on operations.

## Executable Extension Separation

Any future executable extension follows `trusted-executable-extension.md` and requires a separate
reviewed contract with its own manifest, registry, identity, compatibility, trust, permission, and
lifecycle rules. A schema-pack manifest cannot double as that executable manifest or reference code
that a runtime silently loads.

A future trusted extension may implement a capability declared through portable schema contracts,
but that relationship must not move capability identity, pack composition, or project data into
executable code. Phase 3.3.2 defines this boundary without implementing an extension host.

## Conformance Requirements

Paired schema-pack conformance must prove:

- supported declarative packs retain current composition behavior;
- executable entrypoint, script, command, hook, import, permission, credential, runtime-dependency,
  commercial-offering, and entitlement fields fail closed;
- executable additions to dependency and capability mappings fail closed;
- malformed rejection is equivalent in Python, PowerShell 7, and Windows PowerShell 5.1; and
- the added safety vectors do not change canonical pack, catalog, effective-schema, QA,
  Visualization, or extraction outputs.
