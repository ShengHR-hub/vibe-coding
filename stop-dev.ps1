# =============================================================
#  墨池 Inkstone · 一键停止（开发模式）
#  按端口找到并结束 5000(后端) / 5173(前端) 的监听进程
#  用法：双击 停止开发服务.bat，或：
#    powershell -ExecutionPolicy Bypass -File .\stop-dev.ps1 [-Force]
# =============================================================
param([switch]$Force)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Ports = @(5000, 5173)

function Say($m) { Write-Host "[Inkstone] $m" -ForegroundColor Cyan }

function Get-ListenerPids([int]$port) {
    $netstat = Join-Path $env:WINDIR 'System32\netstat.exe'
    $pids = @()
    & $netstat -ano -p tcp | Select-String "\:$port\s" | ForEach-Object {
        if ($_.Line -match 'LISTENING\s+(\d+)\s*$') { $pids += [int]$Matches[1] }
    }
    $pids | Select-Object -Unique
}

$any = $false
foreach ($port in $Ports) {
    $pids = @(Get-ListenerPids $port)
    foreach ($pid_ in $pids) {
        $any = $true
        $proc = Get-Process -Id $pid_ -ErrorAction SilentlyContinue
        $desc = if ($proc) { $proc.ProcessName } else { '?' }
        if ($Force) {
            Stop-Process -Id $pid_ -Force -ErrorAction SilentlyContinue
            Say "已停止端口 $port 的进程 (PID $pid_, $desc)"
        } else {
            Say "端口 $port 由 PID $pid_ ($desc) 监听 —— 使用 -Force 停止（或直接关闭对应黑窗口）"
        }
    }
    if ($pids.Count -eq 0) { Say "端口 $port 无监听进程" }
}
if (-not $any -and -not $Force) {
    Say '没有找到运行中的开发服务，无需停止。'
}
