# Experiments

This directory holds focused learning exercises, exploratory notebooks, and prototypes that help
evaluate ideas for the reusable knowledge framework. LoTM is the first project used to exercise
those ideas; experiment-specific assumptions do not become universal framework rules.

Experiments should be small enough to understand, explain, and review. They can demonstrate a
possible feature, expose a limitation, or supply evidence for a later design decision without
implementing that feature in the platform.

## Current Work

| Area | Purpose | Status |
| --- | --- | --- |
| [ML](ML/README.md) | Demonstrate extraction, category suggestions, and progressive human review across three LoTM chapters. | Agreed demo scope; notebook and execution remain pending. |

## Authority And Scope

[ARCHITECTURE.md](../ARCHITECTURE.md) owns component and authority boundaries. The
[analytical projection architecture](../Framework/analytical-projection-architecture.md) owns
notebook and analytical-consumer policy. These documents remain authoritative as experiments evolve.

- Structured knowledge and human-authored prose are separate first-class canonical content.
  Preserve authored wording; do not reconstruct narrative analysis from taxonomy or YAML values.
- Generated summaries, predictions, clusters, charts, and notebook outputs are experimental
  projections or proposals. They do not become canonical knowledge by being produced or saved.
- Read project categories and supported behavior from the appropriate project configuration and
  shared services. Keep domain-specific examples separate from reusable mechanics.
- Preserve uncertainty, contradictory evidence, and unresolved identity matches. A successful
  schema check does not establish that a proposed assertion is true.
- Experiments do not close platform-plan checkboxes, resolve discovery conflicts, migrate pages,
  or change production contracts without a separately reviewed promotion step.

The current [platform implementation plan](../Framework/platform-implementation-plan.md) and
[page-schema discovery inventory](../Framework/page-schema-discovery-inventory.md) govern Phase 4.
ML exploration can proceed independently while that reconciliation continues.

## Working And Sharing Conventions

Track general experiment documentation and only explicitly approved notebook code and teaching
fixtures. The initial ML demo notebook and its supporting data remain ignored under `ML/.local/`.
Label synthetic examples and distinguish them from source-grounded project evidence.
Keep personal class conversations and local reference documents outside shared documentation.

Use an experiment-local `.local/` directory for extracted source text, working datasets, trained
models, and generated results. Use `.tmp/` for disposable intermediate files. Both directory names
are already ignored by repository policy; the root `.gitignore` also excludes Jupyter checkpoints
throughout the repository.
Original ebooks remain in the existing ignored `Source/` area.

Before committing or publicly publishing a notebook, inspect its saved outputs and metadata. Clear
source excerpts, private information, machine-specific paths, and bulky generated output. An ignored
data directory does not protect text embedded in a tracked notebook. Record source references and
paraphrased findings rather than copying long ebook passages into tracked files.

The initial ML demo is intended for private class sharing, not Git publication. Its ignored notebook
will deliberately retain short source snippets, source locations, and saved results so readers can
follow the lesson without the repository. Review that copy for credentials, unrelated private data,
and unnecessary local paths before sharing; retain the intended teaching evidence. Keeping a file
ignored does not prevent a recipient from seeing material embedded in it.

Each experiment should explain:

- the question being tested and the limits of the claim;
- its inputs, evidence basis, label decisions, and relevant reader/source boundary;
- the steps needed to reproduce it, including dependencies and randomness where applicable;
- how results are evaluated, including mistakes and unresolved cases;
- whether any finding warrants a proposed framework change.

Reuse existing helpers where their behavior fits. Notebooks must not become hidden owners of
production parsing, validation, composition, or mutation rules. If an experiment establishes a
durable requirement, propose its promotion through the
[framework improvement lifecycle](../Framework/framework_improvement_lifecycle.md), with the
[testing methodology](../Framework/testing_methodology.md) supplying applicable permanent coverage.
Shared runtime behavior should then be callable from the notebook rather than duplicated there.

## Initial Structure

```text
Experiments/
  README.md
  ML/
    README.md
```

Notebook creation, dataset preparation, dependency installation, and model execution are separate
future increments.
