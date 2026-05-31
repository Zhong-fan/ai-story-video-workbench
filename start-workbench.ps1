param(
    [switch]$SkipBuild,
    [switch]$SkipNpmInstall,
    [switch]$NoBackend,
    [switch]$WithEmbedding
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

trap {
    Write-Host ""
    Write-Host "[Error] $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

function Write-Header {
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "  ChenFlow Workbench Launcher"
    Write-Host "=========================================="
    Write-Host ""
}

function Require-Command {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$InstallHint
    )
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found in PATH. $InstallHint"
    }
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    Write-Host ""
    Write-Host $Label
    & $Action
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [string]$ErrorMessage = ""
    )
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $FilePath @Arguments
    $ErrorActionPreference = $previousErrorActionPreference
    if ($LASTEXITCODE -ne 0) {
        if ($ErrorMessage) {
            throw $ErrorMessage
        }
        throw "$FilePath exited with code $LASTEXITCODE."
    }
}

function Test-NativeSuccess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $FilePath @Arguments > $null 2> $null
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference
    return $exitCode -eq 0
}

function Wait-TcpPort {
    param(
        [Parameter(Mandatory = $true)][string]$HostName,
        [Parameter(Mandatory = $true)][int]$Port,
        [int]$TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $client = [System.Net.Sockets.TcpClient]::new()
        try {
            $connect = $client.BeginConnect($HostName, $Port, $null, $null)
            if ($connect.AsyncWaitHandle.WaitOne(1000, $false)) {
                $client.EndConnect($connect)
                return
            }
        }
        catch {
        }
        finally {
            $client.Close()
        }
        Start-Sleep -Seconds 1
    }
    throw "Timed out waiting for $HostName`:$Port."
}

Write-Header

Invoke-Step "[1/7] Checking required commands..." {
    Require-Command docker "Install Docker Desktop and start it."
    Require-Command python "Install Python 3.11+ and make sure python is in PATH."
    Require-Command npm "Install Node.js 20+ and make sure npm is in PATH."
}

Invoke-Step "[2/7] Checking Docker Desktop..." {
    if (-not (Test-NativeSuccess -FilePath "docker" -Arguments @("version"))) {
        throw "Docker Desktop is not running. Start Docker Desktop, wait until it is ready, then run this launcher again."
    }
}

Invoke-Step "[3/7] Preparing .env..." {
    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example. Fill API keys in .env if model calls fail."
    }
    elseif (Test-Path ".env") {
        Write-Host ".env found."
    }
    else {
        Write-Host ".env.example not found; continuing with environment variables only."
    }
}

Invoke-Step "[4/7] Starting Docker services..." {
    $services = @("mysql")
    if ($WithEmbedding) {
        $services += "bge-m3"
    }
    Invoke-Native -FilePath "docker" -Arguments (@("compose", "up", "-d") + $services) -ErrorMessage "Failed to start Docker services. Check that Docker Desktop is running Linux containers."
    Wait-TcpPort -HostName "127.0.0.1" -Port 3307 -TimeoutSeconds 60
    Write-Host "MySQL is reachable on 127.0.0.1:3307."
    if ($WithEmbedding) {
        Wait-TcpPort -HostName "127.0.0.1" -Port 8090 -TimeoutSeconds 60
        Write-Host "Embedding service is reachable on 127.0.0.1:8090."
    }
}

Invoke-Step "[5/7] Checking backend Python dependencies..." {
    python -c "import fastapi, sqlalchemy, uvicorn, pymysql" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing backend dependencies from requirements.txt..."
        Invoke-Native -FilePath "python" -Arguments @("-m", "pip", "install", "-r", "requirements.txt") -ErrorMessage "Failed to install backend dependencies."
    }
    else {
        Write-Host "Backend dependencies look available."
    }
}

Invoke-Step "[6/7] Preparing frontend..." {
    Push-Location "frontend"
    try {
        if (-not $SkipNpmInstall -and -not (Test-Path "node_modules")) {
            Invoke-Native -FilePath "npm" -Arguments @("install") -ErrorMessage "Failed to install frontend dependencies."
        }
        elseif (Test-Path "node_modules") {
            Write-Host "frontend/node_modules found."
        }

        if (-not $SkipBuild) {
            Invoke-Native -FilePath "npm" -Arguments @("run", "build") -ErrorMessage "Frontend build failed."
        }
        else {
            Write-Host "Skipped frontend build."
        }
    }
    finally {
        Pop-Location
    }
}

if ($NoBackend) {
    Write-Host ""
    Write-Host "Startup checks completed. Backend launch skipped because -NoBackend was set."
    exit 0
}

Invoke-Step "[7/7] Starting backend..." {
    Write-Host ""
    Write-Host "Open: http://127.0.0.1:8500"
    Write-Host "Stop: press Ctrl+C in this window."
    Write-Host ""
    python -m app.api
}
