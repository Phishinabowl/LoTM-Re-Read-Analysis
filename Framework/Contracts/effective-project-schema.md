# Effective Project Schema Contract

## Purpose

`EffectiveProjectSchema` is the domain-neutral, generated description of the schema that one
project can actually use after project configuration, selected schema packs, capability lifecycle,
capability activation, taxonomy, and resource configuration have been composed.

It is the common inspection boundary for headless tools, QA, Visualization, editors, and future
interfaces. Consumers must not reconstruct equivalent pack, capability, vocabulary, taxonomy, or
resource state from the individual registries.

The effective schema is diagnostic output, not canonical configuration. Its inputs remain the
project manifest, selected packs, and project registries. Editing an export has no effect on the
project.

## Ownership And Scope

Core owns the effective-schema shape, lifecycle resolution, diagnostics model, deterministic
ordering, and serialization contract. Selected packs own capability and controlled-value
definitions. Project registries own instantiated taxonomy, roots, placements, and resource policy.

Contract version 2 retains every version-1 field and adds:

- selected-pack architectural classification and complete pack presentation;
- effective and provider-level capability presentation;
- deterministic singular pack and capability selection over the composed document.

The complete contract includes:

- project identity and input schema versions;
- selected packs in validated dependency order;
- declared capability providers, lifecycle, availability, and activation state;
- composed controlled-value namespaces, definitions, broader-value relationships, and owners;
- configured content roots, content types, categories, placements, templates, QA eligibility, and
  graph eligibility;
- configured resource roots, kinds, types, placements, authority, tracking, and editor eligibility;
- deterministic diagnostics that can be produced after successful composition.

Page modules, normalized content records, canonical relationships, and projection declarations join
the effective schema only when their later platform contracts are implemented. Their absence from
version 2 is not an empty declaration that they exist.

## Document Shape

The serialized document uses this top-level order:

```json
{
  "contract": "effective-project-schema",
  "contract_version": 2,
  "project": {},
  "registry_schema_versions": [],
  "packs": [],
  "capabilities": [],
  "controlled_value_namespaces": [],
  "content": {},
  "resources": {},
  "diagnostics": []
}
```

Every listed key is required. Collections are present as empty arrays or objects when validly empty;
they are not omitted. JSON `null` is used only where this contract explicitly permits it.

## Project Identity

`project` contains:

| Field | Meaning |
| --- | --- |
| `project_id` | Stable project ID from the project manifest. |
| `framework_id` | Selected framework ID. |
| `domain_id` | Selected domain ID. |
| `project_manifest_schema_version` | Validated project-manifest schema version. |

The export never contains the repository's absolute path, current working directory, machine name,
user profile, or generation timestamp. Those values are environmental rather than schema identity
and would make otherwise identical compositions compare differently.

`registry_schema_versions` is an array of `{ "registry_id", "schema_version" }` rows for every
registry whose data contributes to the export. It is ordered by `registry_id`. Pack schema and pack
release versions remain on each pack row because independently versioned packs may differ.

## Selected Packs

`packs` contains one row per selected pack in validated dependency order:

| Field | Meaning |
| --- | --- |
| `id` | Stable pack ID. |
| `kind` | Pack kind such as `core`, `domain`, or `extension`. |
| `lifecycle` | Pack lifecycle. |
| `schema_version` | Pack document schema version. |
| `pack_version` | Pack's independently incremented release version. |
| `label` | Human-facing pack label. |
| `description` | Human-facing pack description. |
| `classification` | Authored family, architectural role, scope, domains, and bridge joins. |
| `presentation` | Complete localizable pack presentation, or `null` for a legacy schema-4 input. |
| `dependencies` | Ordered dependency rows. |

Each dependency row contains `pack_id`, `minimum_version`, `selected_version`, and `status`.
Successful composition uses status `satisfied`. A missing, out-of-order, or incompatible hard
dependency is fatal and therefore cannot produce an `EffectiveProjectSchema`; the command boundary
reports it through the failure behavior defined for Phase 2.2.

Dependency order is the schema-pack registry's validated selection order. It is meaningful and must
not be alphabetized by serializers.

## Capability Resolution

`capabilities` contains one row for every capability declared by at least one selected pack. Rows are
ordered by capability ID. Each row contains:

| Field | Meaning |
| --- | --- |
| `id` | Stable capability ID. |
| `declared` | Always `true` for a serialized capability row. |
| `effective_lifecycle` | Resolved `available`, `deprecated`, or `planned` lifecycle. |
| `available` | Whether the capability may legally be activated. |
| `deprecated` | Whether every activatable provider is deprecated. |
| `planned` | Whether the capability is declared for future work but unavailable. |
| `enabled` | Whether this project activates it. |
| `disabled` | Exact inverse of `enabled`. |
| `presentation` | Effective capability presentation, or `null` for legacy providers. |
| `providers` | Definitions contributed by selected packs. |

Provider rows appear in selected-pack dependency order and contain `pack_id`, `lifecycle`, `label`,
`description`, and `presentation`. Compatibility labels and descriptions may be `null` when a
legacy pack used shorthand. Schema-5 providers always include presentation. Multiple schema-5
providers must have equivalent presentation, so the effective row uses that shared value.

Lifecycle resolution is deterministic:

1. Any `available` provider makes the effective lifecycle `available`.
2. Otherwise, any `deprecated` provider makes it `deprecated`.
3. Otherwise, all providers are `planned` and the effective lifecycle is `planned`.

`available` is true for effective lifecycle `available` or `deprecated`. `deprecated` and `planned`
are true only for their matching effective lifecycle and are otherwise false. A `planned` capability
is unavailable, disabled, and cannot appear in the project's enabled list. An available or
deprecated capability omitted from activation is available but disabled. A deprecated enabled
capability is valid but produces a warning diagnostic. Capabilities from unselected packs do not
appear as rows; they are undeclared, unavailable, and disabled for this composition.

The export does not merge provider labels or descriptions into one synthetic definition. Consumers
may choose a display definition, but must retain provider identity and must not infer that two
providers are interchangeable.

## Controlled Values

`controlled_value_namespaces` contains rows ordered by namespace ID. Each row contains `id` and a
`values` array. Value rows are ordered by stable value ID and contain:

| Field | Meaning |
| --- | --- |
| `id` | Stable controlled value ID. |
| `label` | Human-facing label or `null`. |
| `description` | Human-facing description or `null`. |
| `broader_value_id` | Direct broader value in the same namespace or `null`. |
| `owner_pack_id` | The one selected pack that owns the value. |

The effective schema preserves direct broader-value relationships and never emits a delimiter-built
hierarchy or silently computed transitive closure. Duplicate ownership, unknown broader values, and
hierarchy cycles are fatal composition errors rather than diagnostics on a successful schema.

Typed semantic declarations remain runtime contract data rather than generic controlled values.
They may receive a dedicated effective-schema section in a later contract version when an editor or
consumer requirement is defined; version 2 must not flatten them into synthetic namespaces.

## Content Configuration

`content` has `roots`, `content_types`, and `categories` arrays.

Content roots retain manifest order and contain `id`, `relative_path`, `provenance_mode`, and
`provenance_label`. Their `relative_path` uses repository-relative forward slashes.

Content-type rows are ordered by stable ID and contain the normalized fields already owned by the
taxonomy registry:

- `id`, `lifecycle`, `label`, `plural_label`, and `canonical_pages_enabled`;
- `content_root_id`, `category_policy`, `path_strategy`, `metadata_type_mode`, and `slug_mode`;
- `default_template`, `qa_page_enabled`, and `graph_enabled`;
- `metadata_type`, `record_slug_prefix`, `record_slug_pattern`, and `record_path`.

`default_template` and `record_path` are repository-relative forward-slash strings or `null`.
Optional textual values use the registry's normalized empty string where empty and null have
different existing semantics.

Category rows are ordered by stable ID and contain:

- `id`, `lifecycle`, `label`, `plural_label`, and `canonical_pages_enabled`;
- `metadata_type`, `subject_slug_prefix`, `subject_slug_pattern`, and `graph_class`;
- `placements` ordered by `content_type_id`.

Each placement contains `content_type_id`, `relative_folder`, and `template`. `relative_folder` is
relative to the referenced content type's content root; `template` is repository-relative. Both use
forward slashes. Content-type eligibility remains authoritative: category graph class does not make
a record graphable when its content type disables graph projection, and a category placement does
not override QA-page eligibility.

## Resource Integration

`resources` has `roots`, `kinds`, and `types` arrays.

Resource roots retain manifest order and contain `id`, `relative_path`, and `required`. Resource-kind
rows are ordered by stable ID and contain `id`, `label`, and `plural_label`. Resource-type rows are
ordered by stable ID and contain:

- `id`, `lifecycle`, `label`, `plural_label`, and `kind_id`;
- `authority` and `editor_enabled`;
- `placements` in registry order.

Each resource placement contains `root_id`, `relative_path`, `tracking`, and `required`.
`relative_path` is relative to the referenced resource root and uses forward slashes. The effective
schema describes configured placement and policy; it does not inventory every concrete file beneath
a resource root.

## Diagnostics

`diagnostics` contains explainable non-fatal findings produced while composing a valid schema. Each
row contains:

| Field | Meaning |
| --- | --- |
| `severity` | `warning` or `info` in a successful schema; the shared diagnostic type also permits `error` for a failed composition result. |
| `code` | Stable machine-readable diagnostic code. |
| `message` | Human-readable explanation. |
| `path` | Stable configuration field path or `null`. |
| `related_ids` | Sorted stable IDs relevant to the finding. |

Diagnostics are ordered by severity (`warning` before `info`), then code, path with null first,
message, and related IDs using ordinal comparison.

Fatal malformed input, missing dependencies, dependency cycles or ordering failures, conflicting
ownership, unknown references, and invalid activation do not produce a partial
`EffectiveProjectSchema`. The service and command surface give callers a machine-readable failure
result using the same diagnostic row shape with severity `error`, while preserving existing
fail-closed loaders. That failure result contains no schema and is not an effective-schema document.

The initial diagnostic code catalog includes:

- `deprecated-capability-enabled`;
- `deferred-pack-selected`;
- `multiple-capability-providers`;
- `deferred-content-type`;
- `deferred-category`;
- `deferred-resource-type`.

The failure catalog provides stable codes for malformed input, missing or incompatible dependencies,
dependency ordering, provider or ownership conflicts, invalid activation, and unknown references.
Human-readable exception text is not itself a stable diagnostic code.

Implementations may add diagnostics only with stable codes, deterministic ordering, and matching
Python/PowerShell behavior. Diagnostics never mutate or complete canonical configuration.

## Deterministic JSON Serialization

Canonical effective-schema JSON uses:

- UTF-8 without a byte-order mark;
- two-space indentation;
- LF line endings and one final newline for file output;
- the property order defined by this contract and its row definitions;
- JSON `true`, `false`, and `null` literals;
- no ASCII escaping of ordinary Unicode display text;
- ordinal ordering by stable machine ID unless a section explicitly preserves validated input order;
- portable forward-slash paths relative to the repository, content root, or resource root defined
  for each field;
- no absolute paths, generation timestamps, host state, or filesystem discovery results.

Object property order is part of canonical file serialization for parity snapshots even though JSON
object semantics are unordered. In-memory consumers must address fields by name. Human-readable
output may present the same data differently, but JSON output and exported files must use the
canonical shape.

Running composition twice against identical canonical inputs must produce byte-identical JSON.
Python, PowerShell 7, and Windows PowerShell 5.1 must produce semantically identical documents; the
permanent compatibility check additionally compares canonical export bytes across all three
runtimes.

## Compatibility And Evolution

`contract_version` versions this generated shape independently from every input registry. A change
that removes or renames a field, changes field meaning, changes lifecycle resolution, changes
required ordering, or changes null/empty behavior requires a contract-version increment and a
documented compatibility decision.

Additive fields also require a contract-version increment until a future negotiated extension
mechanism exists. Consumers must reject an unsupported newer contract version rather than guessing.
They may accept an older supported version through an explicit adapter.

The service implementation may evolve without changing the contract version when canonical output
and semantics remain identical. Generated snapshots may be used for tests and diagnostics, but they
must not become an alternate source of truth or an input required to load the project.

## Runtime And Command API

Python library consumers import `EffectiveProjectSchema`, `compose_effective_project_schema`,
`load_effective_project_schema`, `compose_effective_schema_selection`, `effective_schema_json`, or
`effective_schema_failure` from `knowledge_framework.effective_schema`. PowerShell library consumers import
`KnowledgeFramework.psd1` and call `New-KnowledgeEffectiveProjectSchema`,
`Get-KnowledgeEffectiveProjectSchema`, `New-KnowledgeEffectiveSchemaSelection`, or
`New-KnowledgeEffectiveSchemaFailure`.

The paired headless commands are:

```powershell
python Tools\Commands\Framework\inspect_effective_schema.py [--root PATH] [--json] [--output PATH] [--report-output PATH] [--show SECTION] [--pack PACK_ID] [--capability CAPABILITY_ID]
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\Commands\Framework\Get-EffectiveProjectSchema.ps1 [-Root PATH] [-Json] [-Output PATH] [-ReportOutput PATH] [-Show SECTION[,SECTION]] [-Pack PACK_ID] [-Capability CAPABILITY_ID]
```

Without structured-output switches, each command prints a concise project, pack, capability,
content, resource, and diagnostic summary. `--json` / `-Json` writes the canonical document to
standard output. `--output` / `-Output` additionally writes canonical UTF-8 JSON beneath the
resolved project root and refuses an escaping path. Failure exits nonzero; structured mode emits an
`effective-project-schema-result` envelope containing `schema: null` and one stable error diagnostic.

`--report-output` / `-ReportOutput` writes the selected human report beneath the resolved project
root as UTF-8 without a byte-order mark, with LF line endings and one final newline. In human mode,
the command then prints only export confirmations instead of duplicating the report on standard
output. It may be combined with the JSON switches when both compiled artifacts are needed.

Human mode accepts repeatable Python `--show` selections or one comma-separated PowerShell `-Show`
list for `overview`, `packs`, `capabilities`, `namespaces`, `content`, `resources`, `diagnostics`, or
`all`. `overview` emits only friendly pack/capability labels, stable IDs, and descriptions for the
project composition. `all` expands to the six detailed contract sections and deliberately excludes
the redundant overview.
Selections are deduplicated in requested order, and `all` expands in the documented canonical section
order. They append raw contract-backed detail to the compact summary; they do not add semantics or
reinterpret canonical JSON.

`--pack` / `-Pack` and `--capability` / `-Capability` are independently optional and may be
combined with each other or any `show` selection. Exact stable IDs win. Otherwise, the project
lookup-key service resolves the supplied value; zero matches fail as unknown and multiple matches
fail as ambiguous. Human mode appends detailed inspection blocks. Structured mode emits:

```json
{
  "contract": "effective-project-schema-selection",
  "contract_version": 1,
  "source_contract": "effective-project-schema",
  "source_contract_version": 2,
  "project_id": "example-project",
  "packs": [],
  "capabilities": []
}
```

Each selected collection contains zero or one complete row copied from the composed effective
schema. The envelope is a filtered view, not a second schema authority. Without selectors, JSON
and output files remain the complete canonical effective-schema document.

The permanent `effective-schema` conformance suite covers positive composition, pack and capability
presentation, classification, exact and normalized singular selection, unknown and ambiguous
selection, available-disabled, planned, deprecated, multiple-provider, dependency-failure,
malformed, deterministic, path-safety, and generated 400-capability scale behavior. The
compatibility orchestrator compares the complete document, export, selection, and failure envelopes
across Python, PowerShell 7, and Windows PowerShell 5.1.

## Consumer Rules

- Library consumers import the effective-schema service; they do not invoke its CLI as a subprocess.
- CLI, QA, Visualization, and interface consumers read the same composed object.
- QA and Visualization derive discovery and eligibility from direct effective-schema projections;
  no legacy discovery projection or shadow comparison remains in their runtime path.
- Consumers may filter the effective schema for presentation but must not reinterpret lifecycle,
  activation, ownership, eligibility, or path policy.
- A disabled capability is normally omitted from feature UI without warning; diagnostics explain
  deprecation or configuration concerns, not ordinary opt-in absence.
- No consumer may write canonical project state by editing or replaying the generated JSON.
