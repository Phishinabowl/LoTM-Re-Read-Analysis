"""Shared synthetic extraction consumer; no runtime imports or canonical project data."""

from pathlib import Path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_neutral_consumer(target_root: Path) -> None:
    for relative in (
        "Content",
        "Project_Config",
        "Tools/Extraction-Stubs",
    ):
        (target_root / relative).mkdir(parents=True, exist_ok=True)

    write_text(target_root / "Tools/Extraction-Stubs/helper.py", "# Neutral extraction helper stub.\n")
    write_text(target_root / "Tools/Extraction-Stubs/Helper.ps1", "# Neutral extraction helper stub.\n")
    write_text(target_root / "Tools/Extraction-Stubs/settings.json", "{}\n")

    write_text(
        target_root / "Project_Config/project.yaml",
        """schema_version: 11
project_id: extraction-smoke
framework: knowledge-model
domain: neutral

paths:
  content_roots:
    - id: content
      path: Content
      provenance_mode: fixed
      provenance_label: content
  resource_roots:
    - id: framework
      path: Framework
      required: true
    - id: tools
      path: Tools
      required: true
    - id: project-config
      path: Project_Config
      required: true
  qa_export: QA_Output
  visualization:
    python_helper: Tools/Extraction-Stubs/helper.py
    powershell_helper: Tools/Extraction-Stubs/Helper.ps1
    render_settings: Tools/Extraction-Stubs/settings.json
    puppeteer_config: Tools/Extraction-Stubs/settings.json
  cleanup:
    python_helper: Tools/Extraction-Stubs/helper.py
    powershell_helper: Tools/Extraction-Stubs/Helper.ps1

registries:
  lookup_keys: Framework/Data/unicode-lookup-16.0.0.json
  schema_packs: Project_Config/schema-packs.yaml
  taxonomy: Project_Config/taxonomy.yaml
  resources: Project_Config/resources.yaml
  sources: Project_Config/sources.yaml
  entities: Project_Config/entities.yaml
  reconciliation: Project_Config/reconciliation.yaml
  provenance: Project_Config/provenance.yaml
  chronology: Project_Config/chronology.yaml
  occurrences: Project_Config/occurrences.yaml
  interpretations: Project_Config/interpretations.yaml
  hosting: Project_Config/hosting.yaml
""",
    )
    write_text(
        target_root / "Project_Config/schema-packs.yaml",
        """schema_version: 2
selected_packs:
  - pack_id: core
    path: Framework/Packs/core/pack.yaml
capability_activation:
  default: disabled
  enabled:
    - structural-interpretation-modeling
""",
    )
    write_text(
        target_root / "Project_Config/taxonomy.yaml",
        """schema_version: 2
content_types: {}
categories: {}
""",
    )
    write_text(
        target_root / "Project_Config/resources.yaml",
        """schema_version: 1
resource_kinds: {}
resource_types: {}
""",
    )
    for name in (
        "sources",
        "entities",
        "reconciliation",
        "provenance",
        "chronology",
        "occurrences",
        "interpretations",
        "hosting",
    ):
        write_text(target_root / f"Project_Config/{name}.yaml", "schema_version: 1\n")
