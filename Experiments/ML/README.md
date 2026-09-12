# Machine Learning Experiments

## How The Experiment Uses The AI Service

The planned notebook will use a separately hosted, on-premises AI service to suggest subjects and
categories from chapter text. The notebook prepares selected passages, category guidance, and
previously reviewed decisions; the service runs a pretrained language model and returns suggestions
for human review. The notebook does not need to run the language model on the reader's computer.

The basic connection chain is:

```text
Notebook -> Microsoft sign-in -> HTTPS gateway -> local model server
Notebook <- streamed suggestions <- HTTPS gateway <- local model server
```

- **Sign-in:** Microsoft Entra authenticates the user and issues an access token. Access is limited
  to an assigned group, with membership managed through the existing directory synchronization.
  Applicable sign-in policies determine MFA requirements.
- **Secure connection:** the notebook sends its request and token over HTTPS. A reverse proxy
  handles the encrypted connection, and an authentication gateway checks the token and permitted
  API access before forwarding the request to the model server.
- **Local inference:** the model runs on a dedicated server. Selected source text is sent to that
  service for processing; Microsoft sign-in supplies identity, not the language-model response.
- **Streaming:** generated text can appear progressively in the notebook instead of waiting for
  the entire response. This improves responsiveness without changing the model's generation speed.
- **Review:** suggestions remain experimental. The user accepts, edits, rejects, or defers them;
  reviewed decisions become context for the next chapter, not automatic model retraining or
  changes to canonical project content.

The service foundation has been tested with authenticated, streamed responses. Notebook integration
and chapter-level extraction are still pending. Reproducing live requests requires authorized
service access, network connectivity, and certificate trust; private connection settings and
credentials are kept outside this shared README and saved notebook outputs.

## Purpose And Starting Point

Explore how machine learning could assist knowledge classification and source review through
small, understandable Jupyter exercises. The first experiment grows from an Iris classification
class: load data, explore features, split training and test examples, train, evaluate, and make a
live prediction. It should be explainable to a class while testing a useful part of the LoTM
platform's longer-term direction.

The Iris exercise uses four numerical flower measurements to predict a known species. This demo
extends that learning structure to source text: identify candidate subjects, suggest existing
project categories, and show how human decisions inform analysis of the next chapter. Unlike Iris,
the subjects are not already isolated into labeled rows; extraction is an additional task.

**Status:** experiment documentation and an independently tested AI service foundation are in place.
No notebook, experiment training corpus, extraction pipeline, or chapter-analysis results exist yet;
the service uses a pretrained model rather than a model trained by this experiment.

## Agreed Demo: Three Chapters With Progressive Review

Question: **Can assisted extraction and classification produce useful chapter-level suggestions,
and how do reviewed decisions change the next chapter's analysis?**

Use three sequential chapters from the supported LoTM Book 1 EPUB and an explicitly selected subset
of existing project categories, such as character, location, and faction. Exact chapters and
categories remain to be chosen. The private notebook and supporting data will live under
`Experiments\ML\.local\`, which is already ignored. No notebook has been created.

One candidate row represents a subject mention or proposed subject with supporting context, not a
category assigned to an entire chapter. A chapter can contain many subjects and categories. Repeated
mentions may propose a match to a reviewed subject, but must not silently merge identities. Any
simplified single-label exercise does not impose that restriction on the framework.

The review loop is:

1. Explain the approved category subset and inspect what the existing EPUB helper returns.
2. Read the first selected chapter and display short source snippets with their locations.
3. Produce candidate subjects and category suggestions with supporting evidence and uncertainty.
4. Pause for actual user decisions: accept, edit, reject, or defer, with reasons where useful.
5. Save those decisions as experimental state, separate from canonical project records.
6. Process the second chapter using its text and the reviewed state from the first; show which
   decisions influenced new suggestions. Review and save again before the third chapter.
7. Repeat for the third chapter, then compare new subjects, repeated mentions, corrections,
   unresolved cases, and any proposed revisions to earlier decisions.

Do not invent a completed review history for presentation. Build and execute the review checkpoints
with the user, preserving their actual decisions. Accepted subjects, corrected categories,
rejection reasons, and deferred identity matches should remain distinguishable. Later evidence may
justify revisiting an earlier decision; preserve the history and the chapter where that evidence
appeared instead of silently replacing the earlier understanding.

Carrying reviewed state into the next analysis supplies context; it does not automatically retrain
a classifier. The implementation must explain how the selected method consumes that state. In a
mature pipeline, preliminary extraction could run ahead or in parallel, with reconciliation and
dependency tracking afterward. Human approval before every chapter is the chosen teaching workflow,
not a universal production requirement.

## Notebook Teaching And Private Sharing

Follow the Iris notebook's rhythm: explanatory Markdown, a manageable code cell, and visible
results. Introduce the question, purpose, inputs, and expected observations before each meaningful
step. Explain unfamiliar Python and ML concepts when they first appear.

Code comments should explain intent, transformations, and meaningful decisions. Repository helper
calls need particular care: classmates will not have the full repository. Introduce what each
helper does, show the shape of the data it returns, and explain how the notebook uses that result.
Avoid comments that merely repeat syntax or imply the helper performs semantic extraction when it
only reads or searches source text.

The notebook should read as a complete lesson covering the goal, categories, source reader, three
chapter/review cycles, and final lessons and limitations. Distinguish automatic suggestions, user
decisions, and any manually prepared examples throughout.

Connect the lesson to the long-term platform at relevant points in Markdown and code comments.
Each reference should briefly explain what the owning phase will provide, how the current step
relates to it, and whether the capability is implemented, experimental, or planned. Verify phase
names and status against the current implementation plan when authoring the notebook rather than
assuming this outline remains current.

Use these connections where they help explain the demonstrated behavior:

- Category loading: implemented framework catalog and effective project schema; distinguish these
  from Phase 14 configuration recommendations and Phase 16 setup wizards.
- Candidate fields and descriptions: Phase 4 structured modules and authored blocks, followed by
  Phase 5 normalized content. Temporary notebook rows are not those future canonical contracts.
- Repeated subjects and proposed connections: existing identity/reconciliation services where
  actually used, plus Phase 6 normalized relationships. Label experimental matching explicitly.
- Review checkpoints: Phase 12 preview, mutation, recovery, and editorial governance, with Phase 16
  editing interfaces. Saving a demo decision does not implement canonical promotion.
- Chapter-level presentation: Phase 10 generalized summaries and Phase 11 generated projections;
  preserve the distinction between source snippets, generated proposals, and authored analysis.
- Final recap: show how the three-chapter experiment informs a future ingestion workflow while
  keeping the ML orchestration itself identified as future design.

Recipients will not have the repository, so a phase number or relative link alone is insufficient.
Include the phase title, a short plain-language explanation, and the owning document path beside
useful references. Links can supplement that explanation but must not be required to understand
it. Keep code comments focused on the connection at that call or transformation; use Markdown for
broader architecture. Avoid repeating the full roadmap in every section or presenting future
services as dependencies already available to the notebook.

Run and save the intended outputs before private sharing. The `.ipynb` should retain Markdown,
code, short extracted snippets, chapter/internal-path/line references, ordinary result tables, and
embedded plots if useful. Explain when snippet text is truncated. Show before/after review state
and the influence of earlier decisions without requiring recipients to follow external file links.

Recipients can inspect saved outputs in a compatible notebook viewer without the repository or
rerunning cells. Rerunning still requires the source files, helpers, dependencies, and any selected
model access. Do not rely on live widgets or a running kernel to communicate saved review results.
An HTML companion may be useful later, but is not part of the current documentation increment.

The notebook, source-derived data, and results remain in `.local/`; only these general READMEs are
intended for Git. Short snippets are deliberately retained for this private learning demo. No
email sending or other distribution is part of notebook creation.

## Method Selection Still Pending

The three-chapter workflow is agreed; the extraction/classification method is not yet selected.
A traditional supervised exercise with manually identified subjects teaches feature extraction
and training. A language-model-assisted extractor is closer to the intended ingestion experience,
but must be explained as that kind of experiment rather than presented as an Iris-style model
trained from scratch. Decide the method, dependencies, model access, and state input before coding.

The earlier description-only TF-IDF classifier remains an optional smaller exercise, not a mandatory
first stage of the agreed demo. If used, learn vocabulary and feature weights from training data
only, hold out independent examples, and inspect a baseline, per-category results, and confusion
matrix. Do not report training metrics for a method that did not train a classifier.

The experiment should explain the difference between predicting a category and establishing a
fact. Model scores are not provenance confidence, proof of correctness, or automatic permission
to promote a record. Ambiguous descriptions and inputs outside the selected categories belong in
the discussion; a classifier choosing a label does not prove that any available label fits.

## Dependencies And Reproduction

The maintainer is comfortable installing appropriate Python libraries for the agreed experiment.
Choose dependencies after selecting the method and explain their purpose. No dependencies have
been installed as part of this documentation work.

Include a clearly labeled setup section near the start of the notebook documenting:

- the Python version, notebook environment, and kernel used for the demonstrated run;
- each third-party package, its installation name, import name when different, and role;
- standard-library imports that need no separate installation;
- repository-owned modules/helpers that cannot be obtained simply by installing a PyPI package;
- the source EPUB and local supporting files required to reproduce the demo;
- any model downloads, external services, credentials, network, or compute requirements, including
  whether inference runs locally or remotely;
- the package versions actually used and environment-appropriate installation instructions,
  including kernel restart guidance where needed.

Use a short dependency table and commented imports to connect each library to its purpose. Place
installation commands in an explicit setup cell or documented setup step rather than silently
installing packages during analysis. Keep credentials out of code, outputs, and saved metadata.
Explain any external transfer of source text before using a selected service; permission to install
libraries does not itself select a service or authorize purchases.

Separate viewing requirements from execution requirements: classmates only need a compatible
viewer to inspect saved Markdown and outputs. Rerunning requires the documented environment,
repository helpers, source files, and any selected model access. Record actual setup and versions
when implemented rather than presenting speculative dependencies as installed or tested.

## Dataset And Evaluation Decisions

Source selection and method-appropriate evaluation remain design steps, not completed work. Review
these choices before building the notebook:

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

The chapter review table should show chapter, candidate mention, suggested category, supporting
snippet and location, proposed match to earlier reviewed state, uncertainty, and reviewer decision.
Include reference labels only where actually reviewed. Evaluate extraction omissions and duplicate
or incorrect identity suggestions as well as category errors. Three chapters demonstrate a workflow;
they do not establish whole-book reliability. All review output remains experimental and does not
write back into canonical records.

## Related Experiments

| Task | Question | Relationship to this work |
| --- | --- | --- |
| Classification | Which existing category fits this subject? | Part of the three-chapter demo; uses existing approved categories. |
| Clustering | Which descriptions resemble each other without supplying labels? | Possible follow-up using the same descriptions with labels withheld from fitting. |
| Extraction | Which subjects, events, assertions, and relationships occur in a passage? | Subject candidates enter the initial demo; broader event, relationship, and analysis extraction remain later increments. |
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

The current framework catalog can describe installed packs before a project exists, and the
effective project schema can describe LoTM's configured categories and capability state. This demo
uses that existing configuration; it does not build the separate project-setup recommendation flow.

Future platform work supplies the broader integration: Phase 4 page fields/modules/authored blocks,
Phases 5-6 normalized content and relationships, Phase 10 generalized summaries, Phase 11 analytical
projections, Phase 12 mutation and editorial governance, Phase 14 optional solution/schema
recommendations, and Phase 16 wizards and editors. The full ML ingestion orchestration is a separate
future design, not an already implemented pipeline or an additional completed phase.

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
