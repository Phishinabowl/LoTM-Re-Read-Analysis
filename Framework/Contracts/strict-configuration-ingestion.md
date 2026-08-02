# Strict Configuration Ingestion Contract

Framework registry YAML is executable configuration, not permissive page metadata. `Tools/strict_yaml.py` and `Tools/Strict-Yaml.ps1` provide the shared ingestion boundary used by the project manifest, schema-pack, taxonomy, resource, source, entity, reconciliation, and provenance loaders.

Both runtimes enforce the same baseline rules before registry-specific validation:

- files are strict UTF-8 without a byte-order mark; malformed byte sequences and BOM-prefixed files are errors;
- duplicate mapping keys are errors at every nesting level;
- mapping keys are non-empty scalar strings matching `^[a-z0-9]+(?:[_.-][a-z0-9]+)*$`; labels, localized text, URIs, and other human or external values belong in values rather than executable keys;
- the root value must be a mapping;
- `schema_version` must be an unquoted integer of the exact supported version, not a Boolean, string, or decimal that a runtime can coerce;
- registry-defined closed shapes reject unknown keys with their configuration path;
- stable machine IDs and enum values remain case-sensitive;
- explicit audit timestamps use uppercase RFC 3339 `T` plus uppercase `Z` or a numeric offset, real calendar/time values, no more than six fractional digits, offsets no larger than `+14:00` or `-14:00`, and a UTC-normalized value inside years `0001` through `9999`.

The portable scalar subset is intentionally narrower than YAML 1.1. Booleans are lowercase `true` or `false`; null must be written explicitly as lowercase `null`; and canonical decimal integers have no leading plus, base prefix, underscore, or leading zero. Canonical integers are the only unquoted numeric form. Quote decimal or exponent-shaped values as strings until the owning field contract defines a precise runtime-independent decimal representation and semantic parser. Legacy Boolean words such as `on`, `off`, `yes`, and `no` remain strings. Explicit tags, anchors, aliases, merge keys, document markers, implicit empty nulls, tilde nulls, and unquoted date/timestamp-like scalars are forbidden. Quote date and timestamp values so registry validation, rather than a runtime-specific YAML resolver, owns their interpretation.

Mapping-key validation occurs before runtime-native dictionaries are constructed. This prevents PowerShell's case-insensitive ordered mappings and Python's Boolean/integer key equivalence from silently producing different objects. Plain Boolean, null, and numeric keys are forbidden; quote a canonical key such as `"true"` or `"1"` when its intended identity is textual. Uppercase, case-colliding, complex, empty, Unicode, and punctuation-shaped mapping keys are noncanonical even when a YAML parser could represent them.

Every registry file is also subject to the same hard ingestion budgets in both runtimes: 16 MiB of raw UTF-8 YAML, 128 nested collections, 500,000 parsed nodes, and 4 MiB of UTF-8 bytes for one scalar. Byte budgets are independent of runtime-native string representation, so supplementary Unicode characters cost the same in Python and PowerShell. These are framework safety limits, not project tuning knobs. A registry that legitimately outgrows one requires a reviewed contract migration and paired-runtime tests rather than a local parser exception.

Registry loaders own their allowed-key sets and semantic validation. Project manifest, schema-pack, taxonomy, resource, source, entity, reconciliation, and provenance mappings are closed at their defined record boundaries. The shared helper owns syntax-sensitive behavior that PyYAML and powershell-yaml would otherwise interpret differently. A schema version or record shape change requires paired Python and PowerShell updates, portable malformed fixtures, and a documented schema migration.

Permanent portable conformance lives in `Framework/Data/Strict-Yaml/` and runs through `Tools/test_strict_yaml.py` or `Tools/Test-Strict-Yaml.ps1`. The paired runners verify exact scalar types, canonical mapping keys, forbidden syntax, UTF-8/BOM handling, all four ingestion budgets, and the shared RFC 3339 profile. Their `--json` / `-Json` summaries must match across Python, PowerShell 7, and Windows PowerShell 5.1.

This contract currently covers framework registries only. YAML embedded in human-facing glossary pages is still consumed by transitional page and QA tooling and is not silently promoted to this strict registry contract. The normalized content-index migration must define and test that boundary separately.
