# =============================================================
#  墨池 Inkstone · 一键停止（静默后台版，给自己/命令行用）
#  等价于 stop-dev.ps1 -Force：按端口结束 5000/5173 监听进程
#  用法：powershell -ExecutionPolicy Bypass -File .\dev-down.ps1
# =============================================================
& "$PSScriptRoot\stop-dev.ps1" -Force
exit $LASTEXITCODE
