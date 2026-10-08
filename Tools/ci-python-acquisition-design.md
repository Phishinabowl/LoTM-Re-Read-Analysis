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
