import os
import sys

# Tự động nạp thư viện từ môi trường ảo .venv
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

try:
    from app.database import engine, Base, init_db_if_needed
    from app.routes import api, web
except (ImportError, ModuleNotFoundError):
    from database import engine, Base, init_db_if_needed
    from routes import api, web

# Tạo instance FastAPI chuẩn cho Vercel ASGI Handler
app = FastAPI(
    title="Kính Mắt Kim Chi - Eyewear E-commerce & Computer Vision",
    description="Nền tảng thương mại điện tử kính mắt thông minh tích hợp AR Virtual Try-On",
    version="2.0.0"
)

# Khởi tạo DB khi khởi động module
init_db_if_needed()

# Static Files Directory
static_dir = os.path.join(current_dir, "static")
uploads_dir = os.path.join(static_dir, "uploads")
try:
    os.makedirs(uploads_dir, exist_ok=True)
except OSError:
    pass

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount Routers
app.include_router(api.router)
app.include_router(web.router)

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Đang khởi động máy chủ Kính Mắt Kim Chi")
    print("👉 Mở trình duyệt và truy cập: http://localhost:8000")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
