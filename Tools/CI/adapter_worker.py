"""Fixed Python policy/preflight adapter endpoint over captured input; no arbitrary commands."""

import importlib
import importlib.metadata
import importlib.util
import base64
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


def run(request):
    root = Path(request["root"])
    if request["mode"] == "python-preflight":
        if sys.version.split()[0] != request["version"] or sys.prefix == sys.base_prefix:
            raise ValueError("Adopted Python version and isolated environment required")
        packages = {}
        for name, version in request["packages"].items():
            if importlib.metadata.version(name) != version:
                raise ValueError("Dependency version mismatch: " + name)
            module = importlib.import_module(request["imports"].get(name, name.replace("-", "_")))
            if not Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()):
                raise ValueError("Dependency imported outside selected environment: " + name)
            distribution = importlib.metadata.distribution(name)
            for item in distribution.files or []:
                if item.hash and item.hash.mode == "sha256":
                    path = Path(distribution.locate_file(item)).resolve()
                    if not path.is_relative_to(Path(sys.prefix).resolve()):
                        raise ValueError("Dependency RECORD escapes selected environment")
                    digest = base64.urlsafe_b64encode(hashlib.sha256(path.read_bytes()).digest()).rstrip(b"=").decode()
                    if digest != item.hash.value:
                        raise ValueError("Installed dependency content differs: " + name)
            packages[name] = version
        return {"status": "passed", "version": sys.version.split()[0], "packages": packages}
    if request["mode"] == "annotations":
        path = root / "Tools/Static/lint_work_annotations.py"
        spec = importlib.util.spec_from_file_location("ci_annotation_policy", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        policy = module.load_policy(root / "Tools/Static/work-annotations.json")
        fixtures, failures = module.run_fixtures(root / "Tools/Static/Fixtures/Work-Annotations/cases.json", policy)
        paths = []
        for name in request["paths"]:
            target = (root / name).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                raise ValueError("Annotation input escapes or is missing from captured source")
            paths.append(target)
        count, annotations, findings = module.scan_paths(root, policy, paths)
        return {
            "status": "failed" if findings or failures else "passed",
            "files_checked": count,
            "annotations": annotations,
            "fixture_cases": len(fixtures),
            "fixture_failures": failures,
            "findings": [item.as_dict() for item in findings],
        }
    if request["mode"] == "context":
        sys.path.insert(0, str(root / "Tools/Runtime/Python"))
        from knowledge_framework.effective_schema import load_effective_project_schema

        # Real current configuration/pack/provider context, not a synthetic conformance fixture.
        from knowledge_framework.project_config import load_project_config

        project = load_project_config(root)
        schema = load_effective_project_schema(root)
        return {
            "status": "passed",
            "context": "current project/framework/catalog/provider composition",
            "schema_type": type(schema).__name__,
            "project_type": type(project).__name__,
        }
    raise ValueError("Unknown fixed worker mode")


if __name__ == "__main__":
    try:
        value = run(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except Exception as error:
        value = {"status": "error", "error": str(error)}
    print(json.dumps(value, ensure_ascii=False))
    raise SystemExit(0 if value["status"] == "passed" else 1)
