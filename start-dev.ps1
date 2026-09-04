# =============================================================
#  墨池 Inkstone · 一键启动（开发模式）
#  后端 Flask :5000 + 前端 Vite :5173
#  用法：双击 启动开发服务.bat，或运行：
#    powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
#  参数：
#    -NoBrowser   启动完不自动打开浏览器
#    -SkipDbCheck 跳过 MySQL 检测
#    -Headless    后台静默模式（不开窗口，日志写入 server\logs\，
#                 适合给自己/命令行使用 —— 推荐用 dev-up.ps1）
# =============================================================
param(
    [int]$BackendPort  = 5000,
    [int]$FrontendPort = 5173,
    [switch]$NoBrowser,
    [switch]$SkipDbCheck,
    [switch]$Headless
)

$Root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Server  = Join-Path $Root 'server'
$Client  = Join-Path $Root 'client'
$EnvFile = Join-Path $Server '.env'
$LogDir  = Join-Path $Server 'logs'

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

if ($Headless) { $mode = 'headless' } else { $mode = 'windowed' }
Say "=== 墨池 Inkstone 开发环境一键启动（$mode 模式） ==="

# ---------- 1. 环境检查 ----------
foreach ($cmd in 'python', 'node') {
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
        if ($raw -match '(?m)^\s*MYSQL_HOST\s*=\s*(\S+)') { $host_ = $Matches[1] }
        if ($raw -match '(?m)^\s*MYSQL_PORT\s*=\s*(\S+)') { $port_ = [int]$Matches[1] }
    } catch { }
    if (Test-Tcp $port_) {
        Say "MySQL 检测通过（$host_`:$port_ 可连接）"
    } else {
        Warn "MySQL（$host_`:$port_）连不上：请先启动 MySQL 服务；并确认已执行过 schema.sql + seed.py（见 README）"
    }
}

# ---------- 3. 启动后端 ----------
$beStarted = $false
if (Test-Tcp $BackendPort) {
    Warn "端口 $BackendPort 已被占用，视为后端已在运行，跳过启动"
} else {
    if ($Headless) {
        New-Item -ItemType Directory -Force $LogDir | Out-Null
        Start-Process -FilePath 'python' -ArgumentList @('-u', 'app.py') `
            -WorkingDirectory $Server -WindowStyle Hidden `
            -RedirectStandardOutput (Join-Path $LogDir 'dev-backend.log') `
            -RedirectStandardError  (Join-Path $LogDir 'dev-backend.err.log') | Out-Null
    } else {
        Start-Process powershell -ArgumentList @(
            '-NoExit', '-Command',
            "Set-Location -LiteralPath '$Server'; Write-Host '== Inkstone Backend (Ctrl+C 停止) ==' -ForegroundColor Green; python app.py"
        ) | Out-Null
    }
    $beStarted = $true
    Say "后端启动中 → http://127.0.0.1:$BackendPort"
}

# ---------- 4. 启动前端 ----------
$feStarted = $false
if (Test-Tcp $FrontendPort) {
    Warn "端口 $FrontendPort 已被占用，视为前端已在运行，跳过启动"
} else {
    if ($Headless) {
        New-Item -ItemType Directory -Force $LogDir | Out-Null
        Start-Process -FilePath 'node' -ArgumentList @('node_modules/vite/bin/vite.js') `
            -WorkingDirectory $Client -WindowStyle Hidden `
            -RedirectStandardOutput (Join-Path $LogDir 'dev-frontend.log') `
            -RedirectStandardError  (Join-Path $LogDir 'dev-frontend.err.log') | Out-Null
    } else {
        Start-Process powershell -ArgumentList @(
            '-NoExit', '-Command',
            "Set-Location -LiteralPath '$Client'; Write-Host '== Inkstone Frontend (Ctrl+C 停止) ==' -ForegroundColor Green; npm run dev"
        ) | Out-Null
    }
    $feStarted = $true
    Say "前端启动中 → http://127.0.0.1:$FrontendPort"
}

# ---------- 5. 并行等待两端就绪 ----------
if ($beStarted -or $feStarted) {
    Say '等待服务就绪…'
    $beOk = -not $beStarted   # 本来就已在运行的视为就绪
    $feOk = -not $feStarted
    for ($i = 0; $i -lt 120; $i++) {
        if (-not $beOk) { $beOk = Test-Tcp $BackendPort }
        if (-not $feOk) { $feOk = Test-Tcp $FrontendPort }
        if ($beOk -and $feOk) { break }
        Start-Sleep -Milliseconds 500
    }
    if ($beOk) { Say "后端就绪  http://127.0.0.1:$BackendPort" }
    else       { Warn "后端 60s 内未就绪：请查看日志/后端窗口报错（常见：数据库未启动 / .env 配置问题）" }
    if ($feOk) { Say "前端就绪  http://127.0.0.1:$FrontendPort" }
    else       { Warn "前端 60s 内未就绪：请查看日志/前端窗口报错" }
}

# ---------- 6. 收尾 ----------
if ($Headless) {
    Say "日志文件：$LogDir\dev-backend.log / dev-frontend.log（错误见 *.err.log）"
    Say "停止：powershell -ExecutionPolicy Bypass -File .\dev-down.ps1（或 stop-dev.ps1 -Force）"
}
if (-not $NoBrowser) {
    if (Test-Tcp $FrontendPort) { Say '正在打开浏览器…'; Start-Process "http://127.0.0.1:$FrontendPort" }
}
Say '启动完成。'
