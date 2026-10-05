"""Temporary CI 3.1.2 cross-OS proof; retire after acceptance and canonical test adoption."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-revision")
    args = parser.parse_args()
    out = ROOT / ".tmp/ci-bootstrap-verification"
    out.mkdir(parents=True, exist_ok=True)
    results = []

    def execute(name, command):
        start = time.perf_counter()
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300
        )
        (out / (name + ".log")).write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        results.append({"id": name, "exit_code": result.returncode, "seconds": time.perf_counter() - start})
        (out / "proof.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        if result.returncode:
            print(result.stdout + result.stderr)
            for file in sorted(out.glob("*.json")):
                print(f"Complete diagnostic report: {file.name}\n{file.read_text(encoding='utf-8')}")
            raise RuntimeError(f"Bootstrap proof failed: {name}")
        print(f"{name}: passed ({results[-1]['seconds']:.3f}s)", flush=True)

    base = [sys.executable, "Tools/CI/bootstrap.py"]
    execute("cold", base + ["--media", "--environment-id", "proof-cold", "--report", str(out / "cold.json")])
    execute(
        "warm-fresh",
        base + ["--media", "--offline", "--environment-id", "proof-warm", "--report", str(out / "warm.json")],
    )
    execute(
        "check",
        base
        + ["--media", "--offline", "--check", "--environment-id", "proof-warm", "--report", str(out / "check.json")],
    )
    revision = ["--source-revision", args.source_revision] if args.source_revision else []
    for mode in ("wheel", "editable"):
        execute(
            mode,
            base
            + [
                "--package-mode",
                mode,
                "--environment-id",
                "proof-package",
                *revision,
                "--report",
                str(out / (mode + ".json")),
            ],
        )
    environment = json.loads((out / "warm.json").read_text())["python"]["executable"]
    # Native bootstrap/retirement tests only; conformance membership remains in its original registry.
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    execute(
        "native", [environment, "-m", "pytest", "Tools/Tests/Python", "-q", "--junitxml=" + str(out / "native.xml")]
    )
    execute(
        "baseline",
        [
            environment,
            "Tools/Conformance/run_conformance.py",
            "--profile",
            "baseline",
            "--summary-json",
            "--report-output",
            str(out / "baseline.json"),
        ],
    )
    print("Cross-OS bootstrap proof completed; full artifact/installed semantic acceptance remains CI 3.1.3.")


if __name__ == "__main__":
    main()
