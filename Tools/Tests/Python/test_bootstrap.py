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


def release_deriver_fixture(tmp_path, mutation="none"):
    import hashlib
    import io
    import tarfile

    spec = importlib.util.spec_from_file_location(
        "release_deriver", ROOT / "Tools/CI/derive_python_release_reference.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    specification = json.loads(module.SPEC.read_text(encoding="utf-8"))
    directories = ["bin", "lib", "lib/python3.14", "lib/python3.14/site-packages"]
    files = {"bin/python3.14": b"fixture interpreter"}
    rows = [{"path": path, "kind": "directory", "unix_mode": 0o755} for path in directories]
    rows += [
        {
            "path": path,
            "kind": "file",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "unix_mode": 0o755,
        }
        for path, data in files.items()
    ]
    rows += [
        {"path": path, "kind": "symlink", "target": target}
        for path, target in {
            "bin/python": "python3.14",
            "bin/python314": "python3.14",
            "python": "./bin/python3.14",
        }.items()
    ]
    if mutation == "generated":
        extra_dirs = [
            "lib/python3.14/__pycache__",
            "lib/python3.14/preexisting",
            "lib/python3.14/preexisting/__pycache__",
        ]
        directories += extra_dirs
        rows += [{"path": path, "kind": "directory", "unix_mode": 0o755} for path in extra_dirs]
        retained_files = {
            "lib/python3.14/module.py": b"source",
            "lib/python3.14/__pycache__/sourceless.cpython-314.pyc": b"required",
        }
        rows += [
            {
                "path": path,
                "kind": "file",
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "unix_mode": 0o644,
            }
            for path, data in retained_files.items()
        ]
        files.update(retained_files)
        files["lib/python3.14/__pycache__/module.cpython-314.pyc"] = b"generated"
    frame = {"root_unix_mode": 0o755, "entries": sorted(rows, key=lambda row: row["path"])}
    specification["expected_inventory_sha256"] = hashlib.sha256(
        json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()
    prefix = "lib/python3.14/site-packages/"
    directories += [prefix + "pip", prefix + "pip-26.2.1.dist-info"]
    files.update(
        {
            prefix + "pip/__init__.py": b"pip",
            prefix + "pip-26.2.1.dist-info/RECORD": b"record",
            "setup.sh": b"never run",
        }
    )
    archive = tmp_path / "fixture.tar.gz"
    with tarfile.open(archive, "w:gz") as stream:
        for path in [".", *directories]:
            member = tarfile.TarInfo(path)
            member.type, member.mode = tarfile.DIRTYPE, 0o755
            stream.addfile(member)
        for path, data in files.items():
            member = tarfile.TarInfo(path)
            member.size, member.mode = len(data), 0o755 if path == "bin/python3.14" else 0o644
            if mutation == "mode" and path == "bin/python3.14":
                member.mode = 0o777
            stream.addfile(member, io.BytesIO(data))
        if mutation in ("escape", "hardlink", "duplicate", "link"):
            member = tarfile.TarInfo(
                {"escape": "../outside", "hardlink": "hard", "duplicate": "bin", "link": "bad"}[mutation]
            )
            member.mode = 0o644
            if mutation in ("hardlink", "link"):
                member.type = tarfile.LNKTYPE if mutation == "hardlink" else tarfile.SYMTYPE
                member.linkname = "../outside"
            stream.addfile(member)
    specification["identity"]["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    if mutation == "archive-hash":
        specification["identity"]["archive_sha256"] = "0" * 64
    if mutation == "inventory-hash":
        specification["expected_inventory_sha256"] = "0" * 64
    return module, archive, specification, frame


def test_release_reference_is_reproducible_and_never_extracts_or_runs_installer(tmp_path):
    module, archive, specification, frame = release_deriver_fixture(tmp_path)
    before = archive.read_bytes()
    result = module.derive(archive, specification)
    assert result == module.derive(archive, specification)
    assert result["inventory"]["entries"] == frame["entries"]
    assert list(tmp_path.iterdir()) == [archive] and archive.read_bytes() == before
    assert result["identity"]["normalization"] == "native-core-v2-linux-release-modes"


def test_release_derivation_preserves_sourceless_and_preexisting_empty_cache_inputs(tmp_path):
    module, archive, specification, frame = release_deriver_fixture(tmp_path, "generated")
    result = module.derive(archive, specification)
    assert result["inventory"]["entries"] == frame["entries"]
    paths = {row["path"] for row in result["inventory"]["entries"]}
    assert "lib/python3.14/__pycache__/sourceless.cpython-314.pyc" in paths
    assert "lib/python3.14/preexisting/__pycache__" in paths
    assert "lib/python3.14/__pycache__/module.cpython-314.pyc" not in paths


@pytest.mark.parametrize(
    "mutation", ["mode", "escape", "hardlink", "duplicate", "link", "archive-hash", "inventory-hash"]
)
def test_release_reference_refuses_unqualified_archive_or_expected_identity(tmp_path, mutation):
    module, archive, specification, _ = release_deriver_fixture(tmp_path, mutation)
    with pytest.raises(ValueError):
        module.derive(archive, specification)
    assert list(tmp_path.iterdir()) == [archive]


def test_release_reference_observes_bounded_derivation_deadline(tmp_path):
    module, archive, specification, _ = release_deriver_fixture(tmp_path)
    with pytest.raises(TimeoutError):
        module.derive(archive, specification, timeout=0)


@pytest.mark.parametrize("output_mode", ["fresh", "existing", "escape", "digest"])
def test_release_generator_requires_reviewed_bytes_and_fresh_owned_output(tmp_path, monkeypatch, output_mode):
    import hashlib

    module, archive, specification, _ = release_deriver_fixture(tmp_path)
    result = module.derive(archive, specification)
    expected = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode()
    specification["reference_sha256"] = hashlib.sha256(expected).hexdigest()
    spec_path = tmp_path / "spec.json"
    output = tmp_path / "reference.json"
    if output_mode == "existing":
        output.write_bytes(b"preserve existing output")
    elif output_mode == "escape":
        output = tmp_path / ".." / "outside-reference.json"
    elif output_mode == "digest":
        specification["reference_sha256"] = "0" * 64
    spec_path.write_text(json.dumps(specification), encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "SPEC", spec_path)
    monkeypatch.setattr(sys, "argv", ["derive", "--archive", str(archive), "--output", str(output)])
    if output_mode == "fresh":
        module.main()
        assert output.read_bytes() == expected
    else:
        with pytest.raises(ValueError):
            module.main()
        if output_mode == "existing":
            assert output.read_bytes() == b"preserve existing output"
        else:
            assert not output.exists()


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
    assert key != pilot.cache_identity(tmp_path, "one", "win32", "AMD64", "collection")["key"]
    assert key != pilot.cache_identity(tmp_path, "one", "win32", "AMD64", "build")["key"]
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


def test_collection_payload_never_acquires_execution_build_or_render_tools(tmp_path, monkeypatch):
    pilot = load_host_cache()
    monkeypatch.setattr(pilot, "ROOT", tmp_path)
    monkeypatch.setattr(pilot.platform, "machine", lambda: "x86_64")
    for name in pilot.INPUTS:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    monkeypatch.setattr(pilot, "runtime", lambda *a: pytest.fail("Collection acquired PowerShell"))
    monkeypatch.setattr(pilot, "node_runtime", lambda *a: pytest.fail("Collection acquired Node"))
    monkeypatch.setattr(pilot, "qualify_render", lambda *a: pytest.fail("Collection launched renderer"))
    commands = []

    def child(command, **kwargs):
        import subprocess

        commands.append(command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(pilot.subprocess, "run", child)
    monkeypatch.setattr(
        sys, "argv", ["host_cache", "bootstrap", "--payload-profile", "collection", "--source-revision", "a" * 40]
    )
    assert pilot.main() == 0
    assert len(commands) == 1 and commands[0][commands[0].index("--python-profile") + 1] == "runtime"
    assert not {"--media", "--powershell-profile", "--build-only", "--render"}.intersection(commands[0])
    result = json.loads((tmp_path / ".tmp/ci-cache-pilot/pilot.json").read_text())
    assert result["payload_profile"] == "collection" and result["exit_code"] == 0


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


def load_candidate_qualification():
    prior = sys.path[:]
    try:
        sys.path.insert(0, str(ROOT / "Tools/CI"))
        spec = importlib.util.spec_from_file_location(
            "ci_candidate_qualification", ROOT / "Tools/CI/qualify_runtime_candidate.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path[:] = prior


@pytest.mark.parametrize(
    "mutation",
    ["none", "reference", "inventory", "float-root", "root", "bool-root", "mode", "extra-change", "duplicate-change"],
)
def test_linux_v2_binding_uses_external_reference_and_exact_mode_change_receipt(mutation):
    import copy

    module = load_candidate_qualification()
    reference, inventory = module.load_linux_release_reference()
    receipt = {
        "reference": copy.deepcopy(reference),
        "source_root_mode": 0o777,
        "mode_changes": [{"path": "bin", "from": 0o777, "to": 0o755}],
    }
    candidate = copy.deepcopy(inventory)
    if mutation == "reference":
        receipt["reference"]["sha256"] = "0" * 64
    elif mutation == "inventory":
        candidate["entries"][2]["bytes"] = 0
    elif mutation == "float-root":
        candidate["root_unix_mode"] = float(candidate["root_unix_mode"])
    elif mutation == "root":
        receipt["source_root_mode"] = 0o700
    elif mutation == "bool-root":
        receipt["source_root_mode"] = True
    elif mutation == "mode":
        receipt["mode_changes"][0]["to"] = 0o644
    elif mutation == "extra-change":
        receipt["mode_changes"][0]["unknown"] = 0
    elif mutation == "duplicate-change":
        receipt["mode_changes"] *= 2
    if mutation == "none":
        module.validate_release_binding(receipt, candidate)
    else:
        with pytest.raises(ValueError):
            module.validate_release_binding(receipt, candidate)


@pytest.mark.parametrize(
    "mutation", ["checksum", "duplicate-key", "bool-revision", "identity", "inventory", "linked-reference"]
)
def test_linux_external_reference_loader_rejects_tampered_repository_declarations(tmp_path, monkeypatch, mutation):
    import hashlib
    import shutil

    module = load_candidate_qualification()
    data = tmp_path / "Tools/CI/Data"
    data.mkdir(parents=True)
    for name in (
        "runtime-versions.json",
        "python-linux-release-reference-spec.json",
        "python-linux-3.14.8-reference.json",
    ):
        shutil.copyfile(ROOT / "Tools/CI/Data" / name, data / name)
    spec_path = data / "python-linux-release-reference-spec.json"
    reference_path = data / "python-linux-3.14.8-reference.json"
    spec = json.loads(spec_path.read_text())
    reference = json.loads(reference_path.read_text())
    if mutation == "checksum":
        spec["reference_sha256"] = "0" * 64
    elif mutation == "duplicate-key":
        reference_path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        spec["reference_sha256"] = hashlib.sha256(reference_path.read_bytes()).hexdigest()
    elif mutation == "linked-reference":
        moved = data / "moved-reference.json"
        reference_path.rename(moved)
        reference_path.symlink_to(moved)
    else:
        if mutation == "bool-revision":
            reference["schema_version"] = True
        elif mutation == "identity":
            reference["identity"]["gil"] = "disabled"
        elif mutation == "inventory":
            reference["inventory"]["root_unix_mode"] = True
        reference_path.write_text(json.dumps(reference), encoding="utf-8")
        spec["reference_sha256"] = hashlib.sha256(reference_path.read_bytes()).hexdigest()
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    with pytest.raises(ValueError):
        module.load_linux_release_reference()


@pytest.mark.parametrize(
    "schema,normalization",
    [(1, "native-core-v2-linux-release-modes"), (2, "native-core-v1"), (2, "native-core-v2-linux-release-modes")],
)
def test_qualification_rejects_unbound_revision_or_reference_before_child_launch(
    tmp_path, monkeypatch, schema, normalization
):
    module = load_candidate_qualification()
    candidate, receipt = candidate_fixture(tmp_path)
    receipt.update(schema_version=schema, normalization=normalization, source_root_mode=0o755, mode_changes=[])
    reference, _ = module.load_linux_release_reference()
    receipt["reference"] = reference
    output = tmp_path / "evidence"
    output.mkdir()

    def forbidden(*args):
        raise AssertionError("Unqualified candidate must never execute")

    monkeypatch.setattr(module, "step", forbidden)
    result = module.qualify(candidate, receipt, output, "a" * 40, "fixture")
    assert result["status"] == "failed" and result["exit_code"] == 1
    assert result["processes"] == [] and not result["runtime_probe_verified"] and not result["reference_verified"]
    assert not result["saved"] and not result["handoff_admitted"] and not result["trusted_seal"]


def candidate_fixture(tmp_path):
    import hashlib
    import stat

    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "retained.txt").write_bytes(b"retained bytes")
    row = {
        "path": "retained.txt",
        "kind": "file",
        "bytes": len(b"retained bytes"),
        "sha256": hashlib.sha256(b"retained bytes").hexdigest(),
    }
    if sys.platform == "linux":
        row["unix_mode"] = stat.S_IMODE((candidate / "retained.txt").stat().st_mode)
    frame = {
        "root_unix_mode": stat.S_IMODE(candidate.stat().st_mode) if sys.platform == "linux" else None,
        "entries": [row],
    }
    inventory = {
        "schema_version": 3,
        **frame,
        "sha256": hashlib.sha256(json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(),
    }
    return candidate, {
        "contract": "ci-python-runtime-candidate",
        "schema_version": 1,
        "normalization": "native-core-v1",
        "status": "candidate-complete",
        "inventory": inventory,
        "trusted_seal": False,
        "handoff_admitted": False,
        "saved": False,
        "runtime_probe_verified": False,
    }


@pytest.mark.parametrize("mutation", ["none", "corrupt", "missing", "extra", "receipt-digest", "promotion", "mode"])
def test_candidate_validator_checks_every_byte_and_withholds_cache_trust(tmp_path, mutation):
    module = load_candidate_qualification()
    candidate, receipt = candidate_fixture(tmp_path)
    if mutation == "corrupt":
        (candidate / "retained.txt").write_bytes(b"changed bytes!")
    elif mutation == "missing":
        (candidate / "retained.txt").unlink()
    elif mutation == "extra":
        (candidate / "extra.txt").write_bytes(b"extra")
    elif mutation == "receipt-digest":
        receipt["inventory"]["sha256"] = "0" * 64
    elif mutation == "promotion":
        receipt["trusted_seal"] = True
    elif mutation == "mode" and sys.platform == "linux":
        (candidate / "retained.txt").chmod(0o700)
    elif mutation == "mode":
        receipt["inventory"]["root_unix_mode"] = 0o700
    if mutation == "none":
        assert module.validate_payload(candidate, receipt) == candidate
        assert not receipt["trusted_seal"] and not receipt["handoff_admitted"]
    else:
        with pytest.raises(ValueError):
            module.validate_payload(candidate, receipt)


def test_candidate_environment_scrubs_credentials_and_loader_inheritance(tmp_path):
    module = load_candidate_qualification()
    inherited = {
        "PATH": "system",
        "SYSTEM_ACCESSTOKEN": "sentinel",
        "GITHUB_TOKEN": "sentinel",
        "PYTHONPATH": "hostile",
        "PYTHONHOME": "hostile",
        "LD_LIBRARY_PATH": "hostile",
    }
    result = module.child_environment(tmp_path, inherited)
    assert not {"SYSTEM_ACCESSTOKEN", "GITHUB_TOKEN", "PYTHONPATH", "PYTHONHOME"}.intersection(result)
    assert result["PYTHONDONTWRITEBYTECODE"] == "1"
    if sys.platform == "linux":
        assert result["LD_LIBRARY_PATH"] == str(tmp_path / "lib")
    else:
        assert "LD_LIBRARY_PATH" not in result


def test_candidate_probe_uses_owned_process_cleanup_and_real_core_library_paths(tmp_path):
    import threading
    import time

    module = load_candidate_qualification()
    prefix, base = Path(sys.prefix), Path(sys.base_prefix)
    command = [
        str(Path(sys.executable).resolve()),
        "-I",
        "-B",
        "-c",
        module.PROBE,
        str(prefix),
        str(base),
        str(Path(sys.executable).resolve()),
        sys.version.split()[0],
        "environment",
    ]
    if importlib.util.find_spec("_ssl").origin == "built-in":
        # The local source-built WSL interpreter is not the file-backed Actions distribution.
        # Exercise fail-closed behavior; positive Linux qualification remains a hosted gate.
        with pytest.raises(RuntimeError, match="Expected file-backed qualification module"):
            module.step(
                command,
                tmp_path,
                module.child_environment(base),
                module.Lease(time.monotonic() + 30),
                threading.Event(),
            )
        evidence = json.loads(next(tmp_path.glob("process-*/process.json")).read_text(encoding="utf-8"))
        assert evidence["cleanup"]["verified"] and evidence["child_exit_code"] == 1
        return
    result, stdout = module.step(
        command, tmp_path, module.child_environment(base), module.Lease(time.monotonic() + 30), threading.Event()
    )
    probe = json.loads(stdout.read_text(encoding="utf-8"))
    assert result["cleanup"]["verified"] and result["child_exit_code"] == 0
    assert probe["core_library"] and probe["isolated"] and probe["no_bytecode"]
    assert all(Path(name).resolve().is_relative_to(base.resolve()) for name in probe["core_library"])


def test_candidate_cli_rejects_local_execution_before_opening_candidate(tmp_path, monkeypatch):
    module = load_candidate_qualification()
    monkeypatch.setenv("CAPTURE_MODE", "local")
    monkeypatch.setattr(
        sys,
        "argv",
        ["qualifier", "--candidate", str(tmp_path), "--receipt", str(tmp_path / "missing"), "--output", str(tmp_path)],
    )
    with pytest.raises(ValueError, match="explicit manual hosted"):
        module.main()


@pytest.mark.parametrize("immutable", [False, True])
def test_immutable_base_bootstrap_uses_explicit_no_bytecode_ensurepip_and_keeps_default(
    tmp_path, monkeypatch, immutable
):
    from types import SimpleNamespace

    monkeypatch.setattr(bootstrap, "ROOT", tmp_path)
    identity = {"fixture": True}
    monkeypatch.setattr(bootstrap, "python_plan", lambda *a: ({"pip": "26.2"}, identity, {}))
    monkeypatch.setattr(bootstrap, "acquire_wheels", lambda *a, **k: (["pip==26.2 --hash=sha256:fixture"], []))
    calls, creates = [], []

    class Builder:
        def __init__(self, with_pip):
            creates.append(with_pip)

        def create(self, root):
            pass

    monkeypatch.setattr(bootstrap.venv, "EnvBuilder", Builder)
    monkeypatch.setattr(bootstrap, "run", lambda command, **k: calls.append([str(x) for x in command]) or "")
    monkeypatch.setattr(bootstrap, "verify_python", lambda exe, pins, **k: {"python": "3.14.8", "probe_flags": k})
    args = SimpleNamespace(
        package_mode="source",
        python_profile="runtime",
        media=False,
        environment_id="fixture",
        offline=False,
        check=False,
        no_base_bytecode=immutable,
    )
    _, result = bootstrap.bootstrap_python(args, {"python": "3.14.8"})
    assert creates == [not immutable] and result["environment_created"]
    assert (
        all(command[1:3] == ["-I", "-B"] for command in calls)
        if immutable
        else all("-B" not in command for command in calls)
    )
    bundled = [command for command in calls if bootstrap.IMMUTABLE_PIP_BOOTSTRAP in command]
    assert len(bundled) == int(immutable)
    assert not any(command[3:5] == ["-m", "ensurepip"] for command in calls)
    assert result["probe_flags"] == ({"no_base_bytecode": True} if immutable else {})


def test_upstream_ensurepip_drops_no_bytecode_in_its_nested_interpreter():
    script = """
import ensurepip, json, subprocess
commands = []
class Result:
    returncode = 0
def capture(command, **kwargs):
    commands.append(command)
    return Result()
subprocess.run = capture
ensurepip.bootstrap(default_pip=True)
print(json.dumps(commands))
"""
    commands = json.loads(bootstrap.run([sys.executable, "-I", "-B", "-c", script]))
    assert len(commands) == 1 and "-I" in commands[0] and "-B" not in commands[0]


def test_bundled_pip_bootstrap_runs_offline_in_a_real_fresh_environment(tmp_path):
    import ensurepip
    import venv

    environment = tmp_path / "fresh"
    venv.EnvBuilder(with_pip=False).create(environment)
    executable = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    bootstrap.run([executable, "-I", "-B", "-c", bootstrap.IMMUTABLE_PIP_BOOTSTRAP], timeout=60)
    script = """
import importlib.metadata, json, pathlib, pip, sys
print(json.dumps({'version': importlib.metadata.version('pip'),
                  'origin': pip.__file__, 'prefix': sys.prefix,
                  'isolated': bool(sys.flags.isolated), 'no_bytecode': sys.dont_write_bytecode}))
"""
    proof = json.loads(bootstrap.run([executable, "-I", "-B", "-c", script], timeout=30))
    assert proof["version"] == ensurepip.version()
    assert Path(proof["prefix"]).resolve() == environment.resolve()
    assert Path(proof["origin"]).resolve().is_relative_to(environment.resolve())
    assert proof["isolated"] and proof["no_bytecode"]


@pytest.mark.parametrize("mutation", ["none", "prefix", "core", "flags", "version"])
def test_candidate_probe_admission_requires_actual_ownership_and_capability_evidence(tmp_path, mutation):
    module = load_candidate_qualification()
    value = {
        "version": "3.14.8",
        "mode": "base",
        "isolated": True,
        "no_bytecode": True,
        "prefix": str(tmp_path),
        "base_prefix": str(tmp_path),
        "executable": str(tmp_path / "python"),
        "origins": {name: str(tmp_path / name) for name in ("ssl", "sqlite3", "venv", "ensurepip", "_ssl", "_sqlite3")},
        "core_library": [str(tmp_path / "core")],
    }
    if mutation == "prefix":
        value["prefix"] = str(tmp_path.parent)
    elif mutation == "core":
        value["core_library"] = [str(tmp_path.parent / "external-core")]
    elif mutation == "flags":
        value["no_bytecode"] = 1
    elif mutation == "version":
        value["version"] = "3.14.7"
    if mutation == "none":
        assert module.admit_probe(value, tmp_path, tmp_path, tmp_path / "python", "3.14.8", "base") == value
    else:
        with pytest.raises(ValueError):
            module.admit_probe(value, tmp_path, tmp_path, tmp_path / "python", "3.14.8", "base")


@pytest.mark.parametrize("mode", ["editable", "wheel"])
def test_no_base_bytecode_rejects_unqualified_package_modes_before_acquisition(mode):
    from types import SimpleNamespace

    with pytest.raises(ValueError, match="source package mode"):
        bootstrap.bootstrap_python(SimpleNamespace(no_base_bytecode=True, package_mode=mode), {})


@pytest.mark.parametrize(
    "status,expected,code", [("exited", "failed", 1), ("cancelled", "cancelled", 130), ("timed-out", "timed-out", 124)]
)
def test_candidate_qualification_preserves_failure_cancellation_and_timeout_evidence(
    tmp_path, monkeypatch, status, expected, code
):
    module = load_candidate_qualification()
    candidate, receipt = candidate_fixture(tmp_path)
    output = tmp_path / "diagnostics"
    output.mkdir()
    process = {"status": status, "child_exit_code": 2 if status == "exited" else None, "cleanup": {"verified": True}}

    def fail(*args):
        raise module.QualificationProcessError(process)

    monkeypatch.setattr(module, "step", fail)
    result = module.qualify(candidate, receipt, output, "a" * 40, "fixture")
    assert result["status"] == expected and result["exit_code"] == code
    assert result["failed_process"] == process and result["payload_unchanged"]
    assert not result["handoff_admitted"] and not result["trusted_seal"] and not result["environment_verified"]
    assert json.loads((output / "candidate-qualification.json").read_text()) == result
