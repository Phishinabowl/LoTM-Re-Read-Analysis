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

Describe 'Captured formatter representation preserves physical policy' -Tag Integration {
    It 'accepts an LF Git blob while the physical check still requires CRLF' {
        $source = "`$value = 1`n"
        $formatted = (ConvertTo-ReadablePowerShell -Source $source -SourcePath 'blob.ps1').Source
        Get-PowerShellFormattingComparison -Source $source -FormattedSource $formatted -Representation GitBlob |
            Should -BeFalse
        Get-PowerShellFormattingComparison -Source $source -FormattedSource $formatted | Should -BeTrue
        Get-PowerShellFormattingComparison -Source $formatted -FormattedSource $formatted | Should -BeFalse
    }
    It 'retains whitespace and statement-separator failures in blob mode' {
        foreach ($source in @("`$value=1`n", "`$a = 1; `$b = 2`n")) {
            $formatted = (ConvertTo-ReadablePowerShell -Source $source -SourcePath 'bad-blob.ps1').Source
            Get-PowerShellFormattingComparison -Source $source -FormattedSource $formatted -Representation GitBlob |
                Should -BeTrue
        }
    }
    It 'preserves LF multiline literal text when comparing the computed representation' {
        $source = "`$text = @'`nfirst;literal`nsecond`n'@`n"
        $formatted = (ConvertTo-ReadablePowerShell -Source $source -SourcePath 'literal.ps1').Source
        Get-PowerShellFormattingComparison -Source $source -FormattedSource $formatted -Representation GitBlob |
            Should -BeFalse
        $source | Should -BeExactly "`$text = @'`nfirst;literal`nsecond`n'@`n"
    }
    It 'rejects nonnormalized blob input rather than silently discarding carriage returns' {
        { Get-PowerShellFormattingComparison -Source "`$a = 1`r`n" -FormattedSource "`$a = 1`r`n" `
                -Representation GitBlob } | Should -Throw '*LF-normalized*'
    }
}

Describe 'Formatter CLI representation and read-only contracts' -Tag Integration {
    BeforeAll {
        $fixtureRoot = Join-Path $TestDrive 'formatter-cli'
        $null = New-Item -ItemType Directory -Path (Join-Path $fixtureRoot 'Project_Config') -Force
        [IO.File]::WriteAllText((Join-Path $fixtureRoot 'Project_Config/project.yaml'), "schema_version: 1`n")
        $privateRoot = Join-Path $fixtureRoot 'Tools/Commands/Environment/Private'
        $null = New-Item -ItemType Directory -Path $privateRoot -Force
        Copy-Item (Join-Path $repoRoot 'Tools/Commands/Environment/Private/Requirements.ps1') $privateRoot
        foreach ($name in @('requirements-powershell.txt', 'requirements-powershell-dev.txt')) {
            Copy-Item (Join-Path $repoRoot $name) $fixtureRoot
        }
        & git -C $fixtureRoot init --quiet
        if ($LASTEXITCODE -ne 0) {
            throw 'Synthetic formatter Git initialization failed.'
        }
        $formatter = Join-Path $repoRoot 'Tools/Static/Format-PowerShell.ps1'
        $hostExecutable = [Environment]::ProcessPath
    }
    It 'checks <representation>/<case> without modifying the fixture' -ForEach @(
        @{ representation = 'GitBlob'
            case = 'canonical LF'
            source = "`$value = 1`n"
            expected = 0
            fix = $false
        }
        @{ representation = 'Worktree'
            case = 'canonical CRLF'
            source = "`$value = 1`r`n"
            expected = 0
            fix = $false
        }
        @{ representation = 'Worktree'
            case = 'wrong EOL'
            source = "`$value = 1`n"
            expected = 1
            fix = $false
        }
        @{ representation = 'GitBlob'
            case = 'bad spacing'
            source = "`$value=1`n"
            expected = 1
            fix = $false
        }
        @{ representation = 'GitBlob'
            case = 'parse error'
            source = 'function {'
            expected = 1
            fix = $false
        }
        @{ representation = 'GitBlob'
            case = 'forbidden fix'
            source = "`$value=1`n"
            expected = 1
            fix = $true
        }
    ) {
        $path = Join-Path $fixtureRoot 'sample.ps1'
        [IO.File]::WriteAllText($path, $source, [Text.UTF8Encoding]::new($false))
        $before = [Convert]::ToBase64String([IO.File]::ReadAllBytes($path))
        $arguments = @('-NoProfile', '-File', $formatter, '-Root', $fixtureRoot, '-Path', $path,
            '-SourceRepresentation', $representation, '-Json')
        if ($fix) {
            $arguments += '-Fix'
        }
        $output = & $hostExecutable @arguments 2>&1 | Out-String
        $LASTEXITCODE | Should -Be $expected
        [Convert]::ToBase64String([IO.File]::ReadAllBytes($path)) | Should -BeExactly $before
        if ($case -notin @('parse error', 'forbidden fix')) {
            $document = $output | ConvertFrom-Json
            $document.files_checked | Should -Be 1
            $document.ready | Should -Be ($expected -eq 0)
        }
        else {
            $output | Should -Match $(if ($fix) {
                    'read-only'
                }
                else {
                    'parse failed'
                })
        }
    }
}
