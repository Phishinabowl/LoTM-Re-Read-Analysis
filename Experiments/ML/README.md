# Machine Learning Experiments

## Purpose And Starting Point

Explore how machine learning could assist knowledge classification and source review through
small, understandable Jupyter exercises. The first experiment grows from an Iris classification
class: load data, explore features, split training and test examples, train, evaluate, and make a
live prediction. It should be explainable to a class while testing a useful part of the LoTM
platform's longer-term direction.

The Iris exercise uses four numerical flower measurements to predict a known species. This
experiment asks what changes when the input is a subject description and the target is a project
category. Turning text into numerical features is part of the lesson.

**Status:** documentation and initial directory structure only. No notebook, training corpus,
trained model, extraction pipeline, or execution results exist in this directory yet.

## First Proposed Experiment: Recommend A Category

Question: **Can a model recommend an existing category from a short description of one subject?**

Begin with a small, reviewed set of descriptions and known labels drawn from an explicitly chosen
subset of project categories, such as character, location, and faction. The final category set,
dataset size, example sources, and classifier remain to be selected after checking the available
examples. A proposed notebook name is `lotm-category-classification.ipynb`; it has not been created.

One row should initially represent one description of one identified subject. A chapter can mention
many subjects and categories at once, so classifying whole chapters would answer a different
question. A single-label teaching exercise also does not establish a single-category restriction
for the framework or for subjects that need more complex modeling.

The proposed teaching sequence is:

1. Load the reviewed examples and explain the input text, reference labels, and evidence basis.
2. Explore category balance and representative descriptions before fitting a model.
3. Hold out evaluation examples, keeping repeated descriptions of the same subject together.
4. Convert text into numerical features using an explainable starting approach such as TF-IDF.
   Learn the vocabulary and feature weights from training data only.
5. Train one simple classifier before introducing comparisons between algorithms.
6. Evaluate held-out examples with a baseline, per-category results, and a confusion matrix.
   Inspect incorrect predictions rather than relying only on overall accuracy.
7. Let a user enter a mystery description and inspect the suggested category and available model
   scores. Record whether the suggestion should be accepted, edited, rejected, or deferred.

The experiment should explain the difference between predicting a category and establishing a
fact. Model scores are not provenance confidence, proof of correctness, or automatic permission
to promote a record. Ambiguous descriptions and inputs outside the selected categories belong in
the discussion; a classifier choosing a label does not prove that any available label fits.

## Dataset And Evaluation Decisions

Dataset preparation is the next design step, not completed work. Review these choices before
building the notebook:

- Use sufficient independent subjects per category to support a meaningful split. If the available
  corpus is too small, describe the result as a teaching demonstration rather than a reliable
  estimate of generalization.
- Distinguish source passages, authored page descriptions, and synthetic teaching examples. Success
  on curated page descriptions does not establish success on raw ebook prose.
- Keep labels, category metadata, folder paths, slugs, and category-specific template scaffolding
  out of predictive inputs. Otherwise the model may simply recover an answer already supplied.
- Keep duplicates, near-duplicates, and related descriptions from leaking across the evaluation
  boundary. Choose grouping appropriate to the claim: unseen subjects, chapters, or works.
- Preserve source references and the reason for each reviewed label. Do not silently settle pending
  Phase 4 conflicts to manufacture training labels.
- Select a clear reader boundary for source-grounded examples and avoid introducing later reveals
  into examples presented as earlier reader knowledge.

For a class demonstration, a useful review table would show the input description, reference
category where known, model suggestion, error or uncertainty notes, and the reviewer's decision.
That table remains experimental output; it does not write back into canonical records.

## Related Experiments

| Task | Question | Relationship to this work |
| --- | --- | --- |
| Classification | Which existing category fits this subject? | First proposed exercise; uses reviewed labels. |
| Clustering | Which descriptions resemble each other without supplying labels? | Possible follow-up using the same descriptions with labels withheld from fitting. |
| Extraction | Which subjects, events, assertions, and relationships occur in a passage? | Later bridge from raw ebook text to candidate records. |
| Similarity and recommendation | What other material resembles this description or passage? | Possible retrieval aid for review and investigation. |
| Anomaly detection | Which examples look unusual relative to their peers? | Possible review aid; unusual does not mean incorrect. |

Clustering may group by setting, vocabulary, or topic rather than by the project's categories.
Cluster IDs are not canonical taxonomy IDs, and interpreting a cluster does not authorize adding
a new category. Comparing supervised predictions with discovered groups could provide a second
class exercise after the first notebook is understood.

## Existing EPUB Foundation

The repository already has a read-only source-search helper:

- Preferred Python command: [search_epub.py](../../Tools/Commands/Media/search_epub.py).
- PowerShell counterpart: [Search-Epub.ps1](../../Tools/Commands/Media/Search-Epub.ps1).
- Current switches, output shapes, limitations, and recorded parity evidence:
  [EPUB Search](../../Tools/TOOLING_REFERENCE.md#epub-search).
- Source-investigation discipline:
  [EPUB Sweep Tool](../../PROJECT_RULES.md#epub-sweep-tool).

The helper reads the supported Book 1 EPUB's XHTML into text and identifies chapter numbers,
volumes, titles, internal source paths, and entry types. It supports chapter and volume boundaries,
side stories and other non-chapter sections, literal or regex searches, contextual hits, counts,
volume summaries, and structured JSON output.

The established investigation loop is survey counts, inspect hits in chapter order, expand context,
discover additional search terms, repeat, and record paraphrased evidence with chapter references.
Machine assistance could eventually propose additional candidates within that workflow.

The current implementation has specific limits:

- Discovery depends on the Book 1 package layout. It does not yet select registered works through
  `Project_Config/sources.yaml` or support the current COI EPUB package. Empty discovery is not
  evidence that an unsupported book contains no content.
- Internal `Document.lines` holds extracted text, but search snippets are truncated presentation
  output. A future notebook must not treat snippets as complete source passages.
- Hit locations refer to extracted lines and internal paths. They are useful investigation context,
  but are not yet a durable paragraph-identity or source-revision contract.
- Section classification means chapters, appendices, artwork, and similar package sections. It
  does not perform semantic classification of characters, locations, or events.

Reuse this foundation where appropriate rather than building a second EPUB parser inside a
notebook. Any move from command-local parsing to a shared document service requires a separate
design and implementation increment. Broader format adapters remain future work.

## Long-Term Goal: Review An Entire Ebook

The intended product experience is to ingest an ebook and present chapter-by-chapter and
volume-by-volume suggestions that a user can accept, reject, edit, or defer before promotion into
canonical knowledge. This is a direction for exploration, not a claim that the complete pipeline
already exists.

```text
Ebook and source identity
  -> source text with structural locations
  -> candidate subjects, categories, events, relationships, and assertions
  -> framework checks and proposed matches to existing records
  -> chapter/volume review with evidence and unresolved alternatives
  -> explicit, governed promotion of accepted changes
```

Each suggestion should retain its supporting passage location, source identity, proposed meaning,
uncertainty, and review history. Framework services can check supported vocabulary, references,
identity, provenance, and applicable structural rules; they do not make an ML prediction true.
Future integration must use contracts actually implemented at that time. In particular, the
[effective project schema](../../Framework/Contracts/effective-project-schema.md) does not yet
provide the planned Phase 4 page-module contracts.

Sequential review must distinguish when something happened from when the reader learned it.
Later chapters may reveal an earlier event, correct a belief, or identify an unnamed subject.
Proposed identity links should preserve that disclosure history, and unresolved matches should
remain unresolved. Whole-book processing must not leak later knowledge into earlier bounded views.

Reviewed corrections could later supply examples for evaluation or training. Saving a review
decision does not automatically retrain a model, change a framework rule, or authorize unrelated
canonical mutations.

Machine-generated chapter summaries must remain identified proposals. Human-authored analysis and
structured assertions retain their separate canonical roles. Structured rows and authored blocks
must be filtered independently under the applicable visibility rules.

## Relationship To The Platform

Follow the parent [experiment conventions](../README.md) for authority, local artifacts, sharing,
and promotion. This work can continue while Phase 4 reconciliation is underway, but cannot resolve
its inventory findings or choose physical page storage on its behalf.

The [analytical projection architecture](../../Framework/analytical-projection-architecture.md)
already supports notebooks as exploratory consumers. The first exercise can run locally without
implementing SQLite, Parquet, Spark, or Databricks integration. Those platform projections and
adapters remain governed by the [implementation plan](../../Framework/platform-implementation-plan.md).

The educational objective is to understand the data, features, predictions, and mistakes well
enough to explain them. The platform objective is to learn which assistance is useful and what
evidence and review boundaries it needs before proposing a permanent service.
