"""Reusable knowledge-framework runtime services."""

from .project_paths import (
    PROJECT_MANIFEST_PATH,
    PROJECT_ROOT_ENVIRONMENT_VARIABLE,
    is_project_root,
    resolve_project_root,
)
from .effective_schema import (
    EffectiveProjectSchema,
    assert_consumer_schema_shadow,
    compare_consumer_schema_projections,
    compose_effective_project_schema,
    compose_effective_consumer_schema_projection,
    compose_legacy_consumer_schema_projection,
    effective_schema_failure,
    effective_schema_json,
    load_effective_project_schema,
)

__all__ = [
    "PROJECT_MANIFEST_PATH",
    "PROJECT_ROOT_ENVIRONMENT_VARIABLE",
    "is_project_root",
    "resolve_project_root",
    "EffectiveProjectSchema",
    "assert_consumer_schema_shadow",
    "compare_consumer_schema_projections",
    "compose_effective_project_schema",
    "compose_effective_consumer_schema_projection",
    "compose_legacy_consumer_schema_projection",
    "effective_schema_failure",
    "effective_schema_json",
    "load_effective_project_schema",
]
