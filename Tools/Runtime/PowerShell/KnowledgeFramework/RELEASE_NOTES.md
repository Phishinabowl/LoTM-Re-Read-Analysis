# KnowledgeFramework PowerShell Module Release Notes

## 0.14.0: Supported PS7 Host Boundary

CI Phase 2.2 implements the manifest/import/preflight boundary: minimum PowerShell 7.4, Core only.
Direct module and command startup reject unsupported hosts before root discovery or generation.
Conformance children inherit the verified current PS7 executable. CI Phases 2.3-2.6 migrate QA children, compatibility,
extraction and hosted checks and prove retained behavior before complete retirement closure.

All exports, independent PowerShell behavior, CLI paths, configuration schemas, semantic fixtures,
root/visibility rules and generated project baselines are preserved. Unsupported hosts fail clearly;
no silent host switch or Python delegation is introduced. Host regressions use Pester exactly 6.2.0;
catalog/profile adoption remains future work. Windows media/assembly constraints remain separate from Core host support.

The environment probe retains its JSON fields and exit codes, adds host_supported,
minimum_powershell_version and per-module usable diagnostics, and reports ready only when the host
is supported and the requirements file and declared modules are usable. Discovery is followed by
actual module import. Missing requirement files and failed imports return failure rather than readiness.
On unsupported hosts, requirements_path retains the supplied spelling and modules is empty; no
framework/project discovery or dependency import occurs. PSScriptAnalyzer 1.25.0 requires 7.4.6 even
though the runtime floor is 7.4; the probe reports this dependency failure correctly on 7.4.0.

The pre-1.0 module version 0.14.0 records this support break; it is not a framework model,
project-manifest or schema-pack version bump. Prior dated 5.1 results remain historical evidence.
The source repository's CI retirement inventory owns version/report decisions and complete migration
gates. That CI planning document is not
part of a portable extraction bundle; this release note's host/version statements stand alone.
