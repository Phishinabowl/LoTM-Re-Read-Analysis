# Framework Improvement Lifecycle

## Purpose

This document is the authoritative workflow for improving the reusable knowledge framework. It is the entry point for a maintainer or a fresh coding-assistant session entering **framework improvement mode**.

It coordinates three separate authorities without merging their responsibilities:

- this lifecycle owns the order of work and the completion gates;
- `Framework/testing_methodology.md` owns the pressure-test candidate catalog and cumulative test requirements; and
- `Framework/framework_evolution.md` owns the historical record of what changed, why it changed, what testing found, and what should happen next.

The process is circular. A version begins from the prior evolution recommendation, proposes testing from the retained methodology, implements and verifies the change, records its implementation commit, runs pressure testing, improves the methodology when durable coverage is discovered, records the results and next recommendation in the evolution history, and begins again.

## Entering Framework Improvement Mode

For a new machine, checkout, Codex task, or context-recovery pass, read and inspect in this order:

1. `PROJECT_RULES.md` for mandatory project policy and evidence discipline.
2. `ARCHITECTURE.md` for component ownership and framework boundaries.
3. This lifecycle for the current iterative workflow.
4. `Framework/testing_methodology.md` for retained test families and impact rules.
5. The era index, latest completed version, latest `Testing After Vn` section, and next-version recommendation in `Framework/framework_evolution.md`.
6. The affected contracts, packs, project registries, fixtures, and `Tools/TOOLING_REFERENCE.md` sections.
7. Git branch, status, recent history, and local source/tool availability relevant to the proposed work.

Before designing a version, identify:

- the current completed framework version;
- the last confirmed implementation and pressure-test commits;
- the latest recommended next version;
- unresolved defects, missing capabilities, and explicit deferrals;
- the current permanent test counts and compatibility baseline; and
- the current pressure-test candidate catalog and which candidates were used in the most recent rounds; and
- any uncommitted user or generated changes that must be preserved.

Use Repository Mode evidence discipline unless the maintainer explicitly authorizes source expansion or outside research. A pressure-test scenario may use synthetic or researched evidence, but its basis must be labeled.

## Circular Document Ownership

| Artifact | Lifecycle Role |
| --- | --- |
| `Framework/framework_improvement_lifecycle.md` | Defines how a version moves from recommendation through implementation, confirmation, testing, historical closure, and handoff. |
| `Framework/testing_methodology.md` | Defines candidate selection and retention, what must be tested, stable test-family IDs, impact-based additions, comparison rules, and result classification. |
| `Framework/framework_evolution.md` | Records version intent, exact implementation commit, architectural lessons, executed tests, findings, and next-version recommendation. |
| `Tools/TOOLING_REFERENCE.md` | Defines exact current commands, switches, output contracts, parity recipes, normalization rules, and dated executions. |
| `PROJECT_RULES.md` | Makes the lifecycle and its testing gates mandatory project policy. |
| Contracts, packs, registries, fixtures, and tools | Implement the current framework and its permanent executable proof. |

The required information flow is:

```text
prior evolution recommendation
-> version scope, proposed testing, and proposed candidates
-> implementation and permanent fixtures
-> cumulative methodology-driven verification
-> two-part implementation confirmation
-> methodology-driven pressure testing
-> methodology and candidate-catalog revision when durable coverage changes
-> evolution results and next recommendation
-> next version
```

Do not copy the complete testing contract into the evolution log, exact commands into this lifecycle, or historical results into the testing methodology. Use links and stable test-family IDs to keep the loop connected.

## Version Lifecycle

### 1. Orient And Recover State

Complete the framework-improvement read order, inspect Git state, and summarize the current version boundary before editing. If a prior task stopped midway, determine which lifecycle gate was last completed instead of restarting or guessing.

### 2. Define The Version

Derive the proposed version primarily from the preceding `Testing After Vn` recommendation. Discuss and settle:

- version number and concise title;
- problem and superseded assumption, when applicable;
- intended ownership layer: core, reusable domain pack, project configuration, or consumer;
- contracts, runtimes, fixtures, consumers, and docs likely to change;
- explicitly excluded work and deferred capabilities;
- acceptance criteria; and
- recommended testing by stable methodology ID, selected catalog candidates, and any new version-specific probes.

Every proposed version must name its recommended testing before implementation. At minimum, apply the required framework-version baseline and change-impact matrix from `Framework/testing_methodology.md`, review its pressure-test candidate catalog, and select candidates that stress the affected matrices. If the version exposes a durable new risk class, scenario, candidate, comparison rule, or consumer, propose the methodology revision at this stage rather than treating it as an informal one-off.

### 3. Open The Evolution Entry

Before implementation confirmation, add the new version section to `Framework/framework_evolution.md` with:

```markdown
## Vn - Version Title

**Implemented by:** pending

**Proposed testing:** `CONF-*`, `PARITY-*`, `COMPAT-*`, and applicable `SCENARIO-*` or `PRESSURE-*` IDs.

**Proposed candidates:** Named catalog candidates and any explicitly labeled new conceptual, synthetic, repository-grounded, or externally source-grounded probes.
```

Then record the problem, design, ownership decision, implementation surface, reason, explicit exclusions, and any applicable marker:

- `Superseded assumption`;
- `Architectural extraction`; or
- `Architectural promotion`.

Also add a `## Testing After Vn` placeholder that states testing is pending. Do not prewrite successful results.

The `Proposed testing` and `Proposed candidates` fields are mandatory for new versions beginning with V38. Older entries do not need retroactive fields unless they are otherwise being corrected.

### 4. Implement The Version

Implement the accepted contract across every owning layer:

- contracts and pack declarations;
- Python and PowerShell runtime implementations where paired ownership applies;
- project composition or instance data when the change requires it;
- positive, malformed, decision, boundary, and scale fixtures required by the methodology;
- downstream consumers affected by the contract; and
- architecture, tooling, and narrow operational documentation.

Keep generated outputs redirected and noncanonical during verification. Preserve unrelated worktree changes. A deterministic defect repaired during implementation must become a permanent regression vector.

### 5. Run Implementation Verification

Use `Framework/testing_methodology.md`, not memory, to select and execute:

- the complete required framework-version baseline;
- all impact-matrix additions;
- three-runtime and structured-output parity;
- project compatibility consumers, including QA and visualization; and
- root-discovery, rendering, artifact-safety, or scale tests when triggered.

Use `Tools/TOOLING_REFERENCE.md` for exact commands and comparison recipes. Update that reference when a command, switch, output contract, expected count, normalization rule, or dated parity record changes.

Review the testing methodology before closing verification. Add or revise durable coverage there if the version introduced a new test family, retained scenario, candidate, impact trigger, comparison rule, classification need, or retirement. Do not silently omit inherited coverage or repeatedly choose only familiar candidates when another catalog entry would test the abstraction more honestly.

Any unclassified failure blocks implementation confirmation. Repair implementation and parity defects, migrate accepted contract changes explicitly, and preserve missing capabilities or deferrals for the pressure-test record.

### 6. Confirm Implementation In Two Parts

Framework version implementations use a mandatory two-part commit sequence so the evolution log can cite the exact implementation commit without creating a self-reference problem.

1. Stage and commit all implementation, contract, fixture, consumer, methodology, tooling-reference, and supporting documentation changes **except** `Framework/framework_evolution.md`.
2. Capture the implementation commit's short hash and exact subject.
3. Replace the pending marker with exactly:

   ```markdown
   **Implemented by:** `<short-hash>` (`<exact commit subject>`)
   ```

4. Stage and commit `Framework/framework_evolution.md` as a separate documentation-reference commit.
5. Push both commits and verify branch/upstream state.

Run Git staging, commit, and push operations as separate commands. Codex sessions in this repository have intermittently encountered transient `.git/index.lock` errors when documentation-reference operations were chained. Never delete the lock unless its existence and staleness are independently verified.

The implementation is now confirmed, but the version lifecycle is not closed until post-version pressure testing is recorded.

### 7. Run Post-Version Pressure Testing

Start from the proposed testing recorded in the version entry, then consult the current methodology again. Run:

- every applicable retained scenario;
- adversarial and cross-domain pressure families;
- scale pressure when required;
- the selected catalog candidates, rotated where practical across industries and structural patterns;
- new version-specific conceptual or executable probes; and
- affected implementation-conformance and compatibility families when pressure work changes code or fixtures.

Pressure testing must try to break the version's assumptions. Distinguish consistent missing capability from implementation correctness: three runtimes can agree on the same defect.

Classify every meaningful result using the methodology's result classes. If a deterministic defect is fixed during pressure testing, add permanent regression coverage, rerun the affected cumulative and compatibility gates, and cite the corrective commit in the evolution results. If testing discovers a durable new testing obligation or a reusable candidate that exposes a distinct structural pressure pattern or fills an industry gap, revise `Framework/testing_methodology.md` before closing the round. Do not promote every one-off example; apply the catalog retention rules.

### 8. Close The Evolution Record

Replace the `Testing After Vn` placeholder with a concise but complete record of:

- stable test-family IDs actually run;
- permanent fixture/assertion counts and meaningful count changes;
- runtime parity and structured-output results;
- QA, visualization, render, root-discovery, and other compatibility results;
- source-grounded, synthetic, adversarial, cross-domain, and scale scenarios;
- catalog candidates used, their evidence classification, and any catalog addition, revision, replacement, or deliberate non-promotion;
- implementation or parity defects found and repaired;
- accepted contract changes;
- missing capabilities and deferrals; and
- the recommended title, scope, and exclusions for Vn+1.

Keep requirements in the methodology and commands in the tooling reference. The evolution entry should explain what happened, what was learned, and why the next recommendation follows.

### 9. Confirm Testing Results

When pressure testing changes only the historical record, commit and push the evolution update as one testing-results commit.

When pressure testing causes implementation, fixture, methodology, or tooling changes:

1. commit the corrective or coverage changes first;
2. capture the exact commit reference;
3. record the correction and rerun results in the evolution entry;
4. commit the evolution update separately; and
5. push and verify the branch.

After confirmation, the next version begins at Step 1 using the newly recorded recommendation.

## Completion Gates

A framework version may not advance when:

- its scope or proposed testing is still undefined;
- its evolution entry does not identify the planned verification;
- implementation conformance, parity, or required compatibility has an unclassified failure;
- its implementation commit is not cited through the two-part confirmation sequence;
- post-version pressure testing has not consulted the current methodology;
- the candidate catalog was not reviewed or the evolution record does not identify which candidates were used;
- a durable testing discovery has not been incorporated into the methodology;
- pressure-test results or the next-version recommendation are missing from evolution history; or
- temporary artifacts, canonical-output mutations, or unrelated worktree changes remain unexplained.

## Maintainer Confirmation Semantics

In this project, when the maintainer says `confirm` or `confirmed` about completed changes, that means intentionally stage, commit, and push them.

For a framework version implementation, confirmation means the two-part implementation sequence above. For a completed pressure-test record with no implementation changes, confirmation normally means one evolution-results commit and push. Stop at an explicitly requested checkpoint even when later lifecycle work is already known.

## Future Automation

This document is the human and coding-assistant workflow authority. Stable test-family IDs and the structured lifecycle are designed to support a future framework-version runner, machine-readable test profile, editor, or wizard. Automation must implement this lifecycle rather than creating a competing definition of version completion.
