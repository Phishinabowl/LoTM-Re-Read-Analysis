"""Native-test discovery and per-test process-state restoration; no runtime installation."""

import os
from pathlib import Path
import sys

import pytest

NATIVE_ROOT = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items):
    for item in items:
        if not Path(item.path).resolve().is_relative_to(NATIVE_ROOT):
            raise pytest.UsageError("Native pytest collection escaped Tools/Tests/Python")
        categories = [name for name in ("unit", "integration") if item.get_closest_marker(name)]
        if not categories:
            item.add_marker(pytest.mark.unit)
        elif len(categories) != 1:
            raise pytest.UsageError("Native tests require exactly one unit/integration category: " + item.nodeid)
    items.sort(key=lambda item: item.nodeid)


@pytest.fixture(autouse=True)
def restore_process_state():
    environment = dict(os.environ)
    directory = Path.cwd()
    import_path = sys.path[:]
    try:
        yield
    finally:
        os.chdir(directory)
        os.environ.clear()
        os.environ.update(environment)
        sys.path[:] = import_path
