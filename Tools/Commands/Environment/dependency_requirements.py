"""Strict repository-owned exact Python declaration reader; performs no installation."""

import hashlib
from pathlib import Path, PureWindowsPath
import re
import sys


EXACT = re.compile(r'([A-Za-z0-9][A-Za-z0-9_.-]*)==([0-9]+(?:\.[0-9]+)*)(?:;\s*sys_platform\s*==\s*"(win32|linux)")?')
IMPORT_NAMES = {"pyyaml": "yaml", "pillow": "PIL", "pyproject-hooks": "pyproject_hooks", "pygments": "pygments"}


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def read_requirements(path, root, *, platform=None):
    """Return active exact pins and all declaration inputs; reject unsafe/unknown grammar."""
    root = Path(root).resolve()
    platform = sys.platform if platform is None else platform
    pins, inputs, active = {}, {}, set()

    def visit(candidate):
        candidate = Path(candidate).resolve()
        if not candidate.is_relative_to(root):
            raise ValueError(f"Requirement include escapes repository: {candidate}")
        if candidate in active:
            raise ValueError(f"Requirement include cycle: {candidate}")
        if not candidate.is_file():
            raise ValueError(f"Requirements file missing: {candidate}")
        content = candidate.read_text(encoding="utf-8")
        if not any(line.strip() and not line.lstrip().startswith("#") for line in content.splitlines()):
            raise ValueError(f"Requirements file is empty: {candidate}")
        active.add(candidate)
        inputs[candidate.relative_to(root).as_posix()] = hashlib.sha256(candidate.read_bytes()).hexdigest()
        for number, raw in enumerate(content.splitlines(), 1):
            line = raw.partition("#")[0].strip()
            if not line:
                continue
            if line.startswith("-r "):
                relative = Path(line[3:].strip())
                if relative.is_absolute() or PureWindowsPath(line[3:].strip()).is_absolute():
                    raise ValueError(f"Absolute requirement include: {candidate}:{number}")
                visit(candidate.parent / relative)
                continue
            match = EXACT.fullmatch(line)
            if match is None:
                raise ValueError(f"Unsupported requirement grammar: {candidate}:{number}: {line}")
            name, version, marker = match.groups()
            if marker and marker != platform:
                continue
            name = normalize(name)
            if name in pins and pins[name] != version:
                raise ValueError(f"Conflicting requirement versions for {name}")
            pins[name] = version
        active.remove(candidate)

    visit(path)
    return dict(sorted(pins.items())), dict(sorted(inputs.items()))
