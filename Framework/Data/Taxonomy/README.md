# Taxonomy Conformance Data

This directory owns the shared synthetic corpus for taxonomy configuration. Its neutral IDs test the framework grammar without declaring any LoTM category or content-type vocabulary permanent.

- `base/` provides active and deferred content types and categories across required, optional, and forbidden category policies and all supported path strategies.
- `expectations.json` defines exact positive assertions, structured malformed mutations, invalid lookup cases, and the common category scale used by both runtimes.

The paired runners copy `base/` into an isolated operating-system temporary directory, supply isolated content-root records, and apply each mutation to the copy. Repository fixtures are never modified, and temporary data is removed after every run.
