import os
import sys

# Tự động nạp thư viện từ môi trường ảo .venv (nếu chạy bằng Python ngoài)
current_dir = os.path.dirname(os.path.abspath(__file__))
venv_lib_dir = os.path.join(current_dir, ".venv", "lib")

if os.path.exists(venv_lib_dir):
    for item in os.listdir(venv_lib_dir):
        if item.startswith("python"):
            sp = os.path.join(venv_lib_dir, item, "site-packages")
            if os.path.exists(sp) and sp not in sys.path:
                sys.path.insert(0, sp)

# Also check snap site-packages
snap_sp = "/home/anh/snap/antigravity-cli/common/lib/python3.12/site-packages"
if os.path.exists(snap_sp) and snap_sp not in sys.path:
    sys.path.insert(0, snap_sp)

try:
    import uvicorn
except ImportError as e:
    print("❌ Lỗi: Chưa tìm thấy thư viện uvicorn. Đang thử chạy qua môi trường .venv...")
    venv_python = os.path.join(current_dir, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        raise e

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("=" * 70)
    print(f"🚀 Đang khởi động máy chủ Kính Mắt Kim Chi trên cổng {port}")
    print(f"👉 Mở trình duyệt và truy cập: http://localhost:{port}")
    print(f"👉 Phòng Thử Kính AR Ảo:       http://localhost:{port}/tryon")
    print(f"👉 Bảng Quản Trị Hệ Thống:     http://localhost:{port}/admin")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=(port == 8000))
