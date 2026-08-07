# Compatibility

`run_compatibility.py` is the canonical cross-runtime project-compatibility orchestrator.
`compatibility.json` is its durable check registry and profile inventory. The orchestrator may launch
Python, PowerShell 7, and Windows PowerShell 5.1 because comparison is its explicit responsibility;
domain commands must not use that exception to delegate their own behavior across runtimes.

Run the rapid local comparison:

```powershell
python Tools\Compatibility\run_compatibility.py --profile local
```

Every profile first compares the generated `EffectiveProjectSchema`, its byte-identical canonical
export, combined and deduplicated human inspection, invalid selectors, and its malformed-input
failure envelope across Python, PowerShell 7, and Windows PowerShell 5.1. Use
`--profile pull-request` for root and artifact-lifecycle guards, or `--profile full-release` to add
representative rendering. `--list --json` exposes the registered inventory. Every run writes beneath
a uniquely scoped ignored `.tmp/compatibility/` folder, protects canonical outputs by hash, and
removes its output after success. Use `--keep-output` only when the generated comparison artifacts
need inspection; failed runs retain their scoped output automatically.

Visualization and QA also compare their normalized semantic summaries, complete expected file
inventories, per-file SHA-256 hashes, and aggregate tree hashes with the reviewed project oracle in
`Baselines/lotm-consumers.json`. Cross-runtime agreement is therefore necessary but insufficient:
an identical regression in all three runtimes still fails. Normalization removes only generated
timestamps, redirected `.tmp` roots, accepted newline differences, and JSON property formatting.

The baseline is LoTM project compatibility data, not a portable framework fixture. Update it only
when a reviewed content, graph, QA, preset, or representative-boundary change intentionally alters
the accepted output. Diagnose the reported missing, unexpected, and changed paths first; never
refresh hashes merely to make a failing check green.

QA and Visualization use their effective-schema projections directly for discovery and record
eligibility while retaining legacy Markdown/YAML interpretation and output generation. The
compatibility profiles prove that the completed authority handoff preserves every accepted consumer
artifact and that canonical destinations remain untouched during redirected checks.
