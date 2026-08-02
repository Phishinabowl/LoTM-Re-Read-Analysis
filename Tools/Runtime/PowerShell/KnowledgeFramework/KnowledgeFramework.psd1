@{
    RootModule = 'KnowledgeFramework.psm1'
    ModuleVersion = '0.1.0'
    GUID = '9fbb6c88-07d1-4ed9-a99d-f72475ee53c3'
    Author = 'Knowledge Framework Maintainers'
    Description = 'Reusable knowledge-framework runtime services.'
    PowerShellVersion = '5.1'
    CompatiblePSEditions = @('Desktop', 'Core')
    FunctionsToExport = @(
        'Test-KnowledgeProjectRoot'
        'Resolve-KnowledgeProjectRoot'
    )
    CmdletsToExport = @()
    VariablesToExport = @()
    AliasesToExport = @()
}
