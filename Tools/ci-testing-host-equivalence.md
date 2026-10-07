# Hosted Equivalence And Cost Qualification

## Status And Scope

Phase 6.5 starts from confirmed Phase 6.4 closeout `2f150d6`. The
[modernization plan](ci-testing-modernization-plan.md#phase-65-host-equivalence-and-policy-adoption-review)
owns acceptance. GitHub PR 3 and Azure PR 19 remain paused; no required check, policy, event,
suite membership, conformance fixture or canonical content is changed by this first increment.
The Python patch checkpoint is confirmed and dual-published as `b07f942`. Cold/warm dependency and
build execution passes on both hosts/OSs, but an independently observed pilot checkout-byte gap
keeps final package-input equivalence open. Its correction and the first collection-role optimization
are prepared locally and uncommitted. Wider optimization/equivalence/policy-adoption gates remain open.

## Python Patch Candidate

The reviewed candidate is **CPython 3.14.8**, the current stable 3.14 maintenance/security release
reported by the [official release page](https://www.python.org/downloads/release/python-3148/)
(release date September 30, 2026). Its notes include SSL, archive extraction, decompression,
credential-scheme handling and bundled-library corrections. This is a patch checkpoint within
the already accepted Python 3.14+ eligibility, not a 3.15 migration or a free-threaded lane.

The official Windows install manager verifies its release index signature and extracts the exact
candidate with `py install --target=.local/ci-tools/python-3.14.8 3.14.8`. This creates no global
registration or shortcuts and preserves the existing 3.14.5 installation. The isolated Linux
candidate uses the existing standalone-runtime approach, now release `20261003`:

- Archive: `cpython-3.14.8+20261003-x86_64-unknown-linux-gnu-install_only.tar.gz`.
- Publisher: [Astral Python standalone release](https://github.com/astral-sh/python-build-standalone/releases/tag/20261003).
- Verified SHA256: `371b6c281bbb09b29279e9e3a2996bab4ae2ea03cca52bf869f8bd89286b0ae8`.
- New owner: `/home/matt/lotm-ci-workspaces/phase-6.5/python-3.14.8`; no existing owner is replaced.

The live Actions Python registry contains stable, ordinary x64 3.14.8 payloads for Windows and
Ubuntu 24.04. Registry presence is acquisition eligibility, not hosted execution proof.
The candidate diff updates both runtime/lock interpreter labels and every GitHub/Azure workflow
pin together. Existing package versions, wheel URLs/digests, `Requires-Python >=3.14`, py310 source
syntax policy, package 0.1.0 and PowerShell/Pester versions remain unchanged. Runtime identity
changes invalidate version-specific Python environments and hosted payload keys automatically;
PowerShell dependency receipts retain their unchanged graph identity.

The native adapter's old hard-coded `(3, 14, 5)` probe is replaced by the authoritative
`Data/runtime-versions.json` pin. Two real integration cases prove accepted-version execution and
nonzero prerequisite rejection of a mismatched interpreter, with no invented test counts.
These belong to the existing registered native-results group; no new suite or pressure family is added.

## Local Evidence

| Check | Windows | Linux |
| --- | --- | --- |
| Fresh development/media environment with locked dependencies | Passed, 23.997s | Passed, 134.491s |
| Complete existing Python implementation suite before adapter correction | 574 passed, 91.22s | 574 passed, 82.52s |
| Native adapter group after correction, including two new integration cases | 35 passed, 4.45s | 35 passed, 6.40s |
| Verified wheel build with unchanged build pins | Passed, 18.970s | Passed, 127.192s |
| Outside-checkout installed consumer, 28 wheel members / 10 checks | Passed, 7.393s | Passed, 25.486s |
| Existing Pester portfolio through candidate controller | 60 passed, 28.171s | 58 portable cases passed, 30.268s |
| Existing language-neutral baseline fixtures through Python | 21 suites passed, 64.733s | 21 suites passed, 87.417s |

Linux explicitly excludes the Windows-only two-case image group; it is covered in the Windows run.
These are qualification samples, not new whole-profile timing baselines. Linux environments/builds
were prepared on the Windows-mounted checkout; their setup timings cannot establish native Linux
hosted performance. Existing 3.14.5 environments and all dated evidence remain available.
Linux Pester's initial missing `/usr/bin/pwsh` and omitted owned-module-root launches failed honestly
before cases were credited; correction uses the existing WSL PowerShell/module receipts and
process-local paths, without another runtime/module installation. Original diagnostics remain retained.

Ruff and GitHub actionlint pass. Evidence, exact candidate registry metadata, native XML, environment
receipts and installed-consumer records are retained under ignored `.tmp/ci-phase65`.
All 21 baseline suites pass per OS. Final static/diff review passes before publication; these
results do not substitute for cross-runtime parity or full project/host equivalence gates.

## Existing ADO Cost Decomposition

Run 54 is a functional, shared-slot full PR sample on the old baseline, not an uncontended or accepted
steady-state cost. Its eleven jobs sum to **3097.523s (51m38s)**. Independently summing native task
intervals gives:

| Task category | Occurrences | Summed seconds |
| --- | ---: | ---: |
| Exact Python acquisition | 11 | 564.930 |
| Worker environment preparation | 10 | 579.680 |
| Repository execution and aggregate collection | 10 | 1478.647 |
| Payload cache restoration | 10 | 129.330 |
| Payload post-job cache work | 10 | 15.130 |
| Checkout | 11 | 87.810 |

These categories do not exhaust job time; planning, wrappers, publication, initialization and
finalization remain separately accountable. Queue/allocation gaps and overlapping experiments must
not be mislabeled as execution or removed from wall-time reporting. The single hosted slot makes
summed repeated preparation consequential, even when GitHub runs independent jobs concurrently.
The audit source is retained `.tmp/ci-phase64/ado54-final-timeline.json`; its derived cost record is
`.tmp/ci-phase65/ado54-cost-audit.json`.

Every existing worker, including infrastructure and aggregate collection, currently requests the
complete build/render payload and actionlint. That confirmed duplication motivates the next
increment: derive preparation from the approved plan and assigned role, while preserving
preflight, necessary package/runtime payloads, source protection and complete admission. Test
isolation and full profile membership remain mandatory. ADO consolidation and narrower barriers
must preserve every approved unit exactly once and independent continuation after failure;
job reduction alone is not evidence of stronger or equivalent coverage.

## Hosted Patch Qualification At b07f942

Confirmation publishes all nineteen reviewed files as `b07f9428b43a11b2e71f645f31384e89475b3cc1`.
Local HEAD, upstream and both fetched remote branch tips agree, with a clean tree before the next
increment. Both PRs remain paused. Annotation run 37657000281 and the automatic core cache pilot
37657000390 pass. No automatic full PR run is triggered.

Complete cold and warm pilots pass on Windows and Linux:

- GitHub [cold 37657056851](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37657056851)
  and [warm 37657516265](https://github.com/Phishinabowl/LoTM-Re-Read-Analysis/actions/runs/37657516265).
- Azure [cold 57](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=57)
  and [warm 58](https://dev.azure.com/DreamtechADO/66e8d68e-9ebd-41d1-adc5-9e6fde7a57bb/_build/results?buildId=58).

Independent receipt audit verifies all eight jobs' exact published source, 3.14.8 interpreters,
unchanged dependencies, 7.6.6 PowerShell, package 0.1.0 builds, pinned browser and real SVG labels,
and requested cache miss/hit disposition. Each OS's warm key equals its cold key. The 23 Python
runtime source-input hashes match across all eight jobs. Pilot artifacts retain build receipts/logs,
not downloadable wheel bytes; this audit does not claim independent rehashing of hosted wheel archives.

| Host / OS | Cold setup | Warm setup | Cold job | Warm job | Cold / warm Python acquisition |
| --- | ---: | ---: | ---: | ---: | ---: |
| GitHub / Windows | 82.045s | 55.035s | 162s | 84s | 59s / 0s |
| GitHub / Linux | 67.385s | 33.960s | 100s | 51s | 1s / 0s |
| Azure / Windows | 77.986s | 59.793s | 168.723s | 107.057s | 43.210s / 0.317s |
| Azure / Linux | 54.630s | 39.195s | 91.257s | 88.403s | 10.123s / 10.783s |

Helper setup excludes native cache transport and Python acquisition. Job intervals exclude waiting
for another allocation. These are single samples on distinct hosted allocations, not percentiles;
variation in agent interpreter availability cannot be attributed to the dependency payload cache.

The audit also detects **different Windows/Linux `pyproject.toml` and `LICENSE` input hashes**:
pilot checkouts inherit Windows CRLF conversion. Successful local wheel checks validate each
checkout's own bytes, so green jobs alone do not prove cross-host build-input equivalence.
The prepared correction applies the existing shadow-worker `core.autocrlf=false` process setting
before checkout in both pilots. Existing synthetic real-Git regression covers that setting; corrected
hosted pilot input comparison remains required. Original pilot outcomes remain honest dependency/
build-execution proof, not final package-input equivalence or whole-profile acceptance.

Evidence is retained under `.tmp/ci-phase65`: original cold/warm artifacts, native task timelines,
`patch-pilot-audit.json` and `patch-timing-audit.json`. Python 3.14.5 rollback remains available.

## Prepared Collection-Role Optimization

The aggregate worker now requests a distinct `collection` payload containing only runtime Python
dependencies (`pip` and PyYAML). It neither acquires PowerShell/actionlint/Node nor builds the wheel
or prepares/qualifies rendering. Cache identity distinguishes this role from `complete` and `core`.
Execution workers keep complete preparation unchanged in this increment.

Both host workers explicitly propagate their assigned shard during preparation. A missing shard
denotes collection, not a smaller test selection. Before execution/collection, the transport requires
a successful receipt with the expected role and exact execution commit; execution additionally
requires the original successful build and PowerShell receipts. Collection still admits every
approved shard exactly once with existing provenance, manifest, XML, cleanup and failure checks.
No catalog IDs, suite membership, unit deadlines, check names or policy conditions change.

Final focused bootstrap/scope regression contains **128 cases per OS**, covering role-separated keys,
forbidden collection tool acquisition, assigned-shard propagation and wrong-role/foreign-source
receipt rejection. Fresh production collection bootstraps pass in private owners on both OSs:
Windows 12.457s, Linux 85.850s on the Windows-mounted checkout. Both install only pip/PyYAML and
produce no build/render/Node or PowerShell receipt. These setup samples are not hosted performance proof.

The final real Windows infrastructure shard passes all five checks and **460 native cases** in
96.837s. The runtime-only collector admits its complete bundle in **4.562s**, preserving those same
460 cases and verified source protection/cleanup. An initial accidental use of the bare candidate
controller fails on missing YAML without crediting coverage; the verified runtime controller succeeds.
A Linux attempt to admit that local Windows worktree bundle correctly rejects its different snapshot
digest: mounted Unix worktree mode capture differs from Windows index mode capture. That experiment
does not establish cross-OS local-worktree interchangeability or justify relaxing provenance.
Current hosted aggregate placement remains Windows; Linux reduced preparation and focused tests
are qualified, while full Linux collection would require its own coherent source/manifest proof.

These eight implementation/test/workflow files plus the two evidence/plan updates are uncommitted
pending confirmation. Publication must then prove corrected pilot build-input hashes and the
reduced aggregate's ordinary success/failure publication on both hosts. Further execution-role
preparation, ADO consolidation, barriers and runtime acquisition remain explicit later increments.

## Remaining Qualification And Rollback

Publish the reviewed patch checkpoint only after maintainer confirmation, then qualify exact
interpreter acquisition and dependency/package behavior on both hosted platforms and both OSs.
Use deliberate manual runs while PRs remain paused; the path-specific GitHub cache pilot will also
trigger when its version-pin file is published. Do not mistake a branch pilot for fresh PR merge proof.
Adoption is conditional on those results; setup failure cannot silently select another version.

Review the two `UsePythonVersion@0` warnings during the acquisition increment. Its documented
`githubToken` input concerns registry download limits, while exact-pin acquisition must survive
host-image patch replacement. No personal credential is added to YAML, no existing authentication
is repurposed, and no host-managed secret is created by this checkpoint. A repository-owned
hash-pinned acquisition alternative must be reviewed and measured before replacing native setup.

After patch disposition, qualify role-specific preparation, ADO job consolidation and dependency
barriers separately. Measure cold/warm setup, actual workload, publication and queue time; compare
complete local/hosted portfolio identity and failure/cancellation behavior. Restore the same PRs
before fresh PR/event equivalence and policy adoption. Original checks remain until their accepted
replacement gate. The accepted 90-second native and 16-minute sequential goals are not relaxed.

Rollback is the retained 3.14.5 runtime/pin/lock/workflow baseline at `2f150d6`, plus its original
environment and hosted evidence. Restore the complete candidate pin increment together if hosted
qualification fails; retain failed candidate diagnostics and record its disposition. Do not downgrade
or remove machine runtimes, overwrite existing environment owners, or mix interpreter labels with
different authoritative pins.
