# =============================================================
#  墨池 Inkstone · 一键启动（静默后台版，给自己/命令行用）
#  等价于 start-dev.ps1 -Headless：不开新窗口，日志写 server\logs\
#  用法：powershell -ExecutionPolicy Bypass -File .\dev-up.ps1
# =============================================================
& "$PSScriptRoot\start-dev.ps1" -Headless -NoBrowser
exit $LASTEXITCODE
