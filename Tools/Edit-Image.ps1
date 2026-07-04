param(
  [Parameter(Mandatory = $false)]
  [ValidateSet("Crop")]
  [string]$Operation = "Crop",

  [Parameter(Mandatory = $false)]
  [ValidateSet("PathwayTarotCard")]
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

  [switch]$Force
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
}

if ($ListPresets) {
  $presets.GetEnumerator() |
    Sort-Object Name |
    ForEach-Object {
      [pscustomobject]@{
        Name = $_.Name
        Operation = $_.Value.Operation
        X = $_.Value.X
        Y = $_.Value.Y
        Width = $_.Value.Width
        Height = $_.Value.Height
        Description = $_.Value.Description
      }
    }
  exit 0
}

if (-not $SourceImage) {
  throw "SourceImage is required unless -ListPresets is used."
}

if (-not $OutputImage) {
  throw "OutputImage is required unless -ListPresets is used."
}

if ($Preset) {
  $presetValues = $presets[$Preset]
  $Operation = $presetValues.Operation
  $X = $presetValues.X
  $Y = $presetValues.Y
  $Width = $presetValues.Width
  $Height = $presetValues.Height
}

if ($Operation -ne "Crop") {
  throw "Unsupported operation: $Operation"
}

if ($X -lt 0 -or $Y -lt 0 -or $Width -le 0 -or $Height -le 0) {
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
  $resolvedParent = Resolve-Path -LiteralPath $outputParent -ErrorAction SilentlyContinue
  if ($resolvedParent) {
    [System.IO.Directory]::CreateDirectory($resolvedParent.Path) | Out-Null
  } else {
    [System.IO.Directory]::CreateDirectory((Join-Path (Get-Location) $outputParent)) | Out-Null
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

Add-Type -AssemblyName System.Drawing

$source = [System.Drawing.Image]::FromFile((Resolve-Path -LiteralPath $SourceImage))
try {
  if (($X + $Width) -gt $source.Width -or ($Y + $Height) -gt $source.Height) {
    throw "Crop rectangle x=$X y=$Y width=$Width height=$Height exceeds source size $($source.Width)x$($source.Height)."
  }

  $sourceRect = [System.Drawing.Rectangle]::new($X, $Y, $Width, $Height)
  $targetRect = [System.Drawing.Rectangle]::new(0, 0, $Width, $Height)
  $target = [System.Drawing.Bitmap]::new($Width, $Height)

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

Write-Output "Wrote $OutputImage from $SourceImage using $Operation x=$X y=$Y width=$Width height=$Height."
