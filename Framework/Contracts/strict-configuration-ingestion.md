# Strict Configuration Ingestion Contract

Framework registry YAML is executable configuration, not permissive page metadata. `Tools/strict_yaml.py` and `Tools/Strict-Yaml.ps1` provide the shared ingestion boundary used by the project manifest, schema-pack, taxonomy, resource, source, entity, reconciliation, and provenance loaders.

Both runtimes enforce the same baseline rules before registry-specific validation:

- duplicate mapping keys are errors at every nesting level;
- the root value must be a mapping;
- `schema_version` must be an unquoted integer of the exact supported version, not a Boolean, string, or decimal that a runtime can coerce;
- registry-defined closed shapes reject unknown keys with their configuration path;
- stable machine IDs and enum values remain case-sensitive;
- explicit audit timestamps use uppercase RFC 3339 `T` and `Z`, real calendar/time values, and offsets no larger than `+14:00` or `-14:00`.

Registry loaders own their allowed-key sets and semantic validation. The shared helper owns syntax-sensitive behavior that PyYAML and powershell-yaml would otherwise interpret differently. A schema version or record shape change requires paired Python and PowerShell updates, portable malformed fixtures, and a documented schema migration.

This contract currently covers framework registries only. YAML embedded in human-facing glossary pages is still consumed by transitional page and QA tooling and is not silently promoted to this strict registry contract. The normalized content-index migration must define and test that boundary separately.
