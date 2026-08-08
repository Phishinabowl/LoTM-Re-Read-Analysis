"""Conformance vectors for framework installation discovery and loading."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile


TOOLS_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_ROOT = TOOLS_ROOT / "Runtime" / "Python"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from knowledge_framework.framework_config import load_framework_config
from knowledge_framework.framework_paths import resolve_framework_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    return parser


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def create_framework_marker(root: Path) -> Path:
    write_text(root / "Framework" / "framework.yaml", "schema_version: 1\n")
    return root.resolve()


def assert_rejected(action, expected_text: str) -> None:
    try:
        action()
    except (RuntimeError, ValueError) as exc:
        if expected_text not in str(exc):
            raise AssertionError(f"Expected error containing {expected_text!r}, got: {exc}") from exc
        return
    raise AssertionError(f"Expected rejection containing {expected_text!r}.")


def prepare_config_root(source_root: Path, target_root: Path, manifest_source: Path) -> Path:
    framework = target_root / "Framework"
    (framework / "Packs").mkdir(parents=True)
    data = framework / "Data"
    data.mkdir()
    shutil.copy2(source_root / "Framework" / "Data" / "unicode-lookup-16.0.0.json", data)
    shutil.copy2(manifest_source, framework / "framework.yaml")
    return target_root.resolve()


def main() -> int:
    args = build_parser().parse_args()
    root = resolve_framework_root(args.root, executable_path=__file__)
    fixture_root = root / "Framework" / "Data" / "Framework-Installation"
    expectations = json.loads((fixture_root / "expectations.json").read_text(encoding="utf-8"))
    original_cwd = Path.cwd()
    temp_root = Path(tempfile.mkdtemp(prefix="knowledge-framework-installation-"))
    root_vectors = 0
    config_vectors = 0

    try:
        framework_a = create_framework_marker(temp_root / "framework-a")
        framework_b = create_framework_marker(temp_root / "framework-b")
        nested_a = framework_a / "one" / "two"
        nested_a.mkdir(parents=True)
        nested_b = framework_b / "nested"
        nested_b.mkdir()
        executable_b = nested_b / "command.py"
        executable_b.write_text("# fixture\n", encoding="utf-8")
        unrelated = temp_root / "unrelated"
        unrelated.mkdir()
        unrelated_executable = unrelated / "command.py"
        unrelated_executable.write_text("# fixture\n", encoding="utf-8")
        git_only = temp_root / "git-only"
        (git_only / ".git").mkdir(parents=True)

        assert resolve_framework_root(root, environment={"KNOWLEDGE_FRAMEWORK_ROOT": str(framework_b)}) == root
        root_vectors += 1
        assert resolve_framework_root(environment={"KNOWLEDGE_FRAMEWORK_ROOT": str(framework_b)}) == framework_b
        root_vectors += 1
        assert_rejected(
            lambda: resolve_framework_root(environment={"KNOWLEDGE_FRAMEWORK_ROOT": str(unrelated)}),
            "missing required manifest",
        )
        root_vectors += 1
        assert_rejected(
            lambda: resolve_framework_root(environment={"KNOWLEDGE_FRAMEWORK_ROOT": "relative/framework"}),
            "must be an absolute path",
        )
        root_vectors += 1
        assert resolve_framework_root(current_directory=nested_a, environment={}) == framework_a
        root_vectors += 1
        assert (
            resolve_framework_root(
                executable_path=executable_b,
                current_directory=unrelated,
                environment={},
            )
            == framework_b
        )
        root_vectors += 1
        assert (
            resolve_framework_root(
                executable_path=executable_b,
                current_directory=nested_a,
                environment={},
            )
            == framework_a
        )
        root_vectors += 1
        assert (
            resolve_framework_root(
                executable_path=executable_b,
                current_directory=nested_a,
                environment={"KNOWLEDGE_FRAMEWORK_ROOT": str(framework_b)},
            )
            == framework_b
        )
        root_vectors += 1
        assert_rejected(
            lambda: resolve_framework_root(
                executable_path=unrelated_executable,
                current_directory=git_only,
                environment={},
            ),
            "Could not auto-detect",
        )
        root_vectors += 1
        assert_rejected(
            lambda: resolve_framework_root(
                executable_path=unrelated_executable,
                current_directory=unrelated,
                environment={},
            ),
            "Expected manifest: Framework/framework.yaml",
        )
        root_vectors += 1
        assert Path.cwd() == original_cwd
        root_vectors += 1

        canonical = load_framework_config(root)
        assert canonical.framework_id == expectations["framework_id"]
        assert canonical.packs_relative_path == expectations["packs_relative_path"]
        assert canonical.lookup_keys_relative_path == expectations["lookup_keys_relative_path"]
        assert canonical.lookup_keys.unicode_version == expectations["unicode_version"]
        assert canonical.lookup_keys.algorithm == expectations["algorithm"]
        config_vectors += 1

        multi_root = prepare_config_root(root, temp_root / "multiple-lookups", root / "Framework" / "framework.yaml")
        write_text(
            multi_root / "Framework" / "Data" / "unicode-lookup-99.0.0.json",
            '{"schema_version":0}\n',
        )
        assert load_framework_config(multi_root).lookup_keys.unicode_version == expectations["unicode_version"]
        config_vectors += 1

        for index, case in enumerate(expectations["invalid_cases"]):
            case_root = prepare_config_root(root, temp_root / f"invalid-{index}", fixture_root / case["file"])
            shutil.copy2(fixture_root / "invalid-lookup.json", case_root / "Framework" / "Data" / "invalid-lookup.json")
            assert_rejected(lambda case_root=case_root: load_framework_config(case_root), case["error"])
            config_vectors += 1
    finally:
        shutil.rmtree(temp_root)

    if root_vectors != expectations["root_vectors"]:
        raise AssertionError(f"Expected {expectations['root_vectors']} root vectors, got {root_vectors}.")

    summary = {
        "algorithm": expectations["algorithm"],
        "config_vectors": config_vectors,
        "environment_variable": "KNOWLEDGE_FRAMEWORK_ROOT",
        "framework_id": expectations["framework_id"],
        "invalid_cases": len(expectations["invalid_cases"]),
        "marker": "Framework/framework.yaml",
        "root_vectors": root_vectors,
        "schema_version": expectations["schema_version"],
        "unicode_version": expectations["unicode_version"],
        "working_directory_preserved": Path.cwd() == original_cwd,
    }
    if args.json:
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "Framework-installation conformance passed: "
            f"{root_vectors} root vectors, {config_vectors} config vectors, "
            f"{len(expectations['invalid_cases'])} invalid cases."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
