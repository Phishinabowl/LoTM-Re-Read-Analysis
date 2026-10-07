# Required portable synthetic ZIP/XML behavior; no local book is opened.
BeforeAll {
    $repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
    $search = Join-Path $repoRoot 'Tools/Commands/Media/Search-Epub.ps1'
}

Describe 'Synthetic EPUB search' -Tag 'Integration' {
    BeforeEach {
        $epub = Join-Path $TestDrive 'synthetic book.epub'
        $stream = [System.IO.File]::Create($epub)
        $archive = [System.IO.Compression.ZipArchive]::new($stream, [System.IO.Compression.ZipArchiveMode]::Create)
        try {
            foreach ($chapter in @(1, 2)) {
                $entry = $archive.CreateEntry("OEBPS/Text/volume_1_chapter_$chapter.xhtml")
                $writer = [System.IO.StreamWriter]::new($entry.Open(), [System.Text.UTF8Encoding]::new($false))
                try {
                    $writer.Write("<html><body><h1>Chapter ${chapter}: Fixture</h1><p>café A+B</p></body></html>")
                }
                finally {
                    $writer.Dispose()
                }
            }
        }
        finally {
            $archive.Dispose()
            $stream.Dispose()
        }
    }

    It 'searches Unicode and literal regex punctuation with chapter filtering' {
        $rows = @((& $search -Root $repoRoot -EpubPath $epub -Pattern 'café|A+B' -EndChapter 1 -Json) | ConvertFrom-Json)
        @($rows.term | Sort-Object -Unique) | Should -Be @('A+B', 'café')
        @($rows.chapter | Sort-Object -Unique) | Should -Be @(1)
    }

    It 'rejects malformed ZIP input without rewriting it' {
        $bad = Join-Path $TestDrive 'broken.epub'
        [System.IO.File]::WriteAllText($bad, 'not a zip')
        { & $search -Root $repoRoot -EpubPath $bad -Pattern 'fixture' } | Should -Throw
        [System.IO.File]::ReadAllText($bad) | Should -BeExactly 'not a zip'
    }
}
