param(
  [Parameter(Mandatory = $false)]
  [string]$Operation = "Crop",

  [Parameter(Mandatory = $false)]
  [string]$Preset,

  [Parameter(Mandatory = $false)]
  [switch]$ListPresets,

  [Parameter(Mandatory = $false)]
  [string]$SourceImage,

  [Parameter(Mandatory = $false)]
  [string]$OutputImage,

  [int]$X = -1,
  [int]$Y = -1,
  [int]$Width = -1,
  [int]$Height = -1,

  [switch]$Force,

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

$presets = @{
  PathwayTarotCard = @{
    Operation = "Crop"
    X = 24
    Y = 804
    Width = 660
    Height = 1168
    Description = "Official EPUB pathway guide tarot-card crop, recovered from the validated Strength/Giant pilot crop."
  }
  PathwaySymbol = @{
    Operation = "Crop"
    X = 472
    Y = 305
    Width = 486
    Height = 486
    Description = "Official EPUB pathway guide central symbol crop, recovered from the reviewed Sleepless/Darkness symbol pilot crop."
  }
}

function Resolve-OperationName {
  param([string]$Name)

  switch -Regex ($Name) {
    '^(?i:crop)$' { return "Crop" }
    '^(?i:extract|extractepubimages|extract-epub-images|extract-images|listepubimages|list-epub-images|list-images)$' { return "ExtractEpubImages" }
    default {
      throw "Unsupported operation: $Name. Use Crop or ExtractEpubImages. Aliases include Extract, Extract-Images, List-Images, and List-Epub-Images."
    }
  }
}

function Resolve-PresetName {
  param([string]$Name)

  if ([string]::IsNullOrWhiteSpace($Name)) {
    return $null
  }

  switch -Regex ($Name) {
    '^(?i:pathwaytarotcard|pathway-tarot-card|pathway-tarot|tarot-card)$' { return "PathwayTarotCard" }
    '^(?i:pathwaysymbol|pathway-symbol|pathway-symbol-crop|symbol)$' { return "PathwaySymbol" }
    default {
      throw "Unsupported preset: $Name. Use PathwayTarotCard or PathwaySymbol. Aliases include pathway-tarot-card, pathway-tarot, tarot-card, pathway-symbol, pathway-symbol-crop, and symbol."
    }
  }
}

function Show-Presets {
  $presets.GetEnumerator() |
    Sort-Object Name |
    ForEach-Object {
      $operation = $_.Value.Operation.ToLowerInvariant()
      "$($_.Name): operation=$operation x=$($_.Value.X) y=$($_.Value.Y) width=$($_.Value.Width) height=$($_.Value.Height) - $($_.Value.Description)"
    }
}

function Get-OutputImageFormat {
  param([string]$Path)

  $extension = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
  switch ($extension) {
    ".jpg" { return [System.Drawing.Imaging.ImageFormat]::Jpeg }
    ".jpeg" { return [System.Drawing.Imaging.ImageFormat]::Jpeg }
    ".bmp" { return [System.Drawing.Imaging.ImageFormat]::Bmp }
    ".gif" { return [System.Drawing.Imaging.ImageFormat]::Gif }
    default { return [System.Drawing.Imaging.ImageFormat]::Png }
  }
}

function Invoke-Crop {
  if (-not $SourceImage) {
    throw "SourceImage is required unless -ListPresets is used."
  }

  if (-not $OutputImage) {
    throw "OutputImage is required unless -ListPresets is used."
  }

  $operationName = $Operation
  $cropX = $X
  $cropY = $Y
  $cropWidth = $Width
  $cropHeight = $Height

  if ($Preset) {
    $presetValues = $presets[(Resolve-PresetName $Preset)]
    $operationName = $presetValues.Operation
    $cropX = $presetValues.X
    $cropY = $presetValues.Y
    $cropWidth = $presetValues.Width
    $cropHeight = $presetValues.Height
  }

  if ($operationName -ne "Crop") {
    throw "Unsupported crop operation: $operationName"
  }

  if ($cropX -lt 0 -or $cropY -lt 0 -or $cropWidth -le 0 -or $cropHeight -le 0) {
    throw "Crop requires non-negative X/Y and positive Width/Height, or a preset that supplies them."
  }

  if (-not (Test-Path -LiteralPath $SourceImage)) {
    throw "Source image not found: $SourceImage"
  }

  if ((Test-Path -LiteralPath $OutputImage) -and -not $Force) {
    throw "Output image already exists. Use -Force to overwrite: $OutputImage"
  }

  $outputParent = Split-Path -Parent $OutputImage
  if ($outputParent) {
    [System.IO.Directory]::CreateDirectory((Join-Path (Get-Location) $outputParent)) | Out-Null
  }

  Add-Type -AssemblyName System.Drawing

  $source = [System.Drawing.Image]::FromFile((Resolve-Path -LiteralPath $SourceImage))
  try {
    if (($cropX + $cropWidth) -gt $source.Width -or ($cropY + $cropHeight) -gt $source.Height) {
      throw "Crop rectangle x=$cropX y=$cropY width=$cropWidth height=$cropHeight exceeds source size $($source.Width)x$($source.Height)."
    }

    $sourceRect = [System.Drawing.Rectangle]::new($cropX, $cropY, $cropWidth, $cropHeight)
    $targetRect = [System.Drawing.Rectangle]::new(0, 0, $cropWidth, $cropHeight)
    $target = [System.Drawing.Bitmap]::new($cropWidth, $cropHeight)

    try {
      $graphics = [System.Drawing.Graphics]::FromImage($target)
      try {
        $graphics.DrawImage($source, $targetRect, $sourceRect, [System.Drawing.GraphicsUnit]::Pixel)
      } finally {
        $graphics.Dispose()
      }

      $target.Save((Join-Path (Get-Location) $OutputImage), (Get-OutputImageFormat -Path $OutputImage))
    } finally {
      $target.Dispose()
    }
  } finally {
    $source.Dispose()
  }

  Write-Output "Wrote $OutputImage from $SourceImage using Crop x=$cropX y=$cropY width=$cropWidth height=$cropHeight."
}

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

function Invoke-ExtractEpubImages {
  if ($StartImageNumber -gt $EndImageNumber) {
    throw "StartImageNumber cannot be greater than EndImageNumber."
  }

  if (-not (Test-Path $EpubPath)) {
    throw "EPUB not found: $EpubPath"
  }

  Add-Type -AssemblyName System.IO.Compression.FileSystem

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
    $inSideStories = $false
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
      if ($href -like 'Text/side_stories*') {
        $currentVolume = $null
        $inSideStories = $true
      }

      $hrefVolume = if ($inSideStories -and $href -notmatch 'volume_\d+_') {
        $null
      } else {
        Get-VolumeFromHref $href $title $currentVolume
      }

      if ($href -match 'volume_(\d+)_' -or $title -match '^Volume\s+\d+:') {
        $currentVolume = $hrefVolume
        $inSideStories = $false
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
      ConvertTo-Json -InputObject @($jsonResults.ToArray()) -Depth 6
    }
  } finally {
    $zip.Dispose()
  }
}

$Operation = Resolve-OperationName $Operation
$Preset = Resolve-PresetName $Preset

if ($ListPresets) {
  Show-Presets
  exit 0
}

switch ($Operation) {
  "Crop" {
    Invoke-Crop
  }
  "ExtractEpubImages" {
    Invoke-ExtractEpubImages
  }
}
