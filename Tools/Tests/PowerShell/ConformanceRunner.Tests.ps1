BeforeAll {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
    . (Join-Path $PSScriptRoot 'Support/Get-ToolFunctionBlock.ps1')
    . (Get-ToolFunctionBlock -Path (Join-Path $repoRoot 'Tools/Conformance/Run-Conformance.ps1'))
    $registryRelativePath = 'Tools/Conformance/suites.json'
    $stableIdPattern = '^[a-z0-9]+(?:-[a-z0-9]+)*$'
    $failureExcerptLines = 20
    $failureExcerptBytes = 4096
    function Write-PilotRegistry {
        param([object]$Document)
        $Document | ConvertTo-Json -Depth 20 | Set-Content (Join-Path $TestDrive $registryRelativePath)
    }
}

Describe 'Existing conformance registry implementation with synthetic runners' -Tag Unit {
    BeforeEach {
        $directory = Join-Path $TestDrive 'Tools/Conformance/Suites'
        $null = New-Item -ItemType Directory -Path $directory -Force
        foreach ($id in @('alpha', 'beta')) {
            Set-Content (Join-Path $directory "test_$id.py") '# Synthetic runner; never executed.'
            Set-Content (Join-Path $directory "Test-$id.ps1") '# Synthetic runner; never executed.'
        }
        $document = [ordered]@{
            schema_version = 1
            profiles = @{ baseline = @('beta', 'alpha') }
            suites = @(
                @{ id = 'alpha'
                    python = 'Tools/Conformance/Suites/test_alpha.py'
                    powershell = 'Tools/Conformance/Suites/Test-alpha.ps1'
                    tags = @('pilot')
                },
                @{ id = 'beta'
                    python = 'Tools/Conformance/Suites/test_beta.py'
                    powershell = 'Tools/Conformance/Suites/Test-beta.ps1'
                    tags = @('pilot')
                }
            )
            discovery = @{
                python = @(@{ directory = 'Tools/Conformance/Suites'
                        pattern = 'test_*.py'
                        exclude = @()
                    })
                powershell = @(@{ directory = 'Tools/Conformance/Suites'
                        pattern = 'Test-*.ps1'
                        exclude = @()
                    })
            }
        }
        Write-PilotRegistry $document
    }
    It 'preserves profile and explicit selection order and rejects duplicate or unknown selection' {
        $registry = Get-ConformanceRegistry -RepoRoot $TestDrive
        (Get-SelectedSuites -Registry $registry -ProfileId baseline -SuiteIds @()).suites.id | Should -Be @('beta', 'alpha')
        (Get-SelectedSuites -Registry $registry -ProfileId ignored -SuiteIds @('alpha', 'beta')).suites.id | Should -Be @('alpha', 'beta')
        { Get-SelectedSuites -Registry $registry -ProfileId baseline -SuiteIds @('alpha', 'alpha') } | Should -Throw '*duplicate*'
        { Get-SelectedSuites -Registry $registry -ProfileId baseline -SuiteIds @('missing') } | Should -Throw '*Unknown*'
    }
    It 'rejects duplicate suite identity before invoking any runner' {
        $document.suites[1].id = 'alpha'
        Write-PilotRegistry $document
        { Get-ConformanceRegistry -RepoRoot $TestDrive } | Should -Throw '*duplicate conformance suite ID*'
    }
    It 'rejects unregistered discovery files and stale exclusions' {
        $extra = Join-Path $directory 'test_extra.py'
        Set-Content $extra '# Synthetic unregistered runner.'
        { Get-ConformanceRegistry -RepoRoot $TestDrive } | Should -Throw '*Unregistered python*'
        Remove-Item -LiteralPath $extra
        $document.discovery.python[0].exclude = @('Tools/Conformance/Suites/test_missing.py')
        Write-PilotRegistry $document
        { Get-ConformanceRegistry -RepoRoot $TestDrive } | Should -Throw '*Stale python*'
    }
}

Describe 'Existing conformance report implementation boundaries' -Tag Unit {
    It 'preserves counts and failed-case identity without hiding complete report provenance' {
        $results = @(
            [pscustomobject]@{ id = 'alpha'
                status = 'passed'
            },
            [pscustomobject]@{ id = 'beta'
                status = 'failed'
                error = "fixture failure`nsecond line"
            }
        )
        $summary = New-ConciseConformanceSummary -ProfileId pilot -Results $results -ElapsedSeconds 1.25 -ReportPath '.tmp/pilot/report.json'
        $summary.contract | Should -Be 'validation-run-summary'
        $summary.selected_count | Should -Be 2
        $summary.passed | Should -Be 1
        $summary.failed | Should -Be 1
        $summary.status | Should -Be 'failed'
        $summary.report_path | Should -Be '.tmp/pilot/report.json'
        $summary.failures[0].id | Should -Be 'beta'
        $summary.failures[0].classification | Should -Be 'suite-failure'
        $summary.failures[0].excerpt | Should -Be "fixture failure`nsecond line"
    }
    It 'bounds diagnostic excerpts on a valid UTF8 boundary and retains the truncation signal' {
        $text = ('é' * 3000)
        $bounded = Get-BoundedFailureExcerpt $text
        $bounded.truncated | Should -BeTrue
        [Text.Encoding]::UTF8.GetByteCount($bounded.excerpt) | Should -BeLessOrEqual 4096
        $bounded.excerpt | Should -Not -Match ([string][char]0xfffd)
        $lines = Get-BoundedFailureExcerpt ((1..25 | ForEach-Object { "line $_" }) -join "`n")
        $lines.truncated | Should -BeTrue
        @($lines.excerpt -split "`n").Count | Should -Be 20
    }
    It 'writes complete nested Unicode JSON without BOM and rejects directory or escaping destinations' {
        $path = Resolve-ConformanceReportOutput -RepoRoot $TestDrive -Value 'reports/result.json'
        $summary = @{ text = 'Unicode é'
            nested = @{ count = 2 }
        }
        Write-DetailedConformanceReport -Path $path -Summary $summary
        $bytes = [IO.File]::ReadAllBytes($path)
        ($bytes[0..2] -join ',') | Should -Not -Be '239,187,191'
        $actual = Get-Content $path -Raw | ConvertFrom-Json
        $actual.text | Should -BeExactly 'Unicode é'
        $actual.nested.count | Should -Be 2
        { Resolve-ConformanceReportOutput -RepoRoot $TestDrive -Value '../outside.json' } | Should -Throw '*beneath the project root*'
        { Resolve-ConformanceReportOutput -RepoRoot $TestDrive -Value 'reports' } | Should -Throw '*file path*'
    }
}

Describe 'Conformance child deadlines with synthetic scripts' -Tag Integration {
    BeforeAll {
        function Resolve-KnowledgePowerShellExecutable {
            [Environment]::ProcessPath
        }
    }
    It 'retains nonzero child diagnostics and permits a later independent suite' {
        $failed = Join-Path $TestDrive 'failed.ps1'
        $passed = Join-Path $TestDrive 'passed.ps1'
        Set-Content $failed "Write-Output 'complete synthetic diagnostic'; exit 1"
        Set-Content $passed 'Write-Output ''{"fixture":true}'''
        $first = Invoke-ConformanceSuite $TestDrive @{ id = 'failed'
            powershell_path = $failed
        } 5
        $second = Invoke-ConformanceSuite $TestDrive @{ id = 'passed'
            powershell_path = $passed
        } 5
        $first.status | Should -Be 'failed'
        $first.error | Should -Match 'complete synthetic diagnostic'
        $second.status | Should -Be 'passed'
        $second.summary.fixture | Should -BeTrue
    }
    It 'bounds a hung synthetic child and continues after it' {
        $hung = Join-Path $TestDrive 'hung.ps1'
        Set-Content $hung "Write-Output 'before timeout'; Start-Sleep -Seconds 20"
        $timer = [Diagnostics.Stopwatch]::StartNew()
        $result = Invoke-ConformanceSuite $TestDrive @{ id = 'hung'
            powershell_path = $hung
        } 1
        $result.status | Should -Be 'failed'
        $result.error | Should -Match 'Suite deadline exceeded'
        $result.error | Should -Match 'before timeout'
        $timer.Elapsed.TotalSeconds | Should -BeLessThan 5
    }
}
