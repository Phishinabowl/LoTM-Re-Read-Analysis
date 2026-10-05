BeforeAll {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
    $priorFrameworkModules = @(Get-Module KnowledgeFramework)
    Import-Module (Join-Path $repoRoot 'Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1') -Force
}

AfterAll {
    Remove-Module KnowledgeFramework -Force -ErrorAction SilentlyContinue
    foreach ($module in $priorFrameworkModules) {
        Import-Module $module.Path -Force
    }
}

Describe 'Source runtime project root API pilot' -Tag Integration {
    BeforeEach {
        $priorRoot = $env:KNOWLEDGE_PROJECT_ROOT
        $cwd = (Get-Location).Path
        $explicit = Join-Path $TestDrive 'explicit'
        $other = Join-Path $TestDrive 'other'
        foreach ($root in @($explicit, $other)) {
            $config = Join-Path $root 'Project_Config'
            $null = New-Item -ItemType Directory -Path $config -Force
            Set-Content (Join-Path $config 'project.yaml') 'schema_version: 1'
        }
        $env:KNOWLEDGE_PROJECT_ROOT = $other
    }
    AfterEach { $env:KNOWLEDGE_PROJECT_ROOT = $priorRoot }
    It 'uses the explicit root and does not fall back when that override is invalid' {
        Resolve-KnowledgeProjectRoot -ExplicitRoot $explicit -CurrentDirectory $other | Should -Be $explicit
        { Resolve-KnowledgeProjectRoot -ExplicitRoot (Join-Path $TestDrive 'missing') -CurrentDirectory $other } | Should -Throw '*explicit root*missing required manifest*'
        (Get-Location).Path | Should -Be $cwd
    }
    It 'rejects a relative environment override despite a valid current root' {
        $env:KNOWLEDGE_PROJECT_ROOT = 'relative'
        { Resolve-KnowledgeProjectRoot -CurrentDirectory $other } | Should -Throw '*must be an absolute path*'
        (Get-Location).Path | Should -Be $cwd
    }
}
