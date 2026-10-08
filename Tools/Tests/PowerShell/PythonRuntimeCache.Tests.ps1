BeforeAll {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
    . (Join-Path $repoRoot 'Tools/CI/PythonRuntimeCache.ps1')
    $pins = Get-Content -LiteralPath (Join-Path $repoRoot 'Tools/CI/Data/runtime-versions.json') -Raw |
        ConvertFrom-Json -AsHashtable
}

Describe 'Pre-Python cache admission without cached execution' -Tag Unit {
    BeforeEach {
        $payload = Join-Path $TestDrive ('cache β with spaces ' + [guid]::NewGuid().ToString('N'))
        $null = New-Item -ItemType Directory -Path (Join-Path $payload 'bin'), (Join-Path $payload 'empty') -Force
        $exeRelative = if ($IsWindows) {
            'python.exe'
        }
        else {
            'bin/python3.14'
        }
        [IO.File]::WriteAllText((Join-Path $payload $exeRelative), 'fixture bytes, never executable')
        [IO.File]::WriteAllText((Join-Path $payload 'stdlib.txt'), 'fixture stdlib')
        $inventory = Get-CiPythonRuntimeInventory $payload
        $osName = if ($IsWindows) {
            'windows'
        }
        else {
            'linux'
        }
        $image = if ($IsWindows) {
            'windows-2022'
        }
        else {
            'ubuntu-24.04'
        }
        $cacheContext = @{ host = 'ado'
            event = 'Manual'
            hosted = $true
            os = $osName
            image_family = $image
            architecture = 'x64'
            executed_commit = ('a' * 40)
        }
        $seal = @{ schema_version = 1
            provider = 'actions/python-versions'
            python_version = $pins.python
            provider_build = $pins.python + '-36806082737'
            os = $osName
            image_family = $image
            architecture = 'x64'
            inventory_sha256 = $inventory.sha256
            revision = 1
            prefix = $payload
            executable = $exeRelative
        }
        $cachePlan = Get-CiPythonCachePlan -Context $cacheContext -Specification $seal -RuntimeVersions $pins
    }

    It 'inventories files and empty directories deterministically with ordinal paths and no owner-specific hash' {
        $copy = Join-Path $TestDrive 'second-owner'
        Copy-Item -LiteralPath $payload -Destination $copy -Recurse
        $second = Get-CiPythonRuntimeInventory $copy
        $second.sha256 | Should -BeExactly $inventory.sha256
        @($inventory.entries | Where-Object kind -eq 'directory').Count | Should -Be 2
        ($inventory.entries.path -join '|') | Should -BeExactly ($second.entries.path -join '|')
        $inventory.sha256 | Should -Match '^[0-9a-f]{64}$'
    }

    It 'admits a real exact hit only to probe-required and never runs the fixture executable' {
        $decision = Get-CiPythonCacheDecision $cachePlan $payload true
        $decision.status | Should -BeExactly 'probe-required'
        $decision.integrity_verified | Should -BeTrue
        $decision.executed | Should -BeFalse
        $receipt = New-CiPythonCacheReceipt $cachePlan $decision
        $receipt.handoff_admitted | Should -BeFalse
        $receipt.environment_verified | Should -BeFalse
        $receipt.saved | Should -BeFalse
    }

    It 'a clean miss requests native acquisition without inventing payload verification' {
        $decision = Get-CiPythonCacheDecision $cachePlan (Join-Path $TestDrive 'absent') false
        $decision.status | Should -BeExactly 'native-required'
        $decision.integrity_verified | Should -BeFalse
        $decision.cache_hit | Should -BeFalse
        $receipt = New-CiPythonCacheReceipt $cachePlan $decision
        $receipt.probe_verified | Should -BeFalse
        Test-Path -LiteralPath (Join-Path $TestDrive 'absent') | Should -BeFalse
    }

    It 'rejects a claimed miss with a partial payload and rejects inexact cache matches' {
        { Get-CiPythonCacheDecision $cachePlan $payload false } | Should -Throw '*unexpected payload*'
        { Get-CiPythonCacheDecision $cachePlan $payload inexact } | Should -Throw
        { Get-CiPythonCacheDecision $cachePlan (Join-Path $TestDrive 'missing-hit') true } | Should -Throw '*missing*'
    }

    It 'rejects a matching inventory seal that omits the required executable' {
        Remove-Item -LiteralPath (Join-Path $payload $exeRelative)
        $seal.inventory_sha256 = (Get-CiPythonRuntimeInventory $payload).sha256
        $missingPlan = Get-CiPythonCachePlan $cacheContext $seal $pins
        { Get-CiPythonCacheDecision $missingPlan $payload true } | Should -Throw '*executable missing*'
    }

    It 'rejects <mutation> payload changes against the external trusted seal' -ForEach @(
        @{ mutation = 'corrupt' }, @{ mutation = 'missing' }, @{ mutation = 'extra-file' },
        @{ mutation = 'extra-directory' }, @{ mutation = 'self-supplied-seal' }
    ) {
        switch ($mutation) {
            corrupt {
                [IO.File]::WriteAllText((Join-Path $payload 'stdlib.txt'), 'corrupt stdlib')
            }
            missing {
                Remove-Item -LiteralPath (Join-Path $payload $exeRelative)
            }
            extra-file {
                [IO.File]::WriteAllText((Join-Path $payload 'extra.txt'), 'extra')
            }
            extra-directory {
                $null = New-Item -ItemType Directory -Path (Join-Path $payload 'unexpected')
            }
            self-supplied-seal {
                $seal | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $payload 'seal.json')
            }
        }
        { Get-CiPythonCacheDecision $cachePlan $payload true } | Should -Throw '*external trusted seal*'
    }

    It 'rejects <field>=<value> metadata that crosses the approved native pilot boundary' -ForEach @(
        @{ field = 'host'
            value = 'github'
        }, @{ field = 'event'
            value = 'PullRequest'
        },
        @{ field = 'hosted'
            value = $false
        }, @{ field = 'hosted'
            value = 'true'
        },
        @{ field = 'os'
            value = 'darwin'
        }, @{ field = 'image_family'
            value = 'windows-latest'
        },
        @{ field = 'architecture'
            value = 'x64-freethreaded'
        }, @{ field = 'executed_commit'
            value = 'HEAD'
        }
    ) {
        $cacheContext[$field] = $value
        { Get-CiPythonCachePlan $cacheContext $seal $pins } | Should -Throw '*captured manual*'
    }

    It 'rejects <field>=<value> seal metadata before touching runtime files' -ForEach @(
        @{ field = 'schema_version'
            value = 1.0
        }, @{ field = 'schema_version'
            value = $true
        },
        @{ field = 'python_version'
            value = '3.14.7'
        }, @{ field = 'provider'
            value = 'unapproved'
        },
        @{ field = 'provider_build'
            value = 'latest'
        }, @{ field = 'architecture'
            value = 'arm64'
        },
        @{ field = 'inventory_sha256'
            value = 'untrusted'
        }, @{ field = 'revision'
            value = 0
        },
        @{ field = 'executable'
            value = '../foreign.exe'
        }, @{ field = 'prefix'
            value = 'relative'
        }
    ) {
        $seal[$field] = $value
        { Get-CiPythonCachePlan $cacheContext $seal $pins } | Should -Throw
    }

    It 'reads the adopted version from authoritative pins and uses exact deterministic cache keys' {
        $same = Get-CiPythonCachePlan $cacheContext ($seal.Clone()) $pins
        $same.cache_key | Should -BeExactly $cachePlan.cache_key
        $seal.revision = 2
        (Get-CiPythonCachePlan $cacheContext $seal $pins).cache_key | Should -Not -Be $same.cache_key
        $seal.revision = 1
        $changedPins = $pins.Clone()
        $changedPins.python = '3.14.9'
        { Get-CiPythonCachePlan $cacheContext $seal $changedPins } | Should -Throw
        $jsonSeal = $seal | ConvertTo-Json | ConvertFrom-Json -AsHashtable
        (Get-CiPythonCachePlan $cacheContext $jsonSeal $pins).cache_key | Should -BeExactly $cachePlan.cache_key
    }

    It 'rejects traversal and cross-platform separators: <relative>' -ForEach @(
        @{ relative = '../outside' }, @{ relative = 'bin/../outside' }, @{ relative = 'bin//python' },
        @{ relative = 'bin\python' }, @{ relative = 'C:/outside' }
    ) {
        { Get-CiPythonCachePath $payload $relative } | Should -Throw '*relative path*'
    }

    It 'rejects expired or cancelled admission before filesystem inspection' {
        { Get-CiPythonRuntimeInventory $payload -DeadlineUtc ([datetime]::UtcNow.AddSeconds(-1)) } |
            Should -Throw '*deadline expired*'
        { Get-CiPythonCacheDecision $cachePlan $payload true -Cancelled { $true } } |
            Should -Throw '*cancelled*'
    }

    It 'inventories only qualified relative file links without following link directories' {
        $linkData = [pscustomobject]@{ FullName = (Join-Path $payload 'python-alias')
            DirectoryName = $payload
            Attributes = [IO.FileAttributes]::ReparsePoint
            LinkType = 'SymbolicLink'
            LinkTarget = $exeRelative
        }
        Mock Get-ChildItem { @($linkData) }
        $linked = Get-CiPythonRuntimeInventory $payload
        $linked.entries.Count | Should -Be 1
        $linked.entries[0].kind | Should -BeExactly 'symlink'
        $linked.entries[0].target | Should -BeExactly $exeRelative
        $linkData.LinkTarget = '../outside'
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw
        $linkData.LinkTarget = 'empty'
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw '*directory*'
    }

    It 'rejects absolute, missing and chained link targets before payload acceptance' {
        $linkData = [pscustomobject]@{ FullName = (Join-Path $payload 'python-alias')
            DirectoryName = $payload
            Attributes = [IO.FileAttributes]::ReparsePoint
            LinkType = 'SymbolicLink'
            LinkTarget = $payload
        }
        Mock Get-ChildItem { @($linkData) }
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw '*relative target*'
        $linkData.LinkTarget = 'missing-target'
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw
        $linkData.LinkTarget = $exeRelative
        Mock Get-Item { [pscustomobject]@{ PSIsContainer = $false
                Attributes = [IO.FileAttributes]::ReparsePoint
            } }
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw '*Chained*'
    }

    It 'rejects hard-link and oversized-file metadata before hashing or execution' {
        $linkData = [pscustomobject]@{ FullName = (Join-Path $payload 'hardlink')
            DirectoryName = $payload
            Attributes = [IO.FileAttributes]::Normal
            LinkType = 'HardLink'
            Length = 1
        }
        Mock Get-ChildItem { @($linkData) }
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw '*hard links*'
        $linkData.LinkType = $null
        $linkData | Add-Member -NotePropertyName PSIsContainer -NotePropertyValue $false
        $linkData.Length = 257MB
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw '*size limit*'
    }

    It 'preserves no-handoff when admission fields are forged' {
        $decision = Get-CiPythonCacheDecision $cachePlan $payload true
        $decision.integrity_verified = $false
        { New-CiPythonCacheReceipt $cachePlan $decision } | Should -Throw '*unverified integrity*'
        $decision.integrity_verified = $true
        $decision.cache_key = 'foreign-key'
        { New-CiPythonCacheReceipt $cachePlan $decision } | Should -Throw '*original admission*'
        $miss = Get-CiPythonCacheDecision $cachePlan (Join-Path $TestDrive 'absent-forged') false
        $miss.cache_hit = $true
        { New-CiPythonCacheReceipt $cachePlan $miss } | Should -Throw '*native miss*'
    }

    It 'rejects actual linked owners and directories without visiting the external target' {
        $outside = Join-Path $TestDrive 'external link target'
        $null = New-Item -ItemType Directory -Path $outside
        [IO.File]::WriteAllText((Join-Path $outside 'retained.txt'), 'unrelated bytes')
        $alias = Join-Path $TestDrive 'linked-owner'
        $linkKind = if ($IsWindows) {
            'Junction'
        }
        else {
            'SymbolicLink'
        }
        $null = New-Item -ItemType $linkKind -Path $alias -Target $payload
        { Get-CiPythonRuntimeInventory $alias } | Should -Throw '*owner or parent*'
        $null = New-Item -ItemType $linkKind -Path (Join-Path $payload 'foreign-directory') -Target $outside
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw '*Directory*'
        [IO.File]::ReadAllText((Join-Path $outside 'retained.txt')) | Should -BeExactly 'unrelated bytes'
    }

    It 'rejects actual hard-linked files and leaves their original bytes intact' {
        $original = Join-Path $payload 'stdlib.txt'
        $null = New-Item -ItemType HardLink -Path (Join-Path $payload 'alias.txt') -Target $original
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw '*hard links*'
        [IO.File]::ReadAllText($original) | Should -BeExactly 'fixture stdlib'
    }

    It 'rejects nonregular device metadata before hashing a payload node' {
        $node = [pscustomobject]@{ FullName = (Join-Path $payload 'device')
            DirectoryName = $payload
            Attributes = [IO.FileAttributes]::Device
            LinkType = $null
            Length = 0
            PSIsContainer = $false
        }
        Mock Get-ChildItem { @($node) }
        { Get-CiPythonRuntimeInventory $payload } | Should -Throw '*Nonregular*'
    }

    It 'does not inherit caller tokens or arbitrary context fields into the cache plan' {
        $cacheContext.SYSTEM_ACCESSTOKEN = 'synthetic-sentinel'
        $seal.password = 'synthetic-sentinel'
        $clean = Get-CiPythonCachePlan $cacheContext $seal $pins
        ($clean | ConvertTo-Json -Depth 8) | Should -Not -Match 'synthetic-sentinel|SYSTEM_ACCESSTOKEN|password'
    }

    It 'requires an exact capability and prefix probe but still withholds environment handoff' {
        $decision = Get-CiPythonCacheDecision $cachePlan $payload true
        $probe = @{ python_version = $pins.python
            architecture = 'x64'
            executable = (Join-Path $payload $exeRelative)
            prefix = $payload
            base_prefix = $payload
            ssl = $true
            sqlite = $true
            venv = $true
            ensurepip = $true
            isolated = $true
            GITHUB_TOKEN = 'synthetic-sentinel'
        }
        $receipt = New-CiPythonCacheReceipt $cachePlan $decision $probe
        $receipt.status | Should -BeExactly 'probe-verified'
        $receipt.probe_verified | Should -BeTrue
        $receipt.handoff_admitted | Should -BeFalse
        ($receipt | ConvertTo-Json -Depth 8) | Should -Not -Match 'synthetic-sentinel|GITHUB_TOKEN'
        foreach ($field in @('ssl', 'sqlite', 'venv', 'ensurepip', 'isolated')) {
            $bad = $probe.Clone()
            $bad[$field] = $false
            { New-CiPythonCacheReceipt $cachePlan $decision $bad } | Should -Throw '*capability contract*'
        }
        foreach ($field in @('prefix', 'base_prefix', 'executable')) {
            $bad = $probe.Clone()
            $bad[$field] = Join-Path $TestDrive 'foreign'
            { New-CiPythonCacheReceipt $cachePlan $decision $bad } | Should -Throw '*capability contract*'
        }
        $probe.python_version = '3.14.7'
        { New-CiPythonCacheReceipt $cachePlan $decision $probe } | Should -Throw '*capability contract*'
    }

    It 'preserves <failure> as a terminal failure without cache saving or handoff' -ForEach @(
        @{ failure = 'acquisition-failed'
            code = 1
        }, @{ failure = 'cancelled'
            code = 130
        },
        @{ failure = 'timed-out'
            code = 1
        }
    ) {
        $decision = Get-CiPythonCacheDecision $cachePlan (Join-Path $TestDrive 'absent-failed') false
        $receipt = New-CiPythonCacheReceipt $cachePlan $decision -Failure $failure
        $receipt.status | Should -BeExactly $failure
        $receipt.exit_code | Should -Be $code
        $receipt.saved | Should -BeFalse
        $receipt.handoff_admitted | Should -BeFalse
    }

    It 'captures all raw generated files without claiming a seal, provider proof or handoff' {
        $cacheContext.capture_id = '1'
        $cacheContext.token = 'synthetic-sentinel'
        $null = New-Item -ItemType Directory -Path (Join-Path $payload '__pycache__')
        [IO.File]::WriteAllText((Join-Path $payload '__pycache__/module.pyc'), 'generated bytes')
        $captured = Get-CiPythonRuntimeCapture $cacheContext $pins $payload
        $captured.inventory.schema_version | Should -Be 2
        $captured.inventory.entries.path | Should -Contain '__pycache__/module.pyc'
        $captured.omitted_paths.Count | Should -Be 0
        $captured.trusted_seal | Should -BeFalse
        $captured.provider_build_verified | Should -BeFalse
        $captured.runtime_probe_verified | Should -BeFalse
        $captured.handoff_admitted | Should -BeFalse
        $captured.saved | Should -BeFalse
        ($captured | ConvertTo-Json -Depth 10) | Should -Not -Match 'synthetic-sentinel'
        [IO.File]::ReadAllText((Join-Path $payload '__pycache__/module.pyc')) | Should -BeExactly 'generated bytes'
    }

    It 'rejects raw capture context <field>=<value>' -ForEach @(
        @{ field = 'event'
            value = 'PullRequest'
        }, @{ field = 'hosted'
            value = $false
        },
        @{ field = 'capture_id'
            value = '3'
        }, @{ field = 'architecture'
            value = 'arm64'
        },
        @{ field = 'executed_commit'
            value = 'HEAD'
        }, @{ field = 'image_family'
            value = 'ubuntu-latest'
        }
    ) {
        $cacheContext.capture_id = '1'
        $cacheContext[$field] = $value
        { Get-CiPythonRuntimeCapture $cacheContext $pins $payload } | Should -Throw '*exact manual*'
    }

    It 'records Unix permission differences only in capture inventory and never mutates files' {
        $captured = Get-CiPythonRuntimeInventory $payload -CaptureOnly
        if ($IsLinux) {
            $file = Join-Path $payload 'stdlib.txt'
            $before = [IO.File]::GetUnixFileMode($file)
            try {
                [IO.File]::SetUnixFileMode($file, $before -bxor [IO.UnixFileMode]::UserExecute)
                $changed = Get-CiPythonRuntimeInventory $payload -CaptureOnly
                $changed.sha256 | Should -Not -BeExactly $captured.sha256
                (Get-CiPythonRuntimeInventory $payload).sha256 | Should -BeExactly $inventory.sha256
            }
            finally {
                [IO.File]::SetUnixFileMode($file, $before)
            }
        }
        else {
            @($captured.entries | Where-Object { $_.Contains('unix_mode') }).Count | Should -Be 0
        }
    }

    It 'captures only the exact Windows absolute alias while strict admission still rejects it' {
        if ($IsWindows) {
            $node = [pscustomobject]@{ FullName = (Join-Path $payload 'python3.exe')
                DirectoryName = $payload
                Attributes = [IO.FileAttributes]::ReparsePoint
                LinkType = 'SymbolicLink'
                LinkTarget = (Join-Path $payload 'python.exe')
                PSIsContainer = $false
            }
            Mock Get-ChildItem { @($node) }
            $captured = Get-CiPythonRuntimeInventory $payload -CaptureOnly
            $captured.entries[0].target | Should -BeExactly $node.LinkTarget.Replace('\', '/')
            { Get-CiPythonRuntimeInventory $payload } | Should -Throw '*relative target*'
            $node.FullName = Join-Path $payload 'foreign-alias.exe'
            { Get-CiPythonRuntimeInventory $payload -CaptureOnly } | Should -Throw '*relative target*'
        }
        else {
            $node = [pscustomobject]@{ FullName = (Join-Path $payload 'python3.exe')
                DirectoryName = $payload
                Attributes = [IO.FileAttributes]::ReparsePoint
                LinkType = 'SymbolicLink'
                LinkTarget = (Join-Path $payload $exeRelative)
                PSIsContainer = $false
                UnixStat = $null
            }
            Mock Get-ChildItem { @($node) }
            { Get-CiPythonRuntimeInventory $payload -CaptureOnly } | Should -Throw '*relative target*'
        }
    }

    It 'rejects missing interpreter and cancellation without promoting raw capture' {
        $cacheContext.capture_id = '1'
        { Get-CiPythonRuntimeCapture $cacheContext $pins $payload -Cancelled { $true } } | Should -Throw '*cancelled*'
        Remove-Item -LiteralPath (Join-Path $payload $exeRelative)
        { Get-CiPythonRuntimeCapture $cacheContext $pins $payload } | Should -Throw
    }

    It 'rejects local entry-point execution before creating capture output or reading a tool cache' {
        $previous = $env:LOTM_RUNTIME_CAPTURE
        try {
            $env:LOTM_RUNTIME_CAPTURE = 'local-fixture'
            { & (Join-Path $repoRoot 'Tools/CI/Capture-PythonRuntime.ps1') } | Should -Throw '*restricted*'
        }
        finally {
            $env:LOTM_RUNTIME_CAPTURE = $previous
        }
    }
}
