function ConvertTo-KnowledgeCanonicalJsonString {
    param([string]$Value)

    $builder = [System.Text.StringBuilder]::new()
    [void]$builder.Append('"')
    foreach ($character in $Value.ToCharArray()) {
        $codePoint = [int]$character
        $escaped = switch ($codePoint) {
            8 {
                '\b'
            }
            9 {
                '\t'
            }
            10 {
                '\n'
            }
            12 {
                '\f'
            }
            13 {
                '\r'
            }
            34 {
                '\"'
            }
            92 {
                '\\'
            }
            default {
                $null
            }
        }
        if ($null -ne $escaped) {
            [void]$builder.Append($escaped)
        }
        elseif ($codePoint -lt 32) {
            [void]$builder.Append(('\u{0:x4}' -f $codePoint))
        }
        else {
            [void]$builder.Append($character)
        }
    }
    [void]$builder.Append('"')
    return $builder.ToString()
}

function Add-KnowledgeCanonicalJsonValue {
    param(
        [System.Text.StringBuilder]$Builder,
        [AllowNull()][object]$Value,
        [int]$Depth
    )

    if ($null -eq $Value) {
        [void]$Builder.Append('null')
        return
    }
    if ($Value -is [string] -or $Value -is [char]) {
        [void]$Builder.Append((ConvertTo-KnowledgeCanonicalJsonString ([string]$Value)))
        return
    }
    if ($Value -is [System.Collections.IDictionary]) {
        $keys = @($Value.Keys)
        [void]$Builder.Append('{')
        if ($keys.Count -gt 0) {
            [void]$Builder.Append("`n")
            for ($index = 0; $index -lt $keys.Count; $index += 1) {
                $key = [string]$keys[$index]
                [void]$Builder.Append((' ' * (($Depth + 1) * 2)))
                [void]$Builder.Append((ConvertTo-KnowledgeCanonicalJsonString $key))
                [void]$Builder.Append(': ')
                Add-KnowledgeCanonicalJsonValue -Builder $Builder -Value $Value[$key] -Depth ($Depth + 1)
                if ($index -lt $keys.Count - 1) {
                    [void]$Builder.Append(',')
                }
                [void]$Builder.Append("`n")
            }
            [void]$Builder.Append((' ' * ($Depth * 2)))
        }
        [void]$Builder.Append('}')
        return
    }
    if ($Value -is [System.Management.Automation.PSCustomObject]) {
        $mapping = [ordered]@{}
        foreach ($property in $Value.PSObject.Properties) {
            $mapping[$property.Name] = $property.Value
        }
        Add-KnowledgeCanonicalJsonValue -Builder $Builder -Value $mapping -Depth $Depth
        return
    }
    if ($Value -is [System.Collections.IEnumerable]) {
        $items = @($Value)
        [void]$Builder.Append('[')
        if ($items.Count -gt 0) {
            [void]$Builder.Append("`n")
            for ($index = 0; $index -lt $items.Count; $index += 1) {
                [void]$Builder.Append((' ' * (($Depth + 1) * 2)))
                Add-KnowledgeCanonicalJsonValue -Builder $Builder -Value $items[$index] -Depth ($Depth + 1)
                if ($index -lt $items.Count - 1) {
                    [void]$Builder.Append(',')
                }
                [void]$Builder.Append("`n")
            }
            [void]$Builder.Append((' ' * ($Depth * 2)))
        }
        [void]$Builder.Append(']')
        return
    }
    [void]$Builder.Append(($Value | ConvertTo-Json -Compress))
}

function ConvertTo-KnowledgeCanonicalJson {
    param([object]$Value)

    $builder = [System.Text.StringBuilder]::new()
    Add-KnowledgeCanonicalJsonValue -Builder $builder -Value $Value -Depth 0
    [void]$builder.Append("`n")
    return $builder.ToString()
}
