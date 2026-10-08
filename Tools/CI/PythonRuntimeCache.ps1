#Requires -Version 7.4
# Read-only admission foundation. No installer, network, restoration or cached execution occurs here.

function Test-CiPythonCacheLease {
    param([datetime]$DeadlineUtc, [scriptblock]$Cancelled)
    if (& $Cancelled) {
        throw [OperationCanceledException]::new('Python cache admission cancelled.')
    }
    if ([datetime]::UtcNow -ge $DeadlineUtc) {
        throw [TimeoutException]::new('Python cache admission deadline expired.')
    }
}

function Get-CiPythonCachePath {
    param([Parameter(Mandatory)][string]$Root, [string]$Relative = '')
    $owner = [IO.Path]::GetFullPath($Root)
    if ($Relative -and ($Relative -match '[\\:\x00-\x1f]' -or
            @($Relative.Split('/') | Where-Object { $_ -in '', '.', '..' }).Count)) {
        throw 'Invalid Python runtime relative path.'
    }
    $path = if ($Relative) {
        [IO.Path]::GetFullPath((Join-Path $owner $Relative))
    }
    else {
        $owner
    }
    $comparison = if ($IsWindows) {
        [StringComparison]::OrdinalIgnoreCase
    }
    else {
        [StringComparison]::Ordinal
    }
    if ($path -ne $owner -and -not $path.StartsWith($owner.TrimEnd([IO.Path]::DirectorySeparatorChar) +
            [IO.Path]::DirectorySeparatorChar, $comparison)) {
        throw 'Python runtime path escapes owner.'
    }
    $ancestor = if ($Relative) {
        [IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($path))
    }
    else {
        [IO.DirectoryInfo]::new($owner)
    }
    while ($ancestor) {
        if ($ancestor.Exists -and ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'Python runtime owner or parent is a link.'
        }
        $ancestor = $ancestor.Parent
    }
    $path
}

function Get-CiPythonRuntimeInventory {
    param(
        [Parameter(Mandatory)][string]$Root,
        [datetime]$DeadlineUtc = [datetime]::MaxValue,
        [scriptblock]$Cancelled = { $false },
        [switch]$CaptureOnly
    )
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    $owner = Get-CiPythonCachePath $Root
    if (-not (Test-Path -LiteralPath $owner -PathType Container)) {
        throw 'Python runtime payload directory missing.'
    }
    $queue = [Collections.Generic.Queue[string]]::new()
    $queue.Enqueue($owner)
    $records = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
    while ($queue.Count) {
        foreach ($item in Get-ChildItem -LiteralPath $queue.Dequeue() -Force -ErrorAction Stop) {
            Test-CiPythonCacheLease $DeadlineUtc $Cancelled
            $relative = [IO.Path]::GetRelativePath($owner, $item.FullName).Replace('\', '/')
            $null = Get-CiPythonCachePath $owner $relative
            if ($records.Count -ge 200000) {
                throw 'Python runtime inventory entry limit exceeded.'
            }
            if ($item.LinkType -eq 'HardLink' -or ($IsLinux -and -not $item.PSIsContainer -and $item.UnixStat.HardlinkCount -gt 1)) {
                throw 'Python runtime hard links are not admitted.'
            }
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                if ($item.PSIsContainer) {
                    throw 'Directory Python runtime links are not qualified.'
                }
                $target = $item.LinkTarget
                $nativeAlias = $CaptureOnly -and $IsWindows -and $relative -ceq 'python3.exe' -and
                [IO.Path]::IsPathRooted($target) -and
                [IO.Path]::GetFullPath($target) -ceq (Join-Path $owner 'python.exe')
                if (-not $target -or (-not $nativeAlias -and
                        ([IO.Path]::IsPathRooted($target) -or $target -match '[:\x00-\x1f]'))) {
                    throw 'Python runtime link must have a relative target.'
                }
                $resolved = if ($nativeAlias) {
                    [IO.Path]::GetFullPath($target)
                }
                else {
                    [IO.Path]::GetFullPath((Join-Path $item.DirectoryName $target))
                }
                $targetRelative = [IO.Path]::GetRelativePath($owner, $resolved).Replace('\', '/')
                $null = Get-CiPythonCachePath $owner $targetRelative
                $leaf = Get-Item -LiteralPath $resolved -Force -ErrorAction Stop
                if ($leaf.PSIsContainer -or ($leaf.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                    throw 'Chained or directory Python runtime links are not qualified.'
                }
                $record = [ordered]@{ path = $relative
                    kind = 'symlink'
                    target = $target.Replace('\', '/')
                }
            }
            elseif ($item.PSIsContainer) {
                $record = [ordered]@{ path = $relative
                    kind = 'directory'
                }
                $queue.Enqueue($item.FullName)
            }
            else {
                if ($item.Length -gt 256MB) {
                    throw 'Python runtime file size limit exceeded.'
                }
                if (($item.Attributes -band [IO.FileAttributes]::Device) -or
                    ($IsLinux -and $item.UnixMode -notmatch '^-')) {
                    throw 'Nonregular Python runtime files are not admitted.'
                }
                $record = [ordered]@{ path = $relative
                    kind = 'file'
                    bytes = $item.Length
                    sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                }
                if ((Get-Item -LiteralPath $item.FullName -Force).Length -ne $record.bytes) {
                    throw 'Python runtime file changed during inventory.'
                }
            }
            if ($CaptureOnly -and $IsLinux -and $record.kind -ne 'symlink') {
                $record.unix_mode = [int][IO.File]::GetUnixFileMode($item.FullName)
            }
            $records.Add($relative, $record)
        }
    }
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    [string[]]$names = @($records.Keys)
    [Array]::Sort($names, [StringComparer]::Ordinal)
    $entries = @($names | ForEach-Object { $records[$_] })
    $json = ConvertTo-Json -InputObject $entries -Depth 6 -Compress
    $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($json))).ToLowerInvariant()
    [pscustomobject]@{ schema_version = $(if ($CaptureOnly) {
                2
            }
            else {
                1
            })
        entries = $entries
        sha256 = $hash
    }
}

function Get-CiPythonRuntimeCapture {
    param(
        [Parameter(Mandatory)][Collections.IDictionary]$Context,
        [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions,
        [Parameter(Mandatory)][string]$Root,
        [datetime]$DeadlineUtc = [datetime]::MaxValue,
        [scriptblock]$Cancelled = { $false }
    )
    $osName = if ($IsWindows) {
        'windows'
    }
    elseif ($IsLinux) {
        'linux'
    }
    else {
        ''
    }
    $image = if ($IsWindows) {
        'windows-2022'
    }
    else {
        'ubuntu-24.04'
    }
    if (-not $osName -or $Context.host -cne 'ado' -or $Context.event -cne 'Manual' -or
        $Context.hosted -isnot [bool] -or -not $Context.hosted -or $Context.os -cne $osName -or
        $Context.image_family -cne $image -or $Context.architecture -cne 'x64' -or
        $Context.executed_commit -cnotmatch '^[0-9a-f]{40}$' -or
        $Context.capture_id -cnotmatch '^[12]$' -or
        $RuntimeVersions.python -cnotmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
        throw 'Raw runtime capture requires exact manual hosted pilot context.'
    }
    $owner = Get-CiPythonCachePath $Root
    $exe = if ($IsWindows) {
        'python.exe'
    }
    else {
        'bin/python3.14'
    }
    $file = Get-Item -LiteralPath (Get-CiPythonCachePath $owner $exe) -Force -ErrorAction Stop
    if ($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Raw capture requires a regular interpreter file.'
    }
    $inventory = Get-CiPythonRuntimeInventory $owner -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled -CaptureOnly
    [pscustomobject]@{ contract = 'ci-python-runtime-capture'
        schema_version = 1
        executed_commit = $Context.executed_commit
        capture_id = $Context.capture_id
        os = $osName
        image_family = $image
        architecture = 'x64'
        requested_python = $RuntimeVersions.python
        prefix = $owner
        acquisition = 'native-selection'
        provider_build_verified = $false
        runtime_probe_verified = $false
        trusted_seal = $false
        handoff_admitted = $false
        saved = $false
        omitted_paths = @()
        inventory = $inventory
    }
}

function Get-CiPythonCachePlan {
    param(
        [Parameter(Mandatory)][Collections.IDictionary]$Context,
        [Parameter(Mandatory)][Collections.IDictionary]$Specification,
        [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions
    )
    $image = switch ($Context.os) {
        'windows' {
            'windows-2022'
        }
        'linux' {
            'ubuntu-24.04'
        }
        default {
            ''
        }
    }
    if ($Context.host -cne 'ado' -or $Context.event -cne 'Manual' -or $Context.hosted -isnot [bool] -or
        -not $Context.hosted -or -not $image -or $Context.image_family -ne $image -or
        $Context.architecture -cne 'x64' -or $Context.executed_commit -cnotmatch '^[0-9a-f]{40}$') {
        throw 'Python runtime cache pilot requires captured manual Microsoft-hosted x64 context.'
    }
    if ($RuntimeVersions.python -notmatch '^[0-9]+\.[0-9]+\.[0-9]+$' -or
        ($Specification.schema_version -isnot [int] -and $Specification.schema_version -isnot [long]) -or
        $Specification.schema_version -ne 1 -or $Specification.provider -cne 'actions/python-versions' -or
        $Specification.python_version -cne $RuntimeVersions.python -or
        $Specification.provider_build -cnotmatch ('^' + [regex]::Escape($RuntimeVersions.python) + '-[1-9][0-9]+$') -or
        $Specification.os -cne $Context.os -or $Specification.image_family -cne $image -or
        $Specification.architecture -cne 'x64' -or $Specification.inventory_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        ($Specification.revision -isnot [int] -and $Specification.revision -isnot [long]) -or $Specification.revision -lt 1) {
        throw 'Trusted Python runtime seal metadata differs from the approved pilot.'
    }
    $executable = if ($Context.os -eq 'windows') {
        'python.exe'
    }
    else {
        'bin/python3.14'
    }
    if ($Specification.executable -cne $executable -or -not [IO.Path]::IsPathRooted($Specification.prefix)) {
        throw 'Trusted Python runtime executable or fixed prefix is invalid.'
    }
    $identity = [ordered]@{ schema_version = 1
        os = $Context.os
        image_family = $image
        architecture = 'x64'
        python_version = $Specification.python_version
        provider = $Specification.provider
        provider_build = $Specification.provider_build
        revision = $Specification.revision
        inventory_sha256 = $Specification.inventory_sha256
        prefix = $Specification.prefix
        executable = $executable
    }
    $json = ConvertTo-Json -InputObject $identity -Compress
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($json))).ToLowerInvariant()
    [pscustomobject]@{ contract = 'ci-python-runtime-cache-plan'
        schema_version = 1
        identity = $identity
        executed_commit = $Context.executed_commit
        cache_key = "lotm-python-runtime-v1-$digest"
    }
}

function Get-CiPythonCacheDecision {
    param(
        [Parameter(Mandatory)]$Plan,
        [Parameter(Mandatory)][string]$StagingRoot,
        [Parameter(Mandatory)][ValidateSet('true', 'false')][string]$CacheHit,
        [datetime]$DeadlineUtc = [datetime]::MaxValue,
        [scriptblock]$Cancelled = { $false }
    )
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    if ($Plan.contract -ne 'ci-python-runtime-cache-plan' -or $Plan.schema_version -ne 1 -or
        $Plan.identity.inventory_sha256 -notmatch '^[0-9a-f]{64}$') {
        throw 'Trusted Python cache plan required.'
    }
    $root = Get-CiPythonCachePath $StagingRoot
    if ($CacheHit -eq 'false') {
        if ((Test-Path -LiteralPath $root) -and @((Get-ChildItem -LiteralPath $root -Force)).Count) {
            throw 'A declared cache miss contains unexpected payload files.'
        }
        return [pscustomobject]@{ status = 'native-required'
            cache_hit = $false
            integrity_verified = $false
            executed = $false
            cache_key = $Plan.cache_key
            inventory_sha256 = $null
        }
    }
    $inventory = Get-CiPythonRuntimeInventory -Root $root -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    if ($inventory.entries.Count -eq 0 -or $inventory.sha256 -cne $Plan.identity.inventory_sha256) {
        throw 'Python runtime payload differs from the external trusted seal.'
    }
    $executable = Get-CiPythonCachePath $root $Plan.identity.executable
    if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
        throw 'Python runtime executable missing.'
    }
    [pscustomobject]@{ status = 'probe-required'
        cache_hit = $true
        integrity_verified = $true
        executed = $false
        cache_key = $Plan.cache_key
        inventory_sha256 = $inventory.sha256
    }
}

function New-CiPythonCacheReceipt {
    param(
        [Parameter(Mandatory)]$Plan, [Parameter(Mandatory)]$Decision,
        [Collections.IDictionary]$Probe,
        [ValidateSet('none', 'acquisition-failed', 'cancelled', 'timed-out')][string]$Failure = 'none'
    )
    if ($Plan.contract -ne 'ci-python-runtime-cache-plan' -or $Decision.cache_key -cne $Plan.cache_key -or
        $Decision.status -notin 'native-required', 'probe-required' -or
        $Decision.executed -isnot [bool] -or $Decision.executed -ne $false -or
        $Decision.cache_hit -isnot [bool] -or $Decision.integrity_verified -isnot [bool]) {
        throw 'Python acquisition receipt requires the original admission decision.'
    }
    $verified = $false
    if ($Decision.status -eq 'native-required' -and ($Decision.cache_hit -or $Decision.integrity_verified -or
            $null -ne $Decision.inventory_sha256)) {
        throw 'A native miss cannot claim cached integrity.'
    }
    if ($Probe -and $Failure -eq 'none') {
        $expected = Join-Path $Plan.identity.prefix $Plan.identity.executable
        if ($Probe.python_version -cne $Plan.identity.python_version -or $Probe.architecture -cne 'x64' -or
            [IO.Path]::GetFullPath($Probe.executable) -cne [IO.Path]::GetFullPath($expected) -or
            [IO.Path]::GetFullPath($Probe.prefix) -cne [IO.Path]::GetFullPath($Plan.identity.prefix) -or
            [IO.Path]::GetFullPath($Probe.base_prefix) -cne [IO.Path]::GetFullPath($Plan.identity.prefix) -or
            @('ssl', 'sqlite', 'venv', 'ensurepip', 'isolated' | Where-Object { $Probe[$_] -isnot [bool] -or -not $Probe[$_] }).Count) {
            throw 'Python acquisition probe differs from its exact runtime or capability contract.'
        }
        $verified = $true
    }
    if ($Decision.status -eq 'probe-required' -and ($Decision.cache_hit -ne $true -or
            $Decision.integrity_verified -ne $true -or $Decision.inventory_sha256 -cne $Plan.identity.inventory_sha256)) {
        throw 'Python cache receipt cannot promote unverified integrity.'
    }
    $status = if ($Failure -ne 'none') {
        $Failure
    }
    elseif ($verified) {
        'probe-verified'
    }
    else {
        $Decision.status
    }
    [pscustomobject]@{ contract = 'ci-python-runtime-acquisition-receipt'
        schema_version = 1
        executed_commit = $Plan.executed_commit
        identity = $Plan.identity
        cache_key = $Plan.cache_key
        status = $status
        cache_hit = $Decision.cache_hit
        integrity_verified = $Decision.integrity_verified
        probe_verified = $verified
        environment_verified = $false
        handoff_admitted = $false
        saved = $false
        exit_code = $(if ($Failure -eq 'cancelled') {
                130
            }
            elseif ($Failure -ne 'none') {
                1
            }
            else {
                0
            })
    }
}
