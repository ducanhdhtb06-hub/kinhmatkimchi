import os
import sys

# Tự động nạp thư viện từ môi trường ảo .venv
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

try:
    from app.database import engine, Base, init_db_if_needed, get_db
    from app.routes import api, web
except (ImportError, ModuleNotFoundError):
    from database import engine, Base, init_db_if_needed, get_db
    from routes import api, web

# Tạo instance FastAPI chuẩn cho Vercel ASGI Handler
app = FastAPI(
    title="Kính Mắt Kim Chi - Eyewear E-commerce & Computer Vision",
    description="Nền tảng thương mại điện tử kính mắt thông minh tích hợp AR Virtual Try-On",
    version="2.0.0"
)

# Khởi tạo DB khi khởi động module
init_db_if_needed()

# HTTP Middleware để tự động chuẩn hóa đường dẫn Serverless Vercel
@app.middleware("http")
async def normalize_vercel_path(request: Request, call_next):
    path = request.scope.get("path", "/")
    for prefix in ["/api/index.py", "/api/index"]:
        if path.startswith(prefix):
            new_path = path[len(prefix):]
            if not new_path.startswith("/"):
                new_path = "/" + new_path
            request.scope["path"] = new_path
            request.scope["raw_path"] = new_path.encode("utf-8")
            break
    return await call_next(request)

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

# Direct fallback aliases for Vercel root
@app.get("/api/index.py")
def vercel_root_alias1(request: Request, db: Session = Depends(get_db)):
    return web.page_homepage(request, db)

@app.get("/api/index")
def vercel_root_alias2(request: Request, db: Session = Depends(get_db)):
    return web.page_homepage(request, db)

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Đang khởi động máy chủ Kính Mắt Kim Chi")
    print("👉 Mở trình duyệt và truy cập: http://localhost:8000")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
