# Framework Configuration Contracts

This directory is reserved for portable, versioned configuration-shape contracts.

The current executable contract is enforced by the matching Python and PowerShell loaders:

| Configuration | Current validator pair |
| --- | --- |
| `Project_Config/project.yaml` | `Tools/project_config.py`, `Tools/Project-Config.ps1` |
| `Project_Config/schema-packs.yaml` and selected packs | `Tools/schema_pack_config.py`, `Tools/Schema-Pack-Config.ps1` |
| `Project_Config/taxonomy.yaml` | `Tools/taxonomy_config.py`, `Tools/Taxonomy-Config.ps1` |
| `Project_Config/resources.yaml` | `Tools/resource_config.py`, `Tools/Resource-Config.ps1` |
| `Project_Config/sources.yaml` | `Tools/source_config.py`, `Tools/Source-Config.ps1` |

Future machine-readable schema documents belong here as those loader contracts are stabilized. Do not add a partial schema that claims broader validation coverage than the loaders actually provide.

## Capability Semantics

Schema packs provide capabilities; projects activate them.

- A capability absent from all selected packs is unavailable and therefore disabled.
- A capability supplied by a selected pack but omitted from the project's enabled list is available but disabled.
- Tools and interfaces must omit disabled feature modules without warning.
- A selected pack with a missing or incompatible hard dependency is invalid.
- A project registry that explicitly references an unavailable or disabled schema capability is invalid.

This distinction permits narrative, IT, legal, medical, and other projects to compose only the behavior relevant to their domain.
