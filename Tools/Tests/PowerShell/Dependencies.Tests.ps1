BeforeAll {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
    . (Join-Path $repoRoot 'Tools/Commands/Environment/Private/Requirements.ps1')
}

Describe 'Exact module dependency declarations' -Tag 'Unit' {
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
