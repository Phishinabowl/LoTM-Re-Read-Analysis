# Trusted Executable-Extension Boundary

## Status And Purpose

This contract defines the Phase 3.3.2 architectural boundary for any future executable extension.
It does not define an executable manifest schema, extension registry schema, package format, loader,
host API, trust store, signature verifier, sandbox, permission engine, or extension marketplace.
Those runtime concerns remain deferred to the reviewed executable-extension host phase.

An executable extension is not a schema pack. It is a separately identified, host-managed software
unit that may eventually provide a runtime implementation for a capability already declared by a
selected declarative schema pack. Product interfaces may call both packs and executable extensions
plugins, but their canonical contracts, authorities, state, and risk boundaries remain distinct.

## Separate Identities And Artifacts

A future executable-extension system requires at least these separate objects:

- an extension package containing code and a dedicated executable-extension manifest;
- a stable extension identity and independently versioned software release;
- a host-local installation record that never becomes portable project configuration;
- an explicit binding from the extension release to capability IDs declared by schema packs;
- publisher and signature evidence evaluated by a trust service;
- requested permissions evaluated by host policy; and
- runtime status and diagnostics owned by the extension host.

The executable-extension manifest must use a distinct document kind and schema from `pack.yaml`.
An extension ID is not a pack ID, capability ID, offering ID, product SKU, publisher ID, or project
ID. Matching labels, folders, publishers, or distribution packages never merge those identities.

Package metadata may be portable with the extension artifact. Installed location, verification
result, trust decision, permission grants, loaded state, failures, quarantine, and revocation are
host-local operational state and must not be written into a schema pack or portable project.

## Authority Matrix

| Concern | Authority |
| --- | --- |
| Capability identity, lifecycle, presentation, groups, relationships, and portable semantics | Declarative schema packs |
| Pack dependencies and controlled-value composition | Declarative schema packs plus project selection |
| Capability activation for one project | Project configuration |
| Built-in capability implementation | Trusted framework runtime |
| Future third-party implementation candidate | Executable-extension manifest and package |
| Installed extension inventory and active software version | Future host-local extension registry |
| Publisher/signature evidence and trust decision | Future trust service and host policy |
| Requested and granted runtime permissions | Future permission policy |
| Commercial discovery, acquisition, and entitlement | Future distribution and entitlement service |
| Project facts and canonical content | Project registries and content stores |

No lower row may rewrite the authority of a higher row. In particular, an extension cannot declare
a new capability, change a capability lifecycle, contribute controlled values, satisfy a pack
dependency, select a pack, activate a capability, or mutate project facts merely because it is
installed, trusted, permitted, loaded, purchased, or entitled.

## Capability-Implementation Binding

A future extension may advertise an implementation only for a stable capability ID already
declared through the installed framework catalog. The host may consider that binding only when:

- the declaring schema pack is selected by the project;
- the capability is available and enabled under existing composition rules;
- the extension release is compatible with the current framework and host API;
- package integrity, publisher evidence, and host trust policy are satisfied;
- every required permission is explicitly granted; and
- implementation selection reports no unresolved conflict.

These conditions do not redefine schema-pack lifecycle. `available` continues to mean the selected
portable contract has a supported runtime-backed capability; it must not be overloaded to mean
installed, entitled, trusted, permitted, loaded, or currently healthy. A future host may expose a
separate implementation-readiness diagnostic, but it must not silently change `FrameworkCatalog`
or `EffectiveProjectSchema` records.

Multiple implementation candidates, provider preference, fallback to built-in behavior, version
resolution, process isolation, failure recovery, and hot replacement remain deferred. Until those
policies exist, trusted framework code remains the only implementation authority.

## Trust, Permissions, And Entitlement

Trust, permissions, and entitlement answer different questions:

- a valid signature proves package integrity and signer continuity, not that the publisher is
  trusted;
- a trusted publisher does not grant filesystem, process, network, credential, or secret access;
- an entitlement may permit acquisition, but it does not establish integrity, trust, compatibility,
  installation, permission, activation, or execution; and
- installation does not imply that an extension is enabled, loaded, or authorized for a project.

Future permissions must be explicit, least-privilege, deny-by-default, inspectable before execution,
and evaluated by the host rather than by schema packs or project facts. Future trust and signing
must define publisher identity, signature verification, trust roots, revocation, update continuity,
and failure behavior before any extension code can load.

Entitlement remains optional and external. A local trusted extension must not require commercial
identity merely because a future distribution service can sell or distribute extensions.

## Loading And Mutation Boundary

Phase 3.3.2 authorizes no extension loading. No current command, catalog, effective schema, QA
export, Visualization path, or extraction rehearsal may discover or execute extension code.
Schema-pack documentation URLs remain inert and cannot act as package locations.

A future host must define whether code runs in-process, out-of-process, or in a sandbox; how APIs are
versioned; how resources are bounded; how timeouts, crashes, and partial failures are isolated; and
how audit records are retained. It must also prevent an extension from mutating canonical packs,
project configuration, taxonomy, resources, sources, content, or generated artifacts except through
separately reviewed mutation services with explicit user intent.

## Lifecycle Separation

A future extension registry requires operational states distinct from pack and capability
lifecycle. It must separately represent at least discovery, acquisition, installation, integrity
verification, trust, permission, enablement, loading, health, disablement, quarantine, update,
revocation, and removal where those concepts apply. Phase 3.3.2 does not freeze names or transitions
for that state machine.

No single `active` or `available` flag may collapse these dimensions. A removed or revoked extension
must not delete schema-pack identity, capability declarations, project facts, or historical audit
records. Extension lifecycle must also remain separate from commercial subscription state.

## Deferred Implementation Gate

Phase 14.4 owns the future trusted executable-extension host. Before code loading is implemented, it
must provide:

- dedicated manifest and host-registry schemas;
- deterministic compatibility and implementation-binding rules;
- package integrity, publisher identity, signing, trust, and revocation policy;
- explicit permission declarations and enforcement;
- process or sandbox isolation and bounded failure behavior;
- install, update, rollback, disable, quarantine, and removal semantics;
- audit and diagnostics that do not become canonical project data;
- no-provider and built-in-only compatibility; and
- permanent positive, malformed, boundary, ambiguity, scale, extraction, and security tests.

Until that gate closes, executable extensions are an architectural seam only.
