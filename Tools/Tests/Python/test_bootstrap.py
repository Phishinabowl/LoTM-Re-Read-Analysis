"""Bootstrap regressions: safety, provenance, eligibility and no implicit acquisition."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Tools/Commands/Environment"))
from dependency_requirements import read_requirements  # noqa: E402

spec = importlib.util.spec_from_file_location("ci_bootstrap", ROOT / "Tools/CI/bootstrap.py")
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def test_marker_aware_exact_graph_and_include_digest(tmp_path):
    (tmp_path / "base.txt").write_text("PyYAML==6.0.3\n")
    declaration = tmp_path / "dev.txt"
    declaration.write_text('-r base.txt\ncolorama==0.4.6; sys_platform == "win32"\n')
    windows, inputs = read_requirements(declaration, tmp_path, platform="win32")
    linux, _ = read_requirements(declaration, tmp_path, platform="linux")
    assert windows == {"colorama": "0.4.6", "pyyaml": "6.0.3"}
    assert linux == {"pyyaml": "6.0.3"}
    before = inputs["base.txt"]
    (tmp_path / "base.txt").write_text("PyYAML==6.0.2\n")
    assert read_requirements(declaration, tmp_path)[1]["base.txt"] != before


@pytest.mark.parametrize(
    "text",
    [
        "",
        "PyYAML>=6.0.3\n",
        "--index-url https://example.invalid\n",
        "PyYAML==6.0.3\npyyaml==6.0.2\n",
        "-r missing.txt\n",
        "-r loop.txt\n",
        "PyYAML==6.0.3; unknown == 'x'\n",
    ],
)
def test_unknown_floating_conflicting_missing_or_cyclic_requirements_fail(tmp_path, text):
    file = tmp_path / "loop.txt"
    file.write_text(text)
    with pytest.raises(ValueError):
        read_requirements(file, tmp_path)


def test_include_cannot_escape_owned_root(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (tmp_path / "outside.txt").write_text("PyYAML==6.0.3\n")
    file = root / "runtime.txt"
    file.write_text("-r ../outside.txt\n")
    with pytest.raises(ValueError, match="escapes"):
        read_requirements(file, root)


def test_duplicate_json_keys_are_not_silently_overwritten(tmp_path):
    file = tmp_path / "lock.json"
    file.write_text('{"schema_version":1,"schema_version":2}')
    with pytest.raises(ValueError, match="Duplicate"):
        bootstrap.read_json(file)


def test_corrupt_cached_payload_fails_without_network_or_install(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    cache = tmp_path / ".local/cache"
    cache.mkdir(parents=True)
    file = cache / "example-1.0-py3-none-any.whl"
    file.write_bytes(b"corrupt")
    lock = {
        "packages": {
            "example": {
                "files": [{"filename": file.name, "sha256": "0" * 64, "url": "https://files.pythonhosted.org/example"}]
            }
        }
    }
    monkeypatch.setattr(bootstrap.urllib.request, "urlopen", lambda *a, **k: pytest.fail("Unexpected acquisition"))
    with pytest.raises(ValueError, match="Corrupt"):
        bootstrap.acquire_wheels({"example": "1.0"}, cache, lock, offline=True, check=True)


def test_missing_offline_payload_is_not_a_pass_or_an_automatic_download(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    file = "example-1.0-py3-none-any.whl"
    lock = {
        "packages": {
            "example": {
                "files": [{"filename": file, "sha256": "0" * 64, "url": "https://files.pythonhosted.org/example"}]
            }
        }
    }
    monkeypatch.setattr(bootstrap.urllib.request, "urlopen", lambda *a, **k: pytest.fail("Unexpected acquisition"))
    with pytest.raises(ValueError, match="unavailable offline"):
        bootstrap.acquire_wheels({"example": "1.0"}, tmp_path / ".local/cache", lock, offline=True, check=True)


def test_inherited_browser_selection_and_python_paths_are_not_trusted(monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "outside")
    monkeypatch.setenv("PUPPETEER_FIREFOX_SKIP_DOWNLOAD", "false")
    monkeypatch.setenv("PUPPETEER_EXECUTABLE_PATH", "outside")
    environment = bootstrap.clean_environment()
    assert "PYTHONPATH" not in environment
    assert not any(key.startswith("PUPPETEER_") for key in environment)
    assert environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"


def test_declaration_change_invalidate_key_and_os_keys_do_not_alias():
    assert bootstrap.key_for({"lock": "a", "os": "win32"}) != bootstrap.key_for({"lock": "b", "os": "win32"})
    assert bootstrap.key_for({"lock": "a", "os": "win32"}) != bootstrap.key_for({"lock": "a", "os": "linux"})


def test_pure_runtime_lock_has_no_development_or_media_dependencies():
    versions = json.loads((ROOT / "Tools/CI/Data/runtime-versions.json").read_text())
    pins, _, _ = bootstrap.python_plan("runtime", False, versions)
    assert set(pins) == {"pyyaml", "pip"}
