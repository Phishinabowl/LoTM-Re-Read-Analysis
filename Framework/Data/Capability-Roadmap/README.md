# Capability Roadmap Conformance Data

This corpus validates the project-independent capability-roadmap registry.

- `catalog.json` is a minimal validated-catalog-shaped input with two planned capabilities and one
  available capability.
- `valid-roadmap.json` maps one planned capability to a delivery target and records an accepted
  deferral for the other.

The paired conformance suites derive malformed, boundary, ambiguity, and scale cases from these
neutral fixtures so Python and PowerShell exercise the same contract.
