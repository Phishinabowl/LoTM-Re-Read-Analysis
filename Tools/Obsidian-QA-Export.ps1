param(
  [string]$Root = ".",
  [string]$OutputDir = "Obsidian_Export",
  [switch]$IncludeStubs,
  [switch]$Clean,
  [switch]$Json
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$scriptPath = Join-Path $PSScriptRoot "obsidian_qa_export.py"

$arguments = @($scriptPath, "--root", $Root, "--output-dir", $OutputDir)
if ($IncludeStubs) {
  $arguments += "--include-stubs"
}
if ($Clean) {
  $arguments += "--clean"
}
if ($Json) {
  $arguments += "--json"
}

python @arguments
