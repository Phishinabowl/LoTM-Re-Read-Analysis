# Distribution And Entitlement Boundary

## Status And Purpose

This contract defines the Phase 3.3.3 boundary for optional commercial distribution and
entitlement services. It does not define an offering-catalog schema, account system, identity
provider, payment flow, subscription service, token format, network protocol, package repository,
installer, update service, offline-grace policy, or post-install enforcement engine.

Distribution answers where an artifact may be discovered and acquired. Entitlement answers whether
a host principal has a grant relevant to that acquisition. Neither concern owns schema-pack
semantics, technical dependency composition, project selection, capability activation, executable
trust, runtime permissions, or project facts.

The entitlement-free path remains the default. A local framework installation with valid packs
must retain its current deterministic offline behavior when no distribution source or entitlement
provider is configured.

## Separate Objects And Authorities

A future commercial distribution system may contain:

- an offering catalog with offering identity, presentation, channel, and commercial metadata;
- many-to-many offering grants to packs or pack bundles;
- product prerequisites that govern commercial acquisition rather than technical compatibility;
- an optional entitlement provider that evaluates a host principal's grants;
- acquisition decisions produced from distribution, entitlement, and host policy; and
- host-local download, installation, update, and audit state.

Those objects remain outside canonical `pack.yaml`, `Project_Config/`, `FrameworkCatalog`, and
`EffectiveProjectSchema`. They also remain separate from executable-extension manifests, publisher
trust, signatures, and runtime permissions.

| Concern | Authority |
| --- | --- |
| Pack identity, lifecycle, dependencies, capabilities, and controlled values | Declarative schema packs |
| Installed pack inventory and technical selectability | `FrameworkCatalog` |
| Pack selection and capability activation for one project | Project configuration |
| Offering identity, presentation, pricing, and commercial grouping | Future distribution service |
| Principal, account, organization, tenant, subscription, and grant state | Future identity and entitlement services |
| Whether an artifact may be acquired now | Future acquisition policy |
| Package integrity, publisher trust, and executable permissions | Future package or executable-extension host |
| Canonical project facts | Project registries and content stores |

Commercial state may permit or deny an acquisition operation. It cannot rewrite any higher
authority, manufacture technical compatibility, or become canonical project data.

## Independent State Dimensions

The following states answer different questions and must never collapse into one lifecycle value:

| State | Question | Authority |
| --- | --- | --- |
| Offering discoverable | Is a remote or configured distribution offering visible to this host context? | Distribution service |
| Entitled | Does the evaluated host principal hold a relevant grant? | Entitlement provider |
| Acquirable | Does distribution, entitlement, and host policy permit acquisition now? | Acquisition policy |
| Installed | Is a valid local pack present in the framework installation? | `FrameworkCatalog` discovery |
| Selectable | Is the installed pack active with all technical dependencies and versions satisfied? | `FrameworkCatalog` composition |
| Selected | Did this project select the pack through valid dependency closure? | Project configuration |
| Enabled | Did this project activate an available capability? | Project configuration |

Offering discoverability is not the `FrameworkCatalog` pack row's `discoverability` mapping. The
catalog mapping describes factual local installation and technical selectability; a distribution
service describes remote or configured offerings. Interfaces must label the scopes clearly rather
than presenting one ambiguous `discoverable` flag.

No universal implication chain exists:

- a local or open pack may be installed, selectable, selected, and enabled without an offering or
  entitlement provider;
- an offering may be discoverable but not entitled or acquirable;
- a principal may be entitled while acquisition is blocked by source availability, host policy,
  compatibility, territory, or another distribution rule;
- an acquired artifact is not installed until local validation succeeds;
- an installed pack may be technically unselectable because a dependency is missing or incompatible;
- a selectable pack remains unselected until project configuration changes; and
- a selected pack does not enable every capability automatically.

The existing schema-pack lifecycle `available` retains its current meaning and must not mean
discoverable, entitled, acquirable, installed, selected, subscribed, paid, or licensed.

## Offering And Grant Granularity

An offering is a commercial or distribution-facing identity, not a pack. One offering may grant
several packs, and one pack may appear in several offerings. Offering identity, SKU, product tier,
price, currency, billing cadence, promotion, subscription, and grant terms remain outside pack
files and portable projects.

The initial planned commercial granularity is a pack or named pack bundle. A bundle is a
distribution grouping and does not become a schema pack, pack dependency, capability group,
solution profile, or project composition record. Entitlement may make each granted pack eligible
for acquisition, but every pack still requires independent local validation and normal technical
dependency closure.

Capability-level grants are deferred. Capability identity remains pack-owned, and capability
activation remains project-owned. A future product requirement must prove why capability-level
commercial policy is necessary before it can add another state dimension.

## Product Prerequisites Versus Pack Dependencies

Product prerequisites express commercial relationships such as requiring a base product or tier
before an add-on may be acquired. Pack dependencies express technical requirements such as a stable
pack ID and minimum compatible version. The two graphs must remain separate.

A product prerequisite cannot:

- satisfy, replace, reorder, or weaken a pack dependency;
- make an uninstalled dependency appear installed;
- make a deferred or incompatible pack selectable;
- select a pack for a project; or
- activate a capability.

Likewise, satisfying a technical pack dependency does not prove purchase, subscription, grant, or
commercial eligibility. Explainable acquisition decisions may cite both graphs but must report them
as distinct contributors.

## Optional Entitlement Provider

An entitlement provider is an optional host-service interface. Authentication, account lookup,
organization or tenant membership, subscription evaluation, token storage, network access, and
provider credentials remain behind that interface. Portable framework code and projects must not
store or require them.

A future provider decision should be deterministic for its explicit inputs and return an
explainable result suitable for acquisition policy. It must distinguish at least a confirmed grant,
confirmed absence of a required grant, provider-not-applicable, and indeterminate/provider-failure
outcome without treating service failure as a valid grant.

No-provider behavior is explicit:

- valid locally installed packs remain inspectable, selectable, selected, and enabled according to
  current technical and project rules;
- local or otherwise entitlement-free acquisition remains possible when its configured source and
  host policy allow it;
- an operation that explicitly requires a commercial grant cannot invent one; and
- no account, token, network connection, cached decision, or offline-grace record is required merely
  to load a local project.

Provider outage or an indeterminate remote decision may block only the acquisition operation that
requires it. It must not mutate, uninstall, deselect, disable, or rewrite an already installed pack
or project. Expiry, revocation, cached decisions, offline grace, and any post-install enforcement
remain deferred to a separately reviewed policy.

## Catalog And Project Isolation

The base `FrameworkCatalog` remains a factual inventory of valid locally installed packs. It does
not list remote offerings, prices, accounts, grants, subscriptions, downloadable packages, or
entitlement state. A distribution UI may join catalog records with external offering records by
stable pack ID, but the joined view is a host diagnostic and cannot be ingested as a catalog.

`EffectiveProjectSchema` remains a declarative view of one valid project composition. It must not
change when the current principal, account, subscription, offering, price, token, or entitlement
provider changes. Commercial policy cannot alter pack lifecycle, dependency closure, controlled
values, taxonomy, resources, capability activation, or project facts.

Portable project bundles may record technical framework and pack compatibility requirements. They
must not embed account identity, entitlement grants, subscription state, tokens, prices, or a claim
that the recipient is commercially authorized. Acquisition is evaluated by the receiving host.

## Relationship To Executable Extensions

Entitlement does not establish package integrity, publisher trust, compatibility, permission, or
execution authority. The trusted executable-extension boundary remains independent even if a future
offering can distribute both declarative packs and code-bearing extensions.

Phase 3.3.3 initially defines pack and pack-bundle grants only. Executable-extension distribution,
installation, signing, trust, permissions, and runtime enforcement remain deferred to Phase 14.4.

## Deferred Operations Gate

Phase 14.3 owns future add-on discovery, optional entitlement-aware acquisition, installation
preview, dependency and migration planning, update, disablement, and removal. Before those
operations become available, that phase must define:

- distribution-source and offering-catalog contracts;
- provider and acquisition-decision contracts with explainable failure behavior;
- pack and pack-bundle grant identity;
- product-prerequisite evaluation separate from pack dependency validation;
- package integrity and installation staging;
- transactional project-mutation previews and rollback;
- update, revocation, offline-grace, and post-install policy or explicit deferral; and
- permanent no-provider, provider-failure, malformed, boundary, ambiguity, scale, extraction,
  privacy, and security coverage.

Until that gate closes, distribution and entitlement are an architectural seam only.
