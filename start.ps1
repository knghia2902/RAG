# Script khoi dong Modular RAG cho IT & Logistics
# Ho tro: Windows PowerShell / PowerShell 7

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   KHOI DONG HE THONG MODULAR RAG CHO IT & LOGISTICS     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Kiem tra file .env
if (-not (Test-Path "$ProjectDir\.env")) {
    Write-Host "[1/5] Chua tim thay file .env. Dang tao tu .env.example..." -ForegroundColor Yellow
    if (Test-Path "$ProjectDir\.env.example") {
        Copy-Item "$ProjectDir\.env.example" "$ProjectDir\.env"
        # Sinh mot password ngau nhien an toan cho postgres neu can
        $randPass = [System.Guid]::NewGuid().ToString("N") + [System.Guid]::NewGuid().ToString("N")
        (Get-Content "$ProjectDir\.env") -replace "replace-with-your-local-password", $randPass | Set-Content "$ProjectDir\.env"
        Write-Host "      -> Da tao file .env voi mat khau database moi." -ForegroundColor Green
    } else {
        Write-Host "      [CANH BAO] Khong tim thay file .env.example." -ForegroundColor Red
    }
} else {
    Write-Host "[1/5] File cau hinh .env da ton tai." -ForegroundColor Green
}

# 2. Kiem tra Docker Daemon
Write-Host "[2/5] Kiem tra trang thai Docker Desktop..." -ForegroundColor Yellow
$dockerReady = $false
try {
    $null = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerReady = $true
    }
} catch {
    $dockerReady = $false
}

if (-not $dockerReady) {
    Write-Host "      Docker chua chay. Dang khoi dong cac dich vu Docker..." -ForegroundColor Yellow
    try {
        $svc = Get-Service com.docker.service -ErrorAction SilentlyContinue
        if ($svc -and $svc.Status -ne "Running") {
            Start-Service com.docker.service -ErrorAction SilentlyContinue
        }
    } catch {}

    $dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerExe) {
        $running = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
        if (-not $running) {
            Start-Process $dockerExe
        }
    } else {
        Write-Host "      [LOI] Khong tim thay Docker Desktop tai $dockerExe." -ForegroundColor Red
        Write-Host "      Vui long mo ung dung Docker Desktop thu cong tu Start Menu." -ForegroundColor Red
    }

    Write-Host "      Dang cho Docker Desktop khoi dong (co the mat 30-60 giay)..." -NoNewline
    $maxWait = 45
    for ($i = 0; $i -lt $maxWait; $i++) {
        Start-Sleep -Seconds 2
        Write-Host "." -NoNewline
        try {
            $null = docker info 2>&1
            if ($LASTEXITCODE -eq 0) {
                $dockerReady = $true
                Write-Host ""
                break
            }
        } catch {}
    }

    if (-not $dockerReady) {
        Write-Host ""
        Write-Host "[CANH BAO] Docker Desktop chua san sang." -ForegroundColor Yellow
        Write-Host "Vui long mo ung dung Docker Desktop tren man hinh (Start Menu -> Docker Desktop)," -ForegroundColor Yellow
        Write-Host "cho den khi bieu tuong ca voi o khay he thong bao Running roi chay lai." -ForegroundColor Yellow
        Read-Host "Nhan Enter de thoat..."
        exit 1
    }
}

Write-Host "      -> Docker Desktop da san sang!" -ForegroundColor Green

# 3. Khoi chay Docker Compose
Write-Host "[3/5] Dang khoi dong cac containers (PostgreSQL pgvector, RabbitMQ, Backend, Frontend)..." -ForegroundColor Yellow
docker compose up -d --build postgres rabbitmq migrate backend worker frontend

if ($LASTEXITCODE -ne 0) {
    Write-Host "[LOI] Khong the khoi dong cac dich vu qua docker compose." -ForegroundColor Red
    Read-Host "Nhan Enter de thoat..."
    exit 1
}
Write-Host "      -> Cac dich vu da duoc khoi chay thanh cong." -ForegroundColor Green

# 4. Kiem tra trang thai cac dich vu
Write-Host "[4/5] Kiem tra trang thai hoat dong..." -ForegroundColor Yellow
$frontendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/login" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $frontendReady = $true
            break
        }
    } catch {}
    Start-Sleep -Seconds 2
}

if ($frontendReady) {
    Write-Host "      -> He thong Web san sang tai http://localhost:3000" -ForegroundColor Green
} else {
    Write-Host "      -> Dang hoan tat khoi dong web trong giay lat..." -ForegroundColor Yellow
}

# 5. Huong dan va mo trinh duyet
Write-Host "[5/5] Hoan tat!" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   HE THONG DA KHOI DONG THANH CONG!                     " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " • Giao dien Web:        http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Neu lan dau tien su dung, ban co the tao tai khoan Admin bang cach chay:" -ForegroundColor Yellow
Write-Host "   docker compose run --rm backend python -m scripts.bootstrap_admin" -ForegroundColor White
Write-Host ""
Write-Host "Dang mo trinh duyet web..." -ForegroundColor Cyan

try {
    Start-Process "http://localhost:3000"
} catch {}

Write-Host ""
Write-Host "De dung he thong, chay file stop.bat hoac go: docker compose down" -ForegroundColor Gray
Write-Host ""
