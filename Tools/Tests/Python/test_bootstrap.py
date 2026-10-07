"""Bootstrap regressions: safety, provenance, eligibility and no implicit acquisition."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
_prior_import_path = sys.path[:]
try:
    sys.path.insert(0, str(ROOT / "Tools/Commands/Environment"))
    from dependency_requirements import read_requirements

    spec = importlib.util.spec_from_file_location("ci_bootstrap", ROOT / "Tools/CI/bootstrap.py")
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)
finally:
    sys.path[:] = _prior_import_path

pytestmark = pytest.mark.unit


def load_host_cache():
    prior = sys.path[:]
    try:
        sys.path.insert(0, str(ROOT / "Tools/CI"))
        spec = importlib.util.spec_from_file_location("host_cache_pilot", ROOT / "Tools/CI/host_cache.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = prior


def test_transport_key_separates_platform_namespace_and_changed_inputs(tmp_path):
    pilot = load_host_cache()
    for name in pilot.INPUTS:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / name).read_bytes())
    declaration = tmp_path / "requirements-python.txt"
    declaration.write_text("PyYAML==6.0.3\n")
    key = pilot.cache_identity(tmp_path, "one", "win32", "AMD64")["key"]
    assert key == pilot.cache_identity(tmp_path, "one", "win32", "x86_64")["key"]
    assert key != pilot.cache_identity(tmp_path, "one", "linux", "x86_64")["key"]
    assert key != pilot.cache_identity(tmp_path, "two", "win32", "AMD64")["key"]
    assert key != pilot.cache_identity(tmp_path, "one", "win32", "AMD64", "complete")["key"]
    declaration.write_text("PyYAML==6.0.2\n")
    assert key != pilot.cache_identity(tmp_path, "one", "win32", "AMD64")["key"]
    declaration.unlink()
    (tmp_path / pilot.INPUTS[0]).unlink()
    with pytest.raises(FileNotFoundError):
        pilot.cache_identity(tmp_path, "one", "win32", "AMD64")


@pytest.mark.parametrize("label", ["../outside", "", "a\nkey=bad", "a" * 41])
def test_transport_key_rejects_untrusted_labels(label):
    with pytest.raises(ValueError, match="namespace"):
        load_host_cache().cache_identity(ROOT, label)


def test_runtime_archive_offline_verification_never_downloads_or_repairs(tmp_path, monkeypatch):
    import hashlib

    pilot = load_host_cache()
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    monkeypatch.setattr(pilot.bootstrap, "ROOT", tmp_path)
    monkeypatch.setattr(pilot.urllib.request, "urlopen", lambda *a, **k: pytest.fail("Unexpected network"))
    expected = hashlib.sha256(b"approved").hexdigest()
    with pytest.raises(ValueError, match="unavailable offline"):
        pilot.acquire_archive("fixture.zip", expected, "https://example.invalid/fixture.zip", True)
    payload = tmp_path / ".local/ci-cache/tool-archives/fixture.zip"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="digest mismatch"):
        pilot.acquire_archive("fixture.zip", expected, "https://example.invalid/fixture.zip", True)
    assert payload.read_bytes() == b"corrupt"
    payload.write_bytes(b"approved")
    assert pilot.acquire_archive("fixture.zip", expected, "https://example.invalid/fixture.zip", True) == payload


def test_fault_controls_refuse_local_payload_mutation(monkeypatch):
    pilot = load_host_cache()
    monkeypatch.delenv("LOTM_CI_CACHE_PILOT", raising=False)
    with pytest.raises(ValueError, match="ephemeral hosted"):
        pilot.inject_fault("wheel")
    with pytest.raises(ValueError, match="Unknown cache fault"):
        pilot.inject_fault("unknown")


def test_owned_node_receipt_proves_reuse_and_refuses_modified_installation(tmp_path, monkeypatch):
    import hashlib
    import io
    import tarfile
    import zipfile

    pilot = load_host_cache()
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    monkeypatch.setattr(pilot.bootstrap, "ROOT", tmp_path)
    monkeypatch.setattr(pilot.urllib.request, "urlopen", lambda *a, **k: pytest.fail("Unexpected network"))
    data = tmp_path / "Tools/CI/Data"
    data.mkdir(parents=True)
    (data / "runtime-versions.json").write_text('{"node":"24.15.0","npm":"11.12.1"}')
    folder = "node-v24.15.0-" + ("win-x64" if sys.platform == "win32" else "linux-x64")
    filename = folder + (".zip" if sys.platform == "win32" else ".tar.gz")
    archive = tmp_path / ".local/ci-cache/tool-archives" / filename
    archive.parent.mkdir(parents=True)
    member = folder + ("/node.exe" if sys.platform == "win32" else "/bin/node")
    if sys.platform == "win32":
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr(member, b"approved synthetic executable")
    else:
        with tarfile.open(archive, "w:gz") as bundle:
            entry = tarfile.TarInfo(member)
            entry.size = len(b"approved synthetic executable")
            entry.mode = 0o755
            bundle.addfile(entry, io.BytesIO(b"approved synthetic executable"))
    monkeypatch.setattr(
        pilot, "NODE_ARCHIVES", {sys.platform: (filename, hashlib.sha256(archive.read_bytes()).hexdigest())}
    )
    directory = Path(pilot.node_runtime(True))
    assert Path(pilot.node_runtime(True)) == directory
    executable = directory / ("node.exe" if sys.platform == "win32" else "node")
    executable.write_bytes(b"modified")
    with pytest.raises(ValueError, match="no implicit repair"):
        pilot.node_runtime(True)
    assert executable.read_bytes() == b"modified"


def test_hosted_wheel_fault_is_confined_and_caught_by_real_verification(tmp_path, monkeypatch):
    import hashlib

    pilot = load_host_cache()
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    monkeypatch.setattr(pilot.bootstrap, "ROOT", tmp_path)
    monkeypatch.setenv("LOTM_CI_CACHE_PILOT", "hosted")
    data = tmp_path / "Tools/CI/Data"
    data.mkdir(parents=True)
    (data / "runtime-versions.json").write_text("{}")
    identity = {"synthetic": True}
    lock = {
        "packages": {
            "pyyaml": {
                "files": [
                    {
                        "filename": "pyyaml-6.0.3-py3-none-any.whl",
                        "sha256": hashlib.sha256(b"approved").hexdigest(),
                        "url": "https://files.pythonhosted.org/fixture.whl",
                    }
                ]
            }
        }
    }
    monkeypatch.setattr(pilot.bootstrap, "python_plan", lambda *a: ({"pyyaml": "6.0.3"}, identity, lock))
    with pytest.raises(ValueError, match="Fault target missing"):
        pilot.inject_fault("wheel")
    payload = tmp_path / ".local/ci-cache/python" / pilot.bootstrap.key_for(identity) / "pyyaml-6.0.3-py3-none-any.whl"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"approved")
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_bytes(b"preserved")
    pilot.inject_fault("wheel")
    with pytest.raises(ValueError, match="Corrupt cached wheel"):
        pilot.bootstrap.acquire_wheels({"pyyaml": "6.0.3"}, payload.parent, lock, offline=True, check=True)
    assert unrelated.read_bytes() == b"preserved"


def test_cache_corruption_is_not_silently_repaired_and_explicit_recovery_verifies(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    owner = tmp_path / ".local/cache"
    owner.mkdir(parents=True)
    payload = owner / "example-1.0-py3-none-any.whl"
    good = b"approved synthetic wheel bytes"
    import hashlib

    lock = {
        "packages": {
            "example": {
                "files": [
                    {
                        "filename": payload.name,
                        "sha256": hashlib.sha256(good).hexdigest(),
                        "url": "https://files.pythonhosted.org/example",
                    }
                ]
            }
        }
    }
    payload.write_bytes(b"corrupt")
    monkeypatch.setattr(bootstrap.urllib.request, "urlopen", lambda *a, **k: pytest.fail("Unexpected network"))
    with pytest.raises(ValueError, match="Corrupt"):
        bootstrap.acquire_wheels({"example": "1.0"}, owner, lock, offline=True, check=True)
    assert payload.read_bytes() == b"corrupt"
    payload.write_bytes(good)  # Explicit owner repair, outside verification.
    rows, missing = bootstrap.acquire_wheels({"example": "1.0"}, owner, lock, offline=True, check=True)
    assert len(rows) == 1 and missing == []


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


def test_npm_uses_distinct_empty_owned_configs_and_scrubs_lowercase_inheritance(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    monkeypatch.setenv("npm_config_userconfig", "untrusted")
    environment = bootstrap.npm_environment()
    user, global_config = Path(environment["NPM_CONFIG_USERCONFIG"]), Path(environment["NPM_CONFIG_GLOBALCONFIG"])
    assert user != global_config and user.read_bytes() == global_config.read_bytes() == b""
    assert "npm_config_userconfig" not in environment
    assert bootstrap.npm_environment(check=True)["NPM_CONFIG_USERCONFIG"] == str(user)
    global_config.write_text("unexpected=configuration")
    with pytest.raises(ValueError, match="empty owned"):
        bootstrap.npm_environment(check=True)


def test_npm_check_does_not_create_missing_configs(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="empty owned"):
        bootstrap.npm_environment(check=True)
    assert not (tmp_path / ".local").exists()


@pytest.mark.parametrize("deadline", ["expired", "nonfinite", "bounded"])
def test_bootstrap_children_obey_inherited_whole_unit_deadline(tmp_path, monkeypatch, deadline):
    monkeypatch.setattr(bootstrap.time, "monotonic", lambda: 100)
    monkeypatch.setenv("LOTM_CI_UNIT_DEADLINE", {"expired": "99", "nonfinite": "inf", "bounded": "105"}[deadline])
    calls = []

    def child(*args, **kwargs):
        calls.append(kwargs["timeout"])
        return type("Result", (), {"returncode": 0, "stdout": "ok"})()

    monkeypatch.setattr(bootstrap.subprocess, "run", child)
    if deadline == "bounded":
        assert bootstrap.run(["synthetic"], cwd=tmp_path) == "ok" and calls == [3]
    else:
        with pytest.raises(ValueError, match="deadline"):
            bootstrap.run(["synthetic"], cwd=tmp_path)
        assert not calls
