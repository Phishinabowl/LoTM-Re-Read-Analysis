param(
  [string]$EpubPath = "Source/Lord of Mysteries - Book 1.epub",
  [string]$OutputDir = ".tmp/epub-images",
  [ValidateRange(1, 9999)]
  [int]$StartImageNumber = 1,
  [ValidateRange(1, 9999)]
  [int]$EndImageNumber = 9999,
  [int[]]$Volume,
  [ValidateSet("Cover", "FrontMatter", "VolumeCover", "EndOfVolume", "Pathways", "Characters", "Locations", "Artwork", "Map", "BackCover", "Other", "All")]
  [string[]]$ImageType = @("All"),
  [string]$EntryNamePattern,
  [string]$ImageNamePattern,
  [switch]$Extract,
  [switch]$Json
)

$ErrorActionPreference = "Stop"

if ($StartImageNumber -gt $EndImageNumber) {
  throw "StartImageNumber cannot be greater than EndImageNumber."
}

if (-not (Test-Path $EpubPath)) {
  throw "EPUB not found: $EpubPath"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Get-RelativePath {
  param(
    [string]$BasePath,
    [string]$RelativePath
  )

  $baseDirectory = Split-Path $BasePath -Parent
  $combined = Join-Path $baseDirectory $RelativePath
  $parts = New-Object 'System.Collections.Generic.List[string]'

  foreach ($part in ($combined -split '[\\/]+')) {
    if ([string]::IsNullOrWhiteSpace($part) -or $part -eq '.') {
      continue
    }

    if ($part -eq '..') {
      if ($parts.Count -gt 0) {
        $parts.RemoveAt($parts.Count - 1)
      }
      continue
    }

    $parts.Add($part)
  }

  return ($parts -join '/')
}

function Get-XhtmlTitle {
  param([string]$Xhtml)

  $match = [regex]::Match($Xhtml, '<title>(.*?)</title>', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
  if ($match.Success) {
    return [System.Net.WebUtility]::HtmlDecode($match.Groups[1].Value.Trim())
  }

  return $null
}

function Get-ImgTags {
  param([string]$Xhtml)

  $matches = [regex]::Matches($Xhtml, '<img\b[^>]*>', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
  foreach ($match in $matches) {
    $tag = $match.Value
    $srcMatch = [regex]::Match($tag, '\bsrc\s*=\s*"([^"]+)"', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if (-not $srcMatch.Success) {
      continue
    }

    $altMatch = [regex]::Match($tag, '\balt\s*=\s*"([^"]*)"', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    [pscustomobject]@{
      src = [System.Net.WebUtility]::HtmlDecode($srcMatch.Groups[1].Value)
      alt = if ($altMatch.Success) { [System.Net.WebUtility]::HtmlDecode($altMatch.Groups[1].Value) } else { $null }
    }
  }
}

function Get-VolumeFromHref {
  param(
    [string]$Href,
    [string]$Title,
    [Nullable[int]]$CurrentVolume
  )

  $leaf = Split-Path $Href -Leaf
  if ($leaf -match '^(side_stories.*|artwork\d*|world_map|back_cover)\.xhtml$') {
    return $null
  }

  $fileMatch = [regex]::Match($Href, 'volume_(\d+)_')
  if ($fileMatch.Success) {
    return [int]$fileMatch.Groups[1].Value
  }

  $titleMatch = [regex]::Match($Title, '^Volume\s+(\d+):')
  if ($titleMatch.Success) {
    return [int]$titleMatch.Groups[1].Value
  }

  return $CurrentVolume
}

function Get-ImageType {
  param(
    [string]$Href,
    [string]$Title,
    [string]$Alt
  )

  $leaf = Split-Path $Href -Leaf

  if ($leaf -eq 'cover.xhtml') { return "Cover" }
  if ($leaf -eq 'back_cover.xhtml') { return "BackCover" }
  if ($leaf -eq 'world_map.xhtml') { return "Map" }
  if ($leaf -in @('copyright.xhtml', 'foreword.xhtml', 'synopsis.xhtml', 'table_of_contents.xhtml')) { return "FrontMatter" }
  if ($Title -match '^Volume\s+\d+:') { return "VolumeCover" }
  if ($leaf -match 'end_of') { return "EndOfVolume" }
  if ($Title -eq 'Pathways Guide' -or $leaf -match 'pathways') { return "Pathways" }
  if ($Title -eq 'Characters' -or $leaf -match 'character|tarot') { return "Characters" }
  if ($Title -eq 'Locations' -or $leaf -match 'location') { return "Locations" }
  if ($Title -eq 'Image Gallery' -or $Title -eq 'Artwork' -or $leaf -match 'image_gallery|artwork') { return "Artwork" }

  return "Other"
}

function Test-SelectedImage {
  param($Image)

  if ($Image.image_number -lt $StartImageNumber -or $Image.image_number -gt $EndImageNumber) {
    return $false
  }

  $selectedTypes = if ($ImageType -contains "All") {
    @("Cover", "FrontMatter", "VolumeCover", "EndOfVolume", "Pathways", "Characters", "Locations", "Artwork", "Map", "BackCover", "Other")
  } else {
    $ImageType
  }

  if ($selectedTypes -notcontains $Image.image_type) {
    return $false
  }

  if ($Volume -and ($null -eq $Image.volume -or $Volume -notcontains $Image.volume)) {
    return $false
  }

  if (-not [string]::IsNullOrWhiteSpace($EntryNamePattern)) {
    if ($Image.xhtml_path -notlike $EntryNamePattern -and $Image.xhtml_file -notlike $EntryNamePattern) {
      return $false
    }
  }

  if (-not [string]::IsNullOrWhiteSpace($ImageNamePattern)) {
    if ($Image.image_path -notlike $ImageNamePattern -and $Image.image_file -notlike $ImageNamePattern) {
      return $false
    }
  }

  return $true
}

function Copy-ZipEntry {
  param(
    [System.IO.Compression.ZipArchive]$Zip,
    [string]$EntryPath,
    [string]$DestinationPath
  )

  $entry = $Zip.GetEntry($EntryPath)
  if (-not $entry) {
    throw "Image entry not found in EPUB: $EntryPath"
  }

  $destinationDirectory = Split-Path $DestinationPath -Parent
  New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null

  $inputStream = $entry.Open()
  try {
    $outputStream = [System.IO.File]::Open($DestinationPath, [System.IO.FileMode]::Create)
    try {
      $inputStream.CopyTo($outputStream)
    } finally {
      $outputStream.Close()
    }
  } finally {
    $inputStream.Close()
  }
}

function Convert-ImageToJsonObject {
  param($Image)

  [pscustomobject]@{
    image_number = $Image.image_number
    spine_index = $Image.spine_index
    image_type = $Image.image_type
    volume = $Image.volume
    title = $Image.title
    xhtml_path = $Image.xhtml_path
    image_path = $Image.image_path
    alt = $Image.alt
    output_path = $Image.output_path
  }
}

$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $EpubPath))
$images = New-Object 'System.Collections.Generic.List[object]'

try {
  $opfEntry = $zip.GetEntry('OEBPS/content.opf')
  if (-not $opfEntry) {
    throw "EPUB content.opf not found at OEBPS/content.opf"
  }

  $reader = [System.IO.StreamReader]::new($opfEntry.Open())
  try {
    [xml]$opf = $reader.ReadToEnd()
  } finally {
    $reader.Close()
  }

  $manifest = @{}
  foreach ($item in $opf.package.manifest.item) {
    $manifest[$item.id] = $item.href
  }

  $currentVolume = $null
  $imageNumber = 0
  $spineIndex = 0

  foreach ($itemRef in $opf.package.spine.itemref) {
    $spineIndex++
    $idRef = $itemRef.idref
    if (-not $manifest.ContainsKey($idRef)) {
      continue
    }

    $href = $manifest[$idRef]
    if ($href -notlike 'Text/*.xhtml') {
      continue
    }

    $xhtmlPath = "OEBPS/$href"
    $xhtmlEntry = $zip.GetEntry($xhtmlPath)
    if (-not $xhtmlEntry) {
      continue
    }

    $reader = [System.IO.StreamReader]::new($xhtmlEntry.Open())
    try {
      $xhtml = $reader.ReadToEnd()
    } finally {
      $reader.Close()
    }

    $title = Get-XhtmlTitle $xhtml
    $hrefVolume = Get-VolumeFromHref $href $title $currentVolume
    if ($href -match 'volume_(\d+)_' -or $title -match '^Volume\s+\d+:') {
      $currentVolume = $hrefVolume
    }

    $tags = @(Get-ImgTags $xhtml)
    foreach ($tag in $tags) {
      $imageNumber++
      $imagePath = Get-RelativePath $xhtmlPath $tag.src
      $imageTypeValue = Get-ImageType $href $title $tag.alt
      $imageFile = Split-Path $imagePath -Leaf
      $xhtmlFile = Split-Path $xhtmlPath -Leaf

      $images.Add([pscustomobject]@{
        image_number = $imageNumber
        spine_index = $spineIndex
        image_type = $imageTypeValue
        volume = $hrefVolume
        title = $title
        xhtml_path = $xhtmlPath
        xhtml_file = $xhtmlFile
        image_path = $imagePath
        image_file = $imageFile
        alt = $tag.alt
        output_path = $null
      })
    }
  }

  $selectedImages = @($images.ToArray() | Where-Object { Test-SelectedImage $_ })
  $jsonResults = New-Object 'System.Collections.Generic.List[object]'

  foreach ($image in $selectedImages) {
    if ($Extract) {
      $extension = [System.IO.Path]::GetExtension($image.image_file)
      $safeType = $image.image_type.ToLowerInvariant()
      $safeAlt = if ([string]::IsNullOrWhiteSpace($image.alt)) { "image" } else { $image.alt -replace '[^A-Za-z0-9_-]+', '-' }
      $fileName = "{0:D4}-spine-{1:D4}-{2}-{3}{4}" -f $image.image_number, $image.spine_index, $safeType, $safeAlt, $extension
      $destinationPath = Join-Path $OutputDir $fileName
      Copy-ZipEntry $zip $image.image_path $destinationPath
      $image.output_path = (Resolve-Path $destinationPath).Path
    }

    if ($Json) {
      $jsonResults.Add((Convert-ImageToJsonObject $image))
    } else {
      $volumeText = if ($null -ne $image.volume) { "Vol $($image.volume)" } else { "Vol -" }
      $extractText = if ($image.output_path) { " | Extracted: $($image.output_path)" } else { "" }
      "Image $($image.image_number) | Spine $($image.spine_index) | $($image.image_type) | $volumeText | $($image.xhtml_file) | $($image.image_file) | $($image.title) | Alt: $($image.alt)$extractText"
    }
  }

  if ($Json) {
    $jsonResults | ConvertTo-Json -Depth 6
  }
} finally {
  $zip.Dispose()
}
