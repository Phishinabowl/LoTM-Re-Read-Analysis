"""Reusable knowledge-framework runtime services."""

from .project_paths import (
    PROJECT_MANIFEST_PATH,
    PROJECT_ROOT_ENVIRONMENT_VARIABLE,
    is_project_root,
    resolve_project_root,
)

__all__ = [
    "PROJECT_MANIFEST_PATH",
    "PROJECT_ROOT_ENVIRONMENT_VARIABLE",
    "is_project_root",
    "resolve_project_root",
]
