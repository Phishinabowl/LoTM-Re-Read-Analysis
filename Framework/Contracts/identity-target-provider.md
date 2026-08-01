# Identity Target Provider Contract

## Purpose

Identity-target providers expose stable records that may participate in identity phases and reconciliation. This is narrower than provenance addressing: every identity target may carry provenance, but relationships, evidence locators, authority rules, and other provenance targets are not identities.

## Provider Rules

A provider exposes controlled subject types and exact stable-ID lookup. Unsupported subject types, missing IDs, and collisions between installed providers are errors. Human-facing labels and aliases do not replace typed stable IDs.

The entity provider exposes `entity` and `entity-incarnation` as phase owners and additionally exposes `identity-phase` as a reconciliation target. Identity phases cannot recursively own identity phases.

## Extension Boundary

Future domain registries may provide their own identity-bearing record types without importing narrative incarnation semantics. The reconciliation service consumes this narrow boundary rather than treating every provenance subject as redirectable. Repository mutation remains separate: identity resolution may describe a redirect or merge without silently rewriting files, folders, or references. Taxonomy, resource, and source registries expose parallel reconciliation-target providers for stable records that are not narrative identities.
