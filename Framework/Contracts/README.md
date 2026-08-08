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
| Aggregate validation reporting | `Tools/Conformance/run_conformance.py`, `Tools/Conformance/Run-Conformance.ps1`, and `Tools/Compatibility/run_compatibility.py`; see `validation-run-reporting.md` |

Future machine-readable schema documents belong here as those loader contracts are stabilized. Do not add a partial schema that claims broader validation coverage than the loaders actually provide.

`effective-project-schema.md` defines the generated composition contract implemented by the paired
runtime services and inspection/export commands. It is diagnostic output over the canonical
registries, not another canonical registry.

## Capability Semantics

Schema packs declare capabilities; capability lifecycle controls availability; projects enable available capabilities.

- A capability absent from all selected packs is undeclared, unavailable, and disabled.
- `planned` capabilities are discoverable to roadmap tooling but unavailable for activation.
- `available` capabilities may be enabled by the project.
- `deprecated` capabilities remain available for compatibility or migration but should not be newly recommended.
- An available or deprecated capability omitted from the project's enabled list is disabled.
- Tools and interfaces must omit disabled feature modules without warning.
- A selected pack with a missing or incompatible hard dependency is invalid.
- A project registry that explicitly references an unavailable or disabled schema capability is invalid.

This distinction permits narrative, IT, legal, medical, and other projects to compose only the behavior relevant to their domain.
