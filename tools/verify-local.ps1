param([ValidatePattern('^rag-phase1-acceptance(?:-[a-z0-9-]+)?$')][string]$TestProject = 'rag-phase1-acceptance',
      [ValidateRange(1024,65535)][int]$TestPort = 33071)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = Split-Path -Parent $PSScriptRoot
$dockerPath = 'C:\Program Files\Docker\Docker\resources\bin'
if (Test-Path (Join-Path $dockerPath 'docker.exe')) { $env:PATH = "$dockerPath;$env:PATH" }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop Linux containers and Compose are required.' }
$timer = [Diagnostics.Stopwatch]::StartNew()
$temp = Join-Path ([IO.Path]::GetTempPath()) ('rag-acceptance-' + [guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $temp
$composeFile = Join-Path $temp 'compose.json'
$envFile = Join-Path $temp 'empty.env'
$failureFile = Join-Path $temp 'failure.json'
$oldPassword = $env:POSTGRES_PASSWORD; $oldKey = $env:OPENAI_API_KEY; $oldOrigin = $env:APP_ORIGIN
$runId = [guid]::NewGuid().ToString('N')
$runProject = "$TestProject-$runId"
$runLabel = 'com.logistics-rag.acceptance-run'
$createdVolumes = @(); $createdNetworks = @()
$acceptanceError = $null; $cleanupErrors = @()
function Docker([string[]]$Arguments) {
    # Windows PowerShell 5 represents ordinary Docker stderr progress as ErrorRecord.
    # Decide success solely from the native exit code; never treat progress as failure.
    $ErrorActionPreference = 'Continue'
    $output = & docker.exe @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed ($($Arguments[0])): $($output -join [Environment]::NewLine)" }
    return $output
}
function Compose([string[]]$Arguments) {
    Docker (@('compose','--project-directory',$repo,'--env-file',$envFile,'-p',$runProject,'-f',$composeFile) + $Arguments)
}
function IsOwned($Resource) {
    if ($null -eq $Resource.Labels) { return $false }
    $label = $Resource.Labels.PSObject.Properties[$runLabel]
    $project = $Resource.Labels.PSObject.Properties['com.docker.compose.project']
    return ($null -ne $label -and $label.Value -eq $runId -and $null -ne $project -and $project.Value -eq $runProject)
}
function RemoveOwnedContainers {
    $ids = @(Docker @('ps','-aq','--filter',"label=com.docker.compose.project=$runProject",'--filter',"label=$runLabel=$runId") | Where-Object { $_ })
    foreach ($id in $ids) {
        $resource = @((Docker @('inspect',$id) | Out-String | ConvertFrom-Json))[0]
        if (-not (IsOwned $resource.Config)) { throw 'Refusing to remove a container without this run ownership.' }
        $null = Docker @('rm','-f',$resource.Id)
    }
}
function Pass([string]$Name) { Write-Host "PASS $Name" }
function Check([bool]$Condition, [string]$Name) { if (-not $Condition) { throw "FAIL $Name" }; Pass $Name }
function InspectService([string]$Name) {
    $id = (Compose @('ps','-a','-q',$Name) | Out-String).Trim()
    if (-not $id) { return $null }
    return @((Docker @('inspect',$id) | Out-String | ConvertFrom-Json))[0]
}
try {
    [IO.File]::WriteAllText($envFile, '')
    $env:POSTGRES_PASSWORD = [guid]::NewGuid().ToString('N')
    $env:OPENAI_API_KEY = ''; $env:APP_ORIGIN = "http://localhost:$TestPort"
    $version = (Docker @('version','--format','{{.Server.Version}}') | Out-String).Trim()
    Check ([int]($version.Split('.')[0]) -ge 28) "Docker $version (loopback publishing requires Engine >=28)"
    $null = Docker @('compose','version')
    Check (((Docker @('info','--format','{{.OSType}}') | Out-String).Trim()) -eq 'linux') 'Linux containers'
    # Refuse reuse: an old project might contain data the operator wants to keep.
    $existing = (Docker @('ps','-aq','--filter',"label=com.docker.compose.project=$TestProject") | Out-String).Trim()
    $volumes = (Docker @('volume','ls','-q','--filter',"label=com.docker.compose.project=$TestProject") | Out-String).Trim()
    Check (-not $existing -and -not $volumes) 'Disposable project is unused'
    $config = Docker @('compose','--project-directory',$repo,'--env-file',$envFile,'-f',(Join-Path $repo 'docker-compose.yml'),'config','--format','json') | Out-String | ConvertFrom-Json
    foreach ($property in $config.services.PSObject.Properties) {
        $ports = @($property.Value.PSObject.Properties | Where-Object Name -eq 'ports' | ForEach-Object Value)
        if ($ports.Count) {
            Check ($property.Name -eq 'frontend' -and $ports.Count -eq 1 -and $ports[0].host_ip -eq '127.0.0.1' -and $ports[0].published -eq '3000') 'Only frontend publishes configured IPv4 loopback'
        }
    }
    Check ($config.networks.local.internal -and $config.networks.test.internal) 'Internal local/test networks'
    $webMembers = @($config.services.PSObject.Properties | Where-Object { $_.Value.networks.PSObject.Properties.Name -contains 'web' } | ForEach-Object Name)
    Check ($webMembers.Count -eq 1 -and $webMembers[0] -eq 'frontend' -and $config.services.frontend.networks.PSObject.Properties.Name -contains 'local') 'Only frontend joins publishing web bridge; backend/test remain private'
    $mounts = @($config.services.backend.volumes)
    Check (@($mounts | Where-Object { $_.target -eq '/app/storage' -and $_.type -eq 'bind' }).Count -eq 1 -and @($mounts | Where-Object { $_.target -eq '/app/data/uploads' -and $_.type -eq 'bind' }).Count -eq 1) 'Local private storage/uploads mounts'
    # Replace operational bind mounts and credentials in the disposable copy only.
    foreach ($name in @('backend','migrate')) {
        $config.services.$name.environment.DATABASE_URL = "postgresql+psycopg://rag:$($env:POSTGRES_PASSWORD)@postgres:5432/rag"
        $config.services.$name.environment.OPENAI_API_KEY = ''
        $config.services.$name.environment.APP_ORIGIN = $env:APP_ORIGIN
    }
    $config.services.postgres.environment.POSTGRES_PASSWORD = $env:POSTGRES_PASSWORD
    $config.services.backend.volumes = @(@{type='volume';source='acceptance-uploads';target='/app/data/uploads'},@{type='volume';source='acceptance-storage';target='/app/storage'})
    $config.volumes | Add-Member -NotePropertyName 'acceptance-uploads' -NotePropertyValue @{name="${TestProject}_uploads"}
    $config.volumes | Add-Member -NotePropertyName 'acceptance-storage' -NotePropertyValue @{name="${TestProject}_storage"}
    # Check exact names regardless of labels. Legacy predictable names are also refused.
    $volumeNames = @(Docker @('volume','ls','--format','{{.Name}}'))
    $networkNames = @(Docker @('network','ls','--format','{{.Name}}'))
    foreach ($kind in @('volumes','networks')) {
        $existingNames = if ($kind -eq 'volumes') { $volumeNames } else { $networkNames }
        foreach ($property in $config.$kind.PSObject.Properties) {
            foreach ($name in @("${TestProject}_$($property.Name)","${runProject}_$($property.Name)")) {
                if ($existingNames -contains $name) { throw "Refusing existing exact $kind name: $name" }
            }
        }
    }
    Pass 'Exact volume/network names are unused regardless of labels'
    # Pre-create unique external resources and verify ownership before any mounting.
    # Docker volume create can silently reuse a name, so its return value is insufficient.
    foreach ($volume in $config.volumes.PSObject.Properties) {
        $name = "${runProject}_$($volume.Name)"
        $null = Docker @('volume','create','--label',"$runLabel=$runId",'--label',"com.docker.compose.project=$runProject",$name)
        $resource = @((Docker @('volume','inspect',$name) | Out-String | ConvertFrom-Json))[0]
        if (-not (IsOwned $resource)) { throw 'Refusing to mount a volume without this run ownership.' }
        $createdVolumes += $resource
        $volume.Value = @{name=$name;external=$true}
    }
    foreach ($network in $config.networks.PSObject.Properties) {
        $name = "${runProject}_$($network.Name)"
        $arguments = @('network','create','--driver','bridge','--label',"$runLabel=$runId",'--label',"com.docker.compose.project=$runProject")
        if ($network.Value.PSObject.Properties['internal'] -and $network.Value.internal) { $arguments += '--internal' }
        $id = (Docker ($arguments + $name) | Out-String).Trim()
        $resource = @((Docker @('network','inspect',$id) | Out-String | ConvertFrom-Json))[0]
        if (-not (IsOwned $resource)) { throw 'Refusing to join a network without this run ownership.' }
        $createdNetworks += $resource
        $network.Value = @{name=$name;external=$true}
    }
    foreach ($service in $config.services.PSObject.Properties) {
        $labels = @{}
        if ($service.Value.PSObject.Properties['labels']) {
            foreach ($label in $service.Value.labels.PSObject.Properties) { $labels[$label.Name] = $label.Value }
        }
        $labels[$runLabel] = $runId
        $service.Value | Add-Member -Force -NotePropertyName labels -NotePropertyValue $labels
    }
    $config.name = $runProject
    $config.services.frontend.ports[0].published = "$TestPort"
    [IO.File]::WriteAllText($composeFile, ($config | ConvertTo-Json -Depth 100))
    [IO.File]::WriteAllText($failureFile, '{"services":{"migrate":{"command":["python","-c","raise SystemExit(41)"]}}}')
    $null = Compose @('build','backend','backend-test','frontend','next-test','frontend-test')
    $null = Compose @('up','-d','--wait','postgres')
    $empty = (Compose @('exec','-T','postgres','psql','-U','rag','-d','rag','-tAc',"SELECT count(*) FROM information_schema.tables WHERE table_schema='public'") | Out-String).Trim()
    Check ($empty -eq '0') 'Fresh PostgreSQL has no application tables'
    # A deliberate failing migration must stop dependency startup, not just return 503.
    $ErrorActionPreference = 'Continue'
    $failureOutput = & docker.exe compose --project-directory $repo --env-file $envFile -p $runProject -f $composeFile -f $failureFile up -d frontend 2>&1
    $failedExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    Check ($failedExit -ne 0) 'Failed migration rejects Compose startup'
    foreach ($name in @('backend','frontend')) {
        $service = InspectService $name
        Check ($null -eq $service -or -not $service.State.Running) "Failed migration leaves $name stopped"
    }
    # Remove only this run's containers; external volumes/networks stay for replay.
    RemoveOwnedContainers
    $null = Compose @('up','-d','--wait','frontend')
    $revision = (Compose @('exec','-T','postgres','psql','-U','rag','-d','rag','-tAc',"SELECT version_num FROM alembic_version") | Out-String).Trim()
    Check ($revision -eq '0001_access_control') 'Real Alembic applies expected head'
    $vector = (Compose @('exec','-T','postgres','psql','-U','rag','-d','rag','-tAc',"SELECT extversion FROM pg_extension WHERE extname='vector'") | Out-String).Trim()
    Check ($vector -eq '0.8.7') 'Real pgvector extension'
    $null = Compose @('exec','-T','backend','python','-m','alembic','upgrade','head')
    $null = Compose @('exec','-T','backend','python','-m','alembic','upgrade','head')
    Pass 'Alembic replay twice'
    # Integration tests use their own postgres-test/rag_test only.
    $tests = Compose @('run','--rm','backend-test','python','-m','pytest','tests/integration/test_migrations.py','tests/integration/test_startup.py','tests/integration/test_bootstrap_seed.py','-q')
    $testText = $tests -join [Environment]::NewLine
    Check ($testText -match '(\d+) passed' -and [int]$Matches[1] -gt 0) 'Migration/bootstrap/seed/startup tests execute'
    Write-Host ($testText -split [Environment]::NewLine | Where-Object { $_ -match '\d+ passed' })
    $create = "from scripts.bootstrap_admin import bootstrap_admin; from scripts.seed_demo import seed_demo; assert bootstrap_admin('acceptance-admin','acceptance-only-password'); assert seed_demo('acceptance-demo-password','acceptance-other-password')"
    $null = Compose @('exec','-T','backend','python','-c',$create)
    # Snapshot compares identity, hashes, flags, roles, metadata, grants and timestamps without printing values.
    $digest = "import hashlib,json; from sqlalchemy import text; from app.database.session import engine; c=engine.connect(); rows=[c.execute(text('SELECT row_to_json(t)::text FROM '+n+' t ORDER BY row_to_json(t)::text')).scalars().all() for n in ['accounts','datasets','dataset_grants']]; print(hashlib.sha256(json.dumps(rows).encode()).hexdigest())"
    $before = (Compose @('exec','-T','backend','python','-c',$digest) | Out-String).Trim()
    $null = Compose @('restart','postgres','backend','frontend')
    $null = Compose @('up','-d','--wait','frontend')
    $after = (Compose @('exec','-T','backend','python','-c',$digest) | Out-String).Trim()
    Check ($before -eq $after -and $before.Length -eq 64) 'Restart preserves exact account/password/role/dataset/grant snapshot'
    foreach ($name in @('postgres','backend','api-test','postgres-test')) {
        $service = InspectService $name
        if ($null -ne $service) {
            $bindings = @($service.HostConfig.PortBindings.PSObject.Properties)
            Check ($bindings.Count -eq 0) "$name has no host bindings"
        }
    }
    $web = InspectService 'frontend'
    $bindings = @($web.NetworkSettings.Ports.'3000/tcp')
    Check ($bindings.Count -eq 1 -and $bindings[0].HostIp -eq '127.0.0.1' -and $bindings[0].HostPort -eq "$TestPort") 'Actual Docker mapping is IPv4 loopback only'
    # Inspect the host listener, including wildcard/LAN/IPv6; config alone is insufficient.
    try {
        $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $TestPort -ErrorAction Stop | Select-Object -ExpandProperty LocalAddress)
    } catch {
        $listeners = @(netstat -ano -p tcp | ForEach-Object { if ($_ -match "^\s*TCP\s+(\S+):$TestPort\s+\S+\s+LISTENING\s+") { $Matches[1].Trim('[',']') } })
    }
    Check ($listeners.Count -gt 0 -and @($listeners | Where-Object { $_ -notin @('127.0.0.1','::1') }).Count -eq 0) "Actual host IPv4/IPv6 listeners are loopback ($($listeners -join ', '))"
    Check ((Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$TestPort/login").StatusCode -eq 200) 'Host login reachable without AI key'
    $null = Compose @('exec','-T','backend','python','-m','pip','check')
    Pass 'Locked backend packages compatible'
} catch {
    $acceptanceError = $_
} finally {
    try {
        try { RemoveOwnedContainers } catch { $cleanupErrors += $_.Exception.Message }
        foreach ($resource in $createdNetworks) {
            try {
                $current = @((Docker @('network','inspect',$resource.Id) | Out-String | ConvertFrom-Json))[0]
                if (-not (IsOwned $current)) { throw 'Refusing network cleanup: ownership changed.' }
                $null = Docker @('network','rm',$resource.Id)
            } catch { $cleanupErrors += $_.Exception.Message }
        }
        foreach ($resource in $createdVolumes) {
            try {
                $current = @((Docker @('volume','inspect',$resource.Name) | Out-String | ConvertFrom-Json))[0]
                if (-not (IsOwned $current) -or $current.CreatedAt -ne $resource.CreatedAt) { throw 'Refusing volume cleanup: ownership changed.' }
                $null = Docker @('volume','rm',$resource.Name)
            } catch { $cleanupErrors += $_.Exception.Message }
        }
    } finally {
        $env:POSTGRES_PASSWORD = $oldPassword; $env:OPENAI_API_KEY = $oldKey; $env:APP_ORIGIN = $oldOrigin
        foreach ($path in @($composeFile,$envFile,$failureFile,$temp)) {
            try { if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -ErrorAction Stop } }
            catch { $cleanupErrors += "Temporary cleanup failed: $($_.Exception.Message)" }
        }
    }
}
if ($acceptanceError -or $cleanupErrors.Count) {
    $messages = @()
    if ($acceptanceError) { $messages += "Acceptance failed: $($acceptanceError.Exception.Message)" }
    if ($cleanupErrors.Count) { $messages += "Teardown failed: $($cleanupErrors -join '; ')" }
    throw ($messages -join [Environment]::NewLine)
}
Write-Host ('PASS all acceptance checks and owned cleanup; elapsed {0:N2}s' -f $timer.Elapsed.TotalSeconds)
