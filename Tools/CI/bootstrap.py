#!/usr/bin/env python3
"""Explicit, isolated local acquisition/build bootstrap. --check never installs anything."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import time
import tomllib
import urllib.request
import uuid
import venv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Tools/Commands/Environment"))
from dependency_requirements import IMPORT_NAMES, normalize, read_requirements  # noqa: E402

DATA = ROOT / "Tools/CI/Data"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key {key} in {path}")
            result[key] = value
        return result

    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def key_for(values):
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()[:24]


def owned_path(path):
    resolved = Path(path).resolve()
    local = (ROOT / ".local").resolve()
    if not local.is_relative_to(ROOT.resolve()) or not resolved.is_relative_to(local):
        raise ValueError(f"Bootstrap destination escapes owned .local storage: {path}")
    return resolved


def clean_environment():
    blocked = {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "PIP_CONFIG_FILE", "NODE_OPTIONS", "NODE_PATH"}
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in blocked and not key.startswith(("PIP_", "PUPPETEER_", "NPM_CONFIG_"))
    }
    environment.update(
        PYTHONNOUSERSITE="1",
        PYTHONUTF8="1",
        PIP_CONFIG_FILE=os.devnull,
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_NO_INDEX="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
        NPM_CONFIG_USERCONFIG=os.devnull,
        NPM_CONFIG_GLOBALCONFIG=os.devnull,
    )
    return environment


def run(command, *, cwd=ROOT, environment=None, timeout=600):
    result = subprocess.run(
        [str(item) for item in command],
        cwd=cwd,
        env=environment or clean_environment(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def package_metadata():
    with (ROOT / "pyproject.toml").open("rb") as stream:
        metadata = tomllib.load(stream)
    runtime, _ = read_requirements(ROOT / "requirements-python.txt", ROOT)
    bounds = {}
    for requirement in metadata["project"]["dependencies"]:
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)>=(\d+(?:\.\d+)*),<(\d+(?:\.\d+)*)", requirement)
        if match is None:
            raise ValueError("Unsupported runtime compatibility-bound grammar")
        name, lower, upper = match.groups()
        bounds[normalize(name)] = (lower, upper)
    if set(runtime) != set(bounds) or any(
        not tuple(map(int, low.split(".")))
        <= tuple(map(int, runtime[name].split(".")))
        < tuple(map(int, high.split(".")))
        for name, (low, high) in bounds.items()
    ):
        raise ValueError("Runtime pins and package dependency metadata require coordinated review")
    build, _ = read_requirements(ROOT / "requirements-python-build.txt", ROOT)
    if metadata["build-system"]["requires"] != ["setuptools==" + build["setuptools"]]:
        raise ValueError("Unexpected build-system dependency; update the exact build graph together")
    files = read_json(DATA / "python-package-files.json")["files"]
    source = ROOT / "Tools/Runtime/Python/knowledge_framework"
    if sorted(path.name for path in source.glob("*.py")) != sorted(files):
        raise ValueError("Runtime source files differ from the reviewed package allowlist")
    return metadata, files


def source_version():
    tree = ast.parse((ROOT / "Tools/Runtime/Python/knowledge_framework/_version.py").read_text())
    return next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets)
    )


def python_plan(profile, include_media, versions):
    pins, inputs = read_requirements(ROOT / versions["python_declarations"][profile], ROOT)
    # Every selected environment installs the exact pip; build tools only enter build/editable modes.
    pins["pip"] = versions["pip"]
    if include_media:
        media, declarations = read_requirements(ROOT / versions["python_declarations"]["media"], ROOT)
        pins.update(media)
        inputs.update(declarations)
    lock = read_json(DATA / "python-wheel-lock.json")
    if lock["schema_version"] != 1:
        raise ValueError("Unsupported Python wheel lock")
    for name, version in pins.items():
        if lock["packages"].get(name, {}).get("version") != version:
            raise ValueError(f"Missing/mismatched wheel lock for {name} {version}")
    identity = {
        "schema": 1,
        "os": sys.platform,
        "architecture": platform.machine().lower(),
        "python": versions["python"],
        "pins": pins,
        "inputs": inputs,
        "wheel_lock": digest(DATA / "python-wheel-lock.json"),
    }
    return pins, identity, lock


def wheel_for(entry):
    suffix = "-win_amd64.whl" if sys.platform == "win32" else "x86_64.whl"
    matches = [
        row for row in entry["files"] if row["filename"].endswith("-any.whl") or row["filename"].endswith(suffix)
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one approved wheel for current platform, found {len(matches)}")
    row = matches[0]
    if Path(row["filename"]).name != row["filename"] or not row["filename"].endswith(".whl"):
        raise ValueError("Unsafe wheel-lock filename")
    if not row["url"].startswith("https://files.pythonhosted.org/"):
        raise ValueError("Wheel acquisition must use the approved PyPI file origin")
    return row


def acquire_wheels(pins, cache, lock, *, offline, check):
    rows = []
    missing = []
    for name in sorted(pins):
        row = wheel_for(lock["packages"][name])
        path = owned_path(cache / row["filename"])
        if path.exists():
            if digest(path) != row["sha256"]:
                raise ValueError(
                    f"Corrupt cached wheel: {path}; inspect/remove that owned payload and reacquire explicitly"
                )
        else:
            missing.append(name)
            if offline or check:
                raise ValueError(f"Approved wheel unavailable offline: {path}; run explicit online bootstrap first")
            cache.mkdir(parents=True, exist_ok=True)
            partial = owned_path(path.with_suffix(".part"))
            with urllib.request.urlopen(row["url"], timeout=60) as response:
                partial.write_bytes(response.read())
            if digest(partial) != row["sha256"]:
                raise ValueError(f"Downloaded wheel digest mismatch: {row['filename']}")
            partial.replace(path)
        rows.append(f"{name}=={pins[name]} --hash=sha256:{row['sha256']}")
    return rows, missing


def verify_python(executable, pins):
    script = """
import importlib, importlib.metadata as md, json, pathlib, sys
pins = json.loads(sys.argv[1])
names = json.loads(sys.argv[2])
prefix = pathlib.Path(sys.prefix).resolve()
result = []
for name, version in sorted(pins.items()):
    distribution = md.distribution(name)
    assert distribution.version == version, (name, distribution.version, version)
    module = importlib.import_module(names.get(name, name.replace('-', '_')))
    origin = pathlib.Path(module.__file__).resolve()
    assert origin.is_relative_to(prefix), (name, str(origin), str(prefix))
    for file in distribution.files or []:
        if file.hash and file.hash.mode == 'sha256':
            import base64, hashlib
            location = pathlib.Path(distribution.locate_file(file)).resolve()
            assert location.is_relative_to(prefix), str(location)
            actual = base64.urlsafe_b64encode(hashlib.sha256(location.read_bytes()).digest()).rstrip(b'=').decode()
            assert actual == file.hash.value, (name, str(file), 'installed file digest mismatch')
    result.append({'name': name, 'version': version, 'origin': str(origin)})
print(json.dumps({'python': sys.version.split()[0], 'executable': sys.executable,
                  'prefix': str(prefix), 'packages': result}))
"""
    return json.loads(run([executable, "-I", "-c", script, json.dumps(pins), json.dumps(IMPORT_NAMES)]))


def bootstrap_python(args, versions):
    profile = "build" if args.package_mode in {"editable", "wheel"} else args.python_profile
    pins, identity, lock = python_plan(profile, args.media, versions)
    if profile == "build" and not args.build_only:
        runtime, declarations = read_requirements(ROOT / "requirements-python.txt", ROOT)
        pins.update(runtime)
        identity["pins"], identity["runtime_inputs"] = pins, declarations
    key = key_for(identity)
    cache = owned_path(ROOT / ".local/ci-cache/python" / key)
    environment_key = key_for({"identity": identity, "package_mode": args.package_mode})
    environment_root = owned_path(ROOT / ".local/ci-environments/python" / environment_key / args.environment_id)
    executable = environment_root / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    start = time.perf_counter()
    rows, missing = acquire_wheels(pins, cache, lock, offline=args.offline, check=args.check)
    acquisition = time.perf_counter() - start
    if environment_root.exists() and not (environment_root / "bootstrap-owner.json").is_file():
        raise ValueError(f"Refusing unowned existing environment: {environment_root}")
    installed = False
    if not executable.exists():
        if args.check:
            raise ValueError(f"Environment missing: {environment_root}; run explicit bootstrap")
        environment_root.mkdir(parents=True, exist_ok=True)
        (environment_root / "bootstrap-owner.json").write_text(json.dumps(identity, sort_keys=True), encoding="utf-8")
        venv.EnvBuilder(with_pip=True).create(environment_root)
        requirements = owned_path(environment_root / "locked-requirements.txt")
        requirements.write_text("\n".join(rows) + "\n", encoding="utf-8")
        run(
            [
                executable,
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-index",
                "--find-links",
                cache,
                "--only-binary=:all:",
                "--require-hashes",
                "-r",
                requirements,
            ]
        )
        installed = True
    if read_json(environment_root / "bootstrap-owner.json") != identity:
        raise ValueError("Environment owner/declaration provenance mismatch")
    start = time.perf_counter()
    verified = verify_python(executable, pins)
    if verified["python"] != versions["python"]:
        raise ValueError("Isolated interpreter version mismatch")
    run([executable, "-m", "pip", "check"])
    verified.update(
        key=key,
        acquisition_seconds=acquisition,
        verify_seconds=time.perf_counter() - start,
        acquired=missing,
        environment_created=installed,
        declaration_identity=identity,
    )
    return executable, verified


def build_package(args, executable, metadata, files):
    if args.check:
        if args.build_only:
            result = read_json(executable.parent.parent / "package-build.json")
            wheel = owned_path(result["wheel"])
            if digest(wheel) != result["sha256"]:
                raise ValueError("Built wheel digest differs from its owned provenance")
            return {**result, "build_skipped": True}
        probe = (
            "import importlib.metadata as m,knowledge_framework as k,json; "
            "print(json.dumps({'version':m.version('knowledge-framework'),'source_version':k.__version__,'origin':k.__file__}))"
        )
        result = json.loads(run([executable, "-I", "-c", probe], cwd=ROOT / ".local"))
        if result["version"] != source_version() or result["source_version"] != source_version():
            raise ValueError("Installed package version mismatch")
        origin = Path(result["origin"]).resolve()
        expected_root = ROOT / "Tools/Runtime/Python" if args.package_mode == "editable" else executable.parent.parent
        if not origin.is_relative_to(expected_root.resolve()):
            raise ValueError("Installed package origin does not match requested mode")
        return {"mode": args.package_mode, "build_skipped": True, **result}
    run_id = uuid.uuid4().hex
    owner = owned_path(ROOT / ".local/ci-build" / run_id)
    source = owner / "source"
    package = source / "Tools/Runtime/Python/knowledge_framework"
    package.mkdir(parents=True)
    for name in files:
        shutil.copy2(ROOT / "Tools/Runtime/Python/knowledge_framework" / name, package / name)
    for name in ("pyproject.toml", "LICENSE"):
        shutil.copy2(ROOT / name, source / name)
    environment = clean_environment()
    environment["SOURCE_DATE_EPOCH"] = "1767225600"
    artifacts = owner / "artifacts"
    run(
        [executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", artifacts, source],
        cwd=owner,
        environment=environment,
    )
    wheels = list(artifacts.glob("*.whl"))
    if len(wheels) != 1:
        raise ValueError("Build must produce exactly one wheel")
    wheel = wheels[0]
    if args.build_only:
        result = {
            "mode": "build-only",
            "version": source_version(),
            "wheel": str(wheel),
            "sha256": digest(wheel),
            "source_revision": args.source_revision,
            "source_modified": args.source_modified,
            "build_inputs": {name: digest(ROOT / name) for name in ("pyproject.toml", "LICENSE")},
            "source_inputs": {name: digest(package / name) for name in files},
        }
        (owner / "build-provenance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        (executable.parent.parent / "package-build.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    if args.package_mode == "editable":
        run([executable, "-m", "pip", "install", "--no-index", "--no-deps", "--no-build-isolation", "-e", ROOT])
    else:
        run([executable, "-m", "pip", "install", "--no-index", "--no-deps", "--force-reinstall", wheel])
    probe = (
        "import importlib.metadata as m,knowledge_framework as k,json; "
        "print(json.dumps({'version':m.version('knowledge-framework'),'source_version':k.__version__,'origin':k.__file__}))"
    )
    result = json.loads(run([executable, "-I", "-c", probe], cwd=owner))
    if result["version"] != result["source_version"] or result["version"] != source_version():
        raise ValueError("Package version authority/installed metadata mismatch")
    expected_root = ROOT / "Tools/Runtime/Python" if args.package_mode == "editable" else executable.parent.parent
    if not Path(result["origin"]).resolve().is_relative_to(expected_root.resolve()):
        raise ValueError("Package installation resolved outside expected environment/source")
    result.update(
        mode=args.package_mode,
        source_revision=args.source_revision,
        source_modified=args.source_modified,
        build_inputs={name: digest(ROOT / name) for name in ("pyproject.toml", "LICENSE")},
        wheel=str(wheel),
        sha256=digest(wheel),
        source_inputs={name: digest(package / name) for name in files},
    )
    (owner / "build-provenance.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def tree_manifest(path):
    return {file.relative_to(path).as_posix(): digest(file) for file in sorted(path.rglob("*")) if file.is_file()}


def bootstrap_powershell(args, versions):
    host = shutil.which(args.pwsh)
    if host is None:
        raise ValueError(f"PowerShell executable unavailable: {args.pwsh}")
    expected = versions["powershell_floor"] if args.floor else versions["powershell"]
    host_probe = json.loads(
        run(
            [
                host,
                "-NoProfile",
                "-Command",
                "@{edition=$PSVersionTable.PSEdition;version=$PSVersionTable.PSVersion.ToString()}"
                " | ConvertTo-Json -Compress",
            ]
        )
    )
    if host_probe != {"edition": "Core", "version": expected}:
        raise ValueError(f"Expected exact Core {expected}, found {host_probe}")
    declaration = versions["powershell_declarations"][args.powershell_profile]
    inputs = {name: digest(ROOT / name) for name in versions["powershell_declarations"].values()}
    key = key_for({"schema": 1, "os": sys.platform, "architecture": platform.machine(), "inputs": inputs})
    cache = owned_path(ROOT / ".local/ci-cache/powershell" / key)
    modules = cache / "modules"
    receipt = cache / "content-sha256.json"
    start = time.perf_counter()
    hit = receipt.exists()
    if hit:
        if read_json(receipt) != tree_manifest(modules):
            raise ValueError(f"Corrupt PowerShell module cache: {cache}")
    else:
        if args.offline or args.check:
            raise ValueError(f"Module cache unavailable offline: {cache}; run explicit online bootstrap")
        run(
            [
                host,
                "-NoProfile",
                "-File",
                ROOT / "Tools/CI/Install-PowerShellRequirements.ps1",
                "-Destination",
                modules,
                "-RequirementsPath",
                versions["powershell_declarations"]["development"],
            ]
        )
        receipt.write_text(json.dumps(tree_manifest(modules), indent=2), encoding="utf-8")
    environment = clean_environment()
    builtin = Path(host).parent / "Modules"
    environment["PSModulePath"] = str(modules) + os.pathsep + str(builtin)
    result = json.loads(
        run(
            [
                host,
                "-NoProfile",
                "-File",
                ROOT / "Tools/CI/Probe-PowerShellModules.ps1",
                "-RequirementsPath",
                declaration,
            ],
            environment=environment,
        )
    )
    for module in result["modules"]:
        if not Path(module["path"]).resolve().is_relative_to(modules.resolve()):
            raise ValueError(f"Module resolved outside owned cache: {module}")
    result.update(
        key=key,
        cache_hit=hit,
        elapsed_seconds=time.perf_counter() - start,
        module_path=environment["PSModulePath"],
        content_sha256=digest(receipt),
    )
    return result


def bootstrap_render(args, versions):
    node, npm = shutil.which("node"), shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if node is None or npm is None:
        raise ValueError("Exact Node/npm unavailable; install the declared runtime before bootstrap")
    if run([node, "--version"]).strip() != "v" + versions["node"] or run([npm, "--version"]).strip() != versions["npm"]:
        raise ValueError("Node/npm do not match adopted exact versions")
    manifest = read_json(ROOT / "Tools/CI/Node/package.json")
    if manifest["engines"] != {"node": versions["node"], "npm": versions["npm"]}:
        raise ValueError("Node engine declaration and runtime baseline disagree")
    declared = set((ROOT / "requirements-node.txt").read_text().splitlines())
    if {f"{name}@{version}" for name, version in manifest["dependencies"].items()} != declared:
        raise ValueError("Node package manifest and direct declarations disagree")
    identity = {
        "schema": 2,
        "os": sys.platform,
        "architecture": platform.machine(),
        "node": versions["node"],
        "npm": versions["npm"],
        "browser": "chrome",
        "browser_version": versions["chrome"],
        "lock": digest(ROOT / "Tools/CI/Node/package-lock.json"),
    }
    key = key_for(identity)
    owner = owned_path(ROOT / ".local/ci-environments/render" / key / args.environment_id)
    cache = owned_path(ROOT / ".local/ci-cache/npm" / key)
    browsers = owned_path(ROOT / ".local/ci-cache/browsers" / key)
    environment = clean_environment()
    environment.update(
        PUPPETEER_CACHE_DIR=str(browsers),
        PUPPETEER_SKIP_DOWNLOAD="true",
        PUPPETEER_FIREFOX_SKIP_DOWNLOAD="true",
        PUPPETEER_CHROME_HEADLESS_SHELL_SKIP_DOWNLOAD="true",
        PUPPETEER_BROWSER="chrome",
        PUPPETEER_CHROME_VERSION=versions["chrome"],
    )
    start = time.perf_counter()
    present = (owner / "node_modules/puppeteer/package.json").exists()
    configuration = (
        "module.exports={cacheDirectory:process.env.PUPPETEER_CACHE_DIR,defaultBrowser:'chrome',"
        "chrome:{version:process.env.PUPPETEER_CHROME_VERSION,skipDownload:true},"
        "'chrome-headless-shell':{skipDownload:true},firefox:{skipDownload:true}};\n"
    )
    if not present:
        if args.check:
            raise ValueError("Render environment missing; run explicit bootstrap")
        owner.mkdir(parents=True, exist_ok=True)
        for name in ("package.json", "package-lock.json"):
            shutil.copy2(ROOT / "Tools/CI/Node" / name, owner / name)
        (owner / ".puppeteerrc.cjs").write_text(configuration, encoding="utf-8")
        command = [npm, "ci", "--cache", cache, "--no-audit", "--no-fund"]
        if args.offline:
            command.append("--offline")
        run(command, cwd=owner, environment=environment)
    if digest(owner / "package-lock.json") != identity["lock"]:
        raise ValueError("Installed render lock provenance mismatch")
    if (owner / ".puppeteerrc.cjs").read_text(encoding="utf-8") != configuration:
        raise ValueError("Owned Chrome-only Puppeteer configuration differs from the reviewed policy")
    receipt = owner / "content-sha256.json"
    if present:
        if not receipt.exists() or read_json(receipt) != tree_manifest(owner / "node_modules"):
            raise ValueError("Render dependency content changed; inspect the owned environment before repair")
    else:
        receipt.write_text(json.dumps(tree_manifest(owner / "node_modules"), sort_keys=True), encoding="utf-8")
    script = """
const fs=require('fs'); const p=require('puppeteer');
(async()=>{const path=await p.executablePath();
if(!fs.existsSync(path)) throw new Error('Pinned browser unavailable; run online browser bootstrap');
const b=await p.launch({browser:'chrome',headless:true,args:process.platform==='linux'?['--no-sandbox']:[]});
const page=await b.newPage(); await page.setContent('<p>bootstrap</p>');
if(await page.$eval('p',e=>e.textContent)!=='bootstrap') throw new Error('Browser smoke failed');
console.log(JSON.stringify({puppeteer:require('puppeteer/package.json').version,browser:await b.version(),path}));
await b.close();})().catch(e=>{console.error(e);process.exit(1)});
"""
    # Browser download is explicit acquisition; execution/check/offline never triggers an installer.
    browser_path = run(
        [node, "-e", "Promise.resolve(require('puppeteer').executablePath()).then(p=>console.log(p))"],
        cwd=owner,
        environment=environment,
    ).strip()
    if not Path(browser_path).is_file():
        if args.offline or args.check:
            raise ValueError("Pinned browser unavailable offline; run explicit online render bootstrap")
        install_chrome = """
import('@puppeteer/browsers').then(async b=>{
await b.install({browser:b.Browser.CHROME,buildId:process.env.PUPPETEER_CHROME_VERSION,
cacheDir:process.env.PUPPETEER_CACHE_DIR,platform:b.detectBrowserPlatform(),installDeps:false});
}).catch(e=>{console.error(e);process.exit(1)});
"""
        run([node, "-e", install_chrome], cwd=owner, environment=environment)
    browser_receipt = browsers / "content-sha256.json"
    browser_files = {
        file.relative_to(browsers).as_posix(): digest(file)
        for file in sorted(browsers.rglob("*"))
        if file.is_file() and file != browser_receipt
    }
    if browser_receipt.exists():
        if read_json(browser_receipt) != browser_files:
            raise ValueError("Pinned browser cache content digest mismatch")
    elif args.offline or args.check:
        raise ValueError("Browser cache provenance missing; run explicit online acquisition")
    else:
        browser_receipt.write_text(json.dumps(browser_files, sort_keys=True), encoding="utf-8")
    result = json.loads(run([node, "-e", script], cwd=owner, environment=environment))
    result.update(
        key=key,
        environment=str(owner),
        npm_cache=str(cache),
        browser_cache=str(browsers),
        environment_hit=present,
        elapsed_seconds=time.perf_counter() - start,
        mmdc=str(owner / "node_modules/.bin" / ("mmdc.cmd" if os.name == "nt" else "mmdc")),
    )
    if result["puppeteer"] != manifest["dependencies"]["puppeteer"]:
        raise ValueError("Installed Puppeteer version mismatch")
    if result["browser"] != "Chrome/" + versions["chrome"]:
        raise ValueError("Installed browser version does not match the pinned Chrome release")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-profile", choices=("runtime", "development", "build", "none"), default="development")
    parser.add_argument("--package-mode", choices=("source", "editable", "wheel"), default="source")
    parser.add_argument("--media", action="store_true")
    parser.add_argument("--powershell-profile", choices=("runtime", "development"))
    parser.add_argument("--pwsh", default="pwsh")
    parser.add_argument("--floor", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--environment-id", default="primary")
    parser.add_argument("--source-revision")
    parser.add_argument("--source-modified", action="store_true")
    parser.add_argument("--actionlint", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    started = time.perf_counter()
    report = {"schema_version": 1, "status": "failed", "check_only": args.check, "offline": args.offline}
    try:
        if args.build_only and args.package_mode != "wheel":
            raise ValueError("--build-only requires --package-mode wheel")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", args.environment_id):
            raise ValueError("Environment ID must be a bounded lowercase owned label")
        versions = read_json(DATA / "runtime-versions.json")
        if versions["schema_version"] != 1 or sys.platform not in {"win32", "linux"}:
            raise ValueError("Unsupported bootstrap schema or operating system")
        if args.source_revision and not re.fullmatch(r"[0-9a-f]{40}", args.source_revision):
            raise ValueError("Source revision must be the verified full Git commit ID supplied by the build owner")
        if (
            sys.version.split()[0] != versions["python"]
            or platform.machine().lower() not in {"amd64", "x86_64"}
            or sys.implementation.name != "cpython"
            or sysconfig.get_config_var("Py_GIL_DISABLED")
        ):
            raise ValueError(f"Bootstrap requires adopted CPython {versions['python']} x64; found {sys.version}")
        errors = []
        if args.python_profile != "none":
            try:
                metadata, files = package_metadata()
                executable, report["python"] = bootstrap_python(args, versions)
                if args.package_mode != "source":
                    report["package"] = build_package(args, executable, metadata, files)
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                errors.append({"unit": "python", "error": str(error)})
        elif args.package_mode != "source":
            raise ValueError("Package build requires a Python environment")
        for selected, name, operation in (
            (args.powershell_profile, "powershell", bootstrap_powershell),
            (args.render, "render", bootstrap_render),
        ):
            if selected:
                try:
                    report[name] = operation(args, versions)
                except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                    errors.append({"unit": name, "error": str(error)})
        if args.actionlint:
            try:
                tool = shutil.which("actionlint")
                if not tool or run([tool, "--version"], timeout=15).splitlines()[0] != versions["actionlint"]:
                    raise ValueError(
                        "Exact actionlint missing/unusable; acquire the approved standalone tool explicitly"
                    )
                report["actionlint"] = {"version": versions["actionlint"], "path": tool, "sha256": digest(tool)}
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                errors.append({"unit": "actionlint", "error": str(error)})
        report["status"] = "failed" if errors else "passed"
        if errors:
            report["errors"] = errors
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        report["error"] = str(error)
    report["elapsed_seconds"] = time.perf_counter() - started
    if args.report:
        output = args.report.resolve()
        if not output.is_relative_to((ROOT / ".tmp").resolve()) and not output.is_relative_to(
            (ROOT / ".local").resolve()
        ):
            raise ValueError("Bootstrap reports must use owned ignored .tmp/.local destinations")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    else:
        print(f"Bootstrap {report['status']}: {report['elapsed_seconds']:.3f}s")
        for name in ("python", "package", "powershell", "render", "actionlint"):
            if name in report:
                print(f"  {name}: verified")
        for error in report.get("errors", []):
            print(f"  {error['unit']}: {error['error']}")
        if "error" in report:
            print(report["error"])
        if args.report:
            print(f"Report: {args.report}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
