function Get-ToolFunctionBlock {
    param([string]$Path, [string[]]$Name)
    $tokens = $null
    $errors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
    if ($errors.Count) {
        throw "Pilot source did not parse: $Path"
    }
    $definitions = @($ast.EndBlock.Statements | Where-Object { $_ -is [Management.Automation.Language.FunctionDefinitionAst] })
    if ($Name) {
        foreach ($requested in $Name) {
            if (@($definitions | Where-Object Name -CEQ $requested).Count -ne 1) {
                throw "Pilot function missing or ambiguous: $requested"
            }
        }
        $definitions = @($definitions | Where-Object Name -CIn $Name)
    }
    [scriptblock]::Create(($definitions.Extent.Text -join [Environment]::NewLine))
}
