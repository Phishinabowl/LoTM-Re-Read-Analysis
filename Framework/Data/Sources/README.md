# Source Conformance Fixtures

This directory contains the vocabulary-neutral schema-18 source-registry corpus
shared by the Python and PowerShell conformance runners.

`base/registry.json` instantiates every source-registry family with synthetic
works, structures, continuities, adaptation and distribution records, evidence
coverage, applicability, authority, identifiers, aliases, and provenance
targets. `base/resources.json` and `base/source-files/` provide an independent
resource-binding boundary without relying on LoTM paths.

`expectations.json` owns exact accepted counts, service/query expectations,
structured malformed mutations, and the generated scale size. Runners copy the
base corpus into an operating-system temporary directory before mutation and
must leave no persistent output.
