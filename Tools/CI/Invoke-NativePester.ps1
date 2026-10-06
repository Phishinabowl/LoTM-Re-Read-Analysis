param([string]$Request)
$ErrorActionPreference = 'Stop'
$requestData = Get-Content -LiteralPath $Request -Raw | ConvertFrom-Json
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
function Get-NativeFailurePhase {
    param([object]$ErrorRecord)
    foreach ($frame in [regex]::Matches([string]$ErrorRecord.ScriptStackTrace, '(?m)^at .*?, (.+?): line ([0-9]+)\s*$')) {
        $file = $frame.Groups[1].Value
        $line = [int]$frame.Groups[2].Value
        $relative = [IO.Path]::GetRelativePath((Join-Path $root 'Tools/Tests'), $file)
        if ($relative.StartsWith('..') -or -not (Test-Path -LiteralPath $file -PathType Leaf)) {
            continue
        }
        $tokens = $null
        $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile($file, [ref]$tokens, [ref]$errors)
        $hooks = @($ast.FindAll({ param($node)
                    $node -is [Management.Automation.Language.CommandAst] -and
                    $node.GetCommandName() -in @('AfterEach', 'AfterAll', 'BeforeEach', 'BeforeAll')
                }, $true))
        foreach ($hook in $hooks) {
            if ($line -ge $hook.Extent.StartLineNumber -and $line -le $hook.Extent.EndLineNumber) {
                if ($hook.GetCommandName() -in @('AfterEach', 'AfterAll')) {
                    return 'cleanup'
                }
                return 'prerequisite'
            }
        }
    }
    return 'assertion'
}
$configuration = & (Join-Path $root 'Tools/Tests/PowerShell/PesterConfiguration.ps1') -Path $requestData.paths
if ($requestData.filter) {
    $configuration.Filter.FullName = @($requestData.filter)
}
$configuration.TestResult.Enabled = $true
$configuration.TestResult.OutputFormat = 'JUnitXml'
$configuration.TestResult.OutputPath = $requestData.xml
$configuration.TestResult.OutputEncoding = 'UTF8'
$configuration.TestResult.TestSuiteName = $requestData.identity
$result = Invoke-Pester -Configuration $configuration
$selected = @($result.Tests | Where-Object ShouldRun)
$rows = @($selected | ForEach-Object {
        [ordered]@{
            id = [IO.Path]::GetRelativePath($root, $_.ScriptBlock.File).Replace('\', '/') + '::' + $_.ExpandedPath
            result = [string]$_.Result
            skipped = [bool]$_.Skipped
            duration = $_.Duration.TotalSeconds
            errors = @($_.ErrorRecord | ForEach-Object { $_ | Out-String })
            standard_output = @($_.StandardOutput | ForEach-Object { $_ | Out-String })
            error_phases = @($_.ErrorRecord | ForEach-Object { Get-NativeFailurePhase $_ })
        }
    })
$containerErrors = @($result.FailedContainers | ForEach-Object { $_.ErrorRecord | ForEach-Object { $_ | Out-String } })
$blockErrors = @($result.FailedBlocks | ForEach-Object { $_.ErrorRecord | ForEach-Object { $_ | Out-String } })
$blockPhases = @($result.FailedBlocks | ForEach-Object { $_.ErrorRecord | ForEach-Object { Get-NativeFailurePhase $_ } })
$phase = [ordered]@{
    framework = 'pester'
    collected = $selected.Count
    total_discovered = $result.TotalCount
    excluded = $result.TotalCount - $selected.Count
    failed_containers = $result.FailedContainersCount
    discovery_failed = @($result.FailedContainers | Where-Object { -not $_.Executed }).Count -gt 0
    container_errors = $containerErrors
    block_errors = $blockErrors
    cleanup_failed = ($blockPhases -contains 'cleanup') -or @($rows | Where-Object { $_.error_phases -contains 'cleanup' }).Count -gt 0
    prerequisite_failed = ($blockPhases -contains 'prerequisite') -or @($rows | Where-Object { $_.error_phases -contains 'prerequisite' }).Count -gt 0
    reports = $rows
    exit_code = if ($result.FailedCount -or $result.FailedContainersCount -or $result.FailedBlocksCount) {
        1
    }
    else {
        0
    }
}
$phase | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $requestData.phase -Encoding utf8
if ($phase.exit_code -ne 0) {
    $containerErrors | Write-Output
    $blockErrors | Write-Output
    $rows | Where-Object result -NE Passed | ForEach-Object { $_.errors | Write-Output }
}
exit $phase.exit_code
