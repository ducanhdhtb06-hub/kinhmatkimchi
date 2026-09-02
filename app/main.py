import os
import sys

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

@app.middleware("http")
async def header_diagnostic_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["x-debug-scope-path"] = request.scope.get("path", "NONE")
    response.headers["x-debug-req-url"] = str(request.url)
    return response

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
    app.mount("/api/static", StaticFiles(directory=static_dir), name="static_api")

# Mount Routers on root and all possible prefixes
for pfx in ["", "/api", "/api/index", "/api/index.py"]:
    app.include_router(web.router, prefix=pfx)
    app.include_router(api.router, prefix=pfx)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
