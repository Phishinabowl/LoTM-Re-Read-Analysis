# Required Windows-only System.Drawing crop behavior; no real artwork is read.
BeforeAll {
    if (-not $IsWindows) {
        throw 'System.Drawing image coverage requires Windows; catalog admission must reject this host.'
    }
    $repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
    $edit = Join-Path $repoRoot 'Tools/Commands/Media/Edit-Image.ps1'
    Add-Type -AssemblyName System.Drawing
}

Describe 'Synthetic Windows image crop' -Tag 'Integration' {
    BeforeEach {
        $fixture = Join-Path $TestDrive ([guid]::NewGuid().ToString('N'))
        $null = New-Item -ItemType Directory -Path $fixture
        $source = Join-Path $fixture 'source.png'
        $output = Join-Path $fixture 'crop.png'
        $bitmap = [System.Drawing.Bitmap]::new(4, 3)
        try {
            $bitmap.SetPixel(1, 1, [System.Drawing.Color]::Red)
            $bitmap.Save($source, [System.Drawing.Imaging.ImageFormat]::Png)
        }
        finally {
            $bitmap.Dispose()
        }
        $originalHash = (Get-FileHash -LiteralPath $source).Hash
    }

    It 'preserves pixels and source while enforcing overwrite protection' {
        $null = & $edit -Root $repoRoot -SourceImage $source -OutputImage $output -X 1 -Y 1 -Width 2 -Height 1
        $image = [System.Drawing.Bitmap]::new($output)
        try {
            $image.Width | Should -Be 2
            $image.Height | Should -Be 1
            $image.GetPixel(0, 0).ToArgb() | Should -Be ([System.Drawing.Color]::Red.ToArgb())
        }
        finally {
            $image.Dispose()
        }
        $hash = (Get-FileHash -LiteralPath $output).Hash
        { & $edit -Root $repoRoot -SourceImage $source -OutputImage $output -X 0 -Y 0 -Width 1 -Height 1 } | Should -Throw
        (Get-FileHash -LiteralPath $output).Hash | Should -BeExactly $hash
        $null = & $edit -Root $repoRoot -SourceImage $source -OutputImage $output -X 0 -Y 0 -Width 1 -Height 1 -Force
        (Get-FileHash -LiteralPath $source).Hash | Should -BeExactly $originalHash
    }

    It 'rejects out-of-bounds crops without producing an output' {
        { & $edit -Root $repoRoot -SourceImage $source -OutputImage $output -X 3 -Y 2 -Width 2 -Height 2 } | Should -Throw
        Test-Path -LiteralPath $output | Should -BeFalse
    }
}
