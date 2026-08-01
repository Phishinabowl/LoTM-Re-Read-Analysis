# Strict Configuration Ingestion Contract

Framework registry YAML is executable configuration, not permissive page metadata. `Tools/strict_yaml.py` and `Tools/Strict-Yaml.ps1` provide the shared ingestion boundary used by the project manifest, schema-pack, taxonomy, resource, source, entity, reconciliation, and provenance loaders.

Both runtimes enforce the same baseline rules before registry-specific validation:

- duplicate mapping keys are errors at every nesting level;
- the root value must be a mapping;
- `schema_version` must be an unquoted integer of the exact supported version, not a Boolean, string, or decimal that a runtime can coerce;
- registry-defined closed shapes reject unknown keys with their configuration path;
- stable machine IDs and enum values remain case-sensitive;
- explicit audit timestamps use uppercase RFC 3339 `T` and `Z`, real calendar/time values, and offsets no larger than `+14:00` or `-14:00`.

The portable scalar subset is intentionally narrower than YAML 1.1. Booleans are lowercase `true` or `false`; null is lowercase `null` or `~`; integers are canonical decimal values without a leading plus, base prefix, or leading zero; and finite decimals use ordinary fixed-point notation. Legacy Boolean words such as `on`, `off`, `yes`, and `no` remain strings. Explicit tags, anchors, aliases, merge keys, document markers, and unquoted date/timestamp-like scalars are forbidden. Quote date and timestamp values so registry validation, rather than a runtime-specific YAML resolver, owns their interpretation.

Every registry file is also subject to the same hard ingestion budgets in both runtimes: 16 MiB of UTF-8 YAML, 128 nested collections, 500,000 parsed nodes, and 4 MiB for one scalar. These are framework safety limits, not project tuning knobs. A registry that legitimately outgrows one requires a reviewed contract migration and paired-runtime tests rather than a local parser exception.

Registry loaders own their allowed-key sets and semantic validation. Project manifest, schema-pack, taxonomy, resource, source, entity, reconciliation, and provenance mappings are closed at their defined record boundaries. The shared helper owns syntax-sensitive behavior that PyYAML and powershell-yaml would otherwise interpret differently. A schema version or record shape change requires paired Python and PowerShell updates, portable malformed fixtures, and a documented schema migration.

This contract currently covers framework registries only. YAML embedded in human-facing glossary pages is still consumed by transitional page and QA tooling and is not silently promoted to this strict registry contract. The normalized content-index migration must define and test that boundary separately.
