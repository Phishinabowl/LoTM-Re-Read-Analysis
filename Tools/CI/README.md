# Local Dependency, Package And Bootstrap Tools

CI 3.1.2 implements explicit local acquisition, verified environments and package builds. The
[package contract](../ci-python-package-contract.md) defines identity/version/artifact boundaries;
the [modernization plan](../ci-testing-modernization-plan.md) owns acceptance and later adoption.
Full installed-artifact semantic/boundary testing is 3.1.3. No external package publishing is provided.

## Normal Development Setup

Use the adopted CPython 3.14.5 x64 interpreter and PS7.6.6 development host. The controller fails
with an actionable error if a selected interpreter/tool is missing or mismatched; it does not
upgrade machine runtimes or machine-wide packages. Acquire those explicitly before bootstrap.

```powershell
python Tools/CI/bootstrap.py --media --powershell-profile development --actionlint --report .tmp/ci/bootstrap.json
python Tools/CI/bootstrap.py --media --powershell-profile development --actionlint --offline --check --report .tmp/ci/preflight.json
```

The default Python profile is development; runtime/build/none profiles are explicit. Media adds
Pillow for required synthetic media coverage without adding it to the core wheel. Rendering is
on demand, using `--python-profile none --render`; it requires exact Node 24.15.0/npm 11.12.1.
`--floor --pwsh <path> --powershell-profile runtime` verifies the exact PS7.4.0 runtime lane.
Pester 6.2.0 also passes in that host; PSScriptAnalyzer 1.25.0 requires Core 7.4.6+ and the adopted
development baseline is 7.6.6. The framework runtime floor remains 7.4; no older tool fallback.

Use the executable/module/browser paths recorded in the JSON report for subsequent commands.
Bootstrap does not modify the caller's PATH, PSModulePath or global packages. Python environments
omit system/user site packages and disable pytest plugin auto-loading. PowerShell imports come
from the owned module cache, with exact `-RequiredVersion` and imported-path checks. The report's
`module_path` can be assigned to process-scoped PSModulePath before running Pester/framework tools.
For rendering, prepend the reported mmdc directory to process PATH and set PUPPETEER_CACHE_DIR
and PUPPETEER_EXECUTABLE_PATH to the reported verified Chrome cache/path. Do not substitute Edge.

`--check` performs verification only; missing environments/payloads never trigger acquisition.
`--offline` allows explicit environment creation from already verified payloads. A different
`--environment-id <owned-label>` creates a fresh environment while reusing matching payloads;
use this to distinguish cache restoration from reusing an already installed environment.
Default passing output is concise; `--json` emits the complete structured report. `--report`
persists that report only under owned ignored .tmp/.local locations. Selected independent units
continue after a unit failure and the aggregate exit code remains nonzero.

## Package Build And Install Routes

```powershell
python Tools/CI/bootstrap.py --package-mode wheel --report .tmp/ci/wheel.json
python Tools/CI/bootstrap.py --package-mode editable --report .tmp/ci/editable.json
python Tools/CI/bootstrap.py --package-mode wheel --build-only --report .tmp/ci/build-only.json
```

Package modes use dedicated build environments; source development is a separate profile. Wheel
and editable modes have different environment identities, so one cannot satisfy the other by
accident. Build-only omits PyYAML and proves literal version extraction/building does not import
the runtime service graph. Exact setuptools 84.0.0/build 1.4.0/pip 26.2 and their active transitive
dependencies are acquired before building. Builds use `--no-isolation` and installs use
`--no-build-isolation --no-deps --no-index`: implicit build/dependency downloads are disabled.
Runtime dependencies are installed explicitly from the locked graph first when installation is requested.

Builds stage only the reviewed runtime files, pyproject and unchanged LICENSE under `.local/ci-build/`.
Build output/metadata stays there; editable installation selects the original source tree. Generated
egg-info at the declared runtime source location is ignored. Source CLI paths/import setup are preserved.
The single authored Python version is `_version.py`; installed metadata/version and actual origin
are verified. The artifact digest and source/build input digests are retained. A fixed
SOURCE_DATE_EPOCH removes ZIP timestamp variation; this is not a universal reproducible-build claim.

The build owner may supply `--source-revision <verified-full-commit-id>` and `--source-modified`
for an uncommitted checkout. Absence is recorded as unknown; the tool does not invent a clean Git
revision or require Git for a detached source bundle. Exact source-input digests remain available.
Detailed wheel-member inspection and installed neutral semantic assertions remain 3.1.3.

## Dependency Authorities And Cache Boundaries

- Root requirements files own exact runtime/development/build/media graphs and confined include grammar.
- Pyproject owns compatible runtime metadata and the exact backend declaration; bootstrap checks consistency.
- `Data/runtime-versions.json` owns adopted interpreter/tool baselines and declaration references.
- `Data/python-wheel-lock.json` records published wheel URLs/digests for those exact pins on CPython
  3.14.5 Windows x64/Linux glibc x64. Platform-specific markers are evaluated explicitly.
- Root requirements-node.txt owns the two direct rendering pins; Node/package.json and its full npm
  lock must match. npm uses the lock's integrity records and an owned download cache.
- `Data/python-package-files.json` is the explicit initial source allowlist, not schema-pack membership.

Python includes support exact `name==version`, `-r <relative-file>` and the declared sys_platform
markers only. PowerShell supports exact `name version`, relative includes and comments. Unknown
flags/floating constraints, empty/missing inputs, cycles, conflicting versions and escaping paths
fail. PowerShell includes also reject link traversal. Test-Python/Test-PowerShell readiness performs
actual exact-version import checks; false readiness exits nonzero. Test-Python no longer reports
success merely because an interpreter executable or a module specification exists.

Persistent `.local/ci-cache/` stores verified Python wheels, versioned PowerShell module content,
locked npm downloads and pinned Chrome binaries. `.local/ci-environments/` stores separate owned
execution environments; installed dependency file hashes are verified before reuse. Keys include
OS/architecture, adopted tools and declaration/lock digests. Corrupt/missing provenance or wrong
versions fail explicitly; they are not silently repaired during verification. Inspect the named
owned cache/environment before explicitly reacquiring. No arbitrary/global directory cleanup.

Chrome acquisition calls the explicit browser installer API with Browser.CHROME and build ID
150.0.7871.24. Generic Puppeteer install.mjs is not used. Owned configuration and per-browser
environment flags exclude Firefox/headless-shell acquisition; inherited browser overrides are
removed. A browser executable/content receipt and headless page smoke are verified before reuse.
Headless browser verification needs local loopback access; this tool's restricted execution sandbox
blocked that connection, while the same offline check passed with approved execution permissions.

Lock maintenance is explicit, never part of test execution:

```powershell
python Tools/CI/update_python_wheel_lock.py
npm --prefix Tools/CI/Node install --package-lock-only --ignore-scripts --no-audit --no-fund
```

Review generated diffs, active transitive dependencies, platform wheel availability and hashes.
No package is adopted by automatically following the latest version. Actionlint remains an exact
installed-tool preflight; its negligible measured download cost does not justify adding another cache.
Hosted cache transport, report publication and steady-state profile adoption remain Phase 6.

## Checkpoint Verification And Remaining Gates

The local proof records editable/wheel builds, a build environment without PyYAML, source baseline
21/21, runtime-only nine-suite Python/PS7 neutral extraction with cleanup (306 copied files), and
67 pytest/17 Pester cases on primary/floor hosts. Existing host fixtures now use exact-version
declarations and neutral fixture roots; no assertions or live-5.1 obligations were removed.
The 15 new Python/three Pester cases cover declaration/cache/bootstrap risks; native catalog
registration remains 3.2-3.5/4.1. Actual corrupt-wheel, wrong installed-version and missing-environment
probes fail closed, with independent available units continuing.

The first rendering attempt erroneously enabled Firefox through a general Puppeteer download flag,
launching its Windows self-extracting executable. That failed attempt is preserved in local evidence.
The corrected implementation explicitly acquires Chrome only; no Firefox/setup process remained
in the read-only process inspection. No system browser/profile cleanup is performed.

Cold Chrome-only setup took 247.602 seconds; reuse of its verified environment passed in 8.003.
A fresh offline npm environment still took 245.883: payload caching alone did not demonstrate a
substantial full-setup improvement. Preserve that distinction for later setup/duplication review.
These are local single samples, not hosted results or percentiles. Python/PS/cache observations
and negative diagnostics are retained under ignored `.tmp/ci-phase312-20261005/`.

Ubuntu 24.04 is now available locally through WSL 2. User-owned CPython 3.14.5 and PowerShell
7.6.6 are installed separately from Ubuntu's system Python; uv 0.12.23 was used only for local
interpreter acquisition, not as a repository dependency or replacement for the pip bootstrap.
The isolated Linux source snapshot includes the current uncommitted files and has its own
environments/caches. Local Linux proof supplements hosted acceptance; it does not replace it.
Local Linux cold/fresh-offline/check/wheel/editable bootstrap routes pass, together with 67
pytest cases, 21 Python baseline suites and 17 Pester cases on PS7.6.6. Evidence is preserved
under ignored `.tmp/ci-wsl-20261005/`. Rendering and the Linux PS7.4 floor were not exercised
in this setup pass. The Linux workspace is a test snapshot, not a second Git publication owner.
The temporary manual-only `bootstrap_only` option in the existing CI workflow calls
`verify_bootstrap.py` on Windows/Linux with the same repository-owned commands. GitHub requires
workflow registration on the default branch; a separate branch-only workflow returned HTTP 404,
so the proof uses the already registered CI entry point. Ordinary CI membership/names remain intact.
Cross-OS acceptance passed on 2026-10-05 at `3b9b706e5596eccc862d3cf09c3137ff497d05a0` in
[run 37379644665](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37379644665):
Windows 2m55s, Linux 2m00s, Workflow Policy 5s. Both lanes pass cold/fresh-offline/check,
wheel/editable, native pytest and the Python baseline. Pester remains locally verified on Windows
primary/floor and WSL primary; this temporary hosted driver does not claim hosted Pester adoption.
Complete run logs are preserved under ignored `.tmp/ci-wsl-20261005/`. The temporary option has
no automatic execution on push/PR/schedule, changes no required check, and must retire after acceptance/canonical
native-profile adoption; do not let it become a duplicate permanent CI portfolio. Passing current
conformance alone does not prove a fresh Linux bootstrap. Broad installed-artifact semantics and
boundary regressions remain 3.1.3; process-tree supervision/cancellation remains Phase 4.
