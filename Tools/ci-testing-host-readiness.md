# CI 6.1 Repository Synchronization And Host Readiness

**Status:** Complete 6.1 readiness and cache qualification are verified and confirmed by the maintainer
on 2026-10-07. The expanded implementation is published as `ba6047a` with exact
HEAD/upstream/GitHub/ADO parity; this checkpoint publishes the final evidence and closes 6.1.
All twenty complete-payload job outcomes match expectations. No experiment remains running.
No PR or branch-policy change has been made. Historical inspection and intermediate failures below
retain their original scope. [The plan](ci-testing-modernization-plan.md#phase-61-repository-synchronization-and-host-readiness)
owns completion; [the integration design](ci-testing-host-integration-design.md) retains merge/event
authority. This record supplements its dated inspection rather than rewriting historical evidence.

## Verified Entry And Synchronization

The expanded Phase 5 gate was confirmed and published as `507caa4`. Its accepted
[77-unit OS comparison](ci-testing-os-comparison.md), semantic portfolio, source guards, local recipes
and provisional Windows full placement are the entry baseline. Linux eligibility and required Windows
image coverage remain; actual host costs can change placement at 6.5. Native/full goals remain 90/960
seconds with Phase 8.1 follow-up. Local WSL timing does not establish real agent speed.

Live `git ls-remote --heads` queries returned the same tips on GitHub and ADO:

| Ref | Identical commit |
| --- | --- |
| `main` | `608e48939ec352876ae919213a236592f46d982c` |
| `architecture/framework-extraction-foundation` | `c4b79326e8dde5420f61d318f4f541e752b6030a` |
| `architecture/ci-testing-modernization` | `507caa4bea5743c3dad91bd077eedeb4f63d0d8f` |

The checkout started clean on the modernization branch. `origin` fetches GitHub and retains exactly
two intended push URLs; `ado` fetches Azure Repos independently. Branch names map one-for-one.
Routine confirmed publication remains `git push origin HEAD`, followed by independent fetch/parity
checks. No extra refs, tags, force pushes or mirror publication are introduced.

GitHub is the sole merge authority. Synchronizing a future accepted framework merge is an explicitly
scoped target-ref operation; routine current-branch authorization does not grant that publication.
ADO validation PRs cannot create independent merge history.

| Publication observation | Safe response |
| --- | --- |
| HEAD/upstream/live GitHub/live ADO equal | Publication verified; do not push a second time. |
| One destination rejects or cannot be reached | Record the successful destination and failure; refresh both before retrying. A missing read is unknown, not an equal tip. |
| One destination is an ancestor of the intended commit | Verify ancestry and intended branch. A reviewed retry of the current dual push can bring the lagging destination forward; the already-current side is a no-op. |
| Either destination diverges or is ahead unexpectedly | Stop publication, inspect history and obtain a concrete recovery decision. Never force, merge in ADO, or overwrite history to hide divergence. |

The confirmed publication exercised ordinary parity: HEAD/upstream/GitHub/ADO all equal
`6b884da0798e0706e4ff32cd15a618abf1cb9667`. An isolated local two-bare-repository exercise then proved
partial recovery: the first destination accepted fixture commit `83eedce`, the unavailable second
destination failed and the overall push exited 1. Inspection proved the first ref present and the
second absent. After correcting only the fixture destination, the same dual push left the first
up-to-date and created the second; both matched. No force push, extra production ref or hosted
history mutation occurred. This tests transport failure/retry semantics, not live policy bypass.
An additional fixture-only divergence control set the second destination to independent commit
`f95e3b8`. Routine dual push exited 1 with a non-fast-forward rejection; reinspection proved that
destination unchanged. No forced recovery or production configuration change followed.

## Current Host Configuration

Successful authenticated API reads prove the following pre-activation inspection scope; the hosted
experiment section below supersedes pipeline/agent inventory after activation. Credentials and personal
identity details are excluded from tracked evidence. No tokens are printed, saved or put in caches.

| Surface | 2026-10-06 inspection |
| --- | --- |
| GitHub repository | Public, enabled, default `main`; caller repository role `admin`. |
| GitHub Actions | Enabled; allowed actions `all`; host SHA-pinning enforcement disabled. Repository adapters still pin every adopted action to an immutable commit. |
| GitHub workflow token defaults | Read-only; workflow PR approvals disabled. Pilot requests only `contents: read`. |
| GitHub protections | Rulesets empty; `main` and framework target unprotected. Preserve existing check names; do not treat this as permission to install enforcement early. |
| Existing GitHub workflows | `CI` and `Work Annotation Policy` active. Two active caches total 29,654,461 bytes; this is inventory, not a measured transport benefit. |
| Azure repository | Private project/repository `LoTM Inspired KM Platform`, enabled, default `refs/heads/main`; original project/repository IDs unchanged. |
| ADO pipelines / policies / active PRs | All three inspected inventories empty. No working pipeline identity/agent allocation or per-pipeline permission is claimed. |
| ADO hosted queue | Queue 39, pool 9, nonlegacy `Azure Pipelines`; all-pipelines queue authorization enabled. This is the existing setting, not a new broad grant. |
| Private hosted entitlement | One free slot, zero purchased, 1,800 monthly minutes; build hub confirms one free/total hosted license and no provider discovery failure. |
| Private self-hosted entitlement | One free slot; Default pool has zero agents. No local/self-hosted agent is installed. |
| ADO retention | Runs/artifacts 30 days, PR runs 10 days, three retained runs per protected branch. |

The free private hosted job ceiling is 60 minutes; organization concurrency/minutes are shared with
other projects. Pilot jobs reserve 20 minutes and serialize ADO matrix legs. The hub reports zero
used minutes, which does not independently certify the exact remaining monthly balance. No capacity
purchase, subscription deployment or billing change is proposed.
[Microsoft parallel-job guidance](https://learn.microsoft.com/en-us/azure/devops/pipelines/licensing/concurrent-jobs?view=azure-devops).

Inspection used the existing `gh`/Azure CLI authentication. Successful read and Git transport do not
prove every future pipeline-creation/build-policy permission. Verify the actual created pipeline's
execution identity during activation, and keep policy adoption at 6.3/6.5. The first hub-license
query used the wrong query-parameter route and returned 404; the correct `hubName=build` route succeeded.

## Staged Payload Transport Pilot

[Repository helper](CI/host_cache.py), [GitHub pilot](../.github/workflows/ci-cache-pilot.yml) and
[ADO pilot](../.azuredevops/ci-cache-pilot.yml) form a temporary setup experiment. They do not invoke
profiles, select tests, replace required checks, enable schedules or change any validation semantics.
Original CI remains in place. Retire the pilot after its measured transport is adopted into 6.2/6.3.

The first payload covers Python development/media wheels and PowerShell development modules.
Cache `.local/ci-cache` only; fresh pilot agents populate only those selected payloads. Python virtual
environments, source trees, reports, Git credentials, portable PS installations and build artifacts
are excluded. Node/npm/browser and build dependency transport remain explicit follow-up experiments
within 6.1; this initial payload does not claim them measured.

The repository-owned key hashes exact current runtime declarations, Python wheel lock, all root
requirements, npm lock/declarations and bootstrap/import/install helpers. It separates Windows/Linux
and x64, with a bounded operator namespace for controlled invalidation/recovery. No broad restore
prefix can cross lock or OS boundaries. Namespace is not a package-version authority.

GitHub uses separately pinned cache restore/save actions; ADO uses native `Cache@2`. Both restore
before calling the same bootstrap. On a host-reported hit, bootstrap runs offline and verifies wheel
digests, PowerShell content receipts, exact imports and versions while creating a fresh Python
environment. A hit cannot skip verification or become evidence of a passing test. Failed setup
blocks saving new cache content. ADO performs its cache save as a post-job operation after success;
restore and save task durations must be measured separately.
[GitHub cache reference](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching),
[Azure cache behavior](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops).

Python setup is pinned to 3.14.5. The helper checks actual PowerShell and uses exact 7.6.6; if the agent
image differs, it acquires a portable copy under owned `.local/ci-tools` with SHA256 values taken
from the official [7.6.6 checksum manifest](https://github.com/PowerShell/PowerShell/releases/download/v7.6.6/hashes.sha256).
It performs no machine installation. Runtime acquisition cost remains visible rather than being
attributed to payload-cache restore. Portable-runtime reuse/cache admission needs its own proof if
measurements justify it; no prepared agent image or package feed is needed now.

The GitHub pilot initially runs only for changes to its helper/workflow on the modernization branch,
and supports manual dispatch. ADO YAML has no CI/PR/scheduled trigger and needs a separately created,
nonrequired pipeline using this branch/YAML. Neither adapter supplies a build-validation policy.
Diagnostics are retained after ordinary failures; GitHub artifacts request seven-day retention and
ADO uses its inspected run retention. Cancellation/publication and native Tests-tab acceptance remain
6.4. Cache restore/save time is read from native task logs, not fabricated inside the local helper.

## Local Verification And Remaining Evidence

Focused bootstrap regressions pass **26 cases on Windows and Linux**. Six new cases are registered
through the existing `python-bootstrap` group/file: stable/platform-separated keys, changed-input
invalidation, unsafe labels, corruption rejection and explicit verified recovery. No new group or
language-neutral conformance fixture is added. Linux uses the prepared native interpreter with the
source file mounted from Windows and synthetic fixtures under Linux temporary storage; these are
functional checks, not native-filesystem benchmark samples.

An actual local offline pilot created its dedicated fresh Python environment from existing verified
wheels and verified exact PS module imports. It passed; its local supplied hit flag demonstrates the
bootstrap path, **not a GitHub/ADO cache hit**. Evidence is ignored under `.tmp/ci-cache-pilot` and
the new environment is owned under `.local/ci-environments`; unrelated prepared environments remain.

The initial publication, optional pipeline setup and scoped partial-publication recovery below are
now proved by the hosted/fixture evidence that follows. Before closing 6.1:

1. Confirm/publish the staged files through the normal dual push and verify exact branch parity.
2. Create the nonrequired ADO cache-pilot pipeline at the published modernization ref; record its
   pipeline ID, actual permissions, queued source revision, agent OS/version and run URLs.
3. Run both OS legs on both hosts: fresh namespace with `expect=miss`, the same namespace/key with
   `expect=hit`, then a new namespace with `expect=miss`. Capture queue, runtime acquisition,
   payload acquisition, environment creation, verification, cache restore/save and diagnostic upload
   durations separately. A failed expected hit is a failed experiment, not a silent online fallback.
4. Demonstrate hosted corruption/missing-provenance refusal and explicit recovery using a new cache
   namespace/fresh owned workspace; preserve failure evidence. Do not delete arbitrary caches or
   repair cached bytes implicitly. Complete scoped partial-publication recovery proof.
5. Qualify remaining build/render payload transport and exact Node/npm/browser provisioning; recheck
   real agent fonts/shared libraries and browser isolation. Carry observed costs into 6.5 admission.
6. Open the authorized draft GitHub/framework-target and ADO validation PRs when PR shadow wiring
   needs them at 6.2/6.3; attach the GitHub PR and record both links. Never merge independently in ADO.

**Rollback:** Disable/remove only this optional pilot and its later-created pipeline. Preserve old
CI, required identities, shared branch history and unrelated caches. No adoption decision depends
on a hosted measurement that has not yet happened.

## First Hosted Experiments And Isolation Correction

The reviewed eight-file pilot was committed and published as `6b884da` on both hosts. The worktree
was clean after publication. Optional Azure pipeline **2**, `LoTM CI Cache Pilot`, was created without
an initial run and set to queue 39/pool 9 before launch. The CLI initially selected a legacy queue;
that default was corrected on this new pipeline only. Both OS agent allocations are now observed.
Its repository/default ref is the modernization branch; no trigger, schedule, policy, service
connection or repository permission was added.

| Experiment at `6b884da` | Windows | Linux | Evidence |
| --- | --- | --- | --- |
| GitHub cold, `pilot-1` | Miss; setup passed, verified payloads saved | Miss; PS module provenance failed, cache save skipped | [Run 37564995939](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37564995939) |
| GitHub expected warm, same key | Hit; offline fresh environment passed | Miss correctly rejected by the required-hit assertion | [Run 37565381968](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37565381968) |
| ADO cold, `pilot-1` | Miss; setup passed, verified payloads saved | Miss; same PS module provenance failure | [Run 34](https://dev.azure.com/DreamtechADO/LoTM%20Inspired%20KM%20Platform/_build/results?buildId=34) |
| ADO expected warm, same key | Hit; offline fresh environment passed | Miss correctly rejected by the required-hit assertion | [Run 35](https://dev.azure.com/DreamtechADO/LoTM%20Inspired%20KM%20Platform/_build/results?buildId=35) |

Both cold runs retained success/failure diagnostics. GitHub manual dispatch against this feature
branch succeeded; no default-branch workflow merge was needed. The combined runs remain failed
because their Linux obligations failed. Individual Windows success is not a passing dual-OS gate.
ADO's exact Python pin produced the task's usual patch-pin/download-limit warnings but successfully
installed 3.14.5; no floating version or stored download credential was substituted.

GitHub Windows setup measured 22.355 seconds cold versus 12.622 warm; the warm restore task took
approximately two seconds. These are single setup samples at this snapshot, excluding checkout,
Python setup, queue and publication; they are not full-suite or median performance claims. ADO
Windows setup measured 25.731 seconds cold versus 12.613 warm; its warm restore task took 5.673
seconds. Cache transport overhead must be included before claiming net savings. Exact task timestamps, bootstrap metadata, cache keys
and native outcomes are retained under ignored `.tmp/ci-phase61`.

Both Linux agents loaded equal-version PSScriptAnalyzer 1.25.0 from
`/usr/local/share/powershell/Modules` rather than the receipt-verified owned cache. The existing
origin check rejected it. Inherited `PSModulePath` is insufficient when PowerShell startup inserts
agent paths. The scoped correction passes the intended module path explicitly into the probe and
sets it inside the child after startup; the original exact-version and owned-origin checks remain.

The correction was **confirmed and published as `c4972f8`**, with local/upstream/GitHub/ADO parity.
Its synthetic Pester regression proves an equal-version shadow module wins in the
negative control, then the explicit owned path wins. All four dependency cases pass on Windows/Linux;
26 Python bootstrap cases still pass, and a real Windows offline bootstrap check passes. No host
module is removed or modified. The existing dependency group owns the additional case.

The publication invalidated the transport key automatically because both bootstrap and probe bytes
are keyed. Corrected hosted proof below resolves this specific probe failure. Production adapters
still need their own module-origin and startup isolation proof at 6.2/6.3; a passing setup probe
does not certify every future PowerShell child entry point.

## Corrected Core Payload Checkpoint

The maintainer confirmed this bounded core-payload evidence checkpoint on 2026-10-06. Confirmation
publishes the evidence and authorizes continuing the remaining 6.1 work; it does not close 6.1.

All eight experiments at exact source `c4972f8f8fe5e2b6694403c12cc813d1dc788451` pass. Every cold
leg asserted a miss, every warm leg asserted a hit, and every warm bootstrap ran offline. Each
created a fresh environment; no virtual environment was transported. Both hosts share the same
platform key, with distinct Windows/Linux keys. Artifact audit verifies CPython 3.14.5, Core 7.6.6,
Pester 6.2.0, PSScriptAnalyzer 1.25.0, powershell-yaml 0.4.12, empty warm Python acquisition, intact
module receipts and imported module paths inside the owned cache.

| Host / OS | Cold bootstrap | Warm bootstrap | Warm restore | Cold save |
| --- | ---: | ---: | ---: | ---: |
| GitHub Windows | 22.708s | 12.030s | ~1s | ~2s |
| GitHub Linux | 25.686s | 11.088s | ~1s | ~1s |
| ADO Windows | 26.693s | 12.325s | 5.440s | 5.773s |
| ADO Linux | 22.454s | 12.701s | 5.747s | 9.773s |

Bootstrap is the helper's measured setup interval, including its runtime check and repository
bootstrap. Restore/save are separate native task durations. GitHub timestamps have one-second
resolution, hence approximate transport values. ADO save values are the whole cold post-cache
task; warm post-cache tasks still cost 1.450s/1.260s on Windows/Linux despite no new payload save.
Cold restores also cost 1.647s/2.033s in ADO. These are single samples, not medians or a promise
of steady-state performance. They demonstrate beneficial core payload reuse on the tested agents;
remaining payloads require separate measurements.

Python provisioning remains outside this payload cache: GitHub measured 45s/47s Windows cold/warm
and 9s/11s Linux; ADO measured 51.693s/51.087s Windows and 13.093s/12.087s Linux. Checkout, task
wrappers, diagnostic upload and queue/allocation delays also remain separate. Do not attribute
interpreter acquisition to test execution or claim that a twelve-second bootstrap is the complete
CI job. Retain provisional setup admission until all required dependencies are measured at 6.5.

Corrected run links:

- [GitHub cold 37566066281](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37566066281)
- [GitHub warm 37566222253](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37566222253)
- [ADO cold 36](https://dev.azure.com/DreamtechADO/LoTM%20Inspired%20KM%20Platform/_build/results?buildId=36)
- [ADO warm 37](https://dev.azure.com/DreamtechADO/LoTM%20Inspired%20KM%20Platform/_build/results?buildId=37)

Audited artifacts and sanitized task timings are retained under ignored `.tmp/ci-phase61`;
`fixed-cache-audit.json` records all eight results. Both failed original-source experiments remain
available; they are not overwritten by the corrected success. No hosted jobs are still running.

**At this core-only checkpoint, 6.1 was still open.** Remaining work included build/render payload transport and actual agent
Node/npm/Chrome/font/library qualification, deliberate cached-byte/missing-receipt rejection and
recovery controls, complete queue/setup/restore/save/publication accounting, and final readiness
review. Draft PRs remain conditional on needing actual PR shadow wiring at 6.2/6.3. Original check
names, event ownership, branch protection and canonical sources are unchanged.

## Complete Payload And Negative-Control Pilot Preparation

The maintainer confirmed this increment for publication and hosted experiments. It was published
as `ba6047a`; the complete qualification below supersedes its earlier local-only preparation status.
It extends the same
optional pilot with `payload_profile=complete` and bounded `fault=none|wheel|module-receipt` inputs.
These are dependency-setup controls, not execution-profile membership or new semantic suites.

Complete setup invokes existing bootstrap owners for development/media + PS modules, a fresh
build-only wheel, and a fresh locked npm/Chrome environment. Core and complete payload identities
are separate. Verified tool archives join wheels, PS module receipts, npm downloads and Chrome
content under `.local/ci-cache`; extracted tools, venvs, node_modules, built wheels and reports are
not transported. Node 24.15.0/npm 11.12.1 comes from the hash-pinned official x64 archive, extracted
into owned `.local/ci-tools` storage and checked by a content receipt before local reuse. No machine
installation occurs. [Official Node checksums](https://nodejs.org/dist/v24.15.0/SHASUMS256.txt).

After bootstrap, the real Mermaid CLI renders a tiny synthetic SVG using the verified Chrome
executable. Labels and positive geometry must match. Linux records `ldd` and requires an
Arial-compatible font through `fc-match`; Windows checks its Arial font. Chrome-only configuration
and the existing Linux launch flags remain unchanged. Missing libraries/fonts fail explicitly;
this pilot performs no implicit system-package installation or changes to canonical diagrams.

Faults require an asserted restored hit, a nonlocal host, and the explicit hosted-pilot marker.
They either corrupt the exact locked PyYAML wheel or remove the exact selected PS content receipt
inside the ephemeral restored workspace. Bootstrap then runs offline; ordinary nonzero failure
must remain the host outcome, with complete diagnostics and no cache save. Server caches are
immutable, so a later fresh-workspace recovery can reuse the original intact payload. Tests never
mutate primary local caches or delete arbitrary cache keys. Operator-selected namespace recovery
also remains available when a new acquisition is needed.

The helper imposes a 900-second setup deadline, retains shorter inherited deadlines, and caps
each bootstrap child at 720 seconds or the remaining budget. Existing 20-minute host jobs retain
time for provisioning/transport/publication. Selected bootstrap stages aggregate ordinary failures
and continue independent build/render diagnostics. Timeout partial stdout/stderr is retained;
full production cancellation/process lifecycle acceptance remains with 6.4.

Local preparation passes all 30 focused Python cases on Windows/Linux, adding four meaningful
archive/provenance/fault safety cases within the existing bootstrap group. Offline complete
development/build/render preparation passed on Windows and on a new native Linux source fixture;
real CLI/font/library qualification passed separately on both OSs. Windows preparation measured
309.203s versus 32.409s Linux, before the final additional owned-Node provisioning/CLI checks.
These are local staged samples, not final-source hosted costs. Windows fresh rendering alone cost
268.481s, reinforcing why 6.1 must measure actual agents rather than transferring WSL timings.
Pinned owned Node/npm extraction and strict offline receipt reuse are additionally verified.

The published increment required complete cold and warm setup on
both hosts/OSs, explicit wheel-corruption and missing-receipt failures, and successful subsequent
fresh-workspace recovery. Audit source/key/package/tool identities, render output, queue delay,
runtime provisioning, bootstrap stages, cache restore/save and publication. A failed control is
evidence only when its expected diagnostic is present; it must not be converted into a green run.

Checkpoint verification: repository Ruff lint, both changed Python files' formatting, actionlint across
all workflows, annotation policy (22/22 fixtures, 478 files, zero findings), 101 relative file links,
pilot YAML/permission/pin/timeout invariants and `git diff --check` pass. These static checks do not
certify Azure server YAML compilation, successful agent allocation or cache transport performance.

## Complete Hosted Qualification And 6.1 Review

Every job below executes exact source `ba6047ab0f815be30a03f29750565755226c6764` on
`windows-2022` or `ubuntu-24.04`, using `payload_profile=complete` and namespace `complete-1`.
Cold legs assert a miss. All later legs assert the same platform-specific hit and run offline.
An independent artifact audit verifies all twenty outcomes: twelve positive passes and eight
expected negative failures. Windows/Linux keys differ; corresponding keys match across hosts.

| Experiment | GitHub, both OSs | ADO, both OSs | Audited result |
| --- | --- | --- | --- |
| Cold | [37569838976](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37569838976) | [38](https://dev.azure.com/DreamtechADO/LoTM%20Inspired%20KM%20Platform/_build/results?buildId=38) | Miss; acquisition, qualification and save succeed. |
| Warm | [37570086850](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37570086850) | [39](https://dev.azure.com/DreamtechADO/LoTM%20Inspired%20KM%20Platform/_build/results?buildId=39) | Hit; fresh offline environments and qualification succeed. |
| Corrupt wheel | [37570296299](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37570296299) | [40](https://dev.azure.com/DreamtechADO/LoTM%20Inspired%20KM%20Platform/_build/results?buildId=40) | Red, exit 1; exactly one bootstrap error: `Corrupt cached wheel`. |
| Missing module receipt | [37570302528](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37570302528) | [41](https://dev.azure.com/DreamtechADO/LoTM%20Inspired%20KM%20Platform/_build/results?buildId=41) | Red, exit 1; exactly one bootstrap error: `Module cache unavailable offline`. |
| Fresh-workspace recovery | [37570659120](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37570659120) | [42](https://dev.azure.com/DreamtechADO/LoTM%20Inspired%20KM%20Platform/_build/results?buildId=42) | Hit; intact immutable server payload succeeds without repair/deletion. |

Every positive leg creates a fresh Python environment, build-only Python 0.1.0 wheel and locked
node_modules tree. Verified versions are CPython 3.14.5, PowerShell 7.6.6, Pester 6.2.0,
PSScriptAnalyzer 1.25.0, powershell-yaml 0.4.12, owned Node 24.15.0/npm 11.12.1,
Puppeteer 25.3.0 and Chrome 150.0.7871.24. Module origins and receipts remain owned and verified.
The real Mermaid CLI renders expected labels with positive finite SVG geometry; Windows Arial
and Linux Arial-compatible Liberation Sans qualify, with no missing Linux shared libraries.
No agent system package or global module installation is changed.

Negative legs retain the expected error and complete diagnostics, continue independent build/render
qualification, remain failed at the host, and skip cache saving. Subsequent recovery is a new agent
workspace using the same server key. It proves refusal and safe recovery, not implicit cache repair.
Code/input invalidation is additionally established by the earlier corrected-core key change and
the local changed-input regression. Historical first-source failures remain available.

| Host / OS | Cold setup | Warm setup | Recovery setup | Warm restore | Cold save | Cold / warm job |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GitHub Windows | 68.594s | 51.901s | 52.071s | ~6s | ~6s | 138s / 118s |
| GitHub Linux | 56.341s | 19.782s | 34.948s | ~4s | ~4s | 87s / 43s |
| ADO Windows | 79.174s | 57.647s | 56.816s | 10.450s | 26.770s | 181.580s / 143.647s |
| ADO Linux | 57.252s | 39.062s | 38.655s | 11.257s | 23.357s | 108.010s / 76.327s |

Setup is the measured helper interval, including owned tool provisioning, bootstrap stages and real
render qualification. Native restore/save and job intervals are independent measurements. ADO cold
restores cost 1.697s/1.550s and warm post-cache tasks 1.400s/0.987s (Windows/Linux). Diagnostic
artifact tasks cost approximately 0-1s on GitHub and 1.950-2.807s on ADO for cold/warm jobs.
Warm reuse improves both setup plus transport and whole-job cost in all four comparisons. These
are single samples, not medians, guaranteed savings or full-profile timings. GitHub complete caches
occupy 361,072,281 bytes Windows / 358,384,362 bytes Linux; transport is material at this size.

Exact CPython provisioning remains separate: cold/warm GitHub Windows 47s/46s, Linux 12s/8s;
ADO Windows 50.563s/50.290s, Linux 12.400s/11.307s. Warm caching does not remove interpreter
provisioning or fresh environment installation. Native timelines preserve checkout, key preparation,
task wrappers, post-job work and artifact upload separately. Dispatch-to-job-start elapsed is
GitHub 2-6s for cold/warm/recovery and ADO 7.823-470.534s, including allocation, matrix serialization
and waiting behind other experiments; it is not pure queue time or computation. ADO recovery jobs
take 144.463s Windows / 80.303s Linux. The shared one-slot entitlement remains consequential.

Final readiness refresh confirms the existing empty GitHub ruleset/framework-protection and ADO
repository-policy inventories, optional pipeline 2 at queue 39/pool 9 and the modernization ref.
Actual checkout, cache and artifact permissions are proved by execution. No broad authorization,
service connection, policy, required check, schedule or merge authority changes. Granular future
build-validation/token configuration is not inferred from these effective setup permissions.
No custom agent image or internal feed is justified by these bounded samples; revisit only after
real profile/shard measurement at 6.5. Provisional budgets and 90s/960s goals remain unchanged.

Audited reports, sanitized native timelines and independent audit summaries are retained under
ignored `.tmp/ci-phase61/complete` (`audit.json`, `timing-audit.json`). All required 6.1 runtime
work is complete. The maintainer confirms the final documentation and verified checklist on 2026-10-07.
Draft GitHub/framework and matching ADO validation PRs are conditionally deferred to actual PR
shadow wiring at 6.2/6.3; cache qualification needed neither. Phase 6.2 has not started. Production
child module isolation, profile equivalence, Tests-tab/Markdown publication, cancellation and final
host admission remain their explicit later gates. Retire this optional pilot after adopted transport
has equivalent evidence; preserve original CI until the accepted migration gate.
