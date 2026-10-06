# CI 5.4 Release Inputs And Local Reproduction Proof

**Status:** Implemented, verified locally and confirmed by the maintainer on 2026-10-06.

The [modernization plan](ci-testing-modernization-plan.md) owns acceptance. This checkpoint closes
the npm configuration, browser provenance and unreadable-wheel/reporting boundaries classified by
the [CI 5.1 comparison](ci-testing-shadow-comparison.md). Consumer golden hashes were proved unchanged
at [5.3](ci-testing-consumer-safety-proof.md). Full-system equivalence/performance acceptance remains
5.5; hosted activation remains Phase 6. No fixture, runtime pin, required check or review is retired.

## Implementation Boundaries

- Bootstrap uses distinct empty owned `user.npmrc` and `global.npmrc` files. npm rejects loading the
  same null-device path twice; these separate inputs avoid that collision and inherited user/global
  configuration. Check mode validates existing files without creating missing inputs. Lowercase
  inherited npm/Puppeteer/Python overrides are scrubbed too.
- The Chrome-only Puppeteer configuration has one repository-owned definition shared by bootstrap
  and execution admission. The render bootstrap result now records the exact Node/npm executable paths.
- `run_ci.py --render-bootstrap-report` explicitly supplies a passing render bootstrap report.
  Admission independently checks matching owned environment/cache paths, the current runtime/lock key,
  package/lock declarations, configuration, dependency/browser content receipts and confined links.
  A supervised Node/browser probe verifies exact Node, Puppeteer and full-Chrome versions and the
  resolver used for Mermaid's headless-shell request. Its result must resolve to the admitted full
  Chrome executable. Stale, absent, changed or globally resolved inputs block the required render unit.
- Only admitted render settings reach children: owned cache, exact executable and skip-download flags,
  with owned Mermaid/Node first on PATH. Windows system drive/data variables remain available to native
  libraries; inherited browser overrides stay excluded. No browser download or cache repair occurs
  during CI execution. The existing resolver's asynchronous API is awaited before comparing its path.
- Installed-artifact admission reads both explicit wheel inputs before launching the verifier.
  Missing/unreadable inputs produce an actionable prerequisite result; no ACL override or diagnostic
  copy can supply a passing obligation. Early verifier failures retain a failed report with no invented
  installation checks or cleanup claim. Complete installation/content/dependency checks remain required.
- Bootstrap child launches and copied-framework conformance commands honor inherited whole-unit
  deadlines. Extraction retains timeout streams. The production process supervisor continues to own
  render/extraction descendants, cancellation and final cleanup.

## Native Regression

Existing groups gain 27 cases: five bootstrap configuration/deadline cases; two wheel-readability,
eleven render-admission and one Windows-environment cases; four additional real render/extraction
interruption cases; three extraction deadline/partial-stream cases; one early verifier-report case.
The existing compatibility interruption fixture supplies each kind's nested child only; it never
recursively runs the expensive production portfolio from pytest.

The final affected bootstrap/adapter/gate/compatibility/artifact/reporting cohort passes **234 cases
on Windows in 21.62 seconds and 234 on WSL Ubuntu 24.04 in 29.44 seconds**.
Collection is 434 Python cases; mandatory infrastructure is 328 (ci-execution is 140).
PowerShell remains 44. Inventory is separate from execution evidence.

The negative admission cases reject an absent/failed report, wrong cache key/ownership,
changed lock/dependency/browser/configuration,
wrong Node version and global resolver path. Wheel failures do not launch a verifier. Deadline tests
prove invalid/expired limits reject before launch and bounded calls retain partial diagnostics.
Real nested-child interruption exercises the render and extraction adapter identities, verifies
containment and preserves unrelated artifacts. Existing generic process/source/report regressions remain.

## Acquisition, Provenance And Verification Scope

Ignored evidence is under `.tmp/ci-phase54/`. Offline Chrome-only bootstrap passes against the existing
Node/Puppeteer/browser pins. The normal Windows release account explicitly acquires/builds a fresh
framework wheel using the committed build graph; it is not the 5.1 diagnostic wheel copy. Package source
version remains 0.1.0 and the runtime sources are unchanged. The acquired PyYAML wheel is checked against
the committed platform lock by the installed-artifact verifier.

The two Windows execution accounts cannot read every artifact created by the other. Initial build
success under the restricted account did not imply readability under the browser-capable release
account. Same-account explicit bootstrap resolves that boundary without modifying either artifact ACL.
The original 5.1 inaccessible artifact is preserved; its failure is represented honestly when selected.

The preflight also exposed missing Windows system variables: native library cache files appeared under
a literal `%SystemDrive%` folder inside the owned Chrome directory. All acquired browser files remained
unchanged. The five generated files were inventoried, then removed from that exact verified owned
subfolder; the original receipt was restored exactly, without changing or excluding receipt members.
The corrected environment is independently regressed. Failed preparation/preflight evidence remains;
its external scratch owners were removed. No production suite had run during those failed preflights.

The successful observer captures commit `96a902a` plus explicit Git-normalized code/test overlays,
verified against Git-filtered blob hashes. It executes 33 catalog obligations: installed artifact,
portable extraction, rendering and both runtimes for all 15 registered suite summaries containing
retained scale/budget/deep-limit evidence. Full baseline membership and retained reviews are unchanged.
These 30 detailed conformance rows must match their retained 5.2 rows exactly. This is a narrowed
release/limit proof, not a complete full-verification or release-readiness acceptance.

All **33 selected catalog obligations pass** in 476.99 seconds (7 minutes 57 seconds) after preflight.
This is one narrowed local sample with concurrent native checks/process observation, not the 5.5
full-profile feedback measurement or a hosted performance claim.

| Obligation | Verified evidence |
| --- | --- |
| Installed artifact | Freshly built wheel, exact locked runtime dependency and ten installation/negative/content checks; external temporary environment removed. |
| Portable extraction | 306 copied files, nine forbidden surfaces absent, neutral `extraction-smoke` project and all nine selected suites passed by Python/PS7; no copied canonical LoTM project or CI runtime dependency. |
| Retained executable limits | Fifteen registered suites in both runtimes; all 30 detailed ID/status/type/ordered-summary rows exactly match their retained 5.2 results, including scale counts, ingestion budgets and reconciliation's 1,500-hop chain/limits. |
| Rendering | Python/PS7 each generate the same 298,414-byte SVG and dimensions; hash `41aaafbcf5928cc339fd26bcaa101c80819b58448db6bf8ac793b753f586e4b0` matches the retained explicit-full-Chrome 5.1 diagnostic. |
| Actual browser process | Read-only process metadata observes the owned Mermaid Node command launching the admitted full-Chrome executable with headless arguments; no desktop control is used. This is one observed real launch, supplemented by shared explicit environment admission and both runtime render results. |
| Guards and publication | All captured source bytes/canonical projections unchanged, every process contained, external scratch removed and unrelated sentinel preserved; JSON/Markdown/custom JUnit bundle admits 169 manifest files. Acquired browser/dependency receipts still match after rendering. |

The public absolute-path offline render check also passes from `C:\Windows\System32` in 7.404 seconds
without acquisition or repair. The runner exposes the explicit render-report flag in its CLI contract.
Four final focused input/environment cases were added after the observer
capture. A later Python source line wrap preserves the same parsed adapter code and generated probe
script; it changes no production behavior or shared suite expectation. These later edits are
distinguished from the frozen source digest.

## Exact Local Recipes And OS Assignment

Use one account for acquisition and execution. Bootstrap's reported paths and receipts are authoritative;
do not guess a global Python/module/browser path or substitute an artifact from another account.
The bootstrap interpreter must be adopted CPython 3.14.5 x64. The following Windows recipe uses
absolute script/root paths and also works from an unrelated working directory:

```powershell
$repo = 'C:\Users\ptseb\Documents\LoTM Analysis'
$bootstrapPython = 'C:\Users\ptseb\AppData\Local\Python\pythoncore-3.14-64\python.exe'

# Explicit preparation; offline requires previously acquired payloads.
& $bootstrapPython "$repo\Tools\CI\bootstrap.py" --media --powershell-profile development --actionlint `
    --render --offline --report "$repo\.tmp\ci-local-preparation.json"
& $bootstrapPython "$repo\Tools\CI\bootstrap.py" --python-profile build --package-mode wheel `
    --build-only --environment-id release --offline --report "$repo\.tmp\ci-local-wheel.json"

# Validate existing preparation without acquisition or repair.
& $bootstrapPython "$repo\Tools\CI\bootstrap.py" --media --powershell-profile development --actionlint `
    --render --offline --check --report "$repo\.tmp\ci-local-check.json"

$preparation = Get-Content "$repo\.tmp\ci-local-check.json" -Raw | ConvertFrom-Json
$build = Get-Content "$repo\.tmp\ci-local-wheel.json" -Raw | ConvertFrom-Json
$python = $preparation.python.executable
$pwsh = $preparation.powershell.executable
$modules = $preparation.powershell.module_path.Split([IO.Path]::PathSeparator)[0]
$actionlint = $preparation.actionlint.path
$wheel = $build.package.wheel
# Exact Windows wheel filename from the committed CPython 3.14 platform lock.
$yamlWheel = "$repo\.local\ci-cache\python\$($preparation.python.key)\pyyaml-6.0.3-cp314-cp314-win_amd64.whl"

& $python "$repo\Tools\CI\run_ci.py" --root $repo --profile full-verification `
    --scope local-worktree --pwsh $pwsh --module-root $modules --actionlint $actionlint `
    --wheel $wheel --runtime-wheel $yamlWheel `
    --render-bootstrap-report "$repo\.tmp\ci-local-check.json" --summary-json
```

The last command is the complete catalog profile and retains all its normal obligations; this
checkpoint's narrowed observer is not another public profile. Bootstrap may acquire only through an
explicit preparation command; CI execution never silently prepares missing tools. `release-readiness`
also retains its mandatory pending review families and cannot be declared green by an automated subset.

Linux uses the same Python entrypoints and profile/receipt flags with Linux paths/executables.
This checkpoint verifies WSL native regressions; it does not certify a fresh Linux Node/browser setup,
Linux rendering or Windows/API coverage. The initial release shard plan assigns rendering to Windows.
A Linux-only invocation cannot count absent prerequisites or Windows-assigned obligations as passes;
complete host evidence must include the prescribed Windows shard. Existing Linux package/bootstrap
proof remains historical evidence; hosted multi-OS assignment/admission is verified during Phase 6.

Final scoped validation covers Ruff lint/format, annotation policy/fixtures, relative documentation
links, publication admission and Git whitespace review. No canonical, fixture, registry, dependency
pin, workflow or unrelated tracked change is present. Maintainer confirmation on 2026-10-06
authorizes the focused CI 5.4 commit and dual-remote publication.
