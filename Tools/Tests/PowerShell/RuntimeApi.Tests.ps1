BeforeAll {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
    $priorFrameworkModules = @(Get-Module KnowledgeFramework)
    Import-Module (Join-Path $repoRoot 'Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1') -Force
}

Describe 'Validated lookup registry reuse' -Tag Integration {
    BeforeEach {
        Import-Module (Join-Path $repoRoot 'Tools/Runtime/PowerShell/KnowledgeFramework/KnowledgeFramework.psd1') -Force
        $registryText = @'
{"schema_version":1,"unicode_version":"fixture","algorithm":"trim-nfc-default-casefold-nfc",
"trim_codepoints":[32],"case_folding":{"0041":[97]},"canonical_decomposition":{"00C0":[65,768]},
"canonical_combining_class":{"0300":230},"canonical_composition":{"0041+0300":192},
"counts":{"case_folding":1,"canonical_decomposition":1,"canonical_combining_class":1,"canonical_composition":1}}
'@
        $firstPath = Join-Path $TestDrive 'first.json'
        $secondPath = Join-Path $TestDrive 'second.json'
        [IO.File]::WriteAllText($firstPath, $registryText)
        [IO.File]::WriteAllText($secondPath, $registryText)
    }
    It 'keeps all mutable maps, nested arrays, trim values and metadata independent from its private template' {
        $first = Get-KnowledgeLookupKeyRegistryConfig $firstPath
        $first.case_folding[65][0] = 120
        $first.canonical_decomposition[192][0] = 66
        $first.canonical_combining_class[768] = 1
        $first.canonical_composition['41+300'] = 193
        $null = $first.trim_codepoints.Remove(32)
        $first.unicode_version = 'mutated'
        $second = Get-KnowledgeLookupKeyRegistryConfig $secondPath
        $second.path | Should -BeExactly ([IO.Path]::GetFullPath($secondPath))
        $second.unicode_version | Should -BeExactly 'fixture'
        $second.case_folding[65][0] | Should -Be 97
        $second.canonical_decomposition[192][0] | Should -Be 65
        $second.canonical_combining_class[768] | Should -Be 230
        $second.canonical_composition['41+300'] | Should -Be 192
        $second.trim_codepoints.Contains(32) | Should -BeTrue
        $second.case_folding[65][0] = 121
        $thirdPath = Join-Path $TestDrive 'third.json'
        [IO.File]::WriteAllText($thirdPath, $registryText)
        (Get-KnowledgeLookupKeyRegistryConfig $thirdPath).case_folding[65][0] | Should -Be 97
        $first.case_folding[65][0] | Should -Be 120
    }
    It 'reuses only validated identical text without reconstructing code-point sequences' {
        $null = Get-KnowledgeLookupKeyRegistryConfig $firstPath
        Mock ConvertFrom-KnowledgeCodePointSequence -ModuleName KnowledgeFramework { throw 'unexpected reconstruction' }
        $second = Get-KnowledgeLookupKeyRegistryConfig $secondPath
        ConvertTo-KnowledgeLookupKey ' A ' $second | Should -BeExactly 'a'
        Should -Invoke ConvertFrom-KnowledgeCodePointSequence -ModuleName KnowledgeFramework -Times 0
    }
    It 'reads new paths and rejects malformed text without poisoning later corrected loads' {
        $null = Get-KnowledgeLookupKeyRegistryConfig $firstPath
        Remove-Item -LiteralPath $secondPath
        { Get-KnowledgeLookupKeyRegistryConfig $secondPath } | Should -Throw '*Unable to parse lookup-key registry*second.json*'
        [IO.File]::WriteAllText($secondPath, '{malformed')
        { Get-KnowledgeLookupKeyRegistryConfig $secondPath } | Should -Throw '*Unable to parse lookup-key registry*second.json*'
        [IO.File]::WriteAllText($secondPath, $registryText)
        (Get-KnowledgeLookupKeyRegistryConfig $secondPath).case_folding[65][0] | Should -Be 97
    }
    It 'validates changed content and preserves count and scalar rejection' {
        $null = Get-KnowledgeLookupKeyRegistryConfig $firstPath
        [IO.File]::WriteAllText($secondPath, $registryText.Replace('[97]', '[98]'))
        (Get-KnowledgeLookupKeyRegistryConfig $secondPath).case_folding[65][0] | Should -Be 98
        $invalidPath = Join-Path $TestDrive 'invalid.json'
        [IO.File]::WriteAllText($invalidPath, $registryText.Replace('[97]', '[55296]'))
        { Get-KnowledgeLookupKeyRegistryConfig $invalidPath } | Should -Throw '*not a Unicode scalar value*'
        [IO.File]::WriteAllText($invalidPath, $registryText.Replace('"case_folding":1', '"case_folding":2'))
        { Get-KnowledgeLookupKeyRegistryConfig $invalidPath } | Should -Throw '*declared counts do not match*'
        [IO.File]::WriteAllText($invalidPath, $registryText)
        (Get-KnowledgeLookupKeyRegistryConfig $invalidPath).case_folding[65][0] | Should -Be 97
    }
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
