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

app = FastAPI(
    title="Kính Mắt Kim Chi - Eyewear E-commerce & Computer Vision",
    description="Nền tảng thương mại điện tử kính mắt thông minh tích hợp AR Virtual Try-On",
    version="2.0.0"
)

init_db_if_needed()

# HTTP Middleware để điều hướng chính xác 100% mọi trang trên Vercel
@app.middleware("http")
async def normalize_vercel_path(request: Request, call_next):
    # Ưu tiên 1: Đọc tham số 'path' được truyền từ Vercel rewrite (?path=/...)
    path_param = request.query_params.get("path")
    if path_param:
        clean_path = path_param.split("?")[0]
        if not clean_path.startswith("/"):
            clean_path = "/" + clean_path
        # Clean double slashes if any
        while "//" in clean_path:
            clean_path = clean_path.replace("//", "/")
        request.scope["path"] = clean_path
        request.scope["raw_path"] = clean_path.encode("utf-8")
    else:
        # Ưu tiên 2: Đọc header x-matched-path
        matched_path = request.headers.get("x-matched-path")
        if matched_path:
            clean_path = matched_path.split("?")[0]
            for prefix in ["/api/index.py", "/api/index"]:
                if clean_path.startswith(prefix + "/"):
                    clean_path = clean_path[len(prefix):]
                elif clean_path == prefix:
                    clean_path = "/"
            request.scope["path"] = clean_path
            request.scope["raw_path"] = clean_path.encode("utf-8")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
