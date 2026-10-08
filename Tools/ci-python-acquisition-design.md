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
