# Compatibility

This folder is reserved for the canonical cross-runtime compatibility comparator and its stable comparison inventory. Phase 5 will add the implementation after the runtime, command, and conformance boundaries are fully validated.

Compatibility tooling may orchestrate Python, PowerShell 7, and Windows PowerShell 5.1 because cross-runtime comparison is its explicit responsibility. Domain commands must not use that exception to delegate their own behavior across runtimes.
