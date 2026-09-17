#!/usr/bin/env bash
# ==============================================================
# 大清天朵二期社區 AI 管理助手 - 跨平台執行腳本 (run.sh)
# 適用於 macOS 與 Linux 終端機直接執行：./run.sh
# ==============================================================

set -e
cd "$(dirname "$0")"

echo "=== 啟動 大清天朵二期社區 AI 管理助手 ==="
if command -v open >/dev/null 2>&1; then
    # macOS
    python3 server.py &
    SERVER_PID=$!
    sleep 1
    open "http://127.0.0.1:8080"
    wait $SERVER_PID
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux Desktop
    python3 server.py &
    SERVER_PID=$!
    sleep 1
    xdg-open "http://127.0.0.1:8080"
    wait $SERVER_PID
else
    # Headless / Server
    echo "請以瀏覽器打開: http://127.0.0.1:8080"
    python3 server.py
fi
