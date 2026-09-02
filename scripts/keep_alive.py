import subprocess
import time
import os
import sys
import urllib.request

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_BIN = os.path.join(PROJECT_DIR, ".venv", "bin", "python3")
CLOUDFLARED_BIN = os.path.join(PROJECT_DIR, "cloudflared")

def check_server_health(port=8000):
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False

def main():
    print("=" * 70)
    print("🚀 OPTISTYLE PRO - DAEMON AUTO-HEALING & PERMANENT KEEP-ALIVE")
    print("=" * 70)

    server_proc = None
    tunnel_proc = None

    while True:
        try:
            # 1. Check & Keep Server Alive
            if not check_server_health():
                print("⚡ [Auto-Heal] Đang khởi động lại FastAPI Server...")
                if server_proc:
                    try:
                        server_proc.kill()
                    except Exception:
                        pass
                server_proc = subprocess.Popen(
                    [PYTHON_BIN, "app/main.py"],
                    cwd=PROJECT_DIR,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                time.sleep(3)

            # 2. Check & Keep Cloudflare Tunnel Alive
            if tunnel_proc is None or tunnel_proc.poll() is not None:
                print("🌐 [Auto-Heal] Đang khởi tạo đường truyền Cloudflare Tunnel...")
                tunnel_proc = subprocess.Popen(
                    [CLOUDFLARED_BIN, "tunnel", "--url", "http://localhost:8000"],
                    cwd=PROJECT_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                # Read until URL is printed
                for _ in range(30):
                    line = tunnel_proc.stdout.readline()
                    if "trycloudflare.com" in line:
                        print(f"👉 Link Online Ổn Định: {line.strip()}")
                        break
                    time.sleep(0.3)

            time.sleep(10)

        except KeyboardInterrupt:
            print("\n🛑 Đang dừng hệ thống...")
            if server_proc: server_proc.kill()
            if tunnel_proc: tunnel_proc.kill()
            break
        except Exception as e:
            print(f"⚠️ Giám sát: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
