BeforeAll {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    . (Join-Path $repoRoot 'Tools/Commands/Environment/Private/Requirements.ps1')
}

Describe 'Exact module dependency declarations' -Tag 'Unit' {
    It 'isolates production script children from an equal-version shadow and preserves argument data and exit' {
        $owned = Join-Path $TestDrive 'production-owned'
        $shadow = Join-Path $TestDrive 'production-shadow'
        foreach ($base in @($owned, $shadow)) {
            $module = Join-Path $base 'FixtureChild/1.0.0'
            $null = New-Item -ItemType Directory -Path $module -Force
            Set-Content -LiteralPath (Join-Path $module 'FixtureChild.psm1') -Value "function Get-FixtureChild { 'fixture' }"
            Set-Content -LiteralPath (Join-Path $module 'FixtureChild.psd1') -Value "@{ RootModule='FixtureChild.psm1'; ModuleVersion='1.0.0' }"
        }
        $scriptPath = Join-Path $TestDrive 'child with spaces.ps1'
        Set-Content -LiteralPath $scriptPath -Value @(
            'param([string]$Value)',
            '$module = Import-Module FixtureChild -RequiredVersion 1.0.0 -PassThru',
            '@{path=$module.ModuleBase; value=$Value} | ConvertTo-Json -Compress',
            'exit 7'
        )
        $priorOwner = $env:LOTM_CI_MODULE_ROOT
        $priorPath = $env:PSModulePath
        try {
            $env:LOTM_CI_MODULE_ROOT = $owned
            $env:PSModulePath = $shadow + [IO.Path]::PathSeparator + (Join-Path $PSHOME 'Modules')
            $literal = 'spaces; $(literal) "quoted"'
            $payload = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(
                    (@($scriptPath, '-Value', $literal) | ConvertTo-Json -Compress)))
            $wrapper = Join-Path $repoRoot 'Tools/Commands/Environment/Invoke-OwnedPowerShell.ps1'
            $result = & (Get-Process -Id $PID).Path -NoProfile -File $wrapper -Payload $payload
            $LASTEXITCODE | Should -Be 7
            $document = $result | ConvertFrom-Json
            $document.path | Should -BeLike "$owned*"
            $document.value | Should -Be $literal
            Set-Content -LiteralPath $scriptPath -Value @(
                '$hostExecutable = (Get-Process -Id $PID).Path',
                '& $hostExecutable -NoProfile -Command ''exit 9''',
                '''handled native failure'''
            )
            $payload = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(
                    (@($scriptPath) | ConvertTo-Json -Compress)))
            $result = & (Get-Process -Id $PID).Path -NoProfile -File $wrapper -Payload $payload
            $LASTEXITCODE | Should -Be 0
            $result | Should -Be 'handled native failure'
        }
        finally {
            $env:LOTM_CI_MODULE_ROOT = $priorOwner
            $env:PSModulePath = $priorPath
        }
    }

    It 'probes the owned module path even when an equal-version module shadows it' {
        $project = Join-Path $TestDrive 'probe-project'
        $ci = Join-Path $project 'Tools/CI'
        $private = Join-Path $project 'Tools/Commands/Environment/Private'
        $null = New-Item -ItemType Directory -Path $ci, $private -Force
        Copy-Item -LiteralPath (Join-Path $repoRoot 'Tools/CI/Probe-PowerShellModules.ps1') -Destination $ci
        Copy-Item -LiteralPath (Join-Path $repoRoot 'Tools/Commands/Environment/Private/Requirements.ps1') -Destination $private
        Set-Content -LiteralPath (Join-Path $project 'requirements-powershell-dev.txt') -Value 'FixtureProbe 1.0.0'
        $owned = Join-Path $TestDrive 'owned'
        $shadow = Join-Path $TestDrive 'shadow'
        foreach ($base in @($owned, $shadow)) {
            $module = Join-Path $base 'FixtureProbe/1.0.0'
            $null = New-Item -ItemType Directory -Path $module -Force
            Set-Content -LiteralPath (Join-Path $module 'FixtureProbe.psm1') -Value "function Get-FixtureProbe { 'fixture' }"
            Set-Content -LiteralPath (Join-Path $module 'FixtureProbe.psd1') -Value "@{ RootModule='FixtureProbe.psm1'; ModuleVersion='1.0.0' }"
        }
        $prior = $env:PSModulePath
        try {
            $builtin = Join-Path $PSHOME 'Modules'
            $env:PSModulePath = $shadow + [IO.Path]::PathSeparator + $builtin
            $probe = Join-Path $ci 'Probe-PowerShellModules.ps1'
            $control = & (Get-Process -Id $PID).Path -NoProfile -File $probe | ConvertFrom-Json
            $LASTEXITCODE | Should -Be 0
            $control.modules[0].path | Should -BeLike "$shadow*"
            $result = & (Get-Process -Id $PID).Path -NoProfile -File $probe -ModulePath ($owned + [IO.Path]::PathSeparator + $builtin)
            $LASTEXITCODE | Should -Be 0
            $document = $result | ConvertFrom-Json
            $document.modules[0].path | Should -BeLike "$owned*"
            $document.modules[0].version | Should -Be '1.0.0'
        }
        finally {
            $env:PSModulePath = $prior
        }
    }

    It 'preserves exact versions across confined includes' {
        Set-Content -LiteralPath (Join-Path $TestDrive 'runtime.txt') -Value 'powershell-yaml 0.4.12'
        Set-Content -LiteralPath (Join-Path $TestDrive 'dev.txt') -Value @('-r runtime.txt', 'Pester 6.2.0')
        $rows = @(Read-ExactModuleRequirements -Path (Join-Path $TestDrive 'dev.txt') -Root $TestDrive)
        $rows.Count | Should -Be 2
        $rows[0].Version | Should -Be '0.4.12'
        $rows[1].Version | Should -Be '6.2.0'
    }

    It 'rejects empty, floating, conflicting, unknown and cyclic declarations' {
        foreach ($lines in @(
                @(''), @('Pester'), @('Pester latest'), @('--other flag'),
                @('Pester 6.2.0', 'Pester 6.1.0'), @('-r invalid.txt')
            )) {
            Set-Content -LiteralPath (Join-Path $TestDrive 'invalid.txt') -Value $lines
            { Read-ExactModuleRequirements -Path (Join-Path $TestDrive 'invalid.txt') -Root $TestDrive } | Should -Throw
        }
    }

    It 'rejects escaping includes even when the referenced file exists' {
        $null = New-Item -ItemType Directory -Path (Join-Path $TestDrive 'project')
        Set-Content -LiteralPath (Join-Path $TestDrive 'outside.txt') -Value 'Pester 6.2.0'
        $file = Join-Path $TestDrive 'project/requirements.txt'
        Set-Content -LiteralPath $file -Value '-r ../outside.txt'
        { Read-ExactModuleRequirements -Path $file -Root (Join-Path $TestDrive 'project') } | Should -Throw '*escapes*'
    }
}
