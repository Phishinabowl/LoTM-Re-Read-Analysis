# Compatibility

**CI Phase 2.1 support policy:** Python/PS7 are the retained implementations. The current schema-2
registry/validator, synthetic reporting registry and extraction verifier still require 5.1 until
CI 2.4 migrates them together. The supported comparison obligations below are the adopted policy,
not a claim that current commands already run without Desktop. See the [retirement inventory](../ci-powershell-retirement-inventory.md).

`run_compatibility.py` is the canonical cross-runtime project-compatibility orchestrator.
`compatibility.json` is its durable check registry and profile inventory. The orchestrator may launch
Python and PowerShell 7 because comparison is its explicit responsibility;
domain commands must not use that exception to delegate their own behavior across runtimes.

Run the rapid local comparison:

```powershell
python Tools\Compatibility\run_compatibility.py --profile local --summary-json
```

Every profile first validates compatibility and conformance reporting, then compares the generated
project-independent `FrameworkCatalog` and project-scoped `EffectiveProjectSchema`. Both checks
cover byte-identical canonical and selection exports, combined and deduplicated human inspection,
invalid selectors, malformed-input failure envelopes, and confined output across Python and PowerShell 7. Use
`--profile pull-request` for root and artifact-lifecycle guards, `--profile distribution-boundary`
for no-provider consumers, external commercial-metadata isolation, and extraction, or
`--profile full-release` to include that boundary plus representative rendering. `--list --json`
exposes the registered inventory. Use `--summary-json` for
routine status, `--json` for the complete nested result, and `--report-output PATH` to write that
complete result while retaining concise or human standard output. Every run writes beneath
a uniquely scoped ignored `.tmp/compatibility/` folder, protects canonical outputs by hash, and
removes its output after success. Use `--keep-output` only when the generated comparison artifacts
need inspection; failed runs retain their scoped output and detailed report automatically.

Visualization and QA also compare their normalized semantic summaries, complete expected file
inventories, per-file SHA-256 hashes, and aggregate tree hashes with the reviewed project oracle in
`Baselines/lotm-consumers.json`. Cross-runtime agreement is therefore necessary but insufficient:
an identical regression in both supported runtimes still fails. Normalization removes only generated
timestamps, redirected `.tmp` roots, accepted newline differences, and JSON property formatting.

The baseline is LoTM project compatibility data, not a portable framework fixture. Update it only
when a reviewed content, graph, QA, preset, or representative-boundary change intentionally alters
the accepted output. Diagnose the reported missing, unexpected, and changed paths first; never
refresh hashes merely to make a failing check green.

QA and Visualization use their effective-schema projections directly for discovery and record
eligibility while retaining legacy Markdown/YAML interpretation and output generation. The
compatibility profiles prove that the completed authority handoff preserves every accepted consumer
artifact and that canonical destinations remain untouched during redirected checks.
