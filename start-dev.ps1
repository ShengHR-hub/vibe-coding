# =============================================================
#  墨池 Inkstone · 一键启动（开发模式）
#  后端 Flask :5000 + 前端 Vite :5173
#  用法：双击 启动开发服务.bat，或运行：
#    powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
#  参数：-NoBrowser 不自动开浏览器 / -SkipDbCheck 跳过 MySQL 检测
# =============================================================
param(
    [int]$BackendPort  = 5000,
    [int]$FrontendPort = 5173,
    [switch]$NoBrowser,
    [switch]$SkipDbCheck
)

$Root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Server  = Join-Path $Root 'server'
$Client  = Join-Path $Root 'client'
$EnvFile = Join-Path $Server '.env'

function Say($m)  { Write-Host "[Inkstone] $m" -ForegroundColor Cyan }
function Warn($m){ Write-Host "[Inkstone] $m" -ForegroundColor Yellow }
function Fail($m){ Write-Host "[Inkstone] $m" -ForegroundColor Red; exit 1 }

function Test-Tcp([int]$port) {
    try {
        $c = New-Object Net.Sockets.TcpClient
        $ar = $c.BeginConnect('127.0.0.1', $port, $null, $null)
        if (-not $ar.AsyncWaitHandle.WaitOne(500)) { $c.Close(); return $false }
        $c.EndConnect($ar); $c.Close(); return $true
    } catch { return $false }
}

Say '=== 墨池 Inkstone 开发环境一键启动 ==='

# ---------- 1. 环境检查 ----------
foreach ($cmd in 'python', 'node', 'npm') {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Fail "未找到 $cmd ，请先安装并把它加入 PATH 后重试"
    }
}
if (-not (Test-Path $EnvFile)) {
    Fail "缺少配置文件 $EnvFile （请先复制 server\.env.example 为 server\.env 并填好数据库/AI 配置）"
}
if (-not (Test-Path (Join-Path $Client 'node_modules'))) {
    Warn 'client\node_modules 不存在，先执行 npm install（首次运行需要几分钟）…'
    Push-Location $Client
    npm install
    Pop-Location
}

# ---------- 2. MySQL 可达性检测（可跳过） ----------
if (-not $SkipDbCheck) {
    $host_ = 'localhost'; $port_ = 3306
    try {
        $raw = Get-Content -Raw $EnvFile
        if ($raw -match '(?m)^\s*MYSQL_HOST\s*=\s*(\S+)')  { $host_ = $Matches[1] }
        if ($raw -match '(?m)^\s*MYSQL_PORT\s*=\s*(\S+)')  { $port_ = [int]$Matches[1] }
    } catch { }
    if (Test-Tcp $port_) {
        Say "MySQL 检测通过（$host_`:$port_ 可连接）"
    } else {
        Warn "MySQL（$host_`:$port_）连不上：请先启动 MySQL 服务；并确认已执行过 schema.sql + seed.py（见 README）"
    }
}

# ---------- 3. 启动后端 ----------
if (Test-Tcp $BackendPort) {
    Warn "端口 $BackendPort 已被占用，视为后端已在运行，跳过启动"
} else {
    Say "启动后端 Flask → http://127.0.0.1:$BackendPort （新窗口，日志实时显示）"
    Start-Process powershell -ArgumentList @(
        '-NoExit', '-Command',
        "Set-Location -LiteralPath '$Server'; Write-Host '== Inkstone Backend (Ctrl+C 停止) ==' -ForegroundColor Green; python app.py"
    ) | Out-Null
}

# ---------- 4. 启动前端 ----------
if (Test-Tcp $FrontendPort) {
    Warn "端口 $FrontendPort 已被占用，视为前端已在运行，跳过启动"
} else {
    Say "启动前端 Vite → http://127.0.0.1:$FrontendPort （新窗口，日志实时显示）"
    Start-Process powershell -ArgumentList @(
        '-NoExit', '-Command',
        "Set-Location -LiteralPath '$Client'; Write-Host '== Inkstone Frontend (Ctrl+C 停止) ==' -ForegroundColor Green; npm run dev"
    ) | Out-Null
}

# ---------- 5. 等待就绪并打开浏览器 ----------
Say '等待服务就绪…'
$beOk = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Tcp $BackendPort) { $beOk = $true; break }
}
$feOk = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Tcp $FrontendPort) { $feOk = $true; break }
}

if ($beOk) { Say "后端就绪  http://127.0.0.1:$BackendPort" }
else       { Warn "后端 40s 内未就绪：请查看后端窗口报错（常见：数据库未启动 / .env 配置问题）" }
if ($feOk) { Say "前端就绪  http://127.0.0.1:$FrontendPort" }
else       { Warn "前端 60s 内未就绪：请查看前端窗口报错" }

if ($feOk -and -not $NoBrowser) {
    Say '正在打开浏览器…'
    Start-Process "http://127.0.0.1:$FrontendPort"
}

Say '启动完成。提示：两个黑色窗口分别运行前后端，关掉即停止；也可运行 停止开发服务.bat 一键停止。'
