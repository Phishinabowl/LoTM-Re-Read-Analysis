BeforeAll {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
}

Describe 'Approved Pester file-container execution boundaries' -Tag Integration {
    It 'continues later containers after discovery, setup, assertion and cleanup failures with independent script scope' {
        $root = Join-Path $TestDrive 'synthetic-native'
        $ci = Join-Path $root 'Tools/CI'
        $tests = Join-Path $root 'Tools/Tests/PowerShell'
        $null = New-Item -ItemType Directory -Path $ci, $tests -Force
        Copy-Item -LiteralPath (Join-Path $repoRoot 'Tools/CI/Invoke-NativePester.ps1') -Destination $ci
        Copy-Item -LiteralPath (Join-Path $repoRoot 'Tools/Tests/PowerShell/PesterConfiguration.ps1') -Destination $tests
        $sources = [ordered]@{
            '00-Discovery.Tests.ps1' = "Describe 'discovery' { throw 'intentional discovery failure' }"
            '01-Setup.Tests.ps1' = "Describe 'setup' { BeforeAll { throw 'intentional setup failure' }; It 'selected' { 1 | Should -Be 1 } }"
            '02-Assertion.Tests.ps1' = "Describe 'assertion' { It 'selected' { 1 | Should -Be 2 } }"
            '03-Cleanup.Tests.ps1' = "Describe 'cleanup' { AfterAll { throw 'intentional cleanup failure' }; It 'selected' { 1 | Should -Be 1 } }"
            '04-Scope.Tests.ps1' = "BeforeAll { `$script:ContainerState = 'private' }; Describe 'scope' { It 'local' { `$script:ContainerState | Should -Be 'private' } }"
            '05-Later.Tests.ps1' = (
                "Describe 'later' { It 'still executes independently' { `$script:ContainerState | Should -BeNullOrEmpty; " +
                "[IO.File]::WriteAllText((Join-Path `$PSScriptRoot 'later-ran'), 'yes') } }"
            )
        }
        $paths = @($sources.Keys | ForEach-Object {
                $path = Join-Path $tests $_
                [IO.File]::WriteAllText($path, $sources[$_], [Text.UTF8Encoding]::new($false))
                $path
            })
        $request = Join-Path $root 'request.json'
        $phasePath = Join-Path $root 'phases.json'
        @{ paths = $paths
            xml = (Join-Path $root 'native.xml')
            phase = $phasePath
            identity = 'synthetic-boundaries'
        } |
            ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $request -Encoding utf8
        $start = [Diagnostics.ProcessStartInfo]::new()
        $start.FileName = [Environment]::ProcessPath
        $start.UseShellExecute = $false
        $start.CreateNoWindow = $true
        $start.RedirectStandardOutput = $true
        $start.RedirectStandardError = $true
        foreach ($argument in @('-NoProfile', '-File', (Join-Path $ci 'Invoke-NativePester.ps1'), '-Request', $request)) {
            $start.ArgumentList.Add($argument)
        }
        $child = [Diagnostics.Process]::Start($start)
        try {
            $stdout = $child.StandardOutput.ReadToEndAsync()
            $stderr = $child.StandardError.ReadToEndAsync()
            if (-not $child.WaitForExit(30000)) {
                $child.Kill($true)
                $child.WaitForExit()
                throw 'Synthetic Pester boundary execution exceeded its deadline.'
            }
            $output = $stdout.GetAwaiter().GetResult() + $stderr.GetAwaiter().GetResult()
            $child.ExitCode | Should -Be 1 -Because $output
            $phase = Get-Content -LiteralPath $phasePath -Raw | ConvertFrom-Json
            $phase.discovery_failed | Should -BeTrue
            $phase.prerequisite_failed | Should -BeTrue
            $phase.cleanup_failed | Should -BeTrue
            @($phase.reports | Where-Object { $_.result -eq 'Failed' }).Count | Should -BeGreaterThan 0
            (Get-Content -LiteralPath (Join-Path $tests 'later-ran') -Raw) | Should -BeExactly 'yes'
            @($phase.reports | Where-Object { $_.id.Contains('05-Later.Tests.ps1') -and $_.result -eq 'Passed' }).Count |
                Should -Be 1
        }
        finally {
            $child.Dispose()
        }
    }
}
