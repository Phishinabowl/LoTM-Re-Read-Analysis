# CI 5.3 Consumer Compatibility And Safety Proof

**Status:** Implemented, verified locally and confirmed by the maintainer on 2026-10-06.

The [modernization plan](ci-testing-modernization-plan.md) owns acceptance. The
[CI 5.1 comparison](ci-testing-shadow-comparison.md) identified nested output-path normalization
and generic failure summaries; [CI 5.2](ci-testing-conformance-parity-proof.md) closed formatting
representation and semantic conformance. This checkpoint changes neither consumer semantics nor
canonical pages, templates, Relationship Seeds, QA/Visualization sources or golden baselines.

## Changes And Ownership

`Tools/Compatibility/run_compatibility.py` now derives generated repository-relative output aliases
from the nearest `.tmp` component. An execution checkout can itself be beneath an outer `.tmp`:
the previous first-component lookup retained that outer isolation path and missed aliases emitted
relative to the actual execution repository. Absolute aliases and both slash conventions remain
supported. Existing generated-time/line-ending normalization is unchanged; authored wording and
array order remain protected. This applies to the currently implemented owned output layout.

`Tools/CI/layer_adapters.py` promotes failed owning conformance/compatibility checks' error text into
aggregate reasons, with envelope-error fallback. PowerShell formatter failures include counts and
affected paths/long-line details. Excerpts use the existing 20-line/4,096-byte reporting boundary,
plus an explicit truncation notice. Complete owner JSON and process streams remain separate retained
artifacts; success output stays concise. Owner schemas, statuses, exit reconciliation and canonical
guards still determine outcomes. Reporting never converts an invalid owner result into a pass.

The compatibility registry already selects distribution-boundary through the PR integration
catalog's explicit additional reference. No membership or workflow edit was required. It remains
separate from the copied-framework extraction and installed-wheel boundaries.

## Regression And Safety Evidence

The existing ci-execution group gains 17 cases: six nested-output alias combinations, four bounded
owner-error cases, one envelope fallback, two real adapter/aggregate/Markdown failure cases, two
real nested-child interruption cases, one formatter diagnostic case and one multiple-failure
continuation case. No new group, test-directory sweep or duplicate shared-conformance run is added.

- The final ci-execution group passes **122 cases on Windows and 122 on WSL Ubuntu 24.04**.
  Windows takes 10.46 seconds; Linux takes 7.98 seconds (8.51 seconds including observation/cleanup).
- Compatibility implementation and catalog regression pass **119 cases** on Windows in 20.77 seconds.
- The complete Python collection is 407 cases; current mandatory infrastructure inventory is 310.
  PowerShell remains 44. Collection counts are inventory, not claims that the entire portfolio ran here.
- Nested-child drills invoke the actual compatibility `run_command` under the production supervisor.
  One inherits the whole-unit deadline and reports retained owner failure; the other is cancelled
  after the child signals readiness. Both verify tree cleanup and preserve an unrelated artifact.
- Existing deadline/partial-stream, protected-source mutation and unsafe-state stop tests remain.
  Two independent compatibility failures are retained while a later passing check still executes.
- Normalization tests cover zero, one and two outer isolation directories, absolute and repository-relative
  aliases, both slash conventions, unchanged authored wording and preserved list order.
- Real failed owner envelopes reach aggregate failures and escaped Markdown with specific diagnostics.
  Bounded promotion leaves the original evidence untouched, including truncated content.

All **ten registered non-render compatibility checks pass** through the owning adapters, with both
Python and PowerShell 7 configured. Summed unit execution is **568.18 seconds (9 minutes 28 seconds)**;
this excludes capture/preflight/report recovery and is not a full-profile performance acceptance.

| Registered check | Result | Preserved boundary |
| --- | --- | --- |
| compatibility-reporting | Passed | Owner CLI selection, concise/detailed reporting and failure/export contracts. |
| conformance-reporting | Passed | Shared-suite CLI selection, reporting and expected rejection behavior. |
| framework-catalog | Passed | Composed catalog semantics, public commands and invalid-input cases. |
| effective-schema | Passed | Effective schema export/selection, diagnostics and compatibility behavior. |
| visualization | Passed | 15 nodes/121 relationships; unchanged five-file refresh inventory and unbounded graph hashes. |
| qa | Passed | Unchanged structured summary and 35-file golden inventory, including bounded reader projections. |
| root-discovery | Passed | Eight runtime/location launches across repository, Tools, nested and unrelated locations. |
| artifact-lifecycle | Passed | Stale/optional outputs removed, four unsafe destinations rejected, scoped cleanup and unrelated sentinel preserved. |
| framework-extraction | Passed | Existing copied-framework consumer contracts; portable release rehearsal remains 5.4. |
| distribution-boundary | Passed | Existing project/core pack separation; PR integration membership explicitly verified. |

The eight checks already passing in 5.1 match their retained semantic results exactly after removing
only the previously declared operational fields `elapsed_seconds`, `concise_bytes` and `detailed_bytes`.
Visualization/QA were failed in 5.1; they are compared with the unchanged owning golden baselines,
not a new baseline derived from this run. Both runtime trees match and all source/canonical guards pass.
The external scratch and consumer success outputs are cleaned; the unrelated observer sentinel survives.
The aggregate JSON/Markdown/custom JUnit bundle passes publication admission with **54 manifest files**.

## Execution Provenance And Limits

Ignored evidence lives beneath `.tmp/ci-phase53/`. The consumer observer captures commit `91a1b71`
plus explicit Git-normalized overlays for the compatibility owner, adapter and test file. Each overlay
is checked against Git's filtered blob hash before materialization. It uses registered catalog rows,
production adapters, deterministic sequential aggregation and whole-source guards; it is a narrowed
ten-check observation, not a passing full-verification profile or committed acceptance run.

The temporary observer initially used the wrong referee suffix when preparing selection, before
launching consumers. Its owned scratch was removed. The completed ten-check observation then hit an
incorrect aggregate-report helper call after saving every terminal result and cleaning scratch.
Reporting was reconstructed from those retained results without rerunning consumers; reconstruction
independently rechecks captured source bytes, guard/cleanup, artifact contents and final publication
admission. Incorrect temporary report projections are preserved separately and excluded from the
admitted manifest. These observer errors do not change production runners or consumer outcomes.

Later edits add formatter-only diagnostic promotion and focused regression cases after this capture.
They do not alter successful compatibility execution or consumer normalization. The final focused
Windows/Linux suite tests the final adapter, including its failure-reporting path. Frozen provenance
and later edits are distinguished rather than labeling different source states as the same commit.

Rendering/browser/npm admission, original wheel readability and portable release reproduction remain
5.4. Successful corrected full-profile/performance acceptance remains 5.5. Hosted adoption and
optional actionlint integrations remain Phase 6. No test, fixture or legacy check is retired.

## Local Reproduction

Use the exact prepared Python executable and PowerShell module cache recorded by bootstrap.
The native ci-execution group is authoritative through the implementation catalog; these focused
commands are diagnostic recipes rather than an alternative registration mechanism:

```powershell
& $python -B -m pytest Tools/Tests/Python/test_ci_execution.py `
    Tools/Tests/Python/test_ci_gate.py Tools/Tests/Python/test_ci_reports.py -q

& $python -B Tools/Compatibility/run_compatibility.py --check compatibility-reporting `
    --check conformance-reporting --check framework-catalog --check effective-schema `
    --check visualization --check qa --check root-discovery --check artifact-lifecycle `
    --check framework-extraction --check distribution-boundary `
    --output-root .tmp/phase53-local-consumers --json
```

Choose a fresh output owner for each invocation. Successful outputs are scoped and cleaned; failures
retain their owner report. A direct primary-checkout diagnostic is distinct from the frozen isolated
observer; the latter also verifies captured source bytes and publishes the aggregate projections.

Final scoped checks pass: Ruff lint/format on the three changed Python files; annotation policy's
22 fixtures across 462 eligible files; 82 relative documentation links and Git whitespace review.
No canonical, registry, dependency, workflow or unrelated tracked edit is present. Maintainer
confirmation on 2026-10-06 authorizes the focused CI 5.3 commit and dual-remote publication.
