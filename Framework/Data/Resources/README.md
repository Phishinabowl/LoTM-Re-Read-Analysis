# Resource Conformance Fixtures

This directory contains the vocabulary-neutral corpus shared by the Python and
PowerShell resource-registry conformance runners.

- `base/registry.json` covers every lifecycle, authority, tracking, placement,
  editor, and reconciliation behavior supported by resource schema 1.
- `expectations.json` owns exact positive expectations, structured malformed
  mutations, invalid query counts, and the generated scale size.
- Files beneath `base/documents/` and `base/evidence/` make required-placement
  existence checks portable without depending on the LoTM repository layout.

The runners copy `base/` into an operating-system temporary directory before
mutation. They must not edit this corpus or leave generated output in the repo.
