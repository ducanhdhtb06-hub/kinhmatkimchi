#!/usr/bin/env bash
set -e

PROJECT_DIR="/home/anh/PycharmProjects/PythonProject"
cd "$PROJECT_DIR"

mkdir -p "$PROJECT_DIR/logs"

echo "========================================================"
echo "🚀 KHỞI CHẠY OPTISTYLE PRO TRÊN LINUX (CHẠY NGẦM 24/7)"
echo "========================================================"

# Kill any existing processes
pkill -f "app/main.py" 2>/dev/null || true
pkill -f "scripts/keep_alive.py" 2>/dev/null || true

# Run supervisor daemon in background with nohup
nohup "$PROJECT_DIR/.venv/bin/python3" "$PROJECT_DIR/scripts/keep_alive.py" > "$PROJECT_DIR/logs/service.log" 2>&1 &

echo "✅ Tiến trình đã được đưa vào chạy ngầm (PID: $!)"
echo "📄 Xem log hoạt động bằng lệnh: tail -f logs/service.log"
echo "🛑 Để dừng hệ thống: pkill -f scripts/keep_alive.py"
