# Soul Chat 启动脚本
# 同时启动后端和前端

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

$PROJECT_DIR = Split-Path -Parent $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       Soul Chat 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切换到项目目录
Set-Location $PROJECT_DIR

# 检查并安装后端依赖
Write-Host "[1/4] 检查后端依赖..." -ForegroundColor Yellow
$uv = "C:\Users\cute\AppData\Roaming\Python\Scripts\uv.exe"
if (-not (Test-Path $uv)) {
    $uv = "uv"
}
& $uv sync --quiet 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  依赖安装失败，尝试安装..." -ForegroundColor Red
    & $uv sync
}

# 检查前端依赖
if (-not $BackendOnly) {
    Write-Host "[2/4] 检查前端依赖..." -ForegroundColor Yellow
    $frontendDir = Join-Path $PROJECT_DIR "frontend"
    if (Test-Path (Join-Path $frontendDir "package.json")) {
        if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
            Write-Host "  安装前端依赖中..." -ForegroundColor Yellow
            Push-Location $frontendDir
            npm install --silent 2>$null
            Pop-Location
        }
    }
}

# 启动后端
$backendProcess = $null
if (-not $FrontendOnly) {
    Write-Host "[3/4] 启动后端 (端口 8000)..." -ForegroundColor Yellow
    $backendJob = Start-Job -ScriptBlock {
        param($dir, $uvPath, $pyPath)
        Set-Location $dir
        & $uvPath run python backend/main.py
    } -ArgumentList $PROJECT_DIR, $uv, "python"

    # 等待后端启动
    Start-Sleep -Seconds 5

    # 检查后端是否启动成功
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction Stop
        if ($response.status -eq "ok") {
            Write-Host "  后端启动成功!" -ForegroundColor Green
        }
    } catch {
        Write-Host "  后端启动失败: $_" -ForegroundColor Red
    }
}

# 启动前端
if (-not $BackendOnly) {
    Write-Host "[4/4] 启动前端 (端口 3000)..." -ForegroundColor Yellow
    $frontendDir = Join-Path $PROJECT_DIR "frontend"

    # 先停止可能存在的 node 进程
    Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1

    # 启动前端
    $frontendJob = Start-Job -ScriptBlock {
        param($dir)
        Set-Location $dir
        npm run dev
    } -ArgumentList $frontendDir

    # 等待前端启动
    Start-Sleep -Seconds 5

    Write-Host "  前端启动成功!" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  服务已启动!" -ForegroundColor Green
Write-Host "  后端: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  前端: http://localhost:3000" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Yellow
Write-Host ""

# 等待用户中断
try {
    while ($true) {
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host ""
    Write-Host "正在停止服务..." -ForegroundColor Yellow

    # 停止所有子进程
    Get-Job | Stop-Job -ErrorAction SilentlyContinue
    Get-Job | Remove-Job -ErrorAction SilentlyContinue
    Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    Write-Host "服务已停止" -ForegroundColor Green
}