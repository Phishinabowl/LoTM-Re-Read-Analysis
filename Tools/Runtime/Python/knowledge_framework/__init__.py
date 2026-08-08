"""Reusable knowledge-framework runtime services."""

from .project_paths import (
    PROJECT_MANIFEST_PATH,
    PROJECT_ROOT_ENVIRONMENT_VARIABLE,
    is_project_root,
    resolve_project_root,
)
from .framework_config import FrameworkConfig, load_framework_config
from .framework_catalog import (
    FrameworkCatalog,
    FrameworkCatalogError,
    compose_framework_catalog_project_view,
    compose_framework_catalog_project_view_selection,
    compose_framework_catalog_selection,
    framework_catalog_failure,
    framework_catalog_json,
    framework_catalog_project_view_json,
    load_framework_catalog,
)
from .framework_paths import (
    FRAMEWORK_MANIFEST_PATH,
    FRAMEWORK_ROOT_ENVIRONMENT_VARIABLE,
    is_framework_root,
    resolve_framework_root,
)
from .effective_schema import (
    EffectiveProjectSchema,
    compose_effective_schema_selection,
    compose_effective_schema_report_model,
    compose_effective_project_schema,
    compose_effective_consumer_schema_projection,
    effective_schema_failure,
    effective_schema_json,
    effective_schema_markdown,
    load_effective_project_schema,
)

__all__ = [
    "PROJECT_MANIFEST_PATH",
    "PROJECT_ROOT_ENVIRONMENT_VARIABLE",
    "is_project_root",
    "resolve_project_root",
    "FRAMEWORK_MANIFEST_PATH",
    "FRAMEWORK_ROOT_ENVIRONMENT_VARIABLE",
    "FrameworkConfig",
    "FrameworkCatalog",
    "FrameworkCatalogError",
    "compose_framework_catalog_project_view",
    "compose_framework_catalog_project_view_selection",
    "compose_framework_catalog_selection",
    "framework_catalog_failure",
    "framework_catalog_json",
    "framework_catalog_project_view_json",
    "is_framework_root",
    "load_framework_config",
    "load_framework_catalog",
    "resolve_framework_root",
    "EffectiveProjectSchema",
    "compose_effective_schema_selection",
    "compose_effective_schema_report_model",
    "compose_effective_project_schema",
    "compose_effective_consumer_schema_projection",
    "effective_schema_failure",
    "effective_schema_json",
    "effective_schema_markdown",
    "load_effective_project_schema",
]
