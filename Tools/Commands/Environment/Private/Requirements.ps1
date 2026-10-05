function Read-ExactModuleRequirements {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Root)

    $pins = [ordered]@{}
    $active = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $rootPath = (Resolve-Path -LiteralPath $Root -ErrorAction Stop).ProviderPath.TrimEnd('\', '/')
    $visit = {
        param([string]$Candidate)
        $candidatePath = (Resolve-Path -LiteralPath $Candidate -ErrorAction Stop).ProviderPath
        $relative = [IO.Path]::GetRelativePath($rootPath, $candidatePath)
        if ([IO.Path]::IsPathRooted($relative) -or $relative -eq '..' -or $relative.StartsWith('../') -or
            $relative.StartsWith('..\')) {
            throw "Module requirement include escapes repository: $candidatePath"
        }
        $cursor = $candidatePath
        while ($cursor -and $cursor -ne $rootPath) {
            if ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Module requirement includes may not traverse links: $cursor"
            }
            $cursor = Split-Path -Parent $cursor
        }
        if (-not $active.Add($candidatePath)) {
            throw "Module requirement include cycle: $candidatePath"
        }
        $rows = @(Get-Content -LiteralPath $candidatePath | ForEach-Object { ($_ -split '#', 2)[0].Trim() } |
                Where-Object { $_ })
        if ($rows.Count -eq 0) {
            throw "Module requirements file is empty: $candidatePath"
        }
        foreach ($line in $rows) {
            if ($line.StartsWith('-r ')) {
                $include = $line.Substring(3).Trim()
                if ([IO.Path]::IsPathRooted($include)) {
                    throw "Absolute module requirement include: $include"
                }
                & $visit (Join-Path (Split-Path -Parent $candidatePath) $include)
                continue
            }
            if ($line -notmatch '^([A-Za-z][A-Za-z0-9_.-]*)\s+([0-9]+(?:\.[0-9]+){1,3})$') {
                throw "Unsupported module requirement grammar: $line"
            }
            $moduleName, $version = $Matches[1], $Matches[2]
            if ($pins.Contains($moduleName) -and $pins[$moduleName] -ne $version) {
                throw "Conflicting module requirements for $moduleName"
            }
            $pins[$moduleName] = $version
        }
        $null = $active.Remove($candidatePath)
    }
    & $visit $Path
    foreach ($name in $pins.Keys) {
        [pscustomobject]@{ Name = $name
            Version = $pins[$name]
        }
    }
}
