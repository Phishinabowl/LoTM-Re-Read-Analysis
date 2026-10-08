# Pinned Python Acquisition Proposal

Status: pilot design approved by the maintainer on 2026-10-07; not an adopted acquisition backend.
Scope: the CI modernization Phase 6.5
interpreter acquisition gate. The adopted interpreter remains Python 3.14.8; project environments
continue using the existing pip 26.2 and dependency locks. Catalogs, profile coverage and runtime
support boundaries are unchanged. This proposal introduces no secret, agent, machine installation,
runtime cache, workflow change or hosted run.

## Confirmed Current Behavior

Azure reference run 68 spends 45.693s, 44.163s and 44.283s in its three `UsePythonVersion@0` tasks.
Its worker log identifies the upstream release `3.14.8-36806082737`. Download/extraction precedes
installer output after roughly five seconds; Windows installation then takes about 28 seconds,
followed by a base pip refresh. Archive caching alone would leave most of that measured work.

The same log shows the upstream setup replacing the agent's Python 3.14.7 tool-cache installation
and editing Python installer registry entries. It refreshes base pip to 26.2.1. This base pip is not
the admitted project dependency environment: our existing bootstrap creates fresh environments
and installs the locked pip 26.2 and package versions before verification.

The [Azure task source](https://github.com/microsoft/azure-pipelines-tasks/blob/389757b9654242a29846d88d8d59fb6ca83617a2/Tasks/UsePythonVersionV0/usepythonversion.ts)
emits the exact-version warning before looking for an installed interpreter. Its
[download implementation](https://github.com/microsoft/azure-pipelines-tasks/blob/389757b9654242a29846d88d8d59fb6ca83617a2/Tasks/UsePythonVersionV0/installpythonversion.ts)
uses the Actions Python registry and emits the missing-token warning only on registry acquisition.
Setting `disableDownloadFromRegistry` or restoring a cache therefore does not, by itself, remove
the exact-version warning. Treat the two warnings as separate dispositions.

The [upstream Windows installer](https://github.com/actions/python-versions/blob/77ca8ada59c43eeb7af4c21e3bd55f6a2c65847b/installers/win-setup-template.ps1)
confirms the installation/registry behavior. Its [Linux installer](https://github.com/actions/python-versions/blob/77ca8ada59c43eeb7af4c21e3bd55f6a2c65847b/installers/nix-setup-template.sh)
copies a runtime tree into the tool cache, creates links and refreshes pip. These were inspected as
text only. Do not run either installer on the developer PC or WSL to simulate a hosted agent.
The native Windows task's internal bootstrap implementation does not restore a repository-owned
Windows PowerShell 5.1 support lane.

## Options And Recommended First Experiment

| Option | Likely benefit | Boundary or cost |
| --- | --- | --- |
| Keep native acquisition and add download authentication | Addresses anonymous registry limits | Does not remove installation work or the exact-pin warning; requires a separately reviewed hosted secret |
| Cache only the upstream installer archive | Avoids repeated archive transfer | Windows reinstall and base pip refresh remain |
| Cache the verified completed native interpreter | Can avoid reinstalling a missing pinned interpreter on later agents | Must qualify integrity, fixed-prefix compatibility, platform-specific restoration and restore/save costs |
| Replace native acquisition with a new portable distribution | Could avoid native installer behavior | Changes distribution/provider and creates more acquisition maintenance; requires separate review |
| Introduce managed/self-hosted images | Moves provisioning out of every run | Adds ongoing infrastructure ownership; outside this increment |

Recommend an opt-in Azure pilot of the completed native interpreter cache first. Keep native
acquisition as the current default and explicit rollback. Measure the candidate before changing
the ordinary CI adapter. GitHub keeps `setup-python` during this experiment; evaluate an equivalent
optimization there only if its observed acquisition cost warrants it.

This is a hosted provisioning optimization. Local runner reproduction continues using an explicitly
selected, verified Python 3.14.8 and the same project bootstrap/locks. Local tests exercise the
cache controller against private fixture directories; they do not alter a real agent tool cache.

## Candidate Contract To Qualify

1. Read the exact version from `runtime-versions.json` before requiring Python. Use PS7-compatible
   orchestration and standard facilities already present on the approved hosted images. Keep the
   pilot helper isolated from framework runtime APIs and catalog membership semantics.
2. Restrict the pilot to explicit manual execution on Microsoft-hosted Windows 2022 and Ubuntu
   24.04 x64. Use ordinary, non-free-threaded CPython. Reject local/self-hosted use of the native
   installation path. Keep both existing PRs paused.
3. Restore only a version-specific sealed runtime payload and its provenance/integrity inventory;
   do not cache the whole agent tool cache, project environments, source trees or credentials.
   Key by OS/image family, architecture, exact interpreter version, provider/build identity and
   acquisition contract/inventory revision. Use exact keys without broader-version restore keys.
4. Verify the cached inventory against a trusted source-controlled seal before executing restored
   files. A manifest supplied only by the same cache is not its own trust anchor. The first pilot
   must establish whether a reproducible inventory is feasible after excluding mutable generated
   files from the payload. If it is not, keep this option unadopted and review an immutable artifact
   or archive-import alternative rather than weakening integrity checks.
5. Restore into a new staging owner, verify the complete payload, and admit only the exact version's
   compatible tool-cache location on an ephemeral agent. Do not overwrite existing host-owned
   installations or clean unrelated patch versions. Qualify fixed-prefix bindings, symlinks and
   Windows direct execution before treating the tree as portable between agents. Do not carry
   these operations over to the developer PC or WSL.
6. On a clean miss, use the existing native task on the ephemeral agent and verify the resulting
   runtime. Capturing a candidate must not imply it matches a trusted seal; record mismatches as
   explicit qualification failures. Failed/corrupt/partial restoration must not execute its payload,
   save a new cache, silently select another Python version or overwrite an existing installation.
7. Probe the selected interpreter's exact version, architecture, executable/prefix ownership,
   standard-library imports, SSL, SQLite, `venv` and `ensurepip`. Then reproduce the existing fresh
   project environment with locked pip/dependencies and verify package imports. Prefer executable
   paths and `python -m ...`; do not rely on relocated console-script launchers.
8. Produce an acquisition receipt with source, mode, provider, pin, image/OS/architecture, payload
   identity, actual cache hit/miss, validation results and separate acquisition/restore/save timings.
   Retain bounded setup failure evidence and honest exit status. Receipt acceptance precedes handing
   the interpreter to planning, workers or collection.

## Warning And Credential Disposition

Keep the exact Python pin. If the native task is retained as selector, its exact-version warning
remains expected and must be documented rather than hidden by broadening `versionSpec`. If the
pilot eventually selects a verified restored interpreter directly, it may skip that task only after
proving the same handoff contract; the cold native path still has its documented warning.

An actual verified cache hit can avoid registry downloads; a cold miss still needs acquisition.
Start without creating a credential. Record registry/download failures and prohibit silent fallback.
If hosted acquisition requires authentication for reliable cold recovery, review a narrowly scoped
host-managed GitHub download credential separately. Do not reuse `System.AccessToken`, repurpose
an existing service connection, write a token into YAML/receipts or forward it to execution children.
This pilot must not claim the registry reliability gate closed from warm-only evidence.

## Qualification Sequence And Rollback

1. Implement controller/receipt tests using private fixtures: correct hit/miss, missing interpreter,
   wrong version/architecture/prefix, corrupt/missing/extra payload files, unsafe links/paths,
   incomplete seals, acquisition failure and cancellation/cleanup. Use Pester for PS7 implementation
   contracts; retain existing Python bootstrap/transport regressions. Approve catalog registration
   for any new implementation tests before hosted adoption.
2. Inspect exact upstream archive contents without executing installers. Confirm extraction shape,
   source identity and supplied SHA-256 against downloaded bytes. Resolve the inventory/seal design
   using concrete candidates before wiring cache execution. No new machine installation is authorized
   by this design checkpoint.
3. Publish an opt-in bounded Azure pilot only after local review. Run cold and warm qualification on
   both supported hosted OSs, then controlled corruption/missing-receipt and recovery probes. Include
   a case where the exact interpreter is absent from the image; a preinstalled image is insufficient
   proof of the restoration path. Do not remove other image runtimes to manufacture that condition.
4. Measure acquisition, restore, extraction/admission, environment verification and cache-save costs
   separately. [Azure caching guidance](https://learn.microsoft.com/en-us/azure/devops/pipelines/release/caching?view=azure-devops)
   calls for benefit exceeding restore/save overhead. Do not extrapolate observed near-instant native
   selection into a guaranteed saving.
5. On acceptance, qualify the existing complete infrastructure profile through the opt-in candidate
   at the same source as native reference, including original test/XML identities, aggregate-only
   publication and failure behavior. Qualify planning, ordinary workers, cohort workers and collector
   handoffs before making the candidate a default. Broader full/event/policy qualification remains open.

Rollback is explicit native acquisition plus retained original templates. Candidate integrity or
qualification failures leave native mode active. No change to Python 3.14.8, pip/dependency locks,
required check names, branch protection, test isolation or coverage is approved by this proposal.

## Read-Only Upstream Asset Snapshot

The registry metadata inspected on 2026-10-07 identifies these candidate assets at release
`3.14.8-36806082737`. Values below are supplied upstream metadata, not independently recomputed
downloaded-byte hashes and not yet adopted locks.

| Candidate | Archive bytes | Upstream SHA-256 |
| --- | ---: | --- |
| `python-3.14.8-win32-x64.zip` | 33,100,332 | `2b7a12a17729d1833b81f84396254fb4d5b4f239fd851e6e3f4e3407fe51599c` |
| `python-3.14.8-linux-24.04-x64.tar.gz` | 110,382,248 | `fa74abc70a55c10f6631967784878704eef81bbde9b8ec27469534f6ba997cb3` |

Sources: [upstream release](https://github.com/actions/python-versions/releases/tag/3.14.8-36806082737),
[registry snapshot](https://github.com/actions/python-versions/blob/77ca8ada59c43eeb7af4c21e3bd55f6a2c65847b/versions-manifest.json),
[Azure task documentation](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-python-version-v0?view=azure-pipelines).
Read-only source snapshots and run 68's worker acquisition log remain under ignored `.tmp/ci-phase65`.

## First Local Admission Increment

The approved design is dual-published as `571a488` on 2026-10-07. The first implementation prepares
`Tools/CI/PythonRuntimeCache.ps1` as a read-only library, with no network/installer/restore/probe
execution. It reads the adopted pin through its authoritative runtime-versions input, constructs
exact metadata-bound cache identities, inventories files/directories and qualified relative file
links in ordinal order, and compares the inventory digest against an external trusted seal.
Clean misses request native acquisition; verified hits stop at `probe-required`. Receipts validate
capability/prefix evidence but always withhold environment handoff and cache saving in this increment.

The new Pester file is registered in the existing `powershell-dependencies` group; no new aggregate
unit, profile, shard, timeout or required check is added. The group's 47 new cases and five existing
cases pass through the original native adapter on both OSs: 52/52, zero skips/errors (Windows 6.152s,
Linux 16.516s), including unique native identities and JUnit/phase admission. Catalog and focused
clean-checkout planning regressions pass 89 cases per OS (Windows 48.38s, Linux 38.11s). The clean
fixture explicitly includes the new registered source files during pre-publication review.
Repository PowerShell formatting, Python formatting/lint, work-annotation policy/22 fixtures and
diff checks pass. No broader suite is repeated for this isolated foundation.

The filesystem proof includes actual Windows junction/Linux directory-link owners and actual
hard-linked files. Regular Unix directory link counts are preserved; linked files are rejected.
Absolute/chained/directory links and nonregular files remain unqualified/rejected. Relative file
link handling also has targeted metadata fixtures. These conservative limits are not evidence
that the actual upstream installed tree already fits the contract: Windows fixed-prefix aliases,
mutable generated files, repeatable sealing and exact archive contents remain to be qualified.
No actual runtime seal is adopted, no cached Python is executed and no host cache is restored.
Changes remain uncommitted for review; native hosted setup and both paused PRs remain unchanged.

## Verified Archive Inspection And Remaining Seal Gate

The first admission implementation is confirmed and dual-published as `8719f8d` on 2026-10-07;
HEAD, upstream and both destination refs agree. The subsequent read-only inspection downloads both
exact assets into ignored `.tmp/ci-phase65/runtime-archive-inspection` and independently recomputes
their sizes and SHA-256 values. Both match the upstream values in the snapshot table. They remain
inspection evidence, not adopted runtime-cache seals. Archive members are read as data; no installer
or archived executable is run and no runtime is extracted or restored into a machine/tool-cache tree.

| Confirmed archive property | Consequence for the candidate |
| --- | --- |
| Windows ZIP has exactly two entries: a 33,387,464-byte installer EXE and a 6,820-byte `setup.ps1` | Its archive digest authenticates the installer input, not the completed runtime inventory. Capture must occur on an ephemeral hosted agent. |
| The exact Windows setup deletes other same-minor tool-cache trees, changes installer registry entries, creates an absolute `python3.exe` alias and upgrades base pip without a version pin | Keep it off developer machines. Completed-tree capture needs an explicitly qualified alias/pip disposition; the current admission library rejects the absolute alias. |
| Linux archive has 9,787 members: 9,290 files, 489 directories and eight relative direct-file symlinks; no hard links or special nodes | Its link shapes fit the conservative link policy in principle, but archive member shape alone is not filesystem admission or execution proof. |
| Linux archive includes 5,996 `.pyc` files and an existing pip installation | A repeatable completed seal needs a reviewed generated-file and base-pip policy. Do not exclude arbitrary differences just to make captures match. |
| Linux launchers/pkg-config data and binary strings name `/opt/hostedtoolcache/Python/3.14.8/x64` | Treat the candidate as prefix-bound. Continue using explicit executable paths and `python -m ...`; relocation is unqualified. |
| Linux modes distinguish executables and data; its largest member is a 73,046,056-byte static library | The current file-size bound accommodates this archive. Runtime restoration still needs mode preservation/verification; the first inventory digest does not seal Unix permission bits. |

Before restoration wiring, prepare a bounded capture-only hosted experiment with a concrete
normalization contract for review. Record raw inventory first, then explain every proposed change:
generated bytecode, native pip refresh outputs, prefix-bound aliases and executable modes. Retain
the bundled `ensurepip` wheels and standard-library sources. Keep project environments outside the
payload. Two independent captures per OS must establish whether that contract produces identical
inventories; a single capture or a cache-owned manifest cannot establish a trusted seal. Capture
results must not authorize execution of restored bytes or mark handoff admitted.

If completed-tree reproducibility fails, retain native acquisition and review the immutable-artifact
or archive-import alternative specified above. Do not weaken seal checks, silently expand link
acceptance or adopt a floating pip dependency. Hosted capture implementation/publication, external
seal adoption, actual restoration/probes and cold/warm/failure/recovery measurements remain open.

## Capture-Only Pilot Prepared For Review

The next increment prepares `.azuredevops/ci-runtime-capture.yml` as a dedicated manual-only
experiment, with two separately allocated Windows 2022 jobs and two Ubuntu 24.04 jobs at the same
source. It has no push/PR/schedule trigger, cache task or validation policy. Matrix concurrency is
one; each job has a 15-minute hard limit and two-minute cancellation allowance. Expected cost must
be measured from the actual run; the maximum four-job allocation is not a timing prediction.
The existing CI and cache-pilot pipeline definitions are unchanged. A temporary Azure definition
will be registered only after publication approval, and its first preview must corroborate the four
matrix allocations and exact source before a single bounded run is queued.

The job reads the exact authoritative Python pin using the image's PS7 before invoking the existing
native task. `Capture-PythonRuntime.ps1` then checks manual pilot context, checkout ownership and the
native-selected exact tool-cache prefix. It reads the resulting tree without executing Python,
installing project dependencies, editing native files or restoring a cached tree. New evidence is
written only to a fresh ignored capture-output owner. Collection has a five-minute cooperative
deadline; the job limit bounds native setup as well. Capture errors retain bounded failure JSON and
the original failed task outcome. Native task logs remain the acquisition evidence if setup fails.

**Normalization contract for this first measurement: none.** Retain every inventoried file and
directory, including bytecode, base pip, bundled ensurepip and the observed native aliases. Include
Unix permission bits on regular files/directories in capture inventory schema 2. On Windows, only
the exact absolute `python3.exe` link to the same owner's regular `python.exe` may be *recorded*;
all other unsafe links remain rejected. Its absolute target remains visible in the evidence.
Strict cache admission uses its original schema/policy and still rejects that absolute alias.
No filesystem file is omitted, rewritten, copied or removed by the capture collector.

The capture receipt explicitly withholds provider-build verification, runtime-probe verification,
trusted seal, save and handoff admission. A native task can select an image-installed interpreter
instead of downloading the inspected release; neither its version-shaped directory nor the request
pin proves provider identity or cold acquisition. Correlate native logs/image metadata with the raw
inventories before proposing a normalized completed-payload contract. Repeated raw equality is useful
evidence but cannot alone close provider, execution or restoration qualification.

Eleven new cases cover complete raw retention, context rejection, mode-sensitive inspection,
the narrow recorded alias, cancellation/missing executable and local entry-point rejection. The
existing dependency group now has 63 cases (58 cache/capture and five dependency cases), all passing
through the original native adapter on both OSs with zero skips/errors. Initial native-adapter
measurements are Windows 6.693s and Linux 16.874s; final verification after formatting/guard review
also passes 63/63 per OS (Windows 6.219s, Linux 16.428s). YAML parses and its manual-only/four-job/no-cache
structure is checked locally; Azure service preview and live acquisition/capture remain unverified.
This increment remains uncommitted for review; neither a new definition nor hosted jobs exist yet.

## First Hosted Capture Attempt And Handoff Correction

The capture-only increment is confirmed and dual-published as `5ab075c` with all four refs matching.
The authorized temporary Azure definition is pipeline 4, `LoTM Python Runtime Capture Pilot`, with
no automatic first run. Azure's preview confirms four manual-only matrix allocations, the exact-pin
variable handoff, 15-minute limits and no cache tasks. The first run is
[70](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=70),
at exactly `5ab075c397ef8caba0f63a8574db2be0151572a6`.

Native acquisition succeeds for the two Windows jobs and first Linux job, but all three capture
steps reject the selected-prefix handoff and publish bounded failure receipts. The collector's YAML
uses unqualified `$(pythonLocation)` even though the native task declares it as an output variable.
The [Azure agent source](https://github.com/microsoft/azure-pipelines-agent/blob/master/src/Agent.Worker/ExecutionContext.cs)
qualifies declared outputs with the producing task's reference name. The task's own metadata declares
this output; [Azure documentation](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-python-version-v0?view=azure-pipelines)
describes its role. An unresolved macro can become a relative local path under `GetFullPath`, causing
the exact-prefix check to fail rather than pointing to the acquired interpreter.

Run 70 is explicitly canceled to stop repeating this shared handoff failure. Three matrix jobs
have already failed by the time cancellation takes effect; the fourth is canceled. Overall result
is canceled, elapsed queue-to-finish 187.465s. The three native tasks take 42.380s, 38.740s and 10.537s;
these are acquisition observations, not runtime cache savings. No raw runtime inventory, trusted
seal, restoration, cache save or handoff is admitted. Native logs, final timeline and all three
failure artifacts remain in ignored inspection storage. Defaults and paused PRs are unchanged.

The prepared correction explicitly names the native step `NativePython` and consumes
`$(NativePython.pythonLocation)`. A tested prefix helper rejects empty/unresolved/relative output
before path normalization, preserves exact version/architecture ownership, rejects linked owners,
and uses Windows-insensitive/Linux-sensitive path comparison. Six added cases join the existing
group; all 69 cases pass through native JUnit admission per OS, zero skips/errors (Windows 6.431s,
Linux 16.592s). A no-agent Azure preview using the corrected YAML override confirms that the named
producer and qualified consumer agree and retains all four bounded jobs with no cache tasks. This
validates service expansion only; the queued-source retry and actual runtime handoff are unverified.
The fix and updated evidence remain uncommitted for confirmation. Repeat preview
and the same four-job experiment only after publishing the corrected source; real inventories and
reproducibility/normalization qualification remain open.

## Successful Capture Retry And Bounded Normalization Candidate

The correction is confirmed and dual-published as `b5378a1`; HEAD/upstream/GitHub/Azure agree.
The published-source Azure preview confirms the qualified output, four manual allocations and no
cache tasks. [Run 71](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=71)
then succeeds at exact commit `b5378a16bfc8bce90f096fcca6eb1bb6e3296b35`, with all four original
capture artifacts retained. All inventories pass independent JSON/contract/source/pin checks,
ordinal unique-path checks and recomputation of their inventory SHA-256. Every receipt still
withholds runtime-probe/provider verification, trusted seal, cache save and handoff admission.

| Observation | Windows captures | Linux captures |
| --- | --- | --- |
| Entries in each raw inventory | 5,088 | 9,789 |
| Bytecode files in each | 575 | 5,996 |
| Different entries | 408 | 571 |
| Difference classes | 404 pip bytecode files, three pip EXE launchers and pip's `RECORD` metadata | 404 pip bytecode files and 167 standard-library bytecode files |
| Changed record fields | SHA-256 only; paths, kinds and sizes match | SHA-256 only; paths, kinds, sizes, link targets and recorded Unix modes match |
| Native task seconds, repetitions 1/2 | 0.290 / 41.553 | 9.287 / 9.567 |
| Capture-task seconds, repetitions 1/2 | 24.170 / 9.187 | 10.987 / 10.920 |
| Total job seconds, repetitions 1/2 | 42.607 / 73.670 | 29.940 / 34.093 |

Queue-to-finish is 247.377s (4m07.377s). These costs include native acquisition and read-only hashing;
they do not measure an owned runtime cache hit/restore/save. The first Windows allocation uses image
`20261004.326.1` with Python already present; the second uses `20260927.320.1` and downloads the inspected
Windows release. Both Linux allocations use `20260927.320.1` and download the inspected Linux release.
All three download logs identify `3.14.8-36806082737`. Thus this is a bounded comparison across distinct
job allocations, not a controlled same-image-version Windows cold/cold experiment. Machine names
are retained as context, not treated as unique allocation identities or proof of cache ownership.
The near-instant native selection is not an owned warm-cache result. Native pip remains 26.2.1;
fresh project environments retain their existing locked pip 26.2 policy.

**Confirmed disposition:** the complete raw trees are not reproducible seals. Do not adopt their
digests or ignore mismatches during admission. A read-only hypothetical projection of the actual
inventories nevertheless produces identical retained entries per OS under this concrete candidate:

1. Omit generated `__pycache__` bytecode only when its corresponding `.py` source is present; retain
   sourceless/input bytecode. Omit only generated cache directories that become empty.
2. Omit the complete observed native base-pip package, its distribution metadata and generated pip
   launchers as one coherent boundary, rather than retaining a broken `RECORD` or merely skipping
   failed launcher hashes. Preserve bundled `ensurepip` wheels and all other interpreter/stdlib data.
3. Recreate only the exact Windows `python3.exe` alias as the equivalent relative `python.exe` link
   in a new candidate owner. No native host tree is edited; all other link/type restrictions remain.
4. Preserve and seal Linux file/directory modes in the candidate contract. Keep exact compatible
   prefixes and provider/source identity separate from inventory equality.

This projection retains 3,758 Windows entries and 3,040 Linux entries, with exact pair equality.
It omits 1,330 Windows entries (1,012 native base-pip entries, 171 source-backed bytecode files and
147 empty generated cache directories), and 6,749 Linux entries (1,012 native base-pip entries,
5,592 source-backed bytecode files and 145 empty generated cache directories). It changes only
in-memory inventory views: no runtime is copied, removed, rewritten, executed or restored, and no
project-owned seal is generated/adopted. Raw artifacts and full difference inventories remain intact.

The existing bootstrap acquires locked wheels directly with `urllib`, creates a fresh environment
with `venv.EnvBuilder(with_pip=True)` and installs/verifies pinned pip/dependencies inside that
environment. It does not need the native base-pip installation for those steps. That source inspection
supports the proposed omission, but is not runtime evidence for a stripped candidate. Next review
this normalization contract, implement/test a private-owner candidate builder and mode-aware seal
admission, then prove real candidate execution, ensurepip/venv and locked project bootstrap on both
OSs. Retain no-bytecode execution/write controls as an explicit post-seal requirement. Repeated
normalized hosted payloads and independent trusted seals, corruption/missing-receipt recovery and
fixed-prefix restoration still precede any default change. If that proof fails, use the specified
immutable-artifact/archive-import review fallback; do not widen integrity exemptions.

Only this evidence/design update is uncommitted. No additional hosted run is queued, both PRs stay
paused and ordinary acquisition/CI remain unchanged. Phase 6.5 remains open.

## Private Candidate Builder Increment

The capture findings and normalization boundary are confirmed and dual-published as `38fddb3`;
HEAD/upstream/GitHub/Azure agree. The next local increment implements the reviewed projection and
`New-CiPythonRuntimeCandidate` in the existing CI helper, with no new workflow or machine setup.
It inventories the native source, validates one coherent base-pip distribution, builds only into
a fresh owner beneath an explicitly supplied existing scratch workspace, and writes its receipt
beside the payload. Existing/overlapping/escaping/linked owners are rejected before construction.
The source tree is never edited. Every omitted path has a reason in the receipt.

The builder preserves interpreter/stdlib/ensurepip and sourceless bytecode, omits only qualified
source-backed generated caches and the complete native base-pip installation, and recreates the
exact Windows alias as a relative file link. Copying avoids recursive source traversal. Linux file
and directory modes are preserved, with a canonical candidate-root mode of 0755. Strict inventory
schema 3 hashes those modes and the root mode together with the complete retained file/link inventory.
Capture-only and strict mode sealing cannot be combined. The original schema 1 admission behavior
remains separate; no trusted runtime seal is adopted or newly connected to cache execution here.

Candidate completion requires the materialized payload to match its projection and the source's
post-copy inventory to match its original inventory. Failed/canceled construction retains its own
partial owner and a `candidate-incomplete` receipt; no recursive cleanup or owner reuse occurs.
Successful receipts say `candidate-complete` but still withhold runtime probe, trusted seal, cache
save and handoff admission. No candidate interpreter, archived installer or copied script is executed.

Fifteen added cases cover actual private materialization and file links on both OSs, exact relative
Windows alias conversion, source preservation, retention of sourceless inputs/ensurepip/preexisting
empty caches, repeatability across generated-file changes, retained-source sensitivity, fresh-owner
containment, required-input/ambiguous-metadata rejection, actual retained-file corruption, pre-build
and mid-copy cancellation, incomplete receipt/reuse rejection, and Unix file/root mode sensitivity.
They remain in the existing dependency group with its original deadline and aggregate membership.
All 84 registered cases pass through native JUnit admission per OS (79 cache/capture/builder and five
dependency cases), zero skips/errors. Final verification takes 9.629s on Windows and 17.926s on Linux.
Formatting, annotation policy/22 fixtures and documentation checks pass.

The actual implementation also projects both retained run-71 inventories per OS as data only; each
pair has matching schema-3 digests. Linux retains 3,040 entries and omits 6,749, as the exploratory view
did. Windows retains 3,878 and omits 1,210: it preserves 120 directories that were already empty in the
native source, instead of treating them as directories made empty by omission. Its omission ledger
contains 1,012 native base-pip entries, 171 source-backed bytecode files and 27 newly empty cache
directories. This is a conservative refinement of the initial hypothetical count, consistent with
the approved rule to omit only generated directories that become empty. Captured records are not
copied runtime bytes; matching projections are not provider, executable or restoration qualification.

This five-file code/test/evidence increment is uncommitted for review. No hosted jobs are queued.
Next qualify actual normalized hosted payloads and ensurepip/venv/locked bootstrap, then connect
reviewed mode-aware external seals and fixed-prefix restore admission. Keep post-seal no-bytecode
controls, source/provider identity, corruption/recovery, measured cache benefit and the native rollback
as open gates. Phase 6.5 stays open; ordinary CI, defaults and paused PRs are unchanged.

## Opt-In Hosted Candidate Qualification Pilot

The private builder is confirmed and dual-published as `c743f42`, with four-ref parity. The next
increment adds explicit `mode: candidate` to the same temporary manual pipeline; `raw` remains
the default. Its four matrix allocations and 15-minute job limits are retained. No cache task,
required check, production adapter or schedule is introduced. The entry point first retains the
raw inventory, builds a normalized candidate into a separate fresh ignored owner and publishes
only the receipt/qualification/process-diagnostic folder. Candidate runtime bytes stay on the
ephemeral agent and are not uploaded as artifacts by this experiment.

The native-selected interpreter supervises candidate execution through the existing owned process
primitive. A Python verifier checks the complete schema-3 inventory, hashes, unique ordinal paths,
links, hard-link restrictions and Unix modes before launch and between stages. Child environments
use an allowlist without credentials, inherited Python paths or inherited loader overrides. On
Linux, the explicit candidate library directory is the loader path. The isolated `-B` probe requires
exact CPython/x64/GIL/version/prefix/executable ownership, file-backed SSL/SQLite/venv/ensurepip modules,
absence of base pip and a Python DLL/shared library loaded from the candidate owner. A copied runtime
that still uses the native tree's core library does not pass this probe.

The next child runs the original hash-locked runtime-profile bootstrap, followed by a fresh-environment
probe proving that its base prefix and core library belong to the candidate. A new opt-in bootstrap
flag, `--no-base-bytecode`, uses public `venv` creation without implicit pip setup. Following the
run-72 correction described below, it runs the retained ensurepip bundled wheel directly inside an
isolated `-B` interpreter, then explicit install/check/verification commands. It requires an isolated
`-B` parent and source package mode. Ordinary default bootstrap is preserved; editable/wheel modes
remain unqualified for this opt-in flag.
Post-qualification Python and PowerShell inventories verify both the candidate and native source.

The qualification controller has a 600-second lease, per-probe 60-second limits, a bootstrap limit
of 360 seconds and the existing process-tree termination/cleanup ownership. Verification observes
the lease/cancellation; final failure verification has a 20-second allowance. Structured failure,
cancellation and timeout evidence retain honest exit codes (1, 130 and 124). The final PS inventory
checks share a two-minute deadline; the existing 15-minute job limit bounds the whole experiment.
Successful qualification still withholds provider/external-seal verification, fixed-prefix restore,
cache save and ordinary runtime handoff admission. Scratch execution is not restoration proof.

Local verification passes 53 bootstrap/qualification pytest cases per OS and all 84 registered
Pester dependency cases per OS, with zero skips/errors. Coverage includes byte/owner/mode validation,
credential/loader scrubbing, probe-output ownership, default-vs-opt-in bootstrap commands, package-mode
restriction, local CLI rejection and explicit failure/cancellation/timeout receipts. The real Windows
process probe passes against the preexisting development interpreter. The source-built WSL interpreter
has built-in SSL modules and is intentionally rejected by this Actions-distribution qualification
probe, with verified process cleanup; positive Linux candidate execution awaits the hosted release.
This is a tested refusal, not positive Linux distribution proof or a skipped test.

Real opt-in bootstrap also creates/verifies fresh local runtime-profile environments on Windows and
WSL using adopted pip 26.2/PyYAML 6.0.3 (14.648s/88.457s). Initial offline attempts correctly refuse
missing profile-specific wheels; explicit acquisition uses the existing hash locks and then succeeds.
No machine interpreter is installed or host tool cache restored. Azure's no-agent YAML override
preview accepts candidate mode, the named native output and all four bounded jobs, with no cache
task or binary upload. Formatting/lint, annotation policy/22 fixtures and documentation checks pass.

The maintainer confirms this eight-file increment, published as `b5d04bb`, with four-ref parity.
Azure's committed-source preview verifies four serial candidate allocations, 15-minute deadlines,
the producer-qualified runtime output, diagnostic-only artifacts and no cache task. Manual run
[72](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=72)
executes that exact source. Its first Windows job passes actual copied-base capability/core-library
ownership and creates a fresh locked environment with pip 26.2/PyYAML 6.0.3. Both isolated children
exit successfully with verified cleanup. The subsequent inventory correctly refuses newly generated
`Lib/__pycache__`; qualification remains failed and all trust/save/handoff flags remain false.

The adopted CPython 3.14.8 `ensurepip` implementation starts a nested interpreter that forwards `-I`
but does not forward `-B`. Isolation also ignores the inherited no-bytecode environment setting.
Consequently, the previous explicit `-I -B -m ensurepip` command did not preserve the stripped base.
The experiment is cancelled after retaining the first failure artifact: first Windows job failed,
second Windows job cancelled, both Linux jobs cancelled. Queue-to-finish is 186.900s (3m06.900s),
not a passing cache performance measurement. Evidence is retained under
`.tmp/ci-phase65/runtime-candidate-72`; no copied runtime bytes were uploaded or admitted.

The scoped correction runs the retained ensurepip bundled wheel directly through public
`importlib.resources` and `runpy` inside the fresh environment's explicitly isolated `-B` interpreter.
It uses offline/no-cache/no-dependency/no-compile installation, then retains the existing hash-locked
pip 26.2/PyYAML 6.0.3 installation and verification. No stdlib/private-function monkeypatch, candidate
mutation allowance, deletion of generated bytecode or weakening of the inventory is introduced.
Ordinary bootstrap remains unchanged. Two regressions demonstrate upstream's lost flag and execute
real bundled-wheel installation offline in a fresh environment. All 55 focused pytest cases pass
on Windows/Linux (3.18s/4.65s); the previous 84 Pester cases per OS remain applicable because their
implementation is unchanged. A real private copy of the existing Windows 3.14.8 installation now
passes the complete candidate qualification: base probe, fresh locked bootstrap (11.757s), fresh-env
probe and repeated payload verification. All three children exit zero with verified cleanup; final
PowerShell fingerprints also confirm both source and copy remain unchanged. Evidence is retained
under `.tmp/ci-phase65/candidate-bytecode-correction/evidence`. Trust/restore/save/handoff flags remain
false. This local copy proves the correction's bytecode boundary, not hosted provider repeatability
or Linux release compatibility. Corrected hosted retry remains open.

The maintainer confirms the five-file correction, dual-published as `1f7b1b3`, with four-ref parity.
The actual committed-source preview passes before the bounded retry below. Ordinary CI/default
acquisition and both paused PRs remain unchanged.

## Corrected Hosted Qualification and Permission Repeatability Gate

Manual [run 73](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=73)
executes exact commit `1f7b1b3a98a9fca94cc009e0f130b8b2b7f9a11d` and succeeds in all four jobs.
Queue-to-finish is 457.665s (7m37.665s). Each copied runtime passes actual base/core-library ownership,
fresh hash-locked pip 26.2/PyYAML 6.0.3 bootstrap, fresh-environment ownership and unchanged payload
verification. All twelve owned children exit zero with verified cleanup. Final PS checks confirm
both candidate and native source are unchanged. All provider/trusted-seal/restore/save/handoff
admission flags remain false. Only diagnostic evidence is uploaded; no runtime binaries or cache.

| Allocation | Native acquisition | Candidate copy/probes/bootstrap/verification task | Locked bootstrap | Retained entries |
| --- | --- | --- | --- | --- |
| Windows 1, preinstalled native | 0.310s | 76.577s | 8.717s | 3,878 |
| Windows 2, downloaded native | 41.770s | 53.647s | 9.005s | 3,878 |
| Linux 1, preinstalled native | 0.253s | 106.303s | 7.249s | 3,040 |
| Linux 2, downloaded native | 9.657s | 53.260s | 8.342s | 3,040 |

These costs describe temporary capture/copy/qualification work, not warm cache restore or ordinary
profile feedback. Fast native selection means an image-provided interpreter, not our owned cache.

Independent Windows schema-3 inventories match completely and match the prior projection:
`9dc6d79241cd40fe80e6b8476055f2d7d4d2184ce5099aca2509238d68ef85ec`.
Linux's retained bytes, paths, sizes, types and links also match between allocations, but **3,029
file/directory permission entries differ**. Linux 1 uses image `20261004.327.1`, whose preinstalled
native tree already has 0777 modes; its candidate correctly preserves them, yielding
`badb07773d9121bdc756970fa538727fce617274f13d8dbd90fdac01362cb391`.
Linux 2 uses image `20260927.320.1` and downloads release `3.14.8-36806082737`; its 0644/0755 modes
yield the prior projection fingerprint
`5e88f33c1f23523d9099daf29854fb12536ec3d0e6e5b3b7e212993503ec8794`.
The candidate root remains 0755 in both. This is observed native-provider variance, not copy corruption.

The independent evidence audit verifies all four execution receipts, package pins, native-source
provenance, complete inventory digests, process cleanup and absence of runtime binaries in artifacts.
It records Windows repeatability as passed and Linux repeatability as blocked, with exit 1. A green
runtime-qualification pipeline does not override this stricter cross-allocation seal gate. Exact
differences, all four receipts, task/image logs and audit are retained under
`.tmp/ci-phase65/runtime-candidate-73` and adjacent log snapshots.

Read-only archive comparison rechecks the pinned Linux asset's SHA-256 and reads tar metadata without
extracting or executing anything. Every one of the downloaded candidate's 3,029 mode-bearing retained
entries matches that verified release archive. All 3,029 preinstalled candidate entries differ only
in mode. `linux-mode-comparison.json` preserves that review evidence, not an adopted permission ledger.

**Next scoped design checkpoint:** review a canonical Linux permission ledger derived from the exact
hash-verified release archive, retaining modes in the eventual trusted seal. Define its provenance,
path/type completeness, executable bits, allowable native-mode variance, rejection rules and versioned
normalization boundary before implementation. Prefer the verified release modes over accepting the
observed 0777 image modes or excluding permissions from integrity. Preserve current native trees and
require private-copy regression plus hosted requalification of any changed normalization. This is a
recommendation for review; `native-core-v1` still preserves native modes and no new seal is adopted.

The maintainer confirms this outcome/disposition checkpoint and the archive-derived permission
direction, published as `d9f7298` with four-ref parity. The concrete policy below is prepared for
review before production implementation. Repeated Linux seals, external provider/seal admission,
fixed-prefix restoration, faults/recovery, warm/cold benefit and ordinary profile handoffs remain
open. Phase 6.5 stays open; no additional hosted run is queued.

## Concrete Linux Release Permission Policy Checkpoint

**Status:** proposed implementation contract, not active normalization or cache admission. The
maintainer agrees to the archive-derived direction; this checkpoint makes its complete acceptance
rules and verification sequence reviewable. Current `native-core-v1` behavior is unchanged.

### Independent Reference Derivation

Read-only derivation rehashes the exact pinned tar asset, reads its metadata and hashes retained
regular members through streams. Nothing is extracted or executed. It derives the retained set
from the archive itself using the existing source-backed-bytecode/native-base-pip omission rules;
it does not use a cache-supplied manifest or a hosted capture to choose which files to trust.
The archive contains one complete pip 26.2.1 distribution; that is omitted without changing the
project's adopted pip 26.2 lock. A cache directory is omitted only if source-backed omissions make
it empty; preexisting empty directories and sourceless bytecode remain required by the policy.

The reviewed native installer removes exactly `setup.sh` and adds exactly these direct aliases:

| Added path | Exact target | Reference source |
| --- | --- | --- |
| `bin/python` | `python3.14` | Pinned installer text |
| `bin/python314` | `python3.14` | Pinned installer text |
| `python` | `./bin/python3.14` | Pinned installer text |

All eight archive-supplied links retain their exact targets. The resulting reference has 2,813
regular files, 216 directories and 11 direct file links: 3,040 entries total. Its 3,029 mode-bearing
entries comprise 318 at 0755 (216 directories and 102 executable files) and 2,711 files at 0644.
The root is 0755. Full ordinal schema-3 framing independently reproduces
`5e88f33c1f23523d9099daf29854fb12536ec3d0e6e5b3b7e212993503ec8794`.

Every retained file hash, byte count, path, type and link target matches both run-73 candidates.
Only the first candidate requires 3,029 permission reductions; the second already matches exactly.
The derivation completes in 1.749s. The ignored review artifact is
`.tmp/ci-phase65/linux-permission-policy-design/reference.json`; its reproducer is
`.tmp/ci-phase65/derive_linux_permission_reference.py`.
It is marked design-only, policy unadopted and cache unadmitted. This extends the prior mode-only
comparison to actual independent archive-byte verification; it is not a restored-runtime test.

### Reference Ownership and Revision

Implement a repository-owned reference outside runtime payloads under the existing CI data boundary.
It contains exact provider `actions/python-versions`, build `3.14.8-36806082737`, asset name/archive
SHA-256, CPython 3.14.8, Ubuntu 24.04/x64/normal-GIL identity, the three reviewed aliases, omission
revision, complete expected schema-3 inventory and expected digest. Record the reference-file digest
in the reviewed acquisition specification; never accept a replacement reference from a cache,
downloaded runtime, child environment or user-supplied receipt.

Generate the committed reference reproducibly from the hash-verified asset, then independently
validate it against captured candidates. Retain a single authoritative reference rather than
duplicating thousands of entries in documentation or workflow YAML. A Python patch, provider build,
asset hash or omission-policy change requires explicit reference review and regeneration; no floating
lookup or automatic digest update is allowed. Keep Windows at `native-core-v1` in this increment.

Linux's new explicit normalization is `native-core-v2-linux-release-modes`; inventory schema 3
continues to include modes. Version the reference/provenance fields of candidate receipts so the
driver cannot treat an unstamped v1 receipt as v2. Existing schema-1 cache-plan scaffolding remains
unadopted and must be adapted separately before actual restore/handoff admission. Separate cache
keys by normalization/reference identity when that backend is implemented; do not reuse v1 keys.

### Admission and Copy Rules

1. Load only the reviewed plain repository reference through bounded parsing. Verify file digest,
   contract/revision, exact adopted identity, complete typed rows, ordinal uniqueness, canonical
   relative paths and the independently framed inventory digest. Reject duplicate JSON keys,
   Boolean-as-integer fields, missing/extra fields, malformed hashes and incomplete references.
2. Compute the existing native projection without writing to it. Require its complete retained
   path/type/size/hash/link set to match the reference. Unknown retained files, altered binaries,
   incomplete stdlib, missing aliases or different link targets fail before candidate execution.
   Directory links, chained/escaping links, hard links and special files remain rejected.
3. For each retained regular file/directory, accept only its exact reference mode or the observed
   native 0777 variant. Normalize the latter to that entry's exact reference mode **in the fresh
   private candidate only**. Missing execute/read bits, other unqualified modes, setuid/setgid/sticky
   bits and arbitrary permission changes fail. Do not infer executable bits from suffixes or blanket
   chmod every file. Source-root mode must be captured and qualified separately: propose a 0755/0777
   allowlist with a 0755 candidate root; current raw captures do not prove the native root's mode.
4. Linux symlink permission bits are not chmod targets; preserve and verify exact link kind/target.
   Apply reviewed directory/file modes through existing safe private-owner paths. Record source
   identity, reference identity and every changed mode in the sidecar receipt. Capture the original
   source-root mode and verify it remains unchanged alongside native file inventory.
5. Verify the candidate against the complete external reference after copying and before each
   executable probe. Preserve the final candidate/source checks, cancellation/deadlines, fresh
   owner/refusal of partial reuse, diagnostic retention and aggregate failure behavior. No post-test
   deletion of generated bytecode or rewriting a mismatched expected digest is permitted.
6. A valid v2 candidate still withholds provider/cache/restore/save/handoff admission until their
   separate gates pass. Probe actual module/core-library ownership and bootstrap locks as in run 73.
   Mode normalization does not qualify fixed-prefix restoration, library relocation or ordinary
   planning/worker/cohort/collector handoffs.

The exact/0777 allowance is limited to this reviewed identity and complete matching retained bytes.
It is not a generic permission sanitizer. Future legitimate mode changes require a new reviewed
reference; failed validation retains ordinary native acquisition as the default.

### Bounded Implementation and Acceptance Sequence

- Implement the reproducible reference derivation/reader and explicit v2 private-copy path. Existing
  Windows/v1/default callers remain unchanged. Update only candidate qualification receipt validation
  and explicit manual pilot wiring needed for the v2 experiment; no cache task or ordinary adapter.
- Extend the existing registered Pester dependency and Python bootstrap groups. Cover correct native
  modes, the observed all-0777 source, mixed qualified modes, wrong reference/version/digest, duplicate
  or incomplete rows, changed bytes/types/paths/links, missing executable bits, privileged/unqualified
  modes, source-root preservation, partial-copy reuse refusal, cancellation and mid-copy failure.
  Prove identical complete output from both qualified native variants and no native source writes.
  Preserve existing group IDs/deadlines, meaningful real file/link/mode fixtures and concise results.
- Reproduce the full real archive reference from the exact bytes; independently compare v2 data-only
  projections of the two captured Linux variants. Run focused native/Python/static checks locally.
  Local source-built WSL Python is not a substitute for the Actions release's executable qualification.
- After scoped publication confirmation, preview exact committed YAML and run one bounded four-job
  Windows/Linux experiment. Require equal Linux mode-aware inventories across qualified source
  variants, successful real probes/fresh locked environments, unchanged sources, verified process
  cleanup and honest failure receipts. Record image/native-selection provenance explicitly.
- If image scheduling does not provide both native variants, retain deterministic captured/synthetic
  variant proof and report the hosted boundary honestly; do not remove image runtimes to create a
  cache miss. Separate current hosted execution evidence from historical variant coverage.
- Only after this gate passes, review source-controlled trusted seals and fixed-prefix restoration,
  then cold/warm, corruption/failure/recovery and measured benefit. Ordinary CI remains native until
  broader same-source profile/handoff qualification and adoption review are complete.

Rollback keeps `native-core-v1` and original native acquisition available, retains failed v2 evidence
and declines cache admission. The maintainer confirms this concrete policy checkpoint, dual-published
as `68470c2` with four-ref parity. The first implementation increment below establishes its reference
foundation; production v2 copying and hosted normalization qualification remain separate next steps.

## Release Reference Foundation Implemented for Review

The first focused implementation adds a reproducible, explicitly invoked Python deriver, the
repository-owned Linux release specification/reference, and strict PS7 reference admission helpers.
No ordinary caller, capture pipeline, candidate-copy behavior or cache backend selects v2 yet.
The existing `native-core-v1` builder/driver remains unchanged. The complete reference file is generated
from verified archive bytes rather than hand-authored hashes; its expected inventory digest is the
already independently proved `5e88f33c1f23523d9099daf29854fb12536ec3d0e6e5b3b7e212993503ec8794`.

Authoritative files:

- [Release specification](CI/Data/python-linux-release-reference-spec.json) binds provider/build,
  CPython/GIL/OS/image/architecture, exact archive identity, normalization revision, reference filename,
  reference-file SHA-256 and expected mode-aware inventory SHA-256.
- [Full release reference](CI/Data/python-linux-3.14.8-reference.json) contains the single complete
  3,040-entry external inventory. Its 703,313 UTF-8 bytes hash to
  `95e112863137211040344814033dca6a6c0156bc51546022643108f78ee165c6`.
- [Derivation command](CI/derive_python_release_reference.py) rehashes the pinned archive before and
  after bounded metadata/member processing, applies the reviewed omissions/aliases, verifies expected
  inventory and exact output bytes, and creates only a fresh repository-owned output. It does not
  download, extract, run installers, overwrite an output or automatically update expected digests.
- [PS7 helpers](CI/PythonRuntimeCache.ps1) bind ordinary reference loading to the repository CI data
  boundary. The explicit path reader exists for deterministic private fixtures; no cache payload or
  environment supplies a specification to the production-bound loader.

The reader rejects linked/nonregular/hard-linked/oversized input, invalid UTF-8, duplicate JSON keys,
unexpected fields/revisions/provider identity, malformed checksums, missing/extra/Boolean numeric
metadata, noncanonical or unordered paths, incomplete parents, unqualified modes and indirect/unsafe
links. It recomputes the complete ordinal inventory digest rather than trusting a declared count.
Parsing and row validation observe deadline/cancellation. Real input-owner ancestry is checked once;
metadata rows use lexical validation and complete parent/link checks, avoiding thousands of redundant
filesystem stats on the Windows-mounted WSL checkout.

The scoped `.gitattributes` rule fixes generated Linux reference JSON to LF so a Windows checkout
cannot silently change its byte checksum. Native image permissions, project interpreter selection,
dependency locks, supported runtimes, catalogs and existing group deadlines are unchanged.

Verification passes 69 bootstrap/deriver pytest cases per OS (Windows 3.46s; Linux 4.20s) and all
105 registered dependency/reference Pester cases per OS (Windows 11.082s; Linux 20.528s), with zero
errors/skips. The new cases cover reproducible archive derivation, unsafe members/links/permissions,
hash mismatches, retained sourceless/preexisting-empty cache inputs, output ownership/no overwrite,
typed complete reference admission, duplicate keys, malformed declarations, linked owners, bounded
input, expired leases and mid-parse cancellation. Group IDs/membership and 120-second deadlines
remain unchanged; cases extend the two already-registered test entry files.

Initial WSL Pester verification passes in 71.420s; removing redundant per-row filesystem ownership
checks reduces the same complete group to 20.528s while preserving admission checks. This is local
fixture/reference cost, not a hosted warm-cache baseline. Windows and Linux both regenerate exact
reference bytes from the pinned real archive. Evidence is retained under
`.tmp/ci-phase65/linux-permission-policy-design` and `reference-reader-optimized-pester-*`.
Ruff/formatting, work-annotation policy/22 fixtures, generated-data/line-ending checks, documentation
links and diff checks pass.

The maintainer confirms this ten-file foundation, dual-published as `1e9dd30` with four-ref parity.
No additional hosted experiment is needed to accept its standalone reference proof. The explicit v2
copy/driver implementation below is the next separate increment. Phase 6.5 stays open;
cache-plan/seal/restoration/fault/recovery/benefit and ordinary handoff/adoption gates remain open.

## Explicit Linux V2 Copy and Driver Binding Implemented for Review

The private builder now exposes an explicit `-LinuxReleaseModes` option. Without it, v1 behavior
and schema-1 receipts remain unchanged. Windows refuses the Linux option before creating a candidate.
On Linux, the option loads only the repository-bound reference, captures the original native root
mode before inventory, derives the existing v1 retained projection and requires its complete
path/type/size/hash/link set to match the external reference. Qualified source modes are only exact
reference modes or 0777; root modes are only 0755/0777. Missing executable bits, privileged modes,
different binaries, extra/missing rows or changed link targets fail before copy acceptance.

The normalizer changes metadata in a fresh projection without altering its input. Existing private
copy/link creation then applies exact reference file/directory modes and a 0755 root. Its complete
schema-3 fingerprint must match the independently derived reference. Original native inventory and
root mode must remain unchanged. Success receipts use schema 2 and
`native-core-v2-linux-release-modes`, with external reference identity/file/inventory checksums,
original source-root mode and an ordinal list of exact mode reductions. Incomplete receipts retain
that provenance with bounded JSON depth, never promote the partial owner and never allow its reuse.

The Python qualifier independently reloads the repository-owned specification/reference through
plain bounded input with duplicate-key rejection. Before executing any child, it binds v2 receipt
identity and the entire typed inventory to that external reference, validates the source-root mode
and exact ordinal change records, then performs the existing physical byte/path/link/mode checks.
Canonical serialized comparison distinguishes integers from floating/Boolean lookalikes. A matching
manifest supplied by the runtime alone cannot substitute for the source-controlled reference.
V2 execution remains Linux-only; a namespace/revision mismatch or failed binding yields retained
failure evidence with zero child launches. The existing owned-process/deadline/cancellation logic
and real base/fresh-environment probes are retained. Reports identify normalization, reference binding,
source-root mode and reduction count; cache/provider/restore/save/handoff admission remains withheld.

The temporary capture entry point selects v2 only for its explicit Linux `candidate` mode and checks
native root permissions again after executable qualification. Raw mode, Windows candidate v1,
production adapters, profile membership, four allocations, job limits, artifact-only evidence and
all ordinary acquisition defaults remain unchanged. No Cache task or hosted run is added by this diff.

Focused verification passes all 87 bootstrap/reference/qualification pytest cases per OS (Windows
4.58s; Linux 6.39s) and all 124 registered dependency/reference/copy Pester cases per OS (Windows
13.023s; Linux 22.535s), with zero errors/skips. New portable metadata tests cover exact, all-0777
and mixed sources, unchanged inputs, altered bytes/types/links/modes/version/digest, root restrictions,
lease refusal and exact receiver binding. Actual private Linux file copies prove reduction, source/root
preservation, partial-owner refusal, source-root mutation detection and mid-copy cancellation with
schema-2 provenance. The corresponding Windows cases verify explicit host refusal; they do not claim
positive Linux copying on Windows. No new registered group or deadline is introduced.

Read-only projection of both real run-73 Linux captures produces the same complete 3,040-entry
fingerprint `5e88f33c1f23523d9099daf29854fb12536ec3d0e6e5b3b7e212993503ec8794`: first capture reduces
3,029 modes; second reduces zero. Projection costs are 8.073s/7.485s, including the existing omission
step. Evidence is `.tmp/ci-phase65/release-mode-projections.json`. Because old raw captures did not
record native root mode, this data-only proof explicitly supplies synthetic 0755 and claims neither
real root-mode qualification nor executable release qualification. New hosted receipts must supply
and preserve the actual root; the local source-built WSL interpreter remains outside release proof.

Ruff/formatting, annotation policy/22 fixtures, documentation links and diff checks pass. The maintainer
confirms this eight-file increment, dual-published as `f5705d3` with four-ref parity. Exact-source preview
verifies the four serial bounded candidate jobs, named native output, evidence-only artifacts and no
cache task. The completed hosted experiment below qualifies real execution/root preservation while
distinguishing observed image coverage from historical captured/synthetic variance proof.

## Hosted V2 Qualification and Bounded Repeatability Result

Manual [run 74](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=74)
executes exact source `f5705d34e7de8dafb7be4fd38a536b5f758bd93f`. All four jobs succeed; queue-to-finish
is 458.869s (7m38.869s). All agents report image `20260927.320.1` and download the exact pinned
Windows/Linux assets from release `3.14.8-36806082737`. This provides real cold native acquisition,
not an owned cache hit or a claim about registry reliability under every condition.

| Allocation | Native acquisition | Capture/copy/qualification task | Locked bootstrap | Native root / candidate root | Retained-entry reductions |
| --- | --- | --- | --- | --- | --- |
| Windows 1 | 43.040s | 52.560s | 8.642s | Windows v1 | 0 |
| Windows 2 | 39.123s | 49.497s | 8.307s | Windows v1 | 0 |
| Linux 1 | 8.923s | 56.223s | 8.540s | 0777 / 0755 | 0 |
| Linux 2 | 10.313s | 53.717s | 7.317s | 0777 / 0755 | 0 |

Both Windows receipts remain schema 1/v1; both complete 3,878-entry inventories match the existing
`9dc6d79241cd40fe80e6b8476055f2d7d4d2184ce5099aca2509238d68ef85ec` fingerprint. Both Linux receipts
use schema 2/v2 and bind the exact repository reference. Their complete 3,040-entry inventories,
including all file/directory modes and the 0755 root, match the external reference and each other at
`5e88f33c1f23523d9099daf29854fb12536ec3d0e6e5b3b7e212993503ec8794`.

Linux's downloaded source files/directories already have reference modes, so their per-entry reduction
lists are empty. The root is separately normalized from observed native 0777 to candidate 0755.
The builder records actual native root mode, and final PS source checks confirm that original mode
and raw source inventory remain unchanged after executable qualification. A zero entry-reduction count
does not mean the root stayed at 0777. No native host installation is modified by normalization.

All four copied bases and fresh hash-locked pip 26.2/PyYAML 6.0.3 environments pass actual executable,
module/core-library and prefix ownership. All twelve owned children exit zero with verified cleanup.
Repeated physical candidate checks remain unchanged after bootstrap. Linux reports external reference
binding verified; both hosts still withhold provider/cache/trusted-seal/restore/save/handoff admission.
No runtime binary is uploaded, cache saved/restored, ordinary adapter changed or PR reopened.

The independent artifact audit recomputes each complete inventory digest, compares full paired rows,
checks native-source identity, v2 reference stamps and exact reduction lists against raw modes, verifies
real source-root receipts, locked package versions, child cleanup and loaded-library ownership, and
refuses runtime binaries in the diagnostic bundle. It exits zero. All final task logs corroborate
candidate/native-source checks. Evidence is `.tmp/ci-phase65/runtime-candidate-74/audit.json`, its four
artifact folders and adjacent timeline/task/image snapshots.

**Coverage boundary:** fresh hosted execution exercises only the downloaded retained-mode variant.
The newer image's all-0777 retained files were not scheduled in this run. That variant is covered by
the complete run-73 captured-byte/reference projection and real private synthetic mode-copy tests;
those are not relabelled as fresh hosted execution. The approved bounded sequence permits this
distinction rather than repeatedly spending agent minutes or deleting image runtimes to force a
variant. A future naturally scheduled source with the qualified 0777 modes remains fail-closed against
the same complete external reference and must pass real probes before use.

This establishes bounded executable/root-preserving v2 normalization and paired repeatability. The
7m38.869s includes native acquisition, raw capture, private copying and repeated qualification; it is
not a warm-cache performance measurement or an ordinary-profile target result. There is no evidence
yet that restoring/saving this cache is faster than the native path on either OS.

The maintainer confirms the result/disposition checkpoint, dual-published as `8652baa` with four-ref
parity. Next adapt the unadopted cache-plan/admission scaffolding to explicit mode-aware normalization/
reference identities and reviewed external Windows/Linux seals, then qualify owned staging/fixed-prefix
restoration before any cache execution. Retain native acquisition as default/rollback. Cold/warm
restore/save costs, deliberate corruption/failure/recovery, absent-interpreter behavior and original
profile/worker/cohort/collector handoffs remain required before adoption. Phase 6.5 stays open.

## Mode-Aware Seals and Read-Only Cache Admission Implemented for Review

The next focused increment prepares the Windows external reference alongside the existing Linux
reference, a common strict platform reader preserving the Linux API, and separate schema-2 sealed
cache plan/decision helpers. No existing pipeline or caller selects these cache helpers yet. There
is no cache restore/save, destination creation, executable launch, registry change or tool-cache write.

The [Windows specification](CI/Data/python-windows-native-reference-spec.json) binds the exact provider
archive, declared build and complete normalized inventory. The [Windows reference](CI/Data/python-windows-3.14.8-reference.json)
contains the independently audited run-74 pair's 3,878 rows at inventory fingerprint
`9dc6d79241cd40fe80e6b8476055f2d7d4d2184ce5099aca2509238d68ef85ec`. Its 742,725 UTF-8/LF bytes hash to
`952d15ad6b7cf9062000f5e855ebee2489812314cd01daac041f74de2ef10a98`.
The [explicit freeze command](CI/derive_windows_native_reference.py) rehashes the pinned 33,100,332-byte
archive, requires distinct same-source capture IDs 1/2 with completed immutable candidate/probe/cleanup
declarations, recomputes both reviewed inventory digests and refuses output that differs from the
declared reference-file checksum. It never extracts/runs the installer or automatically updates hashes.

This Windows reference is derived from qualified native outputs, unlike Linux's direct archive-member
derivation. The independent service-log/artifact audit of run 74 establishes the real acquisition and
allocation provenance; parsing copied receipt declarations alone is not proof of two remote agents.
Both run-74 Windows agents download the exact `3.14.8-36806082737` asset. Earlier cold/preinstalled
samples also match the same complete normalized fingerprint. Keep that provenance distinction explicit;
do not claim that reading the installer archive independently reconstructs Windows installed bytes.
Linux continues using its existing archive-derived 3,040-entry reference without changes.

The shared reader retains complete typed/ordinal/path/parent/link/file-hash validation and bounded
duplicate-key-aware parsing. Linux requires its exact Unix modes and 0755 root. Windows requires a
null Unix root and no invented Unix-mode fields. Both loader paths bind repository-owned specification
and reference bytes; cached manifests cannot supply either. A scoped LF attribute keeps Windows
reference bytes stable on checkout, just as for Linux. Both OSs reproduce exact Windows reference bytes.

`Get-CiPythonSealedCachePlan` reads the external reference itself; its caller cannot supply a replacement
seal. It is restricted to captured manual ADO hosted/x64 context. The deterministic `lotm-python-runtime-v2`
key binds OS/image/architecture, exact CPython/GIL/version, provider build/archive, normalization,
reference-file checksum, inventory schema 3/fingerprint and declared native fixed prefix/executable.
Source commit is recorded separately so ordinary source changes do not invalidate identical runtime
bytes. The metadata plan still declares restoration, execution and handoff unqualified.

`Get-CiPythonSealedCacheDecision` independently reconstructs the expected plan from current repository
declarations, rejects schema/key/identity or premature-promotion changes and requires the matching host
for physical staging checks. Only exact `true`/`false` cache results are accepted. A clean miss returns
`native-required` without creating any owner. An exact hit recomputes the full physical schema-3
inventory, verifies the regular interpreter and returns only `staging-verified`, with execution,
restoration and handoff still false. Changed bytes/modes, missing/extra files, a self-trust manifest,
linked/unsafe owners, dirty misses and inexact hits fail rather than silently falling back or executing.
Hash-valid staging is not authority to overwrite a native installation or register a tool-cache slot.

The original schema-1 scaffold remains isolated and unadopted; its decision helper explicitly rejects
schema-2 plans. Retire that temporary scaffold and redundant tests only after the new receipt/probe/
restoration lifecycle proves equivalent or stronger coverage. Windows's retained `native-core-v1`
normalization is a different revision boundary and is not Windows PowerShell 5.1 support.

Verification passes 94 bootstrap/reference pytest cases per OS (Windows 5.24s; Linux 6.23s) and 140
registered dependency/reference/admission Pester cases per OS (Windows 13.951s; Linux 25.874s), with
zero errors/skips. The new cases cover paired reference refusal, archive/source/schema/immutable-payload
identity, exact staged hits/misses, key stability/reference changes, corrupt/extra/missing/mode-altered
payloads, plan tampering, premature promotion, inexact results and cancellation/deadline refusal.
Existing registrations, 120-second group deadlines, native ownership and concise result behavior remain.
Both metadata-test hosts produce identical Windows/Linux plan keys. Real Windows reference output is
byte-identical across Windows/Linux. Ruff/formatting, annotation policy/22 fixtures, generated reference
checksum/line-ending checks, documentation links and diff checks pass.

The maintainer confirms this ten-file source/data/test/evidence increment, published as `c9be93a`
with four-ref parity. No hosted experiment is
needed to accept read-only plan/admission behavior. Next implement the separate owned-restoration lease:
validate actual hosted tools root against the declared prefix, require an absent exact destination,
create only a fresh owned target, preserve existing installations/other patches, copy and reverify sealed
bytes/modes before any probe, and retain honest failure/cancellation/partial-owner evidence. An occupied
host prefix must never be treated as permission to overwrite it; qualify its explicit native route or
blocked disposition separately. Missing-interpreter behavior must be demonstrated on a naturally
appropriate agent, not manufactured by removing image runtimes. Keep the destination and cache YAML
disabled until local lease/receipt regressions and bounded hosted acceptance pass. Restore/save costs,
fault/recovery, broader handoffs and adoption remain open. Phase 6.5 stays open; PRs remain paused.

## Fresh Ownership and Nonexecuting Private Copy Implemented for Review

The next focused increment adds a shared fresh-owner check, a read-only fixed-prefix destination
check and a nonexecuting private copy helper. No pipeline invokes these helpers yet. The complete
external seal is revalidated before either destination admission or copying; a caller's earlier
decision object cannot promote itself into write authority.

`Resolve-CiPythonFreshCopyOwner` requires an existing plain workspace, a contained target below that
owner, disjoint staging and an absent target/external `.copy.json` receipt. Existing files, directories,
receipts, linked ancestors and dangling destination links are refused and preserved. The receipt stays
outside the payload so it cannot change the sealed runtime or serve as its source of trust.

`Get-CiPythonRestorationDestination` compares the supplied actual tools-root-derived exact Python/x64
path with the repository plan's declared native prefix, then checks fresh ownership. It is read-only:
even a successful result retains restoration/execution/handoff false. The future hosted driver must
capture the actual agent tools root and manual hosted context; passing a synthetic root to this helper
alone is not proof of a real hosted allocation. An occupied host prefix is blocked here, preserving
native selection as the separate default route. No host installation or other patch is removed.

`New-CiPythonSealedPrivateCopy` explicitly refuses the declared native runtime owner or overlapping
paths. It claims an external receipt with `CreateNew`, records incomplete state before payload writes,
copies files without overwrite and recreates safe relative file links. Linux applies exact sealed
file/directory/root modes. Final complete schema-3 inventories must match both copied bytes and the
unchanged staging source. Only `private-copy-verified` can result; execution, restoration, handoff and
save remain false. Cancellation, expiration, I/O failure or changed bytes retain incomplete evidence
and any partial target; neither is silently cleaned up or reused. This uses copying rather than a
cross-volume move, anticipating Windows staging and native-prefix volumes that may differ.

Verification uses synthetic private fixtures only, including preserved empty directories and Linux
relative links. It covers complete immutable copying, occupied files/directories/receipts, containment/
overlap, dangling owners, tools-root mismatch, refusal to write the declared native owner, corrupted
staging, source mutation during copying and retained cancellation/timeout/I/O failure evidence. The
first run found a test-fixture name collision; each parameterized owner now has a distinct path.
Final registered group verification passes 152/152 Pester cases on Windows in 14.699s and on Linux
in 25.370s, with zero errors/skips and the existing 120-second group deadline. This adds twelve cases
to the prior 140-case group. Timeout and I/O failures are deliberately injected; successful copying
and cancellation/source-mutation paths use real private filesystem fixtures. Scoped formatting and
annotation policy pass (two files, zero findings, all 22 policy fixtures); 66 relative documentation
links resolve, trailing-whitespace and diff checks pass. Python source is unchanged, so the previously
passing 94-case reference/bootstrap evidence is retained rather than rerun.

This five-file increment remains uncommitted for review. Actual fixed-prefix writes, tool-cache
registration/complete markers, interpreter probes and fresh locked-environment handoff still require
the hosted driver/receipt qualification. The private writer requires the receipt's parent to exist;
creating/owning missing native version-parent directories is a separate driver responsibility, not
implicitly authorized by the read-only destination result. No cache YAML, real host runtime mutation, hosted run or PR
reopening occurs here. Next bind the owned restoration lifecycle to that guarded manual driver, then
qualify bounded cache hit/miss/fault/recovery and measure restore/save costs before adoption. Phase 6.5
stays open and native acquisition remains default/rollback.
