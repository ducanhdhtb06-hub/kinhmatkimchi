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

# Static Files Directory (Mounting on all potential Vercel prefixes)
static_dir = os.path.join(current_dir, "static")
uploads_dir = os.path.join(static_dir, "uploads")
try:
    os.makedirs(uploads_dir, exist_ok=True)
except OSError:
    pass

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.mount("/api/index.py/static", StaticFiles(directory=static_dir), name="static_alias1")
    app.mount("/api/index/static", StaticFiles(directory=static_dir), name="static_alias2")

# Mount Routers across all potential Vercel Serverless path formats
for pfx in ["", "/api/index.py", "/api/index"]:
    app.include_router(web.router, prefix=pfx)
    app.include_router(api.router, prefix=pfx)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
