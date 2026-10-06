"""Fixed layer adapters over captured source; owner JSON/native contracts remain authoritative."""

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

from process_supervisor import Lease, run_process
from native_results import parse_junit, validate_phase, classify
from execution_reports import excerpt


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate result key: " + key)
            result[key] = value
        return result

    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def guarded_manifest(root, snapshot):
    """Every captured source byte is protected, including authored content and current projections."""
    found = set()
    for directory, folders, files in os.walk(root, followlinks=False):
        for name in folders + files:
            path = Path(directory) / name
            if path.is_symlink() or path.is_junction() or not path.resolve().is_relative_to(root):
                raise ValueError("Execution source/output link escape")
        if Path(directory) == root:
            folders[:] = [name for name in folders if name not in {".tmp", ".local", ".git"}]
        found.update((Path(directory) / name).relative_to(root).as_posix() for name in files)
    changed = sorted(found ^ set(snapshot.files))
    for name in sorted(found & set(snapshot.files)):
        path = root / name
        if path.read_bytes() != snapshot.files[name]:
            changed.append(name)
        if os.name != "nt" and bool(path.stat().st_mode & 0o111) != (snapshot.modes[name] == "100755"):
            changed.append(name)
    if changed:
        raise ValueError("Protected execution source changed: " + ", ".join(dict.fromkeys(changed)))
    return snapshot.digest


def typed_equal(left, right):
    """Exact semantic equality: JSON types, keys and ordered arrays; no operational fields guessed away."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(typed_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(typed_equal(a, b) for a, b in zip(left, right))
    return left == right


def conformance_result(document, identity):
    if (
        not isinstance(document, dict)
        or type(document.get("schema_version")) is not int
        or document["schema_version"] != 1
    ):
        raise ValueError("Wrong conformance envelope")
    rows = document.get("suites")
    if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("id") != identity:
        raise ValueError("Wrong/empty conformance inventory")
    for key in ("suite_count", "passed", "failed"):
        if type(document.get(key)) is not int or document[key] < 0:
            raise ValueError("Invalid conformance counts")
    passed = rows[0].get("status") == "passed"
    if document["suite_count"] != 1 or document["passed"] != int(passed) or document["failed"] != int(not passed):
        raise ValueError("Conformance count/status mismatch")
    if passed and not isinstance(rows[0].get("summary"), dict):
        raise ValueError("Missing semantic conformance summary")
    return passed, rows[0]


def compatibility_result(document, identity):
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != 1
        or type(document.get("schema_version")) is not int
    ):
        raise ValueError("Wrong compatibility envelope")
    if document.get("requested_checks") != [identity] or document.get("canonical_outputs_unchanged") is not True:
        raise ValueError("Wrong compatibility inventory or unverified canonical guard")
    rows = document.get("checks")
    if not isinstance(rows, list) or len(rows) != 1 or rows[0].get("id") != identity:
        raise ValueError("Missing/extra compatibility check evidence")
    passed = rows[0].get("status") == "passed"
    if type(document.get("passed")) is not int or type(document.get("failed")) is not int:
        raise ValueError("Invalid compatibility counts")
    if (
        document["passed"] != int(passed)
        or document["failed"] != int(not passed)
        or document.get("status") != ("passed" if passed else "failed")
    ):
        raise ValueError("Compatibility count/status mismatch")
    return passed


def format_representation(snapshot_kind):
    if snapshot_kind in {"commit", "index"}:
        return "GitBlob"
    if snapshot_kind == "worktree":
        return "Worktree"
    raise ValueError("Unknown captured-source representation")


def owning_failure_reasons(document, adapter):
    """Promote owner diagnostics without changing retained evidence or its pass/fail contract."""
    if adapter == "powershell-format":
        details = [
            f"PowerShell formatting: {document.get('files_changed')} changed files; "
            f"{document.get('long_lines')} long lines."
        ]
        for row in document.get("files", []):
            if row.get("changed") or row.get("long_lines"):
                details.append(f"{row.get('path')}: changed={row.get('changed')}; long_lines={row.get('long_lines')}")
    else:
        rows = document.get("checks" if adapter == "compatibility" else "suites", [])
        details = [row.get("error") for row in rows if row.get("status") != "passed" and row.get("error")]
    if not details and document.get("error"):
        details = [document["error"]]
    if not details:
        return []
    text, truncated = excerpt("\n".join(str(detail) for detail in details))
    return [text + ("\n[Truncated; complete owner JSON and process streams retained.]" if truncated else "")]


class AdapterSession:
    def __init__(
        self,
        root,
        snapshot,
        output,
        executables,
        module_root=None,
        wheel=None,
        runtime_wheel=None,
        source_representation="Worktree",
        render_report=None,
    ):
        self.root, self.snapshot, self.output = Path(root), snapshot, Path(output)
        self.executables = {key: str(Path(value).resolve()) for key, value in executables.items() if value}
        self.module_root, self.wheel, self.runtime_wheel = module_root, wheel, runtime_wheel
        if source_representation not in {"Worktree", "GitBlob"}:
            raise ValueError("Unknown formatter source representation")
        self.source_representation = source_representation
        self.render_report = render_report
        names = ("SystemRoot", "SystemDrive", "ProgramData", "WINDIR", "TEMP", "TMP", "HOME", "LANG", "PATH", "PATHEXT")
        self.env = {name: os.environ[name] for name in names if name in os.environ}
        self.env.update(
            PYTHONUTF8="1",
            PYTHONNOUSERSITE="1",
            PYTHONDONTWRITEBYTECODE="1",
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
            PIP_NO_INDEX="1",
            GIT_TERMINAL_PROMPT="0",
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            RUFF_CACHE_DIR=str(self.root / ".tmp/ruff-cache"),
        )
        if module_root:
            self.env["PSModulePath"] = str(Path(module_root).resolve())
        prefixes = [str(Path(value).parent) for value in self.executables.values()]
        self.env["PATH"] = os.pathsep.join(prefixes + [self.env.get("PATH", "")])
        self.inventory = {}
        self.readiness = {}
        self.containment_verified = True

    def request(self, directory, mode, **values):
        path = directory / "request.json"
        path.write_text(json.dumps({"mode": mode, "root": str(self.root), **values}), encoding="utf-8")
        return path

    def launch(self, command, directory, lease, cancel=None):
        environment = {**self.env, "LOTM_CI_UNIT_DEADLINE": str(lease.deadline)}
        result = run_process(
            command,
            cwd=self.root,
            env=environment,
            output_parent=directory,
            lease=lease,
            termination=0.5,
            cleanup=3,
            cancel=cancel,
        )
        self.containment_verified = self.containment_verified and result["cleanup"]["verified"]
        return result

    def preflight(self, rows, versions, cancel=None):
        needs_python = bool(rows)
        adapters = {row["adapter"] for row in rows}
        wants_ps = any("powershell7" in row["runtimes"] for row in rows) or any(
            row["execution_id"].endswith("::powershell7") for row in rows
        )
        for runtime in ("python", "powershell7", "actionlint"):
            if not {"python": needs_python, "powershell7": wants_ps, "actionlint": "actionlint" in adapters}[runtime]:
                continue
            directory = self.output / ("preflight-" + runtime)
            directory.mkdir()
            try:
                executable = self.executables.get(runtime)
                if not executable or not Path(executable).is_file():
                    raise ValueError("Explicit executable unavailable")
                if runtime == "python":
                    packages = {"pyyaml": "6.0.3"}
                    if "pytest" in adapters:
                        packages.update(pytest="9.1.1", pillow="12.3.0")
                    if "ruff" in adapters:
                        packages["ruff"] = "0.16.1"
                    request = self.request(
                        directory,
                        "python-preflight",
                        version=versions["python"],
                        packages=packages,
                        imports={"pyyaml": "yaml", "pillow": "PIL"},
                    )
                    command = [executable, "-I", "-B", str(self.root / "Tools/CI/adapter_worker.py"), str(request)]
                elif runtime == "powershell7":
                    packages = {"powershell-yaml": "0.4.12"}
                    if "pester" in adapters:
                        packages["Pester"] = "6.2.0"
                    if "powershell-format" in adapters or "pester" in adapters:
                        packages["PSScriptAnalyzer"] = "1.25.0"
                    if not self.module_root:
                        raise ValueError("Owned module root required")
                    module_root = Path(self.module_root).resolve()
                    receipt = read_json(module_root.parent / "content-sha256.json")
                    files = {
                        path.relative_to(module_root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in module_root.rglob("*")
                        if path.is_file()
                    }
                    if files != receipt:
                        raise ValueError("Owned module content differs from bootstrap receipt")
                    request = self.request(
                        directory,
                        "powershell-preflight",
                        version=versions["powershell"],
                        packages=packages,
                        module_root=str(Path(self.module_root).resolve()),
                    )
                    command = [
                        executable,
                        "-NoProfile",
                        "-File",
                        str(self.root / "Tools/CI/Invoke-CiAdapter.ps1"),
                        "-Request",
                        str(request),
                    ]
                else:
                    command = [executable, "-version"]
                process = self.launch(command, directory, Lease(time.monotonic() + 30), cancel)
                if (
                    process["status"] != "exited"
                    or process["child_exit_code"] != 0
                    or not process["cleanup"]["verified"]
                ):
                    raise ValueError("Owned prerequisite probe failed: " + str(process["diagnostics"]))
                text = Path(process["directory"], "stdout.bin").read_text(encoding="utf-8-sig")
                document = (
                    json.loads(text)
                    if runtime != "actionlint"
                    else {"status": "passed", "version": text.splitlines()[0]}
                )
                if document.get("status") != "passed" or (
                    runtime == "actionlint" and document["version"] != versions["actionlint"]
                ):
                    raise ValueError("Pinned prerequisite probe failed")
                self.readiness[runtime] = True
                self.inventory[runtime] = {
                    "status": "verified",
                    "version": document["version"],
                    "packages": document.get("packages", {}),
                    "executable": runtime + "-explicit",
                    "executable_sha256": hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
                }
            except Exception as error:
                self.readiness[runtime] = False
                self.inventory[runtime] = {
                    "status": "unavailable",
                    "error": str(error),
                    "executable": runtime + "-explicit",
                }
        if any(row["execution_id"].startswith("compatibility/render::") for row in rows):
            self.preflight_render(versions, cancel)

    def preflight_render(self, versions, cancel=None):
        directory = self.output / "preflight-render"
        directory.mkdir()
        try:
            import bootstrap

            if not self.render_report:
                raise ValueError("Explicit --render-bootstrap-report required; run pinned render bootstrap first")
            document = read_json(self.render_report)
            if document.get("status") != "passed":
                raise ValueError("Render bootstrap report did not pass")
            render = document["render"]
            owner, cache = Path(render["environment"]).resolve(), Path(render["browser_cache"]).resolve()
            key = render["key"]
            if not re.fullmatch(r"[0-9a-f]{24}", key):
                raise ValueError("Invalid render cache key")
            local = owner.parents[3]
            if (
                local.name != ".local"
                or owner.parent != local / "ci-environments/render" / key
                or cache != local / "ci-cache/browsers" / key
            ):
                raise ValueError("Render paths do not belong to matching owned environment/cache")
            for path in (owner, cache):
                if any(item.is_symlink() or item.is_junction() for item in (path, *path.parents)):
                    raise ValueError("Render ownership traverses a link")
            manifest = read_json(self.root / "Tools/CI/Node/package.json")
            identity = {
                "schema": 2,
                "os": sys.platform,
                "architecture": __import__("platform").machine(),
                "node": versions["node"],
                "npm": versions["npm"],
                "browser": "chrome",
                "browser_version": versions["chrome"],
                "lock": bootstrap.digest(self.root / "Tools/CI/Node/package-lock.json"),
            }
            if key != bootstrap.key_for(identity):
                raise ValueError("Render cache key differs from captured runtime/lock identity")
            if (owner / ".puppeteerrc.cjs").read_text() != bootstrap.render_configuration():
                raise ValueError("Owned Chrome-only configuration changed")
            if read_json(owner / "package.json") != manifest or bootstrap.digest(owner / "package-lock.json") != (
                bootstrap.digest(self.root / "Tools/CI/Node/package-lock.json")
            ):
                raise ValueError("Render package/lock differs from captured declarations")
            if read_json(owner / "content-sha256.json") != bootstrap.tree_manifest(owner / "node_modules"):
                raise ValueError("Render dependency content differs from bootstrap receipt")
            browser_files = {
                file.relative_to(cache).as_posix(): bootstrap.digest(file)
                for file in sorted(cache.rglob("*"))
                if file.is_file() and file != cache / "content-sha256.json"
            }
            if not browser_files or read_json(cache / "content-sha256.json") != browser_files:
                raise ValueError("Browser content differs from bootstrap receipt")
            for base in (owner / "node_modules", cache):
                for file in base.rglob("*"):
                    if not file.resolve().is_relative_to(base) or file.is_junction():
                        raise ValueError("Render content link escapes ownership")
            node, browser = Path(render["node"]).resolve(), Path(render["path"]).resolve()
            mmdc = owner / "node_modules/.bin" / ("mmdc.cmd" if os.name == "nt" else "mmdc")
            if not browser.is_relative_to(cache) or not browser.is_file() or not node.is_file() or not mmdc.is_file():
                raise ValueError("Admitted Node/browser/Mermaid executable missing or outside owned cache")
            if render["mmdc"] != str(mmdc) or render["browser"] != "Chrome/" + versions["chrome"]:
                raise ValueError("Render executable/version differs from bootstrap result")
            environment = {
                "PUPPETEER_CACHE_DIR": str(cache),
                "PUPPETEER_EXECUTABLE_PATH": str(browser),
                "PUPPETEER_CHROME_VERSION": versions["chrome"],
                "PUPPETEER_SKIP_DOWNLOAD": "true",
                "PUPPETEER_FIREFOX_SKIP_DOWNLOAD": "true",
                "PUPPETEER_CHROME_HEADLESS_SHELL_SKIP_DOWNLOAD": "true",
            }
            self.env.update(environment)
            self.env["PATH"] = os.pathsep.join([str(mmdc.parent), str(node.parent), self.env["PATH"]])
            script = (
                "const p=require('puppeteer');(async()=>{"
                "const b=await p.launch({executablePath:process.env.PUPPETEER_EXECUTABLE_PATH,"
                "headless:true,args:process.platform==='linux'?['--no-sandbox']:[]});"
                "console.log(JSON.stringify({status:'passed',version:process.version,browser:await b.version(),"
                "puppeteer:require('puppeteer/package.json').version,"
                "path:await p.executablePath({headless:'shell'})}));"
                "await b.close();})().catch(e=>{console.error(e);process.exit(1)});"
            )
            process = run_process(
                [str(node), "-e", script],
                cwd=owner,
                env=self.env,
                output_parent=directory,
                lease=Lease(time.monotonic() + 30),
                termination=0.5,
                cleanup=3,
                cancel=cancel,
            )
            self.containment_verified = self.containment_verified and process["cleanup"]["verified"]
            probe = read_json(Path(process["directory"]) / "stdout.bin")
            if (
                process["status"] != "exited"
                or process["child_exit_code"] != 0
                or not process["cleanup"]["verified"]
                or probe.get("version") != "v" + versions["node"]
                or probe.get("browser") != "Chrome/" + versions["chrome"]
                or probe.get("puppeteer") != manifest["dependencies"]["puppeteer"]
                or Path(probe["path"]).resolve() != browser
            ):
                raise ValueError("Pinned render probe/version/resolver/cleanup mismatch")
            self.readiness["render"] = True
            self.inventory["render"] = {**probe, "status": "verified"}
        except Exception as error:
            self.readiness["render"] = False
            self.inventory["render"] = {"status": "unavailable", "error": str(error)}

    def context(self, cancel=None):
        if not self.readiness.get("python"):
            return {
                "status": "blocked",
                "error": "Python prerequisite unavailable for actual composed-context validation",
            }
        directory = self.output / "actual-context"
        directory.mkdir()
        request = self.request(directory, "context")
        process = self.launch(
            [self.executables["python"], "-B", str(self.root / "Tools/CI/adapter_worker.py"), str(request)],
            directory,
            Lease(time.monotonic() + 30),
            cancel,
        )
        if process["status"] != "exited" or process["child_exit_code"] != 0:
            return {"status": "failed", "error": str(process.get("diagnostics")), "process": process}
        document = read_json(Path(process["directory"]) / "stdout.bin")
        return {**document, "process": process}

    def execute(self, row, lease, cancel, completed):
        self.active_processes = []
        try:
            result = self.execute_layer(row, lease, cancel, completed)
        except Exception as error:
            result = {
                "status": "timed-out" if isinstance(error, TimeoutError) else "error",
                "classification": "timeout" if isinstance(error, TimeoutError) else "result-contract",
                "child_exit_code": self.active_processes[-1]["child_exit_code"] if self.active_processes else None,
                "processes": self.active_processes,
                "reasons": [str(error)],
            }
        if row.get("adapter") in {"pytest", "pester"}:
            try:
                self.retain_native(row, result)
            except Exception as error:
                result.update(
                    status="error", classification="result-contract", reasons=[*result.get("reasons", []), str(error)]
                )
                result.setdefault("processes", self.active_processes)
        return result

    def retain_native(self, row, result):
        native_root = self.root / ".tmp" / ("native-" + row["execution_id"].split("/")[1].split("::")[0])
        if native_root.exists():
            from execution_reports import confined

            directories = list(native_root.iterdir())
            if len(directories) != 1 or not directories[0].name.startswith("run-"):
                raise ValueError("Unexpected native run owner inventory")
            native_owner = directories[0]
            if native_owner.resolve() != native_owner or native_owner.is_symlink() or native_owner.is_junction():
                raise ValueError("Redirected native run owner")
            result["retained_native"] = {
                name: str(confined(native_owner, name))
                for name in ("native.xml", "native-phases.json", "stdout.log", "stderr.log")
                if confined(native_owner, name).is_file()
            }

    def execute_layer(self, row, lease, cancel, completed):
        adapter = row["adapter"]
        identity, runtime = row["execution_id"].split("::")
        logical_id = identity.split("/")[1]
        if adapter == "parity":
            pairs = {}
            for source in row["depends_on"]:
                if completed[source]["status"] != "passed":
                    raise ValueError("Parity source did not pass")
                evidence = completed[source]["evidence"]
                passed, suite = conformance_result(evidence, source.split("::")[0].split("/")[1])
                if not passed or "error" in evidence or set(suite) != {"id", "status", "summary"}:
                    raise ValueError("Parity requires successful, error-free conformance evidence")
                pairs.setdefault(source.split("::")[0], {})[source.split("::")[1]] = evidence["suites"][0]["summary"]
            if not pairs or any(set(pair) != {"python", "powershell7"} for pair in pairs.values()):
                raise ValueError("Incomplete parity runtime/semantic inventory")
            match = all(typed_equal(pair["python"], pair["powershell7"]) for pair in pairs.values())
            return {
                "status": "passed" if match else "failed",
                "classification": None if match else "parity",
                "child_exit_code": None,
                "native_counts": None,
                "evidence": {
                    "contract": "parity",
                    "contract_version": 1,
                    "sources": row["depends_on"],
                    "summaries_match": match,
                },
            }
        needed = ["python"] if runtime == "referee" else [runtime]
        if adapter == "compatibility":
            needed = ["python", "powershell7"]
            if logical_id == "render":
                needed.append("render")
        if adapter == "actionlint":
            needed.append("actionlint")
        missing = [value for value in needed if not self.readiness.get(value)]
        if missing:
            return {
                "status": "blocked",
                "classification": "prerequisite",
                "reasons": ["Unavailable: " + ", ".join(missing)]
                + [self.inventory[name]["error"] for name in missing if self.inventory.get(name, {}).get("error")],
            }
        directory = self.output / ("unit-" + identity.replace("/", "-") + "-" + runtime)
        directory.mkdir()
        python = self.executables["python"]
        paths = sorted(self.snapshot.files)
        commands = []
        if adapter == "ruff":
            eligible = [name for name in paths if Path(name).suffix in {".py", ".pyi"}]
            if not eligible:
                raise ValueError("Required Ruff surface is empty")
            commands = [
                [python, "-B", "-m", "ruff", "check", "--", *eligible],
                [python, "-B", "-m", "ruff", "format", "--check", "--", *eligible],
            ]
        elif adapter == "actionlint":
            eligible = [
                name
                for name in paths
                if name.startswith(".github/workflows/") and Path(name).suffix in {".yml", ".yaml"}
            ]
            if not eligible:
                raise ValueError("Required workflow policy surface is empty")
            commands = [[self.executables["actionlint"], "-shellcheck=", "-pyflakes=", *eligible]]
        elif adapter in {"work-annotations", "powershell-format"}:
            if adapter == "work-annotations":
                request = self.request(directory, "annotations", paths=paths)
                commands = [[python, "-B", str(self.root / "Tools/CI/adapter_worker.py"), str(request)]]
            else:
                eligible = [name for name in paths if Path(name).suffix in {".ps1", ".psm1", ".psd1"}]
                if not eligible:
                    raise ValueError("Required formatting surface is empty")
                request = self.request(
                    directory, "format", paths=eligible, source_representation=self.source_representation
                )
                commands = [
                    [
                        self.executables["powershell7"],
                        "-NoProfile",
                        "-File",
                        str(self.root / "Tools/CI/Invoke-CiAdapter.ps1"),
                        "-Request",
                        str(request),
                    ]
                ]
        elif adapter in {"pytest", "pester"}:
            commands = [
                [
                    python,
                    "-B",
                    str(self.root / "Tools/CI/run_native_tests.py"),
                    "--runtime",
                    runtime,
                    "--executable",
                    self.executables[runtime],
                    "--group",
                    logical_id,
                    "--output-root",
                    str(self.root / ".tmp" / ("native-" + logical_id)),
                    "--timeout",
                    str(max(0.1, lease.remaining())),
                ]
            ]
            for name in row["entry"]:
                commands[0] += ["--path", str(self.root / name)]
        elif adapter == "conformance":
            timeout = str(max(1, int(lease.remaining())))
            commands = (
                [
                    [
                        python,
                        "-B",
                        str(self.root / "Tools/Conformance/run_conformance.py"),
                        "--root",
                        str(self.root),
                        "--suite",
                        logical_id,
                        "--timeout",
                        timeout,
                        "--json",
                    ]
                ]
                if runtime == "python"
                else [
                    [
                        self.executables[runtime],
                        "-NoProfile",
                        "-File",
                        str(self.root / "Tools/Conformance/Run-Conformance.ps1"),
                        "-Root",
                        str(self.root),
                        "-Suite",
                        logical_id,
                        "-TimeoutSeconds",
                        timeout,
                        "-Json",
                    ]
                ]
            )
        elif adapter == "compatibility":
            commands = [
                [
                    python,
                    "-B",
                    str(self.root / "Tools/Compatibility/run_compatibility.py"),
                    "--root",
                    str(self.root),
                    "--check",
                    logical_id,
                    "--output-root",
                    str(self.root / ".tmp" / ("compatibility-" + logical_id)),
                    "--json",
                ]
            ]
        elif adapter == "installed-artifact":
            if not self.wheel or not self.runtime_wheel:
                return {
                    "status": "blocked",
                    "classification": "prerequisite",
                    "reasons": ["Explicit wheel/runtime wheel required"],
                }
            try:
                for name, path in (("framework", self.wheel), ("runtime", self.runtime_wheel)):
                    with Path(path).open("rb") as stream:
                        stream.read(1)
            except OSError as error:
                return {
                    "status": "blocked",
                    "classification": "prerequisite",
                    "reasons": [
                        f"Unreadable {name} wheel input {path}: {error}. "
                        "Acquire readable inputs explicitly; ACLs are unchanged."
                    ],
                }
            commands = [
                [
                    python,
                    "-B",
                    str(self.root / "Tools/CI/verify_installed_package.py"),
                    "--install-and-verify",
                    "--wheel",
                    str(Path(self.wheel).resolve()),
                    "--runtime-wheel",
                    str(Path(self.runtime_wheel).resolve()),
                    "--installer-python",
                    python,
                    "--report",
                    str(self.root / ".tmp/installed-package.json"),
                ]
            ]
        else:
            raise ValueError("Unsupported adapter")
        processes = [self.launch(command, directory, lease, cancel) for command in commands]
        self.active_processes = processes
        last = processes[-1]
        for process in processes:
            if process["status"] != "exited" or not process["cleanup"]["verified"]:
                return {
                    "status": process["status"]
                    if process["status"] in {"timed-out", "cancelled", "blocked"}
                    else "error",
                    "classification": process.get("classification"),
                    "child_exit_code": process["child_exit_code"],
                    "processes": processes,
                }
        codes = [process["child_exit_code"] for process in processes]
        text = Path(last["directory"], "stdout.bin")
        document, native, terminal = None, None, None
        passed = all(code == 0 for code in codes)
        classification = (
            None
            if passed
            else "policy"
            if adapter in {"ruff", "actionlint", "powershell-format", "work-annotations"}
            else "assertion"
        )
        if adapter in {"pytest", "pester"}:
            document = read_json(text)
            if document.get("contract") != "native-test-run" or document.get("identity") != logical_id + "." + runtime:
                raise ValueError("Wrong native adapter identity")
            target = Path(document["run_directory"])
            if not target.resolve().is_relative_to(self.root / ".tmp"):
                raise ValueError("Foreign native artifact directory")
            phase = read_json(target / "native-phases.json")
            validate_phase(runtime, document["child_exit_code"], phase)
            _, _, counts = parse_junit(target / "native.xml")
            if document.get("native_counts") != {"collected": phase["collected"], **counts}:
                raise ValueError("Native reported counts do not match actual XML/phase evidence")
            _, _, published = parse_junit(target / "junit.xml")
            if published != counts:
                raise ValueError("Native publication case inventory differs")
            status, classification, exit_code = classify(runtime, document["child_exit_code"], phase, counts)
            if status != document["status"] or exit_code != document["exit_code"] or exit_code != codes[0]:
                raise ValueError("Native exit/result contract mismatch")
            native = document["native_counts"]
            passed = status == "passed"
            terminal = status
        elif adapter == "conformance":
            document = read_json(text)
            passed, _ = conformance_result(document, logical_id)
            if passed != (codes[0] == 0):
                raise ValueError("Conformance exit/result mismatch")
        elif adapter == "compatibility":
            document = read_json(text)
            passed = compatibility_result(document, logical_id)
            if passed != (codes[0] == 0):
                raise ValueError("Compatibility exit/result mismatch")
        elif adapter in {"work-annotations", "powershell-format"}:
            document = read_json(text)
            if adapter == "work-annotations":
                if document.get("status") not in {"passed", "failed"} or document.get("fixture_cases", 0) <= 0:
                    raise ValueError("Annotation validation evidence missing")
                truthful = document["status"] == "passed"
            else:
                if type(document.get("files_checked")) is not int or document["files_checked"] != len(eligible):
                    raise ValueError("Formatter omitted actual source files")
                truthful = document.get("ready") is True
            if truthful != passed:
                raise ValueError("Policy exit/result mismatch")
        elif adapter == "installed-artifact":
            document = read_json(self.root / ".tmp/installed-package.json")
            passed = (
                document.get("status") == "passed"
                and document.get("cleanup_complete") is True
                and bool(document.get("checks"))
            )
            if passed != (codes[0] == 0):
                raise ValueError("Installed artifact result/cleanup mismatch")
        lease.verify()
        return {
            "status": terminal or ("passed" if passed else "failed"),
            "classification": classification,
            "child_exit_code": last["child_exit_code"],
            "native_counts": native,
            "reasons": owning_failure_reasons(document, adapter)
            if not passed and adapter in {"compatibility", "conformance", "powershell-format", "installed-artifact"}
            else [],
            "evidence": document,
            "processes": processes,
        }
