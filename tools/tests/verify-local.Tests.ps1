param([string]$Runner = (Join-Path $PSScriptRoot '../verify-local.ps1'))
$ErrorActionPreference = 'Stop'
$script:failures = @()
function Assert([bool]$Condition, [string]$Name) {
    if ($Condition) { Write-Host "PASS $Name" } else { $script:failures += $Name; Write-Host "FAIL $Name" }
}
function Run-Mocked([bool]$Collision, [bool]$CleanupFails) {
    $global:runnerMockcollision = $Collision; $global:runnerMockcleanupFails = $CleanupFails
    $global:runnerMockbuildReached = $false; $global:runnerMockdestructive = $false; $global:runnerMockgenerated = $null
    $global:runnerMockbase = 'rag-phase1-acceptance-mocked'
    $saved = @($env:POSTGRES_PASSWORD,$env:OPENAI_API_KEY,$env:APP_ORIGIN)
    $env:POSTGRES_PASSWORD = 'original-password'; $env:OPENAI_API_KEY = 'original-key'; $env:APP_ORIGIN = 'original-origin'
    function docker { }
    function docker.exe {
        $a = @($args); $global:LASTEXITCODE = 0
        if ($a[0] -eq 'version') { return '29.8.1' }
        if ($a[0] -eq 'info') { return 'linux' }
        if ($a[0] -eq 'ps') { return }
        if ($a[0] -eq 'volume' -and $a[1] -eq 'ls') { if ($global:runnerMockcollision -and $a -contains '--format') { return "$($global:runnerMockbase)_postgres-data" }; return }
        if ($a[0] -eq 'network' -and $a[1] -eq 'ls') { return }
        if ($a[0] -eq 'volume' -and $a[1] -eq 'inspect') {
            if ($global:runnerMockcollision -and $a[2] -eq "$($global:runnerMockbase)_postgres-data") { return '[{"Name":"sentinel","Labels":{}}]' }
            $global:LASTEXITCODE = 1; return 'not found'
        }
        if ($a[0] -eq 'compose' -and $a -contains 'version') { return 'Compose test double' }
        if ($a[0] -eq 'compose' -and $a -contains 'config') {
            return '{"name":"rag","services":{"frontend":{"ports":[{"host_ip":"127.0.0.1","published":"3000"}],"networks":{"local":{},"web":{}}},"backend":{"networks":{"local":{}},"environment":{"DATABASE_URL":"","OPENAI_API_KEY":"","APP_ORIGIN":""},"volumes":[{"type":"bind","target":"/app/storage"},{"type":"bind","target":"/app/data/uploads"}]},"migrate":{"networks":{"local":{}},"environment":{"DATABASE_URL":"","OPENAI_API_KEY":"","APP_ORIGIN":""}},"postgres":{"networks":{"local":{}},"environment":{"POSTGRES_PASSWORD":""}}},"volumes":{"postgres-data":{"name":"rag_postgres-data"},"postgres-test-data":{"name":"rag_postgres-test-data"}},"networks":{"local":{"name":"rag_local","internal":true},"test":{"name":"rag_test","internal":true},"web":{"name":"rag_web"}}}'
        }
        if ($a -contains '-f') { $global:runnerMockgenerated = $a[[array]::IndexOf($a,'-f')+1] }
        if ($a -contains 'build') { $global:runnerMockbuildReached = $true; $global:LASTEXITCODE = 1; return 'injected acceptance failure' }
        if ($a -contains 'down' -or $a -contains 'rm') {
            $global:runnerMockdestructive = $true
            if ($global:runnerMockcleanupFails) { $global:LASTEXITCODE = 1; return 'injected teardown failure' }
            return
        }
        throw "Unexpected mocked Docker operation: $($a -join ' ')"
    }
    $caught = ''
    try { & $Runner -TestProject $global:runnerMockbase } catch { $caught = $_.Exception.Message }
    try {
        Write-Host "Mocked result: $caught"
        if ($Collision) {
            Assert (-not $global:runnerMockbuildReached) 'Unlabelled exact-name collision rejects before build/start'
            Assert (-not $global:runnerMockdestructive) 'Unowned collision never reaches destructive cleanup'
        } else {
            Assert ($env:POSTGRES_PASSWORD -eq 'original-password' -and $env:OPENAI_API_KEY -eq 'original-key' -and $env:APP_ORIGIN -eq 'original-origin') 'Teardown failure always restores environment'
            Assert ($null -ne $global:runnerMockgenerated -and -not (Test-Path -LiteralPath (Split-Path $global:runnerMockgenerated))) 'Teardown failure removes temporary credential directory'
            Assert ($caught -match 'injected acceptance failure' -and $caught -match 'injected teardown failure') 'Both acceptance and teardown errors survive'
        }
    } finally {
        $env:POSTGRES_PASSWORD = $saved[0]; $env:OPENAI_API_KEY = $saved[1]; $env:APP_ORIGIN = $saved[2]
        if ($global:runnerMockgenerated) {
            $dir = Split-Path $global:runnerMockgenerated
            foreach ($name in @('compose.json','empty.env','failure.json')) { $file = Join-Path $dir $name; if (Test-Path -LiteralPath $file) { Remove-Item -LiteralPath $file } }
            if (Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir }
        }
    }
}
Run-Mocked $true $false
Run-Mocked $false $true
if ($script:failures.Count) { throw "$($script:failures.Count) runner safety regressions failed" }
