param([Parameter(Mandatory)][string]$Payload)
$ErrorActionPreference = 'Stop'
if (-not $env:LOTM_CI_MODULE_ROOT -or -not (Test-Path -LiteralPath $env:LOTM_CI_MODULE_ROOT -PathType Container)) {
    throw 'Explicit existing CI module owner required.'
}
# Startup may prepend global paths. Reset inside every owned child, retaining only builtin modules.
$env:PSModulePath = $env:LOTM_CI_MODULE_ROOT + [IO.Path]::PathSeparator + (Join-Path $PSHOME 'Modules')
$env:LOTM_CI_POWERSHELL_LAUNCHER = $PSCommandPath
$command = @([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Payload)) | ConvertFrom-Json)
if ($command.Count -eq 2 -and $command[0] -eq '-Command') {
    & ([scriptblock]::Create($command[1]))
    $succeeded = $?
}
else {
    if ($command.Count -eq 0 -or -not (Test-Path -LiteralPath $command[0] -PathType Leaf)) {
        throw 'Existing script command required.'
    }
    $scriptPath = $command[0]
    $parameters = @{}
    for ($index = 1; $index -lt $command.Count; $index++) {
        if ($command[$index] -notmatch '^-[A-Za-z][A-Za-z0-9]*$') {
            throw 'Owned script arguments must use explicit named parameters.'
        }
        $name = $command[$index].Substring(1)
        if ($parameters.ContainsKey($name)) {
            throw 'Duplicate owned script parameter.'
        }
        if ($index + 1 -lt $command.Count -and $command[$index + 1] -notmatch '^-[A-Za-z][A-Za-z0-9]*$') {
            $index++
            $parameters[$name] = $command[$index]
        }
        else {
            $parameters[$name] = $true
        }
    }
    & $scriptPath @parameters
    $succeeded = $?
}
if (-not $succeeded) {
    if ($null -ne $LASTEXITCODE) {
        exit $LASTEXITCODE
    }
    exit 1
}
exit 0
