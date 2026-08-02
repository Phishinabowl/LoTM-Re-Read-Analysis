# Lookup-Key Normalization Contract

Semantic lookup keys must compare identically in every supported runtime. The project manifest selects one pinned Unicode data registry, and every loader that resolves human-facing names, aliases, or case-insensitive semantic values must consume that registry through the paired lookup-key helpers.

## Algorithm

The current algorithm ID is `trim-nfc-default-casefold-nfc`:

1. Remove only the configured leading and trailing code points. The bundled registry uses ASCII horizontal/vertical whitespace: U+0009 through U+000D and U+0020.
2. Apply canonical Unicode normalization form C using the pinned decomposition, combining-class, composition, and Hangul rules.
3. Apply full default Unicode case folding from the pinned table.
4. Apply the same pinned NFC operation again.
5. Compare and store resulting keys with ordinal semantics. PowerShell consumers must use `Test-KnowledgeLookupKeysEqual` or an ordinal dictionary; `-eq`, `-ceq`, and their negative forms are culture-aware and are not valid lookup-key comparers.

The bundled data file is generated from Unicode 16.0.0. Runtime Unicode libraries, locale-sensitive casing, and runtime-default case-insensitive dictionaries are not part of this contract.

Inputs must be strings containing only Unicode scalar values. Runtime coercion of numbers or other objects and unpaired UTF-16 surrogates are rejected before normalization.

## Scope

Use lookup keys for human-facing aliases and other explicitly case-insensitive semantic identifiers, including entity/source/work aliases, scoped segment and numbering aliases, content-group aliases, territory codes, platform aliases, manifestation/package aliases, and case-insensitive external identifier values.

Do not normalize canonical stable IDs, schema field names, filesystem paths, or language tags through this service. Those values retain their own exact, path-aware, or standards-specific validators. Lookup normalization is also not fuzzy matching: it does not remove accents, transliterate scripts, repair spelling, or infer identity.

## Evolution

Changing the algorithm, trim set, or Unicode version is a reviewed data migration. Update the manifest path or registry schema/version deliberately, run exhaustive Python/PowerShell parity tests, and review newly colliding keys before accepting the change.

Portable conformance cases live in `Framework/Data/lookup-key-regression-vectors.json` and `Framework/Data/Lookup-Key/`. Equivalent pairs must resolve to ordinally equal normalized keys, distinct pairs must remain ordinally unequal, exact-output vectors must produce the declared code points, and malformed registry/input cases must be rejected in every supported runtime. Run them with `Tools/test_lookup_key.py` or `Tools/Test-Lookup-Key.ps1`; their `--json` / `-Json` summaries must match across Python, PowerShell 7, and Windows PowerShell 5.1.
