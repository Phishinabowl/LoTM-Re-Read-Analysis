# KnowledgeFramework PowerShell Module Release Notes

## Planned 0.14.0: Supported PS7 Host Boundary

**Not implemented by CI Phase 2.1.** Current manifest remains 0.13.0, minimum 5.1, Desktop/Core.
The reviewed retirement adopts PowerShell 7.4+ Core as the supported host contract. CI Phase 2.2
will change the manifest/import/preflight boundary; 2.3-2.6 migrate child launches, compatibility,
extraction and hosted checks and prove retained behavior before complete retirement closure.

All exports, independent PowerShell behavior, CLI paths, configuration schemas, semantic fixtures,
root/visibility rules and generated project baselines are preserved. Unsupported hosts fail clearly;
no silent host switch or Python delegation is introduced. Pester remains exactly 6.2.0 for future
implementation tests. Windows media/assembly constraints remain separate from Core host support.

The accepted planned pre-1.0 module version 0.14.0 records this support break; it is not a framework model,
project-manifest or schema-pack version bump. Prior dated 5.1 results remain historical evidence.
The source repository's CI retirement inventory owns version/report decisions and complete migration
gates. That CI planning document is not
part of a portable extraction bundle; this release note's host/version statements stand alone.
