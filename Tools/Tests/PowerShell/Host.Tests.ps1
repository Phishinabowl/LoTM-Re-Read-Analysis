# Retained host regressions. Phase 2.6 retires live Desktop migration proof; catalog adoption remains Phase 3.
BeforeAll {
    $priorFrameworkModules = @(Get-Module -Name KnowledgeFramework)
    $repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    $modulePath = Join-Path $repoRoot 'Tools\Runtime\PowerShell\KnowledgeFramework\KnowledgeFramework.psd1'
    . (Join-Path (Split-Path -Parent $modulePath) 'Private\PowerShell-Host.ps1')
    $pwshPath = (Get-Process -Id $PID).Path

    function Initialize-HostFixtureRoot {
        $config = Join-Path $TestDrive 'Project_Config'
        $null = New-Item -ItemType Directory -Path $config -Force
        Set-Content -LiteralPath (Join-Path $config 'project.yaml') -Value 'schema_version: 1'
    }

    function Invoke-HostTestProcess {
        param([string]$Executable = $pwshPath, [string[]]$Arguments)
        $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $Executable
        $startInfo.UseShellExecute = $false
        $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $startInfo.WorkingDirectory = $repoRoot
        foreach ($argument in $Arguments) {
            $startInfo.ArgumentList.Add($argument)
        }
        $process = [System.Diagnostics.Process]::new()
        $process.StartInfo = $startInfo
        try {
            $null = $process.Start()
            $stdoutTask = $process.StandardOutput.ReadToEndAsync()
            $stderrTask = $process.StandardError.ReadToEndAsync()
            if (-not $process.WaitForExit(60000)) {
                $process.Kill($true)
                $process.WaitForExit()
                throw 'Host regression child exceeded 60 seconds.'
            }
            return [pscustomobject]@{
                exit_code = $process.ExitCode
                stdout = $stdoutTask.GetAwaiter().GetResult()
                stderr = $stderrTask.GetAwaiter().GetResult()
            }
        }
        finally {
            $process.Dispose()
        }
    }
}

AfterAll {
    Remove-Module -Name KnowledgeFramework -Force -ErrorAction SilentlyContinue
    foreach ($priorModule in $priorFrameworkModules) {
        Import-Module $priorModule.Path -Force -ErrorAction Stop
    }
}

Describe 'PowerShell support boundary' -Tag 'Integration' {
    It 'accepts Core 7.4 and newer and rejects Desktop and older Core' {
        foreach ($version in @('7.4.0', '7.6.6', '8.0.0')) {
            (Get-KnowledgePowerShellHostStatus @{ PSVersion = [version]$version
                PSEdition = 'Core'
            }).host_supported | Should -BeTrue
        }
        foreach ($table in @(
                @{ PSVersion = [version]'7.3.12'
                    PSEdition = 'Core'
                }
                @{ PSVersion = [version]'5.1'
                    PSEdition = 'Desktop'
                }
                @{ PSVersion = [version]'7.4'
                    PSEdition = 'Desktop'
                }
                @{ PSVersion = [version]'7.4' }
            )) {
            $status = Get-KnowledgePowerShellHostStatus $table
            $status.host_supported | Should -BeFalse
            $status.message | Should -Match 'PowerShell 7.4\+ Core.*pwsh'
        }
    }

    It 'inherits the running host and rejects missing or different executables' {
        Resolve-KnowledgePowerShellExecutable | Should -Be $pwshPath
        { Resolve-KnowledgePowerShellExecutable -Executable '' } | Should -Throw '*unavailable*'
        { Resolve-KnowledgePowerShellExecutable -Executable (Join-Path $TestDrive 'missing.exe') } | Should -Throw '*unavailable*'
        $alternatePath = Join-Path $TestDrive 'alternate.exe'
        Set-Content -LiteralPath $alternatePath -Value 'Host resolver fixture; never execute.' -Encoding utf8
        { Resolve-KnowledgePowerShellExecutable -Executable $alternatePath } | Should -Throw '*alternate hosts*'
    }

    It 'declares the supported module version and imports on the running host' {
        $manifest = Import-PowerShellDataFile $modulePath
        $manifest.ModuleVersion | Should -Be '0.14.0'
        $manifest.PowerShellVersion | Should -Be '7.4'
        @($manifest.CompatiblePSEditions) | Should -Be @('Core')
        Import-Module $modulePath -Force
        # Existing manifest declaration has no implementation; host retirement preserves that baseline.
        $declared = @($manifest.FunctionsToExport | Where-Object { $_ -cne 'Assert-SchemaPackOccurrenceSemanticDeclarations' } | Sort-Object -Unique)
        $exported = @((Get-Module KnowledgeFramework).ExportedFunctions.Keys | Sort-Object)
        @(Compare-Object $declared $exported).Count | Should -Be 0
        (Get-Module KnowledgeFramework).ExportedFunctions.Keys | Should -Not -Contain 'Get-KnowledgePowerShellHostStatus'
    }

    It 'returns supported readiness with existing fields and usable modules' {
        Initialize-HostFixtureRoot
        $requirements = Join-Path $TestDrive 'usable-requirements.txt'
        Set-Content -LiteralPath $requirements -Value 'powershell-yaml 0.4.12'
        $run = Invoke-HostTestProcess -Arguments @('-NoProfile', '-File', 'Tools/Commands/Environment/Test-PowerShell.ps1', '-Root', $TestDrive, '-RequirementsPath', $requirements, '-Json')
        $run.exit_code | Should -Be 0
        $report = $run.stdout | ConvertFrom-Json
        $report.ready | Should -BeTrue
        $report.host_supported | Should -BeTrue
        $report.minimum_powershell_version | Should -Be '7.4'
        @($report.modules | Where-Object { -not $_.present -or -not $_.usable }).Count | Should -Be 0
        $report.requirements_path | Should -Not -BeNullOrEmpty
    }

    It 'does not treat a missing requirements file as an empty successful check' {
        $requirements = Join-Path $TestDrive 'missing-requirements.txt'
        $run = Invoke-HostTestProcess -Arguments @('-NoProfile', '-File', 'Tools/Commands/Environment/Test-PowerShell.ps1', '-RequirementsPath', $requirements, '-Json')
        $run.exit_code | Should -Be 1
        $report = $run.stdout | ConvertFrom-Json
        $report.ready | Should -BeFalse
        $report.message | Should -Match 'requirements file not found'
    }

    It 'reports missing and present but broken module requirements distinctly' {
        Initialize-HostFixtureRoot
        $modulesRoot = Join-Path $TestDrive 'Modules'
        $brokenRoot = Join-Path $modulesRoot 'BrokenHostFixture'
        $null = New-Item -ItemType Directory -Path $brokenRoot -Force
        Set-Content -LiteralPath (Join-Path $brokenRoot 'BrokenHostFixture.psm1') -Value "throw 'Host fixture import failure'"
        New-ModuleManifest -Path (Join-Path $brokenRoot 'BrokenHostFixture.psd1') `
            -RootModule 'BrokenHostFixture.psm1' -ModuleVersion '1.0.0'
        $requirements = Join-Path $TestDrive 'requirements.txt'
        Set-Content -LiteralPath $requirements -Value @('MissingHostFixture 1.0.0', 'BrokenHostFixture 1.0.0')
        $originalModulePath = $env:PSModulePath
        try {
            $env:PSModulePath = $modulesRoot + [System.IO.Path]::PathSeparator + $originalModulePath
            $run = Invoke-HostTestProcess -Arguments @('-NoProfile', '-File', 'Tools/Commands/Environment/Test-PowerShell.ps1', '-Root', $TestDrive, '-RequirementsPath', $requirements, '-Json')
        }
        finally {
            $env:PSModulePath = $originalModulePath
        }
        $run.exit_code | Should -Be 1
        $report = $run.stdout | ConvertFrom-Json
        $report.ready | Should -BeFalse
        $report.modules[0].present | Should -BeFalse
        $report.modules[1].present | Should -BeTrue
        $report.modules[1].usable | Should -BeFalse
        $report.modules[1].detail | Should -Match 'Host fixture import failure'
    }
}
