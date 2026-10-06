param([string]$Runner = (Join-Path $PSScriptRoot '../verify-local.ps1'))
$ErrorActionPreference = 'Stop'
$env:PATH = "C:\Program Files\Docker\Docker\resources\bin;$env:PATH"
$project = 'rag-phase1-acceptance-collision-' + [guid]::NewGuid().ToString('N')
$volume = "${project}_postgres-data"
$token = [guid]::NewGuid().ToString('N')
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$imageLine = Get-Content (Join-Path $repo 'docker-compose.yml') | Where-Object { $_ -match '^\s+image:\s+pgvector/pgvector:' } | Select-Object -First 1
$image = ($imageLine -replace '^\s+image:\s+','').Trim()
$created = $false
function Native([string[]]$Arguments) {
    $ErrorActionPreference = 'Continue'
    $output = & docker.exe @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Sentinel Docker operation failed ($($Arguments[0])): $($output -join ' ')" }
    return $output
}
try {
    # The random name is exclusively owned by this test; omit all Docker labels intentionally.
    $names = @(Native @('volume','ls','--format','{{.Name}}'))
    if ($names -contains $volume) { throw 'Unexpected sentinel name collision; refusing reuse.' }
    $null = Native @('volume','create',$volume); $created = $true
    $null = Native @('run','--rm','--network','none','--mount',"type=volume,src=$volume,dst=/sentinel",'--entrypoint','sh',$image,'-c',"printf '%s' '$token' > /sentinel/proof")
    $before = @((Native @('volume','inspect',$volume) | Out-String | ConvertFrom-Json))[0]
    if ($null -ne $before.Labels -and @($before.Labels.PSObject.Properties).Count -ne 0) { throw 'Sentinel must be unlabelled.' }
    $failure = ''
    try { & $Runner -TestProject $project } catch { $failure = $_.Exception.Message }
    if ($failure -notmatch 'Refusing existing exact volumes name') { throw 'Runner did not reject the exact unlabelled sentinel name.' }
    $after = @((Native @('volume','inspect',$volume) | Out-String | ConvertFrom-Json))[0]
    $actual = (Native @('run','--rm','--network','none','--mount',"type=volume,src=$volume,dst=/sentinel,readonly",'--entrypoint','sh',$image,'-c','cat /sentinel/proof') | Out-String).Trim()
    if ($actual -ne $token -or $after.CreatedAt -ne $before.CreatedAt) { throw 'Sentinel content or volume identity changed.' }
    Write-Host 'PASS Real unlabelled exact-name sentinel is rejected and preserved unchanged'
} finally {
    if ($created) { $null = Native @('volume','rm',$volume) }
}
