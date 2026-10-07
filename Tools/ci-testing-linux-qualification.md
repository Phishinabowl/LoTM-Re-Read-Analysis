# CI 5.8.2 Focused Linux Qualification

**Status:** Implemented, focused qualification verified and confirmed by the maintainer on 2026-10-06.
The [approved inventory](ci-testing-linux-portability-inventory.md),
[D24](ci-testing-contracts.md) and [modernization plan](ci-testing-modernization-plan.md) own scope.
No hosted workflow, required check name, canonical content, golden fixture or framework schema is changed.

## Implementation And Required Coverage

QA's PowerShell relative-path helper now uses native filesystem-relative paths and serializes forward
slashes. Output/root-relative containment uses Windows case folding only on Windows, and output
ancestors reject links before writes/cleanup. A pure old-function Linux probe confirmed that its
previous guard accepted a linked outside path without writing it. Generated filenames use the
existing Windows/Python sanitation set on every host: the real Linux consumer mismatch for
`Volume 1: Clown` is corrected to `Volume 1- Clown`, preserving existing goldens and authored titles.
Visualization's
broken-link exclusions recognize both native separators; diagnostic paths retain the existing `.\`
prefix and native relative separators, matching the Python implementation. Focused Pester regressions
cover Unicode/spaces/literal percent/hash names, root/sibling/case/link boundaries, portable filenames
and Source exclusions.
Existing root/containment conformance retains drive/UNC/symlink rejection obligations.

Only CI coverage metadata advances to schema 2. All 32 external descriptors declare Windows/Linux
eligibility explicitly; the loader no longer invents it from owner/language. Closed-field, version,
missing/empty/duplicate/unknown/type-invalid OS tests preserve Windows coverage and truthful Linux
blockage. Shard admission remains strict, including rejection of Linux placement for Windows media.
Existing conformance/compatibility registry membership, versions, ordering and result contracts remain.

D12 now has three registered synthetic media groups: four Python cases, two PS EPUB cases, and two
Windows PS crop cases. Every implementation-bearing feature/PR/full/release/shadow profile retains
them; the narrowly scoped infrastructure regression profile stays unchanged. No real media is read.
Each new group has a 30-second deadline. New dedicated media shards reserve 300 seconds, including
90 seconds of execution and unchanged 210 seconds of termination/cleanup/finalization reserves.
Existing native groups, deadlines, shard ceilings and check names are preserved. The six affected
profile safety envelopes add exactly 90 seconds for the new required work; feedback goals and
accepted timing exceptions are not relaxed. Hosted placement is still unimplemented.

The complete Windows full profile has **77 units**, PR has **76**, and feature has **44**. The original
74 full IDs remain in their original relative order. Linux planning retains all required IDs and
explicitly blocks `implementation/powershell-media-image::powershell7`: **76 portable full obligations
plus one Windows obligation**, not an all-Linux full pass. Initial shard plans remain Windows plans.
Phase 5.8.3 must measure a complete split portfolio with equal captured inputs and review placement;
it must not bypass the Windows group or combine unrelated evidence into an aggregate pass.

## Preparation And Evidence Boundaries

WSL Ubuntu 24.04.5 x86-64 uses the existing owned Python 3.14.5 development environment and PS7.6.6
host/module receipts. Native Node 24.15.0/npm 11.12.1 was explicitly acquired from the official Node
release and verified against its SHA256 manifest. Render bootstrap uses the committed lock and
Mermaid 11.16.0/Puppeteer 25.3.0/full Chrome 150.0.7871.24; Firefox/headless-shell remain disabled.
The maintainer explicitly approved `unzip`, `libnss3`, `libasound2t64` and `fonts-liberation` inside
WSL; apt installed six packages including libnspr4/libasound2-data, adding 10.5 MB. No Windows
installation or browser sandbox policy changed. The first missing-unzip failure and its empty
extraction directory were retained before retrying; the prepared bootstrap now passes.
Current bootstrap code also passes offline/check-only validation against the existing owned
development environment, with matching declaration/lock inputs: Python and locked wheel payloads,
PowerShell modules/content receipts and actionlint 1.7.12 are verified. Standalone actionlint must
be placed on the process PATH explicitly; a missing host PATH entry is not permission to substitute
another version. No dependency installation occurs during these verification jobs.

The native source copy is audited against captured regular-file bytes and executable modes before
tests. Focused owners run in independent repository-supervised processes with deadlines, complete
logs and verified descendant cleanup. Each owner is followed by a source guard. These are focused
qualification jobs, not a timed aggregate profile or hosted evidence. No independent synthetic Git
baseline is used in this phase; authoritative capture supplies all tracked-under-ignored files.

Windows direct-checkout Visualization/QA attempts encountered an inaccessible old pytest temporary
directory during recursive scanning. Their canonical guards passed and failures are retained. A
fresh materialized source snapshot excludes unrelated ignored caches, matching modern aggregate
execution. Acceptance uses the isolated requalification, not a relaxed scan or changed golden.

Ignored `.tmp/ci-phase582/` retains captures, source audits, acquisition/preparation records,
supervised process records, stdout/stderr, original native XML and normalized JUnit evidence.
The verification below records focused results and source dispositions; no timed aggregate is claimed.

The first Linux preparation-tree Visualization result included 177 broken links in third-party
cache README files on Python, while PS did not traverse hidden caches; the initial QA inventory also
exposed host-dependent filename sanitation. Both failed attempts and their canonical guards are
retained. Requalification uses a separate native execution tree without dependency caches; the
comparison does not strip broken-link records or change golden expectations.

Current native proof: Windows passes **456 pytest / 58 Pester** cases with no skips/errors. The
changed Linux catalog/media selection passes **87 pytest** cases; portable EPUB and final QA path/
filename/link tests pass under PS7.6.6. Initial preparation and focused execution are different
captures. The final execution tree and final Windows consumer snapshot share exact 579-file bytes,
modes and source digest `438c0d12e0ed6cd04f21c96af18618def6d02067e7bb8ba9e7080f9b1a93e639`.
Only QA implementation/tests and documentation changed after the earlier broad focused capture;
the affected consumer/native proofs are repeated. This is not an aggregate assembled from captures.
All-source capture at 5.8.3 must include the final documentary updates before measurement.

## Final Focused Verification

- All eleven compatibility owners qualify on Linux with their current CLI/report/error/output
  contracts and canonical guards. Final isolated Visualization/QA retain the existing five-/35-file
  goldens; artifact lifecycle passes scoped deletion, regeneration, unsafe-output and sentinel checks.
  Affected Windows Visualization/QA/artifact owners also pass against the identical final capture.
- Both baseline runners pass 21 suites: **42 runtime variants**, exact typed Python/PS7 full-baseline
  parity, and exact equality of all 42 rows against certified Phase 5.7 Windows evidence. No shared
  fixture, normalization or suite membership changed. Remaining baseline qualification is closed.
- Final changed Linux native proof passes 87 pytest and 15 Pester cases (13 QA/Visualization path/
  filename/link cases plus two EPUB cases), with no skips/errors. Windows full native discovery and
  execution pass 456 pytest / 58 Pester cases. This adds genuine implementation/admission coverage;
  it does not register a permanent one-time Windows-versus-Linux comparison test.
- Real pinned Chrome rendering passes nonblank/representative-label/size and within-host dimensions.
  Linux's two runtimes produce identical 300079-byte SVGs, viewBox `0 0 11669.47265625 2814`;
  certified Windows evidence has identical 298414-byte SVGs per runtime, viewBox
  `0 0 11770.8046875 2814`. Linux Arial resolves to Liberation Sans. Cross-OS byte/width differences
  are reported, not stripped or silently reclassified; the existing owner requires within-host
  dimensions, not cross-OS byte identity. No new cross-OS comparator is adopted. Actual Chrome
  `ldd` inspection has no missing libraries; bootstrap verifies the adopted browser version.
- All qualified process trees verify cleanup; copied source bytes/modes and post-job source guards
  pass. Failed attempts remain alongside requalification. Ruff check/format, PS formatting,
  annotation policy (22/22 fixtures, 473 files, eight annotations) and `git diff --check` pass.

Ignored `linux-qualification-audit.json` reconciles the eleven owners, 42 exact reference/parity
rows, source differences and cleanup. Earlier broad focused jobs use the audited
`9bb21e0490af5607003c97fc2c06b49fbf197de5c1eff124585ef7371ea027ce` capture; final affected jobs
use the shared `438c0d12e0ed6cd04f21c96af18618def6d02067e7bb8ba9e7080f9b1a93e639` capture.
Every executable difference between them is confined to the requalified QA command and its native
test file. Documentation-only edits after that proof do not warrant repeating expensive consumer
jobs. Original passing/failing process records and complete logs are retained; this ledger is not a
passing complete aggregate or a substitute for the uniform-source Phase 5.8.3 measurement.

## Rollback And Next Checkpoint

Revert path corrections and schema-2 admission/metadata together if qualification fails. Preserve
the new required media coverage and its truthful Windows boundary when restoring older OS placement.
Do not modify canonical files, erase failures, weaken a golden comparator, silently retire helpers,
or declare the timing goals met through incomplete coverage. Phase 5.8.3 owns complete comparison,
fresh affected Windows/full requalification as needed, new-cost disposition and provisional placement.
