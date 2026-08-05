# Provenance Conformance Data

This directory contains domain-neutral fixtures for the schema-version-3 provenance registry.

`base/registry.json` composes with the neutral taxonomy, source, entity, chronology, and occurrence fixtures. The conformance runners extend the source fixture in temporary space with two controlled evidence sources and claim-targeted applicability scopes; canonical fixture files remain unchanged.

`expectations.json` defines authority-decision vectors, invalid service queries, malformed registry mutations, and the scale case shared by Python, PowerShell 7, and Windows PowerShell 5.1.

Coverage includes assertion shape consistency, typed subject lookup including recurrence-cardinality, occurrence-participation, occurrence-track-entry, occurrence-branch-state-transition, state-scale, and subject-state-transition targets, nested field paths including epistemic completeness and capability values, evidence roles, point and range locators, source coverage, observation and effective timing, claim applicability, supersession integrity, authority outcomes, and deterministic scale behavior.
