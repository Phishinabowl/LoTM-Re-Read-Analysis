# Framework Configuration Contracts

This directory is reserved for portable, versioned configuration-shape contracts.

All framework registry rows below share the strict YAML ingestion rules in `strict-configuration-ingestion.md` before their paired loaders apply registry-specific validation.

The current executable contract is enforced by the matching Python and PowerShell loaders:

| Configuration | Current validator pair |
| --- | --- |
| `Project_Config/project.yaml` | `Tools/Runtime/Python/knowledge_framework/project_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` |
| `Project_Config/schema-packs.yaml` and selected packs | `Tools/Runtime/Python/knowledge_framework/schema_pack_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` |
| `Project_Config/taxonomy.yaml` | `Tools/Runtime/Python/knowledge_framework/taxonomy_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` |
| `Project_Config/resources.yaml` | `Tools/Runtime/Python/knowledge_framework/resource_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1` |
| `Project_Config/sources.yaml` | `Tools/Runtime/Python/knowledge_framework/source_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `narrative-source-registry.md` |
| `Project_Config/entities.yaml` | `Tools/Runtime/Python/knowledge_framework/entity_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `narrative-entity-registry.md` |
| Typed identity targets | Entity loader provider APIs; see `identity-target-provider.md` |
| `Project_Config/reconciliation.yaml` | `Tools/Runtime/Python/knowledge_framework/reconciliation_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `reconciliation-registry.md` |
| `Project_Config/provenance.yaml` | `Tools/Runtime/Python/knowledge_framework/provenance_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `provenance-registry.md` |
| Manifest-selected Unicode lookup data | `Tools/Runtime/Python/knowledge_framework/lookup_key_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `lookup-key-normalization.md` |
| Shared temporal windows | `Tools/Runtime/Python/knowledge_framework/temporal_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `temporal-model.md` |
| `Project_Config/chronology.yaml` | `Tools/Runtime/Python/knowledge_framework/chronology_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `chronology-registry.md` |
| `Project_Config/occurrences.yaml` | `Tools/Runtime/Python/knowledge_framework/occurrence_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `occurrence-recurrence-registry.md` |
| `Project_Config/interpretations.yaml` | `Tools/Runtime/Python/knowledge_framework/interpretation_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `structural-interpretation-registry.md` |
| Generated `EffectiveProjectSchema` | `Tools/Runtime/Python/knowledge_framework/effective_schema.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `effective-project-schema.md` |
| `Framework/framework.yaml` | `Tools/Runtime/Python/knowledge_framework/framework_config.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `framework-installation.md` |
| `Framework/capability-roadmap.yaml` | `Tools/Runtime/Python/knowledge_framework/capability_roadmap.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `capability-lifecycle-and-roadmap.md` |
| Generated `FrameworkCatalog` | `Tools/Runtime/Python/knowledge_framework/framework_catalog.py`, `Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1`; see `framework-catalog.md` |
| Aggregate validation reporting | `Tools/Conformance/run_conformance.py`, `Tools/Conformance/Run-Conformance.ps1`, and `Tools/Compatibility/run_compatibility.py`; see `validation-run-reporting.md` |

Future machine-readable schema documents belong here as those loader contracts are stabilized. Do not add a partial schema that claims broader validation coverage than the loaders actually provide.

`effective-project-schema.md` defines the generated composition contract implemented by the paired
runtime services and inspection/export commands. It is diagnostic output over the canonical
registries, not another canonical registry.

`framework-catalog.md` defines the distinct project-independent installed-pack inventory and its
selection envelope. `framework-installation.md` defines its explicit project-independent bootstrap.
Canonical pack files remain authoritative. Paired installation/catalog loaders, inspection
commands, conformance, scale, and compatibility checks are executable. Effective-schema composition
uses validated catalog records, and explicit project attachment emits the separate
`FrameworkCatalogProjectView` without changing the base catalog.

`declarative-schema-pack.md` defines schema packs as versioned, data-only extension units. It makes
the existing closed pack shape an explicit safety boundary, prohibits executable and commercial
host state, and reserves future executable extensions and entitlement services as separate
contracts.

`trusted-executable-extension.md` defines the separate future host boundary for code-bearing
extensions. It separates package, extension, publisher, trust, permission, installation, and
runtime identity from packs and projects; reserves capability implementation binding without
moving capability authority into code; and explicitly implements no extension host.

`distribution-entitlement-boundary.md` defines optional offering, grant, and acquisition concerns
outside portable packs and projects. It preserves the factual installed catalog, separates product
prerequisites from technical dependencies, and makes entitlement-free local behavior the default
without implementing a commercial service.

`capability-lifecycle-and-roadmap.md` defines capability lifecycle meanings and transitions,
separates technical pack dependencies from implementation and domain-delivery prerequisites, and
fixes the authority, identity, ordering, and failure boundary for the future machine-readable
capability roadmap. Phase 3.4.1 implements the contract only; the registry, loaders, projections,
and promotion conformance follow in Phases 3.4.2 through 3.4.4.

## Capability Semantics

`capability-lifecycle-and-roadmap.md` is the sole normative authority for capability lifecycle
meanings, valid transitions, roadmap-candidate status, delivery traceability, and promotion or
removal constraints. Schema packs declare capabilities, selected-pack composition determines which
declarations enter a project, and project activation enables only eligible selected capabilities.

The registry-specific contracts in this directory define how those shared semantics are validated,
resolved, serialized, and consumed. They must reference the lifecycle contract rather than redefine
its states. Roadmap metadata never changes pack dependency, selection, activation, or project-record
validity.

This distinction permits narrative, IT, legal, medical, and other projects to compose only the behavior relevant to their domain.
