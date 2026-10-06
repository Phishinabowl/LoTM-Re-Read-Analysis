# Deliberate failures: explicit adapter verification only, excluded from root discovery glob.
if ($env:NATIVE_FAILURE_CASE -eq 'cancellation') {
    [Environment]::Exit(130)
}
Describe 'Synthetic native result fixture' {
    if ($env:NATIVE_FAILURE_CASE -eq 'collection') {
        throw 'Synthetic discovery failure <&> é'
    }
    BeforeAll {
        if ($env:NATIVE_FAILURE_CASE -eq 'dependency') {
            throw 'Synthetic missing dependency <&> é'
        }
    }
    AfterEach {
        if ($env:NATIVE_FAILURE_CASE -eq 'teardown') {
            throw 'Synthetic teardown failure <&> é'
        }
    }
    if ($env:NATIVE_FAILURE_CASE -ne 'empty') {
        It 'native case with XML & Unicode é' -Skip:($env:NATIVE_FAILURE_CASE -eq 'skip') {
            Write-Output 'native stdout <&> é'
            [Console]::Error.WriteLine('native stderr <&> é')
            if ($env:NATIVE_FAILURE_CASE -eq 'assertion') {
                1 | Should -Be 2
            }
            1 | Should -Be 1
        }
    }
}
