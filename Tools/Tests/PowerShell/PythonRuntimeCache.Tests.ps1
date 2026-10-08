BeforeAll {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
    . (Join-Path $repoRoot 'Tools/CI/PythonRuntimeCache.ps1')
    $pins = Get-Content -LiteralPath (Join-Path $repoRoot 'Tools/CI/Data/runtime-versions.json') -Raw |
        ConvertFrom-Json -AsHashtable
}

Describe 'External Linux release reference admission without execution' -Tag Unit {
    BeforeEach {
        $owner = Join-Path $TestDrive ([guid]::NewGuid().ToString('N'))
        $null = [IO.Directory]::CreateDirectory($owner)
        $specPath = Join-Path $owner 'spec.json'
        $referencePath = Join-Path $owner 'python-linux-3.14.8-reference.json'
        $spec = Get-Content (Join-Path $repoRoot 'Tools/CI/Data/python-linux-release-reference-spec.json') -Raw | ConvertFrom-Json -AsHashtable
        $rows = @([ordered]@{ path = 'bin'
                kind = 'directory'
                unix_mode = 493
            },
            [ordered]@{ path = 'bin/python3.14'
                kind = 'file'
                bytes = 3
                sha256 = ('a' * 64)
                unix_mode = 493
            },
            [ordered]@{ path = 'python'
                kind = 'symlink'
                target = './bin/python3.14'
            })
        $reference = [ordered]@{ contract = 'ci-python-linux-release-reference'
            schema_version = 1
            identity = $spec.identity.Clone()
            inventory = [ordered]@{ schema_version = 3
                root_unix_mode = 493
                entries = $rows
                sha256 = ''
            }
        }
        function Write-ReferenceFixture {
            $frame = [ordered]@{ root_unix_mode = $reference.inventory.root_unix_mode
                entries = $reference.inventory.entries
            }
            $bytes = [Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $frame -Depth 8 -Compress))
            $reference.inventory.sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
            $spec.expected_inventory_sha256 = $reference.inventory.sha256
            [IO.File]::WriteAllText($referencePath, (ConvertTo-Json -InputObject $reference -Depth 10), [Text.UTF8Encoding]::new($false))
            $spec.reference_sha256 = (Get-FileHash $referencePath).Hash.ToLowerInvariant()
            [IO.File]::WriteAllText($specPath, (ConvertTo-Json -InputObject $spec -Depth 10), [Text.UTF8Encoding]::new($false))
        }
        Write-ReferenceFixture
    }

    It 'admits the independently derived production reference on either implementation-test host' {
        $actual = Get-CiPythonLinuxReleaseReference $pins
        $actual.inventory.entries.Count | Should -Be 3040
        $actual.inventory.sha256 | Should -BeExactly '5e88f33c1f23523d9099daf29854fb12536ec3d0e6e5b3b7e212993503ec8794'
        $actual.reference_sha256 | Should -BeExactly '95e112863137211040344814033dca6a6c0156bc51546022643108f78ee165c6'
    }

    It 'admits a complete fixture and keeps exact declared identity' {
        $actual = Read-CiPythonLinuxReleaseReference $specPath $referencePath $pins
        $actual.inventory.entries.Count | Should -Be 3
        $actual.identity.normalization | Should -BeExactly 'native-core-v2-linux-release-modes'
    }

    It 'rejects <mutation> before any runtime operation' -ForEach @(
        @{ mutation = 'file-hash' }, @{ mutation = 'identity' }, @{ mutation = 'bool-schema' },
        @{ mutation = 'bool-size' }, @{ mutation = 'mode' }, @{ mutation = 'extra-field' },
        @{ mutation = 'missing-parent' }, @{ mutation = 'duplicate-path' }, @{ mutation = 'unordered' },
        @{ mutation = 'escape' }, @{ mutation = 'directory-link' }, @{ mutation = 'duplicate-json' },
        @{ mutation = 'inventory-hash' }, @{ mutation = 'version' }) {
        switch ($mutation) {
            'file-hash' {
                $spec.reference_sha256 = '0' * 64
            }
            'identity' {
                $reference.identity.gil = 'disabled'
                Write-ReferenceFixture
            }
            'bool-schema' {
                $reference.schema_version = $true
                Write-ReferenceFixture
            }
            'bool-size' {
                $reference.inventory.entries[1].bytes = $true
                Write-ReferenceFixture
            }
            'mode' {
                $reference.inventory.entries[1].unix_mode = 511
                Write-ReferenceFixture
            }
            'extra-field' {
                $reference.inventory.entries[1].unknown = 0
                Write-ReferenceFixture
            }
            'missing-parent' {
                $reference.inventory.entries = @($reference.inventory.entries | Select-Object -Skip 1)
                Write-ReferenceFixture
            }
            'duplicate-path' {
                $reference.inventory.entries[1].path = 'bin'
                Write-ReferenceFixture
            }
            'unordered' {
                [Array]::Reverse($reference.inventory.entries)
                Write-ReferenceFixture
            }
            'escape' {
                $reference.inventory.entries[2].target = '../outside'
                Write-ReferenceFixture
            }
            'directory-link' {
                $reference.inventory.entries[2].target = 'bin'
                Write-ReferenceFixture
            }
            'duplicate-json' {
                $text = [IO.File]::ReadAllText($referencePath).Replace('"contract":', '"schema_version": 1, "contract":')
                [IO.File]::WriteAllText($referencePath, $text, [Text.UTF8Encoding]::new($false))
                $spec.reference_sha256 = (Get-FileHash $referencePath).Hash.ToLowerInvariant()
            }
            'inventory-hash' {
                $spec.expected_inventory_sha256 = '0' * 64
            }
            'version' {
                $spec.identity.python = '3.14.7'
            }
        }
        [IO.File]::WriteAllText($specPath, (ConvertTo-Json -InputObject $spec -Depth 10), [Text.UTF8Encoding]::new($false))
        { Read-CiPythonLinuxReleaseReference $specPath $referencePath $pins } | Should -Throw
    }

    It 'retains cancellation and expired-deadline refusal' {
        { Read-CiPythonLinuxReleaseReference $specPath $referencePath $pins -Cancelled { $true } } | Should -Throw '*cancelled*'
        { Read-CiPythonLinuxReleaseReference $specPath $referencePath $pins -DeadlineUtc ([datetime]::UtcNow.AddSeconds(-1)) } | Should -Throw '*expired*'
    }

    It 'rejects a linked reference parent before reading its bytes' {
        $link = Join-Path $TestDrive ('linked-' + [guid]::NewGuid().ToString('N'))
        $null = [IO.Directory]::CreateSymbolicLink($link, $owner)
        { Read-CiPythonLinuxReleaseReference $specPath (Join-Path $link $spec.reference_file) $pins } | Should -Throw '*link*'
    }

    It 'rejects invalid UTF-8 bytes' {
        [IO.File]::WriteAllBytes($referencePath, [byte[]]@(255, 254, 255))
        { Read-CiPythonLinuxReleaseReference $specPath $referencePath $pins } | Should -Throw
    }

    It 'rejects oversized reference input before JSON parsing' {
        [IO.File]::WriteAllBytes($referencePath, [byte[]]::new(2MB + 1))
        { Read-CiPythonLinuxReleaseReference $specPath $referencePath $pins } | Should -Throw '*bounded*'
    }

    It 'observes cancellation during nested reference parsing' {
        $state = @{ calls = 0 }
        $cancel = { $state.calls++
            $state.calls -gt 5 }.GetNewClosure()
        { Read-CiPythonLinuxReleaseReference $specPath $referencePath $pins -Cancelled $cancel } | Should -Throw '*cancelled*'
        $state.calls | Should -BeGreaterThan 5
    }
}

Describe 'Release-mode projection from complete admitted metadata' -Tag Unit {
    BeforeEach {
        $rows = @([ordered]@{ path = 'bin'
                kind = 'directory'
                unix_mode = 493
            },
            [ordered]@{ path = 'bin/python3.14'
                kind = 'file'
                bytes = 3
                sha256 = ('a' * 64)
                unix_mode = 493
            },
            [ordered]@{ path = 'python'
                kind = 'symlink'
                target = './bin/python3.14'
            })
        $frame = [ordered]@{ root_unix_mode = 493
            entries = $rows
        }
        $encoded = [Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $frame -Depth 7 -Compress))
        $digest = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($encoded)).ToLowerInvariant()
        $reference = [pscustomobject]@{ identity = @{ python = $pins.python
                normalization = 'native-core-v2-linux-release-modes'
            }
            reference_sha256 = ('b' * 64)
            inventory = [ordered]@{ schema_version = 3
                root_unix_mode = 493
                entries = $rows
                sha256 = $digest
            }
        }
        $projection = [pscustomobject]@{ normalization = 'native-core-v1'
            schema_version = 3
            entries = @(
                $rows | ForEach-Object { $copy = [ordered]@{}
                    foreach ($key in $_.Keys) {
                        $copy[$key] = $_[$key]
                    }
                    $copy })
            omitted = @()
            root_unix_mode = 493
            sha256 = $digest
        }
    }

    It 'normalizes <variant> permissions without modifying input metadata' -ForEach @(
        @{ variant = 'exact'
            changes = 0
        }, @{ variant = 'world-writable'
            changes = 2
        }, @{ variant = 'mixed'
            changes = 1
        }) {
        if ($variant -eq 'world-writable') {
            $projection.entries[0].unix_mode = 511
            $projection.entries[1].unix_mode = 511
        }
        if ($variant -eq 'mixed') {
            $projection.entries[1].unix_mode = 511
        }
        $before = ConvertTo-Json -InputObject $projection -Depth 8 -Compress
        $result = ConvertTo-CiPythonReleaseModeProjection $projection $reference 511 $pins
        $result.sha256 | Should -BeExactly $digest
        $result.mode_changes.Count | Should -Be $changes
        $result.source_root_mode | Should -Be 511
        $result.root_unix_mode | Should -Be 493
        (ConvertTo-Json -InputObject $projection -Depth 8 -Compress) | Should -BeExactly $before
    }

    It 'refuses <mutation> retained metadata' -ForEach @(
        @{ mutation = 'bytes' }, @{ mutation = 'size' }, @{ mutation = 'kind' }, @{ mutation = 'extra' },
        @{ mutation = 'missing' }, @{ mutation = 'link' }, @{ mutation = 'mode' }, @{ mutation = 'privileged' },
        @{ mutation = 'bool-mode' }, @{ mutation = 'root' }, @{ mutation = 'version' }, @{ mutation = 'digest' }) {
        $rootMode = 493
        switch ($mutation) {
            'bytes' {
                $projection.entries[1].sha256 = 'c' * 64
            }
            'size' {
                $projection.entries[1].bytes = 4
            }
            'kind' {
                $projection.entries[1].kind = 'symlink'
            }
            'extra' {
                $projection.entries[1].unexpected = 0
            }
            'missing' {
                $projection.entries = @($projection.entries | Select-Object -Skip 1)
            }
            'link' {
                $projection.entries[2].target = 'bin/other'
            }
            'mode' {
                $projection.entries[1].unix_mode = 420
            }
            'privileged' {
                $projection.entries[1].unix_mode = 2541
            }
            'bool-mode' {
                $projection.entries[1].unix_mode = $true
            }
            'root' {
                $rootMode = 448
            }
            'version' {
                $reference.identity.python = '3.14.7'
            }
            'digest' {
                $reference.inventory.sha256 = '0' * 64
            }
        }
        { ConvertTo-CiPythonReleaseModeProjection $projection $reference $rootMode $pins } | Should -Throw
    }

    It 'honors projection cancellation and deadline without producing metadata' {
        { ConvertTo-CiPythonReleaseModeProjection $projection $reference 493 $pins -Cancelled { $true } } | Should -Throw '*cancelled*'
        { ConvertTo-CiPythonReleaseModeProjection $projection $reference 493 $pins -DeadlineUtc ([datetime]::UtcNow.AddSeconds(-1)) } | Should -Throw '*expired*'
    }
}

Describe 'Private normalized runtime candidates without execution' -Tag Unit {
    BeforeEach {
        $workspace = Join-Path $TestDrive ('candidate workspace ' + [guid]::NewGuid().ToString('N'))
        $source = Join-Path $workspace 'native-source'
        $destination = Join-Path $workspace 'candidate'
        $library = if ($IsWindows) {
            'Lib'
        }
        else {
            'lib/python3.14'
        }
        $exe = if ($IsWindows) {
            'python.exe'
        }
        else {
            'bin/python3.14'
        }
        $pip = "$library/site-packages/pip"
        $pipMetadata = "$library/site-packages/pip-26.2.1.dist-info"
        $files = @{
            $exe = 'dummy interpreter, never executable'
            "$library/ensurepip/_bundled/pip-fixture.whl" = 'bundled fixture wheel'
            "$library/module.py" = 'authoritative source'
            "$library/__pycache__/module.cpython-314.pyc" = 'generated bytecode'
            "$library/__pycache__/sourceless.cpython-314.pyc" = 'required sourceless input'
            "$library/other.py" = 'more source'
            "$library/generated/__pycache__/child.cpython-314.pyc" = 'generated child'
            "$library/generated/child.py" = 'child source'
            "$pip/__init__.py" = 'native pip code'
            "$pipMetadata/RECORD" = 'native pip metadata'
        }
        foreach ($entry in $files.GetEnumerator()) {
            $path = Join-Path $source $entry.Key
            $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path))
            [IO.File]::WriteAllText($path, $entry.Value)
        }
        $script = if ($IsWindows) {
            'Scripts/pip.exe'
        }
        else {
            'bin/pip'
        }
        $path = Join-Path $source $script
        $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path))
        [IO.File]::WriteAllText($path, 'native pip launcher')
        $null = [IO.Directory]::CreateDirectory((Join-Path $source "$library/preexisting/__pycache__"))
        $original = Get-CiPythonRuntimeInventory $source -CaptureOnly
    }

    It 'builds a fresh verified candidate, preserves source and retains sourceless inputs and ensurepip' {
        $result = New-CiPythonRuntimeCandidate $source $workspace $destination $pins
        $result.status | Should -BeExactly 'candidate-complete'
        $result.inventory.schema_version | Should -Be 3
        $result.trusted_seal | Should -BeFalse
        $result.handoff_admitted | Should -BeFalse
        $result.saved | Should -BeFalse
        $result.inventory.entries.path | Should -Contain "$library/__pycache__/sourceless.cpython-314.pyc"
        $result.inventory.entries.path | Should -Contain "$library/ensurepip/_bundled/pip-fixture.whl"
        $result.inventory.entries.path | Should -Contain "$library/preexisting/__pycache__"
        $result.inventory.entries.path | Should -Not -Contain "$library/generated/__pycache__"
        $result.inventory.entries.path | Should -Not -Contain "$library/__pycache__/module.cpython-314.pyc"
        $result.inventory.entries.path | Should -Not -Contain "$pip/__init__.py"
        $result.inventory.entries.path | Should -Not -Contain "$pipMetadata/RECORD"
        $result.inventory.entries.path | Should -Not -Contain $script
        (Get-CiPythonRuntimeInventory $source -CaptureOnly).sha256 | Should -BeExactly $original.sha256
        (Get-Content -LiteralPath ($destination + '.candidate.json') -Raw | ConvertFrom-Json).status | Should -BeExactly 'candidate-complete'
    }

    It 'produces the same sealed entries after generated bytecode and native pip outputs change' {
        $first = New-CiPythonRuntimeCandidate $source $workspace $destination $pins
        [IO.File]::WriteAllText((Join-Path $source "$library/__pycache__/module.cpython-314.pyc"), 'different generated bytes')
        [IO.File]::WriteAllText((Join-Path $source "$pip/__init__.py"), 'different native base pip')
        [IO.File]::WriteAllText((Join-Path $source $script), 'different launcher bytes')
        $second = New-CiPythonRuntimeCandidate $source $workspace (Join-Path $workspace 'second') $pins
        $second.inventory.sha256 | Should -BeExactly $first.inventory.sha256
        $second.source_sha256 | Should -Not -BeExactly $first.source_sha256
    }

    It 'keeps retained source changes visible to the candidate seal' {
        $first = New-CiPythonRuntimeCandidate $source $workspace $destination $pins
        [IO.File]::WriteAllText((Join-Path $source "$library/module.py"), 'changed canonical runtime source')
        $second = New-CiPythonRuntimeCandidate $source $workspace (Join-Path $workspace 'second') $pins
        $second.inventory.sha256 | Should -Not -BeExactly $first.inventory.sha256
    }

    It 'rejects existing and overlapping owners without overwriting their bytes' {
        $null = [IO.Directory]::CreateDirectory($destination)
        [IO.File]::WriteAllText((Join-Path $destination 'retained.txt'), 'user bytes')
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins } | Should -Throw '*fresh*'
        [IO.File]::ReadAllText((Join-Path $destination 'retained.txt')) | Should -BeExactly 'user bytes'
        { New-CiPythonRuntimeCandidate $source $workspace (Join-Path $source 'nested') $pins } | Should -Throw '*overlap*'
        { New-CiPythonRuntimeCandidate $source $workspace (Join-Path $TestDrive 'outside') $pins } | Should -Throw
        (Get-CiPythonRuntimeInventory $source -CaptureOnly).sha256 | Should -BeExactly $original.sha256
    }

    It 'rejects <missing> required candidate inputs before creating an output owner' -ForEach @(
        @{ missing = 'interpreter' }, @{ missing = 'ensurepip' }, @{ missing = 'pip-metadata' }
    ) {
        $file = switch ($missing) {
            interpreter {
                $exe
            }
            ensurepip {
                "$library/ensurepip/_bundled/pip-fixture.whl"
            }
            'pip-metadata' {
                "$pipMetadata/RECORD"
            }
        }
        Remove-Item -LiteralPath (Join-Path $source $file)
        if ($missing -eq 'pip-metadata') {
            Remove-Item -LiteralPath (Join-Path $source $pipMetadata)
        }
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins } | Should -Throw
        Test-Path -LiteralPath $destination | Should -BeFalse
    }

    It 'retains partial failure evidence without promotion and refuses to reuse that owner' {
        Mock Get-CiPythonRuntimeInventory {
            param($Root, $CaptureOnly, $SealModes)
            if ($SealModes) {
                throw 'synthetic post-copy inventory failure'
            }
            $original
        }
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins } | Should -Throw '*post-copy*'
        $receipt = Get-Content -LiteralPath ($destination + '.candidate.json') -Raw | ConvertFrom-Json
        $receipt.status | Should -BeExactly 'candidate-incomplete'
        $receipt.handoff_admitted | Should -BeFalse
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins } | Should -Throw '*fresh*'
    }

    It 'rejects cancellation and expired deadlines before creating a candidate' {
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -Cancelled { $true } } | Should -Throw '*cancelled*'
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -DeadlineUtc ([datetime]::UtcNow.AddSeconds(-1)) } | Should -Throw '*deadline*'
        Test-Path -LiteralPath $destination | Should -BeFalse
    }

    It 'seals Unix file and root permissions while keeping the original content-only contract separate' {
        $first = New-CiPythonRuntimeCandidate $source $workspace $destination $pins
        if ($IsLinux) {
            $file = Join-Path $destination $exe
            $mode = [IO.File]::GetUnixFileMode($file)
            [IO.File]::SetUnixFileMode($file, $mode -bxor [IO.UnixFileMode]::UserExecute)
            (Get-CiPythonRuntimeInventory $destination -SealModes).sha256 | Should -Not -BeExactly $first.inventory.sha256
            [IO.File]::SetUnixFileMode($file, $mode)
            [IO.File]::SetUnixFileMode($destination, [IO.UnixFileMode]448)
            (Get-CiPythonRuntimeInventory $destination -SealModes).sha256 | Should -Not -BeExactly $first.inventory.sha256
        }
        else {
            $first.inventory.root_unix_mode | Should -BeNullOrEmpty
        }
        { Get-CiPythonRuntimeInventory $source -SealModes -CaptureOnly } | Should -Throw '*separate*'
    }

    It 'recreates actual native file links without following or editing the source owner' {
        $alias = if ($IsWindows) {
            'python3.exe'
        }
        else {
            'bin/python'
        }
        $target = if ($IsWindows) {
            Join-Path $source $exe
        }
        else {
            'python3.14'
        }
        $null = [IO.File]::CreateSymbolicLink((Join-Path $source $alias), $target)
        $before = Get-CiPythonRuntimeInventory $source -CaptureOnly
        $built = New-CiPythonRuntimeCandidate $source $workspace $destination $pins
        (Get-Item -LiteralPath (Join-Path $destination $alias)).LinkTarget | Should -BeExactly ([IO.Path]::GetFileName($exe))
        (Get-CiPythonRuntimeInventory $source -CaptureOnly).sha256 | Should -BeExactly $before.sha256
        $built.status | Should -BeExactly 'candidate-complete'
    }

    It 'rejects an incomplete RECORD even when the pip distribution directory remains' {
        Remove-Item -LiteralPath (Join-Path $source "$pipMetadata/RECORD")
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins } | Should -Throw '*complete observed*'
        Test-Path -LiteralPath $destination | Should -BeFalse
    }

    It 'retains ambiguous native distributions as a qualification failure rather than omitting them broadly' {
        $null = [IO.Directory]::CreateDirectory((Join-Path $source "$library/site-packages/pip-26.2.dev1.dist-info"))
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins } | Should -Throw '*complete observed*'
        Test-Path -LiteralPath $destination | Should -BeFalse
    }

    It 'detects actual retained-file corruption during construction and leaves an incomplete receipt' {
        $changed = Join-Path $destination "$library/module.py"
        $callback = { if (Test-Path -LiteralPath $changed) {
                [IO.File]::WriteAllText($changed, 'injected corruption')
            }
            $false }
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -Cancelled $callback } | Should -Throw '*differs*'
        (Get-Content -LiteralPath ($destination + '.candidate.json') -Raw | ConvertFrom-Json).status | Should -BeExactly 'candidate-incomplete'
        (Get-CiPythonRuntimeInventory $source -CaptureOnly).sha256 | Should -BeExactly $original.sha256
    }

    It 'retains mid-copy cancellation evidence without claiming a completed candidate' {
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -Cancelled { Test-Path -LiteralPath $destination } } |
            Should -Throw '*cancelled*'
        $receipt = Get-Content -LiteralPath ($destination + '.candidate.json') -Raw | ConvertFrom-Json
        $receipt.status | Should -BeExactly 'candidate-incomplete'
        $receipt.handoff_admitted | Should -BeFalse
        (Get-CiPythonRuntimeInventory $source -CaptureOnly).sha256 | Should -BeExactly $original.sha256
    }

    It 'copies qualified release modes on Linux and refuses that flag on Windows' {
        if (-not $IsLinux) {
            { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -LinuxReleaseModes } | Should -Throw '*Linux-only*'
            Test-Path $destination | Should -BeFalse
            return
        }
        $native = Get-CiPythonRuntimeInventory $source -CaptureOnly
        $expected = Get-CiPythonCandidateProjection $native $source $pins
        $fixtureReference = [pscustomobject]@{ identity = @{ python = $pins.python
                normalization = 'native-core-v2-linux-release-modes'
            }
            reference_sha256 = ('b' * 64)
            inventory = [ordered]@{ schema_version = 3
                root_unix_mode = 493
                entries = $expected.entries
                sha256 = $expected.sha256
            }
        }
        Mock Get-CiPythonLinuxReleaseReference { $fixtureReference }
        foreach ($row in $native.entries | Where-Object kind -NE 'symlink') {
            [IO.File]::SetUnixFileMode((Join-Path $source $row.path), [IO.UnixFileMode]511)
        }
        [IO.File]::SetUnixFileMode($source, [IO.UnixFileMode]511)
        $before = Get-CiPythonRuntimeInventory $source -CaptureOnly
        $result = New-CiPythonRuntimeCandidate $source $workspace $destination $pins -LinuxReleaseModes
        $result.schema_version | Should -Be 2
        $result.inventory.sha256 | Should -BeExactly $expected.sha256
        $result.mode_changes.Count | Should -BeGreaterThan 0
        $result.source_root_mode | Should -Be 511
        $result.reference.sha256 | Should -BeExactly ('b' * 64)
        $result.saved | Should -BeFalse
        $result.handoff_admitted | Should -BeFalse
        (Get-CiPythonRuntimeInventory $source -CaptureOnly).sha256 | Should -BeExactly $before.sha256
        [int][IO.File]::GetUnixFileMode($source) | Should -Be 511
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -LinuxReleaseModes } | Should -Throw '*fresh*'
    }

    It 'retains Linux v2 cancellation evidence or rejects the flag on Windows' {
        if (-not $IsLinux) {
            { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -LinuxReleaseModes } | Should -Throw '*Linux-only*'
            return
        }
        $expected = Get-CiPythonCandidateProjection $original $source $pins
        $fixtureReference = [pscustomobject]@{ identity = @{ python = $pins.python
                normalization = 'native-core-v2-linux-release-modes'
            }
            reference_sha256 = ('b' * 64)
            inventory = [ordered]@{ schema_version = 3
                root_unix_mode = 493
                entries = $expected.entries
                sha256 = $expected.sha256
            }
        }
        Mock Get-CiPythonLinuxReleaseReference { $fixtureReference }
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -LinuxReleaseModes -Cancelled { Test-Path $destination } } |
            Should -Throw '*cancelled*'
        $failure = Get-Content ($destination + '.candidate.json') -Raw | ConvertFrom-Json
        $failure.schema_version | Should -Be 2
        $failure.normalization | Should -BeExactly 'native-core-v2-linux-release-modes'
        $failure.reference.identity.normalization | Should -BeExactly 'native-core-v2-linux-release-modes'
        $failure.status | Should -BeExactly 'candidate-incomplete'
        $failure.saved | Should -BeFalse
        (Get-CiPythonRuntimeInventory $source -CaptureOnly).sha256 | Should -BeExactly $original.sha256
    }

    It 'detects source-root mutation during Linux release copying or refuses the flag on Windows' {
        if (-not $IsLinux) {
            { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -LinuxReleaseModes } | Should -Throw '*Linux-only*'
            return
        }
        $expected = Get-CiPythonCandidateProjection $original $source $pins
        $fixtureReference = [pscustomobject]@{ identity = @{ python = $pins.python
                normalization = 'native-core-v2-linux-release-modes'
            }
            reference_sha256 = ('b' * 64)
            inventory = [ordered]@{ schema_version = 3
                root_unix_mode = 493
                entries = $expected.entries
                sha256 = $expected.sha256
            }
        }
        Mock Get-CiPythonLinuxReleaseReference { $fixtureReference }
        $copiedExe = Join-Path $destination $exe
        $callback = {
            if (Test-Path $copiedExe) {
                [IO.File]::SetUnixFileMode($source, [IO.UnixFileMode]448)
            }
            $false
        }
        { New-CiPythonRuntimeCandidate $source $workspace $destination $pins -LinuxReleaseModes -Cancelled $callback } | Should -Throw '*differs*'
        $failure = Get-Content ($destination + '.candidate.json') -Raw | ConvertFrom-Json
        $failure.status | Should -BeExactly 'candidate-incomplete'
        $failure.handoff_admitted | Should -BeFalse
    }
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

    It 'validates the selected exact native prefix with a trailing separator and platform case rules' {
        $tools = Join-Path $TestDrive 'private tools owner'
        $expected = [IO.Path]::GetFullPath((Join-Path $tools "Python/$($pins.python)/x64"))
        (Get-CiPythonNativeCaptureRoot $tools ($expected + [IO.Path]::DirectorySeparatorChar) $pins) |
            Should -BeExactly $expected
        if ($IsWindows) {
            (Get-CiPythonNativeCaptureRoot $tools $expected.ToUpperInvariant() $pins) | Should -BeExactly $expected
        }
        else {
            { Get-CiPythonNativeCaptureRoot $tools $expected.ToUpperInvariant() $pins } | Should -Throw '*differs*'
        }
    }

    It 'rejects incomplete native output <location>' -ForEach @(
        @{ location = '' }, @{ location = '$(pythonLocation)' },
        @{ location = '$(NativePython.pythonLocation)' }, @{ location = 'relative/python' }
    ) {
        { Get-CiPythonNativeCaptureRoot $TestDrive $location $pins } | Should -Throw '*empty, unresolved*'
    }

    It 'rejects a different native patch and a linked selected prefix owner' {
        $tools = Join-Path $TestDrive 'tool-cache fixture'
        $wrong = Join-Path $tools 'Python/3.14.7/x64'
        { Get-CiPythonNativeCaptureRoot $tools $wrong $pins } | Should -Throw '*differs*'
        $alias = Join-Path $TestDrive 'selected-link'
        $kind = if ($IsWindows) {
            'Junction'
        }
        else {
            'SymbolicLink'
        }
        $null = New-Item -ItemType $kind -Path $alias -Target $payload
        { Get-CiPythonNativeCaptureRoot $tools $alias $pins } | Should -Throw '*owner or parent*'
    }
}
