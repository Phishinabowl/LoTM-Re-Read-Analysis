BeforeAll {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
    . (Join-Path $PSScriptRoot 'Support/Get-ToolFunctionBlock.ps1')
    . (Get-ToolFunctionBlock -Path (Join-Path $repoRoot 'Tools/Static/Format-PowerShell.ps1'))
    $settingsPath = Join-Path $repoRoot 'Tools/Static/powershell-format-settings.psd1'
    $priorAnalyzerModules = @(Get-Module PSScriptAnalyzer)
    Import-Module PSScriptAnalyzer -RequiredVersion 1.25.0 -ErrorAction Stop
}

AfterAll {
    Remove-Module PSScriptAnalyzer -Force -ErrorAction SilentlyContinue
    foreach ($module in $priorAnalyzerModules) {
        Import-Module $module.Path -Force
    }
}

Describe 'Formatter discovery contracts with synthetic files and mocked Git' -Tag Unit {
    BeforeEach { $priorExitCode = $global:LASTEXITCODE }
    AfterEach { $global:LASTEXITCODE = $priorExitCode }
    It 'sorts and deduplicates tracked/nonignored inventory and omits deleted entries' {
        foreach ($name in @('b.ps1', 'a.psm1')) {
            Set-Content (Join-Path $TestDrive $name) '# fixture source'
        }
        Mock git { $global:LASTEXITCODE = 0
            @('b.ps1', 'a.psm1', 'b.ps1', 'deleted.ps1') }
        $files = @(Get-RepositoryPowerShellSourceFiles -RepoRoot $TestDrive)
        $files.Name | Should -Be @('a.psm1', 'b.ps1')
        Should -Invoke git -Times 1 -Exactly
    }
    It 'rejects failed Git discovery rather than reporting no sources' {
        Mock git { $global:LASTEXITCODE = 128 }
        { Get-RepositoryPowerShellSourceFiles -RepoRoot $TestDrive } | Should -Throw '*Git failed*'
    }
    It 'accepts explicit native sources and rejects unsupported or missing paths' {
        $explicitRoot = Join-Path $TestDrive 'explicit-sources'
        $null = New-Item -ItemType Directory -Path $explicitRoot
        foreach ($name in @('a.ps1', 'b.psm1', 'c.psd1', 'note.txt')) {
            Set-Content (Join-Path $explicitRoot $name) '# fixture'
        }
        $files = @(Get-PowerShellSourceFiles -RepoRoot $explicitRoot -InputPath @($explicitRoot, 'a.ps1'))
        $files.Name | Should -Be @('a.ps1', 'b.psm1', 'c.psd1')
        { Get-PowerShellSourceFiles -RepoRoot $explicitRoot -InputPath @('note.txt') } | Should -Throw '*only accepts*'
        { Get-PowerShellSourceFiles -RepoRoot $explicitRoot -InputPath @('missing.ps1') } | Should -Throw '*not found*'
    }
}

Describe 'Formatter token preservation with real exact-version analyzer' -Tag Integration {
    It 'preserves for separators, comments and string semicolons and is idempotent' {
        $source = '$text = "keep;literal"; for($i=0;$i -lt 2;$i++){ $text += ";" }; # fixture comment'
        $result = ConvertTo-ReadablePowerShell -Source $source -SourcePath 'synthetic.ps1'
        $result.RequiredSemicolonCount | Should -Be 2
        $result.Source | Should -Match 'keep;literal'
        $result.Source | Should -Match '# fixture comment'
        (ConvertTo-ReadablePowerShell -Source $result.Source -SourcePath 'synthetic.ps1').Source | Should -BeExactly $result.Source
    }
    It 'rejects parsing failures with an actionable source location' {
        { Get-ParsedPowerShell -Source 'function {' -SourcePath 'broken.ps1' } | Should -Throw '*parse failed for broken.ps1*'
    }
    It 'rejects analyzer output that changes meaningful tokens' {
        Mock Invoke-Formatter { '$value = 2' }
        { ConvertTo-ReadablePowerShell -Source '$value = 1' -SourcePath 'changed.ps1' } | Should -Throw '*changed non-whitespace tokens*'
    }
    It 'returns exact long-line positions without rewriting content' {
        $source = "short`n$('x' * 81)`nend"
        $issues = @(Get-LongLineIssues -Source $source -MaximumLength 80)
        $issues.Count | Should -Be 1
        $issues[0].line | Should -Be 2
        $issues[0].length | Should -Be 81
    }
}
