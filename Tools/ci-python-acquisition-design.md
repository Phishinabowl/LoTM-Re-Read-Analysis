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

The correction and evidence updates remain uncommitted pending review. Repeated normalized payloads,
positive Linux release execution, external seals, fixed-prefix restoration, faults/recovery and
measured cache benefit remain open. Phase 6.5 stays open; both PRs and ordinary CI/default acquisition
remain unchanged.
