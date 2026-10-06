$ErrorActionPreference = 'Stop'
$env:PATH = "C:\Program Files\Docker\Docker\resources\bin;$env:PATH"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$compose = Get-Content (Join-Path $repo 'docker-compose.yml') -Raw
$image = (($compose -split "`n" | Where-Object { $_ -match '^\s+image:\s+pgvector/pgvector:' } | Select-Object -First 1) -replace '^\s+image:\s+','').Trim()
$name = 'rag-readiness-proof-' + [guid]::NewGuid().ToString('N')
$dir = Join-Path ([IO.Path]::GetTempPath()) $name
$null = New-Item -ItemType Directory -Path $dir
$hook = Join-Path $dir 'barrier.sh'
[IO.File]::WriteAllText($hook,"#!/bin/sh`necho readiness-barrier-active`nwhile [ ! -f /tmp/readiness-release ]; do sleep 0.1; done`n")
$created = $false
function Native([string[]]$Arguments) {
    $ErrorActionPreference = 'Continue'
    $output = & docker.exe @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Readiness Docker operation failed ($($Arguments[0])): $($output -join ' ')" }
    return $output
}
try {
    $null = Native @('run','-d','--name',$name,'--network','none','--tmpfs','/var/lib/postgresql','-e','POSTGRES_HOST_AUTH_METHOD=trust','-e','POSTGRES_USER=readiness','-e','POSTGRES_DB=readiness','--mount',"type=bind,src=$hook,dst=/docker-entrypoint-initdb.d/barrier.sh,readonly",$image)
    $created = $true
    $deadline = [DateTime]::UtcNow.AddSeconds(90)
    do { $logs = Native @('logs',$name) | Out-String; if ($logs -match 'readiness-barrier-active') { break }; Start-Sleep -Milliseconds 200 } while ([DateTime]::UtcNow -lt $deadline)
    if ($logs -notmatch 'readiness-barrier-active') { throw 'Initialization barrier was not reached.' }
    $null = Native @('exec',$name,'pg_isready','-U','readiness','-d','readiness')
    $ErrorActionPreference = 'Continue'
    $null = & docker.exe exec $name pg_isready -h 127.0.0.1 -U readiness -d readiness 2>&1
    $tcpExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($tcpExit -eq 0) { throw 'Temporary initialization server unexpectedly accepts TCP.' }
    Write-Host 'PASS Pinned image temporary init server accepts Unix socket but rejects TCP'
    $null = Native @('exec',$name,'touch','/tmp/readiness-release')
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        $ErrorActionPreference = 'Continue'
        $null = & docker.exe exec $name pg_isready -h 127.0.0.1 -U readiness -d readiness 2>&1
        $tcpExit = $LASTEXITCODE; $ErrorActionPreference = 'Stop'
        if ($tcpExit -eq 0) { break }; Start-Sleep -Milliseconds 200
    } while ([DateTime]::UtcNow -lt $deadline)
    if ($tcpExit -ne 0) { throw 'Final PostgreSQL TCP server did not become ready.' }
    Write-Host 'PASS Final pinned PostgreSQL server accepts TCP after initialization'
    if ([regex]::Matches($compose,'pg_isready -h 127\.0\.0\.1 -U rag(?:_test)? -d rag(?:_test)?').Count -ne 2) { throw 'Both Compose PostgreSQL healthchecks must probe final TCP server' }
    Write-Host 'PASS Operational and isolated-test Compose healthchecks probe TCP'
} finally {
    if ($created) { $null = Native @('rm','-f',$name) }
    if (Test-Path -LiteralPath $hook) { Remove-Item -LiteralPath $hook }
    if (Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir }
}
