# Narrow launch-contract regressions; shared consumer baselines own generated-content semantics.
BeforeAll {
    $repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $qaPath = Join-Path $repoRoot 'Tools\Commands\QA\Obsidian-QA-Export.ps1'
    $hostPolicy = Join-Path $repoRoot 'Tools\Runtime\PowerShell\KnowledgeFramework\Private\PowerShell-Host.ps1'
    . $hostPolicy
    $script:QaPowerShellExecutable = Resolve-KnowledgePowerShellExecutable
    $tokens = $null
    $errors = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseFile($qaPath, [ref]$tokens, [ref]$errors)
    if ($errors.Count -gt 0) {
        throw 'QA source did not parse.'
    }
    # QA is a command, so load only its existing launch functions without running canonical export.
    foreach ($name in @('Write-TextFile', 'Get-RepoRelativePath', 'Write-RepoRefreshCheck', 'Write-BoundedGraphs', 'Invoke-DisposableCacheCleanup')) {
        $definition = $ast.Find({ param($node)
                $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name
            }, $true)
        if ($null -eq $definition) {
            throw "QA launch function missing: $name"
        }
        . ([scriptblock]::Create($definition.Extent.Text))
    }
    $fixtureHelper = @'
param([string]$Root, [string]$Mode, [string]$SettingsPath, [switch]$SkipRender, [switch]$Delete)
$record = [ordered]@{
    pid = $PID
    version = [string]$PSVersionTable.PSVersion
    edition = $PSVersionTable.PSEdition
    executable = (Get-Process -Id $PID).Path
    cwd = (Get-Location).Path
    root = $Root
    mode = $Mode
    settings_path = $SettingsPath
    skip_render = [bool]$SkipRender
    delete = [bool]$Delete
}
$record | ConvertTo-Json -Compress | Add-Content -LiteralPath $env:LOTM_QA_CHILD_TEST_LOG -Encoding utf8
if ($env:LOTM_QA_CHILD_TEST_EXIT) { exit ([int]$env:LOTM_QA_CHILD_TEST_EXIT) }
Write-Output 'Fixture helper completed.'
'@
}

Describe 'QA child launch contracts' {
    BeforeEach {
        $fixtureRoot = Join-Path $TestDrive ('project with spaces ' + [guid]::NewGuid().ToString('N'))
        $generatedDir = Join-Path $fixtureRoot 'generated output'
        $null = New-Item -ItemType Directory -Path $generatedDir -Force
        $helper = Join-Path $fixtureRoot 'helper with spaces.ps1'
        Set-Content -LiteralPath $helper -Value $fixtureHelper
        $settingsPath = Join-Path $fixtureRoot 'source settings.json'
        [ordered]@{
            reportPath = 'original-report.md'
            snapshotPath = 'original-snapshot.json'
            views = @([ordered]@{ name = 'fixture'
                    input = 'original-view.mmd'
                    outputs = @('original-view.svg')
                })
        } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $settingsPath
        $config = [pscustomobject]@{
            root = $fixtureRoot
            visualization_render_settings = $settingsPath
            visualization_powershell_helper = $helper
            cleanup_powershell_helper = $helper
        }
        $logPath = Join-Path $fixtureRoot 'child log.jsonl'
        $priorLog = $env:LOTM_QA_CHILD_TEST_LOG
        $priorExit = $env:LOTM_QA_CHILD_TEST_EXIT
        $env:LOTM_QA_CHILD_TEST_LOG = $logPath
        $env:LOTM_QA_CHILD_TEST_EXIT = $null
        $callerDirectory = (Get-Location).Path
        $graphSpecs = @([pscustomobject]@{
                name = 'chapter-32'
                file_stem = 'chapter-32'
                medium = 'novel'
                max_volume = 1
                max_chapter = 32
                include_unknown_subjects = $false
                include_unknown_positions = $false
            })
    }

    AfterEach {
        $env:LOTM_QA_CHILD_TEST_LOG = $priorLog
        $env:LOTM_QA_CHILD_TEST_EXIT = $priorExit
    }

    It 'runs all three helpers in isolated approved PS7 children with unchanged cwd and arguments' {
        $null = Write-RepoRefreshCheck $config $generatedDir
        $null = Write-BoundedGraphs $config $generatedDir $graphSpecs
        $cleanupOutput = @(Invoke-DisposableCacheCleanup $config)
        $records = @(Get-Content -LiteralPath $logPath | ForEach-Object { $_ | ConvertFrom-Json })
        $records.Count | Should -Be 3
        @($records.pid | Sort-Object -Unique).Count | Should -Be 3
        foreach ($record in $records) {
            $record.edition | Should -Be 'Core'
            $record.version | Should -Be ([string]$PSVersionTable.PSVersion)
            $record.executable | Should -Be $script:QaPowerShellExecutable
            $record.pid | Should -Not -Be $PID
            $record.cwd | Should -Be $callerDirectory
        }
        foreach ($record in $records[0..1]) {
            $record.root | Should -Be $fixtureRoot
            $record.mode | Should -Be 'Refresh'
            $record.skip_render | Should -BeTrue
            $record.delete | Should -BeFalse
            Test-Path (Join-Path $fixtureRoot $record.settings_path) | Should -BeTrue
        }
        $records[2].delete | Should -BeTrue
        $records[2].root | Should -BeNullOrEmpty
        $cleanupOutput.Count | Should -Be 0
        $settings = Get-Content -LiteralPath (Join-Path $fixtureRoot $records[1].settings_path) -Raw | ConvertFrom-Json
        $settings.views[0].readerBoundary.maxChapter | Should -Be 32
        $settings.views[0].readerBoundary.includeUnknownSubjects | Should -BeFalse
        (Get-Location).Path | Should -Be $callerDirectory
    }

    It 'propagates refresh child failure with its exit code' {
        $env:LOTM_QA_CHILD_TEST_EXIT = '17'
        { Write-RepoRefreshCheck $config $generatedDir } | Should -Throw '*Visualization refresh check failed with exit code 17*'
    }

    It 'propagates bounded child failure with its exit code' {
        $env:LOTM_QA_CHILD_TEST_EXIT = '19'
        { Write-BoundedGraphs $config $generatedDir $graphSpecs } | Should -Throw '*Bounded visualization generation failed with exit code 19*'
    }

    It 'retains best-effort cleanup when its child returns failure' {
        $env:LOTM_QA_CHILD_TEST_EXIT = '23'
        { Invoke-DisposableCacheCleanup $config } | Should -Not -Throw
        $record = Get-Content -LiteralPath $logPath -Raw | ConvertFrom-Json
        $record.delete | Should -BeTrue
    }

    It 'retains missing-helper and launch-failure cleanup behavior' {
        $config.cleanup_powershell_helper = Join-Path $fixtureRoot 'missing helper.ps1'
        { Invoke-DisposableCacheCleanup $config } | Should -Not -Throw
        Test-Path $logPath | Should -BeFalse
        $config.cleanup_powershell_helper = $helper
        $originalExecutable = $script:QaPowerShellExecutable
        try {
            $script:QaPowerShellExecutable = Join-Path $fixtureRoot 'missing pwsh.exe'
            { Invoke-DisposableCacheCleanup $config } | Should -Not -Throw
        }
        finally {
            $script:QaPowerShellExecutable = $originalExecutable
        }
        Test-Path $logPath | Should -BeFalse
    }

    It 'does not launch a bounded child when no graph is requested' {
        $null = Write-BoundedGraphs $config $generatedDir @()
        Test-Path $logPath | Should -BeFalse
        Test-Path (Join-Path $generatedDir 'bounded-graphs') | Should -BeFalse
    }

    It 'delegates real cache deletion to PS7 while preserving adjacent files in an isolated project' {
        $resolvedFixture = [System.IO.Path]::GetFullPath($fixtureRoot)
        $testPrefix = [System.IO.Path]::GetFullPath($TestDrive) + [System.IO.Path]::DirectorySeparatorChar
        $resolvedFixture.StartsWith($testPrefix, [System.StringComparison]::OrdinalIgnoreCase) | Should -BeTrue
        $markerDir = Join-Path $fixtureRoot 'Project_Config'
        $cacheDir = Join-Path $fixtureRoot '.pytest_cache'
        $null = New-Item -ItemType Directory -Path $markerDir, $cacheDir
        # Cleanup only needs the project-root marker; it does not load the project schema.
        Set-Content -LiteralPath (Join-Path $markerDir 'project.yaml') -Value 'fixture: root-discovery-marker'
        Set-Content -LiteralPath (Join-Path $cacheDir 'owned-cache.txt') -Value 'Disposable'
        $sentinel = Join-Path $fixtureRoot 'preserve.txt'
        Set-Content -LiteralPath $sentinel -Value 'Preserve'
        $config.cleanup_powershell_helper = Join-Path $repoRoot 'Tools\Commands\Maintenance\Clean-TempFiles.ps1'
        try {
            Set-Location -LiteralPath $fixtureRoot
            Invoke-DisposableCacheCleanup $config
        }
        finally {
            Set-Location -LiteralPath $callerDirectory
        }
        Test-Path $cacheDir | Should -BeFalse
        Get-Content -LiteralPath $sentinel | Should -Be 'Preserve'
    }

    It 'removes stale bounded output while preserving adjacent owned output' {
        $boundedDir = [System.IO.Path]::GetFullPath((Join-Path $generatedDir 'bounded-graphs'))
        $fixturePrefix = [System.IO.Path]::GetFullPath($fixtureRoot) + [System.IO.Path]::DirectorySeparatorChar
        $boundedDir.StartsWith($fixturePrefix, [System.StringComparison]::OrdinalIgnoreCase) | Should -BeTrue
        $null = New-Item -ItemType Directory -Path $boundedDir
        Set-Content -LiteralPath (Join-Path $boundedDir 'stale.txt') -Value 'Owned stale output'
        $sentinel = Join-Path $generatedDir 'unrelated.txt'
        Set-Content -LiteralPath $sentinel -Value 'Preserve'
        $null = Write-BoundedGraphs $config $generatedDir @()
        Test-Path $boundedDir | Should -BeFalse
        Get-Content -LiteralPath $sentinel | Should -Be 'Preserve'
        Test-Path $logPath | Should -BeFalse
    }
}
