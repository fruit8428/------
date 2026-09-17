@echo off
REM ==============================================================
REM 大清天朵二期社區 AI 管理助手 - Windows 雙擊啟動檔 (run.bat)
REM ==============================================================
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================================
echo   大清天朵二期社區 AI 管理助手 - Windows 啟動中...
echo ==========================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 找不到 Python，請確認已安裝 Python 3 並加入 PATH 環境變數。
    pause
    exit /b 1
)

echo 正在開啟瀏覽器前往: http://127.0.0.1:8080
start "" "http://127.0.0.1:8080"
echo 正在運行伺服器... 按 Ctrl+C 可停止服務。
python server.py
pause
