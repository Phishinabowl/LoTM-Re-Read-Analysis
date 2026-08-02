param(
    [string[]]$Path = @(),
    [ValidateRange(80, 1000)]
    [int]$MaximumLineLength = 200,
    [switch]$Fix,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$settingsPath = Join-Path $PSScriptRoot 'powershell-format-settings.psd1'

function Get-PowerShellRepositoryRoot {
    $root = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace([string]$root)) {
        throw 'PowerShell formatting requires a Git worktree so tracked and nonignored source discovery is deterministic.'
    }
    return [System.IO.Path]::GetFullPath(([string]$root).Trim())
}

function Get-RepositoryPowerShellSourceFiles {
    param([string]$RepoRoot)

    $relativePaths = @(
        & git -C $RepoRoot ls-files --cached --others --exclude-standard -- '*.ps1' '*.psm1' '*.psd1'
    )
    if ($LASTEXITCODE -ne 0) {
        throw "Git failed while discovering PowerShell sources beneath '$RepoRoot'."
    }

    return @(
        $relativePaths |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            ForEach-Object { Get-Item -LiteralPath (Join-Path $RepoRoot $_) } |
            Sort-Object FullName -Unique
    )
}

function Get-PowerShellSourceFiles {
    param(
        [string]$RepoRoot,
        [string[]]$InputPath
    )

    if ($InputPath.Count -eq 0) {
        return @(Get-RepositoryPowerShellSourceFiles -RepoRoot $RepoRoot)
    }

    $files = foreach ($candidate in $InputPath) {
        $resolvedCandidate = if ([System.IO.Path]::IsPathRooted($candidate)) {
            $candidate
        }
        else {
            Join-Path $RepoRoot $candidate
        }
        if (-not (Test-Path -LiteralPath $resolvedCandidate)) {
            throw "PowerShell formatting path not found: $candidate"
        }

        $item = Get-Item -LiteralPath $resolvedCandidate
        if ($item.PSIsContainer) {
            Get-ChildItem -LiteralPath $item.FullName -Recurse -File |
                Where-Object Extension -in @('.ps1', '.psm1', '.psd1')
        }
        elseif ($item.Extension -in @('.ps1', '.psm1', '.psd1')) {
            $item
        }
        else {
            throw "PowerShell formatting only accepts .ps1, .psm1, .psd1, or directory paths: $candidate"
        }
    }

    return @($files | Sort-Object FullName -Unique)
}

function Get-ParsedPowerShell {
    param(
        [string]$Source,
        [string]$SourcePath
    )

    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseInput(
        $Source,
        $SourcePath,
        [ref]$tokens,
        [ref]$errors
    )
    if ($errors.Count -gt 0) {
        $details = $errors | ForEach-Object {
            '{0}:{1}: {2}' -f $_.Extent.StartLineNumber, $_.Extent.StartColumnNumber, $_.Message
        }
        throw "PowerShell parse failed for ${SourcePath}:`n$($details -join "`n")"
    }

    return [pscustomobject]@{
        Ast    = $ast
        Tokens = @($tokens)
    }
}

function Get-TokenFingerprint {
    param([object[]]$Tokens)

    $ignoredKinds = @('NewLine', 'LineContinuation', 'EndOfInput', 'Semi')
    return @(
        $Tokens |
            Where-Object { $_.Kind -notin $ignoredKinds } |
            ForEach-Object { '{0}:{1}' -f $_.Kind, $_.Text }
    )
}

function Get-LongLineIssues {
    param(
        [string]$Source,
        [int]$MaximumLength
    )

    $lineNumber = 0
    return @(
        foreach ($line in $Source -split "`r?`n") {
            $lineNumber++
            if ($line.Length -gt $MaximumLength) {
                [ordered]@{
                    line   = $lineNumber
                    length = $line.Length
                }
            }
        }
    )
}

function Remove-OptionalStatementSeparators {
    param(
        [string]$Source,
        [object]$Parsed
    )

    $newline = if ($Source.Contains("`r`n")) {
        "`r`n"
    }
    else {
        "`n"
    }
    $forHeaderRanges = @(
        $Parsed.Ast.FindAll(
            { param($node) $node -is [System.Management.Automation.Language.ForStatementAst] },
            $true
        ) | ForEach-Object {
            [pscustomobject]@{
                Start = $_.Extent.StartOffset
                End   = $_.Body.Extent.StartOffset
            }
        }
    )

    $requiredOffsets = [System.Collections.Generic.HashSet[int]]::new()
    $semicolons = @($Parsed.Tokens | Where-Object Kind -eq 'Semi')
    foreach ($token in $semicolons) {
        foreach ($range in $forHeaderRanges) {
            if (
                $token.Extent.StartOffset -ge $range.Start -and
                $token.Extent.EndOffset -le $range.End
            ) {
                [void]$requiredOffsets.Add($token.Extent.StartOffset)
                break
            }
        }
    }

    $builder = [System.Text.StringBuilder]::new($Source)
    foreach ($token in ($semicolons | Sort-Object { $_.Extent.StartOffset } -Descending)) {
        if ($requiredOffsets.Contains($token.Extent.StartOffset)) {
            continue
        }

        $start = $token.Extent.StartOffset
        $end = $token.Extent.EndOffset
        [void]$builder.Remove($start, $end - $start)
        if (
            $end -lt $Source.Length -and
            $Source[$end] -ne "`r" -and
            $Source[$end] -ne "`n"
        ) {
            [void]$builder.Insert($start, $newline)
        }
    }

    return [pscustomobject]@{
        Source                     = $builder.ToString()
        RequiredSemicolonCount     = $requiredOffsets.Count
        OriginalSemicolonCount     = $semicolons.Count
    }
}

function ConvertTo-ReadablePowerShell {
    param(
        [string]$Source,
        [string]$SourcePath
    )

    $normalizedSource = $Source.Replace("`r`n", "`n").Replace("`r", "`n").Replace("`n", "`r`n")
    $before = Get-ParsedPowerShell -Source $normalizedSource -SourcePath $SourcePath
    $expanded = Remove-OptionalStatementSeparators -Source $normalizedSource -Parsed $before
    $formatted = Invoke-Formatter `
        -ScriptDefinition $expanded.Source `
        -Settings $settingsPath `
        -ErrorAction Stop
    $after = Get-ParsedPowerShell -Source $formatted -SourcePath $SourcePath

    $beforeFingerprint = Get-TokenFingerprint -Tokens $before.Tokens
    $afterFingerprint = Get-TokenFingerprint -Tokens $after.Tokens
    if (($beforeFingerprint -join "`u{1f}") -cne ($afterFingerprint -join "`u{1f}")) {
        throw "Formatting changed non-whitespace tokens in $SourcePath."
    }

    $remainingSemicolons = @($after.Tokens | Where-Object Kind -eq 'Semi').Count
    if ($remainingSemicolons -ne $expanded.RequiredSemicolonCount) {
        throw (
            "Formatting retained $remainingSemicolons semicolons in $SourcePath; " +
            "expected $($expanded.RequiredSemicolonCount) required by for statements."
        )
    }

    return [pscustomobject]@{
        Source                    = $formatted
        OriginalSemicolonCount    = $expanded.OriginalSemicolonCount
        RequiredSemicolonCount    = $expanded.RequiredSemicolonCount
    }
}

if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) {
    throw (
        'PSScriptAnalyzer is required. Run Tools/Test-PowerShell.ps1 for dependency status, ' +
        'then install the missing requirement before formatting.'
    )
}
Import-Module PSScriptAnalyzer -ErrorAction Stop

$repoRoot = Get-PowerShellRepositoryRoot
$results = @()
foreach ($file in Get-PowerShellSourceFiles -RepoRoot $repoRoot -InputPath $Path) {
    $source = Get-Content -LiteralPath $file.FullName -Raw
    $converted = ConvertTo-ReadablePowerShell -Source $source -SourcePath $file.FullName
    $changed = $source -cne $converted.Source
    $longLines = @(Get-LongLineIssues -Source $converted.Source -MaximumLength $MaximumLineLength)

    if ($changed -and $Fix) {
        [System.IO.File]::WriteAllText(
            $file.FullName,
            $converted.Source,
            [System.Text.UTF8Encoding]::new($false)
        )
    }

    $results += [ordered]@{
        path                         = $file.FullName
        changed                      = $changed
        fixed                        = $changed -and $Fix
        original_semicolons          = $converted.OriginalSemicolonCount
        required_for_semicolons      = $converted.RequiredSemicolonCount
        long_lines                   = $longLines
    }
}

$changedCount = @($results | Where-Object changed).Count
$longLineCount = @($results | ForEach-Object long_lines).Count
$result = [ordered]@{
    ready         = ($changedCount -eq 0 -or $Fix) -and $longLineCount -eq 0
    mode          = if ($Fix) {
        'fix'
    }
    else {
        'check'
    }
    files_checked = $results.Count
    files_changed = $changedCount
    maximum_line_length = $MaximumLineLength
    long_lines     = $longLineCount
    files         = @($results)
}

if ($Json) {
    $result | ConvertTo-Json -Depth 5
}
else {
    foreach ($entry in $results) {
        $status = if ($entry.fixed) {
            'FORMATTED'
        }
        elseif ($entry.changed) {
            'NEEDS FORMAT'
        }
        else {
            'OK'
        }
        Write-Output ('{0}: {1}' -f $status, $entry.path)
        foreach ($longLine in $entry.long_lines) {
            Write-Output (
                '  LONG LINE: {0}:{1} has {2} characters; maximum is {3}.' -f
                $entry.path,
                $longLine.line,
                $longLine.length,
                $MaximumLineLength
            )
        }
    }
    Write-Output (
        'PowerShell formatting {0}: {1} files checked; {2} files changed; {3} long lines.' -f
        $result.mode,
        $result.files_checked,
        $result.files_changed,
        $result.long_lines
    )
}

if (-not $result.ready) {
    exit 1
}
