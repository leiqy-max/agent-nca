param(
    [switch]$NoFrontend,
    [switch]$NoBackend,
    [switch]$CleanBuildEnv,
    [switch]$NoOcrBundle
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectRoot

$ReleaseDir = Join-Path $ProjectRoot "release"
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

function Invoke-Docker {
    param([string[]]$DockerArgs)
    Write-Host "[debug] docker $($DockerArgs -join ' ')"
    & docker @DockerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker $($DockerArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

if (-not $NoFrontend) {
    Write-Host "[frontend] Building Docker image..."
    Invoke-Docker -DockerArgs @("compose", "build", "frontend")

    $FrontendOut = Join-Path $ReleaseDir "frontend-static"
    if (Test-Path $FrontendOut) {
        Remove-Item -Recurse -Force $FrontendOut
    }
    New-Item -ItemType Directory -Force -Path $FrontendOut | Out-Null

    $cid = (& docker create agent-nca-frontend:latest).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $cid) {
        throw "docker create agent-nca-frontend:latest failed"
    }
    try {
        Invoke-Docker -DockerArgs @("cp", "${cid}:/usr/share/nginx/html/.", $FrontendOut)
    }
    finally {
        & docker rm $cid | Out-Null
    }

    Copy-Item -Force (Join-Path $ProjectRoot "frontend\nginx.conf") (Join-Path $FrontendOut "nginx.conf")
    Compress-Archive -Path (Join-Path $FrontendOut "*") -DestinationPath (Join-Path $ReleaseDir "ops-agent-frontend-static.zip") -Force

    $FrontendDist = Join-Path $ProjectRoot "frontend\dist"
    if (Test-Path $FrontendDist) {
        Remove-Item -Recurse -Force $FrontendDist
    }
    New-Item -ItemType Directory -Force -Path $FrontendDist | Out-Null
    Copy-Item -Recurse -Force (Join-Path $FrontendOut "*") $FrontendDist
    Remove-Item -Force (Join-Path $FrontendDist "nginx.conf") -ErrorAction SilentlyContinue

    $DemoOut = Join-Path $ReleaseDir "demo"
    $AgentUiOut = Join-Path $DemoOut "agent-ui"
    if (Test-Path $DemoOut) {
        Remove-Item -Recurse -Force $DemoOut
    }
    New-Item -ItemType Directory -Force -Path $AgentUiOut | Out-Null
    Copy-Item -Recurse -Force (Join-Path $FrontendDist "*") $AgentUiOut
    Compress-Archive -Path $DemoOut -DestinationPath (Join-Path $ReleaseDir "demo.zip") -Force

    Write-Host "[frontend] Output: release\ops-agent-frontend-static.zip"
    Write-Host "[frontend] Output: release\demo.zip"
}

if (-not $NoBackend) {
    Write-Host "[backend] Building Linux x64 binary package in Docker..."
    $envArgs = @()
    if ($CleanBuildEnv) {
        $envArgs += @("-e", "CLEAN_BUILD_ENV=1")
    }
    if ($NoOcrBundle) {
        $envArgs += @("-e", "ENABLE_OCR_BUNDLE=0")
    }

    $runArgs = @(
        "run", "--rm",
        "-v", "${ProjectRoot}:/work",
        "-w", "/work"
    ) + $envArgs + @(
        "agent-nca-backend",
        "bash", "-lc",
        "apt-get update && apt-get install -y curl zip && bash build_intranet.sh"
    )
    Invoke-Docker -DockerArgs $runArgs

    Copy-Item -Force (Join-Path $ProjectRoot "ops-agent-linux-x64.zip") (Join-Path $ReleaseDir "ops-agent-linux-x64.zip")
    Write-Host "[backend] Output: release\ops-agent-linux-x64.zip"
}

Write-Host "[done] Intranet packages are under: $ReleaseDir"
