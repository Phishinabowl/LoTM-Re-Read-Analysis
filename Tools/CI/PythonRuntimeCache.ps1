#Requires -Version 7.4
# Admission/inventory and private candidate construction. No installer, network, restoration or runtime execution.

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
        if ($ancestor.LinkTarget -or ($ancestor.Exists -and ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint))) {
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
        [switch]$CaptureOnly,
        [switch]$SealModes
    )
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    if ($CaptureOnly -and $SealModes) {
        throw 'Capture and strict mode sealing are separate inventory contracts.'
    }
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
            if (($CaptureOnly -or $SealModes) -and $IsLinux -and $record.kind -ne 'symlink') {
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
    $rootMode = if ($SealModes -and $IsLinux) {
        [int][IO.File]::GetUnixFileMode($owner)
    }
    else {
        $null
    }
    if ($SealModes) {
        $json = ConvertTo-Json -InputObject ([ordered]@{ root_unix_mode = $rootMode
                entries = $entries
            }) -Depth 7 -Compress
    }
    $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($json))).ToLowerInvariant()
    [pscustomobject]@{ schema_version = $(if ($SealModes) {
                3
            }
            elseif ($CaptureOnly) {
                2
            }
            else {
                1
            })
        entries = $entries
        sha256 = $hash
        root_unix_mode = $rootMode
    }
}

function Read-CiPythonReferenceJson {
    param([string]$Path, [datetime]$DeadlineUtc, [scriptblock]$Cancelled)
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    $path = Get-CiPythonCachePath ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Path))) ([IO.Path]::GetFileName($Path))
    $file = Get-Item -LiteralPath $path -Force -ErrorAction Stop
    if ($file.PSIsContainer -or $file.LinkType -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        $file.Length -gt 2MB -or ($IsLinux -and ($file.UnixStat.HardlinkCount -gt 1 -or $file.UnixMode -notmatch '^-'))) {
        throw 'Plain bounded release reference file required.'
    }
    $bytes = [IO.File]::ReadAllBytes($path)
    if ($bytes.Length -gt 2MB) {
        throw 'Release reference size limit exceeded.'
    }
    $text = [Text.UTF8Encoding]::new($false, $true).GetString($bytes)
    $options = [Text.Json.JsonDocumentOptions]::new()
    $options.MaxDepth = 16
    $document = [Text.Json.JsonDocument]::Parse($text, $options)
    try {
        $queue = [Collections.Generic.Queue[Text.Json.JsonElement]]::new()
        $queue.Enqueue($document.RootElement)
        while ($queue.Count) {
            Test-CiPythonCacheLease $DeadlineUtc $Cancelled
            $node = $queue.Dequeue()
            if ($node.ValueKind -eq [Text.Json.JsonValueKind]::Object) {
                $names = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
                foreach ($property in $node.EnumerateObject()) {
                    if (-not $names.Add($property.Name)) {
                        throw 'Duplicate release reference JSON key.'
                    }
                    $queue.Enqueue($property.Value)
                }
            }
            elseif ($node.ValueKind -eq [Text.Json.JsonValueKind]::Array) {
                foreach ($value in $node.EnumerateArray()) {
                    $queue.Enqueue($value)
                }
            }
        }
    }
    finally {
        $document.Dispose()
    }
    [pscustomobject]@{ value = ($text | ConvertFrom-Json -AsHashtable)
        sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
    }
}

function Assert-CiPythonReferenceFields {
    param($Value, [string[]]$Fields)
    if ($Value -isnot [Collections.IDictionary] -or $Value.Count -ne $Fields.Count -or
        @($Value.Keys | Where-Object { $_ -cnotin $Fields }).Count) {
        throw 'Exact release reference fields required.'
    }
}

function Read-CiPythonPlatformReference {
    param(
        [Parameter(Mandatory)][string]$SpecificationPath,
        [Parameter(Mandatory)][string]$ReferencePath,
        [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions,
        [datetime]$DeadlineUtc = [datetime]::MaxValue,
        [scriptblock]$Cancelled = { $false },
        [ValidateSet('linux', 'windows')][string]$OS = 'linux'
    )
    $linux = $OS -ceq 'linux'
    $normalization = if ($linux) {
        'native-core-v2-linux-release-modes'
    }
    else {
        'native-core-v1'
    }
    $image = if ($linux) {
        'ubuntu-24.04'
    }
    else {
        'windows-2022'
    }
    $asset = if ($linux) {
        "python-$($RuntimeVersions.python)-linux-24.04-x64.tar.gz"
    }
    else {
        "python-$($RuntimeVersions.python)-win32-x64.zip"
    }
    $contract = if ($linux) {
        'ci-python-linux-release-reference'
    }
    else {
        'ci-python-windows-native-reference'
    }
    $spec = (Read-CiPythonReferenceJson $SpecificationPath $DeadlineUtc $Cancelled).value
    Assert-CiPythonReferenceFields $spec @('schema_version', 'reference_file', 'reference_sha256', 'expected_inventory_sha256', 'identity')
    if ($spec.schema_version -isnot [long] -and $spec.schema_version -isnot [int] -or $spec.schema_version -ne 1 -or
        $spec.reference_file -isnot [string] -or $spec.reference_file -cne "python-$OS-$($RuntimeVersions.python)-reference.json" -or
        [IO.Path]::GetFileName($ReferencePath) -cne $spec.reference_file) {
        throw 'Exact release reference declaration required.'
    }
    foreach ($key in 'reference_sha256', 'expected_inventory_sha256') {
        if ($spec[$key] -isnot [string] -or $spec[$key] -cnotmatch '^[0-9a-f]{64}$') {
            throw 'Typed reference hash required.'
        }
    }
    $identity = $spec.identity
    Assert-CiPythonReferenceFields $identity @('normalization', 'provider', 'provider_build', 'python', 'implementation', 'gil',
        'image_family', 'architecture', 'asset', 'archive_sha256')
    if (@($identity.Values | Where-Object { $_ -isnot [string] }).Count -or
        $RuntimeVersions.python -cnotmatch '^3\.14\.[0-9]+$' -or $identity.python -cne $RuntimeVersions.python -or
        $identity.normalization -cne $normalization -or $identity.provider -cne 'actions/python-versions' -or
        $identity.provider_build -cnotmatch ('^' + [regex]::Escape($identity.python) + '-[0-9]+$') -or
        $identity.implementation -cne 'cpython' -or $identity.gil -cne 'enabled' -or $identity.image_family -cne $image -or
        $identity.architecture -cne 'x64' -or $identity.asset -cne $asset -or
        $identity.archive_sha256 -cnotmatch '^[0-9a-f]{64}$') {
        throw 'Pinned platform release identity required.'
    }
    $loaded = Read-CiPythonReferenceJson $ReferencePath $DeadlineUtc $Cancelled
    if ($loaded.sha256 -cne $spec.reference_sha256) {
        throw 'Release reference file hash differs.'
    }
    $reference = $loaded.value
    Assert-CiPythonReferenceFields $reference @('contract', 'schema_version', 'identity', 'inventory')
    Assert-CiPythonReferenceFields $reference.identity @($identity.Keys)
    if ($reference.contract -isnot [string] -or $reference.contract -cne $contract -or
        ($reference.schema_version -isnot [long] -and $reference.schema_version -isnot [int]) -or $reference.schema_version -ne 1 -or
        @($reference.identity.Values | Where-Object { $_ -isnot [string] }).Count -or
        @($identity.Keys | Where-Object { $reference.identity[$_] -cne $identity[$_] }).Count) {
        throw 'Release reference identity differs.'
    }
    $inventory = $reference.inventory
    Assert-CiPythonReferenceFields $inventory @('schema_version', 'root_unix_mode', 'entries', 'sha256')
    if (($inventory.schema_version -isnot [long] -and $inventory.schema_version -isnot [int]) -or $inventory.schema_version -ne 3 -or
        ($linux -and (($inventory.root_unix_mode -isnot [long] -and $inventory.root_unix_mode -isnot [int]) -or $inventory.root_unix_mode -ne 493)) -or
        (-not $linux -and $null -ne $inventory.root_unix_mode) -or
        $inventory.sha256 -isnot [string] -or $inventory.sha256 -cne $spec.expected_inventory_sha256 -or
        $inventory.entries -isnot [array] -or $inventory.entries.Count -eq 0 -or $inventory.entries.Count -gt 200000) {
        throw 'Complete typed mode-aware release reference required.'
    }
    $paths = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
    $entries = [Collections.Generic.List[object]]::new()
    $previous = $null
    $dummyRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'Data'))
    foreach ($row in $inventory.entries) {
        Test-CiPythonCacheLease $DeadlineUtc $Cancelled
        if ($row -isnot [Collections.IDictionary] -or $row.path -isnot [string] -or -not $row.path -or
            $row.kind -isnot [string] -or $row.kind -cnotin 'file', 'directory', 'symlink' -or ($null -ne $previous -and
                [StringComparer]::Ordinal.Compare($previous, $row.path) -ge 0)) {
            throw 'Unique ordinal typed reference paths required.'
        }
        # These are metadata paths, not filesystem owners. The reference file's
        # real ancestry was verified once; avoid thousands of redundant stat calls.
        if ($row.path -match '[\\:\x00-\x1f]' -or @($row.path.Split('/') | Where-Object { $_ -in '', '.', '..' }).Count) {
            throw 'Canonical relative reference metadata path required.'
        }
        $previous = $row.path
        $copy = [ordered]@{ path = $row.path
            kind = $row.kind
        }
        if ($row.kind -ceq 'file') {
            $fields = @('path', 'kind', 'bytes', 'sha256')
            if ($linux) {
                $fields += 'unix_mode'
            }
            Assert-CiPythonReferenceFields $row $fields
            if (($row.bytes -isnot [long] -and $row.bytes -isnot [int]) -or $row.bytes -lt 0 -or $row.bytes -gt 256MB -or
                $row.sha256 -isnot [string] -or $row.sha256 -cnotmatch '^[0-9a-f]{64}$') {
                throw 'Typed bounded reference file required.'
            }
            $copy.bytes = $row.bytes
            $copy.sha256 = $row.sha256
        }
        elseif ($row.kind -ceq 'directory') {
            $fields = @('path', 'kind')
            if ($linux) {
                $fields += 'unix_mode'
            }
            Assert-CiPythonReferenceFields $row $fields
        }
        else {
            Assert-CiPythonReferenceFields $row @('path', 'kind', 'target')
            if ($row.target -isnot [string] -or -not $row.target -or [IO.Path]::IsPathRooted($row.target) -or
                $row.target -match '[\\:\x00-\x1f]' -or '..' -cin $row.target.Split('/')) {
                throw 'Relative reference file link required.'
            }
            $copy.target = $row.target
        }
        if ($linux -and $row.kind -cne 'symlink') {
            if (($row.unix_mode -isnot [long] -and $row.unix_mode -isnot [int]) -or $row.unix_mode -notin 420, 493 -or
                ($row.kind -ceq 'directory' -and $row.unix_mode -ne 493)) {
                throw 'Canonical reference mode required.'
            }
            $copy.unix_mode = $row.unix_mode
        }
        $paths.Add($row.path, $copy)
        $entries.Add($copy)
    }
    foreach ($row in $entries) {
        Test-CiPythonCacheLease $DeadlineUtc $Cancelled
        $parent = [IO.Path]::GetDirectoryName($row.path).Replace('\', '/')
        if ($parent -and (-not $paths.ContainsKey($parent) -or $paths[$parent].kind -cne 'directory')) {
            throw 'Complete reference parent directories required.'
        }
        if ($row.kind -ceq 'symlink') {
            $target = [IO.Path]::GetFullPath((Join-Path (Join-Path $dummyRoot $parent) $row.target))
            $relative = [IO.Path]::GetRelativePath($dummyRoot, $target).Replace('\', '/')
            $null = Get-CiPythonCachePath $dummyRoot $relative
            if (-not $paths.ContainsKey($relative) -or $paths[$relative].kind -cne 'file') {
                throw 'Reference links require direct retained file targets.'
            }
        }
    }
    $frame = [ordered]@{ root_unix_mode = $inventory.root_unix_mode
        entries = @($entries.ToArray())
    }
    $encoded = [Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $frame -Depth 7 -Compress))
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($encoded)).ToLowerInvariant()
    if ($digest -cne $inventory.sha256) {
        throw 'Release reference inventory digest differs.'
    }
    [pscustomobject]@{ identity = $identity
        reference_sha256 = $loaded.sha256
        inventory = $inventory
    }
}

function Read-CiPythonLinuxReleaseReference {
    param([Parameter(Mandatory)][string]$SpecificationPath, [Parameter(Mandatory)][string]$ReferencePath,
        [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions,
        [datetime]$DeadlineUtc = [datetime]::MaxValue, [scriptblock]$Cancelled = { $false })
    Read-CiPythonPlatformReference $SpecificationPath $ReferencePath $RuntimeVersions $DeadlineUtc $Cancelled -OS linux
}

function Get-CiPythonPlatformReference {
    param([Parameter(Mandatory)][ValidateSet('linux', 'windows')][string]$OS,
        [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions,
        [datetime]$DeadlineUtc = [datetime]::MaxValue, [scriptblock]$Cancelled = { $false })
    $data = Join-Path $PSScriptRoot 'Data'
    $specification = if ($OS -ceq 'linux') {
        'python-linux-release-reference-spec.json'
    }
    else {
        'python-windows-native-reference-spec.json'
    }
    Read-CiPythonPlatformReference (Join-Path $data $specification) `
    (Join-Path $data "python-$OS-$($RuntimeVersions.python)-reference.json") $RuntimeVersions $DeadlineUtc $Cancelled -OS $OS
}

function Get-CiPythonLinuxReleaseReference {
    param([Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions,
        [datetime]$DeadlineUtc = [datetime]::MaxValue, [scriptblock]$Cancelled = { $false })
    $data = Join-Path $PSScriptRoot 'Data'
    Read-CiPythonLinuxReleaseReference (Join-Path $data 'python-linux-release-reference-spec.json') `
    (Join-Path $data "python-linux-$($RuntimeVersions.python)-reference.json") $RuntimeVersions $DeadlineUtc $Cancelled
}

function Get-CiPythonCandidateProjection {
    param(
        [Parameter(Mandatory)]$Inventory,
        [Parameter(Mandatory)][string]$SourceRoot,
        [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions,
        [datetime]$DeadlineUtc = [datetime]::MaxValue,
        [scriptblock]$Cancelled = { $false }
    )
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    if (-not ($IsWindows -or $IsLinux) -or $Inventory.schema_version -ne 2 -or $RuntimeVersions.python -cnotmatch '^3\.14\.[0-9]+$') {
        throw 'Candidate projection requires raw schema 2 and the adopted Python 3.14 pin.'
    }
    $library = if ($IsWindows) {
        'Lib'
    }
    else {
        'lib/python3.14'
    }
    $package = "$library/site-packages/pip"
    $paths = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
    foreach ($row in $Inventory.entries) {
        Test-CiPythonCacheLease $DeadlineUtc $Cancelled
        $paths.Add($row.path, $row)
    }
    $metadata = @($Inventory.entries | Where-Object {
            $_.kind -eq 'directory' -and $_.path -match ('^' + [regex]::Escape($library) + '/site-packages/pip-[^/]+\.dist-info$')
        })
    if ($metadata.Count -ne 1 -or $metadata[0].path -cnotmatch
        ('^' + [regex]::Escape($library) + '/site-packages/pip-[0-9]+\.[0-9]+(?:\.[0-9]+)?\.dist-info$') -or
        -not $paths.ContainsKey("$package/__init__.py") -or
        $paths["$package/__init__.py"].kind -ne 'file' -or -not $paths.ContainsKey($metadata[0].path + '/RECORD') -or
        $paths[$metadata[0].path + '/RECORD'].kind -ne 'file') {
        throw 'Candidate requires one complete observed native base-pip distribution.'
    }
    $launchers = if ($IsWindows) {
        @('Scripts/pip.exe', 'Scripts/pip3.exe', 'Scripts/pip3.14.exe')
    }
    else {
        @('bin/pip', 'bin/pip3', 'bin/pip3.14')
    }
    $omitted = [Collections.Generic.Dictionary[string, string]]::new([StringComparer]::Ordinal)
    foreach ($row in $Inventory.entries) {
        Test-CiPythonCacheLease $DeadlineUtc $Cancelled
        if ($row.path -eq $package -or $row.path.StartsWith($package + '/', [StringComparison]::Ordinal) -or
            $row.path -eq $metadata[0].path -or $row.path.StartsWith($metadata[0].path + '/', [StringComparison]::Ordinal) -or
            $row.path -cin $launchers) {
            $omitted.Add($row.path, 'native-base-pip')
        }
        elseif ($row.kind -eq 'file' -and $row.path -match ('^(' + [regex]::Escape($library) +
                '(?:/.*)?)/__pycache__/([^/]+)\.cpython-314(?:\.opt-[12])?\.pyc$')) {
            $source = $Matches[1] + '/' + $Matches[2] + '.py'
            if ($paths.ContainsKey($source) -and $paths[$source].kind -eq 'file') {
                $omitted.Add($row.path, 'source-backed-bytecode')
            }
        }
    }
    $retained = [Collections.Generic.List[object]]::new()
    foreach ($row in $Inventory.entries) {
        Test-CiPythonCacheLease $DeadlineUtc $Cancelled
        if ($omitted.ContainsKey($row.path)) {
            continue
        }
        if ($row.kind -eq 'directory' -and $row.path.EndsWith('/__pycache__', [StringComparison]::Ordinal)) {
            $children = @($Inventory.entries | Where-Object { $_.path.StartsWith($row.path + '/', [StringComparison]::Ordinal) })
            if ($children.Count -and -not @($children | Where-Object { -not $omitted.ContainsKey($_.path) }).Count) {
                $omitted.Add($row.path, 'empty-generated-cache-directory')
                continue
            }
        }
        $copy = [ordered]@{}
        foreach ($key in $row.Keys) {
            $copy[$key] = $row[$key]
        }
        if ($IsWindows -and $row.path -ceq 'python3.exe' -and $row.kind -eq 'symlink') {
            if ($row.target -cne (Join-Path $SourceRoot 'python.exe').Replace('\', '/') -and $row.target -cne 'python.exe') {
                throw 'Candidate Windows alias differs from its exact native target.'
            }
            $copy.target = 'python.exe'
        }
        $retained.Add($copy)
    }
    $exe = if ($IsWindows) {
        'python.exe'
    }
    else {
        'bin/python3.14'
    }
    if (-not @($retained | Where-Object { $_.path -ceq $exe -and $_.kind -eq 'file' }).Count -or
        -not @($retained | Where-Object { $_.kind -eq 'file' -and
                $_.path.StartsWith("$library/ensurepip/_bundled/", [StringComparison]::Ordinal) -and $_.path.EndsWith('.whl') }).Count) {
        throw 'Candidate must retain the interpreter and bundled ensurepip wheels.'
    }
    $rootMode = if ($IsLinux) {
        493
    }
    else {
        $null
    }
    $entries = @($retained.ToArray())
    $json = ConvertTo-Json -InputObject ([ordered]@{ root_unix_mode = $rootMode
            entries = $entries
        }) -Depth 7 -Compress
    $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($json))).ToLowerInvariant()
    [pscustomobject]@{ normalization = 'native-core-v1'
        schema_version = 3
        entries = $entries
        root_unix_mode = $rootMode
        sha256 = $hash
        omitted = @($Inventory.entries | Where-Object { $omitted.ContainsKey($_.path) } |
                ForEach-Object { [ordered]@{ path = $_.path
                        reason = $omitted[$_.path]
                    } })
    }
}

function ConvertTo-CiPythonReleaseModeProjection {
    param([Parameter(Mandatory)]$Projection, [Parameter(Mandatory)]$Reference,
        [Parameter(Mandatory)]$SourceRootMode, [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions,
        [datetime]$DeadlineUtc = [datetime]::MaxValue, [scriptblock]$Cancelled = { $false })
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    if (($SourceRootMode -isnot [int] -and $SourceRootMode -isnot [long]) -or $SourceRootMode -notin 493, 511 -or
        $Projection.normalization -cne 'native-core-v1' -or $Projection.schema_version -ne 3 -or
        $Reference.identity.python -cne $RuntimeVersions.python -or
        $Reference.identity.normalization -cne 'native-core-v2-linux-release-modes' -or
        $Reference.reference_sha256 -cnotmatch '^[0-9a-f]{64}$' -or
        $Reference.inventory.schema_version -ne 3 -or $Reference.inventory.root_unix_mode -ne 493 -or
        $Projection.entries.Count -ne $Reference.inventory.entries.Count) {
        throw 'Complete admitted Linux reference and qualified source root required.'
    }
    $changes = [Collections.Generic.List[object]]::new()
    $entries = [Collections.Generic.List[object]]::new()
    for ($index = 0; $index -lt $Projection.entries.Count; $index++) {
        Test-CiPythonCacheLease $DeadlineUtc $Cancelled
        $actual = $Projection.entries[$index]
        $expected = $Reference.inventory.entries[$index]
        if ($actual.path -isnot [string] -or $actual.kind -isnot [string] -or $actual.path -cne $expected.path -or
            $actual.kind -cne $expected.kind -or $actual.Count -ne $expected.Count -or
            @($actual.Keys | Where-Object { $_ -cnotin @($expected.Keys) }).Count) {
            throw 'Retained reference paths or types differ.'
        }
        if ($actual.kind -ceq 'file' -and
            (($actual.bytes -isnot [int] -and $actual.bytes -isnot [long]) -or $actual.bytes -ne $expected.bytes -or
            $actual.sha256 -isnot [string] -or $actual.sha256 -cne $expected.sha256)) {
            throw 'Retained release bytes differ.'
        }
        if ($actual.kind -ceq 'symlink') {
            if ($actual.target -isnot [string] -or $actual.target -cne $expected.target) {
                throw 'Retained release link differs.'
            }
        }
        elseif (($actual.unix_mode -isnot [int] -and $actual.unix_mode -isnot [long]) -or
            ($actual.unix_mode -ne $expected.unix_mode -and $actual.unix_mode -ne 511)) {
            throw 'Unqualified native release mode.'
        }
        elseif ($actual.unix_mode -ne $expected.unix_mode) {
            $changes.Add([ordered]@{ path = $actual.path
                    from = $actual.unix_mode
                    to = $expected.unix_mode
                })
        }
        $copy = [ordered]@{}
        foreach ($key in $expected.Keys) {
            $copy[$key] = $expected[$key]
        }
        $entries.Add($copy)
    }
    $frame = [ordered]@{ root_unix_mode = 493
        entries = @($entries.ToArray())
    }
    $encoded = [Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $frame -Depth 7 -Compress))
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($encoded)).ToLowerInvariant()
    if ($digest -cne $Reference.inventory.sha256) {
        throw 'Normalized release reference digest differs.'
    }
    [pscustomobject]@{ normalization = 'native-core-v2-linux-release-modes'
        schema_version = 3
        entries = $frame.entries
        root_unix_mode = 493
        sha256 = $digest
        omitted = $Projection.omitted
        source_root_mode = $SourceRootMode
        mode_changes = @($changes.ToArray())
        reference = [ordered]@{ identity = $Reference.identity
            sha256 = $Reference.reference_sha256
            inventory_sha256 = $Reference.inventory.sha256
        }
    }
}

function New-CiPythonRuntimeCandidate {
    param(
        [Parameter(Mandatory)][string]$SourceRoot,
        [Parameter(Mandatory)][string]$WorkspaceRoot,
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions,
        [datetime]$DeadlineUtc = [datetime]::MaxValue,
        [scriptblock]$Cancelled = { $false },
        [switch]$LinuxReleaseModes
    )
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    if ($LinuxReleaseModes -and -not $IsLinux) {
        throw 'Release-mode copying is explicitly Linux-only.'
    }
    $source = Get-CiPythonCachePath $SourceRoot
    $workspace = Get-CiPythonCachePath $WorkspaceRoot
    if (-not (Test-Path -LiteralPath $workspace -PathType Container)) {
        throw 'Candidate workspace must already exist.'
    }
    $relative = [IO.Path]::GetRelativePath($workspace, [IO.Path]::GetFullPath($Destination)).Replace('\', '/')
    $target = Get-CiPythonCachePath $workspace $relative
    $comparison = if ($IsWindows) {
        [StringComparison]::OrdinalIgnoreCase
    }
    else {
        [StringComparison]::Ordinal
    }
    if ($target.Equals($source, $comparison) -or $target.StartsWith($source + [IO.Path]::DirectorySeparatorChar, $comparison) -or
        $source.StartsWith($target + [IO.Path]::DirectorySeparatorChar, $comparison)) {
        throw 'Candidate owners must not overlap.'
    }
    $receipt = Get-CiPythonCachePath $workspace ($relative + '.candidate.json')
    if ((Test-Path -LiteralPath $target) -or (Test-Path -LiteralPath $receipt)) {
        throw 'Candidate and receipt owners must be fresh.'
    }
    if ($LinuxReleaseModes) {
        $sourceMode = [int][IO.File]::GetUnixFileMode($source)
    }
    $raw = Get-CiPythonRuntimeInventory $source -CaptureOnly -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    $projection = Get-CiPythonCandidateProjection $raw $source $RuntimeVersions -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    if ($LinuxReleaseModes) {
        $reference = Get-CiPythonLinuxReleaseReference $RuntimeVersions -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
        $projection = ConvertTo-CiPythonReleaseModeProjection $projection $reference $sourceMode $RuntimeVersions `
            -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    }
    $null = New-Item -ItemType Directory -Path $target
    try {
        foreach ($row in $projection.entries | Where-Object { $_.kind -ne 'symlink' }) {
            Test-CiPythonCacheLease $DeadlineUtc $Cancelled
            $from = Get-CiPythonCachePath $source $row.path
            $to = Get-CiPythonCachePath $target $row.path
            if ($row.kind -eq 'directory') {
                $null = [IO.Directory]::CreateDirectory($to)
            }
            else {
                [IO.File]::Copy($from, $to, $false)
            }
        }
        foreach ($row in $projection.entries | Where-Object kind -eq 'symlink') {
            Test-CiPythonCacheLease $DeadlineUtc $Cancelled
            $to = Get-CiPythonCachePath $target $row.path
            $null = [IO.File]::CreateSymbolicLink($to, $row.target)
        }
        if ($IsLinux) {
            [object[]]$modeEntries = @($projection.entries | Where-Object { $_.kind -ne 'symlink' })
            [Array]::Reverse($modeEntries)
            foreach ($row in $modeEntries) {
                Test-CiPythonCacheLease $DeadlineUtc $Cancelled
                [IO.File]::SetUnixFileMode((Get-CiPythonCachePath $target $row.path), [IO.UnixFileMode]$row.unix_mode)
            }
            [IO.File]::SetUnixFileMode($target, [IO.UnixFileMode]$projection.root_unix_mode)
        }
        $complete = Get-CiPythonRuntimeInventory $target -SealModes -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
        if ($complete.sha256 -cne $projection.sha256 -or
            ($LinuxReleaseModes -and [int][IO.File]::GetUnixFileMode($source) -ne $sourceMode) -or
            (Get-CiPythonRuntimeInventory $source -CaptureOnly -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled).sha256 -cne $raw.sha256) {
            throw 'Candidate or source differs from its pre-copy inventory.'
        }
        $result = [ordered]@{ contract = 'ci-python-runtime-candidate'
            schema_version = $(if ($LinuxReleaseModes) {
                    2
                }
                else {
                    1
                })
            normalization = $projection.normalization
            status = 'candidate-complete'
            source_sha256 = $raw.sha256
            inventory = $complete
            omitted = $projection.omitted
            runtime_probe_verified = $false
            trusted_seal = $false
            handoff_admitted = $false
            saved = $false
        }
        if ($LinuxReleaseModes) {
            $result.reference = $projection.reference
            $result.source_root_mode = $sourceMode
            $result.mode_changes = $projection.mode_changes
        }
        $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $receipt -Encoding utf8
        [pscustomobject]$result
    }
    catch {
        $failure = [ordered]@{ contract = 'ci-python-runtime-candidate'
            schema_version = $(if ($LinuxReleaseModes) {
                    2
                }
                else {
                    1
                })
            status = 'candidate-incomplete'
            failure_type = $_.Exception.GetType().Name
            trusted_seal = $false
            handoff_admitted = $false
            saved = $false
        }
        if ($LinuxReleaseModes) {
            $failure.normalization = $projection.normalization
            $failure.reference = $projection.reference
            $failure.source_root_mode = $sourceMode
        }
        $failure | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receipt -Encoding utf8
        throw
    }
}

function Get-CiPythonNativeCaptureRoot {
    param(
        [Parameter(Mandatory)][string]$ToolsRoot,
        [Parameter(Mandatory)][AllowEmptyString()][string]$SelectedLocation,
        [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions
    )
    if ([string]::IsNullOrWhiteSpace($SelectedLocation) -or $SelectedLocation -match '\$\(' -or
        -not [IO.Path]::IsPathRooted($SelectedLocation)) {
        throw 'Native Python output is empty, unresolved or not absolute.'
    }
    if ($RuntimeVersions.python -cnotmatch '^[0-9]+\.[0-9]+\.[0-9]+$') {
        throw 'Exact authoritative Python pin required for native prefix validation.'
    }
    $expected = Get-CiPythonCachePath (Join-Path $ToolsRoot "Python/$($RuntimeVersions.python)/x64")
    $selected = Get-CiPythonCachePath $SelectedLocation
    $comparison = if ($IsWindows) {
        [StringComparison]::OrdinalIgnoreCase
    }
    else {
        [StringComparison]::Ordinal
    }
    if (-not $selected.TrimEnd([IO.Path]::DirectorySeparatorChar).Equals(
            $expected.TrimEnd([IO.Path]::DirectorySeparatorChar), $comparison)) {
        throw 'Native selected Python differs from the exact expected tool-cache prefix.'
    }
    $expected
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

function Get-CiPythonSealedCachePlan {
    param([Parameter(Mandatory)][Collections.IDictionary]$Context,
        [Parameter(Mandatory)][Collections.IDictionary]$RuntimeVersions,
        [datetime]$DeadlineUtc = [datetime]::MaxValue, [scriptblock]$Cancelled = { $false })
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    $image = switch -CaseSensitive ($Context.os) {
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
    if (-not $image -or $Context.host -cne 'ado' -or $Context.event -cne 'Manual' -or
        $Context.hosted -isnot [bool] -or -not $Context.hosted -or $Context.image_family -cne $image -or
        $Context.architecture -cne 'x64' -or $Context.executed_commit -isnot [string] -or
        $Context.executed_commit -cnotmatch '^[0-9a-f]{40}$') {
        throw 'Captured manual hosted context required for sealed planning.'
    }
    $reference = Get-CiPythonPlatformReference $Context.os $RuntimeVersions -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    $prefix = if ($Context.os -ceq 'windows') {
        "C:/hostedtoolcache/windows/Python/$($RuntimeVersions.python)/x64"
    }
    else {
        "/opt/hostedtoolcache/Python/$($RuntimeVersions.python)/x64"
    }
    $identity = [ordered]@{ schema_version = 2
        os = $Context.os
        image_family = $image
        architecture = 'x64'
        python_version = $reference.identity.python
        implementation = $reference.identity.implementation
        gil = $reference.identity.gil
        provider = $reference.identity.provider
        provider_build = $reference.identity.provider_build
        archive_sha256 = $reference.identity.archive_sha256
        normalization = $reference.identity.normalization
        reference_sha256 = $reference.reference_sha256
        inventory_schema_version = 3
        inventory_sha256 = $reference.inventory.sha256
        prefix_strategy = 'native-fixed-prefix'
        prefix = $prefix
        executable = $(if ($Context.os -ceq 'windows') {
                'python.exe'
            }
            else {
                'bin/python3.14'
            })
    }
    $encoded = [Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $identity -Compress))
    $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($encoded)).ToLowerInvariant()
    [pscustomobject]@{ contract = 'ci-python-runtime-sealed-cache-plan'
        schema_version = 2
        identity = $identity
        executed_commit = $Context.executed_commit
        cache_key = "lotm-python-runtime-v2-$digest"
        restoration_qualified = $false
        executed = $false
        handoff_admitted = $false
    }
}

function Get-CiPythonSealedCacheDecision {
    param([Parameter(Mandatory)]$Plan, [Parameter(Mandatory)][string]$StagingRoot,
        [Parameter(Mandatory)][string]$CacheHit, [datetime]$DeadlineUtc = [datetime]::MaxValue,
        [scriptblock]$Cancelled = { $false })
    Test-CiPythonCacheLease $DeadlineUtc $Cancelled
    if ($Plan.contract -cne 'ci-python-runtime-sealed-cache-plan' -or
        ($Plan.schema_version -isnot [int] -and $Plan.schema_version -isnot [long]) -or $Plan.schema_version -ne 2 -or
        $CacheHit -cnotin 'true', 'false' -or $Plan.executed -isnot [bool] -or $Plan.executed -or
        $Plan.restoration_qualified -isnot [bool] -or $Plan.restoration_qualified -or
        $Plan.handoff_admitted -isnot [bool] -or $Plan.handoff_admitted) {
        throw 'Unpromoted sealed staging plan and exact cache result required.'
    }
    $osName = if ($IsWindows) {
        'windows'
    }
    elseif ($IsLinux) {
        'linux'
    }
    else {
        ''
    }
    if ($Plan.identity.os -cne $osName) {
        throw 'Staged payload verification requires the matching implementation host.'
    }
    $pins = (Read-CiPythonReferenceJson (Join-Path $PSScriptRoot 'Data/runtime-versions.json') $DeadlineUtc $Cancelled).value
    $context = @{ host = 'ado'
        event = 'Manual'
        hosted = $true
        os = $osName
        image_family = $Plan.identity.image_family
        architecture = 'x64'
        executed_commit = $Plan.executed_commit
    }
    $expected = Get-CiPythonSealedCachePlan $context $pins -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    if ($Plan.cache_key -cne $expected.cache_key -or
        (ConvertTo-Json -InputObject $Plan.identity -Compress) -cne (ConvertTo-Json -InputObject $expected.identity -Compress)) {
        throw 'Sealed cache plan differs from repository declarations.'
    }
    $root = Get-CiPythonCachePath $StagingRoot
    if ($CacheHit -ceq 'false') {
        if ((Test-Path $root) -and @((Get-ChildItem -LiteralPath $root -Force)).Count) {
            throw 'Declared cache miss has unexpected staged bytes.'
        }
        return [pscustomobject]@{ contract = 'ci-python-runtime-sealed-cache-decision'
            schema_version = 2
            status = 'native-required'
            cache_hit = $false
            integrity_verified = $false
            executed = $false
            cache_key = $expected.cache_key
            inventory_sha256 = $null
            restoration_qualified = $false
            handoff_admitted = $false
        }
    }
    $inventory = Get-CiPythonRuntimeInventory $root -SealModes -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    if ($inventory.sha256 -cne $expected.identity.inventory_sha256) {
        throw 'Staged bytes or modes differ from the external sealed reference.'
    }
    $executable = Get-Item -LiteralPath (Get-CiPythonCachePath $root $expected.identity.executable) -Force -ErrorAction Stop
    if ($executable.PSIsContainer -or $executable.LinkType -or ($executable.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'A sealed staged interpreter must be a regular file.'
    }
    [pscustomobject]@{ contract = 'ci-python-runtime-sealed-cache-decision'
        schema_version = 2
        status = 'staging-verified'
        cache_hit = $true
        integrity_verified = $true
        executed = $false
        cache_key = $expected.cache_key
        inventory_sha256 = $inventory.sha256
        restoration_qualified = $false
        handoff_admitted = $false
    }
}

function Resolve-CiPythonFreshCopyOwner {
    param([Parameter(Mandatory)][string]$WorkspaceRoot,
        [Parameter(Mandatory)][string]$Destination, [Parameter(Mandatory)][string]$SourceRoot)
    $workspace = Get-CiPythonCachePath $WorkspaceRoot
    if (-not (Test-Path -LiteralPath $workspace -PathType Container)) {
        throw 'Copy workspace must already exist.'
    }
    $relative = [IO.Path]::GetRelativePath($workspace, [IO.Path]::GetFullPath($Destination)).Replace('\', '/')
    if ($relative -eq '.') {
        throw 'Copy target must be below its owner.'
    }
    $target = Get-CiPythonCachePath $workspace $relative
    $source = Get-CiPythonCachePath $SourceRoot
    $receipt = Get-CiPythonCachePath $workspace ($relative + '.copy.json')
    $comparison = if ($IsWindows) {
        [StringComparison]::OrdinalIgnoreCase
    }
    else {
        [StringComparison]::Ordinal
    }
    if ($target.Equals($source, $comparison) -or
        $target.StartsWith($source + [IO.Path]::DirectorySeparatorChar, $comparison) -or
        $source.StartsWith($target + [IO.Path]::DirectorySeparatorChar, $comparison)) {
        throw 'Copy source and destination must not overlap.'
    }
    if ((Get-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue) -or
        (Get-Item -LiteralPath $receipt -Force -ErrorAction SilentlyContinue)) {
        throw 'Copy target and external receipt must be fresh; existing owners are preserved.'
    }
    [pscustomobject]@{ target = $target
        receipt = $receipt
        workspace = $workspace
    }
}

function Get-CiPythonRestorationDestination {
    param([Parameter(Mandatory)]$Plan, [Parameter(Mandatory)][string]$ToolsRoot,
        [Parameter(Mandatory)][string]$StagingRoot,
        [datetime]$DeadlineUtc = [datetime]::MaxValue, [scriptblock]$Cancelled = { $false })
    # Read-only admission rebinds the complete plan before examining a host destination.
    $null = Get-CiPythonSealedCacheDecision $Plan $StagingRoot true -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    $tools = Get-CiPythonCachePath $ToolsRoot
    $expected = Get-CiPythonCachePath $tools "Python/$($Plan.identity.python_version)/x64"
    $declared = [IO.Path]::GetFullPath($Plan.identity.prefix)
    $comparison = if ($IsWindows) {
        [StringComparison]::OrdinalIgnoreCase
    }
    else {
        [StringComparison]::Ordinal
    }
    if (-not $expected.Equals($declared, $comparison)) {
        throw 'Actual hosted tools root differs from the declared native fixed prefix.'
    }
    $owner = Resolve-CiPythonFreshCopyOwner $tools $expected $StagingRoot
    [pscustomobject]@{ contract = 'ci-python-runtime-restoration-destination'
        schema_version = 1
        target = $owner.target
        receipt = $owner.receipt
        cache_key = $Plan.cache_key
        status = 'fresh-destination'
        executed = $false
        restoration_qualified = $false
        handoff_admitted = $false
    }
}

function New-CiPythonSealedPrivateCopy {
    param([Parameter(Mandatory)]$Plan, [Parameter(Mandatory)][string]$StagingRoot,
        [Parameter(Mandatory)][string]$WorkspaceRoot, [Parameter(Mandatory)][string]$Destination,
        [datetime]$DeadlineUtc = [datetime]::MaxValue, [scriptblock]$Cancelled = { $false })
    $decision = Get-CiPythonSealedCacheDecision $Plan $StagingRoot true -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    $owner = Resolve-CiPythonFreshCopyOwner $WorkspaceRoot $Destination $StagingRoot
    $fixed = [IO.Path]::GetFullPath($Plan.identity.prefix)
    $comparison = if ($IsWindows) {
        [StringComparison]::OrdinalIgnoreCase
    }
    else {
        [StringComparison]::Ordinal
    }
    if ($owner.target.Equals($fixed, $comparison) -or
        $owner.target.StartsWith($fixed + [IO.Path]::DirectorySeparatorChar, $comparison) -or
        $fixed.StartsWith($owner.target + [IO.Path]::DirectorySeparatorChar, $comparison)) {
        throw 'Private copying cannot write the declared native runtime owner.'
    }
    $inventory = Get-CiPythonRuntimeInventory $StagingRoot -SealModes -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
    if ($inventory.sha256 -cne $decision.inventory_sha256) {
        throw 'Staging changed before copying.'
    }
    $result = [ordered]@{ contract = 'ci-python-runtime-private-copy'
        schema_version = 1
        status = 'copy-incomplete'
        cache_key = $Plan.cache_key
        target = $owner.target
        inventory_sha256 = $null
        source_unchanged = $false
        integrity_verified = $false
        executed = $false
        restoration_qualified = $false
        handoff_admitted = $false
        saved = $false
    }
    # CreateNew claims the external lease before any payload write, including cancellation.
    $stream = [IO.File]::Open($owner.receipt, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    $stream.Dispose()
    try {
        $result | ConvertTo-Json | Set-Content -LiteralPath $owner.receipt -Encoding utf8
        Test-CiPythonCacheLease $DeadlineUtc $Cancelled
        $null = New-Item -ItemType Directory -Path $owner.target -ErrorAction Stop
        foreach ($row in $inventory.entries | Where-Object kind -ne 'symlink') {
            Test-CiPythonCacheLease $DeadlineUtc $Cancelled
            $to = Get-CiPythonCachePath $owner.target $row.path
            if ($row.kind -eq 'directory') {
                $null = [IO.Directory]::CreateDirectory($to)
            }
            else {
                [IO.File]::Copy((Get-CiPythonCachePath $StagingRoot $row.path), $to, $false)
            }
        }
        foreach ($row in $inventory.entries | Where-Object kind -eq 'symlink') {
            Test-CiPythonCacheLease $DeadlineUtc $Cancelled
            $null = [IO.File]::CreateSymbolicLink((Get-CiPythonCachePath $owner.target $row.path), $row.target)
        }
        if ($IsLinux) {
            [object[]]$rows = @($inventory.entries | Where-Object kind -ne 'symlink')
            [Array]::Reverse($rows)
            foreach ($row in $rows) {
                Test-CiPythonCacheLease $DeadlineUtc $Cancelled
                [IO.File]::SetUnixFileMode((Get-CiPythonCachePath $owner.target $row.path), [IO.UnixFileMode]$row.unix_mode)
            }
            [IO.File]::SetUnixFileMode($owner.target, [IO.UnixFileMode]$inventory.root_unix_mode)
        }
        $copied = Get-CiPythonRuntimeInventory $owner.target -SealModes -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
        $after = Get-CiPythonRuntimeInventory $StagingRoot -SealModes -DeadlineUtc $DeadlineUtc -Cancelled $Cancelled
        if ($copied.sha256 -cne $inventory.sha256 -or $after.sha256 -cne $inventory.sha256) {
            throw 'Copied payload or original staging changed during copying.'
        }
        $result.status = 'private-copy-verified'
        $result.inventory_sha256 = $copied.sha256
        $result.source_unchanged = $true
        $result.integrity_verified = $true
        $result | ConvertTo-Json | Set-Content -LiteralPath $owner.receipt -Encoding utf8
        [pscustomobject]$result
    }
    catch {
        $result.status = 'copy-incomplete'
        $result.integrity_verified = $false
        $result.failure_type = $_.Exception.GetType().Name
        $result | ConvertTo-Json | Set-Content -LiteralPath $owner.receipt -Encoding utf8
        throw
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
