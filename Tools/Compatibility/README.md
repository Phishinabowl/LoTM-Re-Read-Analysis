# Compatibility

`run_compatibility.py` is the canonical cross-runtime project-compatibility orchestrator. `compatibility.json` is its durable check registry and profile inventory. The orchestrator may launch Python, PowerShell 7, and Windows PowerShell 5.1 because comparison is its explicit responsibility; domain commands must not use that exception to delegate their own behavior across runtimes.

Run the rapid local comparison:

```powershell
python Tools\Compatibility\run_compatibility.py --profile local
```

Use `--profile pull-request` for root and artifact-lifecycle guards, or `--profile full-release` to add representative rendering. `--list --json` exposes the registered inventory. Every run writes beneath a uniquely scoped ignored `.tmp/compatibility/` folder, protects canonical outputs by hash, and removes its output after success. Use `--keep-output` only when the generated comparison artifacts need inspection; failed runs retain their scoped output automatically.
